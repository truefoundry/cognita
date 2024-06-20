import asyncio
import json

import async_timeout
from fastapi import Body, HTTPException
from fastapi.responses import StreamingResponse
from langchain.prompts import PromptTemplate
from langchain.retrievers import ContextualCompressionRetriever, MultiQueryRetriever
from langchain.schema.vectorstore import VectorStoreRetriever
from langchain_community.chat_models.ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai.chat_models import ChatOpenAI
from truefoundry.langchain import TrueFoundryChat

from backend.logger import logger
from backend.modules.metadata_store.client import get_client
from backend.modules.metadata_store.truefoundry import TrueFoundry
from backend.modules.model_gateway.model_gateway import model_gateway
from backend.modules.query_controllers.example.payload import (
    QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_MMR_PAYLOAD,
    QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD,
    QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE_PAYLOAD,
    QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_PAYLOAD,
    QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_MMR_PAYLOAD,
    QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_SIMILARITY_WITH_SCORE_PAYLOAD,
    QUERY_WITH_MULTI_QUERY_RETRIEVER_MMR_PAYLOAD,
    QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD,
    QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE_PAYLOAD,
    QUERY_WITH_VECTOR_STORE_RETRIEVER_MMR_PAYLOAD,
    QUERY_WITH_VECTOR_STORE_RETRIEVER_PAYLOAD,
    QUERY_WITH_VECTOR_STORE_RETRIEVER_SIMILARITY_SCORE_PAYLOAD,
)
from backend.modules.query_controllers.example.types import (
    GENERATION_TIMEOUT_SEC,
    ExampleQueryInput,
)
from backend.modules.rerankers.reranker_svc import InfinityRerankerSvc
from backend.modules.vector_db.client import VECTOR_STORE_CLIENT
from backend.server.decorators import post, query_controller
from backend.settings import settings
from backend.types import Collection, ModelConfig

EXAMPLES = {
    "vector-store-similarity": QUERY_WITH_VECTOR_STORE_RETRIEVER_PAYLOAD,
}

if settings.RERANKER_SVC_URL:
    EXAMPLES.update(
        {
            "contexual-compression-similarity": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_PAYLOAD,
        }
    )

    EXAMPLES.update(
        {
            "contexual-compression-similarity-threshold": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_SIMILARITY_WITH_SCORE_PAYLOAD,
        }
    )

    EXAMPLES.update(
        {
            "contexual-compression-multi-query-similarity": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD,
        }
    )

    EXAMPLES.update(
        {
            "contexual-compression-multi-query-mmr": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_MMR_PAYLOAD,
        }
    )


@query_controller("/basic-rag")
class BasicRAGQueryController:
    def _get_prompt_template(self, input_variables, template):
        """
        Get the prompt template
        """
        return PromptTemplate(input_variables=input_variables, template=template)

    def _format_docs(self, docs):
        final_list = list()
        for doc in docs:
            doc.metadata.pop("image_b64", None)
            final_list.append(
                {"page_content": doc.page_content, "metadata": doc.metadata}
            )
        return "\n\n".join([f"{doc['page_content']}" for doc in final_list])

    def _format_docs_for_stream(self, docs):
        metadata_list = []
        for doc in docs:
            doc.metadata.pop("image_b64", None)
            metadata_list.append(
                {"page_content": doc.page_content, "metadata": doc.metadata}
            )

    def _get_llm(self, model_configuration: ModelConfig, stream=False):
        """
        Get the LLM
        """
        return model_gateway.get_llm_from_model_config(model_configuration, stream)

    async def _get_vector_store(self, collection_name: str):
        """
        Get the vector store for the collection
        """
        client = await get_client()
        if isinstance(client, TrueFoundry):
            loop = asyncio.get_event_loop()
            collection = await loop.run_in_executor(
                None, client.get_collection_by_name, collection_name
            )
        else:
            collection = await client.get_collection_by_name(collection_name)

        if collection is None:
            raise HTTPException(status_code=404, detail="Collection not found")

        if not isinstance(collection, Collection):
            collection = Collection(**collection.dict())

        return VECTOR_STORE_CLIENT.get_vector_store(
            collection_name=collection.name,
            embeddings=model_gateway.get_embedder_from_model_config(
                model_name=collection.embedder_config.model_config.name
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
            if settings.RERANKER_SVC_URL:
                retriever = self._get_vector_store_retriever(
                    vector_store, retriever_config
                )
                logger.info("Using MxBaiRerankerSmall th' service...")
                compressor = InfinityRerankerSvc(
                    top_k=retriever_config.top_k,
                    model=retriever_config.compressor_model_name,
                )

                compression_retriever = ContextualCompressionRetriever(
                    base_compressor=compressor, base_retriever=retriever
                )

                return compression_retriever
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Reranker service is not available",
                )
        except Exception as e:
            logger.error(f"Error in getting contextual compression retriever: {e}")
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
        elif retriever_type == "contexual-compression":
            base_retriever = self._get_contextual_compression_retriever(
                vector_store, retriever_config
            )

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

        elif retriever_name == "contexual-compression":
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

        elif retriever_name == "contexual-compression-multi-query":
            logger.debug(
                f"Using MultiQueryRetriever with {retriever_config.search_type} search and retriever type as contexual-compression"
            )
            retriever = self._get_multi_query_retriever(
                vector_store, retriever_config, retriever_type="contexual-compression"
            )

        else:
            raise HTTPException(status_code=404, detail="Retriever not found")

        return retriever

    async def _stream_answer(self, rag_chain, query):
        async with async_timeout.timeout(GENERATION_TIMEOUT_SEC):
            try:
                async for chunk in rag_chain.astream(query):
                    if "question " in chunk:
                        # print("Question: ", chunk['question'])
                        yield json.dumps({"question": chunk["question"]})
                        await asyncio.sleep(0.1)
                    elif "context" in chunk:
                        # print("Context: ", self._format_docs_for_stream(chunk['context']))
                        yield json.dumps(
                            {"docs": self._format_docs_for_stream(chunk["context"])}
                        )
                        await asyncio.sleep(0.1)
                    elif "answer" in chunk:
                        # print("Answer: ", chunk['answer'])
                        yield json.dumps({"answer": chunk["answer"]})
                        await asyncio.sleep(0.1)

                yield json.dumps({"end": "<END>"})
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="Stream timed out")

    @post("/answer")
    async def answer(
        self,
        request: ExampleQueryInput = Body(
            openapi_examples=EXAMPLES,
        ),
    ):
        """
        Sample answer method to answer the question using the context from the collection
        """
        try:
            # Get the vector store
            vector_store = await self._get_vector_store(request.collection_name)

            # Create the QA prompt templates
            QA_PROMPT = self._get_prompt_template(
                input_variables=["context", "question"],
                template=request.prompt_template,
            )

            # Get the LLM
            llm = self._get_llm(request.model_configuration, request.stream)

            # get retriever
            retriever = await self._get_retriever(
                vector_store=vector_store,
                retriever_name=request.retriever_name,
                retriever_config=request.retriever_config,
            )

            # Using LCEL
            rag_chain_from_docs = (
                RunnablePassthrough.assign(
                    context=(lambda x: self._format_docs(x["context"]))
                )
                | QA_PROMPT
                | llm
                | StrOutputParser()
            )

            rag_chain_with_source = RunnableParallel(
                {"context": retriever, "question": RunnablePassthrough()}
            ).assign(answer=rag_chain_from_docs)

            if request.stream:
                return StreamingResponse(
                    self._stream_answer(rag_chain_with_source, request.query),
                    media_type="text/event-stream",
                )

            else:
                outputs = await rag_chain_with_source.ainvoke(request.query)

                # Intermediate testing
                # Just the retriever
                # setup_and_retrieval = RunnableParallel({"context": retriever, "question": RunnablePassthrough()})
                # outputs = await setup_and_retrieval.ainvoke(request.query)
                # print(outputs)

                # Retriver and QA
                # outputs = await (setup_and_retrieval | QA_PROMPT).ainvoke(request.query)
                # print(outputs)

                # Retriver, QA and LLM
                # outputs = await (setup_and_retrieval | QA_PROMPT | llm).ainvoke(request.query)
                # print(outputs)

                return {
                    "answer": outputs["answer"],
                    "docs": outputs["context"] if outputs["context"] else [],
                }

        except HTTPException as exp:
            raise exp
        except Exception as exp:
            logger.exception(exp)
            raise HTTPException(status_code=500, detail=str(exp))


#######
# Streaming Client

# import httpx
# from httpx import Timeout

# from backend.modules.query_controllers.example.types import ExampleQueryInput

# payload = {
#   "collection_name": "pstest",
#   "query": "What are the features of Diners club black metal edition?",
#   "model_configuration": {
#     "name": "openai-devtest/gpt-3-5-turbo",
#     "parameters": {
#       "temperature": 0.1
#     },
#     "provider": "truefoundry"
#   },
#   "prompt_template": "Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}",
#   "retriever_name": "vectorstore",
#   "retriever_config": {
#     "search_type": "similarity",
#     "search_kwargs": {
#       "k": 20
#     },
#     "filter": {}
#   },
#   "stream": True
# }

# data = ExampleQueryInput(**payload).dict()
# ENDPOINT_URL = 'http://localhost:8000/retrievers/example-app/answer'


# with httpx.stream('POST', ENDPOINT_URL, json=data, timeout=Timeout(5.0*60)) as r:
#     for chunk in r.iter_text():
#         print(chunk)
#######
