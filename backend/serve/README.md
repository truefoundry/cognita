This directory contains the primary code for the fastapi service that has APIs to perform the following actions:

1. Ask questions over an already indexed document repository.
2. Index a new document repository.
3. List all the indexed document repositories.
4. Get the status of an indexing job.

### Running code locally

Prerequisite: [here](../../GETTING_STARTED.md)

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
pip install -r backend/serve/requirements.txt
```

4. Set environment variables

Copy the file .env.example to .env and set the values for the following variables. This is assuming we will be using OpenAI for the embeddings and LLM.

```
OPEN_API_KEY=<paste your OpenAI API key here to use OpenAI embedders>
TFY_API_KEY=<paste your api key here from https://<organization>.truefoundry.cloud/settings?tab=api-keys >
TFY_HOST=<dashboard endpoint eg https://tenant.truefoundry.cloud>
```

5. Run the script

```
uvicorn --host 0.0.0.0 --port 8000 backend.serve.app:app --reload
```

6. Check out the APIs on the browser at `http://localhost:8000`

### Deploying on Truefoundry

Go to root directory of this repository and type:

```
sfy deploy --workspace_fqn <paste your workspace fqn here> --file serve.yaml
```

> To figure out how to get workspace fqn, please check: [here](../../GETTING_STARTED.md)

### Extending and modifying the code

You probably don't need to modify the fastapi code.