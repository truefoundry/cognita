# Author: https://github.com/paulpierre/markdown-crawler/
# Description: A multithreaded web crawler that recursively crawls a website and creates a markdown file for each page.
import hashlib
import os
import tempfile
from typing import AsyncGenerator, Dict, List, Tuple
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

from backend.logger import logger
from backend.modules import model_gateway
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import (
    DataIngestionMode,
    DataPoint,
    DataSource,
    LoadedDataPoint,
    ModelConfig,
    ModelProviderConfig,
)

DEFAULT_BASE_DIR = os.path.join(
    tempfile.gettempdir(), "webloader"
)  # temporary directory
DEFAULT_MAX_DEPTH = 2
DEFAULT_NUM_THREADS = 5
DEFAULT_TARGET_LINKS = ["body"]
DEFAULT_TARGET_CONTENT = ["article", "div", "main", "p"]
DEFAULT_DOMAIN_MATCH = True
DEFAULT_BASE_PATH_MATCH = True


async def fetch_sitemap(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


async def extract_urls_from_sitemap(url: str) -> List[str]:
    sitemap_url = f"{url.rstrip('/')}/sitemap.xml"
    sitemap_content = await fetch_sitemap(sitemap_url)
    if not sitemap_content:
        logger.debug(f"No sitemap found for {url}")
        return [url]
    logger.debug(f"Found sitemap for {url} at {sitemap_url}")
    soup = BeautifulSoup(sitemap_content, "xml")
    urls = [loc.text for loc in soup.find_all("loc")]
    return urls


def calculate_full_path(url: str, extension: str, dest_dir: str) -> Tuple[str, str]:
    parsed_url = urlparse(url)
    path = parsed_url.path.strip("/")
    if not path:
        path = "index"
    filename = f"{path}{extension}"
    host = parsed_url.netloc

    rel_path = os.path.join(host, path)
    full_path = os.path.join(dest_dir, rel_path + extension)

    return rel_path, full_path


async def write_file_and_create_hash(content: str, file_path: str) -> str:
    """
    Writes content to a file and returns the hash of the file content.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Calculate hash from the content
    hash_md5 = hashlib.md5(content.encode("utf-8"))

    # Write content to file
    with open(file_path, "w") as f:
        f.write(content)

    return hash_md5.hexdigest()


class WebLoader(BaseDataLoader):
    """
    Load data from a web URL
    """

    def model_config_to_extraction_strategy(
        self, model_config: ModelConfig, prompt: str
    ) -> LLMExtractionStrategy:
        model_provider_config: ModelProviderConfig = (
            model_gateway.model_name_to_provider_config[model_config.name]
        )
        if not model_config.parameters:
            model_config.parameters = {}
        if not model_provider_config.api_key_env_var:
            api_key = "EMPTY"
        else:
            api_key = os.environ.get(model_provider_config.api_key_env_var, "")

        os.environ["LITELLM_PROXY_API_KEY"] = api_key
        os.environ["LITELLM_PROXY_API_BASE"] = model_provider_config.base_url
        model_id = "litellm_proxy" + "/".join(model_config.name.split("/")[1:])
        return LLMExtractionStrategy(
            instruction=prompt,
            model=model_id,
            temperature=model_config.parameters.get("temperature", 0.1),
            default_headers=model_provider_config.default_headers,
        )

    async def load_filtered_data(
        self,
        data_source: DataSource,
        dest_dir: str,
        previous_snapshot: Dict[str, str],
        batch_size: int,
        data_ingestion_mode: DataIngestionMode,
    ) -> AsyncGenerator[List[LoadedDataPoint], None]:
        """
        Loads data from a web URL and converts it to Markdown format.
        """

        if not data_source.uri.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid URL: {data_source.uri}. URL must start with http:// or https://"
            )

        urls = await extract_urls_from_sitemap(data_source.uri)

        logger.debug(f"Found a total of {len(urls)} URLs.")

        loaded_data_points: List[LoadedDataPoint] = []
        dest_dir = DEFAULT_BASE_DIR

        js_code = data_source.metadata.get("js_code", None)
        wait_for = data_source.metadata.get("wait_for", None)
        css_selector = data_source.metadata.get("css_selector", None)
        extraction_strategy = None
        if model_config := data_source.metadata.get("model_config", None):
            extraction_strategy = self.model_config_to_extraction_strategy(
                model_config, data_source.metadata.get("prompt", "")
            )

        async with AsyncWebCrawler(verbose=True) as crawler:
            for url in urls:
                result = await crawler.arun(
                    url=url,
                    bypass_cache=True,
                    js_code=js_code,
                    wait_for=wait_for,
                    css_selector=css_selector,
                    extraction_strategy=extraction_strategy,
                )
                assert result.success, f"Failed to crawl the page: {url}"

                if extraction_strategy:
                    data = result.extracted_content
                    file_ext = ".json"
                else:
                    data = result.markdown
                    file_ext = ".md"

                rel_path, full_path = calculate_full_path(url, file_ext, dest_dir)

                file_hash = await write_file_and_create_hash(data, full_path)

                data_point = DataPoint(
                    data_source_fqn=data_source.fqn,
                    data_point_uri=rel_path,
                    data_point_hash=file_hash,
                    local_filepath=full_path,
                    file_extension=file_ext,
                )

                # If the data ingestion mode is incremental, check if the data point already exists.
                if (
                    data_ingestion_mode == DataIngestionMode.INCREMENTAL
                    and previous_snapshot.get(data_point.data_point_fqn)
                    and previous_snapshot.get(data_point.data_point_fqn)
                    == data_point.data_point_hash
                ):
                    continue

                loaded_data_points.append(
                    LoadedDataPoint(
                        data_point_hash=data_point.data_point_hash,
                        data_point_uri=data_point.data_point_uri,
                        data_source_fqn=data_point.data_source_fqn,
                        local_filepath=full_path,
                        file_extension=file_ext,
                    )
                )
                if len(loaded_data_points) >= batch_size:
                    yield loaded_data_points
                    loaded_data_points.clear()

        yield loaded_data_points
