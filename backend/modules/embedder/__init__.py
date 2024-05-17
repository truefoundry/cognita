from truefoundry.langchain import TrueFoundryEmbeddings

from backend.modules.embedder.embedder import register_embedder
from backend.settings import settings

if settings.OPENAI_API_KEY:
    from langchain.embeddings.openai import OpenAIEmbeddings

    register_embedder("openai", OpenAIEmbeddings)

register_embedder("truefoundry", TrueFoundryEmbeddings)

if settings.LOCAL:
    from backend.modules.embedder.mixbread_embedder import MixBreadEmbeddings

    register_embedder("mixedbread", MixBreadEmbeddings)

from backend.modules.embedder.embedding_svc import EmbeddingSvc

register_embedder("embedding-svc", EmbeddingSvc)
