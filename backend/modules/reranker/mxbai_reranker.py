from langchain.retrievers.document_compressors.base import BaseDocumentCompressor
from langchain.docstore.document import Document
from typing import List, Optional, Sequence
from langchain.callbacks.manager import Callbacks
from sentence_transformers import CrossEncoder

class MxBaiReranker(BaseDocumentCompressor):
    """
    Document compressor that uses a pipeline of Transformers.
    """
    model: str
    top_k: int = 3

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """Compress retrieved documents given the query context."""
        model = CrossEncoder(self.model)
        docs = [doc.page_content for doc in documents]
        reranked_docs = model.rank(query, docs, return_documents=True, top_k=self.top_k)

        documents = [
            Document(
                page_content=doc['text'], 
                metadata=documents[doc['corpus_id']].metadata
            ) for doc in reranked_docs
        ]
        return documents