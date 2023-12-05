import concurrent.futures
import math
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
import tqdm
from langchain.embeddings.base import Embeddings
from langchain.pydantic_v1 import Extra, Field, root_validator
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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


EMBEDDER_BATCH_SIZE = 32
PARALLEL_WORKERS = 4


class TrueFoundryEmbeddings(Embeddings):
    """TrueFoundry embedding models.

    To use, you should have the ``servicefoundry`` python package installed, and the
    environment variable ``TFY_API_KEY`` set with your API key and ``TFY_HOST`` set with your host or pass it
    as a named parameter to the constructor.

    Example:
        .. code-block:: python

            from servicefoundry.langchain.truefoundry_embedding import TrueFoundryEmbeddings
            truefoundry = TrueFoundryEmbeddings(tfy_api_key="my-api-key",tfy_llm_gateway_url="my-gateway-url")

    """

    model: str = Field(default=None)
    """The model to use for embedding."""
    tfy_host: Optional[str] = Field(default=None, alias="url")
    """Base URL path for API requests, Automatically inferred from env var `TFY_HOST` if not provided."""
    tfy_api_key: Optional[str] = Field(default=None, alias="api_key")
    """Automatically inferred from env var `TFY_API_KEY` if not provided."""
    model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    model_parameters: Dict[str, Any] = Field(default_factory=dict)
    tfy_llm_gateway_url: Optional[str] = Field(default=None, alias="llm_gateway_url")
    """Overwrite for tfy_host for LLM Gateway"""
    batch_size: Optional[int] = Field(default=EMBEDDER_BATCH_SIZE)
    """The batch size to use for embedding."""
    parallel_workers: Optional[int] = Field(default=PARALLEL_WORKERS)
    """The number of parallel workers to use for embedding."""

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        allow_population_by_field_name = True

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        values["tfy_api_key"] = values["tfy_api_key"] or os.getenv("TFY_API_KEY")
        values["tfy_host"] = values["tfy_host"] or os.getenv("TFY_HOST")
        values["tfy_llm_gateway_url"] = values["tfy_llm_gateway_url"] or os.getenv(
            "TFY_LLM_GATEWAY_URL"
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

    def __init__(
        self,
        **kwargs: Any,
    ):
        """
        Initializes the TruefoundryEmbeddings.
        """
        self.client = None
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.parallel_workers
        )
        if self.tfy_llm_gateway_url:
            self.endpoint = f"{self.tfy_llm_gateway_url}/api/inference/embedding"
        else:
            self.endpoint = f"{self.tfy_host}/api/llm/api/inference/embedding"

    def __del__(self):
        """
        Destructor method to clean up the executor when the object is deleted.

        Args:
            None

        Returns:
            None
        """
        self._executor.shutdown()

    def _remote_embed(self, texts, query_mode=False):
        """
        Perform remote embedding using a HTTP POST request to a designated endpoint.

        Args:
            texts (List[str]): A list of text strings to be embedded.
            query_mode (bool): A flag to indicate if running in query mode or in embed mode (indexing).
        Returns:
            List[List[float]]: A list of embedded representations of the input texts.
        """
        session = _requests_retry_session(
            retries=5,
            backoff_factor=3,
            status_forcelist=(400, 408, 499, 500, 502, 503, 504),
        )
        payload = {
            "input": texts,
            "model": {"name": self.model, "parameters": self.model_parameters},
        }
        response = session.post(
            self.endpoint,
            json=payload,
            headers={
                "Authorization": f"Bearer {self.tfy_api_key}",
            },
            timeout=30,
        )
        response.raise_for_status()
        embeddings = response.json()
        return embeddings

    def _embed(self, texts: List[str], query_mode: bool):
        """
        Perform embedding on a list of texts using remote embedding in chunks.

        Args:
            texts (List[str]): A list of text strings to be embedded.
            query_mode (bool): A flag to indicate if running in query mode or in embed mode (indexing).
        Returns:
            List[List[float]]: A list of embedded representations of the input texts.
        """
        embeddings = []

        def _feeder():
            for i in range(0, len(texts), self.batch_size):
                chunk = texts[i : i + self.batch_size]
                yield chunk

        embeddings = list(
            tqdm.tqdm(
                self._executor.map(self._remote_embed, _feeder()),
                total=int(math.ceil(len(texts) / self.batch_size)),
            )
        )
        return [item for batch in embeddings for item in batch]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of text documents.

        Args:
            texts (List[str]): A list of text documents to be embedded.

        Returns:
            List[List[float]]: A list of embedded representations of the input documents.
        """
        return self._embed(texts, query_mode=False)

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a query text.

        Args:
            text (str): The query text to be embedded.

        Returns:
            List[float]: The embedded representation of the input query text.
        """
        return self._embed([text], query_mode=True)[0]
