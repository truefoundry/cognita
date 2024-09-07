from abc import ABC, abstractmethod
from typing import Generator, List, Optional

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.schema.vectorstore import VectorStore

from backend.constants import DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE
from backend.logger import logger
from backend.types import DataPointVector

MAX_SCROLL_LIMIT = int(1e6)


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
    def get_vector_client(self):
        """
        Get vector client
        """
        raise NotImplementedError()

    @abstractmethod
    def yield_data_point_vector_batches(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ) -> Generator[List[DataPointVector], None, Optional[List[DataPointVector]]]:
        """
        Yield vectors from the collection
        """
        raise NotImplementedError()

    def list_data_point_vectors(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ) -> List[DataPointVector]:
        """
        Get vectors from the collection
        """
        logger.debug(
            f"Listing all data point vectors for collection {collection_name}"
        )
        data_point_vectors = []
        for batch in self.yield_data_point_vector_batches(
            collection_name, data_source_fqn, batch_size
        ):
            data_point_vectors.extend(batch)
            if len(data_point_vectors) >= MAX_SCROLL_LIMIT:
                break
        logger.debug(
            f"Listing {len(data_point_vectors)} data point vectors for collection {collection_name}"
        )
        return data_point_vectors

    @abstractmethod
    def delete_data_point_vectors(
        self,
        collection_name: str,
        data_point_vectors: List[DataPointVector],
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ):
        """
        Delete vectors from the collection
        """
        raise NotImplementedError()

    def delete_data_point_vectors_by_data_source(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ):
        """
        Delete vectors from the collection based on data_source_fqn
        """
        for data_points_batch in self.yield_data_point_vector_batches(
            collection_name=collection_name,
            data_source_fqn=data_source_fqn,
            batch_size=batch_size,
        ):
            self.delete_data_point_vectors(
                collection_name=collection_name, data_point_vectors=data_points_batch
            ),
