import re

from git import Repo

from backend.common.logger import logger
from backend.train.dataloaders.loader import BaseLoader


class GithubLoader(BaseLoader):
    """
    This loader handles Git repositories.
    The source_uri should be of the form: github://github_repo_url
    """

    name = "GithubLoader"
    supported_protocol = "github://"

    def load_data(self, source_uri, dest_dir, credentials):
        if not source_uri.startswith(self.supported_protocol):
            raise Exception("This loader only supports github:// protocol")

        github_repo_url = source_uri.replace("github://", "")
        if not self.is_valid_github_repo_url(github_repo_url):
            raise Exception("Invalid Github repo URL")

        # TODO: Handle git credentials
        logger.info("Cloning repo: %s", github_repo_url)
        Repo.clone_from(github_repo_url, dest_dir)
        logger.info("Git repo cloned successfully")

    def is_valid_github_repo_url(self, url):
        pattern = r"^(?:https?://)?github\.com/[\w-]+/[\w.-]+/?$"
        return re.match(pattern, url) is not None
