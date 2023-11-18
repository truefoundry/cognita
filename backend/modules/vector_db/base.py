from abc import ABC, abstractmethod
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
    def delete_collection(self):
        """
        Delete a collection from the vector database
        """
        raise NotImplementedError()

    def get_retriver(self, embeddings: Embeddings) -> VectorStoreRetriever:
        """
        Get a retriver for the collection
        """
        raise NotImplementedError()
