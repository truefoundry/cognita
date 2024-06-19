import os
import shutil
from pathlib import Path
from typing import Dict, Iterator, List

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint


class LocalDirLoader(BaseDataLoader):
    """
    Load data from a local directory
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
        Loads data from a local directory specified by the given source URI.
        """
        # Data source URI is the path of the local directory.
        source_dir = data_source.uri

        # Check if the source_dir is a relative path or an absolute path.
        if not os.path.isabs(source_dir):
            logger.info("source_dir is a relative path")
            source_dir = os.path.join(os.getcwd(), source_dir)

        logger.info(
            f"CURRENT DIR:{os.getcwd()}, Path exists: {os.path.exists(source_dir)}, Dir contents: {os.listdir(source_dir)}"
        )
        # Check if the source directory exists.
        if not os.path.exists(source_dir):
            raise Exception("Source directory does not exist")

        # If the source directory and destination directory are the same, do nothing.
        logger.info("source_dir: %s", source_dir)
        logger.info("dest_dir: %s", dest_dir)
        if source_dir == dest_dir:
            # Temrinate the function
            return

        def copy(src, dst):
            if os.path.islink(src):
                linkto = os.readlink(src)
                os.symlink(linkto, dst)
            else:
                shutil.copyfile(src, dst, follow_symlinks=True)

        # Copy the entire directory (including subdirectories) from source to destination.
        shutil.copytree(
            source_dir, dest_dir, dirs_exist_ok=True, symlinks=False, copy_function=copy
        )

        logger.info(f"Dest dir contents: {os.listdir(dest_dir)}")

        loaded_data_points: List[LoadedDataPoint] = []
        for root, d_names, f_names in os.walk(dest_dir):
            for f in f_names:
                if f.startswith("."):
                    continue
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, dest_dir)
                file_ext = os.path.splitext(f)[1]
                logger.info(
                    f"full_path: {full_path}, rel_path: {rel_path}, file_ext: {file_ext}"
                )
                data_point = DataPoint(
                    data_source_fqn=data_source.fqn,
                    data_point_uri=rel_path,
                    data_point_hash=str(os.lstat(full_path)),
                    local_filepath=full_path,
                    file_extension=file_ext,
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
