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

import backend.server.service as service
from backend.modules import query_controllers
from backend.modules.dataloaders.loader import LOADER_REGISTRY
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
    return await service.get_collections()


@app.post("/collections")
async def create_collection(request: CreateCollection):
    return await service.create_collection(request)


@app.post("/collections/{collection_name}/upsert_docs")
async def upsert_documents_to_collection(
    request: AddDocuments, collection_name: str = Path(title="Collection name")
):
    return await service.upsert_documents_to_collection(request, collection_name)


@app.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str = Path(title="Collection name")):
    return await service.delete_collection(collection_name)


@app.get("/collections/{collection_name}/status")
async def get_collection_status(collection_name: str = Path(title="Collection name")):
    return await service.get_collection_status(collection_name)

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
