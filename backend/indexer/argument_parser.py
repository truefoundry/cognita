import argparse

from pydantic import BaseModel

from backend.constants import DEFAULT_BATCH_SIZE
from backend.types import DataIngestionMode


class ParsedIndexingArguments(BaseModel):
    """
    Configuration for storing indexing arguments.
    Requires a collection name (already exisiting) and data source fqn.
    """
    collection_name: str
    data_source_fqn: str
    data_ingestion_mode: DataIngestionMode
    raise_error_on_failure: bool
    batch_size: int = DEFAULT_BATCH_SIZE


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
        "--data_source_fqn",
        type=str,
        required=True,
        help="fully qualified name for your data source run",
    )
    parser.add_argument(
        "--data_ingestion_mode",
        type=str,
        required=False,
        default="INCREMENTAL",
        help="Data Ingestion Mode. NONE/INCREMENTAL/FULL",
    )
    parser.add_argument(
        "--raise_error_on_failure",
        type=str,
        required=False,
        default="True",
        help="If true, raise error on failure of batch, else continue for other batch",
    )
    parser.add_argument(
        "--batch_size",
        type=str,
        required=False,
        default="100",
        help="Batch size for processing documents",
    )
    args = parser.parse_args()

    return ParsedIndexingArguments(
        collection_name=args.collection_name,
        data_source_fqn=args.data_source_fqn,
        data_ingestion_mode=DataIngestionMode(args.data_ingestion_mode),
        raise_error_on_failure=args.raise_error_on_failure == "True",
        batch_size=int(args.batch_size),
    )
