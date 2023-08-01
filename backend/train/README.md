This directory contains the primary code for the documents indexer job. The code can be run locally or deployed
as a job on the Truefoundry platform.

### Running code locally

Prerequisite: follow [here](../../GETTING_STARTED.md) and fetch following values

```
TFY_API_KEY
TFY_HOST
OPENAI_API_KEY
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
pip install -r backend/train/requirements.txt
```

4. Set environment variables

Copy the file .env.example to .env and set the values for the following variables. This is assuming we will be using OpenAI for the embeddings and LLM initially.

```
OPEN_API_KEY=<paste your OpenAI API key here>
TFY_API_KEY=<paste your TFY_API_KEY>
TFY_HOST=<paste your TFY_HOST>
```

5. Run the script

```
python -m backend.train.train --source_uri local://sample-data/mlops-pdf --repo_name test-repo --dry_run
```

To see other options you can customize, you can type:

```
python -m backend.train.train -h
```

### Extending the code for your own datasets

This can be relevant if you plan to edit the code to suit your own usecases. You can also try to run the
code as it is and evaluate the performance before making any changes.

The indexing code accepts the source of the documents as an input and then indexes the documents. The code comes with default parsers for different types of files like pdf, md, txt. The code also supports using OpenAI or other
Truefoundry deployed embedding models. The indexer job uses Qdrant as the vector database which has worked out pretty well for most usecases and also seems to [perform quite well compared](https://qdrant.tech/benchmarks/?gad=1&gclid=CjwKCAjwzo2mBhAUEiwAf7wjkiDRHpZK4sUynT1JQqwyDWO48q_0P1rWaXdh2IpAXqFRLAEpd4KO4RoCq1sQAvD_BwE) to some of the other vector databases.

The code is organized in the following way:

1. **DataLoaders**: The dataloaders load the data from different sources like localdir, github, mlfoundry. The dataloaders download the documents and place it in the dest dir (repo-data by default)
2. **Parsers**: One parser works for one kind of document. It is supposed to parse the document, split it and then return the chunks.
3. **Embedders**: Embedders have the job of generating embeddings from the chunks. Currently the code supports OpenAI and Truefoundry hosted embedding models.
4. **Qdrant**: We use Qdrant as the vector database to store the embeddings.

We use [mlfoundry](https://docs.truefoundry.com/docs/ml-repo-quickstart) as the metadata-store for storing the metadata of the indexing jobs. For each run, the indexer creates a MLFoundry run and automatically stores the input embedding configuration and documents source.

### Indexing Job

The user provides a repo_name, and the source of the documents and the indexing parameters. This triggers the train.py script in the train folder.

To run the training job, use the command below:

- Using OpenAI for embedding model

```
python -m backend.train.train --chunk_size 800 --source_uri github://https://github.com/domoritz/streamlit-docker --repo_name test-repo
```

- Using self hosted model deployed on TrueFoundry

```
python -m backend.train.train --ml_repo docs-qa-llm --chunk_size 1000 --repo_name merck-testing-test1 --source_uri local:///home/jovyan/examples/pdf-docs --dry_run False --embedder TruefoundryEmbeddings --embedder_config '{
    "endpoint_url": "https://<embedding_model_endpoint>",
    "batch_size": 16,
    "parallel_workers": 12
}' --repo_creds '' --parsers_map '{".md": "MarkdownParser", ".pdf": "PdfParserFast", ".py": "PythonCodeParser", ".txt": "TextParser"}'
```

You can also provide the embedder and the embedder parameters as part of the command above. The code can later be extended to support all the embedders along with their respective embedding configuration as provided in the Langchain library (https://python.langchain.com/en/latest/reference/modules/embeddings.html)

The code has been written using async so that multiple documents can be indexed parallely.

The code comprises of the following concepts:

1. **DataLoaders**: They are supposed to download the docs from a certain source and place it in the dest dir.
2. **Parsers**: One parser works for one kind of document. It is supposed to parse the document, split it and then return the chunks.
3. **Embedders**: They follow the same structure as provided in the langchain library.
4. **Qdrant**: We use Qdrant as the vector database to store the embeddings.

We have already added dataloaders for mlfoundry_artifact, github_repo and local_dir. The commands to trigger the indexing job for each of them are:

```
python -m backend.train.train --chunk_size 100 --source_uri mlfoundry://<artifact_fqn> --repo_name test-repo
```

```
python -m backend.train.train --chunk_size 100 --source_uri github://https://github.com/domoritz/streamlit-docker --repo_name test-repo
```

```
python -m backend.train.train --chunk_size 100 --source_uri local://sample-data/mlops-pdf --repo_name test-repo
```
