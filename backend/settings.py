import os
from typing import Any, Dict

from pydantic import ConfigDict, model_validator
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

    CARBON_AI_API_KEY: str = ""

    UNSTRUCTURED_IO_URL: str = ""

    UNSTRUCTURED_IO_API_KEY: str = ""

    @model_validator(mode="before")
    @classmethod
    def _validate_values(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate search type."""
        if not isinstance(values, dict):
            raise ValueError(
                f"Unexpected Pydantic v2 Validation: values are of type {type(values)}"
            )
        models_config_path = values.get("MODELS_CONFIG_PATH")
        if not os.path.isabs(models_config_path):
            this_dir = os.path.abspath(os.path.dirname(__file__))
            root_dir = os.path.dirname(this_dir)
            models_config_path = os.path.join(root_dir, models_config_path)

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

        return values


settings = Settings()
