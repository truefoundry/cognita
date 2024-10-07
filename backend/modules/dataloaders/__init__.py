from backend.modules.dataloaders.loader import register_dataloader
from backend.modules.dataloaders.localdirloader import LocalDirLoader
from backend.modules.dataloaders.webloader import WebLoader
from backend.settings import settings

register_dataloader("localdir", LocalDirLoader)
register_dataloader("web", WebLoader)
if settings.TFY_API_KEY:
    from backend.modules.dataloaders.truefoundryloader import TrueFoundryLoader

    register_dataloader("truefoundry", TrueFoundryLoader)
