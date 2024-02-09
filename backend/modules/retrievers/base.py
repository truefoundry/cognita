from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import List, Optional
from fastapi import APIRouter

from backend.settings import settings
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


class TFQueryInput(BaseModel):

    collection_name: str = Field(
        default=None,
        title="Collection name on which to search",
    )

    query: str = Field(title="Query using which the similar documents will be searched", max_length=1000)


class TFQueryEngine(ABC):
    """Base Retriever Class"""

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
    def get_llm(self):
        """Logic for using a custom llm if any"""

    
    @abstractmethod
    def get_retriever(self):
        """Logic for retriever. It gets the vector store from collection name and passes it to user defined retriver"""

    @abstractmethod
    def query(self, query: TFQueryInput):
        """Logic for getting the RAG output. It gets the retiever and fetches document from it"""
        raise NotImplementedError()







