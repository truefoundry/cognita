import os
from typing import Dict, List

import yaml
from cachetools import LRUCache, cached
from cachetools.keys import hashkey
from langchain.embeddings.base import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI

from backend.logger import logger
from backend.modules.model_gateway.audio_processing_svc import AudioProcessingSvc
from backend.modules.model_gateway.reranker_svc import InfinityRerankerSvc
from backend.settings import settings
from backend.types import ModelConfig, ModelProviderConfig, ModelType


class ModelGateway:
    """
    A gateway for managing and accessing various AI models.
    This class serves as a central hub for model configuration, initialization,
    and retrieval.

    Attributes:
        provider_configs (List[ModelProviderConfig]): List of provider configurations.
        model_name_to_provider_config (Dict[str, ModelProviderConfig]): Mapping of model names to their provider configs.
        llm_models (List[ModelConfig]): Available LLM models.
        embedding_models (List[ModelConfig]): Available embedding models.
        reranker_models (List[ModelConfig]): Available reranker models.
        audio_models (List[ModelConfig]): Available audio processing models.
    """

    def __init__(self):
        """
        Initialize the ModelGateway.

        Loads configurations, initializes model lists, and sets up the gateway.
        Raises a ValueError if required API keys are not set in the environment.
        """
        self.provider_configs: List[ModelProviderConfig] = []
        self.model_name_to_provider_config: Dict[str, ModelProviderConfig] = {}
        self.llm_models: List[ModelConfig] = []
        self.embedding_models: List[ModelConfig] = []
        self.reranker_models: List[ModelConfig] = []
        self.audio_models: List[ModelConfig] = []

        self._model_cache = LRUCache()

        self._load_config()
        self._initialize_models()

    def _load_config(self):
        """
        Load model configurations from the specified YAML file.

        Parses the YAML config and initializes provider configurations.
        """
        logger.info(f"Loading models config from {settings.MODELS_CONFIG_PATH}")
        with open(settings.MODELS_CONFIG_PATH) as f:
            data = yaml.safe_load(f)
        logger.info(f"Loaded models config: {data}")

        self.provider_configs = [
            ModelProviderConfig.model_validate(item)
            for item in data.get("model_providers", [])
        ]

    def _initialize_models(self):
        """
        Initialize all models based on the loaded configurations.

        Checks API keys and registers models for each provider.
        """
        for provider_config in self.provider_configs:
            self._check_api_key(provider_config)
            self._register_models(provider_config)

    def _check_api_key(self, provider_config: ModelProviderConfig):
        """
        Verify that the required API key is set in the environment.

        Args:
            provider_config (ModelProviderConfig): The provider configuration to check.

        Raises:
            ValueError: If the required API key is not set in the environment.
        """
        if provider_config.api_key_env_var and not os.environ.get(
            provider_config.api_key_env_var
        ):
            raise ValueError(
                f"Environment variable {provider_config.api_key_env_var} not set. "
                f"Cannot initialize the model gateway."
            )

    def _register_models(self, provider_config: ModelProviderConfig):
        """
        Register models for a given provider across all supported model types.

        Args:
            provider_config (ModelProviderConfig): The provider configuration containing model IDs.
        """
        model_types = {
            "embedding": (provider_config.embedding_model_ids, self.embedding_models),
            "llm": (provider_config.llm_model_ids, self.llm_models),
            "reranking": (provider_config.reranking_model_ids, self.reranker_models),
            "audio": (provider_config.audio_model_ids, self.audio_models),
        }

        for model_type, (model_ids, model_list) in model_types.items():
            for model_id in model_ids:
                model_name = f"{provider_config.provider_name}/{model_id}"
                self.model_name_to_provider_config[model_name] = provider_config
                model_list.append(
                    ModelConfig(
                        name=model_name,
                        type=getattr(ModelType, model_type),
                    )
                )

    def _get_api_key(self, model_provider_config: ModelProviderConfig) -> str:
        """
        Retrieve the API key for a given model provider.

        Args:
            model_provider_config (ModelProviderConfig): The provider configuration.

        Returns:
            str: The API key or "EMPTY" if not set.
        """
        if not model_provider_config.api_key_env_var:
            return "EMPTY"
        return os.environ.get(model_provider_config.api_key_env_var, "")

    def _get_model_provider_config(self, model_name: str) -> ModelProviderConfig:
        """
        Get the provider configuration for a given model name.

        Args:
            model_name (str): The full name of the model.

        Returns:
            ModelProviderConfig: The provider configuration for the model.

        Raises:
            ValueError: If the model is not registered in the gateway.
        """
        if model_name not in self.model_name_to_provider_config:
            raise ValueError(f"Model {model_name} not registered in the model gateway.")
        return self.model_name_to_provider_config[model_name]

    def _get_model_id(self, model_name: str) -> str:
        """
        Extract the model ID from the full model name.

        Args:
            model_name (str): The full name of the model.

        Returns:
            str: The model ID.
        """
        return "/".join(model_name.split("/")[1:])

    def get_embedding_models(self) -> List[ModelConfig]:
        """
        Get a list of all available embedding models.

        Returns:
            List[ModelConfig]: Available embedding models.
        """
        return self.embedding_models

    def get_llm_models(self) -> List[ModelConfig]:
        """
        Get a list of all available LLM models.

        Returns:
            List[ModelConfig]: Available LLM models.
        """
        return self.llm_models

    def get_reranker_models(self) -> List[ModelConfig]:
        """
        Get a list of all available reranker models.

        Returns:
            List[ModelConfig]: Available reranker models.
        """
        return self.reranker_models

    def get_audio_models(self) -> List[ModelConfig]:
        """
        Get a list of all available audio processing models.

        Returns:
            List[ModelConfig]: Available audio processing models.
        """
        return self.audio_models

    @cached(
        cache=lambda self: self._model_cache,
        key=lambda self, model_name: hashkey("embedder", model_name),
    )
    def get_embedder_from_model_config(self, model_name: str) -> Embeddings:
        """
        Get a cached embedder instance for the specified model.

        Args:
            model_name (str): The name of the embedding model.

        Returns:
            Embeddings: A cached instance of the embedding model.
        """
        model_provider_config = self._get_model_provider_config(model_name)
        api_key = self._get_api_key(model_provider_config)
        model_id = self._get_model_id(model_name)

        return OpenAIEmbeddings(
            openai_api_key=api_key,
            model=model_id,
            openai_api_base=model_provider_config.base_url,
            check_embedding_ctx_length=(
                model_provider_config.provider_name == "openai"
            ),
        )

    @cached(
        cache=lambda self: self._model_cache,
        key=lambda self, model_config, stream: hashkey(
            "llm", model_config.name, stream
        ),
    )
    def get_llm_from_model_config(
        self, model_config: ModelConfig, stream=False
    ) -> BaseChatModel:
        """
        Get a cached LLM instance for the specified model configuration.

        Args:
            model_config (ModelConfig): The configuration of the LLM model.
            stream (bool, optional): Whether to enable streaming. Defaults to False.

        Returns:
            BaseChatModel: A cached instance of the LLM model.
        """
        model_provider_config = self._get_model_provider_config(model_config.name)
        api_key = self._get_api_key(model_provider_config)
        model_id = self._get_model_id(model_config.name)

        parameters = model_config.parameters or {}

        return ChatOpenAI(
            model=model_id,
            temperature=parameters.get("temperature", 0.1),
            max_tokens=parameters.get("max_tokens", 1024),
            streaming=stream,
            api_key=api_key,
            base_url=model_provider_config.base_url,
            default_headers=model_provider_config.default_headers,
        )

    @cached(
        cache=lambda self: self._model_cache,
        key=lambda self, model_name, top_k: hashkey("reranker", model_name, top_k),
    )
    def get_reranker_from_model_config(self, model_name: str, top_k: int = 3):
        """
        Get a cached reranker instance for the specified model.

        Args:
            model_name (str): The name of the reranker model.
            top_k (int, optional): The number of top results to return. Defaults to 3.

        Returns:
            InfinityRerankerSvc: A cached instance of the reranker model.
        """
        model_provider_config = self._get_model_provider_config(model_name)
        api_key = self._get_api_key(model_provider_config)
        model_id = self._get_model_id(model_name)

        return InfinityRerankerSvc(
            model=model_id,
            api_key=api_key,
            base_url=model_provider_config.base_url,
            top_k=top_k,
        )

    @cached(
        cache=lambda self: self._model_cache,
        key=lambda self, model_name: hashkey("audio", model_name),
    )
    def get_audio_model_from_model_config(self, model_name: str):
        """
        Get a cached audio processing model instance for the specified model.

        Args:
            model_name (str): The name of the audio processing model.

        Returns:
            AudioProcessingSvc: A cached instance of the audio processing model.
        """
        model_provider_config = self._get_model_provider_config(model_name)
        api_key = self._get_api_key(model_provider_config)
        _, model = model_name.split("/", 1)

        return AudioProcessingSvc(
            api_key=api_key,
            base_url=model_provider_config.base_url,
            model=model,
        )


model_gateway = ModelGateway()
