from abc import ABC, abstractmethod
from typing import List

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.schema.vectorstore import VectorStore


class BaseVectorDB(ABC):
    @abstractmethod
    def create_collection(self, collection_name: str, embeddings: Embeddings):
        """
        Create a collection in the vector database
        """
        raise NotImplementedError()

    @abstractmethod
    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Document],
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        """
        Upsert documents into the vector database
        """
        raise NotImplementedError()

    @abstractmethod
    def get_collections(self) -> List[str]:
        """
        Get all collection names from the vector database
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_collection(self, collection_name: str):
        """
        Delete a collection from the vector database
        """
        raise NotImplementedError()

    @abstractmethod
    def get_vector_store(
        self, collection_name: str, embeddings: Embeddings
    ) -> VectorStore:
        """
        Get vector store
        """
        raise NotImplementedError()

    @abstractmethod
    def list_documents_in_collection(
        self, collection_name: str, base_document_id: str = None
    ) -> List[dict]:
        """
        List all documents in a collection
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_documents(self, collection_name: str, document_ids: List[str]):
        """
        Delete documents from the collection with given `document_ids`
        """
        raise NotImplementedError()

    @abstractmethod
    def get_vector_ids(self, collection_name: str):
        """
        Get vectors from the collection
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_vectors(self, vector_ids: List[str]):
        """
        Delete vectors from the collection
        """
        raise NotImplementedError()

    @abstractmethod
    def get_vector_client(self):
        """
        Get vector client
        """
        raise NotImplementedError()
