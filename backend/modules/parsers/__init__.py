from backend.modules.parsers.codeparser import CodeParser
from backend.modules.parsers.markdownparser import MarkdownParser
from backend.modules.parsers.parser import register_parser
from backend.modules.parsers.pdfparser_fast import PdfParserUsingPyMuPDF
from backend.modules.parsers.tablepdfparser import PdfTableParser
from backend.modules.parsers.textparser import TextParser
from backend.modules.parsers.TruefoundryParser.tfparser import TfParser

# The order of registry defines the order of precedence
register_parser("MarkdownParser", MarkdownParser)
register_parser("TextParser", TextParser)
register_parser("PdfParserFast", PdfParserUsingPyMuPDF)
register_parser("PdfTableParser", PdfTableParser)
register_parser("TfParser", TfParser)
register_parser("CodeParser", CodeParser)
