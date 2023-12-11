This directory contains the primary code for the backend including a FastAPI service and documents indexer job. The code can be run locally or deployed as a service and job on the Truefoundry platform.

### Running code locally

Prerequisite: follow [here](../../GETTING_STARTED.md) and fetch following values

```
ML_REPO_NAME = 
VECTOR_DB_CONFIG = 
METADATA_STORE_TYPE = 
TFY_SERVICE_ROOT_PATH = 
JOB_FQN = 
TFY_API_KEY = 
TFY_HOST = 
LLM_GATEWAY_ENDPOINT = 
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

Note: To run the indexer job too locally, add `DEBUG_MODE=true` as env

5. Run the Server

```
uvicorn --host 0.0.0.0 --port 8080 backend.server.app:app --reload
```

6. Run indexer JOB

**Use mlfoundry artifact as the data source**
```
python -m backend.indexer.main --collection_name newtestag --chunk_size 350 --indexer_job_run_name newtestag-k185 --data_source '{"type": "mlfoundry", "credentials": null, "config": {"uri": "artifact:truefoundry/ag-test/newtestag_7a62e508-41f1-45ff-b49f-bf75a6afe4fa:1"}}' --embedder_config '{"description": null, "provider": "OpenAI", "config": {"model": "text-embedding-ada-002"}}' --parser_config '{}' --vector_db_config '{"provider": "weaviate", "url": "https://test-f97pfm6u.weaviate.network", "api_key": null}'
```

**Use local file as the data source**
```
python -m backend.indexer.main --collection_name newtestag --chunk_size 350 --indexer_job_run_name newtestag-k185 --data_source '{"type": "local", "credentials": null, "config": {"uri": "sample-data/creditcards"}}' --embedder_config '{"description": null, "provider": "OpenAI", "config": {"model": "text-embedding-ada-002"}}' --parser_config '{}' --vector_db_config '{"provider": "weaviate", "url": "https://test-f97pfm6u.weaviate.network", "api_key": null}'
```

# Development

# Folder structure
    .
    ├── backend                 # Source files for backend
    │   ├── indexer             # Files for indexer
    │   ├── modules             # Modules to support different functions
    │   ├── server              # Files for FastAPI server
    |   ├── utils               # Utils functions and base types
    |   ├── __init__.py         
    |   ├── Dockerfile          # Dockerfile for backedn
    │   ├── README.md           # Readme 
    |   ├── requirements.txt    
    │   └── settings.py         # Env validation and parsing           
    ├── venv                    # virtual env dir
    ├── .env                    # For local envs
    └── ...

# Modules

Modules are designed to support different functionalities like metadata_store, vector_db, embeddings, llms, parsers and data loaders
Each module can be extended by adding a subclass class of class defined in `__init__.py` of each folder.
Currently, we support following types in each module
- dataloaders - dataloaders are component responsible for loading data from `DataSource`. We have `mlfoundry`, `web`, `github` and `local` dataloaders
- embedder - embedder are component responsible for embedding functions used to index the documents into vector. We support all the embedding models available in TrueFoundry's LLM Gateway
- llms - llms contain various llm components. We support all the chat models available in TrueFoundry's LLM Gateway.
- metadara_store - used to store metadata of various collections like embedding used, chunk size, data source used, status of indexing. We are using `mlfoundry` ML repos, you can also use SQL for same
- parsers - parsers are component responsible for parsing data and chunking them based on file type. We have `markdown`, `pdf`, and `txt` support
- vector_db - used to store and query over vectors. We have `chroma`, `qdrant`, `weaviate`.

# Indexer

Indexer contains `indexer.py` that defines the steps for indexing and storing given data source to vector db. For running long indexing jobs, we give capability to run it as TrueFoundry `job` that is defined in `main.py`

# Server

Server contains `app.py` that defines API interface for the complete RAG system. Its built on `FastAPI` and out of the box exposes `swagger` (at path `/`) that can be used to test easily.