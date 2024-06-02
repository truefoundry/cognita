import asyncio
import base64
import io
import json
import os
import pathlib
from itertools import islice
from typing import Any, Optional

import aiohttp
import cv2
import fitz
import numpy as np
import requests
from langchain.docstore.document import Document
from PIL import Image

from backend.logger import logger
from backend.modules.parsers.parser import BaseParser
from backend.modules.parsers.utils import contains_text
from backend.settings import settings


def stringToRGB(base64_string: str):
    imgdata = base64.b64decode(str(base64_string))
    img = Image.open(io.BytesIO(imgdata))
    opencv_img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
    return opencv_img


def arrayToBase64(image_arr: np.ndarray):
    image = Image.fromarray(image_arr)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()

    encoded = base64.b64encode(img_bytes)
    base64_str = encoded.decode("utf-8")
    return base64_str


class MultiModalParser(BaseParser):
    """
    MultiModalParser is a multi-modal parser class for deep extraction of pdf documents
    """

    supported_file_extensions = [".pdf"]

    def __init__(
        self,
        max_chunk_size: int = 1000,
        chunk_overlap: int = 20,
        additional_config: dict = {},
        *args,
        **kwargs,
    ):
        """
        Initializes the MultiModalParser object.
        """
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap

        # Multi-modal parser needs to be configured with the openai compatible client url and vision model
        if "base_url" in additional_config:
            self.client = additional_config["base_url"]
            logger.info(f"Using custom base url..., {self.client}")
        else:
            self.client = (
                settings.TFY_LLM_GATEWAY_URL.strip("/") + "/openai/chat/completions"
            )

        if "vision_model" in additional_config:
            self.vision_model = additional_config["vision_model"]
            logger.info(f"Using custom vision model..., {self.vision_model}")
        else:
            self.vision_model = "openai-main/gpt-4-turbo"

        if "prompt" in additional_config:
            self.prompt = additional_config["prompt"]
            logger.info(f"Using custom prompt..., {self.prompt}")
        else:
            self.prompt = """Given an image containing one or more charts/graphs, and texts, provide a detailed analysis of the data represented in the charts. Your task is to analyze the image and provide insights based on the data it represents.
Specifically, the information should include but not limited to:
Title of the Image: Provide a title from the charts or image if any.
Type of Chart: Determine the type of each chart (e.g., bar chart, line chart, pie chart, scatter plot, etc.) and its key features (e.g., labels, legends, data points).
Data Trends: Describe any notable trends or patterns visible in the data. This may include increasing/decreasing trends, seasonality, outliers, etc.
Key Insights: Extract key insights or observations from the charts. What do the charts reveal about the underlying data? Are there any significant findings that stand out?
Data Points: Identify specific data points or values represented in the charts, especially those that contribute to the overall analysis or insights.
Comparisons: Compare different charts within the same image or compare data points within a single chart. Highlight similarities, differences, or correlations between datasets.
Conclude with a summary of the key findings from your analysis and any recommendations based on those findings."""

    async def call_vlm_agent(
        self,
        base64_image: str,
        page_number: int,
        prompt: str = "Describe the information present in the image in a structured format.",
    ):
        logger.info(f"Processing Image... {page_number}")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.TFY_API_KEY}",
            # Set the tfy_log_request to "true" in X-TFY-METADATA header to log prompt and response for the request
            "X-TFY-METADATA": json.dumps(
                {"tfy_log_request": "true", "Custom-Metadata": "Custom-Value"}
            ),
        }
        # Parallel calls to VLM
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": 2048,
            }
            async with session.post(
                self.client, json=payload, headers=headers
            ) as response:
                result = await response.json(content_type=response.content_type)
                if "choices" in result:
                    return {
                        "response": [
                            page_number,
                            result["choices"][0]["message"]["content"],
                        ]
                    }
                if "error" in result:
                    return {"error": result["error"]}

    async def get_chunks(
        self, filepath: str, metadata: Optional[dict] = None, *args, **kwargs
    ):
        """
        Asynchronously extracts text from a PDF file and returns it in chunks.
        """

        try:
            if not filepath.endswith(".pdf"):
                logger.error(
                    "Invalid file extension. MultiModalParser only supports PDF files."
                )
                return []

            final_texts = list()
            # Open the PDF file using pdfplumber
            doc = fitz.open(filepath)

            # get file path & name
            file_path, file_name = os.path.split(filepath)
            pages = dict()

            # Iterate over each page in the PDF
            logger.info(f"\n\nLoading all pages...")
            for page in doc:
                try:
                    page_number = page.number + 1
                    # Convert the page to an image (RGB mode)
                    pix = page.get_pixmap(alpha=False)
                    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                        pix.h, pix.w, pix.n
                    )

                    # Convert the image to base64
                    _, buffer = cv2.imencode(".png", img)
                    image_base64 = base64.b64encode(buffer).decode("utf-8")

                    pages[page_number] = image_base64
                except Exception as e:
                    logger.error(f"Error in page: {page_number} - {e}")
                    continue

            # make parallel requests to VLM for all pages
            prompt = self.prompt

            def break_chunks(data, size=30):
                it = iter(data)
                for i in range(0, len(data), size):
                    yield {k: data[k] for k in islice(it, size)}

            for page_items in break_chunks(pages):
                tasks = [
                    self.call_vlm_agent(
                        base64_image=image_b64,
                        page_number=page_number,
                        prompt=prompt,
                    )
                    for page_number, image_b64 in page_items.items()
                ]
                responses = await asyncio.gather(*tasks)

                logger.info("Total Responses:", len(responses))

                if responses is not None:
                    for response in responses:
                        if response is not None:
                            if "error" in response:
                                logger.error(f"Error in page: {response['error']}")
                                continue
                            else:
                                pg_no, page_content = response["response"]
                                if contains_text(page_content):
                                    logger.debug(f"Processed page: {pg_no}")
                                    final_texts.append(
                                        Document(
                                            page_content="File Name: "
                                            + file_name
                                            + "\n\n"
                                            + page_content,
                                            metadata={
                                                "image_b64": pages[pg_no],
                                                "page_number": pg_no,
                                                "source": file_name,
                                            },
                                        )
                                    )
                else:
                    logger.debug("No response from VLM...")
                await asyncio.sleep(5)
            return final_texts
        except Exception as e:
            logger.error(f"Final Exception: {e}")
            return final_texts
