import os
from typing import List

import mlfoundry

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseLoader
from backend.modules.metadata_store.base import generate_document_id
from backend.types import DataSource, DocumentMetadata, LoadedDocument
from backend.utils import unzip_file


class ArtifactLoader(BaseLoader):
    """
    This loader handles mlfoundry artifact fqn
    """

    def load_data(
        self, data_source: DataSource, dest_dir: str, allowed_extensions: List[str]
    ) -> List[LoadedDocument]:
        """
        Loads data from an MLFoundry data directory specified by the given source URI.

        Args:
            data_source (DataSource): Artifact FQN (artifact:truefoundry/prathamesh-merck/test:1).
            dest_dir (str): The destination directory where the data directory will be downloaded to.
            allowed_extensions (List[str]): A list of allowed file extensions.

        Returns:
            List[LoadedDocument]: A list of LoadedDocument objects containing metadata.
        """
        client = mlfoundry.get_client()
        
        # If user has given given FQN for datasrc either in uri or fqn
        uri = None
        if data_source.uri:
            uri = data_source.uri
        if data_source.fqn:
            uri = data_source.fqn

        # Get information about the data directory and download it to the destination directory.
        logger.info("Downloading Artifact: {}".format(uri))

        # Get the artifact version directly
        artifact_version = client.get_artifact_version_by_fqn(uri)

        # download it to disk
        # `download_path` points to a directory that has all contents of the artifact
        download_path = artifact_version.download(path=dest_dir)

        # If the downloaded data directory is a ZIP file, unzip its contents.
        for file_name in os.listdir(download_path):
            if file_name.endswith(".zip"):
                unzip_file(
                    file_path=os.path.join(download_path, file_name),
                    dest_dir=download_path,
                )

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
                _document_id = generate_document_id(
                    data_source=data_source, path=rel_path
                )
                docs.append(
                    LoadedDocument(
                        filepath=full_path,
                        file_extension=file_ext,
                        metadata=DocumentMetadata(_document_id=_document_id),
                    )
                )

        return docs


