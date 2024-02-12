from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Any
from fastapi import APIRouter

from backend.settings import settings
from backend.utils.logger import logger
from backend.modules.metadata_store.models import Collection
from backend.utils.base import RetrieverConfig, LLMConfig
from langchain.chat_models.base import SimpleChatModel as LangChainSimpleChatModel

# TODO: Change this to OpenAI API from langchain later
from servicefoundry.langchain import TrueFoundryChat

from langchain.schema import Document
from langchain.schema.vectorstore import VectorStore as LangChainVectorStore, VectorStoreRetriever as LangChainVectorStoreRetriever

from backend.modules.metadata_store import get_metadata_store_client
from backend.modules.vector_db import get_vector_db_client
from backend.modules.embedder import get_embedder


# Custom router
RETRIEVER_ROUTER = APIRouter(
    prefix="/retriever",
)

def retriever_post(retriever_name):
    def decorator(func, **kwargs):
        url = '/'+retriever_name +'/'+func.__name__.replace("_","-") 
        RETRIEVER_ROUTER.post(url, **kwargs)(func)
        return func
    return decorator


class QueryInput(BaseModel):

    collection_name: str = Field(
        default=None,
        title="Collection name on which to search",
    )

    query: str = Field(title="Query using which the similar documents will be searched", max_length=1000)

    retrieval_chain_name: Optional[Literal["RetrievalQA", "CustomRetrievalQA"]] = Field(
        default="RetrievalQA",
        title="Name of the retrieval chain to use for retrieving documents",
    )

    retriever_config: Optional[RetrieverConfig] = Field(
        title="Retriever configuration",
    )

    model_configuration: Optional[LLMConfig]

    system_prompt: Optional[str] = Field(
        default="""Your task is to craft the most helpful, highly informative, accurate and comprehensive answers possible, 
    ensuring they are easy to understand and implement. Use the context information provided as a reference to form accurate responses 
    that incorporate as much relevant detail as possible. Strive to make each answer clear and precise to enhance user comprehension and 
    assist in solving their problems effectively.\n\nEmploy the provided context information meticulously to craft precise answers, 
    ensuring they incorporate all pertinent details. Structure your responses for ease of reading and relevance by providing as much as 
    information regarding it. Make sure the answers are well detailed and provide proper references. Align your answers with the context given and maintain transparency 
    by indicating any uncertainty or lack of knowledge regarding the correct answer to avoid providing incorrect information.""",
        title="System prompt to use for generating answer to the question",
    )
    prompt_template: Optional[str] = Field(
        default="""Here is the context information:\n\n'''\n{context}\n'''\n\nQuestion: {question}\nAnswer:""",
        title="Prompt Template to use for generating answer to the question using the context",
    )


class LangchainQueryEngine:
    """Base Query Engine class, this class lets you write your own retriver. All it's methods can be inherited and overridden 
    for custom use. 

    This class follows the following steps to write your own query engine:
        1. Get your collection by giving the collection name
        2. Get the corresponding vector store client and vector store
        3. Get the necessary embeddings
        4. Define an LLM to format the query and retrival
        5. Define retriver logic
        6. Define query, this is a compulsory method, with compulsory collection name argument, either you can write your custom 
            logic here or use the above helper functions to stitch together your query engine components.
    """

    def _get_vector_store_for_collection(self, collection_name: str) -> LangChainVectorStore:
        """Function to get langchain vector store"""

        # get the vector store client from the collection name
        vector_store_client = get_vector_db_client(
            config=settings.VECTOR_DB_CONFIG, collection_name=collection_name
        )

        # get collection
        metadata_store_client = get_metadata_store_client(config=settings.METADATA_STORE_CONFIG)
        collection = metadata_store_client.get_collection_by_name(collection_name)

        # Get the embeddings from the collections embedding config
        embedding = get_embedder(collection.embedder_config)

        # Get vector store for the corresponding embedding
        vector_store = vector_store_client.get_vector_store(embedding)

        return vector_store
    

    def _get_llm(self, model_config: LLMConfig, system_prompt: str) -> LangChainSimpleChatModel:
        """Logic for using a custom llm if any"""
        # TODO: Replace with OpenAI client
        llm = TrueFoundryChat(
            model=model_config.name,
            model_parameters=model_config.parameters,
            system_prompt=system_prompt,
        )
        return llm

    def _get_retriever(self, collection_name: str, retriever_config: RetrieverConfig) -> LangChainVectorStore:
        """Logic for retriever to get relavant documents. 
        It gets the vector store from collection name and passes it to user defined retriver"""
        # get vector store
        vector_store = self._get_vector_store_for_collection(collection_name)

        # initialize the document retriver
        retriever = LangChainVectorStoreRetriever(
            vectorstore=vector_store,
            search_type=retriever_config.get_search_type,
            search_kwargs=retriever_config.get_search_kwargs
        )
        return retriever


class BaseRAGTool(ABC):

    retriever_name: str = ''    
    query_object: Optional[LangchainQueryEngine] = None
        
    @staticmethod
    @abstractmethod
    def query(self, query: QueryInput) -> dict[str, Any]:
        """Logic for getting the RAG output. It gets the retiever and fetches relavant documents.
        Finally answers the query based on fetched context. User can also write their own helper methods if required."""
        raise NotImplementedError()










