from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, List, Optional

from langchain.docstore.document import Document

from backend.logger import logger
from backend.types import LoadedDataPoint

PARSER_REGISTRY = {}
PARSER_REGISTRY_EXTENSIONS = defaultdict(list)


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
    for extension in cls.supported_file_extensions:
        PARSER_REGISTRY_EXTENSIONS[extension].append(name)


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
        filepath: str,
        metadata: Optional[Dict[Any, Any]],
        *args,
        **kwargs,
    ) -> List[Document]:
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
) -> Optional[BaseParser]:
    """
    During the indexing phase, given the file_extension and parsers mapping, return the appropriate mapper.
    If no mapping is given, use the default registry.
    """
    global PARSER_REGISTRY_EXTENSIONS
    global PARSER_REGISTRY

    # We dont have a parser for this extension yet
    if file_extension not in PARSER_REGISTRY_EXTENSIONS:
        logger.error(f"Loaded doc with extension {file_extension} is not supported")
        return None
    # Extension not given in parser map use the default registry
    if file_extension not in parsers_map:
        # get the first parser name registered with the extension
        name = PARSER_REGISTRY_EXTENSIONS[file_extension][0]
        print(
            f"Parser map not found in the collection for extension {file_extension}. Hence, using parser {name}"
        )
        logger.debug(
            f"Parser map not found in the collection for extension {file_extension}. Hence, using parser {name}"
        )
    else:
        name = parsers_map[file_extension]
        print(
            f"Parser map found in the collection for extension {file_extension}. Hence, using parser {name}"
        )
        logger.debug(
            f"Parser map found in the collection for extension {file_extension}. Hence, using parser {name}"
        )

    if name not in PARSER_REGISTRY:
        raise ValueError(f"No parser registered with name {name}")

    return PARSER_REGISTRY[name](*args, **kwargs)


def list_parsers():
    """
    Returns a list of all the registered parsers.

    Returns:
        List[Dict]: A list of all the registered parsers.
    """
    global PARSER_REGISTRY
    return [
        {
            "type": type,
            "class": cls.__name__,
        }
        for type, cls in PARSER_REGISTRY.items()
    ]
