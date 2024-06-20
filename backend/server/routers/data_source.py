import asyncio
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse

from backend.logger import logger
from backend.modules.metadata_store.client import get_client
from backend.modules.metadata_store.truefoundry import TrueFoundry
from backend.types import CreateDataSource

router = APIRouter(prefix="/v1/data_source", tags=["data_source"])


@router.get("")
async def get_data_source():
    """Get data sources"""
    try:
        client = await get_client()
        if isinstance(client, TrueFoundry):
            loop = asyncio.get_event_loop()
            data_sources = await loop.run_in_executor(None, client.get_data_sources)
        else:
            data_sources = await client.get_data_sources()
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
        client = await get_client()
        if isinstance(client, TrueFoundry):
            loop = asyncio.get_event_loop()
            data_sources = await loop.run_in_executor(None, client.list_data_sources)
        else:
            data_sources = await client.list_data_sources()
        return JSONResponse(content={"data_sources": data_sources})
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("")
async def add_data_source(
    data_source: CreateDataSource,
):
    """Create a data source for the given collection"""
    try:
        client = await get_client()
        if isinstance(client, TrueFoundry):
            loop = asyncio.get_event_loop()
            created_data_source = await loop.run_in_executor(
                None, client.create_data_source, data_source
            )
        else:
            created_data_source = await client.create_data_source(
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


@router.delete("/delete")
async def delete_data_source(data_source_fqn: str):
    """Delete a data source"""
    decoded_data_source_fqn = unquote(data_source_fqn)
    logger.info(f"Deleting data source: {decoded_data_source_fqn}")
    try:
        client = await get_client()
        if isinstance(client, TrueFoundry):
            raise HTTPException(
                status_code=501,
                detail="Truefoundry Metadatastore does not support delete data source",
            )
        else:
            await client.delete_data_source(decoded_data_source_fqn)
            return JSONResponse(content={"deleted": True})
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))
