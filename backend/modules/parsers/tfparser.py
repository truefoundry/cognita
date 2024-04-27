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
            self.tf_service_url.rstrip("/") + endpoint,
            files=payload,
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

            # get file path & name
            head, tail = os.path.split(filepath)

            for page in doc:
                try:
                    page_number = page.number + 1
                    print(f"\n\nProcessing page {page_number}...")

                    content = fitz.open()
                    # copy over current page
                    content.insert_pdf(doc, from_page=page.number, to_page=page.number)
                    # save the page to a temporary file
                    temp_file = os.path.join(head, f"{tail}.pdf")
                    content.save(temp_file)
                    content.close()

                    # send the page to the TfParser service
                    response = await self._send_file_request(
                        payload={
                            "file": open(temp_file, "rb"),
                        },
                        endpoint="/tf-parse-pdf",
                    )

                    # Parse the response
                    response = response.json()
                    if "error" not in response:
                        for res in response:
                            page_content = res.get("page_content")
                            page_texts.append(page_content)
                            if (
                                page_content != ""
                                or page_content is not None
                                or page_content != " "
                            ):
                                metadata = res.get("metadata", {})
                                metadata["page_number"] = (page_number,)
                                metadata["source"] = tail
                                final_texts.append(
                                    Document(
                                        page_content=page_content,
                                        metadata=metadata,
                                    )
                                )
                    else:
                        print(f"Error in Page: {response['error']}")

                    # remove the temporary file
                    print("Removing temp file...")
                    os.remove(temp_file)
                except Exception as e:
                    print(f"Exception in Page: {e}")
                    # remove the temporary file
                    print("Removing temp file...")
                    os.remove(temp_file)
                    continue

            document_text = " ".join(page_texts)
            if document_text:
                response = await self._send_text_request(
                    payload={"text": document_text, "file_name": tail},
                    endpoint="/tf-get-response",
                )

                response = response.json()
                if "error" not in response:
                    page_content = response["response"].get("page_content")
                    metadata = response["response"].get("metadata", {})
                    if (
                        page_content != ""
                        or page_content is not None
                        or page_content != " "
                    ):
                        final_texts.append(
                            Document(
                                page_content=page_content,
                                metadata=metadata,
                            )
                        )
                else:
                    print(f"Error: {response['error']}")
            return final_texts
        except Exception as e:
            print(f"Ultimate Exception: {e}")
            return final_texts
