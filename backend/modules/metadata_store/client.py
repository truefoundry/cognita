# from backend.modules.metadata_store.base import get_metadata_store_client
# from backend.settings import settings

# METADATA_STORE_CLIENT = get_metadata_store_client(config=settings.METADATA_STORE_CONFIG)

### BREAKING CHANGE!!
# TODO: WOULD NEED TO MODIFY QUERY CONTROLLER TO USE THIS CLIENT

METADATA_STORE_CLIENT = None


from backend.modules.metadata_store.base import get_metadata_store_client
from backend.settings import settings


async def get_client():
    client = await get_metadata_store_client(config=settings.METADATA_STORE_CONFIG)
    return client


# Instantiate the client
