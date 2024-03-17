# RAG Local Environment Setup

---

This file contains instructions for running the RAG application locally without any additional Truefoundry dependencies

### Repository Cloning and Environment Setup:

-   Clone the repo: `git clone https://github.com/truefoundry/docs-qa-playground.git`
-   Virtual Environment Creation:
    -   Create venv: `python -m venv ./venv`
    -   Activate venv: `source ./venv/bin/activate`
    -   Install required packages: `pip install -r requirements.txt`
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

-   Setup `.env` file

    -   Create a `.env` file or copy from `.env.sample`
    -   Enter the following values:

        ```env
        # For local setup
        METADATA_STORE_CONFIG='{"provider":"local","config":{"path":"local.metadata.yaml"}}'
        VECTOR_DB_CONFIG='{"provider":"qdrant","local":true}'

        TFY_API_KEY = <YOUR_TF_API_KEY>
        TFY_SERVICE_ROOT_PATH = '/'
        DEBUG_MODE = true
        LOG_LEVEL = "DEBUG"
        ```

    -   You can also provide `OPENAI_API_KEY` here.

-   Now the setup is done, you can run your RAG locally, an example python script is provided by the name `local_rag.py`. The script has code for ingesting data into vector db and answering the query.
