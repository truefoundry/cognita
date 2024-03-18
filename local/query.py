
# This is a simple script to test the retrieval QA chain
# Make sure the data is ingested in Qdrant DB before running this script

from backend.settings import Settings

from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.modules.vector_db.client import VECTOR_STORE_CLIENT
from backend.modules.embedder.embedder import get_embedder

from langchain.chains import RetrievalQA
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.schema.vectorstore import VectorStoreRetriever
from langchain_openai.chat_models import ChatOpenAI



settings = Settings()

def answer(query):
        
    # Get vector store
    collection = METADATA_STORE_CLIENT.get_collection_by_name(no_cache=True)
    vector_store = VECTOR_STORE_CLIENT.get_vector_store(
                collection_name=collection.name,
                embeddings=get_embedder(collection.embedder_config),
            )
    # Get the LLM
    llm = ChatOpenAI(
        model='openai-devtest/gpt-3-5-turbo',
    )

    # Create the retriever using langchain VectorStoreRetriever
    retriever = VectorStoreRetriever(
        vectorstore=vector_store,
        search_type="similarity",
        search_kwargs={"k": 3},
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
        retriever=retriever,
        combine_documents_chain=load_qa_chain(
            llm=llm,
            chain_type="stuff",
            prompt=QA_PROMPT,
            document_variable_name="context",
            document_prompt=DOCUMENT_PROMPT,
            verbose=False,
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
    query = "What is a credit card?"
    ans = answer(query=query)
    print(ans['answer'])
