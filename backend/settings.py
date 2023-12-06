import os

import orjson
from pydantic import BaseSettings

from backend.utils.base import EmbeddingCacheConfig, VectorDBConfig


class Settings(BaseSettings):
    """
    Settings class to hold all the environment variables for FastAPI
    """

    DOCUMENT_ID_SEPARATOR = "::"

    DEBUG_MODE = True if os.getenv("DEBUG_MODE", "false") == "true" else False
    ML_REPO_NAME = os.getenv("ML_REPO_NAME")
    VECTOR_DB_CONFIG = os.getenv("VECTOR_DB_CONFIG")
    METADATA_STORE_TYPE = os.getenv("METADATA_STORE_TYPE", "mlfoundry")
    TFY_SERVICE_ROOT_PATH = os.getenv("TFY_SERVICE_ROOT_PATH", "")
    JOB_FQN = os.getenv("JOB_FQN")
    TFY_API_KEY = os.getenv("TFY_API_KEY")
    TFY_HOST = os.getenv("TFY_HOST")
    TFY_LLM_GATEWAY_ENDPOINT = os.getenv("TFY_LLM_GATEWAY_ENDPOINT", None)
    TFY_LLM_GATEWAY_PATH = os.getenv("TFY_LLM_GATEWAY_PATH", "/api/llm")
    EMBEDDING_CACHE_ENABLED = os.getenv("EMBEDDING_CACHE_ENABLED", "false") == "true"
    EMBEDDING_CACHE_CONFIG = (
        EmbeddingCacheConfig.parse_obj(
            orjson.loads(os.getenv("EMBEDDING_CACHE_CONFIG"))
        )
        if os.getenv("EMBEDDING_CACHE_CONFIG", None)
        else None
    )

    if not ML_REPO_NAME:
        raise ValueError("ML_REPO_NAME is not set")

    if not TFY_API_KEY:
        raise ValueError("TFY_API_KEY is not set")

    if not TFY_HOST:
        raise ValueError("TFY_HOST is not set")

    if EMBEDDING_CACHE_ENABLED and not EMBEDDING_CACHE_CONFIG:
        raise ValueError("EMBEDDING_CACHE_CONFIG is not set")

    if not TFY_LLM_GATEWAY_ENDPOINT:
        TFY_LLM_GATEWAY_ENDPOINT = f"{TFY_HOST}{TFY_LLM_GATEWAY_PATH}"


settings = Settings()
