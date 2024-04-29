import base64
import io
import os
import re
from typing import Optional

import cv2
import fitz
import layoutparser as lp
import numpy as np
from huggingface_hub import hf_hub_download
from langchain.docstore.document import Document
from PIL import Image

from backend.logger import logger
from backend.modules.parsers.MultiModalPdfParser.src.llms.gpt4 import GPT4Vision
from backend.modules.parsers.parser import BaseParser
from backend.modules.parsers.utils import contains_text


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


class PdfMultiModalParser(BaseParser):
    """
    TfParser is a multi-modal parser class for deep extraction of pdf documents.
    Requires a running instance of the TfParser service that has access to TFLLM Gateway
    """

    supported_file_extensions = [".pdf"]

    def __init__(
        self, max_chunk_size: int = 1000, chunk_overlap: int = 20, *args, **kwargs
    ):
        """
        Initializes the TfParser object.
        """
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
        self.config_path = os.path.abspath(
            "./backend/modules/parsers/MultiModalPdfParser/src/layout-model/mask_rcnn_X_101_32x8d_FPN_3x.yml"
        )

        self.model_path = download(
            path="./backend/modules/parsers/MultiModalPdfParser/src/layout-model/"
        )
        print(self.model_path)

        self.model = lp.Detectron2LayoutModel(
            config_path=self.config_path,
            model_path=self.model_path,
            extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.4],
            label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
        )
        self.vlm_agent = GPT4Vision()

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
        logger.info("Extracting images from figure blocks...")
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
                                # "image_b64": image_b64,
                                "type": figure.type,
                                "page_number": page_number,
                                "source": file_name,
                            },
                        )
                    )
                    logger.debug(f"Figure response: {response}")

        return parsed_images

    async def _parse_image(self, image_b64: str, page_number: int, file_name: str):
        parsed_images = list()
        page_description = ""

        # get response from VLM for main image
        logger.info("Sending main image to VLM...")
        response = await self.vlm_agent(
            base64_image=image_b64,
            prompt="Summarize the contents of the image in a structured format",
        )

        if "error" in response:
            logger.error(f"Error in VLM: {response['error']}")
            return {"error": response["error"]}
        else:
            logger.info("Received response from VLM...")
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
                logger.debug(f"Main image response: {response}")
                page_description = response

            ########################################################
            # LAYOUT PARSING
            ########################################################
            logger.info("Parsing layout...")
            # Convert the base64 string to an image
            org_image = stringToRGB(image_b64)
            # Detect the layout
            layout = self.model.detect(org_image)
            # Get text and figure blocks
            parsed_blocks = self._get_text_and_figure_blocks(layout, org_image)

            logger.info("Extracting text and images from blocks...")
            # Get text from text blocks and images from figure blocks
            await self._get_text_from_blocks(
                figure_blocks=parsed_blocks,
                image=org_image,
                parsed_images=parsed_images,
                page_number=page_number,
                image_b64=image_b64,
                file_name=file_name,
            ),

            return parsed_images, page_description

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
            file_path, file_name = os.path.split(filepath)

            for page in doc:
                try:
                    page_number = page.number + 1
                    print(f"\n\nProcessing page {page_number}...")

                    # Convert the page to an image (RGB mode)
                    pix = page.get_pixmap(alpha=False)
                    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                        pix.h, pix.w, pix.n
                    )

                    # Convert the image to base64
                    _, buffer = cv2.imencode(".png", img)
                    image_base64 = base64.b64encode(buffer).decode("utf-8")

                    # Send the image to the parse
                    parsed_page_layouts, page_description = await self._parse_image(
                        image_base64, page_number, file_name
                    )

                    if parsed_page_layouts != []:
                        final_texts.extend(parsed_page_layouts)
                    if page_description != "" and page_description is not None:
                        page_texts.append(page_description)
                except Exception as e:
                    print(f"Error in page: {page_number} - {e}")
                    continue
            return final_texts
        except Exception as e:
            print(f"Final Exception: {e}")
            return final_texts
