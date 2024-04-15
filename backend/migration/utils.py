from typing import Dict

from qdrant_client._pydantic_compat import to_dict
from qdrant_client.client_base import QdrantBase
from qdrant_client.http import models
import requests

from backend.logger import logger
import warnings

def get_collection(backend_url: str, collection_name: str, type: str = "source"):
    
    # fetch collection from source
    collections = None
    with requests.get(f"{backend_url.rstrip('/')}/v1/collections/") as r:
        collections = r.json().get("collections")

    if type == "source" and not collections:
        raise Exception("No collections found at source")

    fetched_collection = None
    for collection in collections:
        if collection.get("name") == collection_name:
            fetched_collection = collection
            break

    if type == "source" and fetched_collection is None:
        raise Exception(f"Collection {collection_name} not found at source")
    
    return fetched_collection

def migrate(
    source_client: QdrantBase,
    dest_client: QdrantBase,
    source_collection_name: str,
    destination_collection_name: str,
    batch_size: int = 100,
    same_qdrant: bool = False,
) -> None:
    """
    Migrate collections from source client to destination client

    Args:
        source_client (QdrantBase): Source client
        dest_client (QdrantBase): Destination client
        source_collection_name (str): source collection names to migrate.
        destination_collection_name (str): destination collection name.
        recreate_on_collision (bool, optional): If True - recreate collection if it exists, otherwise
            raise ValueError.
        batch_size (int, optional): Batch size for scrolling and uploading vectors. Defaults to 100.
    """
    if _has_custom_shards(source_client, source_collection_name):
        raise ValueError("Migration of collections with custom shards is not supported yet")
    
    if source_collection_name == destination_collection_name and same_qdrant:
        destination_collection_name = destination_collection_name + "copy"
        logger.debug(f"Destination collection name is same as source collection name. Renaming destination collection to {destination_collection_name}")

    _recreate_collection(
        source_client=source_client, 
        dest_client=dest_client, 
        source_collection_name=source_collection_name, 
        destination_collection_name=destination_collection_name
    )
    _migrate_collection(
        source_client=source_client, 
        dest_client=dest_client, 
        source_collection_name=source_collection_name, 
        destination_collection_name=destination_collection_name,
        batch_size=batch_size
    )


def _has_custom_shards(source_client: QdrantBase, collection_name: str) -> bool:
    collection_info = source_client.get_collection(collection_name)
    return (
        getattr(collection_info.config.params, "sharding_method", None)
        == models.ShardingMethod.CUSTOM
    )

def _recreate_collection(
    source_client: QdrantBase,
    dest_client: QdrantBase,
    source_collection_name: str,
    destination_collection_name: str,

) -> None:
    src_collection_info = source_client.get_collection(source_collection_name)
    src_config = src_collection_info.config
    src_payload_schema = src_collection_info.payload_schema

    dest_client.recreate_collection(
        destination_collection_name,
        vectors_config=src_config.params.vectors,
        sparse_vectors_config=src_config.params.sparse_vectors,
        shard_number=src_config.params.shard_number,
        replication_factor=src_config.params.replication_factor,
        write_consistency_factor=src_config.params.write_consistency_factor,
        on_disk_payload=src_config.params.on_disk_payload,
        hnsw_config=models.HnswConfigDiff(**to_dict(src_config.hnsw_config)),
        optimizers_config=models.OptimizersConfigDiff(**to_dict(src_config.optimizer_config)),
        wal_config=models.WalConfigDiff(**to_dict(src_config.wal_config)),
        quantization_config=src_config.quantization_config,
    )

    _recreate_payload_schema(dest_client, destination_collection_name, src_payload_schema)


def _recreate_payload_schema(
    dest_client: QdrantBase,
    collection_name: str,
    payload_schema: Dict[str, models.PayloadIndexInfo],
) -> None:
    for field_name, field_info in payload_schema.items():
        dest_client.create_payload_index(
            collection_name,
            field_name=field_name,
            field_schema=field_info.data_type if field_info.params is None else field_info.params,
        )


def _migrate_collection(
    source_client: QdrantBase,
    dest_client: QdrantBase,
    source_collection_name: str,
    destination_collection_name: str,
    batch_size: int = 100,
) -> None:
    """Migrate collection from source client to destination client

    Args:
        source_collection_name (str): Collection name of source
        destination_collection_name (str): Collection name of destination
        source_client (QdrantBase): Source client
        dest_client (QdrantBase): Destination client
        batch_size (int, optional): Batch size for scrolling and uploading vectors. Defaults to 100.
    """
    records, next_offset = source_client.scroll(source_collection_name, limit=2, with_vectors=True)
    dest_client.upload_points(destination_collection_name, records, wait=True)  # type: ignore

    # upload_records has been deprecated due to the usage of models.Record; models.Record has been deprecated as a
    # structure for uploading due to a `shard_key` field, and now is used only as a result structure.
    # since shard_keys are not supported in migration, we can safely type ignore here and use Records for uploading
    while next_offset is not None:
        records, next_offset = source_client.scroll(
            source_collection_name, offset=next_offset, limit=batch_size, with_vectors=True
        )
        dest_client.upload_points(destination_collection_name, records, wait=True)
    source_client_vectors_count = source_client.get_collection(source_collection_name).vectors_count
    dest_client_vectors_count = dest_client.get_collection(destination_collection_name).vectors_count

    if source_client_vectors_count != dest_client_vectors_count:
        warnings.warn(
            f"Migration completed, but vector counts are not equal, source vectors count: {source_client_vectors_count}, dest vectors count: {dest_client_vectors_count}. You may want to delete the destination collection and try again."
        )

