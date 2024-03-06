from backend.modules.embedder.embedder import register_embedder
from backend.modules.embedder.truefoundry_embedder import DefaultEmbeddings

register_embedder("truefoundry", DefaultEmbeddings)
