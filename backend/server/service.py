from fastapi import HTTPException
from fastapi.responses import JSONResponse
from servicefoundry import trigger_job

from backend.indexer.indexer import upsert_documents_to_collection
from backend.indexer.types import IndexerConfig
from backend.logger import logger
from backend.modules.embedder import get_embedder
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.modules.metadata_store.models import (
    CollectionCreate,
    CollectionIndexerJobRunCreate,
    CollectionIndexerJobRunStatus,
)
from backend.modules.vector_db import get_vector_db_client
from backend.settings import settings
from backend.types import AddDocuments, CreateCollection


async def get_collections():
    try:
        vector_db_client = get_vector_db_client(config=settings.VECTOR_DB_CONFIG)
        collection_names = vector_db_client.get_collections()
        collections = METADATA_STORE_CLIENT.get_collections(
            names=collection_names, include_runs=False
        )
        return JSONResponse(
            content={"collections": [obj.dict() for obj in collections]}
        )
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


async def create_collection(request: CreateCollection):
    try:
        existing_collection = METADATA_STORE_CLIENT.get_collection_by_name(
            collection_name=request.name
        )
        if existing_collection:
            raise HTTPException(
                status_code=400,
                detail=f"Collection with name {request.name} already exists.",
            )
        collection = METADATA_STORE_CLIENT.create_collection(
            CollectionCreate(
                name=request.name,
                description=request.description,
                embedder_config=request.embedder_config,
                chunk_size=request.chunk_size,
            )
        )
        vector_db_client = get_vector_db_client(
            config=settings.VECTOR_DB_CONFIG, collection_name=request.name
        )
        vector_db_client.create_collection(get_embedder(request.embedder_config))
        return JSONResponse(content={"collection": collection.dict()}, status_code=201)
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


async def upsert_documents_to_collection(request: AddDocuments, collection_name: str):
    try:
        collection = METADATA_STORE_CLIENT.get_collection_by_name(
            collection_name=collection_name
        )
        if not collection:
            raise HTTPException(
                status_code=404,
                detail=f"Collection with name {collection_name} does not exist.",
            )
        current_indexer_job_run = METADATA_STORE_CLIENT.get_current_indexer_job_run(
            collection_name=collection_name
        )
        if (
            not request.force
            and current_indexer_job_run
            and current_indexer_job_run.status
            not in [
                CollectionIndexerJobRunStatus.COMPLETED,
                CollectionIndexerJobRunStatus.FAILED,
            ]
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Collection with name {collection_name} already has an active indexer job run with status {current_indexer_job_run.status.value}. Please wait for it to complete.",
            )
        indexer_job_run = METADATA_STORE_CLIENT.create_collection_indexer_job_run(
            collection_name=collection_name,
            indexer_job_run=CollectionIndexerJobRunCreate(
                data_source=request.data_source,
                parser_config=request.parser_config,
            ),
        )
        if settings.DEBUG_MODE:
            await upsert_documents_to_collection(
                inputs=IndexerConfig(
                    collection_name=collection_name,
                    indexer_job_run_name=indexer_job_run.name,
                    data_source=request.data_source,
                    chunk_size=collection.chunk_size,
                    embedder_config=collection.embedder_config,
                    parser_config=request.parser_config,
                    vector_db_config=settings.VECTOR_DB_CONFIG,
                    metadata_store_config=settings.METADATA_STORE_CONFIG,
                    embedding_cache_config=settings.EMBEDDING_CACHE_CONFIG,
                    indexing_mode=request.indexing_mode,
                )
            )
        else:
            if not settings.JOB_FQN or not settings.JOB_COMPONENT_NAME:
                raise HTTPException(
                    status_code=500,
                    detail="Job FQN and Job Component Name are required to trigger the job",
                )
            trigger_job(
                application_fqn=settings.JOB_FQN,
                component_name=settings.JOB_COMPONENT_NAME,
                params={
                    "collection_name": collection_name,
                    "indexer_job_run_name": indexer_job_run.name,
                },
            )
        return JSONResponse(
            status_code=201, content={"indexer_job_run": indexer_job_run.dict()}
        )
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        METADATA_STORE_CLIENT.update_indexer_job_run_status(
            collection_inderer_job_run_name=indexer_job_run.name,
            status=CollectionIndexerJobRunStatus.FAILED,
        )
        raise HTTPException(status_code=500, detail=str(exp))


async def delete_collection(collection_name: str):
    try:
        vector_db_client = get_vector_db_client(
            config=settings.VECTOR_DB_CONFIG, collection_name=collection_name
        )
        vector_db_client.delete_collection()
        METADATA_STORE_CLIENT.delete_collection(collection_name, include_runs=True)
        return JSONResponse(content={"deleted": True})
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


async def get_collection_status(collection_name: str):
    collection = METADATA_STORE_CLIENT.get_collection_by_name(
        collection_name=collection_name
    )

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    current_indexer_job_run = METADATA_STORE_CLIENT.get_current_indexer_job_run(
        collection_name=collection_name
    )

    if current_indexer_job_run is None:
        return JSONResponse(
            content={"status": "MISSING", "message": "No indexer job runs found"}
        )

    return JSONResponse(
        content={
            "status": current_indexer_job_run.status.value,
            "message": f"Indexer job run {current_indexer_job_run.name} in {current_indexer_job_run.status.value}. Check logs for more details.",
        }
    )
