import os , requests
from carbondataloader import Carbon
import shutil
from typing import Dict, Iterator, List

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint


api_key = os.get("")
customer_id = os.get("")

def download_file(url, local_filename):
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(local_filename, 'wb') as local_file:
            for chunk in response.iter_content(chunk_size=8192):
                local_file.write(chunk)
    return local_filename

class CarbonDataLoader(BaseDataLoader):
    """
    Load data from any  source that carbon ai supports 
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
       
        """
        carbon = Carbon(api_key=api_key,customer_id=customer_id)

        query_user_files_response = carbon.files.query_user_files(
            pagination={
                "limit": 10,
                "offset": 0,
            },
            order_by="created_at",
            order_dir="desc",
            filters={
                "organization_user_data_source_id": [data_source.uri]
                
            },
            include_raw_file=True,
            include_parsed_text_file=True,
            include_additional_files=True,
        )

        for file in query_user_files_response.results:
            url = file.presigned_url
            filename = file.name
            download_file(url, f"{dest_dir}/{filename}")

        
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