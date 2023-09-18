import os
import shutil

from backend.common.logger import logger
from backend.train.dataloaders.loader import BaseLoader


class LocalDirLoader(BaseLoader):
    """
    This loader handles local directories.
    The source_uri should be of the form: local://<path_to_directory>
    """

    name = "LocalDirLoader"
    supported_protocol = "local://"

    def load_data(self, source_uri, dest_dir, credentials):
        """
        Loads data from a local directory specified by the given source URI.

        Args:
            source_uri (str): The source URI of the local directory (local://path_to_directory).
            dest_dir (str): The destination directory where the data will be copied to.
            credentials (dict): Optional credentials (currently not used, left for future implementation).

        Returns:
            None
        """
        if not source_uri.startswith(self.supported_protocol):
            raise Exception("This loader only supports local:// protocol")
        source_dir = source_uri.replace("local://", "")

        # Check if the source_dir is a relative path or an absolute path.
        if not os.path.isabs(source_dir):
            source_dir = os.path.join(os.getcwd(), source_dir)

        # Check if the source directory exists.
        if not os.path.exists(source_dir):
            raise Exception("Source directory does not exist")

        # If the source directory and destination directory are the same, do nothing.
        logger.info("source_dir: %s", source_dir)
        logger.info("dest_dir: %s", dest_dir)
        if source_dir == dest_dir:
            return

        # Copy the entire directory (including subdirectories) from source to destination.
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
