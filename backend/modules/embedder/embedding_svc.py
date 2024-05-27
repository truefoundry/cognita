from typing import List, Union

import requests
from langchain.embeddings.base import Embeddings

from backend.settings import settings


class EmbeddingSvc(Embeddings):
    """If you deploying the embedding service using hf inference server, you can use this class to interact with it.
    It does not require any model to be loaded in the backend. It sends the text to the embedding service and gets the embeddings back.

    ```
    embedder_config:
        provider: embedding-svc
    ```
    OR
    ```
    'embedder_config' : {
        'provider': 'embedding-svc'
    }
    ```
    """

    def __init__(self, **kwargs) -> None:
        # ideally get url from settings
        self.url = settings.EMBEDDING_SVC_URL

    def call_embedding_service(
        self, texts: Union[str, List[str]], type: str
    ) -> Union[List[float], List[List[float]]]:
        """Call the embedding service."""
        if type == "query":
            response = requests.post(
                self.url.rstrip("/") + "/embed-query", json={"text": texts}
            )
        elif type == "documents":
            response = requests.post(
                self.url.rstrip("/") + "/embed-documents", json={"texts": texts}
            )
        response.raise_for_status()
        return response.json()["embeddings"]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        return self.call_embedding_service(texts, "documents")

    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        return self.call_embedding_service(text, "query")
