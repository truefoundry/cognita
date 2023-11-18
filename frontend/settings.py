from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    """
    Settings class to hold all the environment variables for Frontend
    """

    ML_REPO_NAME = os.getenv("ML_REPO_NAME")
    TFY_API_KEY = os.getenv("TFY_API_KEY", "")
    TFY_HOST = os.getenv("TFY_HOST", "")
    LLM_GATEWAY_ENDPOINT = os.getenv("LLM_GATEWAY_ENDPOINT")
    BACKEND_URL = os.getenv("BACKEND_URL", "")
    TRUEFOUNDRY_EMBEDDINGS_ENDPOINT = os.getenv("TRUEFOUNDRY_EMBEDDINGS_ENDPOINT", "")

    if not ML_REPO_NAME:
        raise ValueError("ML_REPO_NAME is not set")
    # if not VECTOR_DB_CONFIG:
    #     raise ValueError("VECTOR_DB_CONFIG is not set")
    # if not JOB_FQN:
    #     raise ValueError("JOB_FQN is not set")
    if not LLM_GATEWAY_ENDPOINT:
        raise ValueError("LLM_GATEWAY_ENDPOINT is not set")

    if not BACKEND_URL:
        raise ValueError("BACKEND_URL is not set")


settings = Settings()
