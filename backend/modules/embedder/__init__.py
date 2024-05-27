from truefoundry.langchain import TrueFoundryEmbeddings

from backend.modules.embedder.embedder import register_embedder
from backend.modules.embedder.embedding_svc import InfinityEmbeddingSvc
from backend.settings import settings

if settings.OPENAI_API_KEY:
    from langchain.embeddings.openai import OpenAIEmbeddings

    register_embedder("openai", OpenAIEmbeddings)

register_embedder("truefoundry", TrueFoundryEmbeddings)

# Using embedding th' a deployed service such as Infinity API
register_embedder("embedding-svc", InfinityEmbeddingSvc)

# Register the MixBreadEmbeddings class if required
# from backend.modules.embedder.mixbread_embedder import MixBreadEmbeddings
# register_embedder("mixbread", MixBreadEmbeddings)
