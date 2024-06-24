import json
import os
from typing import List, Union

from langchain.embeddings.base import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.llms import LLM
from langchain_openai import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.llms.sambanova import SambaStudio
from langchain_community.llms import Replicate
from langchain_community.embeddings.sambanova import SambaStudioEmbeddings

from backend.modules.model_gateway import MODELS_CONFIG_PATH
from backend.types import ModelConfig, ModelProviderConfig, ModelType

class ModelGateway:
    provider_configs: List[ModelProviderConfig]
    model_name_to_provider_config = {}

    def __init__(self):
        with open(MODELS_CONFIG_PATH) as f:
            data = json.load(f)
            self.provider_configs = [ModelProviderConfig.parse_obj(item) for item in data]

            self.llm_models: List[ModelConfig] = []
            self.embedding_models: List[ModelConfig] = []

            for provider_config in self.provider_configs:
                if provider_config.api_key_env_var and not os.environ.get(provider_config.api_key_env_var):
                    raise ValueError(f"Environment variable {provider_config.api_key_env_var} not set. Cannot initialize the model gateway.")

                for model_id in provider_config.embedding_model_ids:
                    model_name = f"{provider_config.provider_name}/{model_id}"
                    self.model_name_to_provider_config[model_name] = provider_config
                    self.embedding_models.append(ModelConfig(name=model_name, type=ModelType.embedding))

                for model_id in provider_config.llm_model_ids:
                    model_name = f"{provider_config.provider_name}/{model_id}"
                    parameters = provider_config.parameters
                    self.model_name_to_provider_config[model_name] = provider_config
                    self.llm_models.append(ModelConfig(name=model_name, type=ModelType.chat,parameters=parameters))

    def get_embedding_models(self) -> List[ModelConfig]:
        return self.embedding_models

    def get_llm_models(self) -> List[ModelConfig]:
        return self.llm_models

    def get_embedder_from_model_config(self, model_name: str) -> Embeddings:
        if model_name not in self.model_name_to_provider_config:
            raise ValueError(f"Model {model_name} not registered in the model gateway.")
        model_provider_config: ModelProviderConfig = self.model_name_to_provider_config[model_name]
        
        if model_provider_config.provider_name == "sambastudio":
            return SambaStudioEmbeddings()
        else:
            api_key = os.environ.get(model_provider_config.api_key_env_var, "") if model_provider_config.api_key_env_var else "EMPTY"
            model_id = "/".join(model_name.split("/")[1:])
            return OpenAIEmbeddings(
                openai_api_key=api_key,
                model=model_id,
                openai_api_base=model_provider_config.base_url,
                check_embedding_ctx_length=(model_provider_config.provider_name == "openai"),
            )

    def get_llm_from_model_config(self, model_config: ModelConfig, stream=False) -> Union[BaseChatModel, LLM]:
        if model_config.name not in self.model_name_to_provider_config:
            raise ValueError(f"Model {model_config.name} not registered in the model gateway.")
        model_provider_config: ModelProviderConfig = self.model_name_to_provider_config[model_config.name]
        
        if not model_config.parameters:
            model_config.parameters = {}
        
        api_key = os.environ.get(model_provider_config.api_key_env_var, "") if model_provider_config.api_key_env_var else None
        model_id = "/".join(model_config.name.split("/")[1:])

        if model_provider_config.provider_name in ["openai", "local-ollama", "local-infinity", "truefoundry"]:
            return ChatOpenAI(
                model=model_id,
                temperature=model_config.parameters.get("temperature", 0.1),
                streaming=stream,
                api_key=api_key,
                base_url=model_provider_config.base_url,
            )
        elif model_provider_config.provider_name == "sambastudio":
            model_kwargs = model_config.parameters.copy() if model_config.parameters else {}
            model_kwargs["select_expert"] = model_id
            model_kwargs.update(model_config.parameters)
            return SambaStudio(
                streaming=True,
                model_kwargs=model_kwargs,
            )
        elif model_provider_config.provider_name == "replicate":
            return Replicate(
                model=model_config.name,
                streaming=stream,
                model_kwargs=model_config.parameters
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {model_provider_config.provider_name}")

model_gateway = ModelGateway()