from langchain.embeddings.base import Embeddings
from typing import Dict, List

import torch
import numpy as np
from transformers import AutoModel, AutoTokenizer

# https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1
class MixBreadEmbeddings(Embeddings):

    def __init__(self, model) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.model = AutoModel.from_pretrained(model)

    
    # The model works really well with cls pooling (default) but also with mean poolin.
    def pooling(self, outputs: torch.Tensor, inputs: Dict,  strategy: str = 'cls') -> np.ndarray:
        if strategy == 'cls':
            outputs = outputs[:, 0]
        elif strategy == 'mean':
            outputs = torch.sum(
                outputs * inputs["attention_mask"][:, :, None], dim=1) / torch.sum(inputs["attention_mask"])
        else:
            raise NotImplementedError
        return outputs.detach().cpu().numpy()
    
    # For retrieval you need to pass this prompt.
    # https://www.mixedbread.ai/blog/mxbai-embed-large-v1
    def transform_query(self, query: str) -> str:
        """ For retrieval, add the prompt for query (not for documents).
        """
        return f'Represent this sentence for searching relevant passages: {query}'

    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        inputs = self.tokenizer(texts, padding=True, return_tensors='pt')
        outputs = self.model(**inputs)
        embeddings = self.pooling(outputs.last_hidden_state, inputs)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        return self.embed_documents([self.transform_query(text)])[0]
