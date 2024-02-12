from langchain.chat_models.base import BaseChatModel
from langchain.schema.vectorstore import VectorStore, VectorStoreRetriever

from backend.modules.retrievers.default_retriever import DefaultRetriver
from backend.utils.base import RetrieverConfig


def get_retriever(
    vectorstore: VectorStore,
    retriever_config: RetrieverConfig,
    llm: BaseChatModel,
):
    """Get retriever."""
    base_retriever = VectorStoreRetriever(
        vectorstore=vectorstore,
        search_type=retriever_config.get_search_type,
        search_kwargs=retriever_config.get_search_kwargs,
    )
    SUPPORTED_RETRIEVERS = [
        "VectorStoreRetriever",
        "DefaultRetriver",
    ]
    if retriever_config.class_name not in SUPPORTED_RETRIEVERS:
        raise ValueError(f"Unsupported retriever: {retriever_config.class_name}")
    match retriever_config.class_name:
        case "VectorStoreRetriever":
            return base_retriever
        case "DefaultRetriver":
            return DefaultRetriver(retriever=base_retriever, llm=llm)
