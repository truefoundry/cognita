import argparse

from pydantic import BaseModel


class ParsedIndexingArguments(BaseModel):
    collection_name: str
    data_ingestion_run_name: str


def parse_args() -> ParsedIndexingArguments:
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
        "--data_ingestion_run_name",
        type=str,
        required=True,
        help="a unique name to your ingestion run",
    )
    args = parser.parse_args()

    return ParsedIndexingArguments(
        collection_name=args.collection_name,
        data_ingestion_run_name=args.data_ingestion_run_name,
    )
