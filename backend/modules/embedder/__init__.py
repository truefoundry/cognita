from backend.modules.embedder.embedder import register_embedder
from langchain_openai.embeddings import OpenAIEmbeddings
from backend.modules.embedder.mixbread_embedder import MixBreadEmbeddings

register_embedder("default", OpenAIEmbeddings)
register_embedder("mixbread", MixBreadEmbeddings)
