from backend.modules.metadata_store.base import BaseMetadataStore
from backend.modules.metadata_store.mlfoundry import MLFoundry
from backend.types import MetadataStoreConfig

SUPPORTED_METADATA_STORES = {
    "mlfoundry": MLFoundry,
}


def get_metadata_store_client(
    config: MetadataStoreConfig,
) -> BaseMetadataStore:
    if config.provider in SUPPORTED_METADATA_STORES:
        return SUPPORTED_METADATA_STORES[config.provider](config=config.config)
    else:
        raise ValueError(f"Unknown metadata store type: {config.provider}")
