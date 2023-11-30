import os
from typing import List

import mlfoundry

from backend.modules.dataloaders.loader import BaseLoader
from backend.utils.base import DocumentMetadata, LoadedDocument
from backend.utils.logger import logger
from backend.utils.utils import generate_uri, unzip_file


class MlFoundryLoader(BaseLoader):
    """
    This loader handles mlfoundry data directory fqn.
    """

    type = "mlfoundry"

    def load_data(
        self, source_uri: str, dest_dir: str, allowed_extensions: List[str]
    ) -> List[LoadedDocument]:
        """
        Loads data from an MLFoundry data directory specified by the given source URI.

        Args:
            source_uri (str): Data directory FQN (data-dir:truefoundry/llama-finetune-test/akash-test).
            dest_dir (str): The destination directory where the data directory will be downloaded to.
            allowed_extensions (List[str]): A list of allowed file extensions.

        Returns:
            List[LoadedDocument]: A list of LoadedDocument objects containing metadata.
        """

        mlfoundry_client = mlfoundry.get_client()

        # Get information about the data directory and download it to the destination directory.
        logger.info("Downloading MLFoundry data directory: {}".format(source_uri))
        dataset = mlfoundry_client.get_data_directory_by_fqn(source_uri)
        download_info = dataset.download(path=dest_dir)

        # If the downloaded data directory is a ZIP file, unzip its contents.
        for file in os.listdir(download_info):
            f = os.path.join(download_info, file)
            if f.endswith(".zip"):
                unzip_file(f, download_info)

        logger.info("Downloaded data directory to: {}".format(dest_dir))

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
                uri = generate_uri(self.type, source_uri, rel_path)
                docs.append(
                    LoadedDocument(
                        file_path=full_path,
                        ext=file_ext,
                        metadata=DocumentMetadata(uri=uri),
                    )
                )

        return docs
