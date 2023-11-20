from abc import ABC, abstractmethod
from backend.utils.logger import logger

# A global registry to store all available loaders.
LOADER_REGISTRY = {}


def register(cls):
    """
    Registers all the available loaders using `BaseLoader` class

    Args:
        cls: The loader class to be registered.

    Returns:
        None
    """
    global LOADER_REGISTRY
    loader_type = cls.type

    # Validate and add the loader to the registry.
    if not loader_type:
        raise ValueError(
            f"static attribute `name` needs to be a non-empty string on class {cls.__name__}"
        )
    if loader_type in LOADER_REGISTRY:
        raise ValueError(
            f"Error while registering class {cls.__name__}, `name` already taken by {LOADER_REGISTRY[loader_type].__name__}"
        )
    LOADER_REGISTRY[loader_type] = cls


class BaseLoader(ABC):
    """
    Base class for all loaders. The loaders are responsible for loading the data
    from the source and storing it in the destination directory.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Register the subclass automatically when it is defined.
        register(cls)

    @abstractmethod
    def load_data(self, source_uri, dest_dir):
        """
        Load data function that downloads the data from the source URI and stores it in the destination directory.

        Args:
            source_uri (str): Source URI with protocol `supported_protocol`.
            dest_dir (str): Destination directory where the data will be stored.

        Returns:
            None
        """
        pass


def get_loader_for_knowledge_source(type, *args, **kwargs) -> BaseLoader:
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
