import json
from pydantic import BaseModel
from typing import List, Optional
from backend.types import ModelConfig, ModelProviderConfig, ModelType
from langchain.embeddings.base import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai.chat_models import ChatOpenAI
import os

class ModelGateway:
    config: List[ModelProviderConfig]
    modelsToProviderMap = {}
    def __init__(self):        
        with open("./models_config.json") as f:
            data = json.load(f)
            self.config = [ModelProviderConfig(**item) for item in data]
            self.models: List[ModelConfig] = []
            for list in self.config:
                if list.api_key_env_var and not os.environ.get(list.api_key_env_var):
                    raise ValueError(f"Environment variable {list.api_key_env_var} not set.")
                for model_id in list.embedding_model_ids:
                    model_name = f"{list.provider_name}/{model_id}"
                    self.modelsToProviderMap[model_name] = list
                for model_id in list.llm_model_ids:
                    model_name = f"{list.provider_name}/{model_id}"
                    self.modelsToProviderMap[model_name] = list
            
    def get_embedding_models(self) -> List[ModelConfig]:
        models: List[ModelConfig] = []
        for list in self.config:
            for model_id in list.embedding_model_ids:
                models.append(ModelConfig(
                    name=f"{list.provider_name}/{model_id}", 
                    type=ModelType.embedding
                ).dict())
                              
        return models
    
    def get_llm_models(self) -> List[ModelConfig]:
        models: List[ModelConfig] = []
        for list in self.config:
            for model_id in list.llm_model_ids:
                models.append(ModelConfig(
                    name=f"{list.provider_name}/{model_id}", 
                    type=ModelType.chat
                ).dict())
                              
        return models
    
    def get_embedder_from_model_config(self, model_name: str) -> Embeddings:
        if model_name not in self.modelsToProviderMap:
            raise ValueError(f"Model {model_name} not registered in the model gateway.")
        model_provider_config: ModelProviderConfig = self.modelsToProviderMap[model_name]
        if not model_provider_config.api_key_env_var:
            api_key = None
        else:
            api_key = os.environ.get(model_provider_config.api_key_env_var, '')
        return OpenAIEmbeddings(
            openai_api_key=api_key, 
            model=model_name.split("/")[1],
            openai_api_base=model_provider_config.base_url
        )
    
    def get_llm_from_model_config(self, model_config: ModelConfig, stream=False) -> BaseChatModel:
        if model_config.name not in self.modelsToProviderMap:
            raise ValueError(f"Model {model_config.name} not registered in the model gateway.")
        model_provider_config: ModelProviderConfig = self.modelsToProviderMap[model_config.name]
        if not model_config.parameters:
           model_config.parameters = {} 
        if not model_provider_config.api_key_env_var:
            api_key = None
        else:
            api_key = os.environ.get(model_provider_config.api_key_env_var, '')
        return ChatOpenAI(
                model=model_config.name.split("/")[1],
                temperature=model_config.parameters.get("temperature", 0.1),
                streaming=stream,
                api_key=api_key,
                base_url=model_provider_config.base_url
            )
    
model_gateway = ModelGateway()
