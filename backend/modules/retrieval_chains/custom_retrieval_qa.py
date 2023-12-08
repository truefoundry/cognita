from typing import List

from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.chains import RetrievalQA
from langchain.chat_models.base import BaseChatModel
from langchain.schema import Document

from backend.utils.logger import logger


class CustomRetrievalQA(RetrievalQA):
    """Custom RetrievalQA chain."""

    llm: BaseChatModel = None
    query_template: str = """As an assistant, your role is to translate a user's natural \
language query into a suitable query for a vectorstore, ensuring to omit any extraneous \
information that may hinder the retrieval process. Please take the provided user query "{question}" \
and refine it into a concise, relevant query for the vectorstore, focusing only on the \
essential elements required for accurate and efficient data retrieval."""

    def _get_docs(
        self,
        question: str,
        *,
        run_manager: CallbackManagerForChainRun,
    ) -> List[Document]:
        """Get docs."""
        # rewrite the question for retrieval
        query_template = self.query_template.format(question=question)
        updated_question = self.llm.predict(query_template)

        logger.info(
            f"Retrieving documents for updated question: {updated_question} instead of {question}"
        )
        # retrieve N docs
        docs = self.retriever.get_relevant_documents(
            updated_question, callbacks=run_manager.get_child()
        )
        return docs
