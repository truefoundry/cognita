import hashlib
import json
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, List, Optional

from langchain.docstore.document import Document

from backend.logger import logger

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

    def __init__(self, **kwargs):
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


def get_parser_for_extension_with_cache(
    extension: str,
    parsers_map: Dict[str, Any],
    parser_cache: Dict[str, BaseParser],
    *args: Any,
    **kwargs: Any,
) -> BaseParser:
    # Create a cache key using MD5 hash
    cache_key = _create_cache_key(extension, parsers_map, args, kwargs)

    # Check if the parser is in the cache
    if cache_key not in parser_cache:
        # If not in cache, get the parser and store it
        parser_cache[cache_key] = get_parser_for_extension(
            extension, parsers_map, *args, **kwargs
        )

    # Return the cached parser
    return parser_cache[cache_key]


def _create_cache_key(
    extension: str, parsers_map: Dict[str, Any], args: tuple, kwargs: dict
) -> str:
    # Convert parsers_map to a JSON string
    parsers_json = json.dumps(parsers_map, sort_keys=True, default=lambda o: o.__dict__)

    # Combine all elements into a single string
    key_string = f"{extension}:{parsers_json}:{args}:{sorted(kwargs.items())}"

    # Create MD5 hash
    return hashlib.md5(key_string.encode()).hexdigest()


def get_parser_for_extension(
    file_extension, parsers_map, *args, **kwargs
) -> Optional[BaseParser]:
    """
    During the indexing phase, given the file_extension and parsers mapping, return the appropriate mapper.
    If no mapping is given, use the default registry.
    """
    global PARSER_REGISTRY_EXTENSIONS
    global PARSER_REGISTRY

    logger.debug(
        f"PARSER REGISTRY: {PARSER_REGISTRY}, file_extension: {file_extension}, parsers_map: {parsers_map}"
    )
    # We dont have a parser for this extension yet
    if file_extension not in PARSER_REGISTRY_EXTENSIONS:
        logger.error(f"Loaded doc with extension {file_extension} is not supported")
        return None
    # Extension not given in parser map use the default registry
    if file_extension not in parsers_map:
        # get the first parser name registered with the extension
        parser_name = PARSER_REGISTRY_EXTENSIONS[file_extension][0]
        logger.debug(
            f"Parser map not found in the collection for extension {file_extension}. Hence, using parser {parser_name}"
        )
        return PARSER_REGISTRY[parser_name](**kwargs)
    else:
        parser_name = parsers_map[file_extension].name
        logger.debug(
            f"Parser map found in the collection for extension {file_extension}. Hence, using parser {parser_name}"
        )

    if parser_name not in PARSER_REGISTRY:
        raise ValueError(f"No parser registered with name {parser_name}")

    return PARSER_REGISTRY[parser_name](**parsers_map[file_extension].parameters)


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
