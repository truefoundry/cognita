VectorDB

---

Vector DBs are used to store/retrive/compare embeddings for your documents.

To add your own interface for a VectorDB you can inhertit `BaseVectorDB` from `from backend.modules.vector_db.base.py`

Register the vectordb under `__init__.py`
