import json
import os
from typing import Optional

import orjson
from pydantic import BaseSettings

from backend.types import MetadataStoreConfig, VectorDBConfig


class Settings(BaseSettings):
    """
    Settings class to hold all the environment variables
    """

    LOG_LEVEL: str = "info"
    METADATA_STORE_CONFIG: MetadataStoreConfig
    VECTOR_DB_CONFIG: VectorDBConfig
    TFY_SERVICE_ROOT_PATH: Optional[str] = "/"
    TFY_API_KEY: str
    OPENAI_API_KEY: Optional[str]
    TFY_HOST: Optional[str]
    TFY_LLM_GATEWAY_URL: str

    # Additional Reqs For SambaStudio
    SAMBASTUDIO_BASE_URL: Optional[str]
    SAMBASTUDIO_PROJECT_ID: Optional[str]
    SAMBASTUDIO_ENDPOINT_ID: Optional[str]
    SAMBASTUDIO_API_KEY: Optional[str]
    SAMBASTUDIO_EMBEDDINGS_BASE_URL: Optional[str]
    SAMBASTUDIO_EMBEDDINGS_PROJECT_ID: Optional[str]
    SAMBASTUDIO_EMBEDDINGS_ENDPOINT_ID: Optional[str]
    SAMBASTUDIO_EMBEDDINGS_API_KEY: Optional[str]

    REPLICATE_API_TOKEN: Optional[str]
    WB_PROJECT: Optional[str]
    WB_STREAM: Optional[str]
    WB_ENTITY: Optional[str]

    # Additional Keys For Confluence
    CONFLUENCE_API_TOKEN: Optional[str]
    CONFLUENCE_USER_EMAIL: Optional[str]
    CONFLUENCE_URL: Optional[str]

    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
    VECTOR_DB_CONFIG = os.getenv("VECTOR_DB_CONFIG", "")
    METADATA_STORE_CONFIG = os.getenv("METADATA_STORE_CONFIG", "")
    TFY_SERVICE_ROOT_PATH = os.getenv("TFY_SERVICE_ROOT_PATH", "")
    JOB_FQN = os.getenv("JOB_FQN", "")
    JOB_COMPONENT_NAME = os.getenv("JOB_COMPONENT_NAME", "")
    TFY_API_KEY = os.getenv("TFY_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    TFY_HOST = os.getenv("TFY_HOST", "")
    TFY_LLM_GATEWAY_URL = os.getenv("TFY_LLM_GATEWAY_URL", "")

    LOCAL: bool = os.getenv("LOCAL", False)
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    EMBEDDING_SVC_URL: str = os.getenv("EMBEDDING_SVC_URL", "")
    RERANKER_SVC_URL: str = os.getenv("RERANKER_SVC_URL", "")

    # SambaStudio Envs
    SAMBASTUDIO_BASE_URL = os.getenv("SAMBASTUDIO_BASE_URL", "")
    SAMBASTUDIO_PROJECT_ID = os.getenv("SAMBASTUDIO_PROJECT_ID", "")
    SAMBASTUDIO_ENDPOINT_ID = os.getenv("SAMBASTUDIO_ENDPOINT_ID", "")
    SAMBASTUDIO_API_KEY = os.getenv("SAMBASTUDIO_API_KEY", "")

    # SambaStudioEmbeddingSettings
    SAMBASTUDIO_EMBEDDINGS_BASE_URL = os.getenv("SAMBASTUDIO_EMBEDDINGS_BASE_URL", "")
    SAMBASTUDIO_EMBEDDINGS_PROJECT_ID = os.getenv(
        "SAMBASTUDIO_EMBEDDINGS_PROJECT_ID", ""
    )
    SAMBASTUDIO_EMBEDDINGS_ENDPOINT_ID = os.getenv(
        "SAMBASTUDIO_EMBEDDINGS_ENDPOINT_ID", ""
    )
    SAMBASTUDIO_EMBEDDINGS_API_KEY = os.getenv("SAMBASTUDIO_EMBEDDINGS_API_KEY", "")

    # Replicate LLMs
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

    # WeightsAndBiases
    WB_PROJECT = "traces"
    WB_STREAM = "lc_traces_stream"
    WB_ENTITY = ""

    # Confluence
    CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "")
    CONFLUENCE_USER_EMAIL = os.getenv("CONFLUENCE_USER_EMAIL", "")
    CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "")

    if not VECTOR_DB_CONFIG:
        raise ValueError("VECTOR_DB_CONFIG is not set")

    if not METADATA_STORE_CONFIG:
        raise ValueError("METADATA_STORE_CONFIG is not set")

    if not TFY_LLM_GATEWAY_URL:
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
