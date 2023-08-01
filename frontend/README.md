### Streamlit Frontend

Streamlit app provides an interface to connect data, upload and trigger its training, and then allows asking questions.

### Running code locally

To run the training job locally, follow the steps:

1. Go to the parent directory (`tfy-rag/`)

```
cd ..
```

2. Create a python environment

```
python3 -m venv venv
source venv/bin/activate
```

3. Install packages required

```
pip install -r frontend/requirements.txt
```

4. Set environment variables

```
export ML_REPO=
export JOB_FQN=
export BACKEND_URL=<server url>
export TFY_API_KEY=
export TFY_HOST="https://<organization>.truefoundry.cloud"
```

4. Run the script

```
streamlit run --server.port 8000 frontend/main.py
```

# Deploy Using truefoundry

### Deploying a new Version

1. Install servicefoundry library

```
pip install servicefoundry --upgrade
```

2. Login into servicefoundry

```
servicefoundry login --host https://example.domain.com
```

3. Edit servicefoundry.yaml and add the values of environment variables mentioned in .env.example

```
env:
  JOB_FQN: <tfy_llm_qa_fqn>
  ML_REPO: <ml_repo_name>
  TFY_API_KEY: <secret_fqn>
  BACKEND_URL: <tfy_llm_qa_backend_url>
  TFY_HOST: <control_plane_url>
...
```

3. Deploy using python sdk

```
sfy deploy --workspace_fqn <paste your workspace fqn here>
```

You will find the workspace fqn at in the workpace section.

You can read more about deploying a service at: https://docs.truefoundry.com/docs/deploying-your-first-service
