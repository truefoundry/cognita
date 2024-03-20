from servicefoundry.langchain.truefoundry_embeddings import TrueFoundryEmbeddings

from backend.modules.embedder.embedder import register_embedder

register_embedder("default", TrueFoundryEmbeddings)
