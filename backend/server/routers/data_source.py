from fastapi import APIRouter

from backend.server.services.data_source import DataSourceService
from backend.types import CreateDataSource

router = APIRouter(prefix="/v1/data_source", tags=["data_source"])


@router.get("/")
def list_data_source():
    """Get data sources"""
    return DataSourceService.list_data_sources()


@router.post("/")
def add_data_source(
    data_source: CreateDataSource,
):
    """Create a data source for the given collection"""
    return DataSourceService.create_data_source(data_source=data_source)
