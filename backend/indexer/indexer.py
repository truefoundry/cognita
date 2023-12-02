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
from backend.utils.utils import get_base_document_id

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
            ).load_data(inputs.knowledge_source.config, tmpdirname, parsers_map.keys())

            # Count number of documents/files/urls loaded
            docs_to_index_count = len(loaded_documents)
            logger.info("Total docs to index: %s", docs_to_index_count)

            for doc in loaded_documents:
                parser = get_parser_for_extension(
                    file_extension=doc.file_extension, parsers_map=parsers_map
                )
                chunks = await parser.get_chunks(
                    filepath=doc.filepath,
                    max_chunk_size=inputs.chunk_size,
                )
                for chunk in chunks:
                    chunk.metadata.update(doc.metadata.dict())
                    final_documents.append(chunk)
                logger.info("%s -> %s chunks", doc.filepath, len(chunks))

        logger.info("Total chunks to index: %s", len(final_documents))

        if len(final_documents) == 0:
            logger.warning("No documents to index")
            metadata_store_client.update_indexer_job_run_status(
                collection_inderer_job_run_name=inputs.indexer_job_run_name,
                status=CollectionIndexerJobRunStatus.COMPLETED,
            )
            return

        # Create vectors of all the final_documents
        embeddings = get_embedder(inputs.embedder_config)
        vector_db_client = get_vector_db_client(
            config=inputs.vector_db_config, collection_name=inputs.collection_name
        )

        # Delete all the documents with the same base_document_id to avoid duplicate data
        # Note: Since by default we enable embedding caching, we do not have to bare any embedding model cost
        vector_db_client.delete_documents(
            document_id_match=get_base_document_id(source=inputs.knowledge_source)
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
