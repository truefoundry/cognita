from abc import ABC, abstractmethod
from typing import Any, Dict, List

from backend.constants import FQN_SEPARATOR
from backend.types import (
    AssociateDataSourceWithCollection,
    Collection,
    CreateCollection,
    CreateDataIngestionRun,
    CreateDataSource,
    DataIngestionRun,
    DataIngestionRunStatus,
    DataSource,
    MetadataStoreConfig,
)


class BaseMetadataStore(ABC):
    @abstractmethod
    def create_collection(self, collection: CreateCollection) -> Collection:
        """
        Create a collection in the metadata store
        """
        raise NotImplementedError()

    @abstractmethod
    def get_collection_by_name(
        self, collection_name: str, no_cache: bool = True
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
        self, collection_name: str, data_source_fqn: str = None
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
        collection_name: str,
        data_source_association: AssociateDataSourceWithCollection,
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
    return f"{FQN_SEPARATOR}".join([data_source.type, data_source.uri])

# A global registry to store all available metadata store.
METADATA_STORE_REGISTRY = {}


def register_metadata_store(provider: str, cls):
    """
    Registers all the available metadata store.

    Args:
        provider: The type of the metadata store to be registered.
        cls: The metadata store class to be registered.

    Returns:
        None
    """
    global METADATA_STORE_REGISTRY
    if provider in METADATA_STORE_REGISTRY:
        raise ValueError(
            f"Error while registering class {cls.__name__} already taken by {METADATA_STORE_REGISTRY[provider].__name__}"
        )
    METADATA_STORE_REGISTRY[provider] = cls


def get_metadata_store_client(
    config: MetadataStoreConfig,
) -> BaseMetadataStore:
    if config.provider in METADATA_STORE_REGISTRY:
        return METADATA_STORE_REGISTRY[config.provider](config=config.config)
    else:
        raise ValueError(f"Unknown metadata store type: {config.provider}")
