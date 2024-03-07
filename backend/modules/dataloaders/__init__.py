from backend.modules.dataloaders.githubloader import GithubLoader
from backend.modules.dataloaders.loader import register_dataloader
from backend.modules.dataloaders.localdirloader import LocalDirLoader
from backend.modules.dataloaders.mlfoundryloader import MlFoundryLoader
from backend.modules.dataloaders.webloader import WebLoader
from backend.modules.dataloaders.artifactloader import ArtifactLoader

register_dataloader("github", GithubLoader)
register_dataloader("local", LocalDirLoader)
register_dataloader("web", WebLoader)
register_dataloader("mlfoundry", MlFoundryLoader)
register_dataloader("artifact", ArtifactLoader)
