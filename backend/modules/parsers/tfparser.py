import os
from typing import Optional

import fitz
import requests
from langchain.docstore.document import Document

from backend.logger import logger
from backend.modules.parsers.parser import BaseParser
from backend.settings import settings


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
            print(f"Error: {response.json()['error']}")
            return None
        return response

    async def _send_text_request(self, payload: dict, endpoint: str):
        """
        Sends a POST request to the TfParser service.
        """
        response = requests.post(
            self.tf_service_url.rstrip("/") + endpoint, json=payload
        )
        if "error" in response:
            print(f"Error: {response.json()['error']}")
            return None
        return response

    async def get_chunks(
        self, filepath: str, metadata: Optional[dict] = None, *args, **kwargs
    ):
        """
        Asynchronously extracts text from a PDF file and returns it in chunks.
        """
        if not filepath.endswith(".pdf"):
            print("Invalid file extension. TfParser only supports PDF files.")
            return []
        page_texts = list()
        final_texts = list()

        try:
            # Open the PDF file using pdfplumber
            doc = fitz.open(filepath)

            # get file name
            _, tail = os.path.split(filepath)

            # iterate over each page in the PDF file
            for page in doc:
                page_number = page.number + 1
                print(f"\n\nProcessing page {page_number}...")
                response = await self._send_file_request(
                    payload={"file": page.tobytes(), "file_name": tail},
                    endpoint="/tf-parse-pdf-page",
                )

                response = response.json()
                print(response)
            #     if 'error' not in response:
            #         if response['page'] != "" or response['page'] is not None or response['page'] != " ":
            #             page_texts.append(response['page'])

            #         if response['parsed_page'].get("page_content") != "" or response['parsed_page'].get("page_content") is not None or response['parsed_page'].get("page_content") != " ":
            #             final_texts.append(
            #                 Document(
            #                     page_content=response['parsed_page'].get("page_content"),
            #                     metadata=response['parsed_page'].get("metadata"),
            #                 )
            #             )
            #     else:
            #         print(f"Error: {response['error']}")

            # document_text = " ".join(page_texts)
            # if document_text:
            #     response = await self._send_text_request(
            #         payload={"text": document_text},
            #         endpoint="/tf-get-response",
            #     )
            #     response = response.json()
            #     if 'error' not in response:
            #         if response['response'].get("page_content") != "" or response['response'].get("page_content") is not None or response['response'].get("page_content") != " ":
            #             final_texts.append(
            #                 Document(
            #                     page_content=response['response'].get("page_content"),
            #                     metadata=response['response'].get("metadata"),
            #                 )
            #             )
            #     else:
            #         print(f"Error: {response['error']}")

            # file_obj = {"file": open(filepath, "rb")}
            # print("Sending file to TfParser service...")
            # response = await self._send_file_request(
            #     payload=file_obj, endpoint="/tf-parse-pdf"
            # )
            # print("Received response from TfParser service.")

            # response = response.json()
            # if response:
            #     print("Parsing response...")
            #     for res in response:
            #         if res["page_content"] != "" or res["page_content"] is not None or res["page_content"] != " ":
            #             final_texts.append(
            #                 Document(
            #                     page_content=res["page_content"], metadata=res["metadata"]
            #                 )
            #             )
            return final_texts
        except Exception as e:
            print(f"Error: {e}")
            return final_texts
