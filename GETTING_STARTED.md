# Prerequisite

To be able to use RAG, follow the following steps:

1. Register at TrueFoundry and complete the basic setup, follow: https://docs.truefoundry.com/docs/installation-and-setup

2. Keep your dashboard URL handy, we will refer it as `TFY_HOST` and it should have structure like `https://<organization_name>.truefoundry.cloud`

3. Create a **ML Repo**, follow: 

4. Create a **Workspace** and give it access to created ML Repo, follow: 

5. Generate an **API Key**, follow: https://docs.truefoundry.com/docs/generate-api-key
    Note: we will refer it as `TFY_API_KEY`

6. Set Up your Embedder OR use OpenAI embedder. To use OpenAI embedder, please set the `OPENAI_API_KEY` as env. You can get your API Key [here](https://platform.openai.com/account/api-keys)

    ```
    export OPENAI_API_KEY=<paste your API key here>
    ```
# Try it Out!

### Indexer
    Refer [this](/backend/train/README.md)

### Serve
    Refer [this](/backend/serve/README.md)

### Frontend
    Refer [this](/frontend/README.md)

# Deploy
    Refer [this](/README.md)