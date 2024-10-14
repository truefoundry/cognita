import tempfile
from concurrent.futures import Executor
from typing import Dict, List, Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from langchain.docstore.document import Document
from truefoundry.deploy import trigger_job

from backend.constants import (
    DATA_POINT_FILE_PATH_METADATA_KEY,
    DATA_POINT_FQN_METADATA_KEY,
    DATA_POINT_HASH_METADATA_KEY,
)
from backend.indexer.types import DataIngestionConfig
from backend.logger import logger
from backend.modules.dataloaders.loader import get_loader_for_data_source
from backend.modules.metadata_store.client import get_client
from backend.modules.model_gateway.model_gateway import model_gateway
from backend.modules.parsers.parser import get_parser_for_extension_with_cache
from backend.modules.vector_db.client import VECTOR_STORE_CLIENT
from backend.settings import settings
from backend.types import (
    CreateDataIngestionRun,
    DataIngestionMode,
    DataIngestionRunStatus,
    DataPointVector,
    IngestDataToCollectionDto,
    LoadedDataPoint,
)


def get_data_point_fqn_to_hash_map(
    data_point_vectors: List[DataPointVector],
) -> Dict[str, str]:
    """
    Returns a map of data point fqn to hash
    """
    return {dpv.data_point_fqn: dpv.data_point_hash for dpv in data_point_vectors}


async def sync_data_source_to_collection(inputs: DataIngestionConfig):
    """
    Synchronizes the data source to the collection by performing the following steps:
    1. Updates the data ingestion run status to indicate that existing vectors are being fetched.
    2. Retrieves the existing data point vectors from the vector store.
    3. Logs the total number of existing data point vectors in the collection.
    4. Updates the data ingestion run status to indicate that data ingestion has started.
    5. Calls the _sync_data_source_to_collection function to perform the actual data ingestion.
    6. Updates the data ingestion run status to indicate the completion of data ingestion.
    7. If the data ingestion mode is set to FULL, deletes the outdated data point vectors from the vector store.
    8. Updates the data ingestion run status to indicate the completion of data cleanup.

    Args:
        inputs (DataIngestionConfig): The configuration for data ingestion.

    Raises:
        Exception: If any error occurs during data ingestion or cleanup.

    Returns:
        None
    """
    client = await get_client()
    await client.aupdate_data_ingestion_run_status(
        data_ingestion_run_name=inputs.data_ingestion_run_name,
        status=DataIngestionRunStatus.FETCHING_EXISTING_VECTORS,
    )
    try:
        existing_data_point_vectors = VECTOR_STORE_CLIENT.list_data_point_vectors(
            collection_name=inputs.collection_name,
            data_source_fqn=inputs.data_source.fqn,
        )
        previous_snapshot = get_data_point_fqn_to_hash_map(
            data_point_vectors=existing_data_point_vectors
        )

        logger.info(
            f"Total existing data point vectors in collection {inputs.collection_name}: {len(existing_data_point_vectors)}"
        )
    except Exception as e:
        logger.exception(e)
        await client.aupdate_data_ingestion_run_status(
            data_ingestion_run_name=inputs.data_ingestion_run_name,
            status=DataIngestionRunStatus.FETCHING_EXISTING_VECTORS_FAILED,
        )
        raise e

    await client.aupdate_data_ingestion_run_status(
        data_ingestion_run_name=inputs.data_ingestion_run_name,
        status=DataIngestionRunStatus.DATA_INGESTION_STARTED,
    )
    try:
        await _sync_data_source_to_collection(
            inputs=inputs,
            previous_snapshot=previous_snapshot,
        )
    except Exception as e:
        logger.exception(e)
        await client.aupdate_data_ingestion_run_status(
            data_ingestion_run_name=inputs.data_ingestion_run_name,
            status=DataIngestionRunStatus.DATA_INGESTION_FAILED,
        )
        raise e
    await client.aupdate_data_ingestion_run_status(
        data_ingestion_run_name=inputs.data_ingestion_run_name,
        status=DataIngestionRunStatus.DATA_INGESTION_COMPLETED,
    )
    # Delete the outdated data point vectors from the vector store
    if inputs.data_ingestion_mode == DataIngestionMode.FULL:
        await client.aupdate_data_ingestion_run_status(
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
            await client.aupdate_data_ingestion_run_status(
                data_ingestion_run_name=inputs.data_ingestion_run_name,
                status=DataIngestionRunStatus.DATA_CLEANUP_FAILED,
            )
            raise e
    await client.aupdate_data_ingestion_run_status(
        data_ingestion_run_name=inputs.data_ingestion_run_name,
        status=DataIngestionRunStatus.COMPLETED,
    )


async def _sync_data_source_to_collection(
    inputs: DataIngestionConfig, previous_snapshot: Dict[str, str] = None
):
    """
    Synchronizes data from a data source to a collection.

    Args:
        inputs (DataIngestionConfig): The configuration for data ingestion.
        previous_snapshot (Dict[str, str], optional): A dictionary mapping data point FQNs to their hashes. Defaults to None.

    Raises:
        Exception: If failed to ingest any data points.

    Returns:
        None
    """

    client = await get_client()

    failed_data_point_fqns = []
    documents_ingested_count = 0
    # Create a temp dir to store the data
    with tempfile.TemporaryDirectory() as tmp_dirname:
        # Load the data from the source to the dest dir
        logger.info("Loading data from data source")
        data_source_loader = get_loader_for_data_source(inputs.data_source.type)
        loaded_data_points_batch_iterator = data_source_loader.load_filtered_data(
            data_source=inputs.data_source,
            dest_dir=tmp_dirname,
            previous_snapshot=previous_snapshot,
            batch_size=inputs.batch_size,
            data_ingestion_mode=inputs.data_ingestion_mode,
        )

        async for loaded_data_points_batch in loaded_data_points_batch_iterator:
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
                failed_data_point_fqns.extend(
                    [doc.data_point_fqn for doc in loaded_data_points_batch]
                )

        if len(failed_data_point_fqns) > 0:
            logger.error(
                f"Failed to ingest {len(failed_data_point_fqns)} data points. data point fqns:"
            )
            logger.error(failed_data_point_fqns)
            await client.alog_errors_for_data_ingestion_run(
                data_ingestion_run_name=inputs.data_ingestion_run_name,
                errors={"failed_data_point_fqns": failed_data_point_fqns},
            )
            raise Exception(
                f"Failed to ingest {len(failed_data_point_fqns)} data points"
            )


async def ingest_data_points(
    inputs: DataIngestionConfig,
    loaded_data_points: List[LoadedDataPoint],
    documents_ingested_count: int,
):
    """
    Ingests data points into the vector store for a given batch.

    Args:
        inputs (DataIngestionConfig): Configuration for data ingestion.
        loaded_data_points (List[LoadedDataPoint]): List of loaded data points to be ingested.
        documents_ingested_count (int): Current count of ingested documents.

    Returns:
        None
    """
    # Calculate embeddings for the data points
    embeddings = model_gateway.get_embedder_from_model_config(
        inputs.embedder_config.name
    )
    documents_to_be_upserted = []
    logger.info(
        f"Processing {len(loaded_data_points)} new documents. Total ingested: {documents_ingested_count}"
    )

    parser_cache = {}

    for index, data_point in enumerate(loaded_data_points, start=1):
        logger.info(f"Parsing document {index}/{len(loaded_data_points)}")

        # Get the parser for the data point extension
        parser = get_parser_for_extension_with_cache(
            data_point.file_extension, inputs.parser_config, parser_cache
        )
        if not parser:
            logger.warning(
                f"No parser found for {data_point.data_point_fqn} with extension: {data_point.file_extension}"
            )
            continue

        # For the current data point, get the chunks by parser
        chunks = await parser.get_chunks(data_point.local_filepath, data_point.metadata)

        # Enrich the chunk with data point metadata
        documents_to_be_upserted.extend(
            [
                enrich_chunk_with_data_point_metadata(chunk, data_point)
                for chunk in chunks
            ]
        )

        logger.info(f"{data_point.local_filepath} -> {len(chunks)} chunks")

    # If there are no documents to be upserted, log a warning and return
    if not documents_to_be_upserted:
        logger.warning("No documents to index in this batch.")
        return
    # Ingest the documents to the vector store
    logger.info(f"Upserting {len(documents_to_be_upserted)} documents to vector store")
    VECTOR_STORE_CLIENT.upsert_documents(
        collection_name=inputs.collection_name,
        documents=documents_to_be_upserted,
        embeddings=embeddings,
        incremental=inputs.data_ingestion_mode == DataIngestionMode.INCREMENTAL,
    )


def enrich_chunk_with_data_point_metadata(chunk: Document, data_point: LoadedDataPoint):
    # Add the data point metadata to the chunk metadata
    chunk.metadata.update(data_point.metadata or {})
    # Add the data point fqn and hash to the chunk metadata
    # This information will be used in the retrieval process to identify the source of the chunk
    chunk.metadata.update(
        {
            DATA_POINT_FQN_METADATA_KEY: data_point.data_point_fqn,
            DATA_POINT_HASH_METADATA_KEY: data_point.data_point_hash,
            DATA_POINT_FILE_PATH_METADATA_KEY: data_point.local_filepath,
            "_data_source_fqn": data_point.data_source_fqn,
        }
    )

    return chunk


async def ingest_data(
    request: IngestDataToCollectionDto, pool: Optional[Executor] = None
):
    """Ingest data into the collection"""
    metadata_store_client = await get_client()
    collection = await metadata_store_client.aget_collection_by_name(
        request.collection_name
    )

    if not collection.associated_data_sources:
        logger.error(
            f"Collection {request.collection_name} does not have any associated data sources."
        )
        raise HTTPException(
            status_code=400,
            detail=f"Collection {request.collection_name} does not have any associated data sources.",
        )
    associated_data_sources_to_be_ingested = []
    if request.data_source_fqn:
        associated_data_sources_to_be_ingested = [
            collection.associated_data_sources.get(request.data_source_fqn)
        ]
    else:
        associated_data_sources_to_be_ingested = (
            collection.associated_data_sources.values()
        )

    logger.info(f"Associated: {associated_data_sources_to_be_ingested}")
    for associated_data_source in associated_data_sources_to_be_ingested:
        logger.debug(
            f"Starting ingestion for data source fqn: {associated_data_source.data_source_fqn}"
        )
        if not request.run_as_job or settings.LOCAL:
            data_ingestion_run = CreateDataIngestionRun(
                collection_name=collection.name,
                data_source_fqn=associated_data_source.data_source_fqn,
                embedder_config=collection.embedder_config,
                parser_config=associated_data_source.parser_config,
                data_ingestion_mode=request.data_ingestion_mode,
                raise_error_on_failure=request.raise_error_on_failure,
            )
            created_data_ingestion_run = (
                await metadata_store_client.acreate_data_ingestion_run(
                    data_ingestion_run=data_ingestion_run
                )
            )
            ingestion_config = DataIngestionConfig(
                collection_name=created_data_ingestion_run.collection_name,
                data_ingestion_run_name=created_data_ingestion_run.name,
                data_source=associated_data_source.data_source,
                embedder_config=collection.embedder_config,
                parser_config=created_data_ingestion_run.parser_config,
                data_ingestion_mode=created_data_ingestion_run.data_ingestion_mode,
                raise_error_on_failure=created_data_ingestion_run.raise_error_on_failure,
                batch_size=request.batch_size,
            )
            if pool:
                logger.info(f"Submitting sync_data_source_to_collection job to pool")
                # future of this submission is ignored, failures not tracked
                pool.submit(sync_data_source_to_collection, ingestion_config)
            else:
                await sync_data_source_to_collection(ingestion_config)
            created_data_ingestion_run.status = DataIngestionRunStatus.INITIALIZED
        else:
            if not settings.JOB_FQN:
                logger.error("Job FQN is required to trigger the job")
                raise HTTPException(
                    status_code=500,
                    detail="Job FQN and Job Component Name are required to trigger the job",
                )
            data_ingestion_run = CreateDataIngestionRun(
                collection_name=collection.name,
                data_source_fqn=associated_data_source.data_source_fqn,
                embedder_config=collection.embedder_config,
                parser_config=associated_data_source.parser_config,
                data_ingestion_mode=request.data_ingestion_mode,
                raise_error_on_failure=request.raise_error_on_failure,
            )
            created_data_ingestion_run = (
                await metadata_store_client.acreate_data_ingestion_run(
                    data_ingestion_run=data_ingestion_run
                )
            )
            trigger_job(
                application_fqn=settings.JOB_FQN,
                params={
                    "collection_name": collection.name,
                    "data_source_fqn": associated_data_source.data_source_fqn,
                    "data_ingestion_run_name": created_data_ingestion_run.name,
                    "data_ingestion_mode": request.data_ingestion_mode,
                    "raise_error_on_failure": (
                        "True" if request.raise_error_on_failure else "False"
                    ),
                },
            )
    return JSONResponse(
        status_code=201,
        content={"message": "triggered"},
    )
