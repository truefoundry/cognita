import os
import tempfile
from backend.logger import logger
from backend.base import IndexConfig
from backend.modules.embedder import get_embedder
from backend.modules.metadata_store import get_metadata_store_client
from backend.modules.metadata_store.models import CollectionIndexerJobRunStatus
from backend.modules.vector_db import get_vector_db_client
from backend.modules.dataloaders.loader import get_loader_for_knowledge_source
from backend.modules.parsers.parser import (
    get_parser,
    get_parsers_map,
    get_parser_for_file,
    get_parsers_configurations,
)

METADATA_STORE_TYPE = os.environ.get("METADATA_STORE_TYPE", "mlfoundry")


def count_docs_to_index_in_dir(target_dir: str) -> int:
    count = 0
    parsers_map = get_parsers_map()
    for dirpath, dirnames, filenames in os.walk(target_dir):
        for file in filenames:
            for ext in parsers_map.keys():
                if file.endswith(ext):
                    count += 1
    return count


async def get_all_chunks_from_dir(
    dest_dir,
    max_chunk_size,
    parsers_map,
):
    """
    This function loops over all the files in the dest dir and uses
    parsers to get the chunks from all the files. It returns the chunks
    as an array where each element is the chunk along with some metadata
    """
    docs_to_embed = []
    for dirpath, dirnames, filenames in os.walk(dest_dir):
        for file in filenames:
            if file.startswith("."):
                continue
            # Get the file extension using os.path
            file_ext = os.path.splitext(file)[1]
            if file_ext not in parsers_map.keys():
                continue
            parser_name = get_parser_for_file(file, parsers_map)
            if parser_name is None:
                logger.info(f"Skipping file {file} as it is not supported")
                continue
            parser = get_parser(parser_name, max_chunk_size)
            filepath = os.path.join(dirpath, file)
            chunks = await parser.get_chunks(filepath)
            # Loop over all the chunks and add them to the docs_to_embed
            # array
            for chunk in chunks:
                docs_to_embed.append(chunk)

            logger.info("%s -> %s chunks", filepath, len(chunks))
    return docs_to_embed


async def index_collection(inputs: IndexConfig):
    parsers_map = get_parsers_configurations(inputs.parser_config)
    embeddings = get_embedder(inputs.embedder_config)
    metadata_store_client = get_metadata_store_client(METADATA_STORE_TYPE)
    vector_db_client = get_vector_db_client(
        config=inputs.vector_db_config, collection_name=inputs.collection_name
    )

    # Set the status of the collection run to running
    metadata_store_client.update_indexer_job_run_status(
        collection_inderer_job_run_name=inputs.indexer_job_run_name,
        status=CollectionIndexerJobRunStatus.RUNNING,
    )

    try:
        # Create a temp dir to store the data
        dest_dir = tempfile.mkdtemp()

        # Load the data from the source to the dest dir
        get_loader_for_knowledge_source(inputs.knowledge_source.type).load_data(
            inputs.knowledge_source.config.uri, dest_dir
        )

        # Count number of documents/files
        docs_to_index_count = count_docs_to_index_in_dir(dest_dir)
        logger.info("Total docs to index: %s", docs_to_index_count)

        # Index all the documents in the dest dir
        chunks = await get_all_chunks_from_dir(
            dest_dir,
            inputs.chunk_size,
            parsers_map,
        )

        # Index all the chunks
        vector_db_client.upsert_documents(documents=chunks, embeddings=embeddings)

        metadata_store_client.update_indexer_job_run_status(
            collection_inderer_job_run_name=inputs.indexer_job_run_name,
            status=CollectionIndexerJobRunStatus.COMPLETED,
        )

    except Exception as e:
        logger.error(e)
        metadata_store_client.update_indexer_job_run_status(
            collection_inderer_job_run_name=inputs.indexer_job_run_name,
            status=CollectionIndexerJobRunStatus.FAILED,
        )
        raise e


async def trigger_job_locally(inputs: IndexConfig):
    await index_collection(inputs)
