This directory contains the primary code for the backend including a FastAPI service and documents indexer job. The code can be run locally or deployed as a service and job on the Truefoundry platform.

### Running code locally

Store the following values in local .env file

```
VECTOR_DB_CONFIG = '{"url": "<vectordb url here>", "provider": "<any of chroma/qdrant/weaviate>"}'
METADATA_STORE_CONFIG = '{"provider": "mlfoundry", "config": {"ml_repo_name": "<ml-repo name here>"}}'
TFY_SERVICE_ROOT_PATH = '/'
TFY_API_KEY =
TFY_HOST = <Truefoundry host for your account here>
```

1. Go to the root directory of this repository

```
cd ../..
```

2. Create a python environment

```
python3 -m venv venv
source venv/bin/activate
```

3. Install packages required

```
pip install -r backend/requirements.txt
```

4. Set environment variables

Copy the file .env.example to .env and set the values for the following variables. This is assuming we will be using OpenAI for the embeddings and LLM initially.

5. Run the Server

```
uvicorn --host 0.0.0.0 --port 8080 backend.server.app:app --reload
```

```
python -m backend.indexer.main --collection_name "test0403" --data_source_fqn "mlfoundry::data-dir:truefoundry/tfy-docs-rag/tfycc1" --raise_error_on_failure "False"
```

# Development

# Folder structure

    .
    ├── backend                             # Source files for backend
    │   ├── indexer                         # Source files for backend
    │   ├── modules                         # Modules to support different functions etc
    │   │   ├── dataloaders
    │   │   ├── embedder
    │   │   ├── metadata_store
    │   │   ├── parsers
    │   │   ├── query_controllers           # Register your query controllers here
    │   │   │   └── sample_controller
    │   │   └── vector_db
    │   └── server                          # Backend server that hosts the API
    │       ├── routers
    │       └── services
    ├── sample-data
    │   ├── creditcards
    │   └── mlops-pdf
    └── venv
    ├── .env                                # For local envs
    └── ...

# Modules

Modules are designed to support different functionalities like metadata_store, vector_db, embeddings, llms, parsers and data loaders
Each module can be extended by adding a subclass class of class defined in `__init__.py` of each folder.
Currently, we support following types in each module

-   dataloaders - dataloaders are component responsible for loading data from `DataSource`. We have `mlfoundry`, `web`, `github` and `local` dataloaders
-   embedder - embedder are component responsible for embedding functions used to index the documents into vector. We support all the embedding models available in TrueFoundry's LLM Gateway
-   llms - llms contain various llm components. We support all the chat models available in TrueFoundry's LLM Gateway.
-   metadara_store - used to store metadata of various collections like embedding used, chunk size, data source used, status of indexing. We are using `mlfoundry` ML repos, you can also use SQL for same
-   parsers - parsers are component responsible for parsing data and chunking them based on file type. We have `markdown`, `pdf`, and `txt` support
-   vector_db - used to store and query over vectors. We have `chroma`, `qdrant`, `weaviate`.

# Indexer

Indexer contains `indexer.py` that defines the steps for indexing and storing given data source to vector db. For running long indexing jobs, we give capability to run it as TrueFoundry `job` that is defined in `main.py`

# Server

Server contains `app.py` that defines API interface for the complete RAG system. Its built on `FastAPI` and out of the box exposes `swagger` (at path `/`) that can be used to test easily.
