from backend.modules.dataloaders.githubloader import GithubLoader
from backend.modules.dataloaders.loader import register_dataloader
from backend.modules.dataloaders.localdirloader import LocalDirLoader
from backend.modules.dataloaders.truefoundryloader import TrueFoundryLoader
from backend.modules.dataloaders.webloader import WebLoader
from backend.modules.dataloaders.confluenceloader import ConfluenceLoader
from backend.settings import settings

register_dataloader("localdir", LocalDirLoader)
register_dataloader("web", WebLoader)
register_dataloader("github", GithubLoader)
if settings.TFY_API_KEY:
    register_dataloader("truefoundry", TrueFoundryLoader)

if settings.CONFLUENCE_API_TOKEN:
    register_dataloader("confluence", ConfluenceLoader)
