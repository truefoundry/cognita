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
from backend.modules.embedder.embedder import get_embedder
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.modules.query_controllers.summary.payload import (
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
from backend.modules.query_controllers.summary.types import (
    GENERATION_TIMEOUT_SEC,
    ExampleQueryInput,
)
from backend.modules.reranker import MxBaiReranker
from backend.modules.vector_db.client import VECTOR_STORE_CLIENT
from backend.server.decorators import post, query_controller
from backend.settings import settings

EXAMPLES = {
    "vector-store-similarity": QUERY_WITH_VECTOR_STORE_RETRIEVER_PAYLOAD,
    "vector-store-similarity-threshold": QUERY_WITH_VECTOR_STORE_RETRIEVER_SIMILARITY_SCORE_PAYLOAD,
    "contexual-compression-multi-query-similarity": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD,
    "contextual-compression-multi-query-similarity-threshold": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE_PAYLOAD,
    # Keeping these for future use:
    # "contexual-compression-similarity-threshold": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_SIMILARITY_WITH_SCORE_PAYLOAD,
    # "vector-store-mmr": QUERY_WITH_VECTOR_STORE_RETRIEVER_MMR_PAYLOAD,
    # "contexual-compression-similarity": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_PAYLOAD,
    # "multi-query-mmr": QUERY_WITH_MULTI_QUERY_RETRIEVER_MMR_PAYLOAD,
}

# if settings.LOCAL:
#     EXAMPLES.update(
#         {
#             "contexual-compression-similarity": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_PAYLOAD,
#             "contexual-compression-multi-query-similarity": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD,
#             "multi-query-similarity": QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD,
#             "multi-query-similarity-threshold": QUERY_WITH_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE_PAYLOAD,
#         }
#     )


@query_controller("/summary-report")
class SummaryQueryController:
    def _get_prompt_template(self, input_variables, template):
        """
        Get the prompt template
        """
        return PromptTemplate(input_variables=input_variables, template=template)

    def _format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def _format_docs_for_stream(self, docs):
        return [
            {"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs
        ]

    def _get_llm(self, model_configuration, stream=False):
        """
        Get the LLM
        """
        system = "You are a helpful assistant."
        if model_configuration.provider == "openai":
            logger.debug(f"Using OpenAI model {model_configuration.name}")
            llm = ChatOpenAI(
                model=model_configuration.name,
                temperature=model_configuration.parameters.get("temperature", 0.1),
                streaming=stream,
            )
        elif model_configuration.provider == "ollama":
            logger.debug(f"Using Ollama model {model_configuration.name}")
            llm = ChatOllama(
                base_url=settings.OLLAMA_URL,
                model=(
                    model_configuration.name.split("/")[1]
                    if "/" in model_configuration.name
                    else model_configuration.name
                ),
                temperature=model_configuration.parameters.get("temperature", 0.1),
                system=system,
            )
        elif model_configuration.provider == "truefoundry":
            logger.debug(f"Using TrueFoundry model {model_configuration.name}")
            llm = TrueFoundryChat(
                model=model_configuration.name,
                model_parameters=model_configuration.parameters,
                system_prompt=system,
            )
        else:
            logger.debug(f"Using TrueFoundry model {model_configuration.name}")
            llm = TrueFoundryChat(
                model=model_configuration.name,
                model_parameters=model_configuration.parameters,
                system_prompt=system,
            )
        return llm

    async def _get_vector_store(self, collection_name: str):
        """
        Get the vector store for the collection
        """
        collection = METADATA_STORE_CLIENT.get_collection_by_name(collection_name)

        if collection is None:
            raise HTTPException(status_code=404, detail="Collection not found")

        return VECTOR_STORE_CLIENT.get_vector_store(
            collection_name=collection.name,
            embeddings=get_embedder(collection.embedder_config),
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
        # Using mixbread-ai Reranker
        if retriever_config.compressor_model_provider == "mixbread-ai":
            retriever = self._get_vector_store_retriever(vector_store, retriever_config)

            compressor = MxBaiReranker(
                model=retriever_config.compressor_model_name,
                top_k=retriever_config.top_k,
            )

            compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor, base_retriever=retriever
            )

            return compression_retriever
        # Can add other rerankers too!
        else:
            raise HTTPException(
                status_code=404, detail="Compressor model provider not found"
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

                SUMMARY_PROMPT = "You are an AI assistant specialising in summarizing documents finance, insurance and private equity. Given a list of question and answers, your task is to provide a detailed one pager summary report. Summary: {context}"

                # Get the summary
                summary_rag_chain = (
                    RunnablePassthrough.assign(
                        context=lambda x: x["answer"],
                    )
                    | PromptTemplate(
                        input_variables=["context"],
                        template=SUMMARY_PROMPT,
                    )
                    | llm
                    | StrOutputParser()
                )

                summary = await summary_rag_chain.ainvoke(outputs)

                answer = (
                    outputs["answer"] + "\n\n**Summary:**\n" + summary
                    if ("Summary" or "summary") not in summary
                    else outputs["answer"] + "\n\n\n" + summary
                )
                return {
                    "answer": answer,
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

# from backend.modules.query_controllers.summary.types import ExampleQueryInput

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
