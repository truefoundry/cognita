import asyncio
import time
import uuid
from datetime import datetime
from typing import AsyncIterator, Dict, List

from fastapi import Body
from fastapi.responses import StreamingResponse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from backend.logger import logger
from backend.modules.query_controllers.base import BaseQueryController
from backend.modules.query_controllers.rag_visualization.types import (
    RAGStep,
    RAGStepStatus,
    RAGStepType,
    RAGVisualizationData,
    RAGVisualizationQueryInput,
    RAGVisualizationResponse,
    RAGVisualizationStreamChunk,
    RetrievedDocument,
)
from backend.modules.query_controllers.types import Document
from backend.server.decorators import post, query_controller


@query_controller("/rag-visualization")
class RAGVisualizationController(BaseQueryController):
    """
    Controller for RAG visualization that tracks and visualizes each step of the RAG pipeline
    """

    def __init__(self):
        super().__init__()
        self.current_visualization_data: RAGVisualizationData = None

    def _create_step(
        self,
        step_type: RAGStepType,
        step_name: str,
        input_data: Dict = None,
        metadata: Dict = None,
    ) -> RAGStep:
        """Create a new RAG step"""
        return RAGStep(
            step_id=str(uuid.uuid4()),
            step_type=step_type,
            step_name=step_name,
            input_data=input_data or {},
            metadata=metadata or {},
        )

    def _start_step(self, step: RAGStep) -> RAGStep:
        """Mark a step as started"""
        step.status = RAGStepStatus.IN_PROGRESS
        step.start_time = datetime.now()
        logger.info(f"Starting RAG step: {step.step_name}")
        return step

    def _complete_step(self, step: RAGStep, output_data: Dict = None) -> RAGStep:
        """Mark a step as completed"""
        step.status = RAGStepStatus.COMPLETED
        step.end_time = datetime.now()
        if step.start_time:
            step.duration_ms = int(
                (step.end_time - step.start_time).total_seconds() * 1000
            )
        step.output_data = output_data or {}
        logger.info(f"Completed RAG step: {step.step_name} in {step.duration_ms}ms")
        return step

    def _fail_step(self, step: RAGStep, error_message: str) -> RAGStep:
        """Mark a step as failed"""
        step.status = RAGStepStatus.FAILED
        step.end_time = datetime.now()
        if step.start_time:
            step.duration_ms = int(
                (step.end_time - step.start_time).total_seconds() * 1000
            )
        step.error_message = error_message
        logger.error(f"Failed RAG step: {step.step_name} - {error_message}")
        return step

    async def _visualized_retrieval(
        self, query: str, retriever, visualization_data: RAGVisualizationData
    ):
        """Perform document retrieval with visualization tracking"""
        # Vector search step
        search_step = self._create_step(
            RAGStepType.VECTOR_SEARCH,
            "Vector Similarity Search",
            input_data={"query": query},
        )
        self._start_step(search_step)
        visualization_data.steps.append(search_step)

        try:
            # Perform the actual retrieval
            start_time = time.time()
            docs = await retriever.ainvoke(query)
            end_time = time.time()

            # Create retrieved documents with metadata
            retrieved_docs = []
            for i, doc in enumerate(docs):
                retrieved_doc = RetrievedDocument(
                    document=doc,
                    similarity_score=doc.metadata.get("relevance_score"),
                    retrieval_method="vector_similarity",
                    chunk_index=i,
                )
                retrieved_docs.append(retrieved_doc)

            visualization_data.retrieved_documents = retrieved_docs

            self._complete_step(
                search_step,
                output_data={
                    "num_documents": len(docs),
                    "search_time_ms": int((end_time - start_time) * 1000),
                    "documents_preview": [
                        {
                            "content_preview": doc.page_content[:100] + "...",
                            "metadata": doc.metadata,
                        }
                        for doc in docs[:3]
                    ],
                },
            )

            return docs

        except Exception as e:
            self._fail_step(search_step, str(e))
            raise

    async def _visualized_llm_generation(
        self, prompt, llm, visualization_data: RAGVisualizationData
    ):
        """Perform LLM generation with visualization tracking"""
        generation_step = self._create_step(
            RAGStepType.LLM_GENERATION,
            "LLM Answer Generation",
            input_data={"prompt_length": len(str(prompt))},
        )
        self._start_step(generation_step)
        visualization_data.steps.append(generation_step)

        try:
            start_time = time.time()
            response = await llm.ainvoke(prompt)
            end_time = time.time()

            self._complete_step(
                generation_step,
                output_data={
                    "response_length": len(response),
                    "generation_time_ms": int((end_time - start_time) * 1000),
                    "model_name": getattr(llm, "model_name", "unknown"),
                },
            )

            return response

        except Exception as e:
            self._fail_step(generation_step, str(e))
            raise

    async def _stream_visualization_answer(
        self, rag_chain, query: str, visualization_data: RAGVisualizationData
    ) -> AsyncIterator[RAGVisualizationStreamChunk]:
        """Stream the answer with visualization data"""
        try:
            # Send initial visualization data
            yield RAGVisualizationStreamChunk(
                type="visualization_init",
                content=visualization_data.model_dump(),
            )

            # Process the RAG chain
            async for chunk in rag_chain.astream(query):
                if "context" in chunk:
                    # Update retrieved documents
                    retrieved_docs = []
                    for i, doc in enumerate(chunk["context"]):
                        retrieved_doc = RetrievedDocument(
                            document=doc,
                            similarity_score=doc.metadata.get("relevance_score"),
                            retrieval_method="vector_similarity",
                            chunk_index=i,
                        )
                        retrieved_docs.append(retrieved_doc)

                    visualization_data.retrieved_documents = retrieved_docs

                    yield RAGVisualizationStreamChunk(
                        type="documents",
                        content=retrieved_docs,
                    )

                elif "answer" in chunk:
                    yield RAGVisualizationStreamChunk(
                        type="answer",
                        content=chunk["answer"],
                    )

            # Send final visualization data
            yield RAGVisualizationStreamChunk(
                type="visualization_complete",
                content=visualization_data.model_dump(),
            )

        except Exception as e:
            logger.exception(f"Error in streaming visualization: {e}")
            yield RAGVisualizationStreamChunk(
                type="error",
                content={"error": str(e)},
            )

    @post("/answer")
    async def answer(
        self,
        request: RAGVisualizationQueryInput = Body(),
    ):
        """
        Answer method with complete RAG pipeline visualization
        """
        query_start_time = datetime.now()
        query_id = str(uuid.uuid4())

        # Initialize visualization data
        visualization_data = RAGVisualizationData(
            query_id=query_id,
            original_query=request.query,
            collection_name=request.collection_name,
            model_configuration=request.model_configuration.model_dump(),
            retriever_config=request.retriever_config.model_dump(),
        )

        try:
            # Step 1: Query Processing
            query_step = self._create_step(
                RAGStepType.QUERY_PROCESSING,
                "Query Processing",
                input_data={"original_query": request.query},
            )
            self._start_step(query_step)
            visualization_data.steps.append(query_step)

            # Process query (could include query expansion, cleaning, etc.)
            processed_query = request.query  # For now, just use original
            visualization_data.processed_query = processed_query

            self._complete_step(
                query_step,
                output_data={"processed_query": processed_query},
            )

            # Step 2: Vector Store Setup
            vector_store_step = self._create_step(
                RAGStepType.EMBEDDING_GENERATION,
                "Vector Store Initialization",
                input_data={"collection_name": request.collection_name},
            )
            self._start_step(vector_store_step)
            visualization_data.steps.append(vector_store_step)

            vector_store = await self._get_vector_store(request.collection_name)

            self._complete_step(
                vector_store_step,
                output_data={"vector_store_type": type(vector_store).__name__},
            )

            # Step 3: Retriever Setup
            retriever_step = self._create_step(
                RAGStepType.DOCUMENT_RETRIEVAL,
                "Retriever Configuration",
                input_data={"retriever_name": request.retriever_name},
            )
            self._start_step(retriever_step)
            visualization_data.steps.append(retriever_step)

            retriever = await self._get_retriever(
                vector_store=vector_store,
                retriever_name=request.retriever_name,
                retriever_config=request.retriever_config,
            )

            self._complete_step(
                retriever_step,
                output_data={"retriever_type": type(retriever).__name__},
            )

            # Step 4: Prompt Template Setup
            prompt_step = self._create_step(
                RAGStepType.PROMPT_CONSTRUCTION,
                "Prompt Template Construction",
                input_data={"template": request.prompt_template},
            )
            self._start_step(prompt_step)
            visualization_data.steps.append(prompt_step)

            QA_PROMPT = self._get_prompt_template(
                input_variables=["context", "question"],
                template=request.prompt_template,
            )

            self._complete_step(
                prompt_step,
                output_data={"prompt_variables": ["context", "question"]},
            )

            # Step 5: LLM Setup
            llm_setup_step = self._create_step(
                RAGStepType.LLM_GENERATION,
                "LLM Configuration",
                input_data={"model_name": request.model_configuration.name},
            )
            self._start_step(llm_setup_step)
            visualization_data.steps.append(llm_setup_step)

            llm = self._get_llm(request.model_configuration, request.stream)

            self._complete_step(
                llm_setup_step,
                output_data={
                    "model_name": request.model_configuration.name,
                    "streaming": request.stream,
                },
            )

            # Build the RAG chain with visualization
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
            )

            if request.internet_search_enabled:
                rag_chain_with_source = (
                    rag_chain_with_source | self._internet_search
                ).assign(answer=rag_chain_from_docs)
            else:
                rag_chain_with_source = rag_chain_with_source.assign(
                    answer=rag_chain_from_docs
                )

            # Execute the chain
            if request.stream:
                return StreamingResponse(
                    self._sse_wrap(
                        self._stream_visualization_answer(
                            rag_chain_with_source, request.query, visualization_data
                        )
                    ),
                    media_type="text/event-stream",
                )
            else:
                # Non-streaming execution with detailed tracking
                execution_step = self._create_step(
                    RAGStepType.RESPONSE_FORMATTING,
                    "RAG Chain Execution",
                    input_data={"query": request.query},
                )
                self._start_step(execution_step)
                visualization_data.steps.append(execution_step)

                outputs = await rag_chain_with_source.ainvoke(request.query)

                # Process retrieved documents
                if "context" in outputs:
                    retrieved_docs = []
                    for i, doc in enumerate(outputs["context"]):
                        retrieved_doc = RetrievedDocument(
                            document=doc,
                            similarity_score=doc.metadata.get("relevance_score"),
                            retrieval_method="vector_similarity",
                            chunk_index=i,
                        )
                        retrieved_docs.append(retrieved_doc)
                    visualization_data.retrieved_documents = retrieved_docs

                visualization_data.final_answer = outputs["answer"]

                # Calculate total duration
                query_end_time = datetime.now()
                visualization_data.total_duration_ms = int(
                    (query_end_time - query_start_time).total_seconds() * 1000
                )

                self._complete_step(
                    execution_step,
                    output_data={
                        "answer_length": len(outputs["answer"]),
                        "num_retrieved_docs": len(outputs.get("context", [])),
                    },
                )

                # Add performance metrics
                visualization_data.metrics = {
                    "total_steps": len(visualization_data.steps),
                    "successful_steps": len(
                        [
                            s
                            for s in visualization_data.steps
                            if s.status == RAGStepStatus.COMPLETED
                        ]
                    ),
                    "failed_steps": len(
                        [
                            s
                            for s in visualization_data.steps
                            if s.status == RAGStepStatus.FAILED
                        ]
                    ),
                    "average_step_duration_ms": (
                        sum(
                            s.duration_ms
                            for s in visualization_data.steps
                            if s.duration_ms
                        )
                        / len(visualization_data.steps)
                        if visualization_data.steps
                        else 0
                    ),
                }

                return RAGVisualizationResponse(
                    answer=outputs["answer"],
                    visualization_data=visualization_data,
                    docs=self._enrich_context_for_non_stream_response(outputs),
                )

        except Exception as e:
            logger.exception(f"Error in RAG visualization: {e}")
            # Mark any in-progress steps as failed
            for step in visualization_data.steps:
                if step.status == RAGStepStatus.IN_PROGRESS:
                    self._fail_step(step, str(e))

            raise

    async def _sse_wrap_visualization(self, gen):
        """SSE wrapper for visualization streaming"""
        async for data in gen:
            yield "event: data\n"
            yield f"data: {data.model_dump_json()}\n\n"
        yield "event: end\n"
