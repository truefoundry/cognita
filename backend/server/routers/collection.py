from fastapi import APIRouter, Path

from backend.server.services.collection import CollectionService
from backend.types import CreateCollection, CreateDataIngestionRun

router = APIRouter(prefix="/v1/collections", tags=["collections"])


@router.get("/")
def get_collections():
    return CollectionService.list_collections()


@router.post("/")
def create_collection(request: CreateCollection):
    return CollectionService.create_collection(request)


@router.post("/data_ingestion_run")
async def ingest_data(data_ingestion_run: CreateDataIngestionRun):
    return await CollectionService.ingest_data(data_ingestion_run=data_ingestion_run)


@router.delete("/{collection_name}")
def delete_collection(collection_name: str = Path(title="Collection name")):
    return CollectionService.delete_collection(collection_name)


@router.get("/data_ingestion_run/{data_ingestion_run_name}/status")
def get_collection_status(
    data_ingestion_run_name: str = Path(title="Data Ingestion Run name"),
):
    return CollectionService.get_data_ingestion_run_status(
        data_ingestion_run_name=data_ingestion_run_name
    )
