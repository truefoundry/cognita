from backend.modules.parsers.customparser import CustomPdfParserUsingPyMuPDF
from backend.modules.parsers.markdownparser import MarkdownParser
from backend.modules.parsers.parser import register_parser
from backend.modules.parsers.pdfparser_fast import PdfParserUsingPyMuPDF
from backend.modules.parsers.textparser import TextParser

register_parser("MarkdownParser", MarkdownParser)
register_parser("PdfParserFast", PdfParserUsingPyMuPDF)
register_parser("TextParser", TextParser)
register_parser("CustomPdfParser", CustomPdfParserUsingPyMuPDF)
