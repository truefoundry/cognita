import pdfplumber
from langchain.docstore.document import Document
from langchain.text_splitter import SpacyTextSplitter

from .parser import BaseParser


class PdfParserUsingPlumber(BaseParser):
    name = "PdfParserFast"
    supported_file_extensions = [".pdf"]

    def __init__(self, max_chunk_size, dry_run=True, *args, **kwargs):
        self.text_splitter = SpacyTextSplitter(
            pipeline="en_core_web_md", chunk_size=max_chunk_size
        )

    async def get_chunks(self, file_path):
        # Extract text from PDF using pdfplumber
        final_texts = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
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
            return []

        return final_texts
