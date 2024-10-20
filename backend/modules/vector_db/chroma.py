from typing import List, Optional

from chromadb import HttpClient, PersistentClient
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from fastapi import HTTPException
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores import Chroma

from backend.constants import DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE
from backend.modules.vector_db.base import BaseVectorDB
from backend.types import ChromaVectorDBConfig


class ChromaVectorDB(BaseVectorDB):
    def __init__(self, db_config: ChromaVectorDBConfig):
        self.db_config = db_config
        self.client = self._create_client()

    ## Initialization utility

    def _create_client(self) -> ClientAPI:
        # For local development, we use a persistent client that saves data to a temporary directory
        if self.db_config.local:
            return PersistentClient()

        # For production, we use an http client that connects to a remote server
        return HttpClient(
            url=self.db_config.url,
            api_key=self.db_config.api_key,
            config=self.db_config.config,
        )

    ## Client
    def get_vector_client(self) -> ClientAPI:
        return self.client

    ## Vector store

    def get_vector_store(self, collection_name: str, **kwargs):
        return Chroma(
            client=self.client,
            collection_name=collection_name,
            **kwargs,
        )

    ## Collections

    def create_collection(self, collection_name: str, **kwargs):
        try:
            return self.client.create_collection(
                name=collection_name,
                **kwargs,
            )
        except ValueError as e:
            # Error is raised if
            # 1. collection already exists
            # 2. collection name is invalid
            raise HTTPException(
                status_code=400, detail=f"Unable to create collection: {e}"
            )

    def get_collection(self, collection_name: str):
        return self.client.get_collection(name=collection_name)

    def delete_collection(self, collection_name: str):
        try:
            return self.client.delete_collection(name=collection_name)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Unable to delete collection. {collection_name} does not exist",
            )

    def list_collections(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Collection]:
        return self.client.list_collections(limit=limit, offset=offset)

    def get_collections(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Collection]:
        return self.client.list_collections(limit=limit, offset=offset)

    ## Documents

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Document],
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        return super().upsert_documents(
            collection_name, documents, embeddings, incremental
        )

    def delete_documents(self, collection_name: str, document_ids: List[str]):
        # Fetch the collection
        collection: Collection = self.client.get_collection(collection_name)
        # Delete the documents in the collection by ids
        collection.delete(ids=document_ids)

    ## Data point vectors

    def list_data_point_vectors(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ):
        pass

    def delete_data_point_vectors(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ):
        return super().delete_data_point_vectors(
            collection_name, data_source_fqn, batch_size
        )
