from fastapi import APIRouter, HTTPException, Path, Request
from fastapi.responses import JSONResponse

from backend.indexer.indexer import ingest_data as ingest_data_to_collection
from backend.logger import logger
from backend.modules.metadata_store.base import BaseMetadataStore
from backend.modules.metadata_store.client import get_client
from backend.modules.model_gateway.model_gateway import model_gateway
from backend.modules.vector_db.client import VECTOR_STORE_CLIENT
from backend.types import (
    AssociateDataSourceWithCollection,
    AssociateDataSourceWithCollectionDto,
    CreateCollection,
    CreateCollectionDto,
    IngestDataToCollectionDto,
    ListDataIngestionRunsDto,
    UnassociateDataSourceWithCollectionDto,
)

router = APIRouter(prefix="/v1/collections", tags=["collections"])


@router.get("")
async def get_collections():
    """API to list all collections with details"""
    logger.debug("Listing all the collections...")
    metadata_store_client = await get_client()
    collections = await metadata_store_client.aget_collections()
    if collections is None:
        return JSONResponse(content={"collections": []})
    return JSONResponse(
        content={"collections": [obj.model_dump() for obj in collections]}
    )


@router.get("/list")
async def list_collections():
    metadata_store_client = await get_client()
    collections = await metadata_store_client.alist_collections()
    return JSONResponse(content={"collections": collections})


@router.get("/{collection_name}")
async def get_collection_by_name(collection_name: str = Path(title="Collection name")):
    """Get the collection config given its name"""
    metadata_store_client = await get_client()
    collection = await metadata_store_client.aget_collection_by_name(collection_name)
    if collection is None:
        return JSONResponse(content={"collection": []})
    return JSONResponse(content={"collection": collection.model_dump()})


@router.post("")
async def create_collection(
    collection: CreateCollectionDto,
):
    """API to create a collection"""
    logger.info(f"Creating collection {collection.name}...")
    metadata_store_client = await get_client()
    created_collection = await metadata_store_client.acreate_collection(
        collection=CreateCollection(
            name=collection.name,
            description=collection.description,
            embedder_config=collection.embedder_config,
        )
    )
    logger.info(f"Creating collection {collection.name} on vector db...")
    VECTOR_STORE_CLIENT.create_collection(
        collection_name=collection.name,
        embeddings=model_gateway.get_embedder_from_model_config(
            model_name=collection.embedder_config.name
        ),
    )
    logger.info(f"Created collection... {created_collection}")

    if collection.associated_data_sources:
        data_source_associations = [
            AssociateDataSourceWithCollection(
                data_source_fqn=data_source.data_source_fqn,
                parser_config=data_source.parser_config,
            )
            for data_source in collection.associated_data_sources
        ]

        created_collection = (
            await metadata_store_client.aassociate_data_sources_with_collection(
                collection_name=created_collection.name,
                data_source_associations=data_source_associations,
            )
        )

    return JSONResponse(
        content={"collection": created_collection.model_dump()}, status_code=201
    )


@router.post("/associate_data_source")
async def associate_data_source_to_collection(
    request: AssociateDataSourceWithCollectionDto,
):
    """Add a data source to the collection"""
    metadata_store_client = await get_client()
    collection = await metadata_store_client.aassociate_data_sources_with_collection(
        collection_name=request.collection_name,
        data_source_associations=[
            AssociateDataSourceWithCollection(
                data_source_fqn=request.data_source_fqn,
                parser_config=request.parser_config,
            )
        ],
    )
    return JSONResponse(content={"collection": collection.model_dump()})


@router.post("/unassociate_data_source")
async def unassociate_data_source_from_collection(
    request: UnassociateDataSourceWithCollectionDto,
):
    """Remove a data source to the collection"""
    metadata_store_client = await get_client()
    collection = await metadata_store_client.aunassociate_data_source_with_collection(
        collection_name=request.collection_name,
        data_source_fqn=request.data_source_fqn,
    )
    return JSONResponse(content={"collection": collection.model_dump()})


@router.post("/ingest")
async def ingest_data(
    ingest_data_to_collection_dto: IngestDataToCollectionDto, request: Request
):
    """Ingest data into the collection"""
    try:
        process_pool = request.app.state.process_pool
    except AttributeError:
        process_pool = None
    return await ingest_data_to_collection(
        ingest_data_to_collection_dto, pool=process_pool
    )


@router.delete("/{collection_name}")
async def delete_collection(collection_name: str = Path(title="Collection name")):
    """Delete collection given its name"""
    metadata_store_client: BaseMetadataStore = await get_client()
    await metadata_store_client.adelete_collection(collection_name, include_runs=True)
    VECTOR_STORE_CLIENT.delete_collection(collection_name=collection_name)
    return JSONResponse(content={"deleted": True})


@router.post("/data_ingestion_runs/list")
async def list_data_ingestion_runs(request: ListDataIngestionRunsDto):
    metadata_store_client: BaseMetadataStore = await get_client()
    data_ingestion_runs = await metadata_store_client.aget_data_ingestion_runs(
        request.collection_name, request.data_source_fqn
    )
    return JSONResponse(
        content={
            "data_ingestion_runs": [obj.model_dump() for obj in data_ingestion_runs]
        }
    )


@router.get("/data_ingestion_runs/{data_ingestion_run_name}/status")
async def get_collection_status(
    data_ingestion_run_name: str = Path(title="Data Ingestion Run name"),
):
    """Get status for given data ingestion run"""
    metadata_store_client: BaseMetadataStore = await get_client()
    data_ingestion_run = await metadata_store_client.aget_data_ingestion_run(
        data_ingestion_run_name=data_ingestion_run_name, no_cache=True
    )
    if data_ingestion_run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Data ingestion run {data_ingestion_run_name} not found",
        )

    return JSONResponse(
        content={
            "status": data_ingestion_run.status.value,
            "message": f"Data ingestion job run {data_ingestion_run.name} in {data_ingestion_run.status.value}. Check logs for more details.",
        }
    )
