# QA on Docs

The repository follows the architecture below:

### Indexing Job
The user provides a repo_name, and the source of the documents and the indexing parameters. This triggers the train.py script in the train folder. 

To run the training job, use the command below:

`python -m backend.train.train --chunk_size 800 --source_uri github://https://github.com/domoritz/streamlit-docker --repo_name test-repo`

You can also provide the embedder and the embedder parameters as part of the command above. The code can later be extended to support all the embedders along with their respective embedding configuration as provided in the Langchain library (https://python.langchain.com/en/latest/reference/modules/embeddings.html)

The code has been written using async so that multiple documents can be indexed parallely. 

The code comprises of the following concepts:

1. **DataLoaders**: They are supposed to download the docs from a certain source and place it in the dest dir.
2. **Parsers**: One parser works for one kind of document. It is supposed to parse the document, split it and then return the chunks.
3. **Embedders**: They follow the same structure as provided in the langchain library.
4. **Qdrant**: We use Qdrant as the vector database to store the embeddings.  

We have already added dataloaders for local_dir, github_repo and mlfoundry_artifact. The commands to trigger the indexing job for each of them are:

` python -m backend.train.train --chunk_size 800 --source_uri mlfoundry://artifact:truefoundry/code-search-qa/calyx-docs:1 --repo_name test-repo`

`python -m backend.train.train --chunk_size 800 --source_uri github://https://github.com/domoritz/streamlit-docker --repo_name test-repo`

`python -m backend.train.train --chunk_size 800 --source_uri local://examples/calyx-docs --repo_name test-repo`

### Fastapi search server

The fastapi server provides the apis to search through the docs which the user previously indexed. Every indexing job has a repo_name and the user will provide a repo_name to refer to which repo they want to search through. The key apis exposed in the fastapi server are:

1. List indexed repos
2. Submit repo to index
3. Get status of submitted indexing job.
4. Search through the indexed repo

### Streamlit Frontend

Streamlit app provides an interface to connect data, upload and trigger its training, and then allows asking questions.

### Deploying on Truefoundry

1. Install **servicefoundry**
    `pip install servicefoundry`

2. Login at TrueFoundry
    `sfy login`

3. Create a workspace **docs-qa-llm** and a ml_repo **docs-qa** , then assign ml_repo access to the workspace
    
    ```sfy create workspace docs-qa-llm --cluster_name <cluster_name>```
    
    ###### create_ml_repo.py
    ```
    import mlfoundry as mlf

    client = mlfoundry.get_client()

    ml_repo = client.create_ml_repo(ml_repo="docs-qa")
    ```


2. Deploy Qdrant via Helm
    
    ```servicefoundry deploy --workspace_fqn <paste your workspace fqn here> --file qdrant.yaml --no-wait```

3. Indexing Job in `backend/train/`

    * Edit the indexer.yaml and add following environment variables
        
        ```
        env:
            ML_REPO: <ml repo>
            QDRANT_URL: <qdrant host eg qdrant.<workspace_name>.svc.cluster.local>
        ```

    * Deploy the job
        
        ```sfy deploy --workspace_fqn <paste your workspace fqn here> --file indexer.yaml```


4. Backend Service in `backend/serve/`

    * Edit serve.yaml and add the values of environment variables
        
        ```
        env:
            ML_REPO: <ml repo>
            QDRANT_URL: <qdrant host eg qdrant.<workspace_name>.svc.cluster.local>
            TF_API_KEY: <tf api key>
            LLM_ENDPOINT: <llm endpoint eg https://tenant.truefoundry.cloud/llm-playground/api/inference/text>
        ...
        ```

    * Deploy using python sdk
    
        ```sfy deploy --workspace_fqn <paste your workspace fqn here> --file serve.yaml```

5. Streamlit Frontend in `frontend/`

    * Edit frontend.yaml and add the value of host for your frontend

        ```
        ports:
        - host: <host for frontend>
        ...
        ```

    * Edit frontend.yaml and add the values of environment variables mentioned in .env.example
        
        ```
        env:
            JOB_FQN: <tfy_llm_qa_in>
            ML_REPO: <ml_repo_name>
            TF_API_KEY: <secret_fqn>
            BACKEND_URL: <tfy_llm_qa_backend_url>
            MODEL_CATALOGUE_ENDPOINT: <control_plane_url>/llm-playground/api/models-enabled
        ...
        ```

    *  Deploy using python sdk
        
        ```sfy deploy --workspace_fqn <paste your workspace fqn here>```
