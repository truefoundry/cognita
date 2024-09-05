from backend.modules.metadata_store.base import register_metadata_store
from backend.modules.metadata_store.prismastore import PrismaStore

register_metadata_store("prisma", PrismaStore)
