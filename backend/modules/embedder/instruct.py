from typing import Any, List, Optional

import requests
from langchain.embeddings.base import Embeddings


class RemoteHuggingFaceInstructEmbeddings(Embeddings):
    """
    Custom InstructorEmbedding class with langchain support.
    """

    def __init__(
        self,
        id_: Optional[str] = None,
        embedding_configuration: dict = None,
        **kwargs: Any
    ):
        """
        Initialize the RemoteHuggingFaceInstructEmbeddings.

        Args:
            id_ (str, optional): An optional ID for the embeddings instance.
            embedding_configuration (dict, optional): A dictionary containing configuration parameters for the embeddings.

        Returns:
            None
        """
        self.id = id_
        self.client = None
        self.embeddings_configuration = embedding_configuration

    def _remote_embed(self, texts, query_mode):
        """
        Perform remote embedding using a HTTP POST request to a designated endpoint.

        Args:
            texts (List[str]): A list of text strings to be embedded.
            query_mode (bool): A flag to indicate if running in query mode or in embed mode (indexing).

        Returns:
            List[List[float]]: A list of embedded representations of the input texts.
        """
        payload = {
            "texts": texts,
            "query_mode": query_mode,
            "instruction": self.embeddings_configuration.get("query_instruction")
            if query_mode
            else self.embeddings_configuration.get("embed_instruction"),
        }
        if self.id:
            payload["id"] = self.id
        response = requests.post(
            self.embeddings_configuration.get("embedder_endpoint"), json=payload
        )
        response.raise_for_status()
        return response.json()["data"]["embeddings"]

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
        for i in range(
            0,
            len(texts),
            int(self.embeddings_configuration.get("embedder_batchsize")),
        ):
            chunk = texts[
                i : i + int(self.embeddings_configuration.get("embedder_batchsize"))
            ]
            chunk_embeddings = self._remote_embed(chunk, query_mode)
            embeddings.extend(chunk_embeddings)
        return embeddings

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
