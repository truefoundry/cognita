import os
import time
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional

import requests
from pydantic import BaseModel, Field

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.settings import settings
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint

MAX_SYNC_ATTEMPTS = 5


class _FileStatistics(BaseModel):
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    file_format: Optional[str] = None


class _File(BaseModel):
    id: int
    name: str
    presigned_url: Optional[str] = None
    external_file_id: str
    sync_status: str
    source: str
    source_created_at: str
    file_statistics: Optional[_FileStatistics] = Field(default_factory=_FileStatistics)


class _UserFilesV2Response(BaseModel):
    results: List[_File]
    count: int


class SyncStatus(str, Enum):
    QUEUED = "QUEUED_FOR_SYNCING"
    SYNCING = "SYNCING"
    READY = "READY"
    ERROR = "SYNC_ERROR"


class _Connection(BaseModel):
    id: int
    data_source_external_id: str
    data_source_type: str
    sync_status: SyncStatus


class _SyncStatusResponse(BaseModel):
    results: List[_Connection]


class _CarbonClient:
    def __init__(self, api_key: str, customer_id: str):
        self.api_key = api_key
        self.customer_id = customer_id

    def _request(self, method: str, endpoint: str, **kwargs):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "customer-id": self.customer_id,
        }
        response = requests.request(method, endpoint, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    def check_sync_status(self, collection_id: str) -> bool:
        response = self._request(
            "POST",
            "https://api.carbon.ai/user_data_sources",
            json={"filters": {"ids": [collection_id]}},
        )

        data = _SyncStatusResponse.model_validate(response)

        if len(data.results) != 1:
            raise Exception(f"Data source {collection_id} not found")

        data = data.results[0]

        if data.sync_status == SyncStatus.ERROR:
            raise Exception(
                f"Syncing failed for data source {data.data_source_external_id}"
            )

        return data.sync_status == SyncStatus.READY

    def query_user_files(
        self,
        pagination: Optional[Dict[str, int]] = None,
        order_by: Optional[str] = None,
        order_dir: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_raw_file: Optional[Optional[bool]] = None,
        include_parsed_text_file: Optional[Optional[bool]] = None,
        include_additional_files: Optional[Optional[bool]] = None,
    ) -> Iterator[_File]:
        payload = {}
        if pagination is not None:
            payload["pagination"] = pagination
        if order_by is not None:
            payload["order_by"] = order_by
        if order_dir is not None:
            payload["order_dir"] = order_dir
        if filters is not None:
            payload["filters"] = filters
        if include_raw_file is not None:
            payload["include_raw_file"] = include_raw_file
        if include_parsed_text_file is not None:
            payload["include_parsed_text_file"] = include_parsed_text_file
        if include_additional_files is not None:
            payload["include_additional_files"] = include_additional_files

        total = -1
        count = 0

        while total == -1 or count < total:
            response = self._request(
                "POST", "https://api.carbon.ai/user_files_v2", json=payload
            )
            page = _UserFilesV2Response.model_validate(response)
            if total == -1:
                total = page.count
            for file in page.results:
                # TODO (chiragjn): There can be an edge case here where file.file_metadata.is_folder = True
                yield file
            count += len(page.results)
            payload["pagination"]["offset"] = count


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
        carbon_customer_id = data_source.metadata["customerId"]
        carbon_data_source_id = data_source.metadata["internalId"]
        carbon = _CarbonClient(
            api_key=settings.CARBON_AI_API_KEY,
            customer_id=carbon_customer_id,
        )

        attempts = 0

        while not carbon.check_sync_status(collection_id=carbon_data_source_id):
            if attempts >= MAX_SYNC_ATTEMPTS:
                raise Exception(
                    f"Data source {carbon_data_source_id} is not ready after {MAX_SYNC_ATTEMPTS} attempts, please check for partially failed files or wait and try again."
                )
            logger.info(
                f"Data source {carbon_data_source_id} is not ready yet. Retrying in 5 seconds"
            )
            time.sleep(5)
            attempts += 1

        user_files = carbon.query_user_files(
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

        for file in user_files:
            url = file.presigned_url
            filename = file.name
            file_id = file.external_file_id
            if file.file_statistics is None:
                logger.warning(f"File statistics missing for file {file_id}")
                continue
            mime_type = file.file_statistics.mime_type
            file_format = file.file_statistics.file_format

            # Convert CONFLUENCE file format to HTML or NOTION file format to JSON
            match file_format:
                case "CONFLUENCE":
                    filename += ".html"
                    file_format = "HTML"
                    mime_type = "text/html"

                case "NOTION":
                    filename += ".json"
                    file_format = "JSON"
                    mime_type = "application/json"

            _, file_extension = os.path.splitext(filename)

            # Replace spaces and slashes in the filename
            escaped_filename = filename.replace(" ", "_").replace("/", "-")
            local_filepath = os.path.join(dest_dir, f"{file_id}-{escaped_filename}")

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
                        "file_name": escaped_filename,
                        "file_format": file_format,
                        "mime_type": mime_type,
                        "created_at": file.source_created_at,
                        "file_url": f"CARBON::{file.id}",
                    },
                )
            )
            if len(loaded_data_points) >= batch_size:
                yield loaded_data_points
                loaded_data_points.clear()
        yield loaded_data_points
