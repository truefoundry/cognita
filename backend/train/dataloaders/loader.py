from abc import ABC, abstractmethod
from backend.common.logger import logger

LOADER_REGISTRY = {}


def register(cls):
    """
    Registers all the available loaders using `BaseLoader` class
    """
    global LOADER_REGISTRY
    name = cls.name
    logger.debug("Loading loader: " + str(name))
    supported_protocol = cls.supported_protocol
    if not name:
        raise ValueError(
            f"static attribute `name` needs to be non empty string on class {cls.__name__}"
        )
    if name in LOADER_REGISTRY:
        raise ValueError(
            f"Error while registering class {cls.__name__}, `name` already taken by {LOADER_REGISTRY[name].__name__}"
        )
    LOADER_REGISTRY[name] = {"cls": cls, "supported_protocol": supported_protocol}


def get_loader(name, *args, **kwargs):
    """
    Return object of loader class for given name
    """
    global LOADER_REGISTRY
    if name not in LOADER_REGISTRY:
        raise ValueError(f"No loader registered with name {name}")
    return LOADER_REGISTRY[name]["cls"](*args, **kwargs)


def get_loaders_map():
    """
    Returns a mapping of protocol and name of loader
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
        register(cls)

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of the loader
        """
        pass

    @property
    @abstractmethod
    def supported_protocol(self) -> str:
        """
        Supported protocol of the loader eg "github://", "local://", "mlfoundry://"
        """
        pass

    @abstractmethod
    def load_data(self, source_uri, dest_dir, credentials):
        """
        Load data function that downloads the data at destination
         `source_uri`: source uri with protocol `supported_protocol`
         `dest_dir`: destination directory
         `credentials`: credentials needed to download the data
        """
        pass
