# from typing import List, Optional, Sequence

# import torch
# from langchain.callbacks.manager import Callbacks
# from langchain.docstore.document import Document
# from langchain.retrievers.document_compressors.base import BaseDocumentCompressor
# from sentence_transformers import CrossEncoder

# MODEL = CrossEncoder(
#     "mixedbread-ai/mxbai-rerank-xsmall-v1",
#     device="cuda" if torch.cuda.is_available() else "cpu",
# )


# # More about why re-ranking is essential: https://www.mixedbread.ai/blog/mxbai-rerank-v1
# class MxBaiRerankerSmall(BaseDocumentCompressor):
#     """
#     Document compressor that uses a pipeline of Transformers.
#     """

#     top_k: int = 3

#     def compress_documents(
#         self,
#         documents: Sequence[Document],
#         query: str,
#         callbacks: Optional[Callbacks] = None,
#     ) -> Sequence[Document]:
#         """Compress retrieved documents given the query context."""
#         docs = [doc.page_content for doc in documents]
#         reranked_docs = MODEL.rank(query, docs, return_documents=True, top_k=self.top_k)

#         documents = [
#             Document(
#                 page_content=doc["text"], metadata=documents[doc["corpus_id"]].metadata
#             )
#             for doc in reranked_docs
#         ]
#         return documents
