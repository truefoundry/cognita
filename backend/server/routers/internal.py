import os
import uuid
from types import SimpleNamespace
from typing import Optional

import requests
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from truefoundry import ml
from truefoundry.ml import DataDirectory

from backend.logger import logger
from backend.server.routers.data_source import add_data_source
from backend.settings import settings
from backend.types import (
    CreateDataSource,
    EmbedderConfig,
    LLMConfig,
    ModelType,
    UploadToDataDirectoryDto,
)

router = APIRouter(prefix="/v1/internal", tags=["internal"])


@router.post("/upload-to-docker-directory")
async def upload_to_docker_directory(req: UploadToDataDirectoryDto):
    """This function creates a folder within `/volumes/user_data/` given by the name req.upload_name in the docker volume and add symlinks of the files in the folder."""
    if settings.LOCAL == False:
        return JSONResponse(
            content={"error": "API only supported for local docker environment"},
            status_code=500,
        )
    try:
        # Create a folder with the name req.upload_name in the docker volume.
        folder_path = os.path.abspath(f"./volumes/user_data/{req.upload_name}")
        os.makedirs(folder_path, exist_ok=False)

        # Create symlinks of the files in the folder.
        for filepath in req.filepaths:
            filename = os.path.basename(filepath)
            symlink_path = f"{folder_path}/{filename}"
            os.symlink(filepath, symlink_path)

        data_source = CreateDataSource(
            type="localdir",
            uri=folder_path,
        )

        # Add the data source to the metadata store.
        return await add_data_source(data_source)
    except Exception as ex:
        return JSONResponse(
            content={"error": f"Error uploading files to docker directory: {ex}"},
            status_code=500,
        )


@router.post("/upload-to-data-directory")
async def upload_to_data_directory(req: UploadToDataDirectoryDto):
    if settings.METADATA_STORE_CONFIG.provider != "truefoundry":
        raise Exception("API only supported for metadata store provider: truefoundry")
    try:
        truefoundry_client = ml.get_client()

        # Create a new data directory.
        dataset = truefoundry_client.create_data_directory(
            settings.METADATA_STORE_CONFIG.config.get("ml_repo_name"),
            req.upload_name,
        )

        _artifacts_repo = DataDirectory.from_fqn(fqn=dataset.fqn)._get_artifacts_repo()

        urls = _artifacts_repo.get_signed_urls_for_write(
            artifact_identifier=SimpleNamespace(
                artifact_version_id=None, dataset_fqn=dataset.fqn
            ),
            paths=req.filepaths,
        )

        data = [url.dict() for url in urls]
        return JSONResponse(
            content={"data": data, "data_directory_fqn": dataset.fqn},
        )
    except Exception as ex:
        raise Exception(f"Error uploading files to data directory: {ex}")


@router.get("/models")
def get_enabled_models(
    model_type: Optional[ModelType] = Query(default=None),
):
    enabled_models = []

    # Local Embedding models
    if model_type == ModelType.embedding:
        if settings.EMBEDDING_SVC_URL:
            try:
                url = f"{settings.EMBEDDING_SVC_URL.rstrip('/')}/models"
                response = requests.get(url=url).json()
                for models in response["data"]:
                    if "rerank" not in models["id"]:
                        enabled_models.append(
                            EmbedderConfig(
                                provider="infinity",
                                config={"model": models["id"]},
                            ).dict()
                        )
            except Exception as ex:
                logger.error(f"Error fetching embedding models: {ex}")

    # Local LLM models
    if model_type == ModelType.chat:
        if settings.OLLAMA_URL:
            try:
                # OLLAMA models
                url = f"{settings.OLLAMA_URL.rstrip('/')}/api/tags"
                response = requests.get(url=url)
                data = response.json()
                for model in data["models"]:
                    enabled_models.append(
                        LLMConfig(
                            name=f"ollama/{model['model']}",
                            parameters={"temparature": 0.1},
                            provider="ollama",
                        ).dict()
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
    if settings.TFY_API_KEY:
        try:
            url = (
                f"{settings.TFY_HOST.rstrip('/')}/api/svc/v1/llm-gateway/model/enabled"
            )
            headers = {"Authorization": f"Bearer {settings.TFY_API_KEY}"}
            response = requests.get(url=url, headers=headers)
            response.raise_for_status()

            data: dict[str, dict[str, list[dict]]] = response.json()

            for provider_accounts in data.values():
                for models in provider_accounts.values():
                    for model in models:
                        if model_type is None or model_type in model["types"]:
                            if model_type == ModelType.embedding:
                                enabled_models.append(
                                    EmbedderConfig(
                                        provider="truefoundry",
                                        config={"model": model["model_fqn"]},
                                    ).dict()
                                )

                            elif model_type == ModelType.chat:
                                enabled_models.append(
                                    LLMConfig(
                                        name=model["model_fqn"],
                                        parameters={"temparature": 0.1},
                                        provider="truefoundry",
                                    ).dict()
                                )
                            elif model_type == ModelType.completion:
                                enabled_models.append(
                                    LLMConfig(
                                        name=model["model_fqn"],
                                        parameters={"temparature": 0.9},
                                        provider="truefoundry",
                                    ).dict()
                                )
        except Exception as ex:
            logger.error(f"Error fetching openai models: {ex}")
    return JSONResponse(
        content={"models": enabled_models},
    )
