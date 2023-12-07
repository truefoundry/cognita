import argparse
import asyncio

import orjson
from dotenv import load_dotenv

from backend.indexer.indexer import index_collection
from backend.utils.base import (
    DataSource,
    EmbedderConfig,
    EmbeddingCacheConfig,
    IndexerConfig,
    MetadataStoreConfig,
    ParserConfig,
    VectorDBConfig,
)

# load environment variables
load_dotenv()


def parse_args() -> IndexerConfig:
    parser = argparse.ArgumentParser(
        prog="train",
        usage="%(prog)s [options]",
        description="Indexer job to break down the documents into chunks and index them in VectorDB",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.add_argument(
        "--collection_name",
        type=str,
        required=True,
        help="a unique name for your collection",
    )
    parser.add_argument(
        "--indexer_job_run_name",
        type=str,
        required=True,
        help="a unique name to your indexing run",
    )
    parser.add_argument(
        "--data_source",
        dest="data_source",
        type=str,
        required=True,
        help="Source of documents to be indexed. Can be s3, github or mlfoundry artifact",
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        required=False,
        default=1000,
        help="chunk size for indexing",
    )

    parser.add_argument(
        "--embedder_config",
        type=str,
        required=True,
        default="""{}""",
        help="Embedder configuration (must be a valid json)",
    )

    parser.add_argument(
        "--parser_config",
        type=str,
        default="""{".pdf": "PdfParserFast"}""",
        required=False,
        help="Mapping of file extensions to parsers. Required only incase, multiple parsers are available for same extension. Must be a valid json",
    )
    parser.add_argument(
        "--vector_db_config",
        type=str,
        required=True,
        help="Vector DB config to store the indexed documents.",
    )
    parser.add_argument(
        "--metadata_store_config",
        type=str,
        required=True,
        help="Metadata store config",
    )
    parser.add_argument(
        "--embedding_cache_config",
        type=str,
        required=False,
        help="Embedding cache config",
    )
    args = parser.parse_args()

    return IndexerConfig(
        collection_name=args.collection_name,
        indexer_job_run_name=args.indexer_job_run_name,
        data_source=DataSource.parse_obj(orjson.loads(args.data_source)),
        chunk_size=args.chunk_size,
        embedder_config=EmbedderConfig.parse_obj(orjson.loads(args.embedder_config)),
        parser_config=ParserConfig.parse_obj(orjson.loads(args.parser_config)),
        vector_db_config=VectorDBConfig.parse_obj(orjson.loads(args.vector_db_config)),
        metadata_store_config=MetadataStoreConfig.parse_obj(
            orjson.loads(args.metadata_store_config)
        ),
        embedding_cache_config=(
            EmbeddingCacheConfig.parse_obj(orjson.loads(args.embedding_cache_config))
            if args.embedding_cache_config
            else None
        ),
    )


async def main():
    # parse training arguments
    index_config = parse_args()
    await index_collection(index_config)


if __name__ == "__main__":
    asyncio.run(main())
