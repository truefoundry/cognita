from langchain.embeddings.openai import OpenAIEmbeddings
from backend.common.embedder.instruct import RemoteHuggingFaceInstructEmbeddings
from backend.common.embedder.tfy_embeddings import TruefoundryEmbeddings

SUPPORTED_EMBEDDERS = {
    "OpenAI": OpenAIEmbeddings,
    "HuggingFaceInstruct": RemoteHuggingFaceInstructEmbeddings,
    "TruefoundryEmbeddings": TruefoundryEmbeddings,
}


def get_embedder(embedder, embedding_configuration):
    """
    Returns the embedding class for given configuration.
    """
    if embedder not in SUPPORTED_EMBEDDERS:
        raise Exception("Unsupported embedder")

    if embedder == "HuggingFaceInstruct":
        return SUPPORTED_EMBEDDERS[embedder](
            embedding_configuration=embedding_configuration
        )
    elif embedder == "TruefoundryEmbeddings":
        return SUPPORTED_EMBEDDERS[embedder](**embedding_configuration)
    elif embedder == "OpenAI":
        if "model" in embedding_configuration:
            return SUPPORTED_EMBEDDERS[embedder](
                model=embedding_configuration.pop("model")
            )
        else:
            return SUPPORTED_EMBEDDERS[embedder]()
    else:
        raise Exception("Embedding model not supported!")
