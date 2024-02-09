from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import List, Optional
from fastapi import APIRouter


# Custom router
RETRIEVER_ROUTER = APIRouter(
    prefix="/retriever",
)

def post(retriever_name):
    def decorator(func, **kwargs):
        url = '/'+retriever_name +'/'+func.__name__.replace("_","-") 
        RETRIEVER_ROUTER.post(url, **kwargs)(func)
        return func
    return decorator


class Output(BaseModel):
    docs: List = []

class QueryRequest(BaseModel):
    query: str = Field(title="Question to search for", max_length=1000)

class TFBaseRetriever(ABC):
    """This retriever inhertis functionalities of langchain retriever and 
        adds additional funcitonality on top of it"""

    retriever_name: str = ''



