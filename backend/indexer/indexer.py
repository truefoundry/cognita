import tempfile
from typing import List

from langchain.docstore.document import Document

from backend.indexer.types import IndexerConfig
from backend.logger import logger
from backend.modules.dataloaders.loader import get_loader_for_data_source
from backend.modules.embedder.embedder import get_embedder
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.modules.metadata_store.models import CollectionIndexerJobRunStatus
from backend.modules.parsers.parser import (
    get_parser_for_extension,
    get_parsers_configurations,
)
from backend.modules.vector_db import get_vector_db_client
from backend.types import IndexingMode
from backend.utils import get_base_document_id


async def upsert_documents_to_collection(inputs: IndexerConfig):
    try:
        parsers_map = get_parsers_configurations(inputs.parser_config)

        # Set the status of the collection run to running
        METADATA_STORE_CLIENT.update_indexer_job_run_status(
            collection_inderer_job_run_name=inputs.indexer_job_run_name,
            status=CollectionIndexerJobRunStatus.DATA_LOADING_STARTED,
        )
        embeddings = get_embedder(
            embedder_config=inputs.embedder_config,
        )
        vector_db_client = get_vector_db_client(
            config=inputs.vector_db_config, collection_name=inputs.collection_name
        )

        # Create a temp dir to store the data
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Load the data from the source to the dest dir
            loaded_documents = get_loader_for_data_source(
                inputs.data_source.type
            ).load_data(
                data_source=inputs.data_source,
                dest_dir=tmpdirname,
                allowed_extensions=parsers_map.keys(),
            )

            METADATA_STORE_CLIENT.update_indexer_job_run_status(
                collection_inderer_job_run_name=inputs.indexer_job_run_name,
                status=CollectionIndexerJobRunStatus.CHUNKING_STARTED,
            )

            # Count number of documents/files/urls loaded
            docs_to_index_count = len(loaded_documents)
            if docs_to_index_count == 0:
                logger.warning("No documents to found")
                METADATA_STORE_CLIENT.update_indexer_job_run_status(
                    collection_inderer_job_run_name=inputs.indexer_job_run_name,
                    status=CollectionIndexerJobRunStatus.COMPLETED,
                )
                return

            logger.info("Total docs to index: %s", docs_to_index_count)
            METADATA_STORE_CLIENT.log_metrics_for_indexer_job_run(
                collection_inderer_job_run_name=inputs.indexer_job_run_name,
                metric_dict={"num_files": docs_to_index_count},
            )

            # Batch processing the documents
            for i in range(0, docs_to_index_count, inputs.batch_size):
                documents_to_be_processed = loaded_documents[i : i + inputs.batch_size]
                documents_to_be_uppserted: List[Document] = []
                for index, doc in enumerate(documents_to_be_processed):
                    parser = get_parser_for_extension(
                        file_extension=doc.file_extension, parsers_map=parsers_map
                    )
                    chunks = await parser.get_chunks(
                        document=doc,
                        max_chunk_size=inputs.chunk_size,
                    )
                    documents_to_be_uppserted.extend(chunks)
                    logger.info("%s -> %s chunks", doc.filepath, len(chunks))
                    METADATA_STORE_CLIENT.log_metrics_for_indexer_job_run(
                        collection_inderer_job_run_name=inputs.indexer_job_run_name,
                        metric_dict={"num_chunks": len(chunks)},
                        step=index,
                    )

                if len(documents_to_be_uppserted) == 0:
                    logger.warning(f"No chunks to index in batch {i}")
                    continue

                logger.info(
                    f"Total chunks to index in batch {i}: {len(documents_to_be_uppserted)}"
                )
                # Upserted all the documents_to_be_ingested
                vector_db_client.upsert_documents(
                    documents=documents_to_be_uppserted,
                    embeddings=embeddings,
                    incremental=inputs.indexing_mode == IndexingMode.INCREMENTAL,
                )

        if inputs.indexing_mode == IndexingMode.FULL:
            # Delete the documents that are present in vector db but not in source loaded documents
            base_document_id = get_base_document_id(inputs.data_source)
            existing_document_ids = vector_db_client.list_documents_in_collection(
                base_document_id=base_document_id
            )
            updated_document_ids = set(
                [doc.metadata._document_id for doc in loaded_documents]
            )
            document_ids_to_be_deleted = []
            for id in existing_document_ids:
                if id not in updated_document_ids:
                    document_ids_to_be_deleted.append(id)
            logger.info(
                f"Deleting {len(document_ids_to_be_deleted)} documents from the collection"
            )
            vector_db_client.delete_documents(document_ids=document_ids_to_be_deleted)

        METADATA_STORE_CLIENT.update_indexer_job_run_status(
            collection_inderer_job_run_name=inputs.indexer_job_run_name,
            status=CollectionIndexerJobRunStatus.COMPLETED,
        )

    except Exception as e:
        logger.error(e)
        METADATA_STORE_CLIENT.update_indexer_job_run_status(
            collection_inderer_job_run_name=inputs.indexer_job_run_name,
            status=CollectionIndexerJobRunStatus.FAILED,
        )
        raise e
