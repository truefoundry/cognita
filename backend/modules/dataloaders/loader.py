from abc import ABC, abstractmethod
from typing import List

from backend.types import DataPoint, DataSource, LoadedDocument

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


class BaseLoader(ABC):
    """
    Base class for all loaders. The loaders are responsible for loading the data
    from the source and storing it in the destination directory.
    """

    @abstractmethod
    def list_data_points(self, data_source: DataSource) -> List[DataPoint]:
        """
        List the data points from the source.

        Args:
            data_source (DataSource): The data source from which the data points are to be listed.

        Returns:
            List[DataPoint]: The list of data points.
        """
        pass

    @abstractmethod
    def load_data_points(
        self,
        data_source: DataSource,
        data_points: List[DataPoint],
        dest_dir: str,
    ) -> List[DataPoint]:
        """
        Load the data points from the source to the destination directory.

        Args:
            data_source (DataSource): The data source from which the data points are to be loaded.
            data_points (List[DataPoint]): The list of data points to be loaded.
            dest_dir (str): The destination directory to store the loaded data.

        Returns:
            List[DataPoint]: The list of loaded documents.
        """
        pass


def get_loader_for_data_source(type, *args, **kwargs) -> BaseLoader:
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
        {"type": type, "class": cls.__name__} for type, cls in LOADER_REGISTRY.items()
    ]
