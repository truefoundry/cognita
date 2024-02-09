


# from fastapi import HTTPException

# from langchain.callbacks.manager import CallbackManagerForRetrieverRun
# from langchain.chat_models.base import BaseChatModel
# from langchain.schema import BaseRetriever, Document
# from langchain.schema.vectorstore import VectorStoreRetriever


# from backend.utils.logger import logger
# from backend.modules.retrievers.base import TFBaseRetriever, TFQueryInput, TFQueryOutput, retriever_post
# from backend.utils.base import RetrivalQuery
# from backend.modules.metadata_store import get_metadata_store_client
# from backend.modules.vector_db import get_vector_db_client
# from backend.settings import settings
# from servicefoundry.langchain import TrueFoundryChat
# from backend.modules.embedder import get_embedder



from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal
from backend.utils.logger import logger


from backend.utils.base import RetrieverConfig, LLMConfig
from servicefoundry.langchain import TrueFoundryChat
from backend.modules.embedder import get_embedder

from langchain.schema.vectorstore import VectorStoreRetriever
from langchain.schema import Document
from langchain.schema.vectorstore import VectorStore

from backend.modules.retrievers.base import TFBaseRetriever, TFQueryInput, retriever_post



RETRIEVER_NAME = 'credit-card'

class CreditCardInputDocs(TFQueryInput):

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

class CreditCardInputQuery(TFQueryInput):

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


class CreditCardRetriver(TFBaseRetriever):

    retriever_name: str = RETRIEVER_NAME

    @classmethod
    def get_embeddings(self, collection_name: str):
        collection = CreditCardRetriver._get_collection(collection_name)
        embedding = get_embedder(collection.embedder_config)
        return embedding
    
    @classmethod
    def get_vector_store(self, collection_name: str) -> VectorStore:
        vector_store_client = CreditCardRetriver._get_vector_store_client(collection_name)
        embeddings = CreditCardRetriver.get_embeddings(collection_name)
        vector_store = vector_store_client.get_vector_store(embeddings)
        return vector_store

    @classmethod
    def get_retriever(self, vector_store: VectorStore, retriever_config: RetrieverConfig):
       base_retriever = VectorStoreRetriever(
            vectorstore=vector_store,
            search_type=retriever_config.get_search_type,
            search_kwargs=retriever_config.get_search_kwargs,
        )
       return base_retriever
       
    @classmethod
    def get_llm(self, model_config: LLMConfig, system_prompt: str):
        llm = TrueFoundryChat(
            model=model_config.name,
            model_parameters=model_config.parameters,
            system_prompt=system_prompt,
        )
        logger.info(f"Loaded TrueFoundry LLM model {model_config.name}")
        return llm

    @staticmethod
    @retriever_post(RETRIEVER_NAME)
    def get_documents(input: CreditCardInputDocs):
        try:
            collection_name = input.collection_name
            vector_store = CreditCardRetriver.get_vector_store(collection_name)
            retriever = CreditCardRetriver.get_retriever(vector_store, input.retriever_config)
            llm = CreditCardRetriver.get_llm(input.model_configuration, input.system_prompt)

            # Formating the query

            query_template: str = """As an assistant, your role is to translate a user's natural \
            language query into a suitable query for a vectorstore, ensuring to omit any extraneous \
            information that may hinder the retrieval process. Please take the provided user query "{question}" \
            and refine it into a concise, relevant query for the vectorstore, focusing only on the \
            essential elements required for accurate and efficient data retrieval."""

            formatted_query = query_template.format(question=input.query)
            question = llm.predict(formatted_query)

            # Get Docs
            docs = retriever.get_relevant_documents(
                question
            )
            print("DOCS:",docs, type(docs))
            return docs

        
        except HTTPException as exp:
            raise exp
        except Exception as exp:
            logger.exception(exp)
            raise HTTPException(status_code=500, detail=str(exp))
        
    
    @staticmethod
    @retriever_post(RETRIEVER_NAME)
    def query(input: CreditCardInputQuery):    

        from langchain.prompts import PromptTemplate
        from backend.modules.retrieval_chains import get_retrieval_chain
        from langchain.chains.question_answering import load_qa_chain

        try:
            DOCUMENT_PROMPT = PromptTemplate(
                input_variables=["page_content"],
                template="<document>{page_content}</document>",
            )
            QA_PROMPT = PromptTemplate(
                input_variables=["context", "question"],
                template=input.prompt_template,
            )
            # Chain to get output for given query from docs using llm

            collection_name = input.collection_name
            vector_store = CreditCardRetriver.get_vector_store(collection_name)
            retriever = CreditCardRetriver.get_retriever(vector_store, input.retriever_config)
            llm = CreditCardRetriver.get_llm(input.model_configuration, input.system_prompt)


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












# class CreditCardRetriver(TFBaseRetriever, BaseRetriever):
#     """Custom Retriever that inherits TFRetriver and Langchain BaseRetriver."""

#     retriever_name = RETRIEVER_NAME
#     retriever: BaseRetriever
#     llm: BaseChatModel
#     query_template: str = """As an assistant, your role is to translate a user's natural \
#     language query into a suitable query for a vectorstore, ensuring to omit any extraneous \
#     information that may hinder the retrieval process. Please take the provided user query "{question}" \
#     and refine it into a concise, relevant query for the vectorstore, focusing only on the \
#     essential elements required for accurate and efficient data retrieval."""

#     def _get_relevant_documents(
#         self,
#         query: str,
#     ) -> List[Document]:
#         """Get docs."""
#         # rewrite the question for retrieval
#         query_template = self.query_template.format(question=query)
#         question = self.llm.predict(query_template)

#         logger.info(
#             f"Retrieving documents for updated question: {question} instead of {query}"
#         )
#         # retrieve N docs
#         docs = self.retriever.get_relevant_documents(
#             query
#         )

#         print("DOCS:",docs, type(docs))
#         return docs

# # This decorator will create path as: /retriver/<RETRIEVER_NAME>/<func_name>
# @retriever_post(RETRIEVER_NAME)
# async def get_answer(
#     request: RetrivalQuery
# ) -> List:
#     """Get docs."""

#     metadata_store_client = get_metadata_store_client(config=settings.METADATA_STORE_CONFIG)
#     collection = metadata_store_client.get_collection_by_name(request.collection_name)

#     if collection is None:
#         raise HTTPException(status_code=404, detail="Collection not found")

#     try:
#         # Vector Store Client
#         vector_db_client = get_vector_db_client(
#             config=settings.VECTOR_DB_CONFIG, collection_name=request.collection_name
#         )
#         # Model to use for chat
#         llm = TrueFoundryChat(
#             model=request.model_configuration.name,
#             model_parameters=request.model_configuration.parameters,
#             system_prompt=request.system_prompt,
#         )
#         logger.info(f"Loaded TrueFoundry LLM model {request.model_configuration.name}")

#         # get vector store
#         vector_store = vector_db_client.get_vector_store(
#             embeddings=get_embedder(collection.embedder_config),
#         )

#         # get retriever
#         base_retriever = VectorStoreRetriever(
#             vectorstore=vector_store,
#             search_type=request.retriever_config.get_search_type,
#             search_kwargs=request.retriever_config.get_search_kwargs,
#         )

#         retriver_obj = CreditCardRetriver(retriever=base_retriever, llm=llm)
#         documents = retriver_obj._get_relevant_documents(request.query)
#         return documents
        
#     except HTTPException as exp:
#         raise exp
#     except Exception as exp:
#         logger.exception(exp)
#         raise HTTPException(status_code=500, detail=str(exp))





    




    
    

    

