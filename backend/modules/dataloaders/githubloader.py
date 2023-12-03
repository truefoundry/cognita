import os
import re
from typing import List

from git import Repo

from backend.modules.dataloaders.loader import BaseLoader
from backend.utils.base import DocumentMetadata, LoadedDocument, SourceConfig
from backend.utils.logger import logger
from backend.utils.utils import generate_document_id


class GithubLoader(BaseLoader):
    """
    This loader handles Git repositories.
    """

    type = "github"

    def load_data(
        self, source_config: SourceConfig, dest_dir: str, allowed_extensions: List[str]
    ) -> List[LoadedDocument]:
        """
        Loads data from a Git repository specified by the given source URI. [supports public repository for now]

        Args:
            source_config (SourceConfig): The source URI of the Git repository.
            dest_dir (str): The destination directory where the repository will be cloned.
            allowed_extensions (List[str]): A list of allowed file extensions.

        Returns:
            List[LoadedDocument]: A list of LoadedDocument objects containing metadata.

        """
        if not self.is_valid_github_repo_url(source_config.uri):
            raise Exception("Invalid Github repo URL")

        # Clone the specified GitHub repository to the destination directory.
        logger.info("Cloning repo: %s", source_config.uri)
        Repo.clone_from(source_config.uri, dest_dir)
        logger.info("Git repo cloned successfully")

        docs: List[LoadedDocument] = []
        for root, d_names, f_names in os.walk(dest_dir):
            for f in f_names:
                if f.startswith("."):
                    continue
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, dest_dir)
                file_ext = os.path.splitext(f)[1]
                if file_ext not in allowed_extensions:
                    continue
                document_id = generate_document_id(
                    self.type, source_config.uri, rel_path
                )
                docs.append(
                    LoadedDocument(
                        filepath=full_path,
                        file_extension=file_ext,
                        metadata=DocumentMetadata(document_id=document_id),
                    )
                )

        return docs

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
