from typing import List, Optional, Sequence

import requests
from langchain.callbacks.manager import Callbacks
from langchain.docstore.document import Document
from langchain.retrievers.document_compressors.base import BaseDocumentCompressor

from backend.logger import logger
from backend.settings import settings


# Reranking Service using Infinity API
class InfinityRerankerSvc(BaseDocumentCompressor):
    """
    Reranker Service that uses Infinity API
    Github: https://github.com/michaelfeil/infinity
    """

    model: str
    top_k: int = 3
    url = settings.RERANKER_SVC_URL

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """Compress retrieved documents given the query context."""
        docs = [doc.page_content for doc in documents]

        payload = {
            "query": query,
            "documents": docs,
            "return_documents": False,
            "model": self.model,
        }

        reranked_docs = requests.post(
            self.url.rstrip("/") + "/rerank", json=payload
        ).json()

        """
        reranked_docs =
        {
            "results": [
                {
                    "relevance_score": 0.039407938718795776,
                    "index": 0,
                },
                {
                    "relevance_score": 0.03979039937257767,
                    "index": 1,
                },
                {
                    "relevance_score": 0.1976623684167862,
                    "index": 2,
                }
            ]
        }
        """

        logger.info(f"Reranked documents: {reranked_docs}")

        # Sort the results by relevance_score in descending order
        sorted_results = sorted(
            reranked_docs.get("results"),
            key=lambda x: x["relevance_score"],
            reverse=True,
        )

        # Extract the indices from the sorted results
        sorted_indices = [result["index"] for result in sorted_results][: self.top_k]

        # sort documents based on the sorted indices
        documents = [documents[index] for index in sorted_indices]
        return documents
