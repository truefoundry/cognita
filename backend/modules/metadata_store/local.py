import random
import string
from typing import List

import yaml
from pydantic import BaseModel

from backend.logger import logger
from backend.modules.embedder.embedder import get_embedder
from backend.modules.metadata_store.base import BaseMetadataStore, get_data_source_fqn
from backend.modules.vector_db.client import VECTOR_STORE_CLIENT
from backend.settings import settings
from backend.types import (
    AssociateDataSourceWithCollection,
    AssociatedDataSources,
    Collection,
    CreateDataIngestionRun,
    CreateDataSource,
    DataIngestionRun,
    DataIngestionRunStatus,
    DataSource,
    EmbedderConfig,
    ParserConfig,
)


class LocalMetadata(BaseModel):
    collection_name: str
    embedder_config: EmbedderConfig
    data_source: CreateDataSource
    parser_config: ParserConfig


class LocalMetadataStore(BaseMetadataStore):
    local_metadata: LocalMetadata
    collection: Collection
    data_sources: DataSource
    parser_config: ParserConfig
    data_ingestion_runs: List[DataIngestionRun]

    def __init__(self, config: dict):
        self.path = config.get("path")
        if not self.path:
            raise ValueError("path is required for local metadata store")
        with open(self.path) as f:
            data = yaml.safe_load(f)
            self.local_metadata = LocalMetadata.parse_obj(data)
        self.data_source = DataSource(
            type=self.local_metadata.data_source.type,
            uri=self.local_metadata.data_source.uri,
            metadata=self.local_metadata.data_source.metadata,
        )
        self.fqn = self.data_source.fqn
        self.parser_config = self.local_metadata.parser_config
        associated_data_sources = {}
        associated_data_sources[self.data_source.fqn] = AssociatedDataSources(
            data_source_fqn=self.data_source.fqn,
            parser_config=self.parser_config,
            data_source=self.data_source,
        )
        self.collection = Collection(
            name=self.local_metadata.collection_name,
            embedder_config=self.local_metadata.embedder_config,
            associated_data_sources=associated_data_sources,
        )

        get_collection = VECTOR_STORE_CLIENT.get_collections()
        if not self.local_metadata.collection_name in get_collection:
            VECTOR_STORE_CLIENT.create_collection(
                collection_name=self.local_metadata.collection_name,
                embeddings=get_embedder(self.local_metadata.embedder_config),
            )
            self.data_ingestion_runs = []
            logger.debug(f"Local metadata store initialized with {self.local_metadata}")
        else:
            logger.debug(
                f"Collection {self.local_metadata.collection_name} already present in local"
            )

        self.data_ingestion_runs = []

    def create_collection(self, collection) -> Collection:
        return self.collection

    def get_collection_by_name(
        self, collection_name: str = None, no_cache: bool = True
    ) -> Collection | None:
        return self.collection

    def get_collections(
        self,
    ) -> List[Collection]:
        return [self.collection]

    def create_data_source(self, data_source: CreateDataSource) -> DataSource:
        return self.data_source

    def get_data_source_from_fqn(self, fqn: str = None) -> DataSource | None:
        return self.data_source

    def get_data_sources(self) -> List[DataSource]:
        return [self.data_source]

    def associate_data_source_with_collection(
        self,
        collection_name: str,
        data_source_association: AssociateDataSourceWithCollection,
    ) -> Collection:
        return self.collection

    def unassociate_data_source_with_collection(
        self,
        collection_name: str,
        data_source_fqn: str,
    ) -> Collection:
        return self.collection

    def create_data_ingestion_run(
        self, data_ingestion_run: CreateDataIngestionRun
    ) -> DataIngestionRun:
        random_name = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
        created_data_ingestion_run = DataIngestionRun(
            name=random_name,
            collection_name=data_ingestion_run.collection_name,
            data_source_fqn=data_ingestion_run.data_source_fqn,
            parser_config=data_ingestion_run.parser_config,
            data_ingestion_mode=data_ingestion_run.data_ingestion_mode,
            status=DataIngestionRunStatus.INITIALIZED,
            raise_error_on_failure=data_ingestion_run.raise_error_on_failure,
        )
        self.data_ingestion_runs.append(created_data_ingestion_run)
        return created_data_ingestion_run

    def get_data_ingestion_run(
        self, data_ingestion_run_name: str, no_cache: bool = False
    ) -> DataIngestionRun | None:
        return next(
            (
                data_ingestion_run
                for data_ingestion_run in self.data_ingestion_runs
                if data_ingestion_run.name == data_ingestion_run_name
            ),
            None,
        )

    def get_data_ingestion_runs(
        self, collection_name: str, data_source_fqn: str = None
    ) -> List[DataIngestionRun]:
        return self.data_ingestion_runs

    def delete_collection(self, collection_name: str, include_runs=False):
        self.collection = None
        self.data_ingestion_runs = []

    def update_data_ingestion_run_status(
        self,
        data_ingestion_run_name: str,
        status: DataIngestionRunStatus,
    ):
        data_ingestion_run = self.get_data_ingestion_run(data_ingestion_run_name)
        logger.info(
            f"Updating status of data ingestion run {data_ingestion_run_name} to {status}"
        )

    def log_metrics_for_data_ingestion_run(
        self,
        data_ingestion_run_name: str,
        metric_dict: dict[str, int | float],
        step: int = 0,
    ):
        logger.info(f"Logging metrics for data ingestion run {data_ingestion_run_name}")
        logger.info(f"step: {step}, metric_dict: {metric_dict}")

    def log_errors_for_data_ingestion_run(self, data_ingestion_run_name: str, errors):
        logger.info(f"Logging errors for data ingestion run {data_ingestion_run_name}")
        logger.info(f"errors: {errors}")
