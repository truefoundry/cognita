from backend.modules.vector_db import get_vector_db_client
from backend.settings import settings

VECTOR_STORE_CLIENT = get_vector_db_client(config=settings.VECTOR_DB_CONFIG)
