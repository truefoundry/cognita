from abc import ABC, abstractmethod
from typing import List

from langchain.embeddings.base import Embeddings
from langchain.schema.vectorstore import VectorStoreRetriever


class BaseVectorDB(ABC):
    @abstractmethod
    def create_collection(self, embeddings: Embeddings):
        """
        Create a collection in the vector database
        """
        raise NotImplementedError()

    @abstractmethod
    def upsert_documents(self, documents, embeddings: Embeddings):
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
    def delete_collection(self):
        """
        Delete a collection from the vector database
        """
        raise NotImplementedError()

    @abstractmethod
    def get_retriever(self, embeddings: Embeddings, k: int) -> VectorStoreRetriever:
        """
        Get a retriever for the collection
        """
        raise NotImplementedError()
