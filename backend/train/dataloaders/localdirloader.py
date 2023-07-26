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
        if not source_uri.startswith(self.supported_protocol):
            raise Exception("This loader only supports local:// protocol")
        source_dir = source_uri.replace("local://", "")
        # check if source_dir is relative path or absolute path
        if not os.path.isabs(source_dir):
            source_dir = os.path.join(os.getcwd(), source_dir)
        if not os.path.exists(source_dir):
            raise Exception("Source directory does not exist")

        # if source dir and dest dir are same, then do nothing
        logger.info("source_dir: %s", source_dir)
        logger.info("dest_dir: %s", dest_dir)
        if source_dir == dest_dir:
            return
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
