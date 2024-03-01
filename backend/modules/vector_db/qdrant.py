from typing import List

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores.qdrant import Qdrant
from qdrant_client import QdrantClient, models

from backend.constants import DOCUMENT_ID_METADATA_KEY
from backend.logger import logger
from backend.modules.vector_db.base import BaseVectorDB
from backend.types import VectorDBConfig


class QdrantVectorDB(BaseVectorDB):
    def __init__(self, config: VectorDBConfig, collection_name: str = None):
        self.url = config.url
        self.api_key = config.api_key
        self.collection_name = collection_name
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

    def create_collection(self, embeddings: Embeddings):
        # No provision to create a empty collection
        # We do a workaround by creating a dummy document and deleting it
        Qdrant.from_documents(
            documents=[
                Document(
                    page_content="Initial document",
                    metadata={f"{DOCUMENT_ID_METADATA_KEY}": "__init__"},
                )
            ],
            embedding=embeddings,
            collection_name=self.collection_name,
            url=self.url,
            api_key=self.api_key,
            prefer_grpc=self.prefer_grpc,
            port=self.port,
            prefix=self.prefix,
        )
        self.qdrant_client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key=f"metadata.{DOCUMENT_ID_METADATA_KEY}",
                            match=models.MatchText(text="__init__"),
                        ),
                    ],
                )
            ),
        )
        self.qdrant_client.create_payload_index(
            collection_name=self.collection_name,
            field_name=f"metadata.{DOCUMENT_ID_METADATA_KEY}",
            field_schema="keyword",
        )
        return

    def _get_records_to_be_upserted(self, document_ids: List[str], incremental: bool):
        if not incremental:
            return []
        # For incremental deletion, we delete the documents with the same document_id
        records, _ = self.qdrant_client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                should=[
                    models.FieldCondition(
                        key=f"metadata.{DOCUMENT_ID_METADATA_KEY}",
                        match=models.MatchAny(
                            any=document_ids,
                        ),
                    ),
                ]
            ),
            limit=self.qdrant_client.count(
                collection_name=self.collection_name,
            ).count
            or 1000,
            with_payload=False,
            with_vectors=False,
        )
        record_ids_to_be_upserted = [record.id for record in records]
        logger.info(f"Records to be upserted {len(record_ids_to_be_upserted)}")
        return record_ids_to_be_upserted

    def upsert_documents(
        self,
        documents,
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        if len(documents) == 0:
            logger.warning("No documents to index")
            return
        # get record IDs to be upserted
        record_ids_to_be_upserted: List[str] = self._get_records_to_be_upserted(
            document_ids=[
                document.metadata.get(DOCUMENT_ID_METADATA_KEY)
                for document in documents
            ],
            incremental=incremental,
        )

        # Add Documents
        Qdrant(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embeddings=embeddings,
        ).add_documents(documents=documents)

        # Delete Documents
        if len(record_ids_to_be_upserted):
            logger.info(f"Deleting {len(record_ids_to_be_upserted)} records")
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=record_ids_to_be_upserted,
                ),
            )

    def get_collections(self) -> List[str]:
        collections = self.qdrant_client.get_collections().collections
        return [collection.name for collection in collections]

    def delete_collection(self):
        return self.qdrant_client.delete_collection(
            collection_name=self.collection_name
        )

    def get_vector_store(self, embeddings: Embeddings):
        return Qdrant(
            client=self.qdrant_client,
            embeddings=embeddings,
            collection_name=self.collection_name,
        )

    def list_documents_in_collection(self, base_document_id: str = None) -> List[str]:
        """
        List all documents in a collection
        """
        records, _ = self.qdrant_client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                should=(
                    [
                        models.FieldCondition(
                            key=f"metadata.{DOCUMENT_ID_METADATA_KEY}",
                            match=models.MatchText(
                                text=base_document_id,
                            ),
                        ),
                    ]
                    if base_document_id
                    else None
                )
            ),
            limit=self.qdrant_client.count(
                collection_name=self.collection_name,
            ).count
            or 1000,
            with_payload=[f"metadata.{DOCUMENT_ID_METADATA_KEY}"],
            with_vectors=False,
        )
        document_ids_set = set()
        for record in records:
            if record.payload.get("metadata") and record.payload.get("metadata").get(
                DOCUMENT_ID_METADATA_KEY
            ):
                document_ids_set.add(
                    record.payload.get("metadata").get(DOCUMENT_ID_METADATA_KEY)
                )
        return list(document_ids_set)

    def delete_documents(self, document_ids: List[str]):
        """
        Delete documents from the collection
        """
        try:
            self.qdrant_client.get_collection(collection_name=self.collection_name)
        except Exception as exp:
            logger.debug(exp)
            return
        # https://qdrant.tech/documentation/concepts/filtering/#full-text-match
        self.qdrant_client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key=f"metadata.{DOCUMENT_ID_METADATA_KEY}",
                            match=models.MatchAny(any=document_ids),
                        ),
                    ],
                )
            ),
        )

    def get_vector_client(self):
        return self.qdrant_client
