import os
from typing import List

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores.qdrant import Qdrant
from qdrant_client import QdrantClient, models

from backend.constants import DOCUMENT_ID_METADATA_KEY
from backend.logger import logger
from backend.modules.vector_db.base import BaseVectorDB
from backend.types import IndexingDeletionMode, VectorDBConfig
from backend.utils import get_base_document_id


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

    def upsert_documents(
        self,
        documents,
        embeddings: Embeddings,
        deletion_mode: IndexingDeletionMode = IndexingDeletionMode.incremental,
    ):
        if len(documents) == 0:
            logger.warning("No documents to index")
            return
        # Collection record IDs to be deleted
        record_ids_to_be_deleted: List[str] = []
        if deletion_mode == IndexingDeletionMode.INCREMENTAL:
            # For incremental deletion, we delete the documents with the same document_id
            document_ids = [
                document.metadata.get(DOCUMENT_ID_METADATA_KEY)
                for document in documents
            ]
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
                limit=100000000,
                with_payload=False,
                with_vectors=False,
            )
            record_ids_to_be_deleted = [record.id for record in records]
            logger.info(f"Records to be deleted {len(record_ids_to_be_deleted)}")
        elif deletion_mode == IndexingDeletionMode.FULL:
            # For full deletion, we delete all the documents with same source
            base_document_id = get_base_document_id(
                _document_id=documents[0].metadata.get(DOCUMENT_ID_METADATA_KEY)
            )
            if base_document_id:
                records, _ = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=models.Filter(
                        should=[
                            models.FieldCondition(
                                key=f"metadata.{DOCUMENT_ID_METADATA_KEY}",
                                match=models.MatchText(
                                    text=base_document_id,
                                ),
                            ),
                        ]
                    ),
                    limit=100000000,
                    with_payload=False,
                    with_vectors=False,
                )
                record_ids_to_be_deleted = [record.id for record in records]
                logger.info(f"Records to be deleted {len(record_ids_to_be_deleted)}")

        # Add Documents
        Qdrant(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embeddings=embeddings,
        ).add_documents(documents=documents)

        # Delete Documents
        if len(record_ids_to_be_deleted):
            logger.info(f"Deleting {len(record_ids_to_be_deleted)} records")
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=record_ids_to_be_deleted,
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

    def list_documents_in_collection(self) -> List[dict]:
        """
        List all documents in a collection
        """
        response = self.qdrant_client.search_groups(
            collection_name=self.collection_name,
            group_by=f"{DOCUMENT_ID_METADATA_KEY}",
            query_vector=None,
            limit=1000,
            group_size=1,
        )
        groups = response.groups
        documents: List[dict] = []
        for group in groups:
            documents.append(
                {
                    f"{DOCUMENT_ID_METADATA_KEY}": group.id,
                }
            )
        return documents

    def delete_documents(self, document_id_match: str):
        """
        Delete a document from the collection
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
                            match=models.MatchText(text=document_id_match),
                        ),
                    ],
                )
            ),
        )

    def get_vector_client(self):
        return self.qdrant_client
