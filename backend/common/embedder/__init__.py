from langchain.embeddings.openai import OpenAIEmbeddings

from backend.common.embedder.instruct import RemoteHuggingFaceInstructEmbeddings
from backend.common.embedder.tfy_embeddings import TruefoundryEmbeddings

# A dictionary mapping embedder names to their respective classes.
SUPPORTED_EMBEDDERS = {
    "OpenAI": OpenAIEmbeddings,
    "HuggingFaceInstruct": RemoteHuggingFaceInstructEmbeddings,
    "TruefoundryEmbeddings": TruefoundryEmbeddings,
}


def get_embedder(embedder, embedding_configuration):
    """
    Returns an instance of the embedding class based on the specified embedder and configuration.

    Args:
        embedder (str): The name of the embedder (e.g., "OpenAI", "HuggingFaceInstruct", "TruefoundryEmbeddings").
        embedding_configuration (dict): A dictionary containing configuration parameters for the embedder.

    Returns:
        Embeddings: An instance of the specified embedding class.
    """
    if embedder not in SUPPORTED_EMBEDDERS:
        raise Exception("Unsupported embedder")

    # Create an instance of the embedder based on the given embedder name.
    if embedder == "HuggingFaceInstruct":
        # For HuggingFaceInstruct, pass the embedding configuration as a single argument.
        return SUPPORTED_EMBEDDERS[embedder](
            embedding_configuration=embedding_configuration
        )
    elif embedder == "TruefoundryEmbeddings":
        # For TruefoundryEmbeddings, unpack the embedding configuration as keyword arguments.
        return SUPPORTED_EMBEDDERS[embedder](**embedding_configuration)
    elif embedder == "OpenAI":
        # For OpenAI, extract the "model" key from the embedding configuration (if provided) and pass it as an argument.
        if "model" in embedding_configuration:
            return SUPPORTED_EMBEDDERS[embedder](
                model=embedding_configuration.pop("model")
            )
        else:
            return SUPPORTED_EMBEDDERS[embedder]()
    else:
        raise Exception("Embedding model not supported!")
