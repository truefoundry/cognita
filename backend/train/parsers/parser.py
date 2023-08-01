import typing
from abc import ABC, abstractmethod

from langchain.docstore.document import Document

PARSER_REGISTRY = {}


def register(cls):
    """
    Registers all the available parsers using `BaseParser` class.
    """
    global PARSER_REGISTRY
    name = cls.name
    # logger.debug("Loading parser: " + str(name))
    supported_extensions = cls.supported_file_extensions
    if not name:
        raise ValueError(
            f"static attribute `name` needs to be a non-empty string on class {cls.__name__}"
        )
    if name in PARSER_REGISTRY:
        raise ValueError(
            f"Error while registering class {cls.__name__}, `name` already taken by {PARSER_REGISTRY[name].__name__}"
        )
    PARSER_REGISTRY[name] = {"cls": cls, "supported_extensions": supported_extensions}


def get_parser(name, *args, **kwargs):
    """
    Returns the parser class for the given name.
    """
    global PARSER_REGISTRY
    if name not in PARSER_REGISTRY:
        raise ValueError(f"No parser registered with name {name}")
    return PARSER_REGISTRY[name]["cls"](*args, **kwargs)


def get_parsers_map():
    """
    Returns a mapping of file extensions to parser names.
    """
    global PARSER_REGISTRY
    file_extension_to_parsers_map = {}
    for parser_name, parser_entry in PARSER_REGISTRY.items():
        supported_extensions = parser_entry["supported_extensions"]
        for supported_extension in supported_extensions:
            if supported_extension not in file_extension_to_parsers_map:
                file_extension_to_parsers_map[supported_extension] = []
            file_extension_to_parsers_map[supported_extension].append(parser_name)

    return file_extension_to_parsers_map


class BaseParser(ABC):
    """
    BaseParser is an Abstract Base Class (ABC) that serves as a template for all parser objects.
    It contains the common attributes and methods that each parser should implement.
    """

    def __init__(self, max_chunk_size, dry_run=True, *args, **kwargs):
        """
        Initializes the BaseParser object.

        Parameters:
            max_chunk_size (int): Maximum size for each chunk.
            dry_run (bool): If True, the parser operates in 'dry run' mode.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.max_chunk_size = max_chunk_size
        self.dry_run = dry_run

    def __init_subclass__(cls, **kwargs):
        """
        Special method in Python for class initialization. This method is called whenever a subclass is declared.

        Parameters:
            **kwargs: Additional keyword arguments.
        """
        super().__init_subclass__(**kwargs)
        register(cls)

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Abstract method. This should return the name of the parser.

        Returns:
            str: A string representing the name of the parser.
        """
        pass

    @property
    @abstractmethod
    def supported_file_extensions(self) -> typing.List[str]:
        """
        Abstract method. This should return a list of supported file extensions by the parser.

        Returns:
            typing.List[str]: A list of strings representing the supported file extensions.
        """
        pass

    @abstractmethod
    async def get_chunks(self, filepath) -> typing.List[Document]:
        """
        Abstract method. This should asynchronously read a file and return its content in chunks.

        Parameters:
            filepath (str): Path of the file to be read.

        Returns:
            typing.List[Document]: A list of Document objects, each representing a chunk of the file.
        """
        pass
