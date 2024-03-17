# RAG Local Environment Setup

---

This file contains instructions for running the RAG application locally without any additional Truefoundry dependencies

### Repository Cloning and Environment Setup:

-   Clone the repo: `git clone https://github.com/truefoundry/docs-qa-playground.git`
-   Virtual Environment Creation:
    -   Create venv: `python -m venv ./venv`
    -   Activate venv: `source ./venv/bin/activate`
    -   Install required packages: `pip install -r requirements.txt`
    -   Install jupyter notebook: `pip install jupyter notebook`
-   Local version requires setting up `local.metadata.json` to be filled up

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

-   Setup Qdrant (Docker):
    -   `docker run -p 6333:6333 qdrant/qdrant -v $(pwd)/qdrant_storage:/qdrant/storage`
    -   This will run Qdrant at http://localhost:6333 ensure the same is present in the `VECTOR_DB_CONFIG` url (env file)
    -   Qdrant UI will be available at: `http://localhost:6333/dashboard`
-   Setup `.env` file

    -   Create a `.env` file or copy from `.env.sample`
    -   Enter the following values:

        ```env
        # For local setup
        METADATA_STORE_CONFIG='{"provider":"local","config":{"path":"local.metadata.json"}}'
        VECTOR_DB_CONFIG='{"provider":"qdrant","local":true, "url":"http://localhost:6333"}'

        TFY_API_KEY = <YOUR_TF_API_KEY>
        TFY_SERVICE_ROOT_PATH = '/'
        DEBUG_MODE = true
        LOG_LEVEL = "DEBUG"
        ```

-   Now the setup is done, you can run your RAG locally, an example notebook is provided by the name `RAG_local.ipynb`
