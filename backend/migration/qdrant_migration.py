# This script migrates qdrant collection from one environment to another
# Environment can be same qdrant instance or different qdrant instance
"""
How to run:

python -m backend.migration.qdrant_migration \
--source_backend_url http://localhost:8000 \
--source_qdrant_url https://ps-qdrant-prathamesh-ws.devtest.truefoundry.tech \
--source_collection_name creditcard \
--destination_backend_url http://localhost:8000 \
--destination_qdrant_url https://ps-qdrant-prathamesh-ws.devtest.truefoundry.tech \
--destination_collection_name creditcopy

Add --source_prefix & --destination_prefix if qdrant instance has prefix enabled
"""


import requests, argparse

from backend.types import CreateCollectionDto, AssociateDataSourceWithCollection
from backend.logger import logger

from qdrant_client import QdrantClient
from backend.migration.utils import migrate




def migrate_collection(
    source_backend_url: str,
    source_collection_name: str,
    source_qdrant_url: str,
    source_prefix: str,
    destination_backend_url: str,
    destination_collection_name: str,  
    destination_qdrant_url: str,
    destination_prefix: str, 
):
    # fetch collection from source
    collections = None
    with requests.get(f"{source_backend_url.rstrip('/')}/v1/collections/") as r:
        collections = r.json().get("collections")

    if not collections:
        raise Exception("No collections found")

    fetched_collection = None
    for collection in collections:
        if collection.get("name") == source_collection_name:
            fetched_collection = collection
            break

    if fetched_collection is None:
        raise Exception(f"Collection {source_collection_name} not found")

    logger.debug(f"Source collection found '{fetched_collection.get('name')}' ")


    try:
        # prepare collection to be created at destination
        dest_collection = CreateCollectionDto(
            name=destination_collection_name,
            description=fetched_collection.get("description", f"Collection cloned from {source_collection_name}"),
            embedder_config=fetched_collection.get("embedder_config"),
            associated_data_sources=[
                AssociateDataSourceWithCollection(
                    data_source_fqn=value.get("data_source_fqn"),
                    parser_config=value.get("parser_config"),
                ) for _, value in fetched_collection.get("associated_data_sources").items()
            ]
        ).dict()

        
        logger.debug(f"Creating '{dest_collection.get('name')}' collection at destination")
        # create collection at destination
        with requests.post(
                url = f"{destination_backend_url.rstrip('/')}/v1/collections/",
                json = dest_collection
            ) as r:
            r.raise_for_status()
            logger.debug("Collection entry created: ", r.json())

        logger.debug("Collection migration started...")

        source_qdrant_client = QdrantClient(
            url=source_qdrant_url,
            port=443 if source_qdrant_url.startswith("https://") else 6333,
            prefer_grpc= False if source_qdrant_url.startswith("https://") else True,
            prefix=source_prefix,
        )

        destination_qdrant_client = QdrantClient(
            url=destination_qdrant_url,
            port=443 if destination_qdrant_url.startswith("https://") else 6333,
            prefer_grpc= False if destination_qdrant_url.startswith("https://") else True,
            prefix=destination_prefix,
        )

        migrate(
            source_client = source_qdrant_client,
            dest_client = destination_qdrant_client,
            source_collection_name = source_collection_name,
            destination_collection_name = destination_collection_name,
            batch_size = 100,
            same_qdrant= (source_qdrant_url == destination_qdrant_url) and  (source_prefix == destination_prefix)
        )

    except Exception as e:
        with requests.delete(
            url = f"{destination_backend_url.rstrip('/')}/v1/collections/{destination_collection_name}",
            json = dest_collection
        ) as r:
            logger.debug("Destination collection entry deleted: ", r.json())    
        raise e
        
    logger.debug(f"Collection '{source_collection_name}' migrated to '{destination_collection_name}' successfully...")



def main():
    parser = argparse.ArgumentParser(description='Migrate qdrant collection from one environment to another')

    # source
    parser.add_argument('--source_backend_url', type=str, help='Source backend url', required=True)
    parser.add_argument('--source_collection_name', type=str, help='Source collection name', required=True)
    parser.add_argument('--source_qdrant_url', type=str, help='Source qdrant url', required=True)
    parser.add_argument('--source_prefix', type=str, help='Source qdrant prefix', required=False, default=None)

    # destination
    parser.add_argument('--destination_backend_url', type=str, help='Destination backend url', required=True)
    parser.add_argument('--destination_collection_name', type=str, help='Destination collection name', required=True)
    parser.add_argument('--destination_qdrant_url', type=str, help='Destination qdrant url', required=True)
    parser.add_argument('--destination_prefix', type=str, help='Destination qdrant prefix', required=False, default=None)

    args = parser.parse_args()

    migrate_collection(
        # source args
        source_backend_url = args.source_backend_url,
        source_collection_name = args.source_collection_name,
        source_qdrant_url = args.source_qdrant_url,
        source_prefix = args.source_prefix,

        # destination args
        destination_backend_url = args.destination_backend_url,
        destination_collection_name = args.destination_collection_name,
        destination_qdrant_url = args.destination_qdrant_url,
        destination_prefix = args.destination_prefix
    )

if __name__ == "__main__":
    # SOURCE
    source_backend_url = "http://localhost:8000"
    source_collection_name = "creditcard"
    source_qdrant_url = "https://ps-qdrant-prathamesh-ws.devtest.truefoundry.tech"
    source_prefix = None

    # DESTINATION
    destination_backend_url = "http://localhost:8000"
    destination_collection_name = "cloned"
    destination_qdrant_url = "https://ps-qdrant-prathamesh-ws.devtest.truefoundry.tech"
    destination_prefix = None

    main()