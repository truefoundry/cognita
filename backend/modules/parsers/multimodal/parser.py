import asyncio
import base64
import io
import json
import os
import pathlib
from typing import Any, Optional

import aiohttp
import cv2
import fitz
import layoutparser as lp
import numpy as np
import requests
from huggingface_hub import hf_hub_download
from langchain.docstore.document import Document
from PIL import Image

from backend.logger import logger
from backend.modules.parsers.parser import BaseParser
from backend.modules.parsers.utils import contains_text
from backend.settings import settings


def download(path):
    downloaded_path = hf_hub_download(
        repo_id="truefoundry/layout-parser",
        filename="mask_rcnn_X_101_32x8d_FPN_3x.pth",
        local_dir=path,
    )
    return downloaded_path


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

        self.layout_parser = False

        if "layout_parser" in additional_config:
            self.layout_parser = True

        if self.layout_parser:
            base_path = pathlib.Path(__file__).parent.resolve()
            self.config_path = os.path.join(
                base_path, "layout-model/mask_rcnn_X_101_32x8d_FPN_3x.yml"
            )

            if not os.path.exists(
                os.path.join(base_path, "layout-model/mask_rcnn_X_101_32x8d_FPN_3x.pth")
            ):
                print("Downloading model...")
                self.model_path = download(path=os.path.join(base_path, "layout-model"))
            else:
                print("Model already exists...")
                self.model_path = os.path.join(
                    base_path, "layout-model/mask_rcnn_X_101_32x8d_FPN_3x.pth"
                )

            self.model = lp.Detectron2LayoutModel(
                config_path=self.config_path,
                model_path=self.model_path,
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.4],
                label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
            )
        # Multi-modal parser needs to be configured with the base url, vision model and summary model
        if "base_url" in additional_config:
            self.client = additional_config["base_url"]
            print(f"Using custom base url..., {self.client}")
        else:
            self.client = (
                settings.TFY_LLM_GATEWAY_URL.strip("/") + "/openai/chat/completions"
            )

        if "vision_model" in additional_config:
            self.vision_model = additional_config["vision_model"]
            print(f"Using custom vision model..., {self.vision_model}")
        else:
            self.vision_model = "openai-main/gpt-4-turbo"

        if "summary_model" in additional_config:
            self.summary_model = additional_config["summary_model"]
            print(f"Using custom summary model..., {self.summary_model}")
        else:
            self.summary_model = "openai-main/gpt-3-5-turbo"

    async def _send_request(self, payload):
        response = requests.post(
            self.client,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.TFY_API_KEY}",
                # Set the tfy_log_request to "true" in X-TFY-METADATA header to log prompt and response for the request
                "X-TFY-METADATA": json.dumps(
                    {"tfy_log_request": "true", "Custom-Metadata": "Custom-Value"}
                ),
            },
            json=payload,
        )
        return response.json()

    # TODO: Remove this function later, use call_vlm_agent instead
    async def vlm_agent(
        self,
        base64_image: str,
        prompt: str = "Describe the information present in the image in a structured format.",
    ) -> Any:
        logger.debug(f"Processing Image...")
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

        response = await self._send_request(payload)
        if "choices" in response:
            return {"response": response["choices"][0]["message"]["content"]}
        if "error" in response:
            return {"error": response["error"]}

    async def call_vlm_agent(
        self,
        base64_image: str,
        page_number: int,
        prompt: str = "Describe the information present in the image in a structured format.",
    ):
        print(f"Processing Image... {page_number}")
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

    async def summarize(self, text: str):
        logger.debug(f"Summarizing text...")
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "Generate a detailed summary of the given document.",
                },
                {"role": "user", "content": text},
            ],
            "model": self.summary_model,
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 0.9,
            "top_k": 50,
            "repetition_penalty": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop": ["</s>"],
        }

        response = await self._send_request(payload)
        if "choices" in response:
            output = response["choices"][0]["message"]["content"]
            return {"page_content": output}
        if "error" in response:
            return {"error": response["error"]}

    def _get_text_and_figure_blocks(self, layout, image):
        # Get the text and figure blocks
        figure_blocks = lp.Layout(
            [b for b in layout if b.type == "Figure"]
            + [b for b in layout if b.type == "Table"]
            + [b for b in layout if b.type == "List"]
        )

        text_blocks = lp.Layout(
            [b for b in layout if b.type == "Text"]
            + [b for b in layout if b.type == "Title"]
        )
        # remove text from figure blocks
        text_blocks = lp.Layout(
            [
                b
                for b in text_blocks
                if not any(b.is_in(b_fig) for b_fig in figure_blocks)
            ]
        )

        # sort text regions
        h, w = image.shape[:2]
        left_interval = lp.Interval(0, w / 2 * 1.05, axis="x").put_on_canvas(image)

        left_blocks = text_blocks.filter_by(left_interval, center=True)
        left_blocks.sort(key=lambda b: b.coordinates[1], inplace=True)

        right_blocks = [b for b in text_blocks if b not in left_blocks]
        right_blocks = sorted(right_blocks, key=lambda b: b.coordinates[1])

        # And finally combine the two list and add the index according to the order
        text_blocks = lp.Layout(
            [b.set(id=idx) for idx, b in enumerate(left_blocks + right_blocks)]
        )

        return text_blocks + figure_blocks

    async def _get_text_from_blocks(
        self,
        figure_blocks: list,
        image,
        page_number: int,
        image_b64: str,
        parsed_images: list,
        file_name: str,
    ):
        print("Extracting images from figure blocks...")
        for figure in figure_blocks:
            # Crop the figure block from the main image
            # Some padding is added to the crop to ensure the entire figure is included
            cropped_image_array = figure.pad(
                left=40, right=5, top=40, bottom=40
            ).crop_image(image)
            # Convert the cropped image to a base64 string
            cropped_image_b64 = arrayToBase64(cropped_image_array)

            # send the cropped image to the VLM
            response = await self.vlm_agent(cropped_image_b64)

            if "error" in response:
                logger.error(f"Error in VLM: {response['error']}")
            else:
                response = response["response"].strip()
                if contains_text(response):
                    parsed_images.append(
                        Document(
                            page_content=response,
                            metadata={
                                "image_b64": image_b64,
                                "type": figure.type,
                                "page_number": page_number,
                                "source": file_name,
                            },
                        )
                    )
                    print(f"Figure response: {response} ----- Page: {page_number}")

    async def _parse_image_with_layout(
        self, image_b64: str, page_number: int, file_name: str
    ):
        parsed_images = list()

        # get response from VLM for main image
        print("Sending main image to VLM...")
        response = await self.vlm_agent(
            base64_image=image_b64,
            prompt="Summarize the contents of the image in a structured format",
        )

        if "error" in response:
            logger.error(f"Error in VLM: {response['error']}")
            return {"error": response["error"]}
        else:
            print("Received response from VLM...")
            response = response["response"].strip()
            if contains_text(response):
                parsed_images.append(
                    Document(
                        page_content=response,
                        metadata={
                            "image_b64": image_b64,
                            "type": "Figure",
                            "page_number": page_number,
                            "source": file_name,
                            "category": "main_image",
                        },
                    )
                )
                print(f"Main image response: {response}")

            if self.layout_parser:
                ########################################################
                # LAYOUT PARSING
                ########################################################
                print("Parsing layout...")
                # Convert the base64 string to an image
                org_image = stringToRGB(image_b64)
                # Detect the layout
                layout = self.model.detect(org_image)
                # Get text and figure blocks
                parsed_blocks = self._get_text_and_figure_blocks(layout, org_image)

                print("Extracting text and images from blocks...")
                # Get text from text blocks and images from figure blocks
                await self._get_text_from_blocks(
                    figure_blocks=parsed_blocks,
                    image=org_image,
                    parsed_images=parsed_images,
                    page_number=page_number,
                    image_b64=image_b64,
                    file_name=file_name,
                )

                all_page_content = " ".join(
                    [page.page_content for page in parsed_images]
                )
                page_summary = await self.summarize(all_page_content)

                parsed_images.append(
                    Document(
                        page_content=page_summary["page_content"],
                        metadata={
                            "image_b64": image_b64,
                            "type": "Summary",
                            "source": file_name,
                            "category": "summary",
                        },
                    )
                )

            return parsed_images

    async def get_chunks(
        self, filepath: str, metadata: Optional[dict] = None, *args, **kwargs
    ):
        """
        Asynchronously extracts text from a PDF file and returns it in chunks.
        """
        if not filepath.endswith(".pdf"):
            print("Invalid file extension. MultiModalParser only supports PDF files.")
            return []

        final_texts = list()
        try:
            # Open the PDF file using pdfplumber
            doc = fitz.open(filepath)

            # get file path & name
            file_path, file_name = os.path.split(filepath)
            pages = dict()

            # Iterate over each page in the PDF
            print(f"\n\nLoading all pages...")
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
                    print(f"Error in page: {page_number} - {e}")
                    continue

            if self.layout_parser:
                for page_number, image_b64 in pages.items():
                    print(f"\n\nProcessing page {page_number}...")

                    # Parse the image with layout
                    parsed_page_layouts = await self._parse_image_with_layout(
                        image_b64=image_b64,
                        page_number=page_number,
                        file_name=file_name,
                    )

                    if parsed_page_layouts != []:
                        final_texts.extend(parsed_page_layouts)
            else:
                # make parallel requests to VLM for all pages
                prompt = "You are an AI assistant with the multi-modal/vision conversational capabilities. Your role provide clear explanation of an image for another AI assistant to accomplish a information retrieval task. Provide detailed and insightful responses for image inputs while engaging in meaningful discussions. Your aim is to offer clear explanations and precise explanations for a wide range of topics, leveraging a unique blend of text and image understanding.Your responses should demonstrate your proficiency in explaining complex concepts with precision and clarity, contributing to the exemplary nature of the multi-modal conversational assistant."
                tasks = [
                    self.call_vlm_agent(
                        base64_image=image_b64, page_number=page_number, prompt=prompt
                    )
                    for page_number, image_b64 in pages.items()
                ]
                responses = await asyncio.gather(*tasks)

                for response in responses:
                    if "error" in response:
                        print(f"Error in page: {response['error']}")
                        continue
                    else:
                        pg_no, page_content = response["response"]
                        if contains_text(page_content):
                            print("Processed page: ", pg_no)
                            final_texts.append(
                                Document(
                                    page_content="File Name: "
                                    + file_name
                                    + "\n\n"
                                    + page_content
                                    + "\n\nFile Name: "
                                    + file_name,
                                    metadata={
                                        "image_b64": pages[pg_no],
                                        "type": "Figure",
                                        "page_number": pg_no,
                                        "source": file_name,
                                        "category": "main_image",
                                    },
                                )
                            )

            return final_texts
        except Exception as e:
            print(f"Final Exception: {e}")
            return final_texts
