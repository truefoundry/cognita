import asyncio
import logging
import os
from functools import partial
from typing import Any, Dict, List, Mapping, Optional

import requests
from langchain.chat_models.base import BaseChatModel
from langchain.pydantic_v1 import Extra, Field, root_validator
from langchain.schema import ChatGeneration, ChatResult
from langchain.schema.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.utils.logger import logger

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """Your task is to craft the most helpful, highly informative, accurate and comprehensive answers possible, 
    ensuring they are easy to understand and implement. Use the context information provided as a reference to form accurate responses 
    that incorporate as much relevant detail as possible. Strive to make each answer clear and precise to enhance user comprehension and 
    assist in solving their problems effectively.\n\nEmploy the provided context information meticulously to craft precise answers, 
    ensuring they incorporate all pertinent details. Structure your responses for ease of reading and relevance by providing as much as 
    information regarding it. Make sure the answers are well detailed and provide proper references. Align your answers with the context given and maintain transparency 
    by indicating any uncertainty or lack of knowledge regarding the correct answer to avoid providing incorrect information."""


def _requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 503, 504),
    method_whitelist=frozenset({"GET", "POST"}),
    session=None,
):
    """
    Returns a `requests` session with retry capabilities for certain HTTP status codes.

    Args:
        retries (int): The number of retries for HTTP requests.
        backoff_factor (float): The backoff factor for exponential backoff during retries.
        status_forcelist (tuple): A tuple of HTTP status codes that should trigger a retry.
        method_whitelist (frozenset): The set of HTTP methods that should be retried.
        session (requests.Session, optional): An optional existing requests session to use.

    Returns:
        requests.Session: A session with retry capabilities.
    """
    # Implementation taken from https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        status=retries,
        backoff_factor=backoff_factor,
        allowed_methods=method_whitelist,
        status_forcelist=status_forcelist,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class TrueFoundryLLMGateway(BaseChatModel):
    """`TrueFoundry LLM Gateway` chat models API.

    To use, you must have the environment variable ``TFY_API_KEY`` set with your API key and ``TFY_HOST`` set with your host or pass it as a named parameter to the constructor.
    """

    model: str = Field(default=None)
    """The model to use for embedding."""
    tfy_host: Optional[str] = Field(default=None, alias="url")
    """Base URL path for API requests, Automatically inferred from env var `TFY_HOST` if not provided."""
    tfy_api_key: Optional[str] = Field(default=None, alias="api_key")
    """Automatically inferred from env var `TFY_API_KEY` if not provided."""
    model_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tfy_llm_gateway_url: Optional[str] = Field(default=None)
    """Overwrite for tfy_host for LLM Gateway"""
    tfy_llm_gateway_path: Optional[str] = Field(
        default=None,
    )
    system_prompt: str = Field(default=SYSTEM_INSTRUCTION)

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        allow_population_by_field_name = True

    @classmethod
    def is_lc_serializable(cls) -> bool:
        """Return whether this model can be serialized by Langchain."""
        return False

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        values["tfy_api_key"] = values["tfy_api_key"] or os.getenv("TFY_API_KEY")
        values["tfy_host"] = values["tfy_host"] or os.getenv("TFY_HOST")
        values["tfy_llm_gateway_url"] = values["tfy_llm_gateway_url"] or os.getenv(
            "TFY_LLM_GATEWAY_ENDPOINT"
        )
        values["tfy_llm_gateway_path"] = (
            values["tfy_llm_gateway_path"]
            or os.getenv("TFY_LLM_GATEWAY_PATH")
            or "/api/llm"
        )
        if not values["tfy_api_key"]:
            raise ValueError(
                f"Did not find `tfy_api_key`, please add an environment variable"
                f" `TFY_API_KEY` which contains it, or pass"
                f"  `tfy_api_key` as a named parameter."
            )
        if not values["tfy_host"]:
            raise ValueError(
                f"Did not find `tfy_host`, please add an environment variable"
                f" `TFY_HOST` which contains it, or pass"
                f"  `tfy_host` as a named parameter."
            )
        return values

    def _generate(
        self,
        messages: List[BaseMessage],
        **kwargs: Any,
    ) -> ChatResult:
        message_dicts = [
            TrueFoundryLLMGateway._convert_message_to_dict(message)
            for message in messages
        ]
        if message_dicts[0].get("role") != "system":
            message_dicts.insert(0, {"role": "system", "content": self.system_prompt})
        payload = {
            "messages": message_dicts,
            "model": {
                "name": self.model,
                "parameters": self.model_parameters if self.model_parameters else {},
            },
        }
        session = _requests_retry_session(
            retries=5,
            backoff_factor=3,
            status_forcelist=(400, 408, 499, 500, 502, 503, 504),
        )

        tfy_llm_gateway_endpoint = (
            f"{self.tfy_llm_gateway_url}/api/inference/chat"
            if self.tfy_llm_gateway_url
            else f"{self.tfy_host}{self.tfy_llm_gateway_path}/api/inference/chat"
        )
        logger.info(
            f"Chat using - model: {self.model} at endpoint: {tfy_llm_gateway_endpoint}"
        )
        response = session.post(
            url=tfy_llm_gateway_endpoint,
            json=payload,
            headers={
                "Authorization": f"Bearer {self.tfy_api_key}",
            },
            timeout=30,
        )
        response.raise_for_status()
        output = response.json()
        return TrueFoundryLLMGateway._create_chat_result(output["text"])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        **kwargs: Any,
    ) -> ChatResult:
        func = partial(self._generate, messages, **kwargs)
        return await asyncio.get_event_loop().run_in_executor(None, func)

    @property
    def _llm_type(self) -> str:
        """Return type of chat model."""
        return "chat"

    @staticmethod
    def _convert_dict_to_message(_dict: Mapping[str, Any]) -> BaseMessage:
        role = _dict["role"]
        content = _dict["content"]
        if role == "user":
            return HumanMessage(content=content)
        elif role == "assistant":
            return AIMessage(content=content)
        elif role == "system":
            return SystemMessage(content=content)
        else:
            return ChatMessage(content=content, role=role)

    @staticmethod
    def _raise_functions_not_supported() -> None:
        raise ValueError(
            "Function messages are not supported by the TrueFoundry LLM Gateway."
        )

    def predict(self, text: str, **kwargs: Any) -> str:
        result = self(
            [SystemMessage(content="You are AI assistant"), HumanMessage(content=text)],
            **kwargs,
        )
        if isinstance(result.content, str):
            return result.content
        else:
            raise ValueError("Cannot use predict when output is not a string.")

    @staticmethod
    def _convert_message_to_dict(message: BaseMessage) -> dict:
        if isinstance(message, ChatMessage):
            message_dict = {"role": message.role, "content": message.content}
        elif isinstance(message, HumanMessage):
            message_dict = {"role": "user", "content": message.content}
        elif isinstance(message, AIMessage):
            message_dict = {"role": "assistant", "content": message.content}
        elif isinstance(message, SystemMessage):
            message_dict = {"role": "system", "content": message.content}
        elif isinstance(message, FunctionMessage):
            TrueFoundryLLMGateway._raise_functions_not_supported()
        else:
            raise ValueError(f"Got unknown message type: {message}")

        if "function_call" in message.additional_kwargs:
            TrueFoundryLLMGateway._raise_functions_not_supported()
        if message.additional_kwargs:
            logger.warning(
                "Additional message arguments are unsupported by TrueFoundry LLM Gateway "
                " and will be ignored: %s",
                message.additional_kwargs,
            )
        return message_dict

    @staticmethod
    def _create_chat_result(text: str) -> ChatResult:
        message = ChatMessage(role="user", content=text)
        generations = [
            ChatGeneration(
                message=message,
            )
        ]
        return ChatResult(generations=generations)

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        """Call out to the deployed model

        Args:
            prompt: The prompt to pass into the model.
            stop: Optional list of stop words to use when generating.

        Returns:
            The string generated by the model.

        Example:
            .. code-block:: python

                response = model("I have a joke for you...")
        """
        payload = {
            "prompt": prompt,
            "model": {
                "name": self.model,
                "parameters": self.model_parameters if self.model_parameters else {},
            },
        }
        session = _requests_retry_session(
            retries=5,
            backoff_factor=3,
            status_forcelist=(400, 408, 499, 500, 502, 503, 504),
        )

        tfy_llm_gateway_endpoint = (
            f"{self.tfy_llm_gateway_url}/api/inference/text"
            if self.tfy_llm_gateway_url
            else f"{self.tfy_host}{self.tfy_llm_gateway_path}/api/inference/text"
        )
        logger.info(
            f"Completion using - model: {self.model} at endpoint: {tfy_llm_gateway_endpoint}"
        )
        response = session.post(
            url=tfy_llm_gateway_endpoint,
            json=payload,
            headers={
                "Authorization": f"Bearer {self.tfy_api_key}",
            },
            timeout=30,
        )
        response.raise_for_status()
        output = response.json()
        return output["text"]
