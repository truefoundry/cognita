import argparse

from backend.types import DataIngestionMode, IngestDataToCollectionDto


def parse_args_ingest_total_collection() -> IngestDataToCollectionDto:
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
        required=False,
        help="unique identifier for the data source",
    )

    parser.add_argument(
        "--data_ingestion_run_name",
        type=str,
        required=False,
        default=None,
        help="a unique name for your data ingestion run",
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
        "--run_as_job",
        type=str,
        required=False,
        default="False",
        help="If true, run as job, else run as script",
    )
    parser.add_argument(
        "--batch_size",
        type=str,
        required=False,
        default="100",
        help="Batch size for processing documents",
    )
    args = parser.parse_args()

    return IngestDataToCollectionDto(
        collection_name=args.collection_name,
        data_source_fqn=args.data_source_fqn,
        data_ingestion_mode=DataIngestionMode(args.data_ingestion_mode),
        raise_error_on_failure=args.raise_error_on_failure == "True",
        run_as_job=args.run_as_job == "True",
        batch_size=int(args.batch_size),
    )
