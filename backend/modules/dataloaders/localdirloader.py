import os
import shutil
from typing import List

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseLoader
from backend.types import DocumentMetadata, LoadedDocument, SourceConfig
from backend.utils import generate_document_id


class LocalDirLoader(BaseLoader):
    """
    This loader handles local directories.
    """

    type = "local"

    def load_data(
        self, source_config: SourceConfig, dest_dir: str, allowed_extensions: List[str]
    ) -> List[LoadedDocument]:
        """
        Loads data from a local directory specified by the given source URI.

        Args:
            source_config (SourceConfig): The source URI of the local directory.
            dest_dir (str): The destination directory where the data will be copied to.
            allowed_extensions (List[str]): A list of allowed file extensions.

        Returns:
            List[LoadedDocument]: A list of LoadedDocument objects containing metadata.
        """
        source_dir = source_config.uri

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
                    self.type, source_config.uri, rel_path
                )
                docs.append(
                    LoadedDocument(
                        filepath=full_path,
                        file_extension=file_ext,
                        metadata=DocumentMetadata(_document_id=_document_id),
                    )
                )

        return docs
