from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import List
from fastapi import APIRouter

from backend.settings import settings
from backend.modules.metadata_store import get_metadata_store_client
from backend.modules.vector_db import get_vector_db_client
from backend.utils.base import LLMConfig





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


class TFQueryInput(BaseModel):

    collection_name: str = Field(
        default=None,
        title="Collection name on which to search",
    )

    query: str = Field(title="Query using which the similar documents will be searched", max_length=1000)


class TFQueryEngine(ABC):
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

    retriever_name: str = ''

    @classmethod
    def _get_collection(self, collection_name: str):
        metadata_store_client = get_metadata_store_client(config=settings.METADATA_STORE_CONFIG)
        collection = metadata_store_client.get_collection_by_name(collection_name)
        return collection
    
    @classmethod
    def _get_vector_store_client(self, collection_name: str):
        vector_db_client = get_vector_db_client(
            config=settings.VECTOR_DB_CONFIG, collection_name=collection_name
        )
        return vector_db_client
    
    @abstractmethod
    def get_embeddings(self, collection_name: str):
        """Logic to get embeddings"""
    
    @abstractmethod
    def get_vector_store(self, collection_name: str):
        """Logic to get vector store"""
    
    @abstractmethod
    def get_llm(self, model_config: LLMConfig, system_prompt: str):
        """Logic for using a custom llm if any"""

    
    @abstractmethod
    def get_retriever(self):
        """Logic for retriever. It gets the vector store from collection name and passes it to user defined retriver"""

    @abstractmethod
    def query(self, query: TFQueryInput):
        """Logic for getting the RAG output. It gets the retiever and fetches document from it"""
        raise NotImplementedError()







