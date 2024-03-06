import os
from typing import List

import weaviate
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores.weaviate import Weaviate

from backend.constants import DOCUMENT_ID_METADATA_KEY
from backend.modules.vector_db.base import BaseVectorDB
from backend.types import VectorDBConfig


def decapitalize(s):
    if not s:
        return s
    return s[0].lower() + s[1:]


class WeaviateVectorDB(BaseVectorDB):

    def __init__(self, config: VectorDBConfig):
        self.url = config.url
        self.api_key = config.api_key
        self.weaviate_client = weaviate.Client(
            url=self.url,
            **(
                {"auth_client_secret": weaviate.AuthApiKey(api_key=self.api_key)}
                if self.api_key
                else {}
            ),
        )

    def create_collection(self, collection_name: str, embeddings: Embeddings):
        self.weaviate_client.schema.create_class(
            {
                "class": collection_name.capitalize(),
                "properties": [
                    {
                        "name": f"{DOCUMENT_ID_METADATA_KEY}",
                        "dataType": ["text"],
                    },
                ],
            }
        )

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: Embeddings,
        incremental,
    ):
        """
        Upsert documents to the collection
        Arguments:
        - collection_name: Name of the collection
        - documents: List of documents
        - embeddings: Embeddings object
        - incremental: If True, the documents will be added incrementally, otherwise the collection will be replaced
        Returns:
        - None
        """
        Weaviate.from_documents(
            documents=documents,
            embedding=embeddings,
            client=self.weaviate_client,
            index_name=collection_name.capitalize(),
        )

    def get_collections(self) -> List[str]:
        collections = self.weaviate_client.schema.get().get("classes", [])
        return [decapitalize(collection["class"]) for collection in collections]

    def delete_collection(
        self,
        collection_name: str,
    ):
        return self.weaviate_client.schema.delete_class(collection_name.capitalize())

    def get_vector_store(self, collection_name: str, embeddings: Embeddings):
        return Weaviate(
            client=self.weaviate_client,
            embedding=embeddings,
            index_name=collection_name.capitalize(),  # Weaviate stores the index name as capitalized
            text_key="text",
            by_text=False,
            attributes=[f"{DOCUMENT_ID_METADATA_KEY}"],
        )

    def list_documents_in_collection(
        self, collection_name: str, base_document_id: str = None
    ) -> List[str]:
        """
        List all documents in a collection
        """
        # https://weaviate.io/developers/weaviate/search/aggregate#retrieve-groupedby-properties
        response = (
            self.weaviate_client.query.aggregate(collection_name.capitalize())
            .with_group_by_filter([f"{DOCUMENT_ID_METADATA_KEY}"])
            .with_fields("groupedBy { value }")
            .do()
        )
        groups: List[dict] = (
            response.get("data", {})
            .get("Aggregate", {})
            .get(collection_name.capitalize(), [])
        )
        document_ids = set()
        for group in groups:
            document_ids.add(group.get("groupedBy", {}).get("value", ""))
        return document_ids

    def delete_documents(self, collection_name: str, document_ids: List[str]):
        """
        Delete documents from the collection that match given `document_id_match`
        """
        # https://weaviate.io/developers/weaviate/manage-data/delete#delete-multiple-objects
        res = self.weaviate_client.batch.delete_objects(
            class_name=collection_name.capitalize(),
            where={
                "path": [f"{DOCUMENT_ID_METADATA_KEY}"],
                "operator": "ContainsAny",
                "valueTextArray": document_ids,
            },
        )
        deleted_vectors = res.get("results", {}).get("successful", None)
        if deleted_vectors:
            print(f"Deleted {len(document_ids)} documents from the collection")

    def get_vector_client(self):
        return self.weaviate_client
