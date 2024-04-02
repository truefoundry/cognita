import os
from typing import Dict, Iterator, List

import mlfoundry

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint
from backend.utils import unzip_file


class MlFoundryLoader(BaseDataLoader):
    """
    This loader handles mlfoundry data directory fqn.
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
        Loads data from a mlfoundry data directory with FQN specified by the given source URI.
        """
        self.mlfoundry_client = mlfoundry.get_client()
        # Data source URI is the FQN of the data directory.
        dataset = self.mlfoundry_client.get_data_directory_by_fqn(data_source.uri)

        download_info = dataset.download(path=dest_dir)
        logger.debug(f"Mlfoundry data directory download info: {download_info}")

        if os.path.exists(os.path.join(download_info, "files")):
            logger.debug("Files directory exists")
            download_info = os.path.join(download_info, "files")
            logger.debug(f"[Updated] Mlfoundry data directory download info: {download_info}")

        
        
        # If the downloaded data directory is a ZIP file, unzip its contents.
        for file_name in os.listdir(download_info):
            logger.debug(f"file_name: {file_name}")
            if file_name.endswith(".zip"):
                logger.debug(f"Unzipped file_path: {os.path.join(download_info, file_name)}")
                unzip_file(
                    file_path=os.path.join(download_info, file_name),
                    dest_dir=download_info,
                )

        logger.info("Downloaded data directory to: {}".format(dest_dir))

        loaded_data_points: List[LoadedDataPoint] = []

        for root, d_names, f_names in os.walk(dest_dir):
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
