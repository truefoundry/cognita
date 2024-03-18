# RAGFoundry

## QA on Docs using RAG Playground

Its quite easy to build an end to end RAG system on your own documents using Langchain or LlamaIndex. However, deploying the rag system in a scalable way requires us to solve a lot of problems listed below:

1. **Updating documents**: While we can index the documents one time, most production systems will need to keep the index updated with the latest documents. This requires a system to keep track of the documents and update the index when new documents are added or old documents are updated.
2. **Authorization**: We need to ensure that only authorized users can access the documents - this requires storing custom metadata per document and filtering the documents based on the user's access level.
3. **Scalability**: The system should be able to handle a large number of documents and users.
4. **Semantic Caching**: Caching the results can help reduce and latency in a lot of cases.
5. **Reusability**: RAG modules comprises of multiple components like dataloaders, parsers, vectorDB and retriever. We need to ensure that these components are reusable across different usecases, while also enabling each usecase to customize to the fullest extent.

RAGFoundry is an opensource framework to organize your RAG codebase along with a frontend to play around with different RAG customizations.

-   [✨ Getting Started](#getting-started)
-   [🐍 Installing Python and Setting Up a Virtual Environment](#🐍-installing-python-and-setting-up-a-virtual-environment)
    -   [Installing Python](#installing-python)
    -   [Setting Up a Virtual Environment](#setting-up-a-virtual-environment)
-   [🚀 Quickstart: Running RAG Locally](#🚀-quickstart-deploy-with-pip)
    -   [Install necessary packages](#install-necessary-packages)
    -   [Setting up Yaml](#setting-up-yaml)
    -   [Setting up .env file](#setting-up-env-file)
-   [🛠️ Project Architecture](#️🛠️-project-architecture)
    -   [⚙️ RAG Components](#rag-components)
    -   [💾 Data indexing](#data-indexing)
    -   [❓Question-Answering using API Server](#❓question-answering-using-api-server)
    -   [💻 Code Structure](#💻-code-structure)
    -   [Customizing the code for your usecase](#customizing-the-code-for-your-usecase)
-   [💡 Writing your Query Controller (QnA)](#💡-writing-your-query-controller-qna)
-   [🔑 API Reference](#🔑-api-reference)
-   [🐳 Quickstart: Deployment with Truefoundry](#🐳-quickstart-deployment-with-truefoundry)

# ✨ Getting Started

Starting with RAGFoundry is easy! You can play around with the code locally using the python [script](local_rag.py) or using the UI component that ships along with the code.

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

### Install the virtualenv package:

First, ensure you have pip installed (it comes with Python if you're using version 3.4 and above).
Install virtualenv by running:

```
pip install virtualenv
```

### Create a Virtual Environment:

Navigate to your project's directory in the terminal.
Run the following command to create a virtual environment named venv (you can name it anything you like):

```
python3 -m virtualenv venv
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

## Setting up YAML:

-   Local version requires `local.metadata.yaml` to be filled up

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
                model: openai-devtest/text-embedding-ada-002
        ```

## Setting up .env file:

-   Create a `.env` file or copy from `.env.sample`
-   Enter the following values:

    ```env
    # For local setup
    METADATA_STORE_CONFIG='{"provider":"local","config":{"path":"local.metadata.yaml"}}'
    VECTOR_DB_CONFIG='{"provider":"qdrant","local":true}'

    TFY_API_KEY = <YOUR_TF_API_KEY>
    TFY_SERVICE_ROOT_PATH = '/'
    DEBUG_MODE = true
    LOG_LEVEL = "DEBUG"
    ```

> You can also provide `OPENAI_API_KEY` here.

-   Now the setup is done, you can run your RAG locally, an example python script is provided by the name [`local_rag.py`](local_rag.py). The script has code for ingesting data into vector db and answering the query.

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

## Customizing the Code for your usecase

RAGFoundry goes by the tagline -

> Everything is available and Everything is customizable.

RAGFoundry makes it really easy to switch between parsers, loaders, models and retrievers.

### Customizing Dataloaders:

-   You can write your own data loader by inherting the `BaseDataLoader` class from `backend/modules/dataloaders/loader.py`

-   Finally, register the loader in `backend/modules/dataloaders/__init__.py`

### Customizing Embedder:

-   The codebase currently uses `OpenAIEmbeddings` you can registered as `default`.
-   You can register your custom embeddings in `backend/modules/embedder/__init__.py`

### Customizing Parsers:

-   You can write your own parser by inherting the `BaseParser` class from `backend/modules/parsers/parser.py`

-   Finally, register the parser in `backend/modules/parsers/__init__.py`

### Adding Custom VectorDB:

-   To add your own interface for a VectorDB you can inhertit `BaseVectorDB` from `backend/modules/vector_db/base.py`

-   Register the vectordb under `backend/modules/vector_db/__init__.py`

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

> As an example, we have implemented `sample_controller`. Please refer for better understanding

# 🔑 API Reference

Following section documents all the associated APIs that are used in RAG application.

---

If you run the server locally using the command: `uvicorn --host 0.0.0.0 --port 8080 backend.server.app:app --reload`
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

    Current available parsers include: `MarkdownParser`, `PdfParserUsingPyMuPDF`, `TextParser`.
    To add your own sources refer `backend/modules/parsers/README.md`

-   GET `/v1/components/embedders`: Returns a list of available embedders.

    ```curl
    curl -X 'GET' \
    'http://localhost:8080/v1/components/embedders' \
    -H 'accept: application/json'
    ```

    Current available `default` embeddings include: `TrueFoundryEmbeddings`

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
                    // name of the collection
                    "name": "ps01",

                    // description of the collection
                    "description": "test collection for open src repo",

                    // embedder configuration used to index the data into the collection
                    "embedder_config": {
                        // provider - default, if you init your own embedder add that as provider
                        "provider": "default",
                        "config": {
                            // embedder model name
                            "model": "openai-devtest/text-embedding-ada-002"
                        }
                    },
                    "associated_data_sources": {
                        // currently one associated data source in this collection th' mlfoundry data dir
                        "mlfoundry::data-dir:truefoundry/prathamesh-merck/reindexing-exp": {
                            // fqn of that data src
                            "data_source_fqn": "mlfoundry::data-dir:truefoundry/prathamesh/reindexing-exp",
                            // parser configuration
                            "parser_config": {
                                "chunk_size": 500,
                                "chunk_overlap": 0,
                                "parser_map": {
                                    ".pdf": "PdfParserFast",
                                    ".txt": "TextParser",
                                    ".md": "MarkdownParser"
                                }
                            },
                            // data src config similar to POST /v1/data_source
                            "data_source": {
                                "type": "mlfoundry",
                                "uri": "data-dir:truefoundry/prathamesh/reindexing-exp",
                                "metadata": null,
                                "fqn": "mlfoundry::data-dir:truefoundry/prathamesh/reindexing-exp"
                            }
                        }
                    }
                }
            ]
        }
        ```

-   POST `/v1/collections/`: Creates a new collection.
    -   This API creates a collection, it requires payload of the form:
        -   ```json
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
-   POST `/v1/collections/{collection_name}`: Deletes an already exisiting collection.
    ```curl
    curl -X 'DELETE' \
      'http://localhost:8080/v1/collections/xyz' \
      -H 'accept: application/json'
    ```

### Retrievers

Any registered question answer API is showcased here. To add your own retriever refer: `backend/modules/query_controllers/README.md`

---

-   POST `/retrievers/answer`: Sample answer method to answer the question using the context from the collection.

    -   It requires the following fields as payload:

        -   `collection_name (str)`: The name of the collection to search in. This is a required field.

        -   `retriever_config (RetrieverConfig)`: The configuration for the retriever that will be used to search the collection. This is a required field and must be an instance of the RetrieverConfig class. `retriever_config` in turn requires following arguments:

            -   `search_type (Literal["mmr", "similarity"])`: "Defines the type of search that the Retriever should perform. Can be "similarity" (default), "mmr", or "similarity_score_threshold".

            -   `k (int)`: The number of results/documents to retrieve. This is a required field and must be a positive integer.

            -   `fetch_k (int)`: Amount of documents to pass to MMR algorithm (Default: 20).

            -   `filter (Optional[dict])`: Optional field to add any filters to query.

        -   `query (str)`: The question that will be searched for in the collection. This is a required field and must be a string with a maximum length of 1000 characters.

        -   `model_configuration (LLMConfig)`: The configuration for the Language Model that will be used to generate the answer to the question using the context. This in turn requires following fields:

            -   `name (str)`: Name of the model from the Truefoundry LLM Gateway
            -   `parameters (dict)`: Any optional parameters of the model like max_tokens, etc

        -   `prompt_template (str)`: The template that will be used to format the context, question, and answer. This is an optional field with a default value. The template must include placeholders for the context and the question.

    -   Example:

        ```curl
        curl -X 'POST' \
          'http://localhost:8080/retrievers/answer' \
          -H 'accept: application/json' \
          -H 'Content-Type: application/json' \
          -d '{
          "collection_name": "ps01",
          "retriever_config": {
            "search_type": "similarity",
            "k": 4,
            "fetch_k": 20,
            "filter": {}
          },
          "query": "What is credit card",
          "model_configuration": {
            "name": "openai-devtest/gpt-3-5-turbo",
            "parameters": {}
          },
          "prompt_template": "Here is the context information:\n\n'\'''\'''\''\n{context}\n'\'''\'''\''\n\nQuestion: {question}\nAnswer:"
        }'
        ```

    -   Response:
        ```json
        {
            "answer": "A credit card is a payment card issued by a financial institution that allows the cardholder to borrow funds to make purchases, with the promise to repay the borrowed amount along with any applicable interest and fees. Credit cards typically have a credit limit, which is the maximum amount that the cardholder can borrow. They are widely used for making purchases, both online and in-person, and often come with benefits such as rewards points, cashback, and other perks.",
            "docs": [
                {
                    "page_content": "# [Freedom card new](https://www.hdfcbank.com/personal/pay/cards/credit-cards/freedom-card-new)\n## Features\n#### Contactless Payment\nContactless Payment\nThe HDFC Bank Freedom Credit Card is enabled for contactless payments, facilitating fast, convenient and secure payments at retail outlets. To see if your Card is contactless, look for the contactless network symbol on your Card.",
                    "metadata": {
                        "Header1": "[Freedom card new](https://www.hdfcbank.com/personal/pay/cards/credit-cards/freedom-card-new)",
                        "Header2": "Features",
                        "Header4": "Contactless Payment",
                        "_document_id": "mlfoundry::data-dir:truefoundry/prathamesh-merck/reindexing-exp::freedom-card-new.md",
                        "_id": "cb10dd50-695b-4c26-a2be-a73fcb09e2ba",
                        "_collection_name": "ps01"
                    },
                    "type": "Document"
                },
                {
                    "page_content": "# [Freedom card new](https://www.hdfcbank.com/personal/pay/cards/credit-cards/freedom-card-new)\n## Features\n#### Reward Points/Cashback Redemption & Validity\n* CashPoints can also be used for redemption against travel benefits like Flight & Hotel bookings and also on Rewards Catalogue at the SmartBuy Rewards Portal, wherein Credit Card members can redeem up to a maximum of 50% of the booking value through CashPoints at a value of 1 CashPoint = ₹0.15 and the rest of the amount will have to be paid via the Credit Card. To know more on Rewards catalouge, [click here](/personal/pay/cards/credit-cards/simple-rewards-program",
                    "metadata": {
                        "Header1": "[Freedom card new](https://www.hdfcbank.com/personal/pay/cards/credit-cards/freedom-card-new)",
                        "Header2": "Features",
                        "Header4": "Reward Points/Cashback Redemption & Validity",
                        "_document_id": "mlfoundry::data-dir:truefoundry/prathamesh-merck/reindexing-exp::freedom-card-new.md",
                        "_id": "74d476a3-77f5-46e0-bc69-a49472f20243",
                        "_collection_name": "ps01"
                    },
                    "type": "Document"
                },
                {
                    "page_content": "# [Hdfc bank upi rupay credit card](https://www.hdfcbank.com/personal/pay/cards/credit-cards/hdfc-bank-upi-rupay-credit-card)\n## Features\n#### Revolving Credit\nRevolving Credit\nEnjoy Revolving Credit on your HDFC Bank UPI RuPay Credit Card at nominal interest rate. Please refer to the Fees and Charges section for more details.",
                    "metadata": {
                        "Header1": "[Hdfc bank upi rupay credit card](https://www.hdfcbank.com/personal/pay/cards/credit-cards/hdfc-bank-upi-rupay-credit-card)",
                        "Header2": "Features",
                        "Header4": "Revolving Credit",
                        "_document_id": "mlfoundry::data-dir:truefoundry/prathamesh-merck/reindexing-exp::hdfc-bank-upi-rupay-credit-card.md",
                        "_id": "30a72a77-5055-48be-b0ba-18adcf06ed5e",
                        "_collection_name": "ps01"
                    },
                    "type": "Document"
                },
                {
                    "page_content": "# [Hdfc bank upi rupay credit card](https://www.hdfcbank.com/personal/pay/cards/credit-cards/hdfc-bank-upi-rupay-credit-card)\n## Features\n#### Reward Point/Cashback Redemption & Validity\n* CashPoints can also be used for redemption against travel benefits like Flight & Hotel bookings and also on Rewards Catalogue at the SmartBuy Rewards Portal, wherein Credit Card members can redeem up to a maximum of 50% of the booking value through CashPoints at a value of 1 CashPoint = ₹0.25 and the rest of the amount will have to be paid via the Credit Card. To know more on Rewards catalouge, [click here](/personal/pay/cards/credit-cards/claim-rewards",
                    "metadata": {
                        "Header1": "[Hdfc bank upi rupay credit card](https://www.hdfcbank.com/personal/pay/cards/credit-cards/hdfc-bank-upi-rupay-credit-card)",
                        "Header2": "Features",
                        "Header4": "Reward Point/Cashback Redemption & Validity",
                        "_document_id": "mlfoundry::data-dir:truefoundry/prathamesh-merck/reindexing-exp::hdfc-bank-upi-rupay-credit-card.md",
                        "_id": "a544165f-0542-43cc-a38b-154344ae5d16",
                        "_collection_name": "ps01"
                    },
                    "type": "Document"
                }
            ]
        }
        ```

# 🐳 Quickstart: Deployment with Truefoundry

To be able to **Query** on your own documents, follow the steps below:

1.  Register at TrueFoundry, follow [here](https://www.truefoundry.com/register)

    -   Fill up the form and register as an organization (let's say <org_name>)
    -   On `Submit`, you will be redirected to your dashboard endpoint ie https://<org_name>.truefoundry.cloud
    -   Complete your email verification
    -   Login to the platform at your dashboard endpoint ie. https://<org_name>.truefoundry.cloud

    `Note: Keep your dashboard endpoint handy, we will refer it as "TFY_HOST" and it should have structure like "https://<org_name>.truefoundry.cloud"`

2.  Setup a cluster, use TrueFoundry managed for quick setup

    -   Give a unique name to your **[Cluster](https://docs.truefoundry.com/docs/workspace)** and click on **Launch Cluster**
    -   It will take few minutes to provision a cluster for you
    -   On **Configure Host Domain** section, click `Register` for the pre-filled IP
    -   Next, `Add` a **Docker Registry** to push your docker images to.
    -   Next, **Deploy a Model**, you can choose to `Skip` this step

3.  Add a **Storage Integration**

4.  Create a **ML Repo**

    -   Navigate to **ML Repo** tab
    -   Click on `+ New ML Repo` button on top-right
    -   Give a unique name to your **ML Repo** (say 'docs-qa-llm')
    -   Select **Storage Integration**
    -   On `Submit`, your **ML Repo** will be created

        For more details: [link](https://docs.truefoundry.com/docs/creating-ml-repo-via-ui)

5.  Create a **Workspace**

    -   Navigate to **Workspace** tab
    -   Click on `+ New Workspace` button on top-right
    -   Select your **Cluster**
    -   Give a name to your **Workspace** (say 'docs-qa-llm')
    -   Enable **ML Repo Access** and `Add ML Repo Access`
    -   Select your **ML Repo** and role as **Project Admin**
    -   On `Submit`, a new **Workspace** will be created. You can copy the **Workspace FQN** by clicking on **FQN**.

    For more details: [link](https://docs.truefoundry.com/docs/installation-and-setup#5-creating-workspaces)

6.  Generate an **API Key**

    -   Navigate to **Settings > API Keys** tab
    -   Click on `Create New API Key`
    -   Give any name to the **API Key**
    -   On `Generate`, **API Key** will be gererated.
    -   **Please save the value or download it**

        `Note: we will refer it as "TFY_API_KEY"`

        For more details: https://docs.truefoundry.com/docs/generate-api-key

7.  In order to use default OpenAI embedder. Please get an **OpenAI API Key**. You can get your API Key [here](https://platform.openai.com/account/api-keys)

8.  Qdrant Deployment
    To store and retrieve vectors we setup a vector database in this case Qdrant. You can also setup other databases like Chroma, Weviate,

    -   Go to deployments tab
    -   Select Applications
    -   Select your workspace name for deployment
    -   Select Qdrant
    -   Enter the name of Qdrant DB
    -   Click Submit

    Qdrant will be deployed on your instance, and an endpoint will be available in Qdrant dashboard keep it handy, this will be referred as `VECTOR_DB_CONFIG` url.

9.  Open your Terminal on parent folder and create a virtual env (\*\*python >= 3.10 required)

    ```
      python3 -m venv ./venv
      source ./venv/bin/activate (for Linux/Mac env)
      source .\venv\Scripts\activate (for Windows env)
    ```

10. Install requirements.txt

    ```
    pip install -r backend/requirements.txt
    ```

11. Login from cli

    ```
    sfy login --host <paste your TFY_HOST here>
    ```

12. Setup .env file (Example given below)

    ```
    # For truefoundry setup
    # VECTOR_DB_CONFIG = '{"url": "<vectordb url here from 8.>", "provider": "<any of chroma/qdrant/weaviate>"}'
    VECTOR_DB_CONFIG = '{"url": "https://qdrant-test.tfy-ctl-euwe1-org.org.truefoundry.tech", "provider": "qdrant"}'

    # METADATA_STORE_CONFIG = '{"provider": "mlfoundry", "config": {"ml_repo_name": "<ml-repo name here>"}}'
    METADATA_STORE_CONFIG = '{"provider": "mlfoundry", "config": {"ml_repo_name": "test"}}'

    # For local setup
    TFY_API_KEY = "<YOUR_API_KEY From 6.>"
    TFY_HOST = "<TFY_HOST From 1.">

    TFY_SERVICE_ROOT_PATH = '/'

    # Optional if you have indexer job deployed in truefoundry, and you want to trigger it for indexing.
    # JOB_FQN =
    # JOB_COMPONENT_NAME =

    # Optional if you want to use redis for caching
    # EMBEDDING_CACHE_CONFIG =

    DEBUG_MODE = true
    LOG_LEVEL = "DEBUG"
    ```

13. Run the indexer to index the data into vectordb

```
python -m backend.indexer.main --collection_name "test0403" --data_source_fqn "mlfoundry::data-dir:truefoundry/tfy-docs-rag/tfycc1" --raise_error_on_failure "False"
```

    `--collection_name` will be the collection you use
    `--data_source_fqn` will be the FQN of datasource either from DataDirectory or Artifact of Truefoundry.

14. Run the Server

```
uvicorn --host 0.0.0.0 --port 8080 backend.server.app:app --reload
```
