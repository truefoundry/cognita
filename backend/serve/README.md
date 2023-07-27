### Fastapi search server

The fastapi server provides the apis to search through the docs which the user previously indexed. Every indexing job has a repo_name and the user will provide a repo_name to refer to which repo they want to search through. The key apis exposed in the fastapi server are:

1. List indexed repos
2. Submit repo to index
3. Get status of submitted indexing job.
4. Search through the indexed repo

## Try it out!

To run the training job locally, follow the steps:

1. Open terminal on `/tfy-rag` folder

2. Create a python environment

```
python3 -m venv venv
source venv/bin/activate
```

3. Install packages required

```
pip install -r serve/requirements.txt
```

4. Set environment variables

```
export OPEN_API_KEY=
export ML_REPO= <ml repo>
export TF_API_KEY: <tf api key>
export LLM_ENDPOINT: <llm endpoint eg https://tenant.truefoundry.cloud/llm-playground/api/inference/text>
```

4. Run the script

```
uvicorn --host 0.0.0.0 --port 8000 backend.serve.app:app
```

You can also provide the embedder and the embedder parameters as part of the command above. The code can later be extended to support all the embedders along with their respective embedding configuration as provided in the Langchain library (https://python.langchain.com/en/latest/reference/modules/embeddings.html)
