from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal
from backend.utils.logger import logger


from backend.utils.base import RetrieverConfig, LLMConfig


from backend.modules.retrievers.base import (
    BaseQueryEngine,
    RAGEngine, 
    QueryInput, 
    retriever_post
)



RETRIEVER_NAME = 'credit-card'

class CredCardDocsQuery(QueryInput):
    collection_name: str = Field(
        default=None,
        title="Collection name on which to search",
    )

    query: str = Field(title="Query using which the similar documents will be searched", max_length=1000)

    retrieval_chain_name: Literal["RetrievalQA", "CustomRetrievalQA"] = Field(
        default="RetrievalQA",
        title="Name of the retrieval chain to use for retrieving documents",
    )

    retriever_config: RetrieverConfig = Field(
        title="Retriever configuration",
    )

    model_configuration: LLMConfig

    system_prompt: str = Field(
        default="""Your task is to craft the most helpful, highly informative, accurate and comprehensive answers possible, 
    ensuring they are easy to understand and implement. Use the context information provided as a reference to form accurate responses 
    that incorporate as much relevant detail as possible. Strive to make each answer clear and precise to enhance user comprehension and 
    assist in solving their problems effectively.\n\nEmploy the provided context information meticulously to craft precise answers, 
    ensuring they incorporate all pertinent details. Structure your responses for ease of reading and relevance by providing as much as 
    information regarding it. Make sure the answers are well detailed and provide proper references. Align your answers with the context given and maintain transparency 
    by indicating any uncertainty or lack of knowledge regarding the correct answer to avoid providing incorrect information.""",
        title="System prompt to use for generating answer to the question",
    )

class CreditCardInputQuery(QueryInput):
    collection_name: str = Field(
        default=None,
        title="Collection name on which to search",
    )

    query: str = Field(title="Query using which the similar documents will be searched", max_length=1000)

    retrieval_chain_name: Literal["RetrievalQA", "CustomRetrievalQA"] = Field(
        default="RetrievalQA",
        title="Name of the retrieval chain to use for retrieving documents",
    )

    retriever_config: RetrieverConfig = Field(
        title="Retriever configuration",
    )

    model_configuration: LLMConfig

    system_prompt: str = Field(
        default="""Your task is to craft the most helpful, highly informative, accurate and comprehensive answers possible, 
    ensuring they are easy to understand and implement. Use the context information provided as a reference to form accurate responses 
    that incorporate as much relevant detail as possible. Strive to make each answer clear and precise to enhance user comprehension and 
    assist in solving their problems effectively.\n\nEmploy the provided context information meticulously to craft precise answers, 
    ensuring they incorporate all pertinent details. Structure your responses for ease of reading and relevance by providing as much as 
    information regarding it. Make sure the answers are well detailed and provide proper references. Align your answers with the context given and maintain transparency 
    by indicating any uncertainty or lack of knowledge regarding the correct answer to avoid providing incorrect information.""",
        title="System prompt to use for generating answer to the question",
    )
    prompt_template: str = Field(
        default="""Here is the context information:\n\n'''\n{context}\n'''\n\nQuestion: {question}\nAnswer:""",
        title="Prompt Template to use for generating answer to the question using the context",
    )


class CreditCardRetriver(RAGEngine):

    retriever_name: str = RETRIEVER_NAME
    
    @retriever_post(RETRIEVER_NAME)
    def get_documents(input: CredCardDocsQuery):
        """Here we directly use the get documents function from the base class without any modifications"""
        try:        
            query_object = BaseQueryEngine()
            # Get the retriever
            retriever = query_object._get_retriever(input.collection_name, input.retriever_config)

            # Initialize LLM for query formatting 
            llm = query_object._get_llm(input.model_configuration, input.system_prompt)

            query_template: str = """As an assistant, your role is to translate a user's natural \
            language query into a suitable query for a vectorstore, ensuring to omit any extraneous \
            information that may hinder the retrieval process. Please take the provided user query "{question}" \
            and refine it into a concise, relevant query for the vectorstore, focusing only on the \
            essential elements required for accurate and efficient data retrieval."""

            formatted_query = query_template.format(question=input.query)

            # reformat the user query using the above llm
            question = llm.predict(formatted_query)

            # get relavant documents
            docs = retriever.get_relevant_documents(
                question
            )
            return docs
        except HTTPException as exp:
            raise exp
        except Exception as exp:
            logger.exception(exp)
            raise HTTPException(status_code=500, detail=str(exp))
    
    @retriever_post(RETRIEVER_NAME)
    def query(input: CreditCardInputQuery):    
        """We implement query function for getting answer and relavant documents"""
        from langchain.prompts import PromptTemplate
        from backend.modules.retrieval_chains import get_retrieval_chain
        from langchain.chains.question_answering import load_qa_chain

        try:
            query_object = BaseQueryEngine()

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
            llm = query_object._get_llm(input.model_configuration, input.system_prompt)

            # Define retrieval chain
            retrieval_chain = get_retrieval_chain(
                chain_name=input.retrieval_chain_name,
                retriever=retriever,
                llm=llm,
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
