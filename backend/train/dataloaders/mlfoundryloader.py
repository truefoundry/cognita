import os

import mlfoundry

from backend.common.common import unzip_file
from backend.common.logger import logger
from backend.train.dataloaders.loader import BaseLoader


class MlFoundryLoader(BaseLoader):
    """
    This loader handles mlfoundry artifact uris.
    The source_uri should be of the form: mlfoundry://<path_to_directory>
    """

    name = "MlFoundryLoader"
    supported_protocol = "mlfoundry://"

    def load_data(self, source_uri, dest_dir, credentials):
        if not source_uri.startswith(self.supported_protocol):
            raise Exception("This loader only supports mlfoundry:// protocol")
        artifact_fqn = source_uri.replace("mlfoundry://", "")
        mlfoundry_client = mlfoundry.get_client()
        logger.info("Downloading mlfoundry artifact: {}".format(artifact_fqn))
        artifact_version = mlfoundry_client.get_artifact(artifact_fqn)
        download_info = artifact_version.download(path=dest_dir)

        for file in os.listdir(download_info):
            f = os.path.join(download_info, file)
            if f.endswith(".zip"):
                unzip_file(f, download_info)
        logger.info("Downloaded artifact to: {}".format(dest_dir))
