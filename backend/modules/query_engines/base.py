from fastapi import HTTPException
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models.base import BaseChatModel
from langchain.chat_models.openai import ChatOpenAI
from langchain.schema.vectorstore import VectorStore

from backend.modules.embedder import get_embedder
from backend.modules.vector_db import get_vector_db_client
from backend.settings import settings
from backend.utils.base import LLMConfig


class BaseQueryEngine:
    def _get_vector_store(self, collection_name: str) -> VectorStore:
        collection = settings.METADATA_STORE_CLIENT.get_collection_by_name(
            collection_name
        )

        if collection is None:
            raise HTTPException(status_code=404, detail="Collection not found")

        vector_db_client = get_vector_db_client(
            config=settings.VECTOR_DB_CONFIG, collection_name=collection_name
        )
        vector_store = vector_db_client.get_vector_store(
            embeddings=get_embedder(collection.embedder_config),
        )
        return vector_store

    def _get_llm(self, model_configuration: LLMConfig) -> BaseChatModel:
        llm = ChatOpenAI(
            model=model_configuration.name,
            api_key=settings.TFY_API_KEY,
            base_url=f"{settings.TFY_LLM_GATEWAY_URL}/openai",
        )
        return llm
