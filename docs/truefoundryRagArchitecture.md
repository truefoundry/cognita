# High Level RAG Architecture

![](./images/rag_arch.png)

Overall the RAG architecture is composed of several entities

1. **Data Sources** - These are the places that contain your documents to be indexed. Usually these are S3 buckets, databases, TrueFoundry Artifacts or even local disk

2. **Collection Metadata Store** - This store contains metadata about the collection themselves. A collection refers to a set of documents from one or more data sources combined. For each collection, the collection metadata stores

    - Name of the collection
    - Name of the associated Vector DB collection
    - Linked Data Sources
    - Parsing Configuration for each data source
    - Embedding Model and Configuration to be used

3. **TrueFoundry LLM Gateway** - This is a central proxy that allows proxying requests to various Embedding and LLM models across many providers with a unified API format.

4. **Vector DB** - This stores the embeddings and metadata for parsed files for the collection. It can be queried to get similar chunks or exact matches based on filters. We are using Qdrant as our choice of vector database.

5. **Indexing Job** - This is an asynchronous Job responsible for orchestrating the indexing flow. It will

    - Scan the Data Sources to get list of documents
    - Check the Vector DB state to filter out unchanged documents
    - Downloads and parses files to create smaller chunks with associated metadata
    - Embeds those chunks using the AI Gateway and puts them into Vector DB

    It can be started manually or run regularly on a cron schedule. The source code for this is in the `backend/indexer/`

6. **API Server** - This component processes the user query to generate answers with references synchronously. Each application has full control over the retrieval and answer process. Broadly speaking, when a user sends a request

    - The corresponsing Query Controller bootstraps retrievers or multi-step agents according to configuration.
    - User's question is processed and embedded using the AI Gateway.
    - One or more retrievers interact with the Vector DB to fetch relevant chunks and metadata.
    - A final answer is formed by using a LLM via the AI Gateway.
    - Metadata for relevant documents fetched during the process can be optionally enriched. E.g. adding presigned URLs.

    The code for this component is in `backend/server/`

### Data Indexing Flow

1. A Cron on some schedule will trigger the Indexing Job
1. The data source associated with the collection are **scanned** for all data points (files)
1. The job compares the VectorDB state with data source state to figure out **newly added files, updated files and deleted files**. The new and updated files are **downloaded**
1. The newly added files and updated files are **parsed and chunked** into smaller pieces each with their own metadata
1. The chunks are **embedded** using models like `text-ada-002` on TrueFoundry's AI Gateway
1. The embedded chunks are put into VectorDB with auto generated and provided metadata

### Question-Answering using API Server

1. Users sends a request with their query

2. It is routed to one of the app's query controller

3. One or more retrievers are constructed on top of the Vector DB

4. Then a Question Answering chain / agent is constructed. It embeds the user query and fetches similar chunks.

5. A single shot Question Answering chain just generates an answer given similar chunks. An agent can do multi step reasoning and use many tools before arriving at an answer. In both cases, the API server uses LLM models (like GPT 3.5, GPT 4, etc)

6. Before returning the answer, the metadata for relevant chunks can be updated with things like presigned urls, surrounding slides, external data source links.

7. The answer and relevant document chunks are returned in response.

    **Note:** In case of agents the intermediate steps can also be streamed. It is up to the specific app to decide.

# Code Architecture

### Base Code

Entire codebase lives in `backend/` Think of this as RAG components abstractions

```
.
|-- Dockerfile.merck
|-- README.md
|-- __init__.py
|-- backend/
|   |-- indexer/
|   |   |-- __init__.py
|   |   |-- indexer.py
|   |   |-- main.py
|   |   `-- types.py
|   |-- modules/
|   |   |-- __init__.py
|   |   |-- dataloaders/
|   |   |   |-- __init__.py
|   |   |   |-- loader.py
|   |   |   |-- localdirloader.py
|   |   |   `-- ...
|   |   |-- embedder/
|   |   |   |-- __init__.py
|   |   |   |-- embedder.py
|   |   |   `-- truefoundry_embedder.py
|   |   |-- metadata_store/
|   |   |   |-- base.py
|   |   |   |-- client.py
|   |   |   `-- mlfoundry.py
|   |   |-- parsers/
|   |   |   |-- __init__.py
|   |   |   |-- parser.py
|   |   |   |-- pdfparser_fast.py
|   |   |   `-- ...
|   |   |-- query_controllers/
|   |   |   |-- README.md
|   |   |   |-- default/
|   |   |   |   |-- controller.py
|   |   |   |   `-- types.py
|   |   |   |-- query_controller.py
|   |   |   `-- ...
|   |   `-- vector_db/
|   |       |-- __init__.py
|   |       |-- base.py
|   |       |-- qdrant.py
|   |       `-- ...
|   |-- requirements.txt
|   |-- server/
|   |   |-- __init__.py
|   |   |-- app.py
|   |   |-- decorators.py
|   |   |-- routers/
|   |   `-- services/
|   |-- settings.py
|   |-- types.py
|   `-- utils.py
```
