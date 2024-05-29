from backend.modules.parsers.codeparser import CodeParser
from backend.modules.parsers.markdownparser import MarkdownParser
from backend.modules.parsers.multimodal.parser import MultiModalParser
from backend.modules.parsers.parser import register_parser
from backend.modules.parsers.pdfparser_fast import PdfParserUsingPyMuPDF
from backend.modules.parsers.tablepdfparser import PdfTableParser
from backend.modules.parsers.textparser import TextParser
from backend.settings import settings

# The order of registry defines the order of precedence
register_parser("MarkdownParser", MarkdownParser)
register_parser("TextParser", TextParser)
register_parser("PdfParserFast", PdfParserUsingPyMuPDF)
register_parser("MultiModalParser", MultiModalParser)
register_parser("CodeParser", CodeParser)
register_parser("PdfTableParser", PdfTableParser)
