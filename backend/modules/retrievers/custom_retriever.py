from typing import List

from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseRetriever, Document

from backend.utils.logger import logger


class CustomRetriever(BaseRetriever):
    """Custom Retriever."""

    retriever: BaseRetriever
    llm: BaseChatModel
    query_template: str = """As an assistant, your role is to translate a user's natural \
language query into a suitable query for a vectorstore, ensuring to omit any extraneous \
information that may hinder the retrieval process. Please take the provided user query "{question}" \
and refine it into a concise, relevant query for the vectorstore, focusing only on the \
essential elements required for accurate and efficient data retrieval."""

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        """Get docs."""
        # rewrite the question for retrieval
        query_template = self.query_template.format(question=query)
        question = self.llm.predict(query_template)

        logger.info(
            f"Retrieving documents for updated question: {question} instead of {query}"
        )
        # retrieve N docs
        docs = self.retriever.get_relevant_documents(
            question, callbacks=run_manager.get_child()
        )
        return docs
