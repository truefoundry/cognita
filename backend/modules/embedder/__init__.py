from langchain.embeddings import CacheBackedEmbeddings
from langchain.embeddings.cohere import CohereEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.storage import RedisStore

from backend.modules.embedder.instruct import RemoteHuggingFaceInstructEmbeddings
from backend.modules.embedder.tfy_embeddings import TruefoundryEmbeddings
from backend.settings import settings
from backend.utils.base import EmbedderConfig

# A dictionary mapping embedder names to their respective classes.
SUPPORTED_EMBEDDERS = {
    "OpenAI": OpenAIEmbeddings,
    "HuggingFaceInstruct": RemoteHuggingFaceInstructEmbeddings,
    "TruefoundryEmbeddings": TruefoundryEmbeddings,
    "Cohere": CohereEmbeddings,
}


def get_embedder(embedder_config: EmbedderConfig):
    """
    Returns an instance of the embedding class based on the specified embedder and configuration.

    Args:
        embedder (str): The name of the embedder (e.g., "OpenAI", "HuggingFaceInstruct", "TruefoundryEmbeddings").
        embedding_configuration (dict): A dictionary containing configuration parameters for the embedder.

    Returns:
        Embeddings: An instance of the specified embedding class.
    """
    if embedder_config.provider in SUPPORTED_EMBEDDERS:
        if settings.EMBEDDING_CACHE_ENABLED:
            underlying_embeddings = SUPPORTED_EMBEDDERS[embedder_config.provider](
                **embedder_config.config
            )
            store = RedisStore(
                redis_url=settings.REDIS_URL,
                client_kwargs={"db": 2},
                namespace="embedding_caches",
            )
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
