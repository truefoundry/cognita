import os
from typing import Dict, Iterator, List

import mlfoundry

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint
from backend.utils import unzip_file


class ArtifactLoader(BaseDataLoader):
    """
    This loader handles mlfoundry artifact fqn
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
        Loads data from an MLFoundry artifact with FQN specified by the given source URI.
        """
        client = mlfoundry.get_client()

        # uri is the artifcat fqn that includes the version number
        artifact_fqn = data_source.uri

        # Get information about the data directory and download it to the destination directory.
        logger.info("Downloading Artifact: {}".format(artifact_fqn))

        # Get the artifact version directly
        artifact_version = client.get_artifact_version_by_fqn(artifact_fqn)

        # download it to disk
        # `download_path` points to a directory that has all contents of the artifact
        download_path = artifact_version.download(path=dest_dir)
        logger.debug(f"Artifact data directory download info: {download_info}")

        if os.path.exists(os.path.join(download_info, "files")):
            logger.debug("Files directory exists")
            download_info = os.path.join(download_info, "files")
            logger.debug(f"[Updated] Artifact data directory download info: {download_info}")

        # If the downloaded data directory is a ZIP file, unzip its contents.
        for file_name in os.listdir(download_path):
            if file_name.endswith(".zip"):
                unzip_file(
                    file_path=os.path.join(download_path, file_name),
                    dest_dir=download_path,
                )

        logger.info("Downloaded data directory to: {}".format(dest_dir))

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
                    data_point_hash=f"{os.path.getsize(full_path)}:{artifact_version.updated_at}",
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
