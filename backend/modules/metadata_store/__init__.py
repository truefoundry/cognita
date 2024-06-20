from backend.modules.metadata_store.base import register_metadata_store
from backend.modules.metadata_store.truefoundry import TrueFoundry
from backend.settings import settings

register_metadata_store("truefoundry", TrueFoundry)

# import of PrismaStore only for Local environment
if settings.LOCAL:
    from backend.modules.metadata_store.prismastore import PrismaStore

    register_metadata_store("prisma", PrismaStore)
