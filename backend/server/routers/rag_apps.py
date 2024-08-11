from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse

from backend.logger import logger
from backend.modules.metadata_store.client import get_client
from backend.types import CreateRagApplication

router = APIRouter(prefix="/v1/apps", tags=["apps"])


@router.post("")
async def register_rag_app(
    rag_app: CreateRagApplication,
):
    """Create a rag app"""
    try:
        logger.info(f"Creating rag app: {rag_app}")
        client = await get_client()
        created_rag_app = await client.acreate_rag_app(rag_app)
        return JSONResponse(
            content={"rag_app": created_rag_app.model_dump()}, status_code=201
        )
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception("Failed to add rag app")
        raise HTTPException(status_code=500, detail=str(exp))


@router.get("/list")
async def list_rag_apps():
    """Get rag apps"""
    try:
        client = await get_client()
        rag_apps = await client.alist_rag_apps()
        return JSONResponse(content={"rag_apps": rag_apps})
    except Exception as exp:
        logger.exception("Failed to get rag apps")
        raise HTTPException(status_code=500, detail=str(exp))


@router.get("/{app_name}")
async def get_rag_app_by_name(app_name: str = Path(title="App name")):
    """Get the rag app config given its name"""
    try:
        client = await get_client()
        rag_app = await client.aget_rag_app(app_name)
        if rag_app is None:
            return JSONResponse(content={"rag_app": []})
        return JSONResponse(content={"rag_app": rag_app.model_dump()})
    except HTTPException as exp:
        raise exp


@router.delete("/{app_name}")
async def delete_rag_app(app_name: str = Path(title="App name")):
    """Delete the rag app config given its name"""
    try:
        client = await get_client()
        await client.adelete_rag_app(app_name)
        return JSONResponse(content={"deleted": True})
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception("Failed to delete rag app")
        raise HTTPException(status_code=500, detail=str(exp))
