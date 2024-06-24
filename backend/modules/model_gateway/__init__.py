# When using locally, you can create your own models_config.json file before running docker-compose.
# The following code is used for tf-deployments
import os

import yaml

from backend.logger import logger
from backend.settings import settings
from backend.types import ModelProviderConfig

# Define the paths as constants
# Current file's directory
current_dir = os.path.dirname(__file__)

# Navigate up three levels to get to the project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

MODELS_CONFIG_SAMPLE_PATH = os.path.join(project_root, "models_config.sample.yaml")
MODELS_CONFIG_PATH = os.path.join(project_root, "models_config.yaml")

logger.info(f"MODELS_CONFIG_SAMPLE_PATH: {MODELS_CONFIG_SAMPLE_PATH}")
logger.info(f"MODELS_CONFIG_PATH: {MODELS_CONFIG_PATH}")

if (
    settings.TFY_API_KEY
    and os.path.exists(MODELS_CONFIG_SAMPLE_PATH)
    and not os.path.exists(MODELS_CONFIG_PATH)
):
    logger.info("models_config.yaml not found. Creating a default models_config.yaml")
    config = {
        "model_providers": [
            ModelProviderConfig(
                provider_name="truefoundry",
                api_format="openai",
                llm_model_ids=["openai-main/gpt-4-turbo", "openai-main/gpt-3-5-turbo"],
                embedding_model_ids=["openai-main/text-embedding-ada-002"],
                api_key_env_var="TFY_API_KEY",
                base_url=settings.TFY_LLM_GATEWAY_URL,
            ).dict()
        ]
    }
    with open(MODELS_CONFIG_PATH, "w") as f:
        yaml.safe_dump(config, f, indent=2)
