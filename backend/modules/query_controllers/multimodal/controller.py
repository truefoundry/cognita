import asyncio

import async_timeout
from fastapi import Body, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from backend.logger import logger
from backend.modules.query_controllers.base import BaseQueryController
from backend.modules.query_controllers.multimodal.payload import (
    PROMPT,
    QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD,
    QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_PAYLOAD,
    QUERY_WITH_VECTOR_STORE_RETRIEVER_PAYLOAD,
)
from backend.modules.query_controllers.multimodal.types import MultiModalQueryInput
from backend.modules.query_controllers.types import GENERATION_TIMEOUT_SEC, Answer, Docs
from backend.server.decorators import post, query_controller

EXAMPLES = {
    "vector-store-similarity": QUERY_WITH_VECTOR_STORE_RETRIEVER_PAYLOAD,
    "contextual-compression-similarity": QUERY_WITH_CONTEXTUAL_COMPRESSION_RETRIEVER_PAYLOAD,
    "contextual-compression-multi-query-similarity": QUERY_WITH_CONTEXTUAL_COMPRESSION_MULTI_QUERY_RETRIEVER_SIMILARITY_PAYLOAD,
}


@query_controller("/multimodal-rag")
class MultiModalRAGQueryController(BaseQueryController):
    async def _stream_vlm_answer(self, llm, message_payload, docs):
        try:
            async with async_timeout.timeout(GENERATION_TIMEOUT_SEC):
                yield Docs(content=self._cleanup_metadata(docs))
                async for chunk in llm.astream(message_payload):
                    yield Answer(content=chunk.content)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Stream timed out")

    def _generate_payload_for_vlm(self, prompt: str, images_set: set):
        content = [
            {
                "type": "text",
                "text": prompt,
            }
        ]

        for b64_image in images_set:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64_image}",
                        "detail": "high",
                    },
                }
            )
        return [HumanMessage(content=content)]

    @post("/answer")
    async def answer(
        self,
        request: MultiModalQueryInput = Body(
            openapi_examples=EXAMPLES,
        ),
    ):
        """
        Sample answer method to answer the question using the context from the collection
        """
        try:
            # Get the vector store
            vector_store = await self._get_vector_store(request.collection_name)

            # get retriever
            retriever = await self._get_retriever(
                vector_store=vector_store,
                retriever_name=request.retriever_name,
                retriever_config=request.retriever_config,
            )
            llm = self._get_llm(request.model_configuration, request.stream)

            try:
                prompt = request.prompt_template.format(question=request.query)
            except Exception as e:
                logger.error(f"Error in formatting prompt: {e}")
                logger.info(f"Using default prompt")
                prompt = PROMPT.format(question=request.query)

            # Generate payload for VLM
            images_set = set()

            setup_and_retrieval = RunnableParallel(
                {"context": retriever, "question": RunnablePassthrough()}
            )
            outputs = await setup_and_retrieval.ainvoke(request.query)

            if "context" in outputs:
                docs = outputs["context"]
                for doc in docs:
                    image_b64 = doc.metadata.get("image_b64", None)
                    if image_b64 is not None:
                        images_set.add(image_b64)
                        # Remove the image_b64 from the metadata
                        doc.metadata.pop("image_b64")

            message_payload = self._generate_payload_for_vlm(
                prompt=prompt, images_set=images_set
            )

            if request.stream:
                return StreamingResponse(
                    self._sse_wrap(
                        self._stream_vlm_answer(
                            llm, message_payload, outputs["context"]
                        ),
                    ),
                    media_type="text/event-stream",
                )

            else:
                response = await llm.ainvoke(message_payload)
                return {
                    "answer": response.content,
                    "docs": outputs["context"],
                }

        except HTTPException as exp:
            raise exp
        except Exception as exp:
            logger.exception(exp)
            raise HTTPException(status_code=500, detail=str(exp))
