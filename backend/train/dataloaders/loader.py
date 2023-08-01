from abc import ABC, abstractmethod
from backend.common.logger import logger

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
    name = cls.name
    logger.debug("Loading loader: " + str(name))
    supported_protocol = cls.supported_protocol

    # Validate and add the loader to the registry.
    if not name:
        raise ValueError(
            f"static attribute `name` needs to be a non-empty string on class {cls.__name__}"
        )
    if name in LOADER_REGISTRY:
        raise ValueError(
            f"Error while registering class {cls.__name__}, `name` already taken by {LOADER_REGISTRY[name].__name__}"
        )
    LOADER_REGISTRY[name] = {"cls": cls, "supported_protocol": supported_protocol}


def get_loader(name, *args, **kwargs):
    """
    Returns the object of the loader class for given name

    Args:
        name (str): The name of the loader.
    Returns:
        BaseLoader: An instance of the specified loader class.
    """
    global LOADER_REGISTRY
    if name not in LOADER_REGISTRY:
        raise ValueError(f"No loader registered with name {name}")
    return LOADER_REGISTRY[name]["cls"](*args, **kwargs)


def get_loaders_map():
    """
    Returns a mapping of supported protocols to the names of the registered loaders.

    Returns:
        dict: A mapping of protocol (str) to loader name (str).
    """
    global LOADER_REGISTRY
    protocol_to_loaders_map = {}
    for loader_name, loader_entry in LOADER_REGISTRY.items():
        supported_protocol = loader_entry["supported_protocol"]
        protocol_to_loaders_map[supported_protocol] = loader_name
    return protocol_to_loaders_map


class BaseLoader(ABC):
    """
    Base class for all loaders. The loaders are responsible for loading the data
    from the source and storing it in the destination directory.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Register the subclass automatically when it is defined.
        register(cls)

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of the loader.

        Returns:
            str: The name of the loader (must be a non-empty string).
        """
        pass

    @property
    @abstractmethod
    def supported_protocol(self) -> str:
        """
        Supported protocol of the loader, e.g., "github://", "local://", "mlfoundry://".

        Returns:
            str: The supported protocol of the loader (must be a non-empty string).
        """
        pass

    @abstractmethod
    def load_data(self, source_uri, dest_dir, credentials):
        """
        Load data function that downloads the data from the source URI and stores it in the destination directory.

        Args:
            source_uri (str): Source URI with protocol `supported_protocol`.
            dest_dir (str): Destination directory where the data will be stored.
            credentials (dict): Credentials needed to download the data (currently not used).

        Returns:
            None
        """
        pass
