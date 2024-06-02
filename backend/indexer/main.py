import asyncio

from backend.indexer.argument_parser import parse_args_ingest_total_collection
from backend.indexer.indexer import ingest_data
from backend.logger import logger
from backend.types import DataIngestionMode, IngestDataToCollectionDto


async def main():
    args = parse_args_ingest_total_collection()
    inputs = IngestDataToCollectionDto(
        collection_name=args.collection_name,
        data_source_fqn=args.data_source_fqn,
        data_ingestion_mode=DataIngestionMode(args.data_ingestion_mode),
        raise_error_on_failure=args.raise_error_on_failure == "True",
        batch_size=int(args.batch_size),
    )
    try:
        await ingest_data(request=inputs)
    except Exception as e:
        print(f"Indexer exception - {e}")
        logger.exception(e)
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
