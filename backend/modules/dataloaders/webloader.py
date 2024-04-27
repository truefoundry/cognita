# Author: https://github.com/paulpierre/markdown-crawler/
# Description: A multithreaded web crawler that recursively crawls a website and creates a markdown file for each page.
import os
import tempfile
from typing import Dict, Iterator, List

from markdown_crawler import md_crawl

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint

DEFAULT_BASE_DIR = os.path.join(
    tempfile.gettempdir(), "webloader"
)  # temporary directory
DEFAULT_MAX_DEPTH = 2
DEFAULT_NUM_THREADS = 5
DEFAULT_TARGET_LINKS = ["body"]
DEFAULT_TARGET_CONTENT = ["article", "div", "main", "p"]
DEFAULT_DOMAIN_MATCH = True
DEFAULT_BASE_PATH_MATCH = True


class WebLoader(BaseDataLoader):
    """
    Load data from a web URL
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
        Loads data from a web URL and converts it to Markdown format.
        """

        md_crawl(
            base_url=data_source.uri,
            max_depth=DEFAULT_MAX_DEPTH,
            num_threads=DEFAULT_NUM_THREADS,
            base_dir=DEFAULT_BASE_DIR,
            target_links=DEFAULT_TARGET_LINKS,
            target_content=DEFAULT_TARGET_CONTENT,
            is_domain_match=DEFAULT_DOMAIN_MATCH,
            is_base_path_match=DEFAULT_BASE_PATH_MATCH,
        )
        logger.debug(
            f"WebLoader: Crawled {data_source.uri} and saved to {DEFAULT_BASE_DIR}"
        )

        loaded_data_points: List[LoadedDataPoint] = []
        dest_dir = DEFAULT_BASE_DIR
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
                    data_point_hash=str(os.path.getsize(full_path)),
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
