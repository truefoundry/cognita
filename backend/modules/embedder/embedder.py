# A global registry to store all available embedders.
from langchain.embeddings import CacheBackedEmbeddings
from langchain.embeddings.base import Embeddings
from langchain_community.storage.redis import RedisStore

from backend.settings import settings
from backend.types import EmbedderConfig, EmbeddingCacheConfig

EMBEDDER_REGISTRY = {}


def register_embedder(provider: str, cls):
    """
    Registers all the available loaders using `BaseEmbedder` class

    Args:
        cls: The embedder class to be registered.

    Returns:
        None
    """
    global EMBEDDER_REGISTRY
    # Validate and add the embedder to the registry.
    if provider in EMBEDDER_REGISTRY:
        raise ValueError(
            f"Error while registering class {cls.__name__}, already taken by {EMBEDDER_REGISTRY[provider].__name__}"
        )
    EMBEDDER_REGISTRY[provider] = cls


def get_embedding_cache_store(config: EmbeddingCacheConfig):
    if config.provider == "redis":
        return RedisStore(
            redis_url=config.url,
            client_kwargs=config.config,
            namespace="embedding_caches",
        )
    raise NotImplementedError(
        f"Embedding cache provider {config.provider} not supported!"
    )


def get_embedder(
    embedder_config: EmbedderConfig,
) -> Embeddings:
    """
    Returns an instance of the embedding class based on the specified embedder and configuration.

    Args:
        embedder_config (EmbedderConfig): Config for embedder. Registered with provider (e.g., "truefoundry").

    Returns:
        Embeddings: An instance of the specified embedding class.
    """
    global EMBEDDER_REGISTRY
    if embedder_config.provider not in EMBEDDER_REGISTRY:
        raise ValueError(
            f"No embedder registered with provider {embedder_config.provider}"
        )
    base_embedder: Embeddings = EMBEDDER_REGISTRY[embedder_config.provider](
        **embedder_config.config
    )
    if not settings.EMBEDDING_CACHE_CONFIG:
        return base_embedder

    store = get_embedding_cache_store(config=settings.EMBEDDING_CACHE_CONFIG)
    embedder = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings=base_embedder,
        document_embedding_cache=store,
        namespace=embedder_config.config.get("model", "default"),
    )
    return embedder


def list_embedders():
    """
    Returns a list of all the registered embedders.

    Returns:
        List[dict]: A list of all the registered embedders.
    """
    global EMBEDDER_REGISTRY
    return [
        {"provider": type, "class": cls.__name__}
        for type, cls in EMBEDDER_REGISTRY.items()
    ]
