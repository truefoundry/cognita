from fastapi import APIRouter

from backend.server.services.data_source import DataSourceService
from backend.types import CreateDataSource

router = APIRouter(prefix="/v1/datasource", tags=["datasource"])


@router.get("/")
def list_data_source():
    return DataSourceService.list_data_sources()


@router.post("/")
def add_data_source(
    data_source: CreateDataSource,
):
    return DataSourceService.create_data_source(data_source=data_source)
