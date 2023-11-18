import weaviate
import os
from langchain.vectorstores.weaviate import Weaviate
from langchain.embeddings.base import Embeddings
from backend.modules.vector_db.base import BaseVectorDB
from backend.base import VectorDBConfig


class WeaviateVectorDB(BaseVectorDB):
    def __init__(self, config: VectorDBConfig, collection_name: str):
        self.url = config.url
        self.api_key = config.api_key
        self.collection_name = collection_name
        self.weaviate_client = weaviate.Client(
            url=self.url,
            **(
                {"auth_client_secret": weaviate.AuthApiKey(api_key=self.api_key)}
                if self.api_key
                else {}
            )
        )

    def create_collection(self, embeddings: Embeddings):
        # Skip
        return

    def upsert_documents(self, documents: list[str], embeddings: Embeddings):
        return Weaviate.from_documents(
            documents=documents,
            embedding=embeddings,
            client=self.weaviate_client,
            index_name=self.collection_name,
        )

    def delete_collection(self):
        return self.weaviate_client.schema.delete_class(self.collection_name)

    def get_retriver(self, embeddings: Embeddings):
        return Weaviate(
            client=self.weaviate_client,
            embedding=embeddings,
            index_name=self.collection_name.capitalize(),  # Weaviate stores the index name as capitalized
            text_key="text",
            by_text=False,
        ).as_retriever()
