from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.logger import logger
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.types import CreateDataSource

router = APIRouter(prefix="/v1/data_source", tags=["data_source"])


@router.get("/")
def get_data_source():
    """Get data sources"""
    try:
        data_sources = METADATA_STORE_CLIENT.get_data_sources()
        return JSONResponse(
            content={"data_sources": [obj.dict() for obj in data_sources]}
        )
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.get("/list")
async def list_data_sources():
    """Get data sources"""
    try:
        data_sources = await METADATA_STORE_CLIENT.list_data_sources()
        return JSONResponse(content={"data_sources": data_sources})
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("/")
def add_data_source(
    data_source: CreateDataSource,
):
    """Create a data source for the given collection"""
    try:
        created_data_source = METADATA_STORE_CLIENT.create_data_source(
            data_source=data_source
        )
        return JSONResponse(
            content={"data_source": created_data_source.dict()}, status_code=201
        )
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))
