import json
import os
from typing import List

from langchain.embeddings.base import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI

from backend.logger import logger
from backend.types import ModelConfig, ModelProviderConfig, ModelType


class ModelGateway:
    config: List[ModelProviderConfig]
    modelsToProviderMap = {}

    def __init__(self):
        with open("./models_config.json") as f:
            data = json.load(f)
            self.config = [ModelProviderConfig(**item) for item in data]
            self.models: List[ModelConfig] = []
            for list in self.config:
                for model_id in list.embedding_model_ids:
                    if list.api_key_env_var and os.environ.get(list.api_key_env_var):
                        # Register only those models whose API key is set
                        model_name = f"{list.provider_name}/{model_id}"
                        logger.info(f"Adding model {model_name} to the model gateway.")
                        self.modelsToProviderMap[model_name] = list
                    else:
                        # Avoid adding the model to the map if the API key is not set
                        logger.warning(
                            f"Environment variable {list.api_key_env_var} not set."
                        )
                for model_id in list.llm_model_ids:
                    if list.api_key_env_var and os.environ.get(list.api_key_env_var):
                        # Register only those models whose API key is set
                        model_name = f"{list.provider_name}/{model_id}"
                        logger.info(f"Adding model {model_name} to the model gateway.")
                        self.modelsToProviderMap[model_name] = list
                    else:
                        # Avoid adding the model to the map if the API key is not set
                        logger.warning(
                            f"Environment variable {list.api_key_env_var} not set."
                        )

    def get_embedding_models(self) -> List[ModelConfig]:
        models: List[ModelConfig] = []
        for list in self.config:
            if list.api_key_env_var and os.environ.get(list.api_key_env_var):
                # Register only those models whose API key is set
                for model_id in list.embedding_model_ids:
                    models.append(
                        ModelConfig(
                            name=f"{list.provider_name}/{model_id}",
                            type=ModelType.embedding,
                        ).dict()
                    )

        return models

    def get_llm_models(self) -> List[ModelConfig]:
        models: List[ModelConfig] = []
        for list in self.config:
            if list.api_key_env_var and os.environ.get(list.api_key_env_var):
                # Register only those models whose API key is set
                for model_id in list.llm_model_ids:
                    models.append(
                        ModelConfig(
                            name=f"{list.provider_name}/{model_id}", type=ModelType.chat
                        ).dict()
                    )

        return models

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
