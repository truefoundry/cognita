import asyncio

from backend.indexer.argument_parser import parse_args
from backend.indexer.indexer import sync_data_source_to_collection
from backend.indexer.types import DataIngestionConfig
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.types import CreateDataIngestionRun
from backend.logger import logger


async def main():
    # parse training arguments
    arguments = parse_args()
    collection = METADATA_STORE_CLIENT.get_collection_by_name(
        arguments.collection_name, no_cache=True
    )
    if not collection:
        raise ValueError(f"Collection with name {arguments.collection_name} not found")
    data_source = METADATA_STORE_CLIENT.get_data_source_from_fqn(
        fqn=arguments.data_source_fqn
    )
    if not data_source:
        raise ValueError(f"Data source with fqn {arguments.data_source_fqn} not found")
    associated_data_source = collection.associated_data_sources.get(data_source.fqn)
    if not associated_data_source:
        raise ValueError(
            f"Data source {data_source.fqn} is not associated with collection {collection.name}"
        )

    if arguments.data_ingestion_run_name:
        logger.debug(f"Using data ingestion run name: {arguments.data_ingestion_run_name}")
        created_data_ingestion_run = METADATA_STORE_CLIENT.get_data_ingestion_run(
            data_ingestion_run_name=arguments.data_ingestion_run_name
        )
    else:
        data_ingestion_run = CreateDataIngestionRun(
            collection_name=collection.name,
            data_source_fqn=associated_data_source.data_source_fqn,
            embedder_config=collection.embedder_config,
            parser_config=associated_data_source.parser_config,
            data_ingestion_mode=arguments.data_ingestion_mode,
            raise_error_on_failure=arguments.raise_error_on_failure,
        )
        created_data_ingestion_run = METADATA_STORE_CLIENT.create_data_ingestion_run(
            data_ingestion_run=data_ingestion_run
        )

    inputs = DataIngestionConfig(
        collection_name=collection.name,
        data_ingestion_run_name=created_data_ingestion_run.name,
        data_source=data_source,
        embedder_config=collection.embedder_config,
        parser_config=created_data_ingestion_run.parser_config,
        data_ingestion_mode=created_data_ingestion_run.data_ingestion_mode,
        raise_error_on_failure=created_data_ingestion_run.raise_error_on_failure,
        batch_size=arguments.batch_size,
    )
    await sync_data_source_to_collection(inputs=inputs)


if __name__ == "__main__":
    import time 
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print(f"Time taken for ingestion: {end-start} seconds")
