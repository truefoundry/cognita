from typing import List, Union

import requests
from langchain.embeddings.base import Embeddings

from backend.settings import settings


class InfinityEmbeddingSvc(Embeddings):
    """If you deploying the embedding service deployed using infinity API.
    Github: https://github.com/michaelfeil/infinity
    """

    def __init__(self, model, **kwargs) -> None:
        # ideally get url from settings
        self.url = settings.EMBEDDING_SVC_URL
        self.model = model

    def transform_query(self, query: str) -> str:
        """For retrieval, add the prompt for query (not for documents)."""
        return f"Represent this sentence for searching relevant passages: {query}"

    def call_embedding_service(
        self, texts: Union[str, List[str]], type: str
    ) -> Union[List[float], List[List[float]]]:
        """Call the embedding service."""
        if type == "query" and self.model.startswith("mixedbread"):
            # Only for mixedbread models
            texts = [self.transform_query(texts)]
        elif type == "query":
            texts = [texts]

        payload = {
            "input": texts,
            "model": self.model,
        }

        response = requests.post(self.url.rstrip("/") + "/embeddings", json=payload)
        response.raise_for_status()
        return [data["embedding"] for data in response.json()["data"]]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        return self.call_embedding_service(texts, "documents")

    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        return self.call_embedding_service(text, "query")[0]
