from abc import ABC, abstractmethod
from typing import List

from backend.types import DataSource, LoadedDocument

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
    def load_data(
        self, data_source: DataSource, dest_dir: str, allowed_extensions: List[str]
    ) -> List[LoadedDocument]:
        """
        Load data function that downloads the data from the source URI and stores it in the destination directory.

        Args:
            data_source (DataSource): Source URI with protocol `supported_protocol`.
            dest_dir (str): Destination directory where the data will be stored.
            allowed_extensions (List[str]): A list of allowed file extensions.

        Returns:
            List[LoadedDocument]: A list of LoadedDocument objects containing metadata.
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
