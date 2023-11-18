from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    """
    Settings class to hold all the environment variables for FastAPI
    """

    DEBUG_MODE = True if os.getenv("DEBUG_MODE", "false") == "true" else False
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
    ML_REPO_NAME = os.getenv("ML_REPO_NAME")
    VECTOR_DB_CONFIG = os.getenv("VECTOR_DB_CONFIG")
    METADATA_STORE_TYPE = os.getenv("METADATA_STORE_TYPE", "mlfoundry")
    TFY_SERVICE_ROOT_PATH = os.getenv("TFY_SERVICE_ROOT_PATH", "")
    JOB_FQN = os.getenv("JOB_FQN")
    TFY_API_KEY = os.getenv("TFY_API_KEY")
    TFY_HOST = os.getenv("TFY_HOST")
    LLM_GATEWAY_ENDPOINT = os.getenv("LLM_GATEWAY_ENDPOINT")

    if not ML_REPO_NAME:
        raise ValueError("ML_REPO_NAME is not set")
    # if not VECTOR_DB_CONFIG:
    #     raise ValueError("VECTOR_DB_CONFIG is not set")
    # if not JOB_FQN:
    #     raise ValueError("JOB_FQN is not set")
    if not LLM_GATEWAY_ENDPOINT:
        raise ValueError("LLM_GATEWAY_ENDPOINT is not set")


settings = Settings()
