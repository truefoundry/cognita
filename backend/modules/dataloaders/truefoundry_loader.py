import os
from typing import Dict, Iterator, List

from truefoundry.ml import get_client as get_tfy_client

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint
from backend.utils import unzip_file


class TrueFoundryLoader(BaseDataLoader):
    """
    Load data from a TrueFoundry data source (data-dir).
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
        Loads data from a truefoundry data directory with FQN specified by the given source URI.
        """
        tfy_files_dir = None

        # Check if the data source type is data-dir. Other data source types are not supported with TrueFoundry.
        if not data_source.uri.startswith("data-dir"):
            raise ValueError(f"Unsupported data source type {data_source.uri}")

        # Since only data-dir is allowed, we can directly use the FQN to get the data directory.
        try:
            # Log into TrueFoundry
            tfy_client = get_tfy_client()
            # Data source URI contains the Truefoundry FQN(Fully Qualified Name) of the data directory.
            # Use the FQN to get the data directory from TrueFoundry.
            dataset = tfy_client.get_data_directory_by_fqn(data_source.uri)
            # Download the data directory to the destination directory.
            tfy_files_dir = dataset.download(path=dest_dir)
            logger.debug(f"Data directory download info: {tfy_files_dir}")
        except Exception as e:
            logger.error(f"Error downloading data directory: {str(e)}")
            raise ValueError(f"Failed to download data directory: {str(e)}")

        # If tfy_files_dir is None, it means the data was not downloaded.
        if tfy_files_dir is None:
            logger.error("Download info not found")
            return iter([])

        if os.path.exists(os.path.join(tfy_files_dir, "files")):
            logger.debug("Files directory exists")
            tfy_files_dir = os.path.join(tfy_files_dir, "files")
            logger.debug(f"[Updated] download info: {tfy_files_dir} for data-dir")

        # If the downloaded data directory is a ZIP file, unzip its contents.
        for file_name in os.listdir(tfy_files_dir):
            logger.debug(f"file_name: {file_name}")
            # If the file is a ZIP file, unzip its contents.
            if file_name.endswith(".zip"):
                logger.debug(
                    f"Unzipped file_path: {os.path.join(tfy_files_dir, file_name)}"
                )
                unzip_file(
                    file_path=os.path.join(tfy_files_dir, file_name),
                    dest_dir=tfy_files_dir,
                )

        logger.info("Downloaded data to: {}".format(dest_dir))

        # Initialize the list of loaded data points.
        loaded_data_points: List[LoadedDataPoint] = []

        # Walk through the downloaded data directory and process each file.
        for root, _dirs, files in os.walk(tfy_files_dir):
            for f in files:
                # Skip hidden files.
                if f.startswith("."):
                    continue
                full_path = os.path.join(root, f)
                logger.debug(f"Processing file: {full_path}")
                rel_path = os.path.relpath(full_path, dest_dir)
                file_ext = os.path.splitext(f)[1]
                # Create a DataPoint object for the current file.
                data_point = DataPoint(
                    data_source_fqn=data_source.fqn,
                    data_point_uri=rel_path,
                    data_point_hash=f"{os.path.getsize(full_path)}:{dataset.updated_at}",
                )

                # If the data ingestion mode is incremental, check if the data point already exists.
                if (
                    data_ingestion_mode == DataIngestionMode.INCREMENTAL
                    and previous_snapshot.get(data_point.data_point_fqn)
                    == data_point.data_point_hash
                ):
                    continue

                # Add the data point to the list of loaded data points.
                loaded_data_points.append(
                    LoadedDataPoint(
                        data_point_hash=data_point.data_point_hash,
                        data_point_uri=data_point.data_point_uri,
                        data_source_fqn=data_point.data_source_fqn,
                        local_filepath=full_path,
                        file_extension=file_ext,
                    )
                )
                # If the number of loaded data points is greater than or equal to the batch size, yield the loaded data points.
                if len(loaded_data_points) >= batch_size:
                    yield loaded_data_points
                    loaded_data_points.clear()

        # Yield the remaining loaded data points.
        yield loaded_data_points
