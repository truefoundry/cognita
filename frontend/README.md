### Streamlit Frontend

Streamlit app provides an interface to connect data, upload and trigger its training, and then allows asking questions.

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
pip install -r frontend/requirements.txt
```

4. Set environment variables

```
export ML_REPO=
export JOB_FQN=
export BACKEND_URL=<server url>
export TF_API_KEY=
export MODEL_CATALOGUE_ENDPOINT="https://app.devtest.truefoundry.tech/llm-playground/api/models-enabled"
```

4. Run the script

```
streamlit run --server.port 8000 frontend/main.py
```
