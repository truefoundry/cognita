from fastapi import APIRouter, Path
from fastapi.responses import JSONResponse

from backend.logger import logger
from backend.modules.metadata_store.base import BaseMetadataStore
from backend.modules.metadata_store.client import get_client
from backend.types import CreateRagApplication

router = APIRouter(prefix="/v1/apps", tags=["apps"])


@router.post("")
async def register_rag_app(
    rag_app: CreateRagApplication,
):
    """Create a rag app"""
    logger.info(f"Creating rag app: {rag_app}")
    metadata_store_client: BaseMetadataStore = await get_client()
    created_rag_app = await metadata_store_client.acreate_rag_app(rag_app)
    return JSONResponse(
        content={"rag_app": created_rag_app.model_dump()}, status_code=201
    )


@router.get("/list")
async def list_rag_apps():
    """Get rag apps"""
    metadata_store_client: BaseMetadataStore = await get_client()
    rag_apps = await metadata_store_client.alist_rag_apps()
    return JSONResponse(content={"rag_apps": rag_apps})


@router.get("/{app_name}")
async def get_rag_app_by_name(
    app_name: str = Path(title="App name"),
):
    """Get the rag app config given its name"""
    metadata_store_client: BaseMetadataStore = await get_client()
    rag_app = await metadata_store_client.aget_rag_app(app_name)
    if rag_app is None:
        return JSONResponse(content={"rag_app": []})
    return JSONResponse(content={"rag_app": rag_app.model_dump()})


@router.delete("/{app_name}")
async def delete_rag_app(app_name: str = Path(title="App name")):
    """Delete the rag app config given its name"""
    metadata_store_client: BaseMetadataStore = await get_client()
    await metadata_store_client.adelete_rag_app(app_name)
    return JSONResponse(content={"deleted": True})
