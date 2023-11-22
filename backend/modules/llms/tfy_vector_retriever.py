import uuid
from typing import List, Optional

import cohere
import numpy as np
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.retrievers import MultiVectorRetriever
from langchain.schema import Document
from langchain.text_splitter import TextSplitter

from backend.utils.logger import logger


class CustomParentDocumentRetriever(MultiVectorRetriever):
    """Retrieve small chunks then retrieve their parent documents."""

    child_splitter: TextSplitter
    """The text splitter to use to create child documents."""
    parent_splitter: Optional[TextSplitter] = None
    """The text splitter to use to create parent documents."""

    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None,
        add_to_docstore: bool = True,
    ) -> None:
        """Adds documents to the docstore and vectorstores."""
        if self.parent_splitter is not None:
            # exclude tables while splitting
            texts = [
                doc for doc in documents if doc.metadata.get("type", "") != "table"
            ]
            tables = [
                doc for doc in documents if doc.metadata.get("type", "") == "table"
            ]
            documents = self.parent_splitter.split_documents(texts)
            documents.extend(tables)
        if ids is None:
            doc_ids = [str(uuid.uuid4()) for _ in documents]
            if not add_to_docstore:
                raise ValueError(
                    "If ids are not passed in, `add_to_docstore` MUST be True"
                )
        else:
            if len(documents) != len(ids):
                raise ValueError(
                    "Got uneven list of documents and ids. "
                    "If `ids` is provided, should be same length as `documents`."
                )
            doc_ids = ids

        docs = []
        full_docs = []
        for i, doc in enumerate(documents):
            _id = doc_ids[i]
            if doc.metadata.get("type", "") != "table":
                sub_docs = self.child_splitter.split_documents([doc])
            else:
                sub_docs = [doc]
            for _doc in sub_docs:
                _doc.metadata[self.id_key] = _id
            docs.extend(sub_docs)
            full_docs.append((_id, doc))
        self.vectorstore.add_documents(docs)
        if add_to_docstore:
            self.docstore.mset(full_docs)

    def rerank_responses(self, query, responses, num_responses):
        # transform langchain documents to dictionary
        responses = [response.dict() for response in responses]
        responses = [
            dict(text=response.get("page_content"), metadata=response.get("metadata"))
            for response in responses
        ]

        # initialize cohere reranker client
        co = cohere.Client()
        reranked_responses = co.rerank(
            model="rerank-english-v2.0",
            query=query,
            documents=responses,
            top_n=num_responses,
        )
        logger.info("Documents successfully reranked by cohere.")
        return [reranked_response.index for reranked_response in reranked_responses]

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Get documents relevant to a query."""
        sub_docs = self.vectorstore.similarity_search(query, **self.search_kwargs)

        # re-rank sub documents based on the query
        ranked_indices = self.rerank_responses(
            query, sub_docs, num_responses=self.search_kwargs.get("k")
        )
        sub_docs = np.take(sub_docs, ranked_indices).tolist()

        # We do this to maintain the order of the ids that are returned
        ids = []
        for d in sub_docs:
            if d.metadata[self.id_key] not in ids:
                ids.append(d.metadata[self.id_key])
        docs = self.docstore.mget(ids)
        return [d for d in docs if d is not None]
