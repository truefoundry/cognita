import requests
from langchain.docstore.document import Document
from requests.adapters import HTTPAdapter, Retry

from backend.logger import logger
from backend.modules.parsers.parser import BaseParser
from backend.settings import settings


class UnstructuredIoParser(BaseParser):
    """
    UnstructuredIoParser is a parser class for extracting text from unstructured input.
    """

    supported_file_extensions = [
        ".txt",
        ".eml",
        ".msg",
        ".xml",
        ".html",
        ".md",
        ".rst",
        ".rtf",
        ".jpeg",
        ".png",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".pdf",
        ".odt",
        ".epub",
        ".csv",
        ".tsv",
        ".xlsx",
    ]

    def __init__(self, *, max_chunk_size: int = 2000, **kwargs):
        """
        Initializes the UnstructuredIoParser object.
        """
        self.max_chunk_size = max_chunk_size
        self.session = requests.Session()
        self.retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
        )
        self.adapter = HTTPAdapter(max_retries=self.retry_strategy)
        self.session.mount("https://", self.adapter)
        self.session.mount("http://", self.adapter)
        super().__init__(**kwargs)

    async def get_chunks(self, filepath: str, metadata: dict, **kwargs):
        """
        Asynchronously extracts text from unstructured input and returns it in chunks.
        """
        final_texts = []
        try:
            with open(filepath, "rb") as f:
                # Define files payload
                files = {"files": f}
                data = {
                    "strategy": "auto",
                    # applies language pack for ocr - visit https://github.com/tesseract-ocr/tessdata for more info
                    "languages": ["eng", "hin"],
                    "chunking_strategy": "by_title",
                    "max_characters": self.max_chunk_size,
                }

                headers = {
                    "accept": "application/json",
                }
                if settings.UNSTRUCTURED_IO_API_KEY:
                    headers["unstructured-api-key"] = settings.UNSTRUCTURED_IO_API_KEY

                # Send POST request
                response = self.session.post(
                    settings.UNSTRUCTURED_IO_URL.rstrip("/") + "/general/v0/general",
                    headers=headers,
                    files=files,
                    data=data,
                )
                response.raise_for_status()

            parsed_data = response.json()
            for payload in parsed_data:
                text = payload["text"]
                metadata = payload["metadata"]
                final_texts.append(Document(page_content=text, metadata=metadata))
            return final_texts
        except Exception as e:
            logger.exception(f"Final Exception: {e}")
            raise e
