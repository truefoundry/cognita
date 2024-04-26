from backend.modules.metadata_store.base import register_metadata_store
from backend.settings import settings
from backend.modules.metadata_store.local import LocalMetadataStore
from backend.modules.metadata_store.truefoundry import TrueFoundry

if settings.LOCAL:
    register_metadata_store("local", LocalMetadataStore)
register_metadata_store("truefoundry", TrueFoundry)
