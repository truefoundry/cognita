# Indexer
Indexer is a script used for indexing your documents and then pushing the data to Qdrant. The code has been written using async so that multiple documents can be indexed parallely. 

The code comprises of the following concepts:

1. **DataLoaders**: They are supposed to download the docs from a certain source and place it in the dest dir.
2. **Parsers**: One parser works for one kind of document. It is supposed to parse the document, split it and then return the chunks.
3. **Embedders**: They follow the same structure as provided in the langchain library.
4. **Qdrant**: We use Qdrant as the vector database to store the embeddings.

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
pip install -r train/requirements.txt
```

4. Set environment variables

```
export OPEN_API_KEY=
export TFY_API_KEY=<paste your api key here from https://app.truefoundry.com/settings?tab=api-keys >
```

4. Run the script

```
python -m train.train --chunk_size 800 --source_uri github://https://github.com/domoritz/streamlit-docker --repo_name test-repo
```

You can also provide the embedder and the embedder parameters as part of the command above. The code can later be extended to support all the embedders along with their respective embedding configuration as provided in the Langchain library (https://python.langchain.com/en/latest/reference/modules/embeddings.html)
