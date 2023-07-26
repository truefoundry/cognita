import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import tqdm
import numpy as np
from langchain.embeddings.base import Embeddings
from typing import List, Dict, Any
import concurrent.futures
import math


def _requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 503, 504),
    method_whitelist=frozenset({"GET", "POST"}),
    session=None,
):
    # Taken from https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    session = session or requests.Session()
    retry = Retry(
        total=retries,  # how many overall errors can we tolerate
        read=retries,  # how many read errors can we tolerate
        connect=retries,  # how many connection failures we can tolerate
        status=retries,  # how many failures from `status_forcelist` we can tolerate
        backoff_factor=backoff_factor,  # Sleep for backoff_factor * (2 ^ (try_count - 1))
        allowed_methods=method_whitelist,
        status_forcelist=status_forcelist,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    # noinspection HttpUrlsUsage
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
        self._executor.shutdown()

    def _remote_embed(self, texts, query_mode=False):
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
        return self._embed(texts, query_mode=False)

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text], query_mode=True)[0]
