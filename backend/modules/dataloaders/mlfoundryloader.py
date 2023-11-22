import os

import mlfoundry

from backend.modules.dataloaders.loader import BaseLoader
from backend.utils.logger import logger
from backend.utils.utils import unzip_file


class MlFoundryLoader(BaseLoader):
    """
    This loader handles mlfoundry artifact uris.
    The source_uri should be of the form: mlfoundry://<path_to_directory>
    """

    type = "mlfoundry"

    def load_data(self, source_uri, dest_dir):
        """
        Loads data from an MLFoundry artifact specified by the given source URI.

        Args:
            source_uri (str): The source URI of the MLFoundry artifact (mlfoundry://<artifact_version_fqn>).
            dest_dir (str): The destination directory where the artifact will be downloaded to.

        Returns:
            None
        """

        artifact_version_fqn = source_uri
        mlfoundry_client = mlfoundry.get_client()

        # Get information about the artifact version and download it to the destination directory.
        logger.info("Downloading MLFoundry artifact: {}".format(artifact_version_fqn))
        artifact_version = mlfoundry_client.get_artifact_version_by_fqn(
            artifact_version_fqn
        )
        download_info = artifact_version.download(path=dest_dir)

        # If the downloaded artifact is a ZIP file, unzip its contents.
        for file in os.listdir(download_info):
            f = os.path.join(download_info, file)
            if f.endswith(".zip"):
                unzip_file(f, download_info)

        logger.info("Downloaded artifact to: {}".format(dest_dir))
