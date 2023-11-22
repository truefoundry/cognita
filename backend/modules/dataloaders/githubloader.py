import re

from git import Repo

from backend.modules.dataloaders.loader import BaseLoader
from backend.utils.logger import logger


class GithubLoader(BaseLoader):
    """
    This loader handles Git repositories.
    The source_uri should be of the form: github://github_repo_url
    """

    type = "github"

    def load_data(self, source_uri, dest_dir):
        """
        Loads data from a Git repository specified by the given source URI. [supports public repository for now]

        Args:
            source_uri (str): The source URI of the Git repository (github://github_repo_url).
            dest_dir (str): The destination directory where the repository will be cloned.

        Returns:
            None
        """
        if not self.is_valid_github_repo_url(source_uri):
            raise Exception("Invalid Github repo URL")

        # Clone the specified GitHub repository to the destination directory.
        logger.info("Cloning repo: %s", source_uri)
        Repo.clone_from(source_uri, dest_dir)
        logger.info("Git repo cloned successfully")

    def is_valid_github_repo_url(self, url):
        """
        Checks if the provided URL is a valid GitHub repository URL.

        Args:
            url (str): The URL to be checked.

        Returns:
            bool: True if the URL is a valid GitHub repository URL, False otherwise.
        """
        pattern = r"^(?:https?://)?github\.com/[\w-]+/[\w.-]+/?$"
        return re.match(pattern, url) is not None
