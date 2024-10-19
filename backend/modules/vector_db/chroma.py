from typing import List, Optional, Union

from chromadb import HttpClient, PersistentClient
from chromadb.api import ClientAPI
from fastapi import HTTPException
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings

from backend.constants import DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE
from backend.modules.vector_db.base import BaseVectorDB
from backend.types import VectorDBConfig


class ChromaVectorDB(BaseVectorDB):
    def __init__(self, db_config: VectorDBConfig):
        self.db_config = db_config
        self.client = self.get_client()

    def get_client(self) -> ClientAPI:
        # For local development, we use a persistent client that saves data to a temporary directory
        if self.db_config.local:
            return PersistentClient()

        # For production, we use an http client that connects to a remote server
        return HttpClient(
            url=self.db_config.url,
            api_key=self.db_config.api_key,
            config=self.db_config.config,
        )

    def get_vector_client(self) -> Union[PersistentClient, HttpClient]:
        return self.client

    def get_vector_store(self, collection_name: str, embeddings: Embeddings):
        pass

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
    ):
        return self.client.list_collections(limit=limit, offset=offset)

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

    def list_data_point_vectors(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ):
        return super().list_data_point_vectors(
            collection_name, data_source_fqn, batch_size
        )

    def delete_data_point_vectors(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ):
        return super().delete_data_point_vectors(
            collection_name, data_source_fqn, batch_size
        )
