
# This is a simple script to test the retrieval QA chain
# Make sure the data is ingested in Qdrant DB before running this script
# This makes use of OpenSrc llms from Ollama and OpenSrc Embeddings

from backend.settings import Settings

from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.modules.vector_db.client import VECTOR_STORE_CLIENT
from backend.modules.embedder.embedder import get_embedder

from langchain.chains import RetrievalQA
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.schema.vectorstore import VectorStoreRetriever
from langchain_community.chat_models.ollama import ChatOllama

from langchain.retrievers import ContextualCompressionRetriever
from backend.modules.reranker import MxBaiReranker



settings = Settings()

def answer(query):
        
    # Get vector store
    collection = METADATA_STORE_CLIENT.get_collection_by_name(no_cache=True)
    vector_store = VECTOR_STORE_CLIENT.get_vector_store(
                collection_name=collection.name,
                embeddings=get_embedder(collection.embedder_config),
            )
    # Get the LLM
    llm = ChatOllama(
        # Change the model name to one available in your local Ollama instance
        model='gemma:2b',
        system="You are a question answering system. You answer question only based on the given context",
        temperature=0.1,
    )

    

    # Create the retriever using langchain VectorStoreRetriever
    retriever = VectorStoreRetriever(
        vectorstore=vector_store,
        search_type="similarity",
        search_kwargs={"k": 20},
    )

    # Re-ranking
    compressor = MxBaiReranker(
        model="mixedbread-ai/mxbai-rerank-xsmall-v1",
        top_k=5,
    )
    
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=retriever
    )

    # Prompts
    DOCUMENT_PROMPT = PromptTemplate(
        input_variables=["page_content"],
        template="<document>{page_content}</document>",
    )
    QA_PROMPT = PromptTemplate(
        input_variables=["context", "question"],
        template="Answer the question, given the context. Here is the context information:\n\n'''\n{context}\n'''\n\nQuestion: {question}\nAnswer:",
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
    outputs = qa.invoke({"query": query})


    return {
        "answer": outputs["result"],
        "docs": outputs.get("source_documents") or [],
    }



if __name__ == "__main__":
    query = "What are the features of Diners club black metal edition?"
    ans = answer(query=query)
    print(ans['answer'])
