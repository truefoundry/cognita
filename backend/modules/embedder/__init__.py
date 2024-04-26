from backend.modules.embedder.embedder import register_embedder
from backend.settings import settings

from truefoundry.langchain import TrueFoundryEmbeddings

if settings.OPENAI_API_KEY:
    from langchain.embeddings.openai import OpenAIEmbeddings
    register_embedder("openai", OpenAIEmbeddings)

register_embedder("truefoundry", TrueFoundryEmbeddings)

if settings.LOCAL:
    from backend.modules.embedder.mixbread_embedder import MixBreadEmbeddings
    register_embedder("mixedbread", MixBreadEmbeddings)
