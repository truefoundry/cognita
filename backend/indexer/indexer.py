import tempfile
from typing import List

from langchain.docstore.document import Document

from backend.indexer.types import DataIngestionConfig
from backend.logger import logger
from backend.modules.dataloaders.loader import get_loader_for_data_source
from backend.modules.embedder.embedder import get_embedder
from backend.modules.metadata_store.base import get_base_document_id
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.modules.parsers.parser import (
    get_parser_for_extension,
    get_parsers_configurations,
)
from backend.modules.vector_db import get_vector_db_client
from backend.types import DataIngestionMode, DataIngestionRunStatus, DataPoint


async def sync_data_to_collection(inputs: DataIngestionConfig):
    data_source_loader = get_loader_for_data_source(inputs.data_source.type)
    data_points_to_be_ingested: List[DataPoint] = data_source_loader.list_data_points(
        data_source=inputs.data_source
    )
    existing_vector_ids = .get_all_vector_ids(
    if inputs.data_ingestion_mode == DataIngestionMode.FULL:

    logger.info(f"Data points to be ingested: {len(data_points_to_be_ingested)}")
    await ingest_data_to_collection(inputs=inputs, data_points=data_points_to_be_ingested)


async def ingest_data_to_collection(
    inputs: DataIngestionConfig, data_points: List[DataPoint]
):
    logger.info("+------------------------------------------------------------+")
    logger.info("| Ingesting data to collection                               |")
    logger.info(f"| Data Ingestion Mode - {inputs.data_ingestion_mode.value}       |")
    logger.info("+------------------------------------------------------------+")
    try:
        # Set the status of the collection run to running
        METADATA_STORE_CLIENT.update_data_ingestion_run_status(
            data_ingestion_run_name=inputs.data_ingestion_run_name,
            status=DataIngestionRunStatus.DATA_LOADING_STARTED,
        )
        embeddings = get_embedder(
            embedder_config=inputs.embedder_config,
        )
        vector_db_client = get_vector_db_client(
            config=inputs.vector_db_config, collection_name=inputs.collection_name
        )
        data_source_loader = get_loader_for_data_source(inputs.data_source.type)

        failed_document_ids = []
        data_points_count = len(data_points)

        # Batch processing the documents
        for i in range(0, data_points_count, inputs.batch_size):
            data_points_to_be_processed = data_points[i : i + inputs.batch_size]
            documents_to_be_upserted: List[Document] = []
            try:
                # Create a temp dir to store the data
                with tempfile.TemporaryDirectory() as tmpdirname:
                    # Load the data from the source to the dest dir
                    documents_to_be_processed = data_source_loader.load_data_points(
                        data_source=inputs.data_source,
                        data_points=data_points_to_be_processed,
                        dest_dir=tmpdirname,
                    )

                    METADATA_STORE_CLIENT.update_data_ingestion_run_status(
                        data_ingestion_run_name=inputs.data_ingestion_run_name,
                        status=DataIngestionRunStatus.CHUNKING_STARTED,
                    )

                    # Count number of documents/files/urls loaded
                    docs_to_index_count = len(documents_to_be_processed)
                    logger.info(f"Documents to index: {docs_to_index_count}")

                    if docs_to_index_count == 0:
                        logger.warning("No documents to found")
                        METADATA_STORE_CLIENT.update_data_ingestion_run_status(
                            data_ingestion_run_name=inputs.data_ingestion_run_name,
                            status=DataIngestionRunStatus.COMPLETED,
                        )
                        return

                    METADATA_STORE_CLIENT.log_metrics_for_data_ingestion_run(
                        data_ingestion_run_name=inputs.data_ingestion_run_name,
                        metric_dict={"num_files": docs_to_index_count},
                    )

                    for index, doc in enumerate(documents_to_be_processed):
                        logger.info(
                            f"[{i + index + 1}/{len(docs_to_index_count)}] Processing document"
                        )
                        # Get parser for required file extension
                        parser = get_parser_for_extension(
                            file_extension=doc.file_extension,
                            parsers_map=inputs.parser_config.parser_map,
                            max_chunk_size=inputs.parser_config.chunk_size,
                        )
                        # chunk the given document
                        chunks = await parser.get_chunks(
                            document=doc,
                        )
                        documents_to_be_upserted.extend(chunks)
                        logger.info("%s -> %s chunks", doc.filepath, len(chunks))
                        METADATA_STORE_CLIENT.log_metrics_for_data_ingestion_run(
                            data_ingestion_run_name=inputs.data_ingestion_run_name,
                            metric_dict={"num_chunks": len(chunks)},
                            step=index,
                        )

                    if len(documents_to_be_upserted) == 0:
                        logger.warning(f"No chunks to index in batch {i}")
                        continue

                    logger.info(
                        f"Total chunks to index in batch {i}: {len(documents_to_be_upserted)}"
                    )
                    # Upserted all the documents_to_be_ingested
                    vector_db_client.upsert_documents(
                        documents=documents_to_be_upserted,
                        embeddings=embeddings,
                        incremental=inputs.data_ingestion_mode
                        == DataIngestionMode.INCREMENTAL,
                    )
            except Exception as e:
                logger.exception(e)
                if inputs.raise_error_on_failure:
                    raise e
                failed_document_ids.extend(
                    [doc.metadata._document_id for doc in documents_to_be_processed]
                )


        METADATA_STORE_CLIENT.update_data_ingestion_run_status(
            data_ingestion_run_name=inputs.data_ingestion_run_name,
            status=DataIngestionRunStatus.COMPLETED,
        )

        if len(failed_document_ids) > 0:
            logger.error(
                f"Failed to ingest {len(failed_document_ids)} documents. Document IDs:"
            )
            logger.error(failed_document_ids)
            METADATA_STORE_CLIENT.log_errors_for_data_ingestion_run(
                data_ingestion_run_name=inputs.data_ingestion_run_name,
                errors={"failed_document_ids": failed_document_ids},
            )

    except Exception as e:
        logger.exception(e)
        METADATA_STORE_CLIENT.update_data_ingestion_run_status(
            data_ingestion_run_name=inputs.data_ingestion_run_name,
            status=DataIngestionRunStatus.FAILED,
        )
        raise e
