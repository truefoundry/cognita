import asyncio

from backend.indexer.argument_parser import parse_args
from backend.indexer.indexer import upsert_documents_to_collection
from backend.indexer.types import IndexerConfig
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.settings import settings


async def main():
    # parse training arguments
    arguments = parse_args()
    collection = METADATA_STORE_CLIENT.get_collection_by_name(arguments.collection_name)
    if not collection:
        raise ValueError(f"Collection {arguments.collection_name} not found")
    indexer_job_run = METADATA_STORE_CLIENT.get_collection_indexer_job_run(
        collection_inderer_job_run_name=arguments.indexer_job_run_name
    )
    if not indexer_job_run:
        raise ValueError(f"Indexer job run {arguments.indexer_job_run_name} not found")
    inputs = IndexerConfig(
        collection_name=collection.name,
        indexer_job_run_name=indexer_job_run.name,
        data_source=indexer_job_run.data_source,
        chunk_size=collection.chunk_size,
        embedder_config=collection.embedder_config,
        parser_config=indexer_job_run.parser_config,
        vector_db_config=settings.VECTOR_DB_CONFIG,
        metadata_store_config=settings.METADATA_STORE_CONFIG,
        embedding_cache_config=settings.EMBEDDING_CACHE_CONFIG,
        indexing_mode=indexer_job_run.indexing_mode,
    )
    await upsert_documents_to_collection(inputs=inputs)


if __name__ == "__main__":
    asyncio.run(main())
