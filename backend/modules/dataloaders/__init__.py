from backend.modules.dataloaders.artifactloader import ArtifactLoader
from backend.modules.dataloaders.githubloader import GithubLoader
from backend.modules.dataloaders.loader import register_dataloader
from backend.modules.dataloaders.localdirloader import LocalDirLoader
from backend.modules.dataloaders.mlfoundryloader import MlFoundryLoader
from backend.modules.dataloaders.webloader import WebLoader
from backend.modules.dataloaders.tfdocsloader import TFDocsArtifactLoader

register_dataloader("local", LocalDirLoader)
register_dataloader("mlfoundry", MlFoundryLoader)
register_dataloader("artifact", ArtifactLoader)
register_dataloader("web", WebLoader)
register_dataloader("github", GithubLoader)
register_dataloader("tfdocs-artifact", TFDocsArtifactLoader)
