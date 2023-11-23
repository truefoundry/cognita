This directory contains the primary code for the backend including a FastAPI service and documents indexer job. The code can be run locally or deployed as a service and job on the Truefoundry platform.

### Running code locally

Prerequisite: follow [here](../../GETTING_STARTED.md) and fetch following values

```
OPENAI_API_KEY = 
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
python -m backend.indexer.main --collection_name newtestag --chunk_size 350 --indexer_job_run_name newtestag-k185 --knowledge_source '{"type": "mlfoundry", "credentials": null, "config": {"uri": "artifact:truefoundry/ag-test/newtestag_7a62e508-41f1-45ff-b49f-bf75a6afe4fa:1"}}' --embedder_config '{"description": null, "provider": "OpenAI", "config": {"model": "text-embedding-ada-002"}}' --parser_config '{}' --vector_db_config '{"provider": "weaviate", "url": "https://test-f97pfm6u.weaviate.network", "api_key": null}'
```

**Use local file as the data source**
```
python -m backend.indexer.main --collection_name newtestag --chunk_size 350 --indexer_job_run_name newtestag-k185 --knowledge_source '{"type": "local", "credentials": null, "config": {"uri": "sample-data/creditcards"}}' --embedder_config '{"description": null, "provider": "OpenAI", "config": {"model": "text-embedding-ada-002"}}' --parser_config '{}' --vector_db_config '{"provider": "weaviate", "url": "https://test-f97pfm6u.weaviate.network", "api_key": null}'
```