from fastapi import HTTPException, Body
from langchain.chains import RetrievalQA
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.schema.vectorstore import VectorStoreRetriever

from backend.logger import logger
from backend.modules.embedder.embedder import get_embedder
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.modules.query_controllers.default.types import DefaultQueryInput, DEFAULT_QUERY
from backend.modules.vector_db.client import VECTOR_STORE_CLIENT
from backend.server.decorators import post, query_controller

from langchain_community.chat_models.ollama import ChatOllama
from langchain_openai.chat_models import ChatOpenAI
from langchain.retrievers import ContextualCompressionRetriever
from backend.modules.reranker import MxBaiReranker


@query_controller()
class DefaultQueryController:
    """
    Uses langchain retrieval qa to answer the query
    """

    @post("/answer")
    async def answer(self, request: DefaultQueryInput = Body(DEFAULT_QUERY)):
        """
        Sample answer method to answer the question using the context from the collection
        """
        try:
            # Get the vector store
            collection = METADATA_STORE_CLIENT.get_collection_by_name(
                request.collection_name
            )

            if collection is None:
                raise HTTPException(status_code=404, detail="Collection not found")

            vector_store = VECTOR_STORE_CLIENT.get_vector_store(
                collection_name=collection.name,
                embeddings=get_embedder(collection.embedder_config),
            )

            # If model provider is openai, use OpenAI Chat Model
            if request.model_configuration.provider == "openai":
                llm = ChatOpenAI(
                    model=request.model_configuration.name,
                    temperature=request.model_configuration.parameters.get("temperature", 0.1),
                    system="You are a question answering system. You answer question only based on the given context.",
                )
            # If model provider is ollama, use Ollama Chat Model
            elif request.model_configuration.provider == "ollama":
                llm = ChatOllama(
                    model=request.model_configuration.name,
                    temperature=request.model_configuration.parameters.get("temperature", 0.1),
                    system="You are a question answering system. You answer question only based on the given context.",
                )
            


            # Create the retriever using langchain VectorStoreRetriever
            retriever = VectorStoreRetriever(
                vectorstore=vector_store,
                search_type=request.retriever_config.get_search_type,
                search_kwargs=request.retriever_config.get_search_kwargs,
            )

            # Re-ranking
            compressor = MxBaiReranker(
                model="mixedbread-ai/mxbai-rerank-xsmall-v1",
                top_k=5,
            )
            
            compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor, base_retriever=retriever
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
                retriever=compression_retriever,
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
            logger.info(f"Request query: {request.query}")
            outputs = await qa.ainvoke({"query": request.query})

            return {
                "answer": outputs["result"],
                "docs": outputs.get("source_documents") or [],
            }
        except HTTPException as exp:
            raise exp
        except Exception as exp:
            logger.exception(exp)
            raise HTTPException(status_code=500, detail=str(exp))
