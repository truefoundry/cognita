import os
from typing import Dict, Iterator, List
from unstructured.ingest.connector.confluence import (
    ConfluenceAccessConfig,
    SimpleConfluenceConfig,
)
from unstructured.ingest.interfaces import (
    PartitionConfig,
    ProcessorConfig,
    ReadConfig,
    ChunkingConfig,
)
from unstructured.ingest.runner import ConfluenceRunner

from backend.logger import logger
from backend.settings import settings
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint


class ConfluenceLoader(BaseDataLoader):
    """
    Load data from a Confluence instance using unstructured's ConfluenceConnector
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
        Loads data from a Confluence instance specified by the given source URI.
        """
        confluence_url = data_source.uri

        runner = ConfluenceRunner(
            processor_config=ProcessorConfig(
                verbose=True,
                output_dir=dest_dir,
                num_processes=2,
            ),
            read_config=ReadConfig(),
            partition_config=PartitionConfig(
                metadata_exclude=[
                    "filename",
                    "file_directory",
                    "metadata.data_source.date_processed",
                ],
            ),
            chunking_config=ChunkingConfig(
                chunk_elements=True,
                chunking_strategy="by_title",
                max_characters=1500,  # Set maximum characters per chunk
                overlap=300,  # Set overlap between chunks
                combine_text_under_n_chars=1500,  # Combine small sections
            ),
            connector_config=SimpleConfluenceConfig(
                access_config=ConfluenceAccessConfig(
                    api_token=settings.CONFLUENCE_API_TOKEN,
                ),
                user_email=settings.CONFLUENCE_USER_EMAIL,
                url=confluence_url,
                max_num_of_docs_from_each_space=5000,  # Adjust as needed
            ),
        )

        # Run the Confluence runner
        logger.info("Starting Confluence data ingestion with chunking")
        runner.run()
        logger.info("Confluence data ingestion and chunking completed")

        loaded_data_points: List[LoadedDataPoint] = []
        for root, _, files in os.walk(dest_dir):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, dest_dir)
                file_size = os.path.getsize(full_path)

                data_point = DataPoint(
                    data_source_fqn=data_source.fqn,
                    data_point_uri=relative_path,
                    data_point_hash=f"{file_size}",
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
                        file_extension=os.path.splitext(file)[1],
                    )
                )

                if len(loaded_data_points) >= batch_size:
                    yield loaded_data_points
                    loaded_data_points.clear()

        if loaded_data_points:
            yield loaded_data_points
