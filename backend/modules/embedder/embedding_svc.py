import concurrent.futures
from typing import Dict, List

import requests
from langchain.embeddings.base import Embeddings
from tqdm.auto import tqdm

from backend.logger import logger
from backend.settings import settings


class EmbeddingSvc(Embeddings):
    def __init__(self, **kwargs) -> None:
        # ideally get url from settings
        self.url = settings.EMBEDDING_SVC_URL
        # 8 tokens for query and 2 for start and stop tokens
        self.embedding_ctx_length = 500
        self.chunk_size = 4

    def encode(self, text: str) -> Dict:
        response = requests.post(
            f"{self.url}/tokenize",
            json={"inputs": text, "add_special_tokens": False},
        )

        if response.status_code != 200:
            logger.error(f"Tokenization failed: {response.text}")
            return {}
        return [token["id"] for tokens_list in response.json() for token in tokens_list]

    def decode(self, token_ids: List[int]) -> str:
        response = requests.post(
            f"{self.url}/decode",
            json={"ids": token_ids, "skip_special_tokens": True},
        )
        if response.status_code != 200:
            logger.error(f"Detokenization failed: {response.text}")
            return []
        return response.json()

    def embed_all(self, tokens_batch: List[List[str]]) -> List[List[float]]:
        logger.info("Embedding...")
        response = requests.post(
            f"{self.url}/embed_all",
            json={"inputs": tokens_batch, "truncate": True},
        )
        if response.status_code != 200:
            logger.error(f"Embedding failed: {response.text}")
            return []
        logger.info("Embedding done...")
        return response.json()

    # For retrieval you need to pass this prompt.
    def transform_query(self, query: str) -> str:
        """For retrieval, add the prompt for query (not for documents)."""
        return f"Represent this sentence for searching relevant passages: {query}"

    def _get_len_safe_embeddings(self, texts: str) -> List[List[float]]:
        """
        Generate length-safe embeddings for a list of texts.

        This method handles tokenization and embedding generation,
        respecting the set embedding context length and chunk size.
        """

        tokens = []
        indices = []

        def process_text(text):
            tokenized = self.encode(text)
            # Split tokens into chunks respecting the embedding_ctx_length
            for j in range(0, len(tokenized), self.embedding_ctx_length):
                token_chunk = tokenized[j : j + self.embedding_ctx_length]
                # Convert token IDs back to a string
                chunk_text = self.decode(token_chunk)[0]
                tokens.append(chunk_text)
                indices.append(j)

        logger.info("Chunking...")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(process_text, text)
                for text in tqdm(texts, total=len(texts))
            ]
            concurrent.futures.wait(futures)

        logger.info("Embedding...")
        _iter = tqdm(range(0, len(tokens), self.chunk_size))
        batched_embeddings: List[List[float]] = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.embed_all, tokens[i : i + self.chunk_size])
                for i in _iter
            ]
            concurrent.futures.wait(futures)
            for future in futures:
                embeddings = future.result()
                batched_embeddings.extend(embeddings)
        return batched_embeddings[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        return self._get_len_safe_embeddings(texts)

    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        return self.embed_documents([self.transform_query(text)])[0]
