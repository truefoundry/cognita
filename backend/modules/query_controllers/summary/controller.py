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
    "contexual-compression-similarity": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_PAYLOAD,
    "contexual-compression-similarity-threshold": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_SEARCH_TYPE_SIMILARITY_WITH_SCORE_PAYLOAD,
    "contexual-compression-multi-query-similarity": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD,
    "contextual-compression-multi-query-similarity-threshold": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_SCORE_PAYLOAD,
}


@query_controller("/intelligent-summary")
class IntelligentSummaryQueryController:
    def _get_prompt_template(self, input_variables, template):
        """
        Get the prompt template
        """
        return PromptTemplate(input_variables=input_variables, template=template)

    def _format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def _format_docs_for_stream(self, docs):
        formatted_docs = list()
        # docs is a list of list of document objects
        for doc in docs:
            for pages in doc:
                pages.metadata.pop("image_b64", None)
                formatted_docs.append(
                    {"page_content": pages.page_content, "metadata": pages.metadata}
                )
        return formatted_docs

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

    async def _stream_answer_queries(self, rag_chain, queries, summary_rag_chain):
        async with async_timeout.timeout(GENERATION_TIMEOUT_SEC):
            try:
                final_docs = list()
                all_answers = {"answer": ""}
                for query in queries:
                    yield json.dumps(
                        {"answer": "\n\n**Q:** " + query + "\n\n**Ans:** "}
                    )
                    await asyncio.sleep(0.1)
                    async for chunk in rag_chain.astream(query):
                        if "context" in chunk:
                            final_docs.append(chunk["context"])
                            await asyncio.sleep(0.1)
                        elif "answer" in chunk:
                            yield json.dumps({"answer": chunk["answer"]})
                            all_answers["answer"] += chunk["answer"] + " "
                            await asyncio.sleep(0.1)
                    yield json.dumps({"answer": "\n\n"})
                    await asyncio.sleep(0.1)

                # summarize all answers
                if len(queries) > 1:
                    yield json.dumps({"answer": "**Summary:** "})
                    await asyncio.sleep(0.1)
                    async for chunk in summary_rag_chain.astream(all_answers):
                        yield json.dumps({"answer": chunk})
                        await asyncio.sleep(0.1)

                yield json.dumps({"docs": self._format_docs_for_stream(final_docs)})
                await asyncio.sleep(0.1)
                yield json.dumps({"end": "<END>"})
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="Stream timed out")
            except Exception as e:
                print(f"Stream Error: {e}")

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

        if not request.stream:
            return {
                "answer": "This controller requires streaming to be enables please enable streaming!"
            }

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

        # split query into individual sentences based on '.', '?', or '\n'
        query = request.query.strip()
        query = query.replace("\n", ".")
        query = query.replace("?", ".")
        query = query.split(".")
        queries = [q.strip() for q in query if q.strip() != "" and len(q.strip()) > 5]

        logger.debug(f"Total queries: {len(queries)}")
        SUMMARY_PROMPT = "Give a one pager summary of the given text: {context}"
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

        if request.stream:
            # return streaming response over queries
            return StreamingResponse(
                self._stream_answer_queries(
                    rag_chain_with_source, queries, summary_rag_chain
                ),
                media_type="text/event-stream",
            )
