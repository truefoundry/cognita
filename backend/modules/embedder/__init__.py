from servicefoundry.langchain.truefoundry_embeddings import TrueFoundryEmbeddings

from backend.modules.embedder.embedder import register_embedder
from backend.modules.embedder.mixbread_embedder import MixBreadEmbeddings

register_embedder("default", TrueFoundryEmbeddings)
register_embedder("mixbread", MixBreadEmbeddings)
