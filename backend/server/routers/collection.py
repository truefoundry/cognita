from fastapi import APIRouter, Path, HTTPException
from fastapi.responses import JSONResponse
from truefoundry.deploy import trigger_job



from backend.indexer.indexer import sync_data_source_to_collection
from backend.indexer.types import DataIngestionConfig
from backend.logger import logger
from backend.modules.embedder.embedder import get_embedder
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.modules.vector_db.client import VECTOR_STORE_CLIENT
from backend.settings import settings
from backend.types import (
    AssociateDataSourceWithCollection,
    AssociateDataSourceWithCollectionDto,
    UnassociateDataSourceWithCollectionDto,
    CreateCollection,
    CreateCollectionDto,
    CreateDataIngestionRun,
    DataIngestionRunStatus,
    IngestDataToCollectionDto,
    ListDataIngestionRunsDto,
)


router = APIRouter(prefix="/v1/collections", tags=["collections"])


@router.get("/")
def get_collections():
    """API to list all collections"""
    try:
        logger.debug("Listing all the collections...")
        collections = METADATA_STORE_CLIENT.get_collections()
        if collections is None:
            return JSONResponse(content={"collections": []})
        return JSONResponse(
            content={"collections": [obj.dict() for obj in collections]}
        )
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("/")
def create_collection(collection: CreateCollectionDto):
    """API to create a collection"""
    try:
        logger.debug(f"Creating collection {collection.name}...")
        created_collection = METADATA_STORE_CLIENT.create_collection(
            collection=CreateCollection(
                name=collection.name,
                description=collection.description,
                embedder_config=collection.embedder_config,
            )
        )

        VECTOR_STORE_CLIENT.create_collection(
            collection_name=collection.name,
            embeddings=get_embedder(collection.embedder_config),
        )
        if collection.associated_data_sources:
            for data_source in collection.associated_data_sources:
                METADATA_STORE_CLIENT.associate_data_source_with_collection(
                    collection_name=created_collection.name,
                    data_source_association=AssociateDataSourceWithCollection(
                        data_source_fqn=data_source.data_source_fqn,
                        parser_config=data_source.parser_config,
                    ),
                )
            created_collection = METADATA_STORE_CLIENT.get_collection_by_name(
                collection_name=created_collection.name
            )
        return JSONResponse(
            content={"collection": created_collection.dict()}, status_code=201
        )
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("/associate_data_source")
async def associate_data_source_to_collection(
    request: AssociateDataSourceWithCollectionDto,
):
    """Add a data source to the collection"""
    try:
        collection = METADATA_STORE_CLIENT.associate_data_source_with_collection(
            collection_name=request.collection_name,
            data_source_association=AssociateDataSourceWithCollection(
                data_source_fqn=request.data_source_fqn,
                parser_config=request.parser_config,
            ),
        )
        return JSONResponse(content={"collection": collection.dict()})
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("/unassociate_data_source")
async def unassociate_data_source_from_collection(
    request: UnassociateDataSourceWithCollectionDto,
):
    """Remove a data source to the collection"""
    try:
        collection = METADATA_STORE_CLIENT.unassociate_data_source_with_collection(
            collection_name=request.collection_name,
            data_source_fqn=request.data_source_fqn,
        )
        return JSONResponse(content={"collection": collection.dict()})
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))



@router.post("/ingest")
async def ingest_data(request: IngestDataToCollectionDto):
    """Ingest data into the collection"""
    try:
        collection = METADATA_STORE_CLIENT.get_collection_by_name(
            collection_name=request.collection_name, no_cache=True
        )
        if not collection:
            logger.error(
                f"Collection with name {request.collection_name} does not exist."
            )
            raise HTTPException(
                status_code=404,
                detail=f"Collection with name {request.collection_name} does not exist.",
            )

        if not collection.associated_data_sources:
            logger.error(
                f"Collection {request.collection_name} does not have any associated data sources."
            )
            raise HTTPException(
                status_code=400,
                detail=f"Collection {request.collection_name} does not have any associated data sources.",
            )
        associated_data_sources_to_be_ingested = []
        if request.data_source_fqn:
            associated_data_sources_to_be_ingested = [
                collection.associated_data_sources.get(request.data_source_fqn)
            ]
        else:
            associated_data_sources_to_be_ingested = (
                collection.associated_data_sources.values()
            )

        for associated_data_source in associated_data_sources_to_be_ingested:
            logger.debug(
                f"Starting ingestion for data source fqn: {associated_data_source.data_source_fqn}"
            )
            if not request.run_as_job:
                data_ingestion_run = CreateDataIngestionRun(
                    collection_name=collection.name,
                    data_source_fqn=associated_data_source.data_source_fqn,
                    embedder_config=collection.embedder_config,
                    parser_config=associated_data_source.parser_config,
                    data_ingestion_mode=request.data_ingestion_mode,
                    raise_error_on_failure=request.raise_error_on_failure,
                )
                created_data_ingestion_run = (
                    METADATA_STORE_CLIENT.create_data_ingestion_run(
                        data_ingestion_run=data_ingestion_run
                    )
                )
                await sync_data_source_to_collection(
                    inputs=DataIngestionConfig(
                        collection_name=created_data_ingestion_run.collection_name,
                        data_ingestion_run_name=created_data_ingestion_run.name,
                        data_source=associated_data_source.data_source,
                        embedder_config=collection.embedder_config,
                        parser_config=created_data_ingestion_run.parser_config,
                        data_ingestion_mode=created_data_ingestion_run.data_ingestion_mode,
                        raise_error_on_failure=created_data_ingestion_run.raise_error_on_failure,
                    )
                )
                created_data_ingestion_run.status = DataIngestionRunStatus.COMPLETED
            else:
                if not settings.JOB_FQN or not settings.JOB_COMPONENT_NAME:
                    logger.error(
                        "Job FQN and Job Component Name are required to trigger the job"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail="Job FQN and Job Component Name are required to trigger the job",
                    )
                trigger_job(
                    application_fqn=settings.JOB_FQN,
                    component_name=settings.JOB_COMPONENT_NAME,
                    params={
                        "collection_name": collection.name,
                        "data_source_fqn": associated_data_source.data_source_fqn,
                        "data_ingestion_mode": request.data_ingestion_mode.value,
                        "raise_error_on_failure": (
                            "True" if request.raise_error_on_failure else "False"
                        ),
                    },
                )
        return JSONResponse(
            status_code=201,
            content={"message": "triggered"},
        )
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))



@router.delete("/{collection_name}")
def delete_collection(collection_name: str = Path(title="Collection name")):
    """Delete collection given it's name"""
    try:
        VECTOR_STORE_CLIENT.delete_collection(collection_name=collection_name)
        METADATA_STORE_CLIENT.delete_collection(collection_name, include_runs=True)
        return JSONResponse(content={"deleted": True})
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("/data_ingestion_runs/list")
def list_data_ingestion_runs(request: ListDataIngestionRunsDto):
    data_ingestion_runs = METADATA_STORE_CLIENT.get_data_ingestion_runs(
        request.collection_name, request.data_source_fqn
    )
    return JSONResponse(
        content={"data_ingestion_runs": [obj.dict() for obj in data_ingestion_runs]}
    )


@router.get("/data_ingestion_runs/{data_ingestion_run_name}/status")
def get_collection_status(
    data_ingestion_run_name: str = Path(title="Data Ingestion Run name"),
):
    """Get status for given data ingestion run"""
    data_ingestion_run = METADATA_STORE_CLIENT.get_data_ingestion_run(
        data_ingestion_run_name=data_ingestion_run_name, no_cache=True
    )

    if data_ingestion_run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Data ingestion run {data_ingestion_run_name} not found",
        )

    return JSONResponse(
        content={
            "status": data_ingestion_run.status.value,
            "message": f"Data ingestion job run {data_ingestion_run.name} in {data_ingestion_run.status.value}. Check logs for more details.",
        }
    )

    
