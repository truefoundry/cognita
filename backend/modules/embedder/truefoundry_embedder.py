from servicefoundry.langchain import TrueFoundryEmbeddings

from backend.modules.embedder.embedder import register_embedder

register_embedder("truefoundry", TrueFoundryEmbeddings)
