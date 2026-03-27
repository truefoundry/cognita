import os
from typing import List

import chromadb
from chromadb.config import Settings
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.schema.vectorstore import VectorStore
from langchain_chroma import Chroma

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


class ChromaVectorDB(BaseVectorDB):
    def __init__(self, config: VectorDBConfig):
        """
        Initialize Chroma vector database client
        Args:
            config: VectorDBConfig
                - provider: str
                - local: bool
                - url: str (optional for remote Chroma server)
                - api_key: str (optional for authentication)
                - config: dict with additional configuration
                    - persist_directory: str (for local persistence)
                    - collection_metadata: dict (default metadata for collections)
        """
        logger.debug(f"Connecting to Chroma using config: {config.model_dump()}")
        self.config = config

        if config.local is True:
            # Local Chroma with persistence
            persist_directory = config.config.get("persist_directory", "./chroma_db")
            logger.debug(
                f"Using local Chroma with persist_directory: {persist_directory}"
            )

            # Ensure directory exists
            os.makedirs(persist_directory, exist_ok=True)

            self.chroma_client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )
        else:
            # Remote Chroma server
            if not config.url:
                raise ValueError("URL is required for remote Chroma server")

            logger.debug(f"Connecting to remote Chroma server at: {config.url}")

            # Parse headers for authentication if needed
            headers = {}
            if config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"

            # Add any additional headers from config
            if "headers" in config.config:
                headers.update(config.config["headers"])

            self.chroma_client = chromadb.HttpClient(
                host=(
                    config.url.split("://")[1].split(":")[0]
                    if "://" in config.url
                    else config.url.split(":")[0]
                ),
                port=(
                    int(config.url.split(":")[-1])
                    if ":" in config.url.split("://")[-1]
                    else 8000
                ),
                ssl=config.url.startswith("https://"),
                headers=headers,
                settings=Settings(
                    anonymized_telemetry=False,
                ),
            )

    def create_collection(self, collection_name: str, embeddings: Embeddings):
        """Create a collection in Chroma"""
        logger.debug(f"[Chroma] Creating new collection {collection_name}")

        # Check if collection already exists
        try:
            existing_collection = self.chroma_client.get_collection(collection_name)
            if existing_collection:
                raise ValueError(
                    f"Collection {collection_name} already exists in Chroma"
                )
        except Exception:
            # Collection doesn't exist, which is what we want
            pass

        # Get embedding dimensions
        vector_size = self.get_embedding_dimensions(embeddings)
        logger.debug(f"Vector size: {vector_size}")

        # Create collection with metadata
        collection_metadata = self.config.config.get("collection_metadata", {})
        collection_metadata.update(
            {"embedding_dimension": vector_size, "created_by": "cognita"}
        )

        self.chroma_client.create_collection(
            name=collection_name,
            metadata=collection_metadata,
            embedding_function=None,  # We'll handle embeddings ourselves
        )

        logger.debug(f"[Chroma] Created new collection {collection_name}")

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Document],
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        """Upsert documents into Chroma collection"""
        if len(documents) == 0:
            logger.warning("No documents to index")
            return

        logger.debug(
            f"[Chroma] Adding {len(documents)} documents to collection {collection_name}"
        )

        # Get collection
        collection = self.chroma_client.get_collection(collection_name)

        # Prepare data for upsert
        ids = []
        texts = []
        metadatas = []
        document_embeddings = []

        for i, document in enumerate(documents):
            # Generate ID - use hash if available, otherwise use index
            doc_id = document.metadata.get(DATA_POINT_HASH_METADATA_KEY)
            if not doc_id:
                doc_id = f"{collection_name}_{i}_{hash(document.page_content)}"

            ids.append(doc_id)
            texts.append(document.page_content)
            metadatas.append(document.metadata)

        # Generate embeddings for all documents
        logger.debug(f"[Chroma] Generating embeddings for {len(texts)} documents")
        document_embeddings = embeddings.embed_documents(texts)

        # Handle incremental updates
        if incremental:
            # Check which documents already exist
            try:
                existing_docs = collection.get(ids=ids, include=["metadatas"])
                existing_ids = (
                    set(existing_docs["ids"]) if existing_docs["ids"] else set()
                )

                if existing_ids:
                    logger.debug(
                        f"[Chroma] Found {len(existing_ids)} existing documents, will update them"
                    )
            except Exception as e:
                logger.debug(f"[Chroma] No existing documents found: {e}")
                existing_ids = set()

        # Upsert documents (Chroma handles both insert and update)
        collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=document_embeddings,
        )

        logger.debug(
            f"[Chroma] Successfully upserted {len(documents)} documents to collection {collection_name}"
        )

    def get_collections(self) -> List[str]:
        """Get all collection names from Chroma"""
        logger.debug("[Chroma] Listing all collections")
        collections = self.chroma_client.list_collections()
        collection_names = [collection.name for collection in collections]
        logger.debug(
            f"[Chroma] Found {len(collection_names)} collections: {collection_names}"
        )
        return collection_names

    def delete_collection(self, collection_name: str):
        """Delete a collection from Chroma"""
        logger.debug(f"[Chroma] Deleting collection {collection_name}")
        try:
            self.chroma_client.delete_collection(collection_name)
            logger.debug(f"[Chroma] Successfully deleted collection {collection_name}")
        except Exception as e:
            logger.error(f"[Chroma] Failed to delete collection {collection_name}: {e}")
            raise

    def get_vector_store(
        self, collection_name: str, embeddings: Embeddings
    ) -> VectorStore:
        """Get LangChain Chroma vector store instance"""
        logger.debug(f"[Chroma] Getting vector store for collection {collection_name}")

        if self.config.local:
            persist_directory = self.config.config.get(
                "persist_directory", "./chroma_db"
            )
            return Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=persist_directory,
                client_settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )
        else:
            # For remote Chroma, we need to pass the client
            return Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                client=self.chroma_client,
            )

    def get_vector_client(self):
        """Get Chroma client"""
        logger.debug("[Chroma] Getting Chroma client")
        return self.chroma_client

    def list_data_point_vectors(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ) -> List[DataPointVector]:
        """Get vectors from the collection filtered by data source FQN"""
        logger.debug(
            f"[Chroma] Listing data point vectors for collection {collection_name}, data_source_fqn: {data_source_fqn}"
        )

        collection = self.chroma_client.get_collection(collection_name)
        data_point_vectors = []

        # Query with filter for data source FQN
        try:
            # Get all documents with the specified data source FQN
            results = collection.get(
                where={DATA_POINT_FQN_METADATA_KEY: data_source_fqn},
                include=["metadatas"],
                limit=batch_size,
            )

            if results["ids"]:
                for doc_id, metadata in zip(results["ids"], results["metadatas"]):
                    data_point_vector = DataPointVector(
                        data_point_vector_id=doc_id,
                        data_point_fqn=metadata.get(DATA_POINT_FQN_METADATA_KEY, ""),
                        data_point_hash=metadata.get(DATA_POINT_HASH_METADATA_KEY, ""),
                    )
                    data_point_vectors.append(data_point_vector)

            logger.debug(
                f"[Chroma] Found {len(data_point_vectors)} data point vectors for data_source_fqn: {data_source_fqn}"
            )

        except Exception as e:
            logger.error(f"[Chroma] Error listing data point vectors: {e}")
            raise

        return data_point_vectors

    def delete_data_point_vectors(
        self,
        collection_name: str,
        data_point_vectors: List[DataPointVector],
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ):
        """Delete specific vectors from the collection"""
        if not data_point_vectors:
            logger.warning("[Chroma] No data point vectors to delete")
            return

        logger.debug(
            f"[Chroma] Deleting {len(data_point_vectors)} data point vectors from collection {collection_name}"
        )

        collection = self.chroma_client.get_collection(collection_name)

        # Extract IDs to delete
        ids_to_delete = [dpv.data_point_vector_id for dpv in data_point_vectors]

        # Delete in batches
        for i in range(0, len(ids_to_delete), batch_size):
            batch_ids = ids_to_delete[i : i + batch_size]
            try:
                collection.delete(ids=batch_ids)
                logger.debug(f"[Chroma] Deleted batch of {len(batch_ids)} vectors")
            except Exception as e:
                logger.error(f"[Chroma] Error deleting batch of vectors: {e}")
                raise

        logger.debug(
            f"[Chroma] Successfully deleted {len(data_point_vectors)} data point vectors from collection {collection_name}"
        )
