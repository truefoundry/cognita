from backend.modules.parsers.multimodalparser import MultiModalParser
from backend.modules.parsers.parser import register_parser
from backend.modules.parsers.unstructured_io import UnstructuredIoParser

# The order of registry defines the order of precedence
register_parser("UnstructuredIoParser", UnstructuredIoParser)
register_parser("MultiModalParser", MultiModalParser)
