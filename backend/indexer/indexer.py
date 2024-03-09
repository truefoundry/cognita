import tempfile
from typing import Dict, List

from backend.indexer.types import DataIngestionConfig
from backend.logger import logger
from backend.modules.dataloaders.loader import get_loader_for_data_source
from backend.modules.embedder.embedder import get_embedder
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.modules.parsers.parser import get_parser_for_extension
from backend.modules.vector_db.client import VECTOR_STORE_CLIENT
from backend.types import (
    DataIngestionMode,
    DataIngestionRunStatus,
    DataPointVector,
    LoadedDataPoint,
)


def get_data_point_id_to_hash_map(
    data_point_vectors: List[DataPointVector],
) -> Dict[str, str]:
    """
    Returns a map of data point id to hash
    """
    data_point_id_to_hash: Dict[str, str] = {}
    for data_point_vector in data_point_vectors:
        if data_point_vector.data_point_id not in data_point_id_to_hash:
            data_point_id_to_hash[data_point_vector.data_point_id] = (
                data_point_vector.data_point_hash
            )

    return data_point_id_to_hash


async def sync_data_source_to_collection(inputs: DataIngestionConfig):
    METADATA_STORE_CLIENT.update_data_ingestion_run_status(
        data_ingestion_run_name=inputs.data_ingestion_run_name,
        status=DataIngestionRunStatus.FETCHING_EXISTING_VECTORS,
    )
    try:
        existing_data_point_vectors = VECTOR_STORE_CLIENT.list_data_point_vectors(
            collection_name=inputs.collection_name
        )
        existing_data_point_id_to_hash = get_data_point_id_to_hash_map(
            data_point_vectors=existing_data_point_vectors
        )

        logger.info(
            f"Total existing data point vectors in collection {inputs.collection_name}: {len(existing_data_point_vectors)}"
        )
    except Exception as e:
        logger.exception(e)
        METADATA_STORE_CLIENT.update_data_ingestion_run_status(
            data_ingestion_run_name=inputs.data_ingestion_run_name,
            status=DataIngestionRunStatus.FETCHING_EXISTING_VECTORS,
        )
        raise e
    METADATA_STORE_CLIENT.update_data_ingestion_run_status(
        data_ingestion_run_name=inputs.data_ingestion_run_name,
        status=DataIngestionRunStatus.DATA_INGESTION_STARTED,
    )
    try:

        await _sync_data_source_to_collection(
            inputs=inputs, existing_data_point_id_to_hash=existing_data_point_id_to_hash
        )
    except Exception as e:
        logger.exception(e)
        METADATA_STORE_CLIENT.update_data_ingestion_run_status(
            data_ingestion_run_name=inputs.data_ingestion_run_name,
            status=DataIngestionRunStatus.DATA_INGESTION_FAILED,
        )
        raise e
    # Delete the outdated data point vectors from the vector store
    if inputs.data_ingestion_mode == DataIngestionMode.FULL:
        METADATA_STORE_CLIENT.update_data_ingestion_run_status(
            data_ingestion_run_name=inputs.data_ingestion_run_name,
            status=DataIngestionRunStatus.DATA_CLEANUP_STARTED,
        )
        try:
            VECTOR_STORE_CLIENT.delete_data_point_vectors(
                collection_name=inputs.collection_name,
                data_point_vectors=existing_data_point_vectors,
            )
        except Exception as e:
            logger.exception(e)
            METADATA_STORE_CLIENT.update_data_ingestion_run_status(
                data_ingestion_run_name=inputs.data_ingestion_run_name,
                status=DataIngestionRunStatus.DATA_CLEANUP_FAILED,
            )
            raise e
    METADATA_STORE_CLIENT.update_data_ingestion_run_status(
        data_ingestion_run_name=inputs.data_ingestion_run_name,
        status=DataIngestionRunStatus.COMPLETED,
    )


async def _sync_data_source_to_collection(
    inputs: DataIngestionConfig, existing_data_point_id_to_hash: Dict[str, str] = None
):
    failed_data_point_ids = []
    documents_ingested_count = 0
    # Create a temp dir to store the data
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Load the data from the source to the dest dir
        data_source_loader = get_loader_for_data_source(inputs.data_source.type)
        loaded_data_points_batch_iterator = (
            data_source_loader.load_filtered_data_points_from_data_source(
                data_source=inputs.data_source,
                dest_dir=tmpdirname,
                existing_data_point_id_to_hash=existing_data_point_id_to_hash,
                batch_size=inputs.batch_size,
                data_ingestion_mode=inputs.data_ingestion_mode,
            )
        )

        for loaded_data_points_batch in loaded_data_points_batch_iterator:
            try:
                await ingest_data_points(
                    inputs=inputs,
                    loaded_data_points=loaded_data_points_batch,
                    documents_ingested_count=documents_ingested_count,
                )
                documents_ingested_count = documents_ingested_count + len(
                    loaded_data_points_batch
                )
            except Exception as e:
                logger.exception(e)
                if inputs.raise_error_on_failure:
                    raise e
                failed_data_point_ids.extend(
                    [doc.data_point_id for doc in loaded_data_points_batch]
                )

        METADATA_STORE_CLIENT.update_data_ingestion_run_status(
            data_ingestion_run_name=inputs.data_ingestion_run_name,
            status=DataIngestionRunStatus.DATA_INGESTION_COMPLETED,
        )
        if len(failed_data_point_ids) > 0:
            logger.error(
                f"Failed to ingest {len(failed_data_point_ids)} data points. Data Point IDs:"
            )
            logger.error(failed_data_point_ids)
            METADATA_STORE_CLIENT.log_errors_for_data_ingestion_run(
                data_ingestion_run_name=inputs.data_ingestion_run_name,
                errors={"failed_data_point_ids": failed_data_point_ids},
            )


async def ingest_data_points(
    inputs: DataIngestionConfig,
    loaded_data_points: List[LoadedDataPoint],
    documents_ingested_count: int,
):
    embeddings = get_embedder(
        embedder_config=inputs.embedder_config,
    )
    documents_to_be_upserted = []
    logger.info(
        f"Processing documents - new: {len(loaded_data_points)} completed: {documents_ingested_count}"
    )
    for index, loaded_data_point in enumerate(loaded_data_points):
        logger.info(
            f"Parsing documents - new: [{index+1}/{len(loaded_data_points)}] completed: {documents_ingested_count}"
        )
        # Get parser for required file extension
        parser = get_parser_for_extension(
            file_extension=loaded_data_point.file_extension,
            parsers_map=inputs.parser_config.parser_map,
            max_chunk_size=inputs.parser_config.chunk_size,
        )
        # chunk the given document
        chunks = await parser.get_chunks(
            document=loaded_data_point,
        )
        for chunk in chunks:
            chunk = chunk.metadata.update(loaded_data_point.metadata)
            documents_to_be_upserted.append(chunk)
        logger.info("%s -> %s chunks", loaded_data_point.local_filepath, len(chunks))

    docs_to_index_count = len(documents_to_be_upserted)
    if docs_to_index_count == 0:
        logger.warning(
            "No documents found to index in given batch. Moving to next batch..."
        )
        return
    logger.info(
        f"Upserting {docs_to_index_count} documents to vector store for given batch"
    )
    # Upserted all the documents_to_be_ingested
    VECTOR_STORE_CLIENT.upsert_documents(
        documents=documents_to_be_upserted,
        embeddings=embeddings,
        incremental=inputs.data_ingestion_mode == DataIngestionMode.INCREMENTAL,
    )
