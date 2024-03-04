import asyncio

from backend.indexer.argument_parser import parse_args
from backend.indexer.indexer import ingest_data_to_collection
from backend.indexer.types import DataIngestionConfig
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.settings import settings


async def main():
    # parse training arguments
    arguments = parse_args()
    collection = METADATA_STORE_CLIENT.get_collection_by_name(
        arguments.collection_name, no_cache=True
    )
    if not collection:
        raise ValueError(f"Collection with name {arguments.collection_name} not found")
    data_ingestion_run = METADATA_STORE_CLIENT.get_data_ingestion_run(
        data_ingestion_run_name=arguments.data_ingestion_run_name, no_cache=True
    )
    if not data_ingestion_run:
        raise ValueError(
            f"Data ingestion run with name {arguments.data_ingestion_run_name} not found"
        )
    data_source = METADATA_STORE_CLIENT.get_data_source_from_fqn(
        fqn=data_ingestion_run.data_source_fqn
    )
    if not data_source:
        raise ValueError(
            f"Data source with fqn {data_ingestion_run.data_source_fqn} not found"
        )
    inputs = DataIngestionConfig(
        collection_name=collection.name,
        data_ingestion_run_name=data_ingestion_run.name,
        data_source=data_source,
        embedder_config=collection.embedder_config,
        parser_config=data_ingestion_run.parser_config,
        vector_db_config=settings.VECTOR_DB_CONFIG,
        data_ingestion_mode=data_ingestion_run.data_ingestion_mode,
        raise_error_on_failure=True,
        batch_size=100,
    )
    await ingest_data_to_collection(inputs=inputs)


if __name__ == "__main__":
    asyncio.run(main())
