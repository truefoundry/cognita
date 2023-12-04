from backend.modules.metadata_store.base import BaseMetadataStore
from backend.modules.metadata_store.console_store import ConsoleStore
from backend.modules.metadata_store.mlfoundry_store import MLFoundryStore

SUPPORTED_METADATA_STORES = {"mlfoundry": MLFoundryStore, "console": ConsoleStore}


def get_metadata_store_client(type: str, *args, **kwargs) -> BaseMetadataStore:
    if type in SUPPORTED_METADATA_STORES:
        return SUPPORTED_METADATA_STORES[type](*args, **kwargs)
    else:
        raise ValueError(f"Unknown metadata store type: {type}")
