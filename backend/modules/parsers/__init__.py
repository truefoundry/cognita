from backend.modules.parsers.audio_parser import AudioParser
from backend.modules.parsers.multi_modal_parser import MultiModalParser
from backend.modules.parsers.parser import register_parser
from backend.modules.parsers.unstructured_io import UnstructuredIoParser
from backend.modules.parsers.video_parser import VideoParser

# The order of registry defines the order of precedence
register_parser("UnstructuredIoParser", UnstructuredIoParser)
register_parser("MultiModalParser", MultiModalParser)
register_parser("AudioParser", AudioParser)
register_parser("VideoParser", VideoParser)
