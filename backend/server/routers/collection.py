from fastapi import APIRouter, Path

from backend.server.services.collection import CollectionService
from backend.types import (
    AssociateDataSourceWithCollectionDto,
    CreateCollection,
    CreateDataIngestionRun,
    IngestDataToCollectionDto,
    UnassociateDataSourceWithCollectionDto,
)

router = APIRouter(prefix="/v1/collections", tags=["collections"])


@router.get("/")
def get_collections():
    """API to list all collections"""
    return CollectionService.list_collections()


@router.post("/")
def create_collection(request: CreateCollection):
    """API to create a collection"""
    return CollectionService.create_collection(request)


@router.post("/associate_data_source")
async def associate_data_source_to_collection(
    request: AssociateDataSourceWithCollectionDto,
):
    """Add a data source to the collection"""
    return CollectionService.associate_data_source_with_collection(request=request)


@router.post("/unassociate_data_source")
async def unassociate_data_source_from_collection(
    request: UnassociateDataSourceWithCollectionDto,
):
    """Remove a data source to the collection"""
    return CollectionService.unassociate_data_source_with_collection(request=request)


@router.post("/ingest")
async def ingest_data(request: IngestDataToCollectionDto):
    """Ingest data into the collection"""
    return await CollectionService.ingest_data(request=request)


@router.delete("/{collection_name}")
def delete_collection(collection_name: str = Path(title="Collection name")):
    """Delete collection given it's name"""
    return CollectionService.delete_collection(collection_name)


@router.get("/data_ingestion_run/{data_ingestion_run_name}/status")
def get_collection_status(
    data_ingestion_run_name: str = Path(title="Data Ingestion Run name"),
):
    """Get status for given data ingestion run"""
    return CollectionService.get_data_ingestion_run_status(
        data_ingestion_run_name=data_ingestion_run_name
    )
