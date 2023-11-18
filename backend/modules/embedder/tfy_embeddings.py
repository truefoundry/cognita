import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import tqdm
from langchain.embeddings.base import Embeddings
from typing import List, Any
import concurrent.futures
import math


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


class TruefoundryEmbeddings(Embeddings):
    def __init__(
        self,
        endpoint_url: str,
        batch_size: int = EMBEDDER_BATCH_SIZE,
        parallel_workers: int = PARALLEL_WORKERS,
        **kwargs: Any,
    ):
        """
        Initializes the TruefoundryEmbeddings.

        Args:
            endpoint_url (str): The URL of the deployed embedding model on Truefoundry.
            batch_size (int, optional): The batch size for processing embeddings in parallel.
            parallel_workers (int, optional): The number of parallel worker threads for embedding.
        Returns:
            None
        """
        try:
            session = _requests_retry_session(
                retries=3,
                backoff_factor=3,
                status_forcelist=(400, 408, 499, 500, 502, 503, 504),
            )
            response = session.post(
                url=f"{endpoint_url.strip('/')}/v2/repository/index", json={}
            )
            response.raise_for_status()
            models = response.json()
            if len(models) == 0:
                raise ValueError("No model is deployed in the model server")
            model_names = [m["name"] for m in models]
        except Exception as ex:
            raise Exception(f"Error raised by Inference API: {ex}") from ex
        else:
            model_name = model_names[0]
            self.endpoint = (
                f"{endpoint_url.strip('/')}/v2/models/{model_name}/infer/simple"
            )
        self.client = None
        self.batch_size = int(batch_size)
        self.parallel_workers = int(parallel_workers)
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.parallel_workers
        )

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
            "inputs": texts,
        }
        response = session.post(self.endpoint, json=payload, timeout=30)
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
