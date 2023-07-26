import os

import qdrant_client
from langchain.vectorstores import Qdrant

from backend.common.logger import logger


def put_embeddings_in_vectordb(collection_name, docs, embeddings, embedder_config):
    qdrant_client = get_qdrant_client()
    location = None
    api_key = None
    if not os.environ.get("QDRANT_URL"):
        location = qdrant_client._client.location
    else:
        location = qdrant_client._client.rest_uri
        api_key = qdrant_client._client._api_key
    qdrant_batch_size = 64
    if "batch_size" in embedder_config and "parallel_workers" in embedder_config:
        qdrant_batch_size = (
            embedder_config["batch_size"] * embedder_config["parallel_workers"]
        )
    logger.info("Qdrant batch size: " + str(qdrant_batch_size))
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
    remote_qdrant_url = os.environ.get("QDRANT_URL")
    print("Qdrant url: " + str(remote_qdrant_url))
    try:
        if not remote_qdrant_url:
            client = qdrant_client.QdrantClient(":memory:")
            return client
        else:
            if os.environ.get("QDRANT_KEY"):
                logger.info(
                    "Initializing remote qdrant instance with API key at %s",
                    remote_qdrant_url,
                )
                # Your code that may raise the _InactiveRpcError
                client = qdrant_client.QdrantClient(
                    url=os.environ.get("QDRANT_URL"),
                    api_key=os.environ.get("QDRANT_KEY"),
                    prefer_grpc=True,
                )
                return client
            else:
                logger.info("Initializing remote qdrant instance at %s", remote_qdrant_url)
                # Your code that may raise the _InactiveRpcError
                client = qdrant_client.QdrantClient(
                    url=os.environ.get("QDRANT_URL"),
                    prefer_grpc=True,
                )
                return client

    except Exception as exception:
        logger.info(str(exception))
        raise Exception("Error connecting to qdrant instance.")


def get_qdrant_langchain_client(collection_name, embeddings):
    qdrant_client = get_qdrant_client()
    # initialize langchain qdrant for retrieval
    return Qdrant(
        client=qdrant_client, collection_name=collection_name, embeddings=embeddings
    )


def delete_qdrant_collection_if_exists(collection_name):
    client = get_qdrant_client()
    qdrant_collection = client.get_collection(collection_name=collection_name)
    if qdrant_collection:
        client.delete_collection(collection_name)
    logger.info("Deleted the qdrant collection: " + collection_name)
