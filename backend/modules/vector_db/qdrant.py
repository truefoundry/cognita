import os
from typing import List

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores.qdrant import Qdrant
from qdrant_client import QdrantClient, models

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
                    metadata={"_document_id": "__init__"},
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
                            key="metadata._document_id",
                            match=models.MatchText(text="__init__"),
                        ),
                    ],
                )
            ),
        )
        return

    def upsert_documents(self, documents, embeddings: Embeddings):
        return Qdrant(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embeddings=embeddings,
        ).add_documents(documents=documents)

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
            group_by="_document_id",
            query_vector=None,
            limit=1000,
            group_size=1,
        )
        groups = response.groups
        documents: List[dict] = []
        for group in groups:
            documents.append(
                {
                    "_document_id": group.id,
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
                            key="metadata._document_id",
                            match=models.MatchText(text=document_id_match),
                        ),
                    ],
                )
            ),
        )
