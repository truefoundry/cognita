from backend.modules.parsers.audioparser import AudioParser
from backend.modules.parsers.multimodalparser import MultiModalParser
from backend.modules.parsers.parser import register_parser
from backend.modules.parsers.unstructured_io import UnstructuredIoParser
from backend.modules.parsers.videoparser import VideoParser

# The order of registry defines the order of precedence
register_parser("UnstructuredIoParser", UnstructuredIoParser)
register_parser("MultiModalParser", MultiModalParser)
register_parser("AudioParser", AudioParser)
register_parser("VideoParser", VideoParser)
