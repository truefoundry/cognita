import os
from typing import Any, Dict

from pydantic import ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings

from backend.types import MetadataStoreConfig, VectorDBConfig


class Settings(BaseSettings):
    """
    Settings class to hold all the environment variables
    """

    model_config = ConfigDict(extra="allow")

    MODELS_CONFIG_PATH: str
    METADATA_STORE_CONFIG: MetadataStoreConfig
    ML_REPO_NAME: str = ""
    VECTOR_DB_CONFIG: VectorDBConfig
    LOCAL: bool = False
    TFY_HOST: str = ""
    TFY_API_KEY: str = ""
    JOB_FQN: str = ""
    LOG_LEVEL: str = "info"
    TFY_SERVICE_ROOT_PATH: str = ""
    BRAVE_API_KEY: str = ""
    UNSTRUCTURED_IO_URL: str = ""
    UNSTRUCTURED_IO_API_KEY: str = ""
    PROCESS_POOL_WORKERS: int = 1
    LOCAL_DATA_DIRECTORY: str = os.path.abspath(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_data")
    )
    ALLOW_CORS: bool = False
    CORS_CONFIG: Dict[str, Any] = Field(
        default_factory=lambda: {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
    )

    @model_validator(mode="before")
    @classmethod
    def _validate_values(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate search type."""
        if not isinstance(values, dict):
            raise ValueError(
                f"Unexpected Pydantic v2 Validation: values are of type {type(values)}"
            )

        if not values.get("MODELS_CONFIG_PATH"):
            raise ValueError("MODELS_CONFIG_PATH is not set in the environment")

        models_config_path = os.path.abspath(values.get("MODELS_CONFIG_PATH"))

        if not models_config_path:
            raise ValueError(
                f"{models_config_path} does not exist. "
                f"You can copy models_config.sample.yaml to {settings.MODELS_CONFIG_PATH} to bootstrap config"
            )

        values["MODELS_CONFIG_PATH"] = models_config_path

        tfy_host = values.get("TFY_HOST")
        tfy_llm_gateway_url = values.get("TFY_LLM_GATEWAY_URL")
        if tfy_host and not tfy_llm_gateway_url:
            tfy_llm_gateway_url = f"{tfy_host.rstrip('/')}/api/llm"
            values["TFY_LLM_GATEWAY_URL"] = tfy_llm_gateway_url

        if not values.get("LOCAL", False) and not values.get("ML_REPO_NAME", None):
            raise ValueError("ML_REPO_NAME is not set in the environment")

        return values


settings = Settings()
