import os
import tempfile
from typing import List

from langchain.docstore.document import Document

from backend.modules.dataloaders.loader import get_loader_for_knowledge_source
from backend.modules.embedder import get_embedder
from backend.modules.metadata_store import get_metadata_store_client
from backend.modules.metadata_store.models import CollectionIndexerJobRunStatus
from backend.modules.parsers.parser import (
    get_parser_for_extension,
    get_parsers_configurations,
)
from backend.modules.vector_db import get_vector_db_client
from backend.utils.base import IndexerConfig
from backend.utils.logger import logger

METADATA_STORE_TYPE = os.environ.get("METADATA_STORE_TYPE", "mlfoundry")


async def index_collection(inputs: IndexerConfig):
    parsers_map = get_parsers_configurations(inputs.parser_config)
    metadata_store_client = get_metadata_store_client(METADATA_STORE_TYPE)

    # Set the status of the collection run to running
    metadata_store_client.update_indexer_job_run_status(
        collection_inderer_job_run_name=inputs.indexer_job_run_name,
        status=CollectionIndexerJobRunStatus.RUNNING,
    )

    try:
        final_documents: List[Document] = []
        # Create a temp dir to store the data
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Load the data from the source to the dest dir
            loaded_documents = get_loader_for_knowledge_source(
                inputs.knowledge_source.type
            ).load_data(
                inputs.knowledge_source.config.uri, tmpdirname, parsers_map.keys()
            )

            # Count number of documents/files/urls loaded
            docs_to_index_count = len(loaded_documents)
            logger.info("Total docs to index: %s", docs_to_index_count)

            for doc in loaded_documents:
                parser = get_parser_for_extension(doc.file_extension, parsers_map)
                chunks = await parser.get_chunks(
                    doc.filepath,
                    max_chunk_size=inputs.chunk_size,
                )
                for chunk in chunks:
                    chunk.metadata.update(doc.metadata)
                    chunks.append(chunk)

        logger.info("Total chunks to index: %s", len(final_documents))
        print(final_documents[0])

        # Create vectors of all the final_documents
        embeddings = get_embedder(inputs.embedder_config)
        vector_db_client = get_vector_db_client(
            config=inputs.vector_db_config, collection_name=inputs.collection_name
        )

        # Index all the final_documents
        vector_db_client.upsert_documents(
            documents=final_documents, embeddings=embeddings
        )

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


async def trigger_job_locally(inputs: IndexerConfig):
    await index_collection(inputs)
