import argparse
import asyncio
import orjson
from dotenv import load_dotenv
from backend.base import (
    KnowledgeSource,
    EmbedderConfig,
    ParserConfig,
    VectorDBConfig,
    IndexConfig,
)
from backend.indexer import index_collection

# load environment variables
load_dotenv()


def parse_args() -> IndexConfig:
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
        "--knowledge_source",
        dest="knowledge_source",
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
        default="""{"provider": "weaviate", "url": "", "api_key": ""}""",
        required=False,
        help="Vector DB config to store the indexed documents.",
    )
    args = parser.parse_args()

    return IndexConfig(
        collection_name=args.collection_name,
        indexer_job_run_name=args.indexer_job_run_name,
        knowledge_source=KnowledgeSource.parse_obj(orjson.loads(args.knowledge_source)),
        chunk_size=args.chunk_size,
        embedder_config=EmbedderConfig.parse_obj(orjson.loads(args.embedder_config)),
        parser_config=ParserConfig.parse_obj(orjson.loads(args.parser_config)),
        vector_db_config=VectorDBConfig.parse_obj(orjson.loads(args.vector_db_config)),
    )


async def main():
    # parse training arguments
    index_config = parse_args()
    await index_collection(index_config)


if __name__ == "__main__":
    asyncio.run(main())
