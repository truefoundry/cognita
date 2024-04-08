from typing import List

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores.qdrant import Qdrant
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import VectorParams, Distance


from backend.constants import DATA_POINT_FQN_METADATA_KEY, DATA_POINT_HASH_METADATA_KEY
from backend.logger import logger
from backend.modules.vector_db.base import BaseVectorDB
from backend.types import DataPointVector, VectorDBConfig

MAX_SCROLL_LIMIT = int(1e6)
BATCH_SIZE = 1000


class QdrantVectorDB(BaseVectorDB):
    def __init__(self, config: VectorDBConfig):
        if config.local is True:
            self.local = True
            self.location = config.url
            self.qdrant_client = QdrantClient(
                path="./qdrant_db",
            )
        else:
            self.local = False
            self.url = config.url
            self.api_key = config.api_key
            self.port = 443 if self.url.startswith("https://") else 6333
            self.prefix = config.config.get("prefix", None) if config.config else None
            self.prefer_grpc = False if self.url.startswith("https://") else True
            self.qdrant_client = QdrantClient(
                url=self.url,
                **({"api_key": self.api_key} if self.api_key else {}),
                port=self.port,
                prefer_grpc=self.prefer_grpc,
                prefix=self.prefix,
            )

    def create_collection(self, collection_name: str, embeddings: Embeddings):

        logger.debug(f"[Vector Store Qdrant] Creating new collection {collection_name}")

        # Calculate embedding size
        partial_embeddings = embeddings.embed_documents(["Initial document"])
        vector_size = len(partial_embeddings[0])

        self.qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,  # embedding dimension
                distance=Distance.COSINE,
            ),
        )
        self.qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name=f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        self.qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name=f"metadata.{DATA_POINT_HASH_METADATA_KEY}",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        logger.debug(f"[Vector Store] Created new collection {collection_name}")

    def _get_records_to_be_upserted(
        self, collection_name: str, data_point_fqns: List[str], incremental: bool
    ):
        if not incremental:
            return []
        # For incremental deletion, we delete the documents with the same document_id
        logger.debug(
            f"[Vector Store] Incremental Ingestion: Fetching documents for {len(data_point_fqns)} data point fqns for collection {collection_name}"
        )
        stop = False
        offset = None
        record_ids_to_be_upserted = []
        while stop is not True:
            records, next_offset = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    should=[
                        models.FieldCondition(
                            key=f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                            match=models.MatchAny(
                                any=data_point_fqns,
                            ),
                        ),
                    ]
                ),
                limit=BATCH_SIZE,
                offset=offset,
                with_payload=False,
                with_vectors=False,
            )
            for record in records:
                record_ids_to_be_upserted.append(record.id)
                if len(record_ids_to_be_upserted) > MAX_SCROLL_LIMIT:
                    stop = True
                    break
            if next_offset is None:
                stop = True
            else:
                offset = next_offset

        logger.debug(
            f"[Vector Store] Incremental Ingestion: collection={collection_name} Addition={len(data_point_fqns)}, Updates={len(record_ids_to_be_upserted)}"
        )
        return record_ids_to_be_upserted

    def upsert_documents(
        self,
        collection_name: str,
        documents,
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        if len(documents) == 0:
            logger.warning("No documents to index")
            return
        # get record IDs to be upserted
        logger.debug(
            f"[Vector Store] Adding {len(documents)} documents to collection {collection_name}"
        )
        data_point_fqns = []
        for document in documents:
            if document.metadata.get(DATA_POINT_FQN_METADATA_KEY):
                data_point_fqns.append(
                    document.metadata.get(DATA_POINT_FQN_METADATA_KEY)
                )
        record_ids_to_be_upserted: List[str] = self._get_records_to_be_upserted(
            collection_name=collection_name,
            data_point_fqns=data_point_fqns,
            incremental=incremental,
        )

        # Add Documents
        Qdrant(
            client=self.qdrant_client,
            collection_name=collection_name,
            embeddings=embeddings,
        ).add_documents(documents=documents)
        logger.debug(
            f"[Vector Store] Added {len(documents)} documents to collection {collection_name}"
        )

        # Delete Documents
        if len(record_ids_to_be_upserted):
            logger.debug(
                f"[Vector Store] Deleting {len(documents)} outdated documents from collection {collection_name}"
            )
            for i in range(0, len(record_ids_to_be_upserted), BATCH_SIZE):
                record_ids_to_be_processed = record_ids_to_be_upserted[
                    i : i + BATCH_SIZE
                ]
                self.qdrant_client.delete(
                    collection_name=collection_name,
                    points_selector=models.PointIdsList(
                        points=record_ids_to_be_processed,
                    ),
                )
            logger.debug(
                f"[Vector Store] Deleted {len(documents)} outdated documents from collection {collection_name}"
            )

    def get_collections(self) -> List[str]:
        logger.debug(f"[Vector Store] Fetching collections")
        collections = self.qdrant_client.get_collections().collections
        logger.debug(f"[Vector Store] Fetched {len(collections)} collections")
        return [collection.name for collection in collections]

    def delete_collection(self, collection_name: str):
        logger.debug(f"[Vector Store] Deleting {collection_name} collection")
        self.qdrant_client.delete_collection(collection_name=collection_name)
        logger.debug(f"[Vector Store] Deleted {collection_name} collection")

    def get_vector_store(self, collection_name: str, embeddings: Embeddings):
        logger.debug(
            f"[Vector Store] Getting vector store for collection {collection_name}"
        )
        return Qdrant(
            client=self.qdrant_client,
            embeddings=embeddings,
            collection_name=collection_name,
        )

    def get_vector_client(self):
        logger.debug(f"[Vector Store] Getting Qdrant client")
        return self.qdrant_client

    def list_data_point_vectors(
        self, collection_name: str, data_source_fqn: str, batch_size: int = BATCH_SIZE
    ) -> List[DataPointVector]:
        logger.debug(
            f"[Vector Store] Listing all data point vectors for collection {collection_name}"
        )
        stop = False
        offset = None
        data_point_vectors: List[DataPointVector] = []
        while stop is not True:
            records, next_offset = self.qdrant_client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                with_payload=[
                    f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                    f"metadata.{DATA_POINT_HASH_METADATA_KEY}",
                ],
                scroll_filter=models.Filter(
                    should=[
                        models.FieldCondition(
                            key=f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                            match=models.MatchText(
                                text=data_source_fqn,
                            ),
                        ),
                    ]
                ),
                with_vectors=False,
                offset=offset,
            )
            for record in records:
                metadata: dict = record.payload.get("metadata")
                if (
                    metadata
                    and metadata.get(DATA_POINT_FQN_METADATA_KEY)
                    and metadata.get(DATA_POINT_HASH_METADATA_KEY)
                ):
                    data_point_vectors.append(
                        DataPointVector(
                            data_point_vector_id=record.id,
                            data_point_fqn=metadata.get(DATA_POINT_FQN_METADATA_KEY),
                            data_point_hash=metadata.get(DATA_POINT_HASH_METADATA_KEY),
                        )
                    )
                if len(data_point_vectors) > MAX_SCROLL_LIMIT:
                    stop = True
                    break
            if next_offset is None:
                stop = True
            else:
                offset = next_offset
        logger.debug(
            f"[Vector Store] Listing {len(data_point_vectors)} data point vectors for collection {collection_name}"
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
        """
        logger.debug(
            f"[Vector Store] Deleting {len(data_point_vectors)} data point vectors"
        )
        vectors_to_be_deleted_count = len(data_point_vectors)
        deleted_vectors_count = 0
        for i in range(0, vectors_to_be_deleted_count, batch_size):
            data_point_vectors_to_be_processed = data_point_vectors[i : i + batch_size]
            self.qdrant_client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=[
                        document_vector_point.data_point_vector_id
                        for document_vector_point in data_point_vectors_to_be_processed
                    ],
                ),
            )
            deleted_vectors_count = deleted_vectors_count + len(
                data_point_vectors_to_be_processed
            )
            logger.debug(
                f"[Vector Store] Deleted [{deleted_vectors_count}/{vectors_to_be_deleted_count}] data point vectors"
            )
        logger.debug(
            f"[Vector Store] Deleted {vectors_to_be_deleted_count} data point vectors"
        )

    def list_documents_in_collection(
        self, collection_name: str, base_document_id: str = None
    ) -> List[str]:
        """
        List all documents in a collection
        """
        logger.debug(
            f"[Vector Store] Listing all documents with base document id {base_document_id} for collection {collection_name}"
        )
        stop = False
        offset = None
        document_ids_set = set()
        while stop is not True:
            records, next_offset = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    should=(
                        [
                            models.FieldCondition(
                                key=f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                                match=models.MatchText(
                                    text=base_document_id,
                                ),
                            ),
                        ]
                        if base_document_id
                        else None
                    )
                ),
                limit=BATCH_SIZE,
                with_payload=[f"metadata.{DATA_POINT_FQN_METADATA_KEY}"],
                with_vectors=False,
                offset=offset,
            )
            for record in records:
                if record.payload.get("metadata") and record.payload.get(
                    "metadata"
                ).get(DATA_POINT_FQN_METADATA_KEY):
                    document_ids_set.add(
                        record.payload.get("metadata").get(DATA_POINT_FQN_METADATA_KEY)
                    )
                if len(document_ids_set) > MAX_SCROLL_LIMIT:
                    stop = True
                    break
            if next_offset is None:
                stop = True
            else:
                offset = next_offset
        logger.debug(
            f"[Vector Store] Found {len(document_ids_set)} documents with base document id {base_document_id} for collection {collection_name}"
        )
        return list(document_ids_set)

    def delete_documents(self, collection_name: str, document_ids: List[str]):
        """
        Delete documents from the collection
        """
        logger.debug(
            f"[Vector Store] Deleting {len(document_ids)} documents from collection {collection_name}"
        )
        try:
            self.qdrant_client.get_collection(collection_name=collection_name)
        except Exception as exp:
            logger.debug(exp)
            return
        # https://qdrant.tech/documentation/concepts/filtering/#full-text-match

        for i in range(0, len(document_ids), BATCH_SIZE):
            document_ids_to_be_processed = document_ids[i : i + BATCH_SIZE]
            self.qdrant_client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key=f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                                match=models.MatchAny(any=document_ids_to_be_processed),
                            ),
                        ],
                    )
                ),
            )
        logger.debug(
            f"[Vector Store] Deleted {len(document_ids)} documents from collection {collection_name}"
        )

    def list_document_vector_points(
        self, collection_name: str
    ) -> List[DataPointVector]:
        """
        List all documents in a collection
        """
        logger.debug(
            f"[Vector Store] Listing all document vector points for collection {collection_name}"
        )
        stop = False
        offset = None
        document_vector_points: List[DataPointVector] = []
        while stop is not True:
            records, next_offset = self.qdrant_client.scroll(
                collection_name=collection_name,
                limit=BATCH_SIZE,
                with_payload=[
                    f"metadata.{DATA_POINT_FQN_METADATA_KEY}",
                    f"metadata.{DATA_POINT_HASH_METADATA_KEY}",
                ],
                with_vectors=False,
                offset=offset,
            )
            for record in records:
                metadata: dict = record.payload.get("metadata")
                if (
                    metadata
                    and metadata.get(DATA_POINT_FQN_METADATA_KEY)
                    and metadata.get(DATA_POINT_HASH_METADATA_KEY)
                ):
                    document_vector_points.append(
                        DataPointVector(
                            point_id=record.id,
                            document_id=metadata.get(DATA_POINT_FQN_METADATA_KEY),
                            document_hash=metadata.get(DATA_POINT_HASH_METADATA_KEY),
                        )
                    )
                if len(document_vector_points) > MAX_SCROLL_LIMIT:
                    stop = True
                    break
            if next_offset is None:
                stop = True
            else:
                offset = next_offset
        logger.debug(
            f"[Vector Store] Listing {len(document_vector_points)} document vector points for collection {collection_name}"
        )
        return document_vector_points
