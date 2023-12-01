import os
from typing import List

import mlfoundry
from mlfoundry.artifact.truefoundry_artifact_repo import (
    ArtifactIdentifier,
    MlFoundryArtifactsRepository,
)

from backend.modules.dataloaders.loader import BaseLoader
from backend.settings import settings
from backend.utils.base import DocumentMetadata, LoadedDocument, SourceConfig
from backend.utils.logger import logger
from backend.utils.utils import generate_uri, unzip_file


class MlFoundryLoader(BaseLoader):
    """
    This loader handles mlfoundry data directory fqn.
    """

    type = "mlfoundry"

    def get_presigned_urls_for_write(
        self, data_dir_name: str, filepaths: List[str]
    ) -> List[dict]:
        """
        Uploads data to an MLFoundry data directory using Presigned URLs.

        Args:
            data_dir_name (str): The name of the data directory.
            filepaths (List[str]): The paths to the file to be uploaded.
        """

        mlfoundry_client = mlfoundry.get_client()

        # Create a new data directory.
        logger.info("Creating MLFoundry data directory: {}".format(data_dir_name))
        dataset = mlfoundry_client.create_data_directory(
            settings.ML_REPO_NAME, data_dir_name
        )

        artifact_repo = MlFoundryArtifactsRepository(
            artifact_identifier=ArtifactIdentifier(dataset_fqn=dataset.fqn),
            mlflow_client=mlfoundry_client.mlflow_client,
        )
        urls = artifact_repo.get_signed_urls_for_write(
            artifact_identifier=ArtifactIdentifier(dataset_fqn=dataset.fqn),
            paths=filepaths,
        )
        return [url.dict() for url in urls]

    def load_data(
        self, source_config: SourceConfig, dest_dir: str, allowed_extensions: List[str]
    ) -> List[LoadedDocument]:
        """
        Loads data from an MLFoundry data directory specified by the given source URI.

        Args:
            source_config (SourceConfig): Data directory FQN (data-dir:truefoundry/llama-finetune-test/akash-test).
            dest_dir (str): The destination directory where the data directory will be downloaded to.
            allowed_extensions (List[str]): A list of allowed file extensions.

        Returns:
            List[LoadedDocument]: A list of LoadedDocument objects containing metadata.
        """

        mlfoundry_client = mlfoundry.get_client()

        # Get information about the data directory and download it to the destination directory.
        logger.info(
            "Downloading MLFoundry data directory: {}".format(source_config.uri)
        )
        dataset = mlfoundry_client.get_data_directory_by_fqn(source_config.uri)
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
                uri = generate_uri(self.type, source_config.uri, rel_path)
                docs.append(
                    LoadedDocument(
                        filepath=full_path,
                        file_extension=file_ext,
                        metadata=DocumentMetadata(uri=uri),
                    )
                )

        return docs
