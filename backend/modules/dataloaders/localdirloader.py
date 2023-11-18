import os
import shutil
from backend.logger import logger
from backend.modules.dataloaders.loader import BaseLoader


class LocalDirLoader(BaseLoader):
    """
    This loader handles local directories.
    The source_uri should be of the form: local://<path_to_directory>
    """

    type = "local"

    def load_data(self, source_uri, dest_dir):
        """
        Loads data from a local directory specified by the given source URI.

        Args:
            source_uri (str): The source URI of the local directory (local://path_to_directory).
            dest_dir (str): The destination directory where the data will be copied to.

        Returns:
            None
        """
        source_dir = source_uri

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
