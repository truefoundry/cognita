import uuid
from typing import List

from backend.modules.metadata_store.base import BaseMetadataStore
from backend.modules.metadata_store.models import (
    Collection, CollectionCreate, CollectionIndexerJobRun,
    CollectionIndexerJobRunCreate, CollectionIndexerJobRunStatus)
from backend.utils.base import EmbedderConfig, KnowledgeSource, ParserConfig
from backend.utils.logger import logger


class ConsoleStore(BaseMetadataStore):
    collections: List[Collection] = []

    def create_collection(self, collection: CollectionCreate) -> Collection:
        """
        Create a collection in the metadata store and save its metadata
        """
        logger.info(
            f"Creating new collection with name: {collection.name}, embedding_config: {collection.embedder_config}, chunk_size: {collection.chunk_size}"
        )
        new_collection = Collection(
            name=collection.name,
            embedder_config=collection.embedder_config,
            chunk_size=collection.chunk_size,
            indexer_job_runs=[],
        )
        self.collections.append(new_collection)
        return new_collection

    def get_collection_by_name(
        self, collection_name: str, include_runs=False
    ) -> Collection:
        """
        Get a collection from the metadata store by name
        """
        return next(
            collection
            for collection in self.collections
            if collection.name == collection_name
        )

    def get_collections(
        self, names: List[str] = None, include_runs=False
    ) -> List[Collection]:
        """
        Get all collections from the metadata store
        """
        return self.collections

    def get_collection_indexer_job_runs(self, collection_name: str):
        """
        Get all collection indexer job runs for a collection
        """
        collection = next(
            collection
            for collection in self.collections
            if collection.name == collection_name
        )
        return collection.indexer_job_runs

    def create_collection_indexer_job_run(
        self, collection_name: str, indexer_job_run: CollectionIndexerJobRunCreate
    ) -> CollectionIndexerJobRun:
        """
        Create a collection indexer job run for a collection
        """
        collection = next(
            collection
            for collection in self.collections
            if collection.name == collection_name
        )
        self.collections.remove(collection)

        new_indexer_job_run = CollectionIndexerJobRun(
            name=f"{collection_name}-{uuid.uuid4()}",
            knowledge_source=indexer_job_run.knowledge_source,
            parser_config=indexer_job_run.parser_config,
            status=CollectionIndexerJobRunStatus.INITIALIZED,
        )

        collection.indexer_job_runs.append(new_indexer_job_run)

        self.collections.append(collection)
        return new_indexer_job_run

    def delete_collection(self, collection_name: str):
        """
        Delete a collection from the metadata store
        """
        self.collections = [
            collection
            for collection in self.collections
            if collection.name != collection_name
        ]

    def update_indexer_job_run_status(
        self,
        collection_inderer_job_run_name: str,
        status: CollectionIndexerJobRunStatus,
    ):
        """
        Update the status of a collection indexer job run
        """
        collection = next(
            collection
            for collection in self.collections
            if next(
                indexer_job_run
                for indexer_job_run in collection.indexer_job_runs
                == collection_inderer_job_run_name
            )
        )
        self.collections.remove(collection)
        indexer_job_run = next(
            indexer_job_run
            for indexer_job_run in collection.indexer_job_runs
            if indexer_job_run.name == collection_inderer_job_run_name
        )
        collection.indexer_job_runs.remove(indexer_job_run)
        indexer_job_run.status = status
        collection.indexer_job_runs.append(indexer_job_run)
        self.collections.append(collection)
