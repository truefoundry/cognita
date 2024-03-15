from backend.modules.embedder.embedder import register_embedder
from langchain_openai.embeddings import OpenAIEmbeddings

register_embedder("default", OpenAIEmbeddings)
