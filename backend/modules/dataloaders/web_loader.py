# Author: https://github.com/paulpierre/markdown-crawler/
# Description: A multithreaded web crawler that recursively crawls a website and creates a markdown file for each page.
import mimetypes
import os
import tempfile
from datetime import date
from typing import AsyncGenerator, Dict, List, Tuple
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataSource, LoadedDataPoint

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


async def extract_urls_from_sitemap(url: str) -> List[Tuple[str, str]]:
    sitemap_url = f"{url.rstrip('/')}/sitemap.xml"
    sitemap_content = await fetch_sitemap(sitemap_url)
    if not sitemap_content:
        logger.debug(f"No sitemap found for {url}")
        return [(url, None)]
    logger.debug(f"Found sitemap for {url} at {sitemap_url}")
    soup = BeautifulSoup(sitemap_content, "xml")
    urls = [
        (
            loc.text,
            loc.find_next_sibling("lastmod").text
            if loc.find_next_sibling("lastmod")
            else None,
        )
        for loc in soup.find_all("loc")
    ]
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


class WebLoader(BaseDataLoader):
    """
    Load data from a web URL
    """

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

        urls = [(data_source.uri, None)]

        if data_source.metadata.get("use_sitemap", False):
            urls = await extract_urls_from_sitemap(data_source.uri)
            logger.debug(f"Found a total of {len(urls)} URLs.")

        loaded_data_points: List[LoadedDataPoint] = []

        async with aiohttp.ClientSession() as session:
            for url, lastmod in urls:
                content_hash = lastmod
                # If last modified date is not available, fetch it from the web url
                if not content_hash:
                    logger.debug(f"Cannot find last modified date for {url}.")
                    async with session.head(url) as response:
                        if response.status != 200:
                            logger.warning(
                                f"Failed to fetch {url}: Status {response.status}"
                            )
                            continue

                        # Use ETag or Last-Modified header as the content hash
                        content_hash = (
                            response.headers.get("ETag", None)
                            or response.headers.get("Last-Modified", None)
                            or date.today().isoformat()
                        )
                        logger.debug(
                            f"Last modified date for {url}: {response.headers.get('Last-Modified', 'today')}"
                        )

                else:
                    logger.debug(f"Last modified date for {url}: {content_hash}")

                if previous_snapshot.get(url) == content_hash:
                    logger.debug(f"No changes detected for {url}")
                    continue

                extension = "url"
                local_filepath = url
                if mime := mimetypes.guess_type(url)[0]:
                    extension = mimetypes.guess_extension(mime) or "url"

                if extension != ".url":
                    rel_path, full_path = calculate_full_path(url, extension, dest_dir)
                    async with session.get(url) as response:
                        if response.status != 200:
                            logger.warning(
                                f"Failed to fetch {url}: Status {response.status}"
                            )
                            continue
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, "wb") as f:
                            f.write(await response.read())
                    local_filepath = full_path

                loaded_data_points.append(
                    LoadedDataPoint(
                        data_point_hash=content_hash,
                        data_point_uri=url,
                        data_source_fqn=f"web:{url}",
                        local_filepath=local_filepath,
                        file_extension=extension,
                    )
                )

                if len(loaded_data_points) >= batch_size:
                    yield loaded_data_points
                    loaded_data_points = []

            yield loaded_data_points
