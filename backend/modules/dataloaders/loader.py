from abc import ABC, abstractmethod
from typing import Dict, Iterator, List

from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint

# A global registry to store all available loaders.
LOADER_REGISTRY = {}


def register_dataloader(type: str, cls):
    """
    Registers all the available loaders using `BaseLoader` class

    Args:
        type: The type of the loader to be registered.
        cls: The loader class to be registered.

    Returns:
        None
    """
    global LOADER_REGISTRY
    # Validate and add the loader to the registry.
    if not type:
        raise ValueError(
            f"static attribute `name` needs to be a non-empty string on class {cls.__name__}"
        )
    if type in LOADER_REGISTRY:
        raise ValueError(
            f"Error while registering class {cls.__name__}, `name` already taken by {LOADER_REGISTRY[type].__name__}"
        )
    LOADER_REGISTRY[type] = cls


class BaseDataLoader(ABC):
    """
    Base data loader class. Data loader is responsible for detecting, filtering and then loading data points to be ingested.
    """

    def load_full_data(
        self,
        data_source: DataSource,
        dest_dir: str,
        batch_size: int = 100,
    ):
        """
        Sync the data source and load all data points from the source to the destination directory.
        Args:
            data_source (DataSource): The data source from which the data points are to be loaded.
            dest_dir (str): The destination directory to store the loaded data.
            batch_size (int): The batch size to be used for loading data points.
        Returns:
            None
        """
        return self.load_filtered_data(
            data_source,
            dest_dir,
            previous_snapshot={},
            batch_size=batch_size,
            data_ingestion_mode=DataIngestionMode.FULL,
        )

    def load_incremental_data(
        self,
        data_source: DataSource,
        dest_dir: str,
        previous_snapshot: Dict[str, str],
        batch_size: int = 100,
    ):
        """
        Sync the data source, filter data points and load them from the source to the destination directory.
        Args:
            data_source (DataSource): The data source from which the data points are to be loaded.
            dest_dir (str): The destination directory to store the loaded data.
            previous_snapshot (Dict[str, str]): A dictionary of existing data points.
            batch_size (int): The batch size to be used for loading data points.
        Returns:
            None
        """
        return self.load_filtered_data(
            data_source,
            dest_dir,
            previous_snapshot,
            batch_size,
            DataIngestionMode.INCREMENTAL,
        )

    @abstractmethod
    def load_filtered_data(
        self,
        data_source: DataSource,
        dest_dir: str,
        previous_snapshot: Dict[str, str],
        batch_size: int,
        data_ingestion_mode: DataIngestionMode,
    ) -> Iterator[List[LoadedDataPoint]]:
        """
        Sync the data source, filter data points and load them from the source to the destination directory.
        This method returns the loaded data points in batches as an iterator.
        Args:
            data_source (DataSource): The data source from which the data points are to be loaded.
            dest_dir (str): The destination directory to store the loaded data.
            previous_snapshot (Dict[str, str]): A dictionary of existing data points.
            batch_size (int): The batch size to be used for loading data points.
            data_ingestion_mode (DataIngestionMode): The data ingestion mode to be used.
        Returns:
            Iterator[List[LoadedDataPoint]]: An iterator of list of loaded data points.
        """
        pass


def get_loader_for_data_source(type, *args, **kwargs) -> BaseDataLoader:
    """
    Returns the object of the loader class for given type

    Args:
        type (str): Type of the loader.
    Returns:
        BaseLoader: An instance of the specified loader class.
    """
    global LOADER_REGISTRY
    if type not in LOADER_REGISTRY:
        raise ValueError(f"No loader registered with type {type}")
    return LOADER_REGISTRY[type](*args, **kwargs)


def list_dataloaders():
    """
    Returns a list of all the registered loaders.

    Returns:
        List[dict]: A list of all the registered loaders.
    """
    global LOADER_REGISTRY
    return [
        {"type": type, "class": cls.__name__, "description": cls.__doc__.strip()}
        for type, cls in LOADER_REGISTRY.items()
    ]
