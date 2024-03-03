from typing import Optional

from fastapi import APIRouter, Query

from backend.server.services.internal import InternalService
from backend.types import ModelType, UploadToDataDirectoryDto

router = APIRouter(prefix="/v1/internal", tags=["internal"])


@router.post("/upload-to-data-directory")
async def upload_to_data_directory(req: UploadToDataDirectoryDto):
    return await InternalService.upload_to_data_directory(req)


@router.get("/models")
def get_enabled_models(
    model_type: Optional[ModelType] = Query(default=None),
):
    return InternalService.get_enabled_models(model_type)
