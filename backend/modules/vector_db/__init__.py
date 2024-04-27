from backend.modules.vector_db.base import BaseVectorDB
from backend.modules.vector_db.qdrant import QdrantVectorDB
from backend.modules.vector_db.singlestore import SingleStoreVectorDB
from backend.modules.vector_db.weaviate import WeaviateVectorDB
from backend.types import VectorDBConfig

SUPPORTED_VECTOR_DBS = {
    "qdrant": QdrantVectorDB,
    # "weaviate": WeaviateVectorDB,
    "singlestore": SingleStoreVectorDB,
}


def get_vector_db_client(config: VectorDBConfig) -> BaseVectorDB:
    if config.provider in SUPPORTED_VECTOR_DBS:
        return SUPPORTED_VECTOR_DBS[config.provider](config=config)
    else:
        raise ValueError(f"Unknown vector db provider: {config.provider}")
