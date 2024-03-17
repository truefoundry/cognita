# QA on Docs using RAG Playground

## Introduction

Its quite easy to build an end to end RAG system on your own documents in a Jupyter Notebook using Langchain or LlamaIndex. However, deploying the rag system in a scalable way requires us to solve a lot of problems listed below:

1. **Updating documents**: While we can index the documents one time, most production systems will need to keep the index updated with the latest documents. This requires a system to keep track of the documents and update the index when new documents are added or old documents are updated.
2. **Authorization**: We need to ensure that only authorized users can access the documents - this requires storing custom metadata per document and filtering the documents based on the user's access level.
3. **Scalability**: The system should be able to handle a large number of documents and users.
4. **Semantic Caching**: Caching the results can help reduce and latency in a lot of cases.
5. **Reusability**: RAG modules comprises of multiple components like dataloaders, parsers, vectorDB and retriever. We need to ensure that these components are reusable across different usecases, while also enabling each usecase to customize to the fullest extent.

This is an opensource framework to organize your RAG codebase along with a frontend to play around with different RAG customizations.

### Getting Started

You can play around with the code locally using the python script or using the UI component that ships along with the code. [Follow the steps here](docs/LOCAL_SETUP.md) to run the code locally. You can index a local set of documents and check the responses.

### Code Architecture

You can read about the RAG architecture and how the codebase manifests it [here](docs/ARCHITECTURE.md)

### Customizing the Code for your usecase

This RAG codebase makes it really easy to switch between parsers, loaders, models and retrievers. To understand how to change or add any code for your own usecase, follow the guide here: [Customizing the Code](docs/CUSTOMIZING.md)

### API Reference

To understand all the APIs exposed by this code, please read the docs [here](docs/RUN.md)
