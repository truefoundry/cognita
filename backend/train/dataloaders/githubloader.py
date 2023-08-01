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
        """
        Loads data from a Git repository specified by the given source URI. [supports public repository for now]

        Args:
            source_uri (str): The source URI of the Git repository (github://github_repo_url).
            dest_dir (str): The destination directory where the repository will be cloned.
            credentials (dict): Optional credentials (currently not used, left for future implementation).

        Returns:
            None
        """
        if not source_uri.startswith(self.supported_protocol):
            raise Exception("This loader only supports github:// protocol")

        github_repo_url = source_uri.replace("github://", "")
        if not self.is_valid_github_repo_url(github_repo_url):
            raise Exception("Invalid Github repo URL")

        # TODO: Handle git credentials (currently not used)

        # Clone the specified GitHub repository to the destination directory.
        logger.info("Cloning repo: %s", github_repo_url)
        Repo.clone_from(github_repo_url, dest_dir)
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
