import os

import qdrant_client
from langchain.vectorstores import Qdrant

from backend.common.logger import logger


def put_embeddings_in_vectordb(collection_name, docs, embeddings, embedder_config):
    """
    Puts embeddings into the Qdrant Vector Database for a given collection.

    Args:
        collection_name (str): The name of the collection where embeddings will be stored.
        docs (List[langchain.docstore.document.Document]): List of documents associated with embeddings.
        embeddings (langchain.embeddings.base.Embeddings): Embedding to be used to embed the docs.
        embedder_config (Dict[str, any]): Configuration dictionary containing embedder parameters.

    Returns:
        None
    """
    qdrant_client = get_qdrant_client()
    location = None
    api_key = None
    if not os.environ.get("QDRANT_URL"):
        # Use the local Qdrant client's location if no remote URL is provided.
        location = qdrant_client._client.location
    else:
        # Use the provided remote Qdrant URL and API key (if available).
        location = qdrant_client._client.rest_uri
        api_key = qdrant_client._client._api_key

    # Calculate the batch size for inserting documents into Qdrant.
    qdrant_batch_size = 64
    if "batch_size" in embedder_config and "parallel_workers" in embedder_config:
        qdrant_batch_size = (
            embedder_config["batch_size"] * embedder_config["parallel_workers"]
        )

    # Log the Qdrant batch size.
    logger.info("Qdrant batch size: " + str(qdrant_batch_size))

    # Store documents and embeddings into the Qdrant Vector Database.
    Qdrant.from_documents(
        docs,
        embeddings,
        collection_name=collection_name,
        prefer_grpc=True,
        location=location,
        api_key=api_key,
        batch_size=qdrant_batch_size,
    )


def get_qdrant_client():
    """
    Initializes and returns a Qdrant client for interacting with the Qdrant Vector Database.

    Returns:
        qdrant_client.QdrantClient: The Qdrant client instance.
    """
    remote_qdrant_url = os.environ.get("QDRANT_URL")
    try:
        if not remote_qdrant_url:
            # Initialize a local Qdrant client if no remote URL is provided.
            client = qdrant_client.QdrantClient(":memory:")
            return client
        else:
            if os.environ.get("QDRANT_KEY"):
                # Initialize a remote Qdrant client with an API key if available.
                logger.info(
                    "Initializing remote qdrant instance with API key at %s",
                    remote_qdrant_url,
                )
                # This may raise the _InactiveRpcError
                client = qdrant_client.QdrantClient(
                    url=os.environ.get("QDRANT_URL"),
                    api_key=os.environ.get("QDRANT_KEY"),
                    prefer_grpc=True,
                )
                return client
            else:
                # Initialize a remote Qdrant client without an API key.
                logger.info(
                    "Initializing remote qdrant instance at %s", remote_qdrant_url
                )
                client = qdrant_client.QdrantClient(
                    url=os.environ.get("QDRANT_URL"),
                    prefer_grpc=True,
                )
                return client

    except Exception as exception:
        logger.info(str(exception))
        raise Exception("Error connecting to qdrant instance.")


def delete_qdrant_collection_if_exists(collection_name):
    """
    Deletes a Qdrant collection if it exists.

    Args:
        collection_name (str): The name of the collection to be deleted.

    Returns:
        None
    """
    client = get_qdrant_client()
    qdrant_collection = client.get_collection(collection_name=collection_name)
    if qdrant_collection:
        # Delete the collection if it exists.
        client.delete_collection(collection_name)
    logger.info("Deleted the qdrant collection: " + collection_name)
