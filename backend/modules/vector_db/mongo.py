from typing import List, Optional
from pymongo import MongoClient, UpdateOne
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.mongodb_atlas import MongoDBAtlasVectorSearch
from langchain.schema.vectorstore import VectorStore

from backend import logger
from backend.constants import DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE
from backend.types import DataPointVector, VectorDBConfig
from backend.modules.vector_db.base import BaseVectorDB


class MongoVectorDB(BaseVectorDB):
    def __init__(self, config: VectorDBConfig):
        """Initialize MongoDB vector database client"""
        self.client = MongoClient(host=config.host, port=config.port)
        self.db = self.client[config.database_name]

    def create_collection(self, collection_name: str, embeddings: Embeddings) -> None:
        """Create a collection with vector search index"""
        if collection_name in self.db.list_collection_names():
            raise ValueError(f"Collection {collection_name} already exists in MongoDB")

        collection = self.db.create_collection(collection_name)
            # Create vector search index
        collection.create_index([
            ("embedding", "vectorSearch")
        ], {
            "numDimensions": self.get_embedding_dimensions(embeddings),
            "similarity": "cosine"
        })

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Document],
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        """Upsert documents with their embeddings"""
        collection = self.db[collection_name]
        
        # Generate embeddings for documents
        texts = [doc.page_content for doc in documents]
        embeddings_list = embeddings.embed_documents(texts)

        # Prepare documents for insertion
        docs_to_insert = []
        for doc, embedding in zip(documents, embeddings_list):
            mongo_doc = {
                "text": doc.page_content,
                "embedding": embedding,
                "metadata": doc.metadata
            }
            docs_to_insert.append(mongo_doc)

        # Use bulk write for better performance
        if incremental:
            collection.bulk_write([
                UpdateOne(
                    {"metadata.source": doc["metadata"]["source"]},
                    {"$set": doc},
                    upsert=True
                ) for doc in docs_to_insert
            ])
        else:
            # TODO: only delete the existing documents with the in collection with given ids
            collection.delete_many({})
            collection.insert_many(docs_to_insert)

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
        """List vectors for a data source"""
        collection = self.db[collection_name]
        vectors = []
        
        cursor = collection.find(
            {"metadata.data_source_fqn": data_source_fqn},
            batch_size=batch_size
        )
        
        for doc in cursor:
            vector = DataPointVector(
                id=str(doc["_id"]),
                text=doc["text"],
                metadata=doc["metadata"],
                embedding=doc["embedding"]
            )
            vectors.append(vector)
            
        return vectors

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
            batch = vector_ids[i:i + batch_size]
            collection.delete_many({"_id": {"$in": batch}})
