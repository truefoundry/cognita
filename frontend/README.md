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
