from fastapi import HTTPException
from langchain.chains import RetrievalQA
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.schema.vectorstore import VectorStoreRetriever

from backend.modules.query_engines.base import BaseQueryEngine
from backend.utils.base import DefaultQueryInput
from backend.utils.decorator import Post, QueryEngine
from backend.utils.logger import logger


@QueryEngine("/default")
class DefaultQueryEngine(BaseQueryEngine):
    """
    Default Query Engine
    uses langchain retrieval qa to answer the query
    """

    @Post("/query")
    async def query(self, request: DefaultQueryInput):
        try:
            # Get the vector store
            vector_store = await self._get_vector_store(request.collection_name)

            # Get the LLM
            llm = await self._get_llm(request.model_configuration)

            # Create the retriever using langchain VectorStoreRetriever
            retriever = VectorStoreRetriever(
                vectorstore=vector_store,
                search_type=request.retriever_config.get_search_type,
                search_kwargs=request.retriever_config.get_search_kwargs,
            )
            DOCUMENT_PROMPT = PromptTemplate(
                input_variables=["page_content"],
                template="<document>{page_content}</document>",
            )
            QA_PROMPT = PromptTemplate(
                input_variables=["context", "question"],
                template=request.prompt_template,
            )

            # Create the QA chain
            qa = RetrievalQA(
                retriever=retriever,
                combine_documents_chain=load_qa_chain(
                    llm=llm,
                    chain_type="stuff",
                    prompt=QA_PROMPT,
                    document_variable_name="context",
                    document_prompt=DOCUMENT_PROMPT,
                    verbose=True,
                ),
                return_source_documents=True,
                verbose=True,
            )

            # Get the answer
            outputs = qa({"query": request.query})

            return {
                "answer": outputs["result"],
                "docs": outputs.get("source_documents") or [],
            }
        except HTTPException as exp:
            raise exp
        except Exception as exp:
            logger.exception(exp)
            raise HTTPException(status_code=500, detail=str(exp))
