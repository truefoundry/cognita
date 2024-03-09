import os
import re
from typing import Dict, Iterator, List

from git import Repo

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint


class GithubLoader(BaseDataLoader):
    """
    This loader handles Git repositories.
    """

    def load_data_point(
        self,
        data_source: DataSource,
        dest_dir: str,
        data_point: DataPoint,
    ) -> LoadedDataPoint:
        raise NotImplementedError("Method not implemented")

    def load_filtered_data_points_from_data_source(
        self,
        data_source: DataSource,
        dest_dir: str,
        existing_data_point_fqn_to_hash: Dict[str, str],
        batch_size: int,
        data_ingestion_mode: DataIngestionMode,
    ) -> Iterator[List[LoadedDataPoint]]:
        """
        Loads data from a Git repository specified by the given source URI. [supports public repository for now]
        """
        if not self.is_valid_github_repo_url(data_source.uri):
            raise Exception("Invalid Github repo URL")

        # Clone the specified GitHub repository to the destination directory.
        logger.info("Cloning repo: %s", data_source.uri)
        Repo.clone_from(data_source.uri, dest_dir)
        logger.info("Git repo cloned successfully")

        loaded_data_points: List[LoadedDataPoint] = []
        for root, d_names, f_names in os.walk(dest_dir):
            for f in f_names:
                if f.startswith("."):
                    continue
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, dest_dir)
                file_ext = os.path.splitext(f)[1]
                data_point = DataPoint(
                    data_source_fqn=data_source.fqn,
                    data_point_uri=rel_path,
                    data_point_hash=f"{os.path.getsize(full_path)}",
                )

                # If the data ingestion mode is incremental, check if the data point already exists.
                if (
                    data_ingestion_mode == DataIngestionMode.INCREMENTAL
                    and existing_data_point_fqn_to_hash.get(data_point.data_point_fqn)
                    and existing_data_point_fqn_to_hash.get(data_point.data_point_fqn)
                    == data_point.data_point_hash
                ):
                    continue

                loaded_data_points.append(
                    LoadedDataPoint(
                        data_point_hash=data_point.data_point_hash,
                        data_point_uri=data_point.data_point_uri,
                        data_source_fqn=data_point.data_source_fqn,
                        local_filepath=full_path,
                        file_extension=file_ext,
                    )
                )
                if len(loaded_data_points) >= batch_size:
                    yield loaded_data_points
                    loaded_data_points.clear()
        yield loaded_data_points

    def is_valid_github_repo_url(self, url):
        """
        Checks if the provided URL is a valid GitHub repository URL.

        Args:
            url (str): The URL to be checked.

        Returns:
            bool: True if the URL is a valid GitHub repository URL, False otherwise.
        """
        pattern = r"^(?:https?://)?github\.com/[\w-]+/[\w.-]+/?$"
        return re.match(pattern, url) is not None
