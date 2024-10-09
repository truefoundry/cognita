import asyncio
import json
from typing import AsyncIterator

import async_timeout
import requests
from fastapi import HTTPException
from langchain.prompts import PromptTemplate
from langchain.retrievers import ContextualCompressionRetriever, MultiQueryRetriever
from langchain.schema.vectorstore import VectorStoreRetriever
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel

from backend.logger import logger
from backend.modules.metadata_store.client import get_client
from backend.modules.model_gateway.model_gateway import model_gateway
from backend.modules.query_controllers.types import *
from backend.modules.vector_db.client import VECTOR_STORE_CLIENT
from backend.settings import settings
from backend.types import Collection, ModelConfig


class BaseQueryController:
    required_metadata = [
        "_data_point_fqn",
        "filename",
        "_id",
        "collection_name",
        "page_number",
        "pg_no",
        "source",
        "relevance_score",
    ]

    def _get_prompt_template(self, input_variables, template):
        """
        Get the prompt template
        """
        return PromptTemplate(input_variables=input_variables, template=template)

    def _format_docs(self, docs):
        formatted_docs = list()
        for doc in docs:
            metadata = {
                key: doc.metadata[key]
                for key in self.required_metadata
                if key in doc.metadata
            }
            formatted_docs.append(
                {"page_content": doc.page_content, "metadata": metadata}
            )
        return "\n\n".join([f"{doc['page_content']}" for doc in formatted_docs])

    def _get_llm(self, model_configuration: ModelConfig, stream=False) -> BaseChatModel:
        """
        Get the LLM
        """
        return model_gateway.get_llm_from_model_config(model_configuration, stream)

    async def _get_vector_store(self, collection_name: str):
        """
        Get the vector store for the collection
        """
        client = await get_client()
        collection = await client.aget_collection_by_name(collection_name)
        if collection is None:
            raise HTTPException(status_code=404, detail="Collection not found")

        if not isinstance(collection, Collection):
            collection = Collection(**collection.model_dump())

        return VECTOR_STORE_CLIENT.get_vector_store(
            collection_name=collection.name,
            embeddings=model_gateway.get_embedder_from_model_config(
                model_name=collection.embedder_config.name
            ),
        )

    def _get_vector_store_retriever(self, vector_store, retriever_config):
        """
        Get the vector store retriever
        """
        return VectorStoreRetriever(
            vectorstore=vector_store,
            search_type=retriever_config.search_type,
            search_kwargs=retriever_config.search_kwargs,
        )

    def _get_contextual_compression_retriever(self, vector_store, retriever_config):
        """
        Get the contextual compression retriever
        """
        try:
            retriever = self._get_vector_store_retriever(vector_store, retriever_config)
            logger.info("Using MxBaiRerankerSmall th' service...")

            compressor = model_gateway.get_reranker_from_model_config(
                model_name=retriever_config.compressor_model_name,
                top_k=retriever_config.top_k,
            )
            compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor, base_retriever=retriever
            )

            return compression_retriever
        except Exception as e:
            logger.exception(f"Error in getting contextual compression retriever: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error in getting contextual compression retriever",
            )

    def _get_multi_query_retriever(
        self, vector_store, retriever_config, retriever_type="vectorstore"
    ):
        """
        Get the multi query retriever
        """
        if retriever_type == "vectorstore":
            base_retriever = self._get_vector_store_retriever(
                vector_store, retriever_config
            )
        elif retriever_type == "contextual-compression":
            base_retriever = self._get_contextual_compression_retriever(
                vector_store, retriever_config
            )
        else:
            raise ValueError(f"Unknown retriever type `{retriever_type}`")

        return MultiQueryRetriever.from_llm(
            retriever=base_retriever,
            llm=self._get_llm(retriever_config.retriever_llm_configuration),
        )

    async def _get_retriever(self, vector_store, retriever_name, retriever_config):
        """
        Get the retriever
        """
        if retriever_name == "vectorstore":
            logger.debug(
                f"Using VectorStoreRetriever with {retriever_config.search_type} search"
            )
            retriever = self._get_vector_store_retriever(vector_store, retriever_config)

        elif retriever_name == "contextual-compression":
            logger.debug(
                f"Using ContextualCompressionRetriever with {retriever_config.search_type} search"
            )
            retriever = self._get_contextual_compression_retriever(
                vector_store, retriever_config
            )

        elif retriever_name == "multi-query":
            logger.debug(
                f"Using MultiQueryRetriever with {retriever_config.search_type} search"
            )
            retriever = self._get_multi_query_retriever(vector_store, retriever_config)

        elif retriever_name == "contextual-compression-multi-query":
            logger.debug(
                f"Using MultiQueryRetriever with {retriever_config.search_type} search and "
                f"retriever type as {retriever_name}"
            )
            retriever = self._get_multi_query_retriever(
                vector_store, retriever_config, retriever_type="contextual-compression"
            )

        else:
            raise HTTPException(status_code=404, detail="Retriever not found")
        return retriever

    def _cleanup_metadata(self, docs):
        formatted_docs = list()
        for doc in docs:
            metadata = {
                key: doc.metadata[key]
                for key in self.required_metadata
                if key in doc.metadata
            }
            formatted_docs.append(
                Document(page_content=doc.page_content, metadata=metadata)
            )
        return formatted_docs

    def _intent_summary_search(self, query: str):
        url = f"https://api.search.brave.com/res/v1/web/search?q={query}&summary=1"

        payload = {}
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": f"{settings.BRAVE_API_KEY}",
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        answer = response.json()

        if "summarizer" in answer.keys():
            summary_query = answer["summarizer"]["key"]
            url = f"https://api.search.brave.com/res/v1/summarizer/search?key={summary_query}"
            response = requests.request("GET", url, headers=headers, data=payload)
            answer = response.json()["summary"][0]["data"]
            return answer
        return ""

    def _internet_search(self, context):
        if settings.BRAVE_API_KEY:
            logger.info("Using Internet search...")
            data_context, question = context["context"], context["question"]
            intent_summary_results = self._intent_summary_search(question)
            # insert internet search results into context at the beginning
            data_context.insert(
                0,
                Document(
                    page_content=intent_summary_results,
                    metadata={"_data_point_fqn": "internet::Internet"},
                ),
            )
            context["context"] = data_context
        return context

    async def _sse_wrap(self, gen):
        async for data in gen:
            yield "event: data\n"
            yield f"data: {json.dumps(data.dict())}\n\n"
        yield "event: end\n"

    async def _stream_answer(self, rag_chain, query) -> AsyncIterator[BaseModel]:
        async with async_timeout.timeout(GENERATION_TIMEOUT_SEC):
            try:
                async for chunk in rag_chain.astream(query):
                    if "context" in chunk:
                        yield Docs(content=self._cleanup_metadata(chunk["context"]))
                    elif "answer" in chunk:
                        yield Answer(content=chunk["answer"])
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="Stream timed out")

    async def answer(
        self,
        request: BaseQueryInput,
    ):
        pass
