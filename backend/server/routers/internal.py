from typing import Optional
import uuid
import requests
from backend.logger import logger
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import mlfoundry
from mlfoundry.artifact.truefoundry_artifact_repo import (
    ArtifactIdentifier,
    MlFoundryArtifactsRepository,
)
from backend.settings import settings
from backend.types import ModelType, UploadToDataDirectoryDto

router = APIRouter(prefix="/v1/internal", tags=["internal"])


@router.post("/upload-to-data-directory")
async def upload_to_data_directory(req: UploadToDataDirectoryDto):
    if settings.METADATA_STORE_CONFIG.provider != "mlfoundry":
        raise Exception("API only supported for metadata store provider: mlfoundry")
    mlfoundry_client = mlfoundry.get_client()

    # Create a new data directory.
    dataset = mlfoundry_client.create_data_directory(
        settings.METADATA_STORE_CONFIG.config.get("ml_repo_name"),
        str(uuid.uuid4()),
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


@router.get("/models")
def get_enabled_models(
    model_type: Optional[ModelType] = Query(default=None),
):
    enabled_models = []

    # Local Embedding models 
    if model_type == ModelType.embedding:
        if settings.LOCAL:
            enabled_models.append(
                {
                    "name": "mxbai-embed-large-v1",
                    "provider": "mixedbread-ai",
                    "types": ["embedding"],
                    "backend_provider": "mixedbread",
                    "model_fqn": "mixedbread-ai/mxbai-embed-large-v1",
                }
            )

    # Local LLM models
    if model_type == ModelType.chat:
        if settings.LOCAL:
            try:
                # OLLAMA models
                url = f"{settings.OLLAMA_URL}/api/tags"
                response = requests.get(url=url)
                data = response.json()
                for model in data["models"]:
                    enabled_models.append(
                        {
                            "name": model["name"],
                            "provider": "ollama",
                            "types": ["chat"],
                            "backend_provider": "ollama",
                            "model_fqn": f"ollama/{model['model']}",
                        }
                    )
            except Exception as ex:
                logger.error(f"Error fetching ollama models: {ex}")

            # Similarly u can add other local models fetch from api

        if settings.OPENAI_API_KEY:
            try:
                # OpenAI models
                url = "https://api.openai.com/v1/models"
                headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                response = requests.get(url=url)
                data = response.json()
                # TODO: Add the models to the enabled_models list
            except Exception as ex:
                logger.error(f"Error fetching openai models: {ex}")

    # Models from the llm gateway
    url = f"{settings.TFY_HOST}/api/svc/v1/llm-gateway/model/enabled"
    headers = {"Authorization": f"Bearer {settings.TFY_API_KEY}"}
    try:
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
    except Exception as ex:
        raise Exception(f"Error fetching the models: {ex}") from ex
    data: dict[str, dict[str, list[dict]]] = response.json()

    for provider_accounts in data.values():
        for models in provider_accounts.values():
            for model in models:
                if model_type is None or model_type in model["types"]:
                    # for models from llm gateway backend_provider is truefoundry
                    model["backend_provider"] = "truefoundry"
                    enabled_models.append(model)

    return JSONResponse(
        content={"models": enabled_models},
    )
