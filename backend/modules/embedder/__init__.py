from servicefoundry.langchain.truefoundry_embeddings import TrueFoundryEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from backend.modules.embedder.embedder import register_embedder
from backend.modules.embedder.mixbread_embedder import MixBreadEmbeddings

import os 

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if OPENAI_API_KEY:
    register_embedder("default", OpenAIEmbeddings)
else:
    register_embedder("default", TrueFoundryEmbeddings)
register_embedder("mixbread", MixBreadEmbeddings)
