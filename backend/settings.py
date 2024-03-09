import os
from typing import Optional

import orjson
from pydantic import BaseSettings

from backend.types import EmbeddingCacheConfig, MetadataStoreConfig, VectorDBConfig


class Settings(BaseSettings):
    """
    Settings class to hold all the environment variables
    """

    LOG_LEVEL: str = "info"
    METADATA_STORE_CONFIG: MetadataStoreConfig
    VECTOR_DB_CONFIG: VectorDBConfig
    TFY_SERVICE_ROOT_PATH: Optional[str] = "/"
    TFY_API_KEY: str
    TFY_HOST: Optional[str]
    TFY_LLM_GATEWAY_URL: str
    EMBEDDING_CACHE_CONFIG: Optional[EmbeddingCacheConfig] = None

    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
    VECTOR_DB_CONFIG = os.getenv("VECTOR_DB_CONFIG", "")
    METADATA_STORE_CONFIG = os.getenv("METADATA_STORE_CONFIG", "")
    TFY_SERVICE_ROOT_PATH = os.getenv("TFY_SERVICE_ROOT_PATH", "")
    JOB_FQN = os.getenv("JOB_FQN", "")
    JOB_COMPONENT_NAME = os.getenv("JOB_COMPONENT_NAME", "")
    TFY_API_KEY = os.getenv("TFY_API_KEY", "")
    TFY_HOST = os.getenv("TFY_HOST", "")
    TFY_LLM_GATEWAY_URL = os.getenv("TFY_LLM_GATEWAY_URL", "")
    EMBEDDING_CACHE_CONFIG = (
        EmbeddingCacheConfig.parse_obj(
            orjson.loads(os.getenv("EMBEDDING_CACHE_CONFIG"))
        )
        if os.getenv("EMBEDDING_CACHE_CONFIG", None)
        else None
    )
    if not VECTOR_DB_CONFIG:
        raise ValueError("VECTOR_DB_CONFIG is not set")

    if not METADATA_STORE_CONFIG:
        raise ValueError("METADATA_STORE_CONFIG is not set")

    if not TFY_API_KEY:
        raise ValueError("TFY_API_KEY is not set")

    if not TFY_LLM_GATEWAY_URL:
        if not TFY_HOST:
            raise ValueError("TFY_HOST is not set")
        TFY_LLM_GATEWAY_URL = f"{TFY_HOST}/api/llm"

    try:
        VECTOR_DB_CONFIG = VectorDBConfig.parse_obj(orjson.loads(VECTOR_DB_CONFIG))
    except Exception as e:
        raise ValueError(f"VECTOR_DB_CONFIG is invalid: {e}")
    try:
        METADATA_STORE_CONFIG = MetadataStoreConfig.parse_obj(
            orjson.loads(METADATA_STORE_CONFIG)
        )
    except Exception as e:
        raise ValueError(f"METADATA_STORE_CONFIG is invalid: {e}")


settings = Settings()
