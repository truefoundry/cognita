from typing import List

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.schema.vectorstore import VectorStore
from langchain_community.vectorstores import Neo4jVector
from neo4j import GraphDatabase

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


class Neo4jVectorDB(BaseVectorDB):
    def __init__(self, config: VectorDBConfig):
        """Initialize Neo4j vector database client"""
        logger.debug(f"Connecting to Neo4j using config: {config.model_dump()}")
        self.config = config
        self.url = config.url
        self.username = config.config.get("username", "neo4j")
        self.password = config.config.get("password", "")
        self.database = config.config.get("database", "neo4j")
        self.node_label = config.config.get("node_label", "Document")
        self.embedding_property = config.config.get("embedding_property", "embedding")
        self.text_property = config.config.get("text_property", "text")
        
        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver(
            self.url, 
            auth=(self.username, self.password)
        )

    def create_collection(self, collection_name: str, embeddings: Embeddings) -> None:
        """Create a collection (index) in Neo4j"""
        logger.debug(f"[Neo4j] Creating new collection {collection_name}")
        
        vector_size = self.get_embedding_dimensions(embeddings)
        
        # Create vector index
        with self.driver.session(database=self.database) as session:
            # Create vector index for the collection
            index_name = f"{collection_name}_vector_index"
            query = f"""
            CREATE VECTOR INDEX {index_name} IF NOT EXISTS
            FOR (n:{self.node_label})
            ON (n.{self.embedding_property})
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {vector_size},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
            """
            session.run(query)
            
            # Create index for metadata querying
            metadata_index = f"{collection_name}_metadata_index"
            session.run(
                f"CREATE INDEX {metadata_index} IF NOT EXISTS "
                f"FOR (n:{self.node_label}) ON (n.{DATA_POINT_FQN_METADATA_KEY})"
            )
            
        logger.debug(f"[Neo4j] Created new collection {collection_name}")

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Document],
        embeddings: Embeddings,
        incremental: bool = True,
    ):
        """Upsert documents with their embeddings"""
        if len(documents) == 0:
            logger.warning("No documents to index")
            return
            
        logger.debug(
            f"[Neo4j] Adding {len(documents)} documents to collection {collection_name}"
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

        # Add Documents using LangChain Neo4j integration
        neo4j_store = Neo4jVector.from_documents(
            documents=documents,
            embedding=embeddings,
            url=self.url,
            username=self.username,
            password=self.password,
            database=self.database,
            node_label=self.node_label,
            text_node_property=self.text_property,
            embedding_node_property=self.embedding_property,
        )
        
        logger.debug(
            f"[Neo4j] Added {len(documents)} documents to collection {collection_name}"
        )

        # Delete outdated documents
        if len(record_ids_to_be_upserted) > 0:
            logger.debug(
                f"[Neo4j] Deleting {len(record_ids_to_be_upserted)} outdated documents from collection {collection_name}"
            )
            self._delete_records_by_ids(record_ids_to_be_upserted)
            logger.debug(
                f"[Neo4j] Deleted {len(record_ids_to_be_upserted)} outdated documents from collection {collection_name}"
            )

    def _get_records_to_be_upserted(
        self, collection_name: str, data_point_fqns: List[str], incremental: bool = True
    ) -> List[str]:
        """Get record IDs to be upserted"""
        if not incremental:
            return []

        logger.debug(
            f"[Neo4j] Incremental Ingestion: Fetching documents for {len(data_point_fqns)} data point fqns for collection {collection_name}"
        )

        record_ids_to_be_upserted = []
        
        with self.driver.session(database=self.database) as session:
            for i in range(0, len(data_point_fqns), DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE):
                batch_fqns = data_point_fqns[i : i + DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE]
                
                query = f"""
                MATCH (n:{self.node_label})
                WHERE n.{DATA_POINT_FQN_METADATA_KEY} IN $fqns
                RETURN elementId(n) as id
                LIMIT {MAX_SCROLL_LIMIT}
                """
                
                result = session.run(query, fqns=batch_fqns)
                for record in result:
                    record_ids_to_be_upserted.append(record["id"])
                    if len(record_ids_to_be_upserted) > MAX_SCROLL_LIMIT:
                        break
                        
                if len(record_ids_to_be_upserted) > MAX_SCROLL_LIMIT:
                    break

        logger.debug(
            f"[Neo4j] Incremental Ingestion: collection={collection_name} Addition={len(data_point_fqns)}, Updates={len(record_ids_to_be_upserted)}"
        )
        return record_ids_to_be_upserted

    def _delete_records_by_ids(self, record_ids: List[str]):
        """Delete records by their IDs"""
        with self.driver.session(database=self.database) as session:
            for i in range(0, len(record_ids), DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE):
                batch_ids = record_ids[i : i + DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE]
                
                query = f"""
                MATCH (n:{self.node_label})
                WHERE elementId(n) IN $ids
                DELETE n
                """
                session.run(query, ids=batch_ids)

    def get_collections(self) -> List[str]:
        """Get all collection names (vector indexes)"""
        logger.debug("[Neo4j] Fetching collections")
        
        with self.driver.session(database=self.database) as session:
            result = session.run("SHOW VECTOR INDEXES")
            collections = []
            for record in result:
                index_name = record.get("name", "")
                if index_name.endswith("_vector_index"):
                    collection_name = index_name.replace("_vector_index", "")
                    collections.append(collection_name)
        
        logger.debug(f"[Neo4j] Fetched {len(collections)} collections")
        return collections

    def delete_collection(self, collection_name: str):
        """Delete a collection (drop indexes and delete nodes)"""
        logger.debug(f"[Neo4j] Deleting {collection_name} collection")
        
        with self.driver.session(database=self.database) as session:
            # Drop vector index
            vector_index = f"{collection_name}_vector_index"
            session.run(f"DROP INDEX {vector_index} IF EXISTS")
            
            # Drop metadata index
            metadata_index = f"{collection_name}_metadata_index"
            session.run(f"DROP INDEX {metadata_index} IF EXISTS")
            
            # Delete all nodes (optional - you might want to keep the data)
            # session.run(f"MATCH (n:{self.node_label}) DELETE n")
            
        logger.debug(f"[Neo4j] Deleted {collection_name} collection")

    def get_vector_store(self, collection_name: str, embeddings: Embeddings) -> VectorStore:
        """Get Neo4j vector store instance"""
        logger.debug(f"[Neo4j] Getting vector store for collection {collection_name}")
        
        return Neo4jVector(
            embedding=embeddings,
            url=self.url,
            username=self.username,
            password=self.password,
            database=self.database,
            node_label=self.node_label,
            text_node_property=self.text_property,
            embedding_node_property=self.embedding_property,
        )

    def get_vector_client(self):
        """Get Neo4j driver"""
        logger.debug("[Neo4j] Getting Neo4j driver")
        return self.driver

    def list_data_point_vectors(
        self,
        collection_name: str,
        data_source_fqn: str,
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ) -> List[DataPointVector]:
        """List data point vectors from the collection"""
        logger.debug(
            f"[Neo4j] Listing all data point vectors for collection {collection_name}"
        )
        
        data_point_vectors: List[DataPointVector] = []
        skip = 0
        
        with self.driver.session(database=self.database) as session:
            while True:
                query = f"""
                MATCH (n:{self.node_label})
                WHERE n.{DATA_POINT_FQN_METADATA_KEY} = $data_source_fqn
                RETURN elementId(n) as id, 
                       n.{DATA_POINT_FQN_METADATA_KEY} as data_point_fqn,
                       n.{DATA_POINT_HASH_METADATA_KEY} as data_point_hash
                SKIP $skip
                LIMIT $limit
                """
                
                result = session.run(
                    query,
                    data_source_fqn=data_source_fqn,
                    skip=skip,
                    limit=batch_size
                )
                
                batch_results = list(result)
                if not batch_results:
                    break
                
                for record in batch_results:
                    if (record["data_point_fqn"] and record["data_point_hash"]):
                        data_point_vectors.append(
                            DataPointVector(
                                data_point_vector_id=record["id"],
                                data_point_fqn=record["data_point_fqn"],
                                data_point_hash=record["data_point_hash"],
                            )
                        )
                    
                    if len(data_point_vectors) > MAX_SCROLL_LIMIT:
                        break
                
                if len(batch_results) < batch_size or len(data_point_vectors) > MAX_SCROLL_LIMIT:
                    break
                    
                skip += batch_size

        logger.debug(
            f"[Neo4j] Listing {len(data_point_vectors)} data point vectors for collection {collection_name}"
        )
        return data_point_vectors

    def delete_data_point_vectors(
        self,
        collection_name: str,
        data_point_vectors: List[DataPointVector],
        batch_size: int = DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE,
    ):
        """Delete vectors by their IDs"""
        logger.debug(
            f"[Neo4j] Deleting {len(data_point_vectors)} data point vectors from collection {collection_name}"
        )
        
        vector_ids = [vector.data_point_vector_id for vector in data_point_vectors]

        # Delete in batches
        with self.driver.session(database=self.database) as session:
            for i in range(0, len(vector_ids), batch_size):
                batch = vector_ids[i : i + batch_size]
                
                query = f"""
                MATCH (n:{self.node_label})
                WHERE elementId(n) IN $ids
                DELETE n
                """
                session.run(query, ids=batch)
        
        logger.debug(
            f"[Neo4j] Deleted {len(data_point_vectors)} data point vectors from collection {collection_name}"
        )

    def list_documents_in_collection(
        self, collection_name: str, base_document_id: str = None
    ) -> List[str]:
        """List all documents in a collection"""
        logger.debug(
            f"[Neo4j] Listing all documents with base document id {base_document_id} for collection {collection_name}"
        )
        
        document_ids_set = set()
        skip = 0
        
        with self.driver.session(database=self.database) as session:
            while True:
                if base_document_id:
                    query = f"""
                    MATCH (n:{self.node_label})
                    WHERE n.{DATA_POINT_FQN_METADATA_KEY} = $base_document_id
                    RETURN n.{DATA_POINT_FQN_METADATA_KEY} as fqn
                    SKIP $skip
                    LIMIT $limit
                    """
                    result = session.run(
                        query,
                        base_document_id=base_document_id,
                        skip=skip,
                        limit=BATCH_SIZE
                    )
                else:
                    query = f"""
                    MATCH (n:{self.node_label})
                    RETURN n.{DATA_POINT_FQN_METADATA_KEY} as fqn
                    SKIP $skip
                    LIMIT $limit
                    """
                    result = session.run(query, skip=skip, limit=BATCH_SIZE)
                
                batch_results = list(result)
                if not batch_results:
                    break
                    
                for record in batch_results:
                    if record["fqn"]:
                        document_ids_set.add(record["fqn"])
                        
                    if len(document_ids_set) > MAX_SCROLL_LIMIT:
                        break
                
                if len(batch_results) < BATCH_SIZE or len(document_ids_set) > MAX_SCROLL_LIMIT:
                    break
                    
                skip += BATCH_SIZE

        logger.debug(
            f"[Neo4j] Found {len(document_ids_set)} documents with base document id {base_document_id} for collection {collection_name}"
        )
        return list(document_ids_set)

    def delete_documents(self, collection_name: str, document_ids: List[str]):
        """Delete documents from the collection"""
        logger.debug(
            f"[Neo4j] Deleting {len(document_ids)} documents from collection {collection_name}"
        )
        
        with self.driver.session(database=self.database) as session:
            for i in range(0, len(document_ids), DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE):
                batch_ids = document_ids[i : i + DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE]
                
                query = f"""
                MATCH (n:{self.node_label})
                WHERE n.{DATA_POINT_FQN_METADATA_KEY} IN $document_ids
                DELETE n
                """
                session.run(query, document_ids=batch_ids)
        
        logger.debug(
            f"[Neo4j] Deleted {len(document_ids)} documents from collection {collection_name}"
        )

    def __del__(self):
        """Close the Neo4j driver when the object is destroyed"""
        if hasattr(self, 'driver'):
            self.driver.close()
