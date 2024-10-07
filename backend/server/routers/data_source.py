from contextlib import asynccontextmanager
from urllib.parse import unquote

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from backend.logger import logger
from backend.modules.metadata_store.base import BaseMetadataStore
from backend.modules.metadata_store.client import get_client
from backend.types import CreateDataSource

router = APIRouter(prefix="/v1/data_source", tags=["data_source"])


@router.get("")
async def get_data_source():
    """Get data sources"""
    metadata_store_client = await get_client()
    data_sources = await metadata_store_client.aget_data_sources()
    return JSONResponse(
        content={"data_sources": [obj.model_dump() for obj in data_sources]}
    )


@router.get("/list")
async def list_data_sources():
    """Get data sources"""
    metadata_store_client = await get_client()
    data_sources = await metadata_store_client.alist_data_sources()
    return JSONResponse(content={"data_sources": data_sources})


@router.post("")
async def add_data_source(
    data_source: CreateDataSource,
):
    """Create a data source for the given collection"""
    metadata_store_client = await get_client()
    created_data_source = await metadata_store_client.acreate_data_source(
        data_source=data_source
    )
    return JSONResponse(
        content={"data_source": created_data_source.model_dump()}, status_code=201
    )


@router.delete("/delete")
async def delete_data_source(data_source_fqn: str):
    """Delete a data source"""
    metadata_store_client = await get_client()
    await metadata_store_client.adelete_data_source(unquote(data_source_fqn))
    return JSONResponse(content={"deleted": True})
