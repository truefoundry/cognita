import time
from typing import List

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.schema.vectorstore import VectorStore
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

from backend.constants import (
    DATA_POINT_FQN_METADATA_KEY,
    DATA_POINT_HASH_METADATA_KEY,
    DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
)
from backend.logger import logger
from backend.modules.vector_db.base import BaseVectorDB
from backend.types import DataPointVector, VectorDBConfig

MAX_SCROLL_LIMIT = int(1e6)
BATCH_SIZE = 1000


class MongoVectorDB(BaseVectorDB):
    def __init__(self, config: VectorDBConfig):
        """Initialize MongoDB vector database client"""
        self.config = config
        self.client = MongoClient(config.url)
        self.db = self.client[config.config.get("database_name")]

    def create_collection(self, collection_name: str, embeddings: Embeddings) -> None:
        """Create a collection with vector search index"""
        if collection_name in self.db.list_collection_names():
            raise ValueError(f"Collection {collection_name} already exists in MongoDB")

        # Create the collection first
        self.db.create_collection(collection_name)

        # Define the search index model
        self._create_search_index(collection_name, embeddings)

    def _create_search_index(self, collection_name: str, embeddings: Embeddings):
        # Mongo DB requires a vector search index to be created with a specific configuration
        # Number of dimensions are calculated based on the embedding model. We use a sample text to get the number of dimensions
        # Similarity is set to cosine as we are using cosine similarity for the vector search. This can be changed to euclidean, dotproduct etc as per the requirements.
        # Path is set to "embedding" as embeddings are stored in the "embedding" field in the collection by default in MongoDB.
        # Reference: https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-type/
        search_index_model = SearchIndexModel(
            definition={
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": self.get_embedding_dimensions(embeddings),
                        "similarity": "cosine",
                    }
                ]
            },
            name="vector_search_index",
            type="vectorSearch",
        )

        # Create the search index
        result = self.db[collection_name].create_search_index(model=search_index_model)
        logger.debug(f"New search index named {result} is building.")

        # Immediate avaialbility of the index is not guaranteed upon creation.
        # MongoDB documentation recommends polling for the index to be ready.
        # Ensure this check to provide a seamless experience.
        # TODO (mnvsk97): We might want to introduce a new status in the ingestion runs to reflex this.
        logger.debug(
            "Polling to check if the index is ready. This may take up to a minute."
        )
        predicate = lambda index: index.get("queryable") is True
        while True:
            indices = list(
                self.db[collection_name].list_search_indexes("vector_search_index")
            )
            if len(indices) and predicate(indices[0]):
                break
            time.sleep(5)
        logger.debug(f"{result} is ready for querying.")

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Document],
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        if len(documents) == 0:
            logger.warning("No documents to index")
            return
        # get record IDs to be upserted
        logger.debug(
            f"[Mongo] Adding {len(documents)} documents to collection {collection_name}"
        )

        """Upsert documenlots with their embeddings"""
        collection = self.db[collection_name]

        data_point_fqns = []
        for document in documents:
            if document.metadata.get(DATA_POINT_FQN_METADATA_KEY):
                data_point_fqns.append(
                    document.metadata.get(DATA_POINT_FQN_METADATA_KEY)
                )

        logger.debug(f"[Mongo] documents: {documents}")

        record_ids_to_be_upserted: List[str] = self._get_records_to_be_upserted(
            collection_name=collection_name,
            data_point_fqns=data_point_fqns,
            incremental=incremental,
        )

        # Add Documents
        MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embeddings,
        ).add_documents(documents=documents)
        logger.debug(
            f"[Mongo] Added {len(documents)} documents to collection {collection_name}"
        )

        if len(record_ids_to_be_upserted) > 0:
            logger.debug(
                f"[Mongo] Deleting {len(record_ids_to_be_upserted)} outdated documents from collection {collection_name}"
            )
            for i in range(
                0, len(record_ids_to_be_upserted), DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE
            ):
                record_ids_to_be_processed = record_ids_to_be_upserted[
                    i : i + DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE
                ]
                collection.delete_many({"_id": {"$in": record_ids_to_be_processed}})
            logger.debug(
                f"[Mongo] Deleted {len(record_ids_to_be_upserted)} outdated documents from collection {collection_name}"
            )

    def _get_records_to_be_upserted(
        self, collection_name: str, data_point_fqns: List[str], incremental: bool = True
    ) -> List[str]:
        """Get record IDs to be upserted"""
        if not incremental:
            return []

        # For incremental deletion, we delete the documents with the same document_id
        logger.debug(
            f"[Mongo] Incremental Ingestion: Fetching documents for {len(data_point_fqns)} data point fqns for collection {collection_name}"
        )

        collection = self.db[collection_name]
        record_ids_to_be_upserted = []

        # Query in batches to avoid memory issues
        for i in range(0, len(data_point_fqns), DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE):
            batch_fqns = data_point_fqns[i : i + DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE]

            cursor = collection.find(
                {f"metadata.{DATA_POINT_FQN_METADATA_KEY}": {"$in": batch_fqns}},
                {"_id": 1},
            )

            for doc in cursor:
                record_ids_to_be_upserted.append(doc["_id"])
                if len(record_ids_to_be_upserted) > MAX_SCROLL_LIMIT:
                    break

            if len(record_ids_to_be_upserted) > MAX_SCROLL_LIMIT:
                break

        logger.debug(
            f"[Mongo] Incremental Ingestion: collection={collection_name} Addition={len(data_point_fqns)}, Updates={len(record_ids_to_be_upserted)}"
        )
        return record_ids_to_be_upserted

    def get_collections(self) -> List[str]:
        """Get all collection names"""
        return self.db.list_collection_names()

    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        self.db.drop_collection(collection_name)

    def get_vector_store(
        self, collection_name: str, embeddings: Embeddings
    ) -> VectorStore:
        """Get MongoDB Atlas vector store instance"""
        return MongoDBAtlasVectorSearch(
            collection=self.db[collection_name],
            embedding=embeddings,
            index_name="vector_search_index",
        )

    def get_vector_client(self):
        """Get MongoDB client"""
        return self.client

    def list_data_point_vectors(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ) -> List[DataPointVector]:
        logger.debug(
            f"[Mongo] Listing all data point vectors for collection {collection_name}"
        )
        stop = False
        offset = None
        data_point_vectors: List[DataPointVector] = []
        collection = self.db[collection_name]

        while stop is not True:
            batch_cursor = (
                collection.find(
                    {f"metadata.{DATA_POINT_FQN_METADATA_KEY}": data_source_fqn},
                    {
                        "_id": 1,
                        f"metadata.{DATA_POINT_FQN_METADATA_KEY}": 1,
                        f"metadata.{DATA_POINT_HASH_METADATA_KEY}": 1,
                    },
                )
                .skip(offset if offset else 0)
                .limit(batch_size)
            )

            # Convert cursor to list to check if we got any results
            batch_results = list(batch_cursor)
            if not batch_results:
                stop = True
                break

            for doc in batch_results:
                metadata = doc.get("metadata", {})
                if metadata.get(DATA_POINT_FQN_METADATA_KEY) and metadata.get(
                    DATA_POINT_HASH_METADATA_KEY
                ):
                    data_point_vectors.append(
                        DataPointVector(
                            data_point_vector_id=str(doc["_id"]),
                            data_point_fqn=metadata.get(DATA_POINT_FQN_METADATA_KEY),
                            data_point_hash=metadata.get(DATA_POINT_HASH_METADATA_KEY),
                        )
                    )
                if len(data_point_vectors) > MAX_SCROLL_LIMIT:
                    stop = True
                    break

            if len(batch_results) < batch_size:
                stop = True
            else:
                offset = (offset if offset else 0) + batch_size

        logger.debug(
            f"[Mongo] Listing {len(data_point_vectors)} data point vectors for collection {collection_name}"
        )
        return data_point_vectors

    def delete_data_point_vectors(
        self,
        collection_name: str,
        data_point_vectors: List[DataPointVector],
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ):
        """Delete vectors by their IDs"""
        collection = self.db[collection_name]
        vector_ids = [vector.id for vector in data_point_vectors]

        # Delete in batches
        for i in range(0, len(vector_ids), batch_size):
            batch = vector_ids[i : i + batch_size]
            collection.delete_many({"_id": {"$in": batch}})

    def list_documents_in_collection(
        self, collection_name: str, base_document_id: str = None
    ) -> List[str]:
        """
        List all documents in a collection
        """
        logger.debug(
            f"[Mongo] Listing all documents with base document id {base_document_id} for collection {collection_name}"
        )
        stop = False
        offset = None
        document_ids_set = set()
        collection = self.db[collection_name]

        while stop is not True:
            batch_cursor = (
                collection.find(
                    {f"metadata.{DATA_POINT_FQN_METADATA_KEY}": base_document_id}
                    if base_document_id
                    else {},
                    {f"metadata.{DATA_POINT_FQN_METADATA_KEY}": 1},
                )
                .skip(offset if offset else 0)
                .limit(BATCH_SIZE)
            )

            # Convert cursor to list to check if we got any results
            batch_results = list(batch_cursor)
            if not batch_results:
                stop = True
                break

            for doc in batch_results:
                if doc.get("metadata") and doc.get("metadata").get(
                    DATA_POINT_FQN_METADATA_KEY
                ):
                    document_ids_set.add(
                        doc.get("metadata").get(DATA_POINT_FQN_METADATA_KEY)
                    )
                if len(document_ids_set) > MAX_SCROLL_LIMIT:
                    stop = True
                    break

            if len(batch_results) < BATCH_SIZE:
                stop = True
            else:
                offset = (offset if offset else 0) + BATCH_SIZE

        logger.debug(
            f"[Mongo] Found {len(document_ids_set)} documents with base document id {base_document_id} for collection {collection_name}"
        )
        return list(document_ids_set)

    def delete_documents(self, collection_name: str, document_ids: List[str]):
        """
        Delete documents from the collection
        """
        logger.debug(
            f"[Mongo] Deleting {len(document_ids)} documents from collection {collection_name}"
        )
        try:
            collection = self.db[collection_name]
        except Exception as exp:
            logger.debug(exp)
            return

        for i in range(0, len(document_ids), BATCH_SIZE):
            document_ids_to_be_processed = document_ids[i : i + BATCH_SIZE]
            collection.delete_many(
                {
                    f"metadata.{DATA_POINT_FQN_METADATA_KEY}": {
                        "$in": document_ids_to_be_processed
                    }
                }
            )

        logger.debug(
            f"[Mongo] Deleted {len(document_ids)} documents from collection {collection_name}"
        )

    def list_document_vector_points(
        self, collection_name: str
    ) -> List[DataPointVector]:
        """
        List all documents in a collection
        """
        logger.debug(
            f"[Mongo] Listing all document vector points for collection {collection_name}"
        )
        stop = False
        offset = None
        document_vector_points: List[DataPointVector] = []
        collection = self.db[collection_name]

        while stop is not True:
            batch_cursor = (
                collection.find(
                    {},
                    {
                        "_id": 1,
                        f"metadata.{DATA_POINT_FQN_METADATA_KEY}": 1,
                        f"metadata.{DATA_POINT_HASH_METADATA_KEY}": 1,
                    },
                )
                .skip(offset if offset else 0)
                .limit(BATCH_SIZE)
            )

            # Convert cursor to list to check if we got any results
            batch_results = list(batch_cursor)
            if not batch_results:
                stop = True
                break

            for doc in batch_results:
                metadata = doc.get("metadata", {})
                if metadata.get(DATA_POINT_FQN_METADATA_KEY) and metadata.get(
                    DATA_POINT_HASH_METADATA_KEY
                ):
                    document_vector_points.append(
                        DataPointVector(
                            point_id=str(doc["_id"]),
                            document_id=metadata.get(DATA_POINT_FQN_METADATA_KEY),
                            document_hash=metadata.get(DATA_POINT_HASH_METADATA_KEY),
                        )
                    )
                if len(document_vector_points) > MAX_SCROLL_LIMIT:
                    stop = True
                    break

            if len(batch_results) < BATCH_SIZE:
                stop = True
            else:
                offset = (offset if offset else 0) + BATCH_SIZE

        logger.debug(
            f"[Mongo] Listed {len(document_vector_points)} document vector points for collection {collection_name}"
        )
        return document_vector_points
