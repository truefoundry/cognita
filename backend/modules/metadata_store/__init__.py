from backend.modules.metadata_store.mlfoundry import MLFoundry
from backend.modules.metadata_store.base import BaseMetadataStore

SUPPORTED_METADATA_STORES = {
    "mlfoundry": MLFoundry,
}


def get_metadata_store_client(type: str, *args, **kwargs) -> BaseMetadataStore:
    if type in SUPPORTED_METADATA_STORES:
        return SUPPORTED_METADATA_STORES[type](*args, **kwargs)
    else:
        raise ValueError(f"Unknown metadata store type: {type}")
