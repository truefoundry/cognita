from typing import List
from langchain.embeddings.base import Embeddings
from langchain.docstore.document import Document
from langchain_milvus import Milvus
from pymilvus import MilvusClient, DataType, CollectionSchema, FieldSchema

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


class MilvusVectorDB(BaseVectorDB):
    def __init__(self, config: VectorDBConfig):
        """
        Initialize Milvus vector database client
        Args:
        :param config: VectorDBConfig
            -   provider: str
            -   local: bool
            -   url: str
                URI of the Milvus server.
                    - If you only need a local vector database for small scale data or prototyping,
                    setting the uri as a local file, e.g.`./milvus.db`, is the most convenient method,
                    as it automatically utilizes [Milvus Lite](https://milvus.io/docs/milvus_lite.md)
                    to store all data in this file.
                    - If you have large scale of data, say more than a million vectors, you can set up
                    a more performant Milvus server on [Docker or Kubernetes](https://milvus.io/docs/quickstart.md).
                    In this setup, please use the server address and port as your uri, e.g.`http://localhost:19530`.
                    If you enable the authentication feature on Milvus,
                    use "<your_username>:<your_password>" as the token, otherwise don't set the token.
                    - If you use [Zilliz Cloud](https://zilliz.com/cloud), the fully managed cloud
                    service for Milvus, adjust the `uri` and `token`, which correspond to the
                    [Public Endpoint and API key](https://docs.zilliz.com/docs/on-zilliz-cloud-console#cluster-details)
            -   api_key: str
                Token for authentication with the Milvus server.
        """
        # TODO: create an extended config for Milvus like done in Qdrant
        logger.debug(f"Connecting to Milvus using config: {config.model_dump()}")
        if config.local is True:
            self.milvus_client = MilvusClient(
                "./cognita_milvus.db",
                db_name=config.config.get("db_name", "milvus_default_db"),
            )
        else:
            url = config.url
            api_key = config.api_key
            if not api_key:
                api_key = None

            self.milvus_client = MilvusClient(
                uri=url,
                token=api_key,
                db_name=config.config.get("db_name", "milvus_default_db"),
            )

    def create_collection(self, collection_name: str, embeddings: Embeddings):
        """
        Create a collection in the vector database
        Args:
        :param collection_name: str - Name of the collection
        :param embeddings: Embeddings - Embeddings object to be used for creating embeddings of the documents
        Current implementation includes Quick setup in which the collection is created, indexed and loaded into the memory.

        """
        # TODO: Add customized setup with indexed params
        logger.debug(f"[Milvus] Creating new collection {collection_name}")

        vector_size = self.get_embedding_dimensions(embeddings)

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=vector_size),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]

        schema = CollectionSchema(
            fields=fields, description=f"Collection for {collection_name}"
        )

        self.milvus_client.create_collection(
            collection_name=collection_name,
            dimension=vector_size,
            metric_type="COSINE",  # https://milvus.io/docs/metric.md#Metric-Types : check for other supported metrics
            schema=schema,
        )

        # Can use this to create custom multiple indices
        index_params = self.milvus_client.prepare_index_params()
        index_params.add_index(
            field_name="vector", index_type="IVF_FLAT", metric_type="L2"
        )
        self.milvus_client.create_index(
            collection_name=collection_name, index_params=index_params
        )

        logger.debug(f"[Milvus] Created new collection {collection_name}")

    # TODO: take a look at this again. Have Doubts
    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Document],
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        """
        Upsert documents in the database
        """
        if len(documents) == 0:
            logger.warning("No documents to index")
            return

        logger.debug(
            f"[Milvus] Adding {len(documents)} documents to collection {collection_name}"
        )

        if not self.milvus_client.has_collection(collection_name):
            self.create_collection(
                collection_name=collection_name, embeddings=embeddings
            )
            return

        if incremental and len(documents) > 0:
            # Instead of using document IDs, we'll delete based on metadata matching
            for doc in documents:
                if (
                    DATA_POINT_FQN_METADATA_KEY in doc.metadata
                    and DATA_POINT_HASH_METADATA_KEY in doc.metadata
                ):
                    delete_expr = (
                        f'metadata["{DATA_POINT_FQN_METADATA_KEY}"] == "{doc.metadata[DATA_POINT_FQN_METADATA_KEY]}" && '
                        f'metadata["{DATA_POINT_HASH_METADATA_KEY}"] == "{doc.metadata[DATA_POINT_HASH_METADATA_KEY]}"'
                    )

                    logger.debug(
                        f"[Milvus] Deleting records matching expression: {delete_expr}"
                    )

                    self.milvus_client.delete(
                        collection_name=collection_name,
                        filter=delete_expr,
                    )

        Milvus(
            collection_name=collection_name,
            connection_args={
                "uri": self.milvus_client.uri,
                "token": self.milvus_client.token,
            },
            embedding_function=embeddings,
        ).add_documents(documents=documents)

        logger.debug(
            f"[Milvus] Added {len(documents)} documents to collection {collection_name}"
        )

    def get_collections(self) -> List[str]:
        logger.debug("[Milvus] Fetching collections from the vector database")
        collections = self.milvus_client.list_collections()
        logger.debug(f"[Milvus] Fetched {len(collections)} collections")
        return collections

    def delete_collection(self, collection_name: str):
        logger.debug(f"[Milvus] Deleting {collection_name} collection")
        self.milvus_client.drop_collection(collection_name)
        logger.debug(f"[Milvus] Deleted {collection_name} collection")

    def get_vector_store(self, collection_name: str, embeddings: Embeddings):
        logger.debug(f"[Milvus] Getting vector store for collection {collection_name}")
        return Milvus(
            collection_name=collection_name,
            connection_args={
                "uri": self.milvus_client.uri,
                "token": self.milvus_client.token,
            },
            embedding_function=embeddings,
        )

    def get_vector_client(self):
        logger.debug("[Milvus] Getting Milvus client")
        return self.milvus_client

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
            f"[Milvus] Listing data point vectors for collection {collection_name}"
        )
        filter_expr = (
            f'metadata["{DATA_POINT_FQN_METADATA_KEY}"] == "{data_source_fqn}"'
        )

        data_point_vectors: List[DataPointVector] = []

        offset = 0

        while True:
            search_result = self.milvus_client.query(
                collection_name=collection_name,
                filter=filter_expr,
                output_fields=[
                    "id",
                    f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                    f"metadata.{DATA_POINT_HASH_METADATA_KEY}",
                ],
                limit=batch_size,
                offset=offset,
            )

            for result in search_result:
                if result.get("metadata", {}).get(
                    DATA_POINT_FQN_METADATA_KEY
                ) and result.get("metadata", {}).get(DATA_POINT_HASH_METADATA_KEY):
                    data_point_vectors.append(
                        DataPointVector(
                            data_point_vector_id=result["id"],
                            data_point_fqn=result["metadata"][
                                DATA_POINT_FQN_METADATA_KEY
                            ],
                            data_point_hash=result["metadata"][
                                DATA_POINT_HASH_METADATA_KEY
                            ],
                        )
                    )

            if (
                len(search_result) < batch_size
                or len(data_point_vectors) >= MAX_SCROLL_LIMIT
            ):
                break

            offset += batch_size

        logger.debug(f"[Milvus] Listed {len(data_point_vectors)} data point vectors")

        return data_point_vectors

    def delete_data_point_vectors(
        self,
        collection_name: str,
        data_point_vectors: List[DataPointVector],
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ):
        """
        Delete vectors from the collection
        """
        logger.debug(f"[Milvus] Deleting {len(data_point_vectors)} data point vectors")

        for i in range(0, len(data_point_vectors), batch_size):
            batch_vectors = data_point_vectors[i : i + batch_size]

            delete_expr = " or ".join(
                [f"id == {vector.data_point_vector_id}" for vector in batch_vectors]
            )

            self.milvus_client.delete(
                collection_name=collection_name, filter=delete_expr
            )

        logger.debug(f"[Milvus] Deleted {len(data_point_vectors)} data point vectors")

    def get_embedding_dimensions(self, embeddings: Embeddings) -> int:
        """
        Fetch embedding dimensions
        """
        logger.debug("[Milvus] Embedding a dummy doc to get vector dimensions")
        partial_embeddings = embeddings.embed_documents(["This is a dummy document"])
        vector_size = len(partial_embeddings[0])
        logger.debug(f"Vector size: {vector_size}")
        return vector_size
