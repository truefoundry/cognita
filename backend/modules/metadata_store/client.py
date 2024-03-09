from backend.modules.metadata_store.base import get_metadata_store_client
from backend.settings import settings

METADATA_STORE_CLIENT = get_metadata_store_client(config=settings.METADATA_STORE_CONFIG)
