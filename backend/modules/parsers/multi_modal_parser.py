import asyncio
import base64
import os
from itertools import islice
from typing import Any, Dict, Optional

import cv2
import fitz
import numpy as np
from langchain.docstore.document import Document
from langchain_core.messages import HumanMessage

from backend.constants import (
    MULTI_MODAL_PARSER_PROMPT,
    MULTI_MODAL_PARSER_SUPPORTED_FILE_EXTENSIONS,
    MULTI_MODAL_PARSER_SUPPORTED_IMAGE_EXTENSIONS,
    MULTI_MODAL_PARSER_SUPPORTED_PDF_EXTENSION,
)
from backend.logger import logger
from backend.modules.model_gateway.model_gateway import model_gateway
from backend.modules.parsers.parser import BaseParser
from backend.modules.parsers.utils import contains_text
from backend.types import ModelConfig


class MultiModalParser(BaseParser):
    """
    MultiModalParser is a multi-modal parser class for deep extraction of pdf documents and images.

    Parser Configuration will look like the following while creating the collection:
    {
        ".pdf": {
            "name": "MultiModalParser",
            "parameters": {
                "model_configuration": {
                    "name" : "truefoundry/openai-main/gpt-4o-mini"
                },
                "prompt": "You are a PDF Parser ....."
            }
        }
    }
    """

    supported_file_extensions = MULTI_MODAL_PARSER_SUPPORTED_FILE_EXTENSIONS

    def __init__(self, *, model_configuration: ModelConfig, prompt: str = "", **kwargs):
        """
        Initializes the MultiModalParser object.
        """
        # Multi-modal parser needs to be configured with the openai compatible client url and vision model
        self.model_configuration = ModelConfig.model_validate(model_configuration)
        logger.info(f"Using custom vision model..., {self.model_configuration}")

        if prompt:
            self.prompt = prompt
            logger.info(f"Using custom prompt..., {self.prompt}")
        else:
            self.prompt = MULTI_MODAL_PARSER_PROMPT

        self.llm = model_gateway.get_llm_from_model_config(self.model_configuration)

        super().__init__(**kwargs)

    async def call_vlm_agent(
        self, base64_image: str, page_number: int
    ) -> Dict[str, Any]:
        logger.info(f"Processing Image... {page_number}")

        content = [
            HumanMessage(
                content=[
                    {"type": "text", "text": self.prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high",
                        },
                    },
                ]
            )
        ]

        try:
            response = await self.llm.ainvoke(content)
            return {"response": (page_number, response.content)}
        except Exception as e:
            error_message = f"Error processing page {page_number}: {str(e)}"
            logger.exception(error_message)
            return {"error": error_message}

    async def get_chunks(
        self, filepath: str, _metadata: Optional[Dict[Any, Any]] = None, *args, **kwargs
    ):
        """
        Asynchronously extracts text from a PDF or image file and returns it in chunks.
        """
        _file_path, file_name = os.path.split(filepath)
        pages = self._get_pages(filepath)

        final_texts = []

        for page_chunk in self._chunk_pages(pages):
            tasks = [
                self.call_vlm_agent(image_b64, page_number)
                for page_number, image_b64 in page_chunk.items()
            ]
            responses = await asyncio.gather(*tasks)

            for response in responses:
                if response and "error" not in response:
                    pg_no, page_content = response["response"]
                    if contains_text(page_content):
                        final_texts.append(
                            self._create_document(
                                file_name, pg_no, page_content, pages[pg_no]
                            )
                        )

            await asyncio.sleep(5)

        return final_texts

    def _get_pages(self, filepath: str) -> Dict[int, str]:
        if filepath.endswith(tuple(MULTI_MODAL_PARSER_SUPPORTED_PDF_EXTENSION)):
            return self._get_pdf_pages(filepath)
        elif filepath.endswith(tuple(MULTI_MODAL_PARSER_SUPPORTED_IMAGE_EXTENSIONS)):
            return self._get_image_page(filepath)
        else:
            raise ValueError(
                "Invalid file extension. Supported formats: PDF, PNG, JPEG, JPG"
            )

    def _get_pdf_pages(self, filepath: str) -> Dict[int, str]:
        pages = {}
        doc = fitz.open(filepath)
        for page in doc:
            try:
                pix = page.get_pixmap(alpha=False)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    (pix.h, pix.w, pix.n)
                )
                _, buffer = cv2.imencode(".png", img)
                pages[page.number + 1] = base64.b64encode(buffer).decode("utf-8")
            except Exception as e:
                logger.exception(f"Error in page {page.number + 1}: {e}")
        return pages

    def _get_image_page(self, filepath: str) -> Dict[int, str]:
        with open(filepath, "rb") as f:
            return {0: base64.b64encode(f.read()).decode("utf-8")}

    def _chunk_pages(self, data: Dict[int, str], size: int = 30):
        it = iter(data)
        for i in range(0, len(data), size):
            yield {k: data[k] for k in islice(it, size)}

    def _create_document(
        self, file_name: str, pg_no: int, page_content: str, image_b64: str
    ) -> Document:
        return Document(
            page_content=f"File Name: {file_name}\n\n{page_content}",
            metadata={
                "image_b64": image_b64,
                "page_number": pg_no,
                "source": file_name,
            },
        )
