import json
from typing import List
from uuid import uuid4

from langchain.embeddings.base import Embeddings
from langchain_milvus import Milvus
from langchain_core.vectorstores import VectorStore
from langchain.docstore.document import Document
from pymilvus import MilvusClient, DataType

from backend.logger import logger
from backend.constants import (
    DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    DATA_POINT_FQN_METADATA_KEY,
    DATA_POINT_HASH_METADATA_KEY,
)
from backend.modules.vector_db import BaseVectorDB
from backend.types import DataPointVector, VectorDBConfig

MAX_SCROLL_LIMIT = int(1e6)
BATCH_SIZE = 1000


class MilvusVectorDB(BaseVectorDB):
    def __init__(self, config: VectorDBConfig):
        logger.debug(f"Connecting to milvus using config: {config.model_dump()}")
        if config.local:
            self.uri = config.url if config.url else "./milvus_local.db"
            self.milvus_client = MilvusClient(uri=self.uri)
        else:
            self.uri = config.url
            self.token = config.api_key
            self.milvus_client = MilvusClient(uri=self.uri, token=self.token)

    def create_collection(self, collection_name: str, embeddings: Embeddings):
        """
        Create a new collection in Milvus with the given schema and embedding configuration.

        Args:
            collection_name (str): The name of the collection to be created.
            embeddings (Embeddings): An embedding function to determine vector size.

        Returns:
            None
        """
        logger.debug(f"[Milvus] Creating new collection {collection_name}")

        # Calculate embedding size
        logger.debug(f"[Milvus] Embedding a dummy doc to get vector dimensions")
        partial_embeddings = embeddings.embed_documents(["Initial document"])
        vector_size = len(partial_embeddings[0])
        logger.debug(f"Vector size: {vector_size}")

        schema = self.milvus_client.create_schema(
            auto_id=False, enable_dynamic_field=True
        )

        schema.add_field(
            field_name="id",
            datatype=DataType.VARCHAR,
            is_primary=True,
            max_length=65535,
        )
        schema.add_field(
            field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=vector_size
        )
        schema.add_field(
            field_name="text",
            datatype=DataType.VARCHAR,
            max_length=65535,
        )
        index_params = self.milvus_client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="AUTOINDEX",
            metric_type="COSINE",
        )

        self.milvus_client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params,
        )
        logger.debug(f"[Milvus] Created new collection {collection_name}")

    def _get_records_to_be_upserted(
        self, collection_name: str, data_point_fqns: List[str], incremental: bool
    ) -> List[str]:
        """
        Retrieve record IDs that need to be upserted based on the provided data point FQNs.

        Args:
            collection_name (str): The name of the Milvus collection.
            data_point_fqns (List[str]): A list of fully qualified names (FQNs) of data points to check.
            incremental (bool): Whether to perform incremental updates.

        Returns:
            List[str]: A list of record IDs to be upserted.

        """
        if not incremental or not data_point_fqns:
            return []

        logger.debug(
            f"[Milvus] Incremental Ingestion: Fetching documents for {len(data_point_fqns)} data point fqns for collection {collection_name}"
        )

        try:
            if not data_point_fqns:
                return []
            filter_condition = (
                f"{DATA_POINT_FQN_METADATA_KEY} in {json.dumps(data_point_fqns)}"
            )
            results = self.milvus_client.query(
                collection_name=collection_name,
                filter=filter_condition,
            )
            record_ids_to_be_upserted = []

            for record in results:
                if record.get(DATA_POINT_FQN_METADATA_KEY):
                    record_ids_to_be_upserted.append(record["id"])

            logger.debug(
                f"[Milvus] Incremental Ingestion: collection={collection_name}, Updates={len(record_ids_to_be_upserted)}"
            )
            return record_ids_to_be_upserted
        except Exception as e:
            logger.error(f"[Milvus] Query failed: {str(e)}")
            return []

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Document],
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        """
        Upsert (update or insert) documents into the specified Milvus collection.

        Args:
            collection_name (str): The name of the Milvus collection.
            documents (List[Document]): A list of documents to be upserted.
            embeddings (Embeddings): An embedding function to generate vector representations of the documents.
            incremental (bool): Whether to perform incremental updates by deleting outdated records.

        Returns:
            None
        """

        if len(documents) == 0:
            logger.warning("No documents to index")
            return

        logger.debug(
            f"[Milvus] Adding {len(documents)} documents to collection {collection_name}"
        )

        data_point_fqns = [
            document.metadata.get(DATA_POINT_FQN_METADATA_KEY)
            for document in documents
            if document.metadata.get(DATA_POINT_FQN_METADATA_KEY)
        ]

        record_ids_to_be_upserted = self._get_records_to_be_upserted(
            collection_name=collection_name,
            data_point_fqns=data_point_fqns,
            incremental=incremental,
        )

        if record_ids_to_be_upserted:
            logger.debug(
                f"[Milvus] Deleting {len(record_ids_to_be_upserted)} outdated documents from collection {collection_name}"
            )
            self.milvus_client.delete(
                collection_name=collection_name,
                ids=record_ids_to_be_upserted,
            )
            logger.debug(
                f"[Milvus] Deleted {len(record_ids_to_be_upserted)} outdated documents from collection {collection_name}"
            )
        for doc in documents:
            fqn = doc.metadata.get(DATA_POINT_FQN_METADATA_KEY)
            if not fqn:
                raise ValueError(
                    "[Milvus] Each document must have a unique data_point_fqn"
                )
            doc.metadata["id"] = fqn
            doc.metadata["text"] = doc.page_content

        ids = [doc.metadata["id"] for doc in documents]

        Milvus(
            collection_name=collection_name,
            embedding_function=embeddings,
            connection_args={
                "uri": self.uri,
                "token": self.token,
            },
        ).add_documents(documents=documents, ids=ids)
        logger.debug(
            f"[Milvus] Added {len(documents)} documents to collection {collection_name}"
        )

    def get_collections(self) -> List[str]:
        logger.debug(f"[Milvus] Fetching collections")
        collections = self.milvus_client.list_collections()
        logger.debug(f"[Milvus] Fetched {len(collections)} collections")
        return collections

    def delete_collection(self, collection_name: str):
        logger.debug(f"[Milvus] Deleting {collection_name} collection")
        self.milvus_client.drop_collection(collection_name=collection_name)
        logger.debug(f"[Milvus] Deleted {collection_name} collection")

    def get_vector_store(
        self, collection_name: str, embeddings: Embeddings
    ) -> VectorStore:
        logger.debug(f"[Milvus] Getting vector store for collection {collection_name}")
        return Milvus(
            embedding_function=embeddings,
            collection_name=collection_name,
            connection_args={
                "uri": self.uri,
                "token": self.token,
            },
        )

    def get_vector_client(self):
        logger.debug(f"[Milvus] Getting Milvus client")
        return self.milvus_client

    def list_data_point_vectors(
        self, collection_name: str, data_source_fqn: str, batch_size: int = BATCH_SIZE
    ) -> List[DataPointVector]:
        """
        List all data point vectors for a specific data source in a Milvus collection.

        Args:
            collection_name (str): The name of the Milvus collection.
            data_source_fqn (str): The unique identifier for the data source.
            batch_size (int): The number of records to fetch in each batch.

        Returns:
            List[DataPointVector]: A list of data point vectors with metadata.
        """

        logger.debug(
            f"[Milvus] Listing all data point vectors for collection {collection_name}"
        )

        offset = 0
        total_records_fetched = 0
        data_point_vectors: List[DataPointVector] = []
        stop = False

        while not stop:
            try:
                filter_condition = (
                    f'{DATA_POINT_FQN_METADATA_KEY} == "{data_source_fqn}"'
                )

                results = self.milvus_client.query(
                    collection_name=collection_name,
                    filter=filter_condition,
                    limit=batch_size,
                    offset=offset,
                )

                for record in results:
                    if record.get(DATA_POINT_FQN_METADATA_KEY) and record.get(
                        DATA_POINT_HASH_METADATA_KEY
                    ):
                        data_point_vectors.append(
                            DataPointVector(
                                data_point_vector_id=record["id"],
                                data_point_fqn=record.get(DATA_POINT_FQN_METADATA_KEY),
                                data_point_hash=record.get(
                                    DATA_POINT_HASH_METADATA_KEY
                                ),
                            )
                        )

                total_records_fetched += len(results)
                if len(results) < batch_size:
                    stop = True
                else:
                    offset += batch_size

                if total_records_fetched >= MAX_SCROLL_LIMIT:
                    logger.warning("[Milvus] Reached the maximum scroll limit.")
                    stop = True

            except Exception as e:
                logger.error(f"[Milvus] Query failed: {str(e)}")
                break

        logger.debug(
            f"[Milvus] Listing {len(data_point_vectors)} data point vectors for collection {collection_name}"
        )
        return data_point_vectors

    def delete_data_point_vectors(
        self,
        collection_name: str,
        data_point_vectors: List[DataPointVector],
        batch_size: int = BATCH_SIZE,
    ):
        """
        Delete data point vectors from the collection

        Args:
            collection_name (str): The name of the Milvus collection.
            data_point_vectors (List[DataPointVector]): List of data point vectors to delete.
            batch_size (int): Number of records to delete in each batch.
        """
        logger.debug(f"[Milvus] Deleting {len(data_point_vectors)} data point vectors")

        vectors_to_be_deleted_count = len(data_point_vectors)
        deleted_vectors_count = 0

        for i in range(0, vectors_to_be_deleted_count, batch_size):
            data_point_vectors_to_be_processed = data_point_vectors[i : i + batch_size]

            try:
                self.milvus_client.delete(
                    collection_name=collection_name,
                    ids=[
                        document_vector_point.data_point_vector_id
                        for document_vector_point in data_point_vectors_to_be_processed
                    ],
                )
                deleted_vectors_count += len(data_point_vectors_to_be_processed)

                logger.debug(
                    f"[Milvus] Deleted [{deleted_vectors_count}/{vectors_to_be_deleted_count}] data point vectors"
                )

            except Exception as e:
                logger.error(f"[Milvus] Failed to delete data point vectors: {str(e)}")
                break

        logger.debug(
            f"[Milvus] Deleted {deleted_vectors_count} data point vectors from collection {collection_name}"
        )

    def list_documents_in_collection(
        self,
        collection_name: str,
        base_document_id: str = None,
        batch_size: int = BATCH_SIZE,
    ) -> List[str]:
        """
        List all documents in a Milvus collection, optionally filtering by base document ID.

        Args:
            collection_name (str): The name of the Milvus collection.
            base_document_id (str, optional): The base document ID to filter by. Defaults to None.
            batch_size (int): The number of records to fetch per query. Defaults to BATCH_SIZE.

        Returns:
            List[str]: A list of unique document IDs in the collection.
        """
        logger.debug(
            f"[Milvus] Listing all documents with base document ID {base_document_id} for collection {collection_name}"
        )

        offset = 0
        document_ids_set = set()
        stop = False

        while not stop:
            try:
                if base_document_id:
                    filter_condition = (
                        f'{DATA_POINT_FQN_METADATA_KEY} == "{base_document_id}"'
                    )
                else:
                    filter_condition = None

                results = self.milvus_client.query(
                    collection_name=collection_name,
                    filter=filter_condition,
                    limit=batch_size,
                    offset=offset,
                )

                for record in results:
                    document_id = record.get(DATA_POINT_FQN_METADATA_KEY)
                    if document_id:
                        document_ids_set.add(document_id)

                if len(results) < batch_size:
                    stop = True
                else:
                    offset += batch_size

                if len(document_ids_set) > MAX_SCROLL_LIMIT:
                    logger.warning("[Milvus] Reached the maximum scroll limit.")
                    stop = True

            except Exception as e:
                logger.error(f"[Milvus] Query failed: {str(e)}")
                break

        logger.debug(
            f"[Milvus] Found {len(document_ids_set)} documents with base document ID {base_document_id} for collection {collection_name}"
        )
        return list(document_ids_set)

    def delete_documents(self, collection_name: str, document_ids: List[str]):
        """
        Delete documents from the collection.

        Args:
            collection_name (str): The name of the Milvus collection.
            document_ids (List[str]): List of document IDs to delete.

        Returns:
            None
        """
        logger.debug(
            f"[Milvus] Deleting {len(document_ids)} documents from collection {collection_name}"
        )

        for i in range(0, len(document_ids), BATCH_SIZE):
            document_ids_to_be_processed = document_ids[i : i + BATCH_SIZE]

            try:
                if not document_ids_to_be_processed:
                    continue
                filter_condition = f"{DATA_POINT_FQN_METADATA_KEY} in {json.dumps(document_ids_to_be_processed)}"
                self.milvus_client.delete(
                    collection_name=collection_name,
                    filter=filter_condition,
                )
                logger.debug(
                    f"[Milvus] Deleted batch of {len(document_ids_to_be_processed)} documents from collection {collection_name}"
                )
            except Exception as e:
                logger.error(f"[Milvus] Failed to delete documents: {str(e)}")

    def list_document_vector_points(
        self, collection_name: str
    ) -> List[DataPointVector]:
        """
        List all document vector points in a Milvus collection.

        Args:
            collection_name (str): The name of the Milvus collection.

        Returns:
            List[DataPointVector]: A list of document vector points with metadata.
        """
        logger.debug(
            f"[Milvus] Listing all document vector points for collection {collection_name}"
        )

        offset = 0
        document_vector_points: List[DataPointVector] = []
        stop = False

        while not stop:
            try:
                results = self.milvus_client.query(
                    collection_name=collection_name,
                    limit=BATCH_SIZE,
                    offset=offset,
                )

                for record in results:
                    if record.get(DATA_POINT_FQN_METADATA_KEY) and record.get(
                        DATA_POINT_HASH_METADATA_KEY
                    ):
                        document_vector_points.append(
                            DataPointVector(
                                point_id=record["id"],
                                document_id=record.get(DATA_POINT_FQN_METADATA_KEY),
                                document_hash=record.get(DATA_POINT_HASH_METADATA_KEY),
                            )
                        )

                if len(results) < BATCH_SIZE:
                    stop = True
                else:
                    offset += BATCH_SIZE

                if len(document_vector_points) > MAX_SCROLL_LIMIT:
                    logger.warning("[Milvus] Reached the maximum scroll limit.")
                    stop = True

            except Exception as e:
                logger.error(f"[Milvus] Query failed: {str(e)}")
                break

        logger.debug(
            f"[Milvus] Listed {len(document_vector_points)} document vector points for collection {collection_name}"
        )
        return document_vector_points
