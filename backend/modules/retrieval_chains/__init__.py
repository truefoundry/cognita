from langchain.chains import RetrievalQA
from langchain.chains.combine_documents.base import BaseCombineDocumentsChain
from langchain.chat_models.base import BaseChatModel
from langchain.schema.vectorstore import VectorStoreRetriever

from backend.modules.retrieval_chains.custom_retrieval_qa import CustomRetrievalQA


def get_retrieval_chain(
    chain_name: str,
    retriever: VectorStoreRetriever,
    llm: BaseChatModel,
    combine_documents_chain: BaseCombineDocumentsChain,
    *args,
    **kwargs,
):
    """Get retrieval chain."""
    SUPPORTED_RETRIEVAL_CHAINS = {
        "RetrievalQA": RetrievalQA,
        "CustomRetrievalQA": CustomRetrievalQA,
    }
    if chain_name not in SUPPORTED_RETRIEVAL_CHAINS:
        raise ValueError(f"Unsupported retrieval chain: {chain_name}")
    match chain_name:
        case "RetrievalQA":
            return RetrievalQA(
                retriever=retriever,
                combine_documents_chain=combine_documents_chain,
                *args,
                **kwargs,
            )
        case "CustomRetrievalQA":
            return CustomRetrievalQA(
                retriever=retriever,
                combine_documents_chain=combine_documents_chain,
                llm=llm,
                *args,
                **kwargs,
            )
