import json
from pydantic import BaseModel
from typing import List, Optional
from backend.types import ModelConfig, EmbedderConfig, LLMConfig, ModelProviderConfig, ModelType
     
class ModelGateway:
    config: List[ModelProviderConfig]
    def __init__(self):        
        with open("./models_config.json") as f:
            data = json.load(f)
            self.config = [ModelProviderConfig(**item) for item in data]
    
    def get_models(self):
        models: List[ModelConfig] = []
        for list in self.config:
            for model_id in list.embedding_model_ids:
                models.append(ModelConfig(
                    name=f"{list.provider_name}/{model_id}", 
                    type=ModelType.embedding
                ).dict())
                              
        return models
            
    def get_embedding_models(self) -> List[ModelConfig]:
        models: List[ModelConfig] = []
        for list in self.config:
            for model_id in list.embedding_model_ids:
                models.append(ModelConfig(
                    name=f"{list.provider_name}/{model_id}", 
                    type=ModelType.embedding
                ).dict())
                              
        return models
    
    def get_llm_models(self) -> List[LLMConfig]:
        models: List[ModelConfig] = []
        for list in self.config:
            for model_id in list.llm_model_ids:
                models.append(ModelConfig(
                    name=f"{list.provider_name}/{model_id}", 
                    type=ModelType.chat
                ).dict())
                              
        return models
    
    def call_model():
        pass
    
    def get_embedder_from_model_config():
        pass
    
    def get_llm_from_model_config():
        pass
    
    def get_api_format_for_model(self, config: EmbedderConfig | LLMConfig):
        provider = config.model_name.split("/")[0]
        for list in self.config:
            if list.provider_name == provider:
                return list.api_format
        return None
    
model_gateway = ModelGateway()
