import os
from typing import Any, Dict, List, Optional

import aiofiles
import aiofiles.os
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from langchain.docstore.document import Document
from pydantic import BaseModel

from backend.logger import logger
from backend.modules.model_gateway.model_gateway import model_gateway
from backend.modules.parsers.parser import PARSER_REGISTRY, BaseParser


class WebModelConfig(BaseModel):
    name: str
    prompt: str


class FinalParserConfig(BaseModel):
    name: str
    parameters: Optional[Dict[str, Any]] = None


class WebParserConfig(BaseModel):
    js_code: Optional[str] = None
    wait_for: Optional[str] = None
    css_selector: Optional[str] = None
    llm_extraction_config: Optional[WebModelConfig] = None
    final_parser: Optional[FinalParserConfig] = FinalParserConfig(
        name="UnstructuredIoParser"
    )


class WebParser(BaseParser):
    """
    WebParser is a parser class for extracting text from audio input.

    {
        "url": {
            "name": "WebParser",
            "parameters": {
                "js_code": "",
                "wait_for": "",
                "css_selector": "article",
                "llm_extraction_config": {
                    "name": "openai/gpt-4o-mini",
                    "prompt": "Summarize the webpage"
                },
                "final_parser": {
                    "name": "UnstructuredIoParser",
                    "parameters": {}
                }
            }
        }
    }

    """

    supported_file_extensions = [
        "url",
    ]

    def __init__(self, *, max_chunk_size: int = 2000, **kwargs):
        """
        Initializes the AudioParser object.
        """
        self.config = WebParserConfig.model_validate(kwargs)

        self.max_chunk_size = max_chunk_size
        super().__init__(**kwargs)

    def model_config_to_extraction_strategy(
        self, model_config: WebModelConfig
    ) -> LLMExtractionStrategy:
        model_provider_config = model_gateway.get_model_provider_config(
            model_config.name
        )

        model_params = model_config.get("parameters", {})

        if not model_provider_config.api_key_env_var:
            api_key = "EMPTY"
        else:
            api_key = os.environ.get(model_provider_config.api_key_env_var, "")

        os.environ["LITELLM_PROXY_API_KEY"] = api_key
        os.environ["LITELLM_PROXY_API_BASE"] = model_provider_config.base_url
        model_id = "litellm_proxy" + "/".join(model_config.name.split("/")[1:])
        return LLMExtractionStrategy(
            instruction=model_config.prompt,
            model=model_id,
            api_token=api_key,
            temperature=model_params.get("temperature", 0.1),
            default_headers=model_provider_config.default_headers,
        )

    async def get_chunks(
        self, url: str, metadata: Dict[Any, Any] | None, **kwargs
    ) -> List[Document]:
        """
        Get the chunks of the audio file.
        """

        if self.config.final_parser.name not in PARSER_REGISTRY:
            raise ValueError(
                f"Final parser {self.config.final_parser} not registered in the parser registry."
            )

        try:
            extraction_strategy = None
            if self.config.llm_extraction_config:
                if not self.config.prompt:
                    raise ValueError("Prompt is required for model configuration.")
                extraction_strategy = self.model_config_to_extraction_strategy(
                    self.config.llm_extraction_config
                )

            async with AsyncWebCrawler(verbose=True) as crawler:
                result = await crawler.arun(
                    url=url,
                    bypass_cache=True,
                    js_code=self.config.js_code,
                    wait_for=self.config.wait_for,
                    css_selector=self.config.css_selector,
                    extraction_strategy=extraction_strategy,
                )
                assert result.success, f"Failed to crawl the page: {url}"

                data = result.extracted_content
                file_ext = ".json"

                tempfile_name = None

                async with aiofiles.tempfile.NamedTemporaryFile(
                    mode="w", suffix=file_ext, delete=False
                ) as temp_file:
                    await temp_file.write(data)
                    tempfile_name = temp_file.name

                # Split the text into chunks
                parser: BaseParser = PARSER_REGISTRY[self.config.final_parser.name](
                    **(self.config.final_parser.parameters or {})
                )

                final_texts = await parser.get_chunks(
                    filepath=tempfile_name, metadata=metadata
                )

                # Remove the temporary file
                try:
                    await aiofiles.os.remove(tempfile_name)
                    logger.info(f"Removed temporary file: {tempfile_name}")
                except Exception as e:
                    logger.exception(f"Error in removing temporary file: {e}")

                return final_texts

        except Exception as e:
            logger.exception(f"Error in getting chunks: {e}")
            raise e
