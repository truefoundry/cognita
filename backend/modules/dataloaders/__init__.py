from backend.modules.dataloaders.loader import register_dataloader
from backend.modules.dataloaders.local_dir_loader import LocalDirLoader
from backend.modules.dataloaders.web_loader import WebLoader
from backend.settings import settings

register_dataloader("localdir", LocalDirLoader)
register_dataloader("web", WebLoader)
if settings.TFY_API_KEY:
    from backend.modules.dataloaders.truefoundry_loader import TrueFoundryLoader

    register_dataloader("truefoundry", TrueFoundryLoader)
