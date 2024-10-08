from backend.modules.metadata_store.base import register_metadata_store
from backend.modules.metadata_store.prisma_store import PrismaStore

register_metadata_store("prisma", PrismaStore)
