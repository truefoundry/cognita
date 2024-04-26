from truefoundry.langchain import TrueFoundryEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from backend.modules.embedder.embedder import register_embedder
from backend.modules.embedder.mixbread_embedder import MixBreadEmbeddings
from backend.settings import settings


if settings.OPENAI_API_KEY:
    register_embedder("openai", OpenAIEmbeddings)
register_embedder("truefoundry", TrueFoundryEmbeddings)
if settings.LOCAL:
    register_embedder("mixedbread", MixBreadEmbeddings)
