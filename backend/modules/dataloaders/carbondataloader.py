import os
from typing import Dict, Iterator, List

import requests
from carbon import Carbon

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.settings import settings
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint


class CarbonDataLoader(BaseDataLoader):
    """
    Load data from variety of sources like Google Drive, Confluence, Notion and more
    """

    def _download_file(self, url: str, local_filepath: str, chunk_size: int = 8192):
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(local_filepath, "wb") as local_file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    local_file.write(chunk)
        return local_filepath

    def load_filtered_data(
        self,
        data_source: DataSource,
        dest_dir: str,
        previous_snapshot: Dict[str, str],
        batch_size: int,
        data_ingestion_mode: DataIngestionMode,
    ) -> Iterator[List[LoadedDataPoint]]:
        carbon_customer_id, carbon_data_source_id = data_source.uri.split("/")
        carbon = Carbon(
            api_key=settings.CARBON_AI_API_KEY,
            customer_id=carbon_customer_id,
        )

        query_user_files_response = carbon.files.query_user_files(
            pagination={
                "limit": 50,
                "offset": 0,
            },
            order_by="created_at",
            order_dir="desc",
            filters={"organization_user_data_source_id": [int(carbon_data_source_id)]},
            include_raw_file=True,
            include_parsed_text_file=False,
            include_additional_files=False,  # TODO (chiragjn): Evaluate later
        )

        loaded_data_points: List[LoadedDataPoint] = []

        for file in query_user_files_response.results:
            url = file.presigned_url
            filename = file.name
            file_id = file.external_file_id
            _, file_extension = os.path.splitext(filename)
            local_filepath = os.path.join(dest_dir, f"{file_id}-{filename}")
            logger.info(
                f"Downloading file {filename} from {file.source} data source type to {local_filepath}"
            )
            self._download_file(url=url, local_filepath=local_filepath)

            data_point_uri = f"{file.source}::{file.external_file_id}"
            data_point_hash = (
                f"{file.source_created_at}::{file.file_statistics.file_size or 0}"
            )

            data_point = DataPoint(
                data_source_fqn=data_source.fqn,
                data_point_uri=data_point_uri,
                data_point_hash=data_point_hash,
                local_filepath=local_filepath,
                file_extension=file_extension,
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
                    local_filepath=local_filepath,
                    file_extension=file_extension,
                    metadata={
                        "data_source_type": file.source,
                        "id": file.id,
                        "external_file_id": file.external_file_id,
                        "filename": filename,
                        "file_format": file.file_statistics.file_format,
                        "mime_type": file.file_statistics.mime_type,
                        "created_at": file.source_created_at,
                    },
                )
            )
            if len(loaded_data_points) >= batch_size:
                yield loaded_data_points
                loaded_data_points.clear()
        yield loaded_data_points
