Run Production Level RAG in Local Environment

---

Follow the instructions to setup Truefoundry environment from `docs/TFSETUP.md`

1. Run the indexer to index the data into vectordb

```
python -m backend.indexer.main --collection_name "test0403" --data_source_fqn "mlfoundry::data-dir:truefoundry/tfy-docs-rag/tfycc1" --raise_error_on_failure "False"
```

    -  `--collection_name` will be the collection you use
    -  `--data_source_fqn` will be the FQN of datasource either from DataDirectory or Artifact of Truefoundry.

2. Run the Server

```
uvicorn --host 0.0.0.0 --port 8080 backend.server.app:app --reload
```
