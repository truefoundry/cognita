import typing
from abc import ABC, abstractmethod

from langchain.docstore.document import Document

from backend.logger import logger
from backend.types import LoadedDataPoint

PARSER_REGISTRY = {}


def register_parser(name: str, cls):
    """
    Registers all the available parsers.
    """
    global PARSER_REGISTRY
    if name in PARSER_REGISTRY:
        raise ValueError(
            f"Error while registering class {cls.__name__} already taken by {PARSER_REGISTRY[name].__name__}"
        )
    PARSER_REGISTRY[name] = cls


class BaseParser(ABC):
    """
    BaseParser is an Abstract Base Class (ABC) that serves as a template for all parser objects.
    It contains the common attributes and methods that each parser should implement.
    """

    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    async def get_chunks(
        self,
        loaded_data_point: LoadedDataPoint,
        *args,
        **kwargs,
    ) -> typing.List[Document]:
        """
        Abstract method. This should asynchronously read a file and return its content in chunks.

        Parameters:
            loaded_data_point (LoadedDataPoint): Loaded Document to read and parse.

        Returns:
            typing.List[Document]: A list of Document objects, each representing a chunk of the file.
        """
        pass


def get_parser_for_extension(
    file_extension, parsers_map, *args, **kwargs
) -> BaseParser:
    """
    Given the file_extension and parsers mapping, return the appropriate mapper.
    """
    if file_extension not in parsers_map:
        logger.error(f"Loaded doc with extension {file_extension} is not supported")
        return None
    global PARSER_REGISTRY
    name = parsers_map[file_extension]
    if name not in PARSER_REGISTRY:
        raise ValueError(f"No parser registered with name {name}")
    return PARSER_REGISTRY[name](*args, **kwargs)


def list_parsers():
    """
    Returns a list of all the registered parsers.

    Returns:
        List[dict]: A list of all the registered parsers.
    """
    global PARSER_REGISTRY
    return [
        {
            "type": type,
            "class": cls.__name__,
        }
        for type, cls in PARSER_REGISTRY.items()
    ]
