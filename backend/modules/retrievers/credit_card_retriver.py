from typing import List
from fastapi import HTTPException

from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseRetriever, Document
from langchain.schema.vectorstore import VectorStoreRetriever


from backend.utils.logger import logger
from backend.modules.retrievers.base import TFBaseRetriever, retriever_post
from backend.utils.base import RetrivalQuery
from backend.modules.metadata_store import get_metadata_store_client
from backend.modules.vector_db import get_vector_db_client
from backend.settings import settings
from servicefoundry.langchain import TrueFoundryChat
from backend.modules.embedder import get_embedder


RETRIEVER_NAME = 'credit-card'

class CreditCardRetriver(TFBaseRetriever, BaseRetriever):
    """Custom Retriever that inherits TFRetriver and Langchain BaseRetriver."""

    retriever_name = RETRIEVER_NAME
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
            query
        )

        print("DOCS:",docs, type(docs))
        return docs

# This decorator will create path as: /retriver/<RETRIEVER_NAME>/<func_name>
@retriever_post(RETRIEVER_NAME)
async def get_answer(
    request: RetrivalQuery
) -> List:
    """Get docs."""

    metadata_store_client = get_metadata_store_client(config=settings.METADATA_STORE_CONFIG)
    collection = metadata_store_client.get_collection_by_name(request.collection_name)

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    try:
        # Vector Store Client
        vector_db_client = get_vector_db_client(
            config=settings.VECTOR_DB_CONFIG, collection_name=request.collection_name
        )
        # Model to use for chat
        llm = TrueFoundryChat(
            model=request.model_configuration.name,
            model_parameters=request.model_configuration.parameters,
            system_prompt=request.system_prompt,
        )
        logger.info(f"Loaded TrueFoundry LLM model {request.model_configuration.name}")

        # get vector store
        vector_store = vector_db_client.get_vector_store(
            embeddings=get_embedder(collection.embedder_config),
        )

        # get retriever
        base_retriever = VectorStoreRetriever(
            vectorstore=vector_store,
            search_type=request.retriever_config.get_search_type,
            search_kwargs=request.retriever_config.get_search_kwargs,
        )

        retriver_obj = CreditCardRetriver(retriever=base_retriever, llm=llm)
        documents = retriver_obj._get_relevant_documents(request.query)
        return documents
        
    except HTTPException as exp:
        raise exp
    except Exception as exp:
        logger.exception(exp)
        raise HTTPException(status_code=500, detail=str(exp))





    




    
    

    

