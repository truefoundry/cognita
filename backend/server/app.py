import json
from typing import Optional

import mlfoundry
import requests
from fastapi import APIRouter, FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mlfoundry.artifact.truefoundry_artifact_repo import (
    ArtifactIdentifier,
    MlFoundryArtifactsRepository,
)
from servicefoundry import trigger_job

from backend.indexer.indexer import trigger_job_locally
from backend.indexer.types import IndexerConfig
from backend.logger import logger
from backend.modules import query_controllers
from backend.modules.dataloaders.loader import LOADER_REGISTRY
from backend.modules.embedder import get_embedder
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.modules.metadata_store.models import (
    CollectionCreate,
    CollectionIndexerJobRunCreate,
    CollectionIndexerJobRunStatus,
)
from backend.modules.parsers.parser import PARSER_REGISTRY
from backend.modules.vector_db import get_vector_db_client
from backend.server.decorators import QUERY_CONTROLLER_REGISTRY
from backend.settings import settings
from backend.types import (
    AddDocuments,
    CreateCollection,
    ModelType,
    UploadToDataDirectoryDto,
)

# FastAPI Initialization
app = FastAPI(
    title="Backend for RAG",
    root_path=settings.TFY_SERVICE_ROOT_PATH,
    docs_url="/",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def status():
    return JSONResponse(content={"status": "ok"})


@app.get("/collections")
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


@app.post("/collections")
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


@app.post("/collections/{collection_name}/add_docs")
async def add_documents_to_collection(
    request: AddDocuments, collection_name: str = Path(title="Collection name")
):
    try:
        collection = METADATA_STORE_CLIENT.get_collection_by_name(
            collection_name=collection_name
        )
        if not collection:
            raise HTTPException(
                status_code=404,
                detail=f"Collection with name {collection_name} does not exist.",
            )
        current_indexer_job_run = (
            METADATA_STORE_CLIENT.get_current_indexer_job_run(
                collection_name=collection_name
            )
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
        indexer_job_run = (
            METADATA_STORE_CLIENT.create_collection_indexer_job_run(
                collection_name=collection_name,
                indexer_job_run=CollectionIndexerJobRunCreate(
                    data_source=request.data_source,
                    parser_config=request.parser_config,
                ),
            )
        )
        if settings.DEBUG_MODE:
            await trigger_job_locally(
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
                    deletion_mode=request.deletion_mode,
                )
            )
        else:
            trigger_job(
                application_fqn=settings.JOB_FQN,
                component_name=settings.JOB_COMPONENT_NAME,
                params={
                    "collection_name": collection_name,
                    "indexer_job_run_name": indexer_job_run.name,
                    "data_source": json.dumps(request.data_source.dict()),
                    "chunk_size": str(collection.chunk_size),
                    "embedder_config": json.dumps(collection.embedder_config.dict()),
                    "parser_config": json.dumps(request.parser_config.dict()),
                    "vector_db_config": json.dumps(settings.VECTOR_DB_CONFIG.dict()),
                    "metadata_store_config": json.dumps(
                        settings.METADATA_STORE_CONFIG.dict()
                    ),
                    "deletion_mode": request.deletion_mode.value,
                    **(
                        {
                            "embedding_cache_config": json.dumps(
                                settings.EMBEDDING_CACHE_CONFIG.dict()
                            )
                        }
                        if settings.EMBEDDING_CACHE_CONFIG
                        else {"embedding_cache_config": ""}
                    ),
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


@app.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str = Path(title="Collection name")):
    try:
        vector_db_client = get_vector_db_client(
            config=settings.VECTOR_DB_CONFIG, collection_name=collection_name
        )
        vector_db_client.delete_collection()
        METADATA_STORE_CLIENT.delete_collection(
            collection_name, include_runs=True
        )
        return JSONResponse(content={"deleted": True})
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@app.get("/collections/{collection_name}/status")
async def get_collection_status(collection_name: str = Path(title="Collection name")):
    collection = METADATA_STORE_CLIENT.get_collection_by_name(
        collection_name=collection_name
    )

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    current_indexer_job_run = (
        METADATA_STORE_CLIENT.get_current_indexer_job_run(
            collection_name=collection_name
        )
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

@app.post("/upload-to-data-directory")
async def upload_to_data_directory(req: UploadToDataDirectoryDto):
    if settings.METADATA_STORE_CONFIG.provider != "mlfoundry":
        raise Exception("API only supported for metadata store provider: mlfoundry")
    mlfoundry_client = mlfoundry.get_client()

    # Create a new data directory.
    dataset = mlfoundry_client.create_data_directory(
        settings.METADATA_STORE_CONFIG.config.get("ml_repo_name"), req.collection_name
    )

    artifact_repo = MlFoundryArtifactsRepository(
        artifact_identifier=ArtifactIdentifier(dataset_fqn=dataset.fqn),
        mlflow_client=mlfoundry_client.mlflow_client,
    )

    urls = artifact_repo.get_signed_urls_for_write(
        artifact_identifier=ArtifactIdentifier(dataset_fqn=dataset.fqn),
        paths=req.filepaths,
    )
    data = [url.dict() for url in urls]
    return JSONResponse(
        content={"data": data, "data_directory_fqn": dataset.fqn},
    )


@app.get("/models")
async def get_enabled_models(
    model_type: Optional[ModelType] = Query(default=None),
):
    url = f"{settings.TFY_LLM_GATEWAY_URL}/api/model/enabled{f'?model_types={model_type.value}' if model_type else ''}"
    headers = {"Authorization": f"Bearer {settings.TFY_API_KEY}"}
    try:
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
    except Exception as ex:
        raise Exception(f"Error fetching the models: {ex}") from ex
    data: dict[str, dict[str, list[dict]]] = response.json()
    enabled_models = []
    for provider_accounts in data.values():
        for models in provider_accounts.values():
            enabled_models.extend(models)

    return JSONResponse(
        content={"models": enabled_models},
    )


@app.get("/parsers")
async def get_parsers():
    parsers = []
    for key, value in PARSER_REGISTRY.items():
        parsers.append(
            {"name": key, "supported_extensions": value.get("supported_extensions")}
        )
    return parsers


@app.get("/data_loaders")
async def get_data_loaders():
    data_loaders = []
    for key, value in LOADER_REGISTRY.items():
        data_loaders.append({"name": key})
    return data_loaders


@app.get("/query_controllers")
async def get_query_controllers():
    query_controllers = []
    for key, value in QUERY_CONTROLLER_REGISTRY.items():
        query_controllers.append({"name": key})
    return query_controllers


# Register Query Controllers dynamically as FastAPI routers
for cls in QUERY_CONTROLLER_REGISTRY.values():
    router: APIRouter = cls.get_router()
    app.include_router(router)
