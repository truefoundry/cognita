# Docs QA Playground

## Architecture

To deploy the complete workflow, we need to set up various components. Here's an overview of the architecture:

### Document Store:

The Document Store is where your documents will be stored. Common options include AWS S3, Google Storage Buckets, or Azure Blob Storage. In some cases, data might come in from APIs, such as Confluence docs.

### Indexer Job:

The Indexer Job takes the documents as input, splits them into chunks, calls the embedding model to embed the chunks, and stores the vectors in the VectorDB. The embedding model can be loaded in the job itself or accessed via an API to ensure scalability.

### Embedding Model:

If you're using OpenAI or an externally hosted model, you don't need to host a model. However, if you opt for an open-source model, you'll have to deploy it in your cloud environment.

### LLM Model:

For OpenAI or hosted model APIs like Cohere and Anthropic, there's no need for additional deployment. Otherwise, you'll need to set up an open-source LLM.

### Query Service:

A FastAPI service provides an API to list all indexed document collections and allows users to query over these collections. It also supports triggering new indexing jobs for additional document collections.

### VectorDB:

You can use a hosted solution like PineCone or host an open-source VectorDB like Qdrant or Milvus to efficiently retrieve similar document chunks.

### Metadata Store:

This store is essential for managing links to indexed documents and storing the configuration used to embed the chunks in those documents.

## Setup with Truefoundry:

Truefoundry, a Kubernetes-based platform, simplifies the deployment of ML training jobs and services at an optimal cost. You can deploy all the components mentioned above on your own cloud account using Truefoundry. The final deployment will be a streamlined and powerful system ready to handle your question-answering needs.

## Deploy on TrueFoundry

If you want to quick start and deploy on TrueFoundry, follow [here](./GETTING_STARTED.md).
