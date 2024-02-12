from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal
from backend.utils.logger import logger


from backend.utils.base import RetrieverConfig, LLMConfig

# Compulsory inports
from backend.modules.retrievers.base import (
    LangchainQueryEngine,
    BaseRAGTool, 
    QueryInput, 
    retriever_post
)


class DefaultInputQuery(QueryInput):
    pass

RETRIEVER_NAME = 'default-retriever'

class DefaultRAGTool(BaseRAGTool):

    retriever_name: str = RETRIEVER_NAME
    
    @retriever_post(RETRIEVER_NAME)
    def query(input: DefaultInputQuery):    
        """We implement query function for getting answer and relavant documents"""
        try:
            from langchain.prompts import PromptTemplate
            from langchain.chains.question_answering import load_qa_chain
            from langchain.chains import RetrievalQA

            # Create query object
            query_object = LangchainQueryEngine()

            # Define prompt templates
            DOCUMENT_PROMPT = PromptTemplate(
                input_variables=["page_content"],
                template="<document>{page_content}</document>",
            )
            QA_PROMPT = PromptTemplate(
                input_variables=["context", "question"],
                template=input.prompt_template,
            )
            
            # Define reteiver and llm
            retriever = query_object._get_retriever(input.collection_name, input.retriever_config)
            llm = query_object._get_llm(input.model_configuration)

            # Define retrieval chain
            retrieval_chain = RetrievalQA(
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

            # get the output from the chain
            outputs = retrieval_chain({"query": input.query})

            return {
                "answer": outputs["result"],
                "docs": outputs.get("source_documents") or [],
            }
        
        except HTTPException as exp:
            raise exp
        except Exception as exp:
            logger.exception(exp)
            raise HTTPException(status_code=500, detail=str(exp))
