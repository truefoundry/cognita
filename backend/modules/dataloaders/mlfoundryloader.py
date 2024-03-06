import os
import tempfile
from typing import List

import mlfoundry

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseLoader
from backend.modules.metadata_store.base import generate_document_id
from backend.types import (DataPoint, DataSource, DocumentMetadata,
                           LoadedDocument)
from backend.utils import unzip_file


class MlFoundryLoader(BaseLoader):
    """
    This loader handles mlfoundry data directory fqn.
    """

    type = "mlfoundry"

    def list_data_points(self, data_source: DataSource) -> List[DataPoint]:
        """
        List the data points from the source.

        Args:
            data_source (DataSource): The data source from which the data points are to be listed.

        Returns:
            List[DataPoint]: The list of data points.
        """
        mlfoundry_client = mlfoundry.get_client()
        dataset = mlfoundry_client.get_data_directory_by_fqn(data_source.uri)
        with tempfile.TemporaryDirectory() as tmpdirname:
            download_info = dataset.download(path=tmpdirname)
            data_directory_files = os.path.join(download_info, "files")
            # If the downloaded data directory is a ZIP file, unzip its contents.
            for file_name in os.listdir(data_directory_files):
                if file_name.endswith(".zip"):
                    unzip_file(
                        file_path=os.path.join(data_directory_files, file_name),
                        dest_dir=data_directory_files,
                    )

            logger.info("Downloaded data directory to: {}".format(tmpdirname))

            docs: List[LoadedDocument] = []
            for root, d_names, f_names in os.walk(tmpdirname):
                for f in f_names:
                    if f.startswith("."):
                        continue
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, tmpdirname)
                    file_ext = os.path.splitext(f)[1]
                    docs.append(
                        DataPoint(
                            data_point_uri=rel_path,
                            data_source_fqn=data_source.uri,
                        )
                    )

        return [
            LoadedDocument(
                filepath=file_info.path,
                file_extension=os.path.splitext(file_info.path)[1],
                metadata=DocumentMetadata(
                    _document_id=generate_document_id(
                        data_source=data_source, path=file_info.path
                    )
                ),
            )
            for file_info in dataset.files
        ]

    def load_data(
        self, data_source: DataSource, dest_dir: str, allowed_extensions: List[str]
    ) -> List[LoadedDocument]:
        """
        Loads data from an MLFoundry data directory specified by the given source URI.

        Args:
            data_source (DataSource): Data directory FQN (data-dir:truefoundry/llama-finetune-test/akash-test).
            dest_dir (str): The destination directory where the data directory will be downloaded to.
            allowed_extensions (List[str]): A list of allowed file extensions.

        Returns:
            List[LoadedDocument]: A list of LoadedDocument objects containing metadata.
        """

        mlfoundry_client = mlfoundry.get_client()

        # Get information about the data directory and download it to the destination directory.
        logger.info("Downloading MLFoundry data directory: {}".format(data_source.uri))
        dataset = mlfoundry_client.get_data_directory_by_fqn(data_source.uri)
        dataset.list_files()
        download_info = dataset.download(path=dest_dir)
        data_directory_files = os.path.join(download_info, "files")
        # If the downloaded data directory is a ZIP file, unzip its contents.
        for file_name in os.listdir(data_directory_files):
            if file_name.endswith(".zip"):
                unzip_file(
                    file_path=os.path.join(data_directory_files, file_name),
                    dest_dir=data_directory_files,
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
