import os
from typing import Dict, Iterator, List

from truefoundry import ml

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint
from backend.utils import unzip_file


class TrueFoundryLoader(BaseDataLoader):
    """
    Load data from a TrueFoundry data source (data-dir / artifact).
    """

    def load_filtered_data(
        self,
        data_source: DataSource,
        dest_dir: str,
        previous_snapshot: Dict[str, str],
        batch_size: int,
        data_ingestion_mode: DataIngestionMode,
    ) -> Iterator[List[LoadedDataPoint]]:
        """
        Loads data from a truefoundry data directory / artifact with FQN specified by the given source URI.
        """
        truefoundry_client = ml.get_client()
        artifact_files_dir = None
        datasource_type = None

        if data_source.uri.startswith("artifact"):
            datasource_type = "artifact"
            # uri should be the artifcat fqn that includes the version number
            artifact_fqn = data_source.uri
            # Get information about the data directory and download it to the destination directory.
            logger.info("Downloading Artifact: {}".format(artifact_fqn))

            # Get the artifact version directly
            dataset = truefoundry_client.get_artifact_version_by_fqn(artifact_fqn)
            # download it to disk
            # `artifact_files_dir` points to a directory that has all contents of the artifact
            artifact_files_dir = dataset.download(path=dest_dir)
            logger.debug(f"Artifact download info: {artifact_files_dir}")

        elif data_source.uri.startswith("data-dir"):
            datasource_type = "data-dir"
            # Data source URI is the FQN of the data directory.
            dataset = truefoundry_client.get_data_directory_by_fqn(data_source.uri)
            artifact_files_dir = dataset.download(path=dest_dir)
            logger.debug(f"Data directory download info: {artifact_files_dir}")

        else:
            raise ValueError(f"Unsupported data_source uri type {data_source.uri}")

        if artifact_files_dir:
            if os.path.exists(os.path.join(artifact_files_dir, "files")):
                logger.debug("Files directory exists")
                artifact_files_dir = os.path.join(artifact_files_dir, "files")
                logger.debug(
                    f"[Updated] download info: {artifact_files_dir} for {datasource_type}"
                )

            # If the downloaded data directory is a ZIP file, unzip its contents.
            for file_name in os.listdir(artifact_files_dir):
                logger.debug(f"file_name: {file_name}")
                if file_name.endswith(".zip"):
                    logger.debug(
                        f"Unzipped file_path: {os.path.join(artifact_files_dir, file_name)}"
                    )
                    unzip_file(
                        file_path=os.path.join(artifact_files_dir, file_name),
                        dest_dir=artifact_files_dir,
                    )

            logger.info("Downloaded data to: {}".format(dest_dir))

            loaded_data_points: List[LoadedDataPoint] = []

            for root, d_names, f_names in os.walk(artifact_files_dir):
                for f in f_names:
                    if f.startswith("."):
                        continue
                    full_path = os.path.join(root, f)
                    logger.debug(f"Processing file: {full_path}")
                    rel_path = os.path.relpath(full_path, dest_dir)
                    file_ext = os.path.splitext(f)[1]
                    data_point = DataPoint(
                        data_source_fqn=data_source.fqn,
                        data_point_uri=rel_path,
                        data_point_hash=f"{os.path.getsize(full_path)}:{dataset.updated_at}",
                    )

                    # If the data ingestion mode is incremental, check if the data point already exists.
                    if (
                        data_ingestion_mode == DataIngestionMode.INCREMENTAL
                        and previous_snapshot.get(data_point.data_point_fqn)
                        and previous_snapshot.get(data_point.data_point_fqn)
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
        else:
            logger.error("Download info not found")
            return iter([])
