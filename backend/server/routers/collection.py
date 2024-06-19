from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse

from backend.indexer.indexer import ingest_data as ingest_data_to_collection
from backend.logger import logger
from backend.modules.embedder.embedder import get_embedder
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
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
from backend.modules.model_gateway.model_gateway import model_gateway

router = APIRouter(prefix="/v1/collections", tags=["collections"])


@router.get("")
# TODO: Keep additional route until FE is updated
@router.get("/")
def get_collections():
    """API to list all collections with details"""
    try:
        logger.debug("Listing all the collections...")
        collections = METADATA_STORE_CLIENT.get_collections()
        if collections is None:
            return JSONResponse(content={"collections": []})
        return JSONResponse(
            content={"collections": [obj.dict() for obj in collections]}
        )
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.get("/list")
async def list_collections():
    try:
        collections = await METADATA_STORE_CLIENT.list_collections()
        return JSONResponse(content={"collections": collections})
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.get("/{collection_name}")
def get_collection_by_name(collection_name: str = Path(title="Collection name")):
    """Get the collection config given it's name"""
    try:
        collection = METADATA_STORE_CLIENT.get_collection_by_name(collection_name)
        if collection is None:
            return JSONResponse(content={"collection": []})
        return JSONResponse(content={"collection": collection.dict()})
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("")
# TODO: Keep additional route until FE is updated
@router.post("/")
def create_collection(collection: CreateCollectionDto):
    """API to create a collection"""
    try:
        logger.debug(f"Creating collection {collection.name}...")
        created_collection = METADATA_STORE_CLIENT.create_collection(
            collection=CreateCollection(
                name=collection.name,
                description=collection.description,
                embedder_config=collection.embedder_config,
            )
        )

        VECTOR_STORE_CLIENT.create_collection(
            collection_name=collection.name,
            embeddings=model_gateway.get_embedder_from_model_config(
                model_name=collection.embedder_config.model_config.name
            ),
            # embeddings=get_embedder(collection.embedder_config),
        )
        if collection.associated_data_sources:
            for data_source in collection.associated_data_sources:
                METADATA_STORE_CLIENT.associate_data_source_with_collection(
                    collection_name=created_collection.name,
                    data_source_association=AssociateDataSourceWithCollection(
                        data_source_fqn=data_source.data_source_fqn,
                        parser_config=data_source.parser_config,
                    ),
                )
            created_collection = METADATA_STORE_CLIENT.get_collection_by_name(
                collection_name=created_collection.name
            )
        return JSONResponse(
            content={"collection": created_collection.dict()}, status_code=201
        )
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("/associate_data_source")
async def associate_data_source_to_collection(
    request: AssociateDataSourceWithCollectionDto,
):
    """Add a data source to the collection"""
    try:
        collection = METADATA_STORE_CLIENT.associate_data_source_with_collection(
            collection_name=request.collection_name,
            data_source_association=AssociateDataSourceWithCollection(
                data_source_fqn=request.data_source_fqn,
                parser_config=request.parser_config,
            ),
        )
        return JSONResponse(content={"collection": collection.dict()})
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("/unassociate_data_source")
async def unassociate_data_source_from_collection(
    request: UnassociateDataSourceWithCollectionDto,
):
    """Remove a data source to the collection"""
    try:
        collection = METADATA_STORE_CLIENT.unassociate_data_source_with_collection(
            collection_name=request.collection_name,
            data_source_fqn=request.data_source_fqn,
        )
        return JSONResponse(content={"collection": collection.dict()})
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("/ingest")
async def ingest_data(request: IngestDataToCollectionDto):
    """Ingest data into the collection"""
    try:
        return await ingest_data_to_collection(request)
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.delete("/{collection_name}")
def delete_collection(collection_name: str = Path(title="Collection name")):
    """Delete collection given it's name"""
    try:
        VECTOR_STORE_CLIENT.delete_collection(collection_name=collection_name)
        METADATA_STORE_CLIENT.delete_collection(collection_name, include_runs=True)
        return JSONResponse(content={"deleted": True})
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("/data_ingestion_runs/list")
def list_data_ingestion_runs(request: ListDataIngestionRunsDto):
    data_ingestion_runs = METADATA_STORE_CLIENT.get_data_ingestion_runs(
        request.collection_name, request.data_source_fqn
    )
    return JSONResponse(
        content={"data_ingestion_runs": [obj.dict() for obj in data_ingestion_runs]}
    )


@router.get("/data_ingestion_runs/{data_ingestion_run_name}/status")
def get_collection_status(
    data_ingestion_run_name: str = Path(title="Data Ingestion Run name"),
):
    """Get status for given data ingestion run"""
    data_ingestion_run = METADATA_STORE_CLIENT.get_data_ingestion_run(
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
