from backend.modules.metadata_store.base import get_metadata_store_client
from backend.settings import settings

METADATA_STORE_CLIENT = None


async def get_client():
    global METADATA_STORE_CLIENT
    if METADATA_STORE_CLIENT is None:
        METADATA_STORE_CLIENT = await get_metadata_store_client(
            config=settings.METADATA_STORE_CONFIG
        )
    return METADATA_STORE_CLIENT
