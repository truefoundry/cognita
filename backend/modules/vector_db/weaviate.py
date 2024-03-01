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
    def __init__(self, config: VectorDBConfig, collection_name: str = None):
        self.url = config.url
        self.api_key = config.api_key
        if collection_name:
            self.collection_name = collection_name.capitalize()
        self.weaviate_client = weaviate.Client(
            url=self.url,
            **(
                {"auth_client_secret": weaviate.AuthApiKey(api_key=self.api_key)}
                if self.api_key
                else {}
            ),
        )

    def create_collection(self, embeddings: Embeddings):
        self.weaviate_client.schema.create_class(
            {
                "class": self.collection_name,
                "properties": [
                    {
                        "name": f"{DOCUMENT_ID_METADATA_KEY}",
                        "dataType": ["text"],
                    },
                ],
            }
        )

    def upsert_documents(
        self, documents: List[str], embeddings: Embeddings, incremental
    ):
        Weaviate.from_documents(
            documents=documents,
            embedding=embeddings,
            client=self.weaviate_client,
            index_name=self.collection_name,
        )

    def get_collections(self) -> List[str]:
        collections = self.weaviate_client.schema.get().get("classes", [])
        return [decapitalize(collection["class"]) for collection in collections]

    def delete_collection(self):
        return self.weaviate_client.schema.delete_class(self.collection_name)

    def get_vector_store(self, embeddings: Embeddings):
        return Weaviate(
            client=self.weaviate_client,
            embedding=embeddings,
            index_name=self.collection_name,  # Weaviate stores the index name as capitalized
            text_key="text",
            by_text=False,
            attributes=[f"{DOCUMENT_ID_METADATA_KEY}"],
        )

    def list_documents_in_collection(self, base_document_id: str = None) -> List[str]:
        """
        List all documents in a collection
        """
        # https://weaviate.io/developers/weaviate/search/aggregate#retrieve-groupedby-properties
        response = (
            self.weaviate_client.query.aggregate(self.collection_name)
            .with_group_by_filter([f"{DOCUMENT_ID_METADATA_KEY}"])
            .with_fields("groupedBy { value }")
            .do()
        )
        groups: List[dict] = (
            response.get("data", {}).get("Aggregate", {}).get(self.collection_name, [])
        )
        document_ids = set()
        for group in groups:
            document_ids.add(group.get("groupedBy", {}).get("value", ""))
        return document_ids

    def delete_documents(self, document_ids: List[str]):
        """
        Delete documents from the collection that match given `document_id_match`
        """
        # https://weaviate.io/developers/weaviate/manage-data/delete#delete-multiple-objects
        res = self.weaviate_client.batch.delete_objects(
            class_name=self.collection_name,
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
