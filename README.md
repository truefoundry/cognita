# RAGFoundry

## QA on Docs using RAG Playground

Starting with RAGFoundry is easy! Its quite easy to build an end to end RAG system on your own documents using Langchain or LlamaIndex. However, deploying the rag system in a scalable way requires us to solve a lot of problems listed below:

1. **Updating documents**: While we can index the documents one time, most production systems will need to keep the index updated with the latest documents. This requires a system to keep track of the documents and update the index when new documents are added or old documents are updated.
2. **Authorization**: We need to ensure that only authorized users can access the documents - this requires storing custom metadata per document and filtering the documents based on the user's access level.
3. **Scalability**: The system should be able to handle a large number of documents and users.
4. **Semantic Caching**: Caching the results can help reduce and latency in a lot of cases.
5. **Reusability**: RAG modules comprises of multiple components like dataloaders, parsers, vectorDB and retriever. We need to ensure that these components are reusable across different usecases, while also enabling each usecase to customize to the fullest extent.

-   [✨ Getting Started](#✨-getting-started)
-   [🐍 Installing Python and Setting Up a Virtual Environment](#🐍-installing-python-and-setting-up-a-virtual-environment)
    -   [Installing Python](#installing-python)
    -   [Setting Up a Virtual Environment](#setting-up-a-virtual-environment)
-   [🚀 Quickstart: Running RAG Locally](#🚀-quickstart-running-rag-locally)
    -   [Install necessary packages](#install-necessary-packages)
    -   [Setting up .env file](#setting-up-env-file)
    -   [Executing the Code](#executing-the-code)
-   [🛠️ Project Architecture](#🛠️-project-architecture)
    -   [⚙️ RAG Components](#rag-components)
    -   [💾 Data indexing](#data-indexing)
    -   [❓Question-Answering using API Server](#❓question-answering-using-api-server)
    -   [💻 Code Structure](#💻-code-structure)
    -   [Customizing the code for your usecase](#customizing-the-code-for-your-usecase)
-   [💡 Writing your Query Controller (QnA)](#💡-writing-your-query-controller-qna)
-   [🔑 API Reference](#🔑-api-reference)
-   [🐳 Quickstart: Deployment with Truefoundry](#🐳-quickstart-deployment-with-truefoundry)

# ✨ Getting Started

RAGFoundry is an opensource framework to organize your RAG codebase along with a frontend to play around with different RAG customizations. You can play around with the code locally using the python [script](#🚀-quickstart-running-rag-locally) or using the [UI component](frontend/README.md) that ships with the code.

# 🐍 Installing Python and Setting Up a Virtual Environment

Before you can use RAGFoundry, you'll need to ensure that `Python >=3.10.0` is installed on your system and that you can create a virtual environment for a safer and cleaner project setup.

## Installing Python

Python is required to run RAGFoundry. If you don't have Python installed, follow these steps:

### For Windows:

Download the latest Python installer from the official Python website.
Run the installer and make sure to check the box that says `Add Python to PATH` during installation.

### For macOS:

You can install Python using Homebrew, a package manager for macOS, with the following command in the terminal:

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then install Python:

```
brew install python
```

### For Linux:

Python usually comes pre-installed on most Linux distributions. If it's not, you can install it using your distribution's package manager. You can read more about it [here](https://opensource.com/article/20/4/install-python-linux)

## Setting Up a Virtual Environment

It's recommended to use a virtual environment to avoid conflicts with other projects or system-wide Python packages.

### Create a Virtual Environment:

Navigate to your project's directory in the terminal.
Run the following command to create a virtual environment named venv (you can name it anything you like):

```
python3 -m venv ./venv
```

### Activate the Virtual Environment:

-   On Windows, activate the virtual environment by running:

```
venv\Scripts\activate.bat
```

-   On macOS and Linux, activate it with:

```
source venv/bin/activate
```

Once your virtual environment is activated, you'll see its name in the terminal prompt. Now you're ready to install RAGFoundry using the steps provided in the Quickstart sections.

> Remember to deactivate the virtual environment when you're done working with RAGFoundry by simply running deactivate in the terminal.

# 🚀 Quickstart: Running RAG Locally

Following are the instructions for running the RAG application locally without any additional Truefoundry dependencies

## Install necessary packages:

-   Install the requirements using the following command:

```
pip install -r requirements.txt
```

## Setting up .env file:

-   Create a `.env` file or copy from `.env.sample`
-   Enter the following values:

    ```env
    # For local setup
    METADATA_STORE_CONFIG='{"provider":"local","config":{"path":"local.metadata.yaml"}}'
    VECTOR_DB_CONFIG='{"provider":"qdrant","local":true}'

    TFY_SERVICE_ROOT_PATH = '/'
    DEBUG_MODE = true
    LOG_LEVEL = "DEBUG"

    # Add OPENAI_API_KEY for LLMs and Embedding
    # OPENAI_API_KEY=

    # Else if using TF LLM GATEWAY, add TFY_API_KEY
    # TFY_API_KEY=
    ```

    > Setting up `TFY_API_KEY` or `OPENAI_API_KEY` is optional, you can use opensource LLMs and Embeddings if required (Discussed later).

-   Now the setup is done, you can run your RAG locally.

## Executing the Code:

-   Repository offers two categories of examples that demostrate running your own RAG.

    -   One using OpenAI functions, OpenAI compatible LLMs and Embeddings. Can be used either by setting `TFY_API_KEY` or `OPENAI_API_KEY`
    -   Another using entirely OpenSource LLMs (th' [Ollama](https://ollama.com/library)) and OpenSource Embeddings (e.g: [mixbread](https://www.mixedbread.ai/blog/mxbai-embed-large-v1)).
        > Both of these scripts can be used as a reference for your own use case.
    -   Sample scripts are in the `local` folder.

-   To run RAG locally using OpenAI compatible functions,

    -   Setup Yaml in `local.metadata.yaml`

        -   Example:

        ```yaml
        collection_name: testcollection
        # Sample data is provided under ./sample-data/
        data_source:
            type: local
            # Local data source path
            uri: sample-data/creditcards
        parser_config:
            chunk_size: 400
            parser_map:
                # Since data is markdown type, we use the MarkdownParser
                ".md": MarkdownParser
        embedder_config:
            provider: default
            config:
                # Embedding Model from TFY
                # Can also use OpenAI model directly
                # Or an opensrc embedding registered in embedder module
                model: openai-devtest/text-embedding-ada-002
        ```

    -   Ingest the data, by executing the following command from root folder: `python -m local.ingest`

-   To run RAG locally using OpenSource LLMs and Embeddings,
    -   Setup Yaml in `local.metadata.yaml`
        -   Example:
        ```yaml
        collection_name: testcollection
        # Sample data is provided under ./sample-data/
        data_source:
            type: local
            # Local data source path
            uri: sample-data/creditcards
        parser_config:
            chunk_size: 400
            parser_map:
                # Since data is markdown type, we use the MarkdownParser
                ".md": MarkdownParser
        embedder_config:
            provider: mixbread
            config:
                # Model name from HuggingFace model hub
                # Registered in embedder module of backend
                model: mixedbread-ai/mxbai-embed-large-v1
        ```
    -   This requires using Opensource LLM, Embeddings and Reranking modules.
        -   For LLM download ollama: https://ollama.com/download
        -   For Embeddings: `pip install -r backend/embedder/embedding.requirements.txt`
        -   For Reranking: `pip install -r backend/embedder/reranker.requirements.txt`
    -   Ingest the data, by executing the following command from root folder: `python -m local.ingest`
    -   The Query function uses, `gemma:2b` from Ollama. Make sure you have the corresponding LLM, `ollama pull gemma:2b` else replace the corresponding LLM with the LLM of your choice.
    -   The script also uses a document reranker, `mixedbread-ai/mxbai-rerank-xsmall-v1` to effectively rerank and find top relavant documents.
-   Execute: `python -m local.run`

# 🛠️ Project Architecture

![](./docs/images/rag_arch.png)

Overall the RAG architecture is composed of several entities

## RAG Components:

1. **Data Sources** - These are the places that contain your documents to be indexed. Usually these are S3 buckets, databases, TrueFoundry Artifacts or even local disk

2. **Metadata Store** - This store contains metadata about the collection themselves. A collection refers to a set of documents from one or more data sources combined. For each collection, the collection metadata stores

    - Name of the collection
    - Name of the associated Vector DB collection
    - Linked Data Sources
    - Parsing Configuration for each data source
    - Embedding Model and Configuration to be used

3. **TrueFoundry LLM Gateway** - This is a central proxy that allows proxying requests to various Embedding and LLM models across many providers with a unified API format.

4. **Vector DB** - This stores the embeddings and metadata for parsed files for the collection. It can be queried to get similar chunks or exact matches based on filters. We are using Qdrant as our choice of vector database.

5. **Indexing Job** - This is an asynchronous Job responsible for orchestrating the indexing flow. Indexing can be started manually or run regularly on a cron schedule. It will

    - Scan the Data Sources to get list of documents
    - Check the Vector DB state to filter out unchanged documents
    - Downloads and parses files to create smaller chunks with associated metadata
    - Embeds those chunks using the AI Gateway and puts them into Vector DB
        > The source code for this is in the `backend/indexer/`

6. **API Server** - This component processes the user query to generate answers with references synchronously. Each application has full control over the retrieval and answer process. Broadly speaking, when a user sends a request

    - The corresponsing Query Controller bootstraps retrievers or multi-step agents according to configuration.
    - User's question is processed and embedded using the AI Gateway.
    - One or more retrievers interact with the Vector DB to fetch relevant chunks and metadata.
    - A final answer is formed by using a LLM via the AI Gateway.
    - Metadata for relevant documents fetched during the process can be optionally enriched. E.g. adding presigned URLs.
        > The code for this component is in `backend/server/`

## Data Indexing:

1. A Cron on some schedule will trigger the Indexing Job
1. The data source associated with the collection are **scanned** for all data points (files)
1. The job compares the VectorDB state with data source state to figure out **newly added files, updated files and deleted files**. The new and updated files are **downloaded**
1. The newly added files and updated files are **parsed and chunked** into smaller pieces each with their own metadata
1. The chunks are **embedded** using models like `text-ada-002` on TrueFoundry's LLM Gateway
1. The embedded chunks are put into VectorDB with auto generated and provided metadata

## ❓Question-Answering using API Server:

1. Users sends a request with their query

2. It is routed to one of the app's query controller

3. One or more retrievers are constructed on top of the Vector DB

4. Then a Question Answering chain / agent is constructed. It embeds the user query and fetches similar chunks.

5. A single shot Question Answering chain just generates an answer given similar chunks. An agent can do multi step reasoning and use many tools before arriving at an answer. In both cases, the API server uses LLM models (like GPT 3.5, GPT 4, etc)

6. Before returning the answer, the metadata for relevant chunks can be updated with things like presigned urls, surrounding slides, external data source links.

7. The answer and relevant document chunks are returned in response.

    **Note:** In case of agents the intermediate steps can also be streamed. It is up to the specific app to decide.

## 💻 Code Structure:

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
|   |   |   -- mixbread_embedder.py
|   |   |   `-- embedding.requirements.txt
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
|   |   |   |-- default/
|   |   |   |   |-- controller.py
|   |   |   |   `-- types.py
|   |   |   |-- query_controller.py
|   |   |-- reranker/
|   |   |   |-- mxbai_reranker.py
|   |   |   |-- reranker.requirements.txt
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

## Customizing the Code for your usecase

RAGFoundry goes by the tagline -

> Everything is available and Everything is customizable.

RAGFoundry makes it really easy to switch between parsers, loaders, models and retrievers.

### Customizing Dataloaders:

-   You can write your own data loader by inherting the `BaseDataLoader` class from `backend/modules/dataloaders/loader.py`

-   Finally, register the loader in `backend/modules/dataloaders/__init__.py`

-   Testing a dataloader on localdir, in root dir, copy the following code as `test.py` and execute it. We show how to test an existing `LocalDirLoader` here:

    ```python
    from backend.modules.dataloaders import LocalDirLoader
    from backend.types import DataSource

    data_source = DataSource(
        type="local",
        uri="sample-data/creditcards",
        fqn="xyz://dummy"
    )

    loader = LocalDirLoader()

    # This yeilds a generator
    loaded_data_pts = loader.load_filtered_data_points_from_data_source(
        data_source=data_source,
        dest_dir="test/creditcards",
        existing_data_point_fqn_to_hash={},
        batch_size=1,
        data_ingestion_mode="append"
    )

    for data_pt in loaded_data_pts:
        print(data_pt)
    ```

### Customizing Embedder:

-   The codebase currently uses `OpenAIEmbeddings` you can registered as `default`.
-   You can register your custom embeddings in `backend/modules/embedder/__init__.py`
-   You can also add your own embedder an example of which is given under `backend/modules/embedder/mixbread_embedder.py`. It inherits langchain embedding class.

### Customizing Parsers:

-   You can write your own parser by inherting the `BaseParser` class from `backend/modules/parsers/parser.py`

-   Finally, register the parser in `backend/modules/parsers/__init__.py`

-   Testing a Parser on a local file, in root dir, copy the following code as `test.py` and execute it. Here we show how we can test existing `MarkdownParser`:

    ```python
    import os
    import asyncio
    from backend.types import LoadedDataPoint
    from backend.modules.parsers import MarkdownParser

    async def get_chunks(filepath, **kwargs):
        loader_data_point = LoadedDataPoint(
            local_filepath=filepath,
            file_extension=os.path.splitext(filepath)[1],
            data_point_uri="xyz://dummy",
            data_source_fqn="xyz://dummy",
            data_point_hash="dummy",
        )
        parser = MarkdownParser(**kwargs)
        return await parser.get_chunks(loaded_data_point=loader_data_point)


    chunks =  asyncio.run(get_chunks(filepath="sample-data/creditcards/diners-club-black-metal-edition.md", chunk_size=None, chunk_overlap=0))
    print(chunks)
    ```

### Adding Custom VectorDB:

-   To add your own interface for a VectorDB you can inhertit `BaseVectorDB` from `backend/modules/vector_db/base.py`

-   Register the vectordb under `backend/modules/vector_db/__init__.py`

### Rerankers:

-   Rerankers are used to sort relavant documents such that top k docs can be used as context effectively reducing the context and prompt in general.
-   Sample reranker is written under `backend/modules/reranker/mxbai_reranker.py`

# 💡 Writing your Query Controller (QnA):

Code responsible for implementing the Query interface of RAG application. The methods defined in these query controllers are added routes to your FastAPI server.

## Steps to add your custom Query Controller:

-   Add your Query controller class in `backend/modules/query_controllers/`

-   Add `query_controller` decorator to your class and pass the name of your custom controller as argument

```controller.py
from backend.server.decorator import query_controller

@query_controller("/my-controller")
class MyCustomController():
    ...
```

-   Add methods to this controller as per your needs and use our http decorators like `post, get, delete` to make your methods an API

```controller.py
from backend.server.decorator import post

@query_controller("/my-controller")
class MyCustomController():
    ...

    @post("/answer")
    def answer(query: str):
        # Write code to express your logic for answer
        # This API will be exposed as POST /my-controller/answer
        ...
```

-   Import your custom controller class at `backend/modules/query_controllers/__init__.py`

```__init__.py
...
from backend.modules.query_controllers.sample_controller.controller import MyCustomController
```

> As an example, we have implemented sample controller in `backend/modules/query_controllers/default`. Please refer for better understanding

# 🔑 API Reference

Following section documents important APIs that are used in RAG application.

---

If you run the server locally using the command: `uvicorn --host 0.0.0.0 --port 8000 backend.server.app:app --reload`
Then, Swagger doc will be available at: `http://localhost:8080/`

### Components

This group of API list down different components of RAG that are registered.

---

-   GET `/v1/components/parsers`: Returns a list of available parsers.

    ```curl
    curl -X 'GET' \
    'http://localhost:8080/v1/components/parsers' \
    -H 'accept: application/json'
    ```

    Current available parsers include: `MarkdownParser`, `PdfParserFast`, `TextParser`.
    To add your own sources refer `backend/modules/parsers/README.md`

-   GET `/v1/components/embedders`: Returns a list of available embedders.

    ```curl
    curl -X 'GET' \
    'http://localhost:8080/v1/components/embedders' \
    -H 'accept: application/json'
    ```

    Current available `default` embeddings include: `OpenAIEmbeddings`, `MixBreadEmbeddings`

-   `/v1/components/dataloaders`: Returns a list of available data loaders.
    ```curl
    curl -X 'GET' \
    'http://localhost:8080/v1/components/dataloaders' \
    -H 'accept: application/json'
    ```
    Current available dataloaders are: `github`, `local`, `web`, `mlfoundry`, `artifact`.
    To add your own sources refer `backend/modules/dataloaders/README.md`

### Data Sources

This API is used for creating/listing a new data source. Data source is one through which data is scanned and loaded for indexing.

---

-   GET `/v1/data_source/`: Returns a list of available data sources.

    ```curl
    curl -X 'GET' \
    'http://localhost:8080/v1/data_source/' \
    -H 'accept: application/json'
    ```

-   POST `/v1/data_source/`: Creates a new data source.

    -   Creation API requires following fields:
        ```json
        {
            "type": "string",
            "uri": "string",
            "metadata": {}
        }
        ```
    -   Attributes:

            -   `type` (str): The type of the data source. This field is required. One of `mlfoundry` or `local`.
            -   `uri` (str): A unique identifier for the data source. This field is required. This can be FQN of MLRepo or FQN of Artifact with version number from Truefoundry or local folder path.
            -   `metadata` (Optional[Dict[str, Any]]): Any additional configuration for the data source. This field is optional.

            This API returns a `unique data source fqn` that is then used to associate it with the collection.

    > When using locally, data source is automatically initialized from `local.metadata.yaml`

### Collection

This API is used for managing the collections. Each collection has embedder configuration and associated data sources that forms a key characterisitc of the collection.

---

-   GET `/v1/collections/`: Returns a list of available collections.

    ```curl
      curl -X 'GET' \
      'http://localhost:8080/v1/collections/' \
      -H 'accept: application/json'
    ```

    -   Sample Response:

        ```json
        {
            "collections": [
                {
                    "name": "testcollection",
                    "description": null,
                    "embedder_config": {
                        "provider": "mixbread",
                        "config": {
                            "model": "mixedbread-ai/mxbai-embed-large-v1"
                        }
                    },
                    "associated_data_sources": {
                        "local::sample-data/creditcards": {
                            "data_source_fqn": "local::sample-data/creditcards",
                            "parser_config": {
                                "chunk_size": 400,
                                "chunk_overlap": 0,
                                "parser_map": {
                                    ".md": "MarkdownParser"
                                }
                            },
                            "data_source": {
                                "type": "local",
                                "uri": "sample-data/creditcards",
                                "metadata": null,
                                "fqn": "local::sample-data/creditcards"
                            }
                        }
                    }
                }
            ]
        }
        ```

-   POST `/v1/collections/`: Creates a new collection. - This API creates a collection, it requires payload of the form: -

    ```json
    {
        "name": "collectionName",
        "description": "string",
        "embedder_config": {
            "provider": "string",
            "config": {}
        },
        "associated_data_sources": [
            {
                "data_source_fqn": "string",
                "parser_config": {
                    "chunk_size": 500,
                    "chunk_overlap": 0,
                    "parser_map": {
                        ".md": "MarkdownParser",
                        ".pdf": "PdfParserFast",
                        ".txt": "TextParser"
                    }
                }
            }
        ]
    }
    ```

    > When using locally, collection is automatically initialized from `local.metadata.yaml`

-   DELETE `/v1/collections/{collection_name}`: Deletes an already exisiting collection.
    ```curl
    curl -X 'DELETE' \
      'http://localhost:8080/v1/collections/xyz' \
      -H 'accept: application/json'
    ```

### Data Indexing

-   POST `v1/collections/ingest`: Ingest data into the colleciton.
    ```curl
        {
            "collection_name": "",
            "data_source_fqn": "",
            "data_ingestion_mode": "INCREMENTAL",
            "raise_error_on_failure": true,
            "run_as_job": false
        }
    ```
    -   To run locally either use `python -m local.ingest` or following API request:
        > collection name and data source fqn are taken from `GET` `/v1/collections/`
    ```json
    {
        "collection_name": "testcollection",
        "data_source_fqn": "local::sample-data/creditcards",
        "data_ingestion_mode": "INCREMENTAL",
        "raise_error_on_failure": true,
        "run_as_job": false
    }
    ```

### Retrievers

Any registered question answer API is showcased here. You can add your own retriever at : `backend/modules/query_controllers/`. Refer to `examples` folder for more info.

---

-   POST `/retrievers/openai/answer`: Sample answer method to answer the question using the context from the collection.

    -   It requires the following fields as payload:

        -   `collection_name (str)`: The name of the collection to search in. This is a required field.

        -   `retriever_config (RetrieverConfig)`: The configuration for the retriever that will be used to search the collection. This is a required field and must be an instance of the RetrieverConfig class. `retriever_config` in turn requires following arguments:

            -   `search_type (Literal["mmr", "similarity"])`: "Defines the type of search that the Retriever should perform. Can be "similarity" (default), "mmr", or "similarity_score_threshold".

            -   `k (int)`: The number of results/documents to retrieve. This is a required field and must be a positive integer.

            -   `fetch_k (int)`: Amount of documents to pass to MMR algorithm (Default: 20).

            -   `filter (Optional[dict])`: Optional field to add any filters to query.

        -   `query (str)`: The question that will be searched for in the collection. This is a required field and must be a string with a maximum length of 1000 characters.

        -   `model_configuration (LLMConfig)`: The configuration for the Language Model that will be used to generate the answer to the question using the context. This in turn requires following fields:

            -   `provider(Literal["openai", "ollama"])`: Provider of LLM
            -   `name (str)`: Name of the model from the Truefoundry LLM Gateway
            -   `parameters (dict)`: Any optional parameters of the model like max_tokens, etc

        -   `prompt_template (str)`: The template that will be used to format the context, question, and answer. This is an optional field with a default value. The template must include placeholders for the context and the question.

    -   Example:

        ```curl
        curl -X 'POST' \
            'http://localhost:8000/retrievers/answer' \
            -H 'accept: application/json' \
            -H 'Content-Type: application/json' \
            -d '{
            "collection_name": "testcollection",
            "retriever_config": {
                "search_type": "similarity",
                "k": 20,
                "fetch_k": 20
            },
            "query": "What are the features of Diners club black metal edition?",
            "model_configuration": {
                "name": "gemma:2b",
                "parameters": {
                "temperature": 0.1
                },
                "provider": "ollama"
            },
            "prompt_template": "Given the context, answer the question.\n\nContext: {context}\n'\'''\'''\''Question: {question}\nAnswer:"
        }
        ```

    -   Response:
        ```json
        {
            "answer": "The features of Diners club black metal edition are:\n\n* Smart EMI\n* Key Features\n    * Metal Card\n    * Unlimited Airport Lounge Access\n    * 6 Complimentary Golf games every quarter across the finest courses in the world\n    * Complimentary Annual memberships of Club Marriott, Amazon Prime, Swiggy One as Welcome Benefit\n    * 10,000 Bonus Reward Points on spends of ₹ 4 lakh every calendar quarter\n    * 2X Reward Points on Weekend Dining\n    * 5 Reward Points for every ₹ 150 spent",
            "docs": [
                {
                    "page_content": "# [Diners club black metal edition](https://www.hdfcbank.com/personal/pay/cards/credit-cards/diners-club-black-metal-edition)\n## Features\n#### Smart EMI\nSmart EMI\nHDFC Bank Diners Club Black Metal Credit Card comes with an option to convert your big spends into EMI after purchase. To know more click here",
                    "metadata": {
                        "Header4": "Smart EMI",
                        "Header2": "Features",
                        "Header1": "[Diners club black metal edition](https://www.hdfcbank.com/personal/pay/cards/credit-cards/diners-club-black-metal-edition)",
                        "_data_point_fqn": "local::sample-data/creditcards::diners-club-black-metal-edition.md",
                        "_data_point_hash": "9635",
                        "_id": "ba8852d56ea146ccb549388d10aeb946",
                        "_collection_name": "testcollection"
                    },
                    "type": "Document"
                },
                {
                    "page_content": "# [Diners club black metal edition](https://www.hdfcbank.com/personal/pay/cards/credit-cards/diners-club-black-metal-edition)\n## Features\n#### Key Features\nKey Features\n* Metal Card\n* Unlimited Airport Lounge Access\n* 6 Complimentary Golf games every quarter across the finest courses in the world\n* Complimentary Annual memberships of Club Marriott, Amazon Prime, Swiggy One as Welcome Benefit\n* 10,000 Bonus Reward Points on spends of ₹ 4 lakh every calendar quarter\n* 2X Reward Points on Weekend Dining\n* 5 Reward Points for every ₹ 150 spent",
                    "metadata": {
                        "Header4": "Key Features",
                        "Header2": "Features",
                        "Header1": "[Diners club black metal edition](https://www.hdfcbank.com/personal/pay/cards/credit-cards/diners-club-black-metal-edition)",
                        "_data_point_fqn": "local::sample-data/creditcards::diners-club-black-metal-edition.md",
                        "_data_point_hash": "9635",
                        "_id": "5830cf944447420a9d904ae8b0d57559",
                        "_collection_name": "testcollection"
                    },
                    "type": "Document"
                },
                {
                    "page_content": "# [Diners club black metal edition](https://www.hdfcbank.com/personal/pay/cards/credit-cards/diners-club-black-metal-edition)\n## Features\n#### Contactless Payment\nContactless Payment\nThe HDFC Bank Diners Club Black Metal Credit Card is enabled for contactless payments on HDFC Bank POS machines, facilitating fast, convenient and secure payments at retail outlets. Tap the reverse side of the Black Metal card on the HDFC Bank POS machine to enjoy contactless payments.",
                    "metadata": {
                        "Header4": "Contactless Payment",
                        "Header2": "Features",
                        "Header1": "[Diners club black metal edition](https://www.hdfcbank.com/personal/pay/cards/credit-cards/diners-club-black-metal-edition)",
                        "_data_point_fqn": "local::sample-data/creditcards::diners-club-black-metal-edition.md",
                        "_data_point_hash": "9635",
                        "_id": "503864c47c104d7dadd8213de4d34481",
                        "_collection_name": "testcollection"
                    },
                    "type": "Document"
                },
                {
                    "page_content": "# [Diners club black metal edition](https://www.hdfcbank.com/personal/pay/cards/credit-cards/diners-club-black-metal-edition)\n## Features\n#### Dining Benefits\nEarn 2X on weekend dining at standalone resturants capped at 1000 reward points per day. [Click here](/Personal/Pay/Cards/Credit Card/Credit Card Landing Page/Credit Cards/Super Premium/Diners Club Black Metal Edition/Diners-club-black-metal-T-and-C.pdf \"/Personal/Pay/Cards/Credit Card/Credit Card Landing Page/Credit Cards/Super Premium/Diners Club Black Metal",
                    "metadata": {
                        "Header4": "Dining Benefits",
                        "Header2": "Features",
                        "Header1": "[Diners club black metal edition](https://www.hdfcbank.com/personal/pay/cards/credit-cards/diners-club-black-metal-edition)",
                        "_data_point_fqn": "local::sample-data/creditcards::diners-club-black-metal-edition.md",
                        "_data_point_hash": "9635",
                        "_id": "71477795920c4f898b50289e6ec89499",
                        "_collection_name": "testcollection"
                    },
                    "type": "Document"
                },
                {
                    "page_content": "# [Diners club black metal edition](https://www.hdfcbank.com/personal/pay/cards/credit-cards/diners-club-black-metal-edition)\n## Features\n#### Additional Features\nAdditional Features\n**Interest Free Credit Period:** Up to 50 days of interest free credit period on your HDFC Bank Diners Club Black Credit Card from the date of purchase. (subject to the submission of the charge by the Merchant)\n**Credit liability cover:** ₹ 9 lakh\n**Foreign Currency Markup:** 2% on all your foreign currency spends.",
                    "metadata": {
                        "Header4": "Additional Features",
                        "Header2": "Features",
                        "Header1": "[Diners club black metal edition](https://www.hdfcbank.com/personal/pay/cards/credit-cards/diners-club-black-metal-edition)",
                        "_data_point_fqn": "local::sample-data/creditcards::diners-club-black-metal-edition.md",
                        "_data_point_hash": "9635",
                        "_id": "c837ae1717124b69aa3b8861f82d48d0",
                        "_collection_name": "testcollection"
                    },
                    "type": "Document"
                }
            ]
        }
        ```

# 🐳 Quickstart: Deployment with Truefoundry:

Refer the [docs](docs/TF_DEPLOY.md) for more information.
