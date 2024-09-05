from abc import ABC
from typing import Any, Dict, List, Optional, Union

from backend.constants import DATA_POINT_FQN_METADATA_KEY, FQN_SEPARATOR
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
    RagApplication,
    RagApplicationDto,
)
from backend.utils import run_in_executor


class BaseMetadataStore(ABC):
    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    async def aconnect(cls, **kwargs) -> "BaseMetadataStore":
        return cls(**kwargs)

    #####
    # COLLECTIONS
    #####

    async def aget_collection_by_name(
        self, collection_name: str, no_cache: bool = True
    ) -> Optional[Collection]:
        """
        Get a collection from the metadata store by name
        """
        raise NotImplementedError()

    async def acreate_collection(self, collection: CreateCollection) -> Collection:
        """
        Create a collection in the metadata store
        """
        raise NotImplementedError()

    async def aget_retrieve_collection_by_name(
        self, collection_name: str, no_cache: bool = True
    ) -> Optional[Collection]:
        """
        Get a collection from the metadata store by name used during retrieval phase
        """
        raise NotImplementedError()

    async def aget_collections(
        self,
    ) -> List[Collection]:
        """
        Get all collections from the metadata store
        """
        raise NotImplementedError()

    async def alist_collections(
        self,
    ) -> List[str]:
        """
        List all collection names from metadata store
        """
        raise NotImplementedError()

    async def adelete_collection(self, collection_name: str, include_runs=False):
        """
        Delete a collection from the metadata store
        """
        raise NotImplementedError()

    #####
    # DATA SOURCE
    #####

    async def aget_data_source_from_fqn(self, fqn: str) -> Optional[DataSource]:
        """
        Get a data source from the metadata store by fqn
        """
        raise NotImplementedError()

    async def acreate_data_source(self, data_source: CreateDataSource) -> DataSource:
        """
        Create a data source in the metadata store
        """
        raise NotImplementedError()

    async def aget_data_sources(self) -> List[DataSource]:
        """
        Get all data sources from the metadata store
        """
        raise NotImplementedError()

    async def aassociate_data_source_with_collection(
        self,
        collection_name: str,
        data_source_association: AssociateDataSourceWithCollection,
    ) -> Collection:
        """
        Associate a data source with a collection in the metadata store
        """
        raise NotImplementedError()

    async def aunassociate_data_source_with_collection(
        self,
        collection_name: str,
        data_source_fqn: str,
    ) -> Collection:
        """
        Unassociate a data source with a collection in the metadata store
        """
        raise NotImplementedError()

    async def alist_data_sources(
        self,
    ) -> List[Dict[str, str]]:
        """
        List all data source names from metadata store
        """
        raise NotImplementedError()

    async def adelete_data_source(self, data_source_fqn: str):
        """
        Delete a data source from the metadata store
        """
        raise NotImplementedError()

    #####
    # DATA INGESTION RUNS
    #####

    async def acreate_data_ingestion_run(
        self, data_ingestion_run: CreateDataIngestionRun
    ) -> DataIngestionRun:
        """
        Create a data ingestion run in the metadata store
        """
        raise NotImplementedError()

    async def aget_data_ingestion_run(
        self, data_ingestion_run_name: str, no_cache: bool = False
    ) -> Optional[DataIngestionRun]:
        """
        Get a data ingestion run from the metadata store by name
        """
        raise NotImplementedError()

    async def aget_data_ingestion_runs(
        self, collection_name: str, data_source_fqn: str = None
    ) -> List[DataIngestionRun]:
        """
        Get all data ingestion runs from the metadata store
        """
        raise NotImplementedError()

    async def aupdate_data_ingestion_run_status(
        self,
        data_ingestion_run_name: str,
        status: DataIngestionRunStatus,
    ):
        """
        Update the status of a data ingestion run in the metadata store
        """
        raise NotImplementedError()

    async def alog_errors_for_data_ingestion_run(
        self, data_ingestion_run_name: str, errors: Dict[str, Any]
    ):
        """
        Log errors for a data ingestion run in the metadata store
        """
        raise NotImplementedError()

    ####
    # RAG APPLICATIONS
    ####

    async def aget_rag_app(self, app_name: str) -> Optional[RagApplicationDto]:
        """
        Get a RAG application from the metadata store by name
        """
        raise NotImplementedError()

    async def acreate_rag_app(self, app: RagApplication) -> RagApplicationDto:
        """
        create a RAG application in the metadata store
        """
        raise NotImplementedError()

    async def alist_rag_apps(self) -> List[str]:
        """
        List all RAG application names from metadata store
        """
        raise NotImplementedError()

    async def adelete_rag_app(self, app_name: str):
        """
        Delete a RAG application from the metadata store
        """
        raise NotImplementedError()


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
            f"Error while registering class {cls.__name__}, "
            f"key {provider} is already taken by {METADATA_STORE_REGISTRY[provider].__name__}"
        )
    METADATA_STORE_REGISTRY[provider] = cls


async def get_metadata_store_client(
    config: MetadataStoreConfig,
) -> BaseMetadataStore:
    if config.provider in METADATA_STORE_REGISTRY:
        kwargs = config.config
        return await METADATA_STORE_REGISTRY[config.provider].aconnect(**kwargs)
    else:
        raise ValueError(f"Unknown metadata store type: {config.provider}")
