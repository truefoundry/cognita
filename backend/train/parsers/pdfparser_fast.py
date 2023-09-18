import nltk
import pdfplumber
from langchain.docstore.document import Document
from langchain.text_splitter import SpacyTextSplitter

from .parser import BaseParser

nltk.download("punkt", quiet=True)


class PdfParserUsingPlumber(BaseParser):
    """
    PdfParserUsingPlumber is a parser class for extracting text from PDF files using pdfplumber library.

    Attributes:
        name (str): The name of the parser.
        supported_file_extensions (List[str]): List of supported file extensions (e.g., ['.pdf']).
    """

    name = "PdfParserFast"
    supported_file_extensions = [".pdf"]

    def __init__(self, max_chunk_size, dry_run=True, *args, **kwargs):
        """
        Initializes the PdfParserUsingPlumber object.

        Parameters:
            max_chunk_size (int): Maximum size for each chunk.
            dry_run (bool): If True, the parser operates in 'dry run' mode.
        """
        # Initialize the SpacyTextSplitter for splitting the text into chunks
        self.text_splitter = SpacyTextSplitter(
            pipeline="en_core_web_md", chunk_size=max_chunk_size
        )

    async def get_chunks(self, file_path):
        """
        Asynchronously extracts text from a PDF file and returns it in chunks.

        Parameters:
            file_path (str): Path of the PDF file to be processed.

        Returns:
            List[Document]: A list of Document objects, each representing a chunk of extracted text.
        """
        final_texts = []
        try:
            # Open the PDF file using pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract text from the current page
                    page_text = page.extract_text()

                    # Create a Document object per page with page-specific metadata
                    doc = Document(
                        page_content=page_text,
                        metadata={
                            "filepath": file_path,
                            "page_num": page_num,  # Page number as enum
                            "type": "text",
                        },
                    )

                    # Split the document into chunks if more than one page
                    loader_data = self.text_splitter.split_documents([doc])
                    final_texts.extend(loader_data)
        except Exception:
            # Return an empty list if there was an error during processing
            return []

        return final_texts
