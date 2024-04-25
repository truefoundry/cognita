from typing import Optional
import fitz, cv2, base64
import numpy as np
import requests
from langchain.text_splitter import RecursiveCharacterTextSplitter
from backend.modules.parsers.parser import BaseParser
from backend.settings import settings
from backend.logger import logger
from langchain.docstore.document import Document


class TfParser(BaseParser):
    """
    TfParser is a multi-modal parser class for deep extraction of pdf documents.
    Requires a running instance of the TfParser service that has access to TFLLM Gateway
    """

    supported_file_extensions = [".pdf"]

    def __init__(self, max_chunk_size: int = 1000, *args, **kwargs):
        """
        Initializes the TfParser object.
        """
        self.max_chunk_size = max_chunk_size
        self.tf_service_url = settings.TF_PARSER

    async def _send_file_request(self, payload: dict, endpoint: str):
        """
        Sends a POST request to the TfParser service.
        """
        response = requests.post(
            self.tf_service_url.rstrip("/") + endpoint, files=payload
        )
        if "error" in response:
            logger.error(f"Error: {response.json()['error']}")
            return None
        return response

    async def get_chunks(
        self, filepath: str, metadata: Optional[dict] = None, *args, **kwargs
    ):
        """
        Asynchronously extracts text from a PDF file and returns it in chunks.
        """
        if not filepath.endswith(".pdf"):
            logger.error("Invalid file extension. TfParser only supports PDF files.")
            return []
        final_texts = list()
        try:
            file_obj = {"file": open(filepath, "rb")}
            response = await self._send_file_request(
                payload=file_obj, endpoint="/tf-parse-pdf"
            )

            response = response.json()
            if response:
                for res in response:
                    final_texts.append(
                        Document(
                            page_content=res["page_content"], metadata=res["metadata"]
                        )
                    )
            return final_texts
        except Exception as e:
            logger.error(f"Error: {e}")
            return final_texts
