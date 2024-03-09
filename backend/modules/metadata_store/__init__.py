from backend.modules.metadata_store.base import register_metadata_store
from backend.modules.metadata_store.local import LocalMetadataStore
from backend.modules.metadata_store.mlfoundry import MLFoundry

register_metadata_store("mlfoundry", MLFoundry)
register_metadata_store("local", LocalMetadataStore)
