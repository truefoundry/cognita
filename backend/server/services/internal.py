import uuid
from typing import Optional

import mlfoundry
import requests
from fastapi import Query
from fastapi.responses import JSONResponse
from mlfoundry.artifact.truefoundry_artifact_repo import (
    ArtifactIdentifier,
    MlFoundryArtifactsRepository,
)

from backend.settings import settings
from backend.types import ModelType, UploadToDataDirectoryDto


class InternalService:
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

    def get_enabled_models(
        model_type: Optional[ModelType] = Query(default=None),
    ):
        url = f"{settings.TFY_LLM_GATEWAY_URL}/api/model/enabled"
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
                for model in models:
                    if model_type is None or model_type in model["types"]:
                        enabled_models.append(model)

        return JSONResponse(
            content={"models": enabled_models},
        )
