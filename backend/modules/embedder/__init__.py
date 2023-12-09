from typing import Optional

from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import RedisStore

from backend.modules.embedder.tfy_embeddings import TrueFoundryEmbeddings
from backend.utils.base import EmbedderConfig, EmbeddingCacheConfig

# A dictionary mapping embedder names to their respective classes.
SUPPORTED_EMBEDDERS = {
    "truefoundry": TrueFoundryEmbeddings,
}


def get_embedding_cache_store(config: EmbeddingCacheConfig):
    if config.provider == "redis":
        return RedisStore(
            redis_url=config.url,
            client_kwargs=config.config,
            namespace="embedding_caches",
        )
    raise Exception(f"Embedding cache provider {config.provider} not supported!")


def get_embedder(
    embedder_config: EmbedderConfig,
    embedding_cache_config: Optional[EmbeddingCacheConfig] = None,
):
    """
    Returns an instance of the embedding class based on the specified embedder and configuration.

    Args:
        embedder (str): The name of the embedder (e.g., "truefoundry").
        embedding_configuration (dict): A dictionary containing configuration parameters for the embedder.

    Returns:
        Embeddings: An instance of the specified embedding class.
    """
    if embedder_config.provider in SUPPORTED_EMBEDDERS:
        if embedding_cache_config:
            underlying_embeddings = SUPPORTED_EMBEDDERS[embedder_config.provider](
                **embedder_config.config
            )
            store = get_embedding_cache_store(config=embedding_cache_config)
            embedder = CacheBackedEmbeddings.from_bytes_store(
                underlying_embeddings, store, namespace=underlying_embeddings.model
            )
            return embedder
        else:
            return SUPPORTED_EMBEDDERS[embedder_config.provider](
                **embedder_config.config
            )
    else:
        raise Exception(f"Embedder {embedder_config.provider} not supported!")
