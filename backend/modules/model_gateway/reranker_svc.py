from typing import Optional, Sequence

import requests
from langchain.callbacks.manager import Callbacks
from langchain.docstore.document import Document
from langchain.retrievers.document_compressors.base import BaseDocumentCompressor

from backend.logger import logger


class InfinityRerankerSvc(BaseDocumentCompressor):
    """
    Reranker Service that uses Infinity API for document reranking.
    GitHub: https://github.com/michaelfeil/infinity
    """

    def __init__(
        self, model: str, top_k: int, base_url: str, api_key: Optional[str] = None
    ):
        """
        Initialize the InfinityRerankerSvc.

        Args:
            model: The model to use for reranking.
            top_k: The number of top documents to return.
            base_url: The base URL for the Infinity API.
            api_key: Optional API key for authentication.
        """
        self.model = model
        self.top_k = top_k
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """
        Compress retrieved documents given the query context.

        Args:
            documents: The input documents to rerank.
            query: The query to use for reranking.
            callbacks: Optional callbacks (not used in this implementation).

        Returns:
            A sequence of reranked documents.
        """
        reranked_docs = self._get_reranked_results(documents, query)
        return self._process_reranked_results(documents, reranked_docs)

    def _get_reranked_results(self, documents: Sequence[Document], query: str) -> dict:
        """
        Send a request to the Infinity API to get reranked results.

        Args:
            documents: The input documents to rerank.
            query: The query to use for reranking.

        Returns:
            A dictionary containing the reranked results.
        """
        payload = {
            "query": query,
            "documents": [doc.page_content for doc in documents],
            "return_documents": False,
            "model": self.model,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = requests.post(
            f"{self.base_url}/rerank", headers=headers, json=payload
        )
        response.raise_for_status()
        reranked_docs = response.json()

        logger.info(f"Reranked documents: {reranked_docs}")
        return reranked_docs

    def _process_reranked_results(
        self, original_docs: Sequence[Document], reranked_docs: dict
    ) -> Sequence[Document]:
        """
        Process the reranked results and return the top-k documents.

        Args:
            original_docs: The original input documents.
            reranked_docs: The reranked results from the API.

        Returns:
            A sequence of reranked documents.
        """
        sorted_results = sorted(
            reranked_docs.get("results", []),
            key=lambda x: x["relevance_score"],
            reverse=True,
        )[: self.top_k]

        ranked_documents = []
        for result in sorted_results:
            index = result["index"]
            relevance_score = round(result["relevance_score"], 2)
            doc = original_docs[index]
            doc.metadata["relevance_score"] = relevance_score
            ranked_documents.append(doc)

        return ranked_documents
