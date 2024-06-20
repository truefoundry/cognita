from http.client import HTTPException
import uuid
from types import SimpleNamespace
from typing import Optional

import requests
from backend.modules.model_gateway.model_gateway import model_gateway
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from truefoundry import ml
from truefoundry.ml import DataDirectory

from backend.logger import logger
from backend.settings import settings
from backend.types import ModelType, UploadToDataDirectoryDto

router = APIRouter(prefix="/v1/internal", tags=["internal"])


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
    if model_type == ModelType.embedding:
        enabled_models = model_gateway.get_embedding_models()
    elif model_type == ModelType.chat:
        enabled_models = model_gateway.get_llm_models()
    else:
        raise HTTPException(
                status_code=400,
                detail=f"Invalid model type: {model_type}",
            )
    
    return JSONResponse(
        content={"models": enabled_models},
    )