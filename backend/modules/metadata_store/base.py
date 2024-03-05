from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.types import (
    AssociateDataSourceWithCollectionDto,
    Collection,
    CreateCollection,
    CreateDataIngestionRun,
    CreateDataSource,
    DataIngestionRun,
    DataIngestionRunStatus,
    DataSource,
)

DOCUMENT_ID_SEPARATOR = "::"

class BaseMetadataStore(ABC):
    @abstractmethod
    def create_collection(self, collection: CreateCollection) -> Collection:
        """
        Create a collection in the metadata store
        """
        raise NotImplementedError()

    @abstractmethod
    def get_collection_by_name(
        self, collection_name: str, no_cache: bool = False
    ) -> Collection | None:
        """
        Get a collection from the metadata store by name
        """
        raise NotImplementedError()

    @abstractmethod
    def get_collections(
        self,
    ) -> List[Collection]:
        """
        Get all collections from the metadata store
        """
        raise NotImplementedError()

    @abstractmethod
    def create_data_source(self, data_source: CreateDataSource) -> DataSource:
        """
        Create a data source in the metadata store
        """
        raise NotImplementedError()

    @abstractmethod
    def get_data_source_from_fqn(self, fqn: str) -> DataSource | None:
        """
        Get a data source from the metadata store by fqn
        """
        raise NotImplementedError()

    @abstractmethod
    def get_data_sources(self) -> List[DataSource]:
        """
        Get all data sources from the metadata store
        """
        raise NotImplementedError()

    @abstractmethod
    def create_data_ingestion_run(
        self, data_ingestion_run: CreateDataIngestionRun
    ) -> DataIngestionRun:
        """
        Create a data ingestion run in the metadata store
        """
        raise NotImplementedError()

    @abstractmethod
    def get_data_ingestion_run(
        self, data_ingestion_run_name: str, no_cache: bool = False
    ) -> DataIngestionRun | None:
        """
        Get a data ingestion run from the metadata store by name
        """
        raise NotImplementedError()

    @abstractmethod
    def get_data_ingestion_runs(
        self, collection_name: str, data_source_fqn: str
    ) -> List[DataIngestionRun]:
        """
        Get all data ingestion runs from the metadata store
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_collection(self, collection_name: str, include_runs=False):
        """
        Delete a collection from the metadata store
        """
        raise NotImplementedError()

    @abstractmethod
    def associate_data_source_with_collection(
        self,
        create_collection_data_source_association: AssociateDataSourceWithCollectionDto,
    ) -> Collection:
        """
        Associate a data source with a collection in the metadata store
        """
        raise NotImplementedError()

    @abstractmethod
    def unassociate_data_source_with_collection(
        self,
        collection_name: str,
        data_source_fqn: str,
    ) -> Collection:
        """
        Unassociate a data source with a collection in the metadata store
        """
        raise NotImplementedError()

    @abstractmethod
    def update_data_ingestion_run_status(
        self,
        data_ingestion_run_name: str,
        status: DataIngestionRunStatus,
    ):
        """
        Update the status of a data ingestion run in the metadata store
        """
        raise NotImplementedError()

    @abstractmethod
    def log_metrics_for_data_ingestion_run(
        self,
        data_ingestion_run_name: str,
        metric_dict: dict[str, int | float],
        step: int = 0,
    ):
        """
        Log metrics for a data ingestion run in the metadata store
        """
        raise NotImplementedError()

    @abstractmethod
    def log_errors_for_data_ingestion_run(
        self, data_ingestion_run_name: str, errors: Dict[str, Any]
    ):
        """
        Log errors for a data ingestion run in the metadata store
        """
        raise NotImplementedError()


def get_data_source_fqn(data_source: CreateDataSource) -> str:
    return f"{DOCUMENT_ID_SEPARATOR}".join([data_source.type, data_source.uri])


def get_base_document_id(data_source: DataSource) -> str | None:
    """
    Generates unique document id for a given data source. We use the following format:
    <fqn>
    This will be used to identify the source in the database.
    """
    return data_source.fqn


def generate_document_id(data_source: DataSource, path: str):
    """
    Generates unique document id for a given document. We use the following format:
    <type>::<source_uri>::<path>
    This will be used to identify the document in the database.
    """
    return f"{DOCUMENT_ID_SEPARATOR}".join([data_source.fqn, path])


def retrieve_data_source_fqn_from_document_id(_document_id: str):
    """
    Retrives params from document id for a given document. We use the following format:
    <type>::<source_uri>::<path>
    This will be used to identify the document in the database.
    reverse for `generate_document_id`
    """
    parts = _document_id.split(DOCUMENT_ID_SEPARATOR)
    if len(parts) == 3:
        return f"{DOCUMENT_ID_SEPARATOR}".join([parts[0], parts[1]])
    return None
