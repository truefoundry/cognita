import os
import shutil
from contextlib import asynccontextmanager
from urllib.parse import unquote

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from backend.logger import logger
from backend.modules.metadata_store.base import BaseMetadataStore
from backend.modules.metadata_store.client import get_client
from backend.settings import settings
from backend.types import CreateDataSource
from backend.utils import TRUEFOUNDRY_CLIENT

router = APIRouter(prefix="/v1/data_source", tags=["data_source"])


@router.get("")
async def get_data_source():
    """Get data sources"""
    metadata_store_client: BaseMetadataStore = await get_client()
    data_sources = await metadata_store_client.aget_data_sources()
    return JSONResponse(
        content={"data_sources": [obj.model_dump() for obj in data_sources]}
    )


@router.get("/list")
async def list_data_sources():
    """Get data sources"""
    metadata_store_client: BaseMetadataStore = await get_client()
    data_sources = await metadata_store_client.alist_data_sources()
    return JSONResponse(content={"data_sources": data_sources})


@router.post("")
async def add_data_source(data_source: CreateDataSource):
    """Create a data source for the given collection"""
    metadata_store_client: BaseMetadataStore = await get_client()
    created_data_source = await metadata_store_client.acreate_data_source(
        data_source=data_source
    )
    return JSONResponse(
        content={"data_source": created_data_source.model_dump()}, status_code=201
    )


@router.delete("/delete")
async def delete_data_source(
    data_source_fqn: str,
):
    """Delete a data source"""
    metadata_store_client: BaseMetadataStore = await get_client()
    deleted_data_source = await metadata_store_client.adelete_data_source(
        unquote(data_source_fqn)
    )

    # Upon successful deletion of the data source, delete the data from `/users_data` directory if data source is of type `localdir`
    if deleted_data_source.type == "localdir":
        data_source_uri = deleted_data_source.uri
        # data_source_uri is of the form: `/app/users_data/folder_name`
        folder_name = data_source_uri.split("/")[-1]
        folder_path = os.path.join(settings.LOCAL_DATA_DIRECTORY, folder_name)
        logger.info(
            f"Deleting folder: {folder_path}, path exists: {os.path.exists(folder_path)}"
        )
        # If the folder does not exist, skip deleting it
        if not os.path.exists(folder_path):
            logger.error(f"Folder does not exist: {folder_path}")
        else:
            # Delete the folder
            shutil.rmtree(folder_path)
            logger.info(f"Deleted folder: {folder_path}")

    if "truefoundry" in deleted_data_source.fqn:
        # Delete the data directory from truefoundry data directory
        try:
            # When the data source is of type `truefoundry`, the uri contains the fqn of the data directory
            # Fetch the data directory object
            data_directory = TRUEFOUNDRY_CLIENT.get_data_directory_by_fqn(
                deleted_data_source.uri
            )
            # Delete the data directory
            data_directory.delete(delete_contents=True)
            logger.info(f"Deleted data directory: {data_directory}")
        except Exception as e:
            logger.exception(f"Failed to delete data directory: {e}")

    return JSONResponse(content={"deleted": True})
