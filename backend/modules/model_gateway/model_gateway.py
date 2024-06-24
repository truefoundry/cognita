import json
import os
from typing import List

from langchain.embeddings.base import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI

from backend.logger import logger
from backend.modules.model_gateway import MODELS_CONFIG_PATH
from backend.types import ModelConfig, ModelProviderConfig, ModelType


class ModelGateway:
    config: List[ModelProviderConfig]
    modelsToProviderMap = {}

    def __init__(self):
        with open(MODELS_CONFIG_PATH) as f:
            data = json.load(f)
            # parse the json data into a list of ModelProviderConfig objects
            self.config = [ModelProviderConfig.parse_obj(item) for item in data]

            # load llm models
            self.llm_models: List[ModelConfig] = []
            # load embedding models
            self.embedding_models: List[ModelConfig] = []

            for config_obj in self.config:
                if config_obj.api_key_env_var and not os.environ.get(
                    config_obj.api_key_env_var
                ):
                    raise ValueError(
                        f"Environment variable {config_obj.api_key_env_var} not set. Cannot initialize the model gateway."
                    )

                for model_id in config_obj.embedding_model_ids:
                    model_name = f"{config_obj.provider_name}/{model_id}"
                    self.modelsToProviderMap[model_name] = config_obj

                    # Register the model as an embedding model
                    self.embedding_models.append(
                        ModelConfig(
                            name=f"{config_obj.provider_name}/{model_id}",
                            type=ModelType.embedding,
                        )
                    )

                for model_id in config_obj.llm_model_ids:
                    model_name = f"{config_obj.provider_name}/{model_id}"
                    self.modelsToProviderMap[model_name] = config_obj

                    # Register the model as an llm model
                    self.llm_models.append(
                        ModelConfig(
                            name=f"{config_obj.provider_name}/{model_id}",
                            type=ModelType.chat,
                        )
                    )

    def get_embedding_models(self) -> List[ModelConfig]:
        return self.embedding_models

    def get_llm_models(self) -> List[ModelConfig]:
        return self.llm_models

    def get_embedder_from_model_config(self, model_name: str) -> Embeddings:
        if model_name not in self.modelsToProviderMap:
            raise ValueError(f"Model {model_name} not registered in the model gateway.")
        model_provider_config: ModelProviderConfig = self.modelsToProviderMap[
            model_name
        ]
        if not model_provider_config.api_key_env_var:
            api_key = None
        else:
            api_key = os.environ.get(model_provider_config.api_key_env_var, "")
        model_id = "/".join(model_name.split("/")[1:])
        return OpenAIEmbeddings(
            openai_api_key=api_key,
            model=model_id,
            openai_api_base=model_provider_config.base_url,
        )

    def get_llm_from_model_config(
        self, model_config: ModelConfig, stream=False
    ) -> BaseChatModel:
        if model_config.name not in self.modelsToProviderMap:
            raise ValueError(
                f"Model {model_config.name} not registered in the model gateway."
            )
        model_provider_config: ModelProviderConfig = self.modelsToProviderMap[
            model_config.name
        ]
        if not model_config.parameters:
            model_config.parameters = {}
        if not model_provider_config.api_key_env_var:
            api_key = None
        else:
            api_key = os.environ.get(model_provider_config.api_key_env_var, "")
        model_id = "/".join(model_config.name.split("/")[1:])
        return ChatOpenAI(
            model=model_id,
            temperature=model_config.parameters.get("temperature", 0.1),
            streaming=stream,
            api_key=api_key,
            base_url=model_provider_config.base_url,
        )


model_gateway = ModelGateway()
