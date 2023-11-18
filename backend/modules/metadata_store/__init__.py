from backend.modules.metadata_store.mlfoundry import MLFoundryDB
from backend.modules.metadata_store.base import BaseMetadataStore

SUPPORTED_METADATA_STORES = {
    "mlfoundry": MLFoundryDB,
}


def get_metadata_store_client(type: str, *args, **kwargs) -> BaseMetadataStore:
    if type in SUPPORTED_METADATA_STORES:
        return SUPPORTED_METADATA_STORES[type](*args, **kwargs)
    else:
        raise ValueError(f"Unknown metadata store type: {type}")
