# Author: https://github.com/paulpierre/markdown-crawler/
# Description: A multithreaded web crawler that recursively crawls a website and creates a markdown file for each page.
from bs4 import BeautifulSoup
import urllib.parse
import threading
from markdownify import markdownify as md
import requests
import logging
import queue
import time
import os
import re
import json
import tempfile
from typing import (
    List,
    Optional,
    Union,
    Dict, 
    Iterator
)

from backend.logger import logger
from backend.modules.dataloaders.loader import BaseDataLoader
from backend.types import DataIngestionMode, DataPoint, DataSource, LoadedDataPoint


DEFAULT_BASE_DIR = os.path.join(tempfile.gettempdir(), 'webloader')  # temporary directory
DEFAULT_MAX_DEPTH = 2
DEFAULT_NUM_THREADS = 5
DEFAULT_TARGET_CONTENT = ['article', 'div', 'main', 'p']
DEFAULT_TARGET_LINKS = ['body']
DEFAULT_DOMAIN_MATCH = True
DEFAULT_BASE_PATH_MATCH = True


class WebLoader(BaseDataLoader):
    """
    This loader handles web URLs
    """

    # --------------
    # URL validation
    # --------------
    def _is_valid_url(self, url: str) -> bool:
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            logger.debug(f'❌ Invalid URL {url}')
            return False
        
    # ----------------
    # Clean up the URL
    # ----------------
    def _normalize_url(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), None, None, None))

    def _get_target_content(
        self,
        soup: BeautifulSoup,
        target_content: Union[List[str], None] = None
    ) -> str:

        content = ''

        # -------------------------------------
        # Get target content by target selector
        # -------------------------------------
        if target_content:
            for target in target_content:
                for tag in soup.select(target):
                    content += f'{str(tag)}'.replace('\n', '')

        # ---------------------------
        # Naive estimation of content
        # ---------------------------
        else:
            max_text_length = 0
            for tag in soup.find_all(DEFAULT_TARGET_CONTENT):
                text_length = len(tag.get_text())
                if text_length > max_text_length:
                    max_text_length = text_length
                    main_content = tag

            content = str(main_content)

        return content if len(content) > 0 else False
    

    def _get_target_links(
        self,
        soup: BeautifulSoup,
        base_url: str,
        target_links: List[str] = DEFAULT_TARGET_LINKS,
        valid_paths: Union[List[str], None] = None,
        is_domain_match: Optional[bool] = DEFAULT_DOMAIN_MATCH,
        is_base_path_match: Optional[bool] = DEFAULT_BASE_PATH_MATCH
    ) -> List[str]:

        child_urls = []

        # Get all urls from target_links
        for target in soup.find_all(target_links):
            # Get all the links in target
            for link in target.find_all('a'):
                child_urls.append(urllib.parse.urljoin(base_url, link.get('href')))

        result = []
        for u in child_urls:

            child_url = urllib.parse.urlparse(u)

            # ---------------------------------
            # Check if domain match is required
            # ---------------------------------
            if is_domain_match and child_url.netloc != urllib.parse.urlparse(base_url).netloc:
                continue

            if is_base_path_match and child_url.path.startswith(urllib.parse.urlparse(base_url).path):
                result.append(u)
                continue

            if valid_paths:
                for valid_path in valid_paths:
                    if child_url.path.startswith(urllib.parse.urlparse(valid_path).path):
                        result.append(u)
                        break

        return result



    # ------------------
    # HTML parsing logic
    # ------------------
    def _crawl(
        self,
        url: str,
        base_url: str,
        already_crawled: set,
        file_path: str,
        target_links: Union[str, List[str]] = DEFAULT_TARGET_LINKS,
        target_content: Union[str, List[str]] = None,
        valid_paths: Union[str, List[str]] = None,
        is_domain_match: Optional[bool] = DEFAULT_DOMAIN_MATCH,
        is_base_path_match: Optional[bool] = DEFAULT_BASE_PATH_MATCH,
        is_links: Optional[bool] = False,
    ) -> List[str]:

        if url in already_crawled:
            return []
        try:
            logger.debug(f'Crawling: {url}')
            response = requests.get(url)
        except requests.exceptions.RequestException as e:
            logger.error(f'❌ Request error for {url}: {e}')
            return []
        if 'text/html' not in response.headers.get('Content-Type', ''):
            logger.error(f'❌ Content not text/html for {url}')
            return []
        already_crawled.add(url)

        # ---------------------------------
        # List of elements we want to strip
        # ---------------------------------
        strip_elements = []

        if is_links:
            strip_elements = ['a']

        # -------------------------------
        # Create BS4 instance for parsing
        # -------------------------------
        soup = BeautifulSoup(response.text, 'html.parser')

        # Strip unwanted tags
        for script in soup(['script', 'style']):
            script.decompose()

        # --------------------------------------------
        # Write the markdown file if it does not exist
        # --------------------------------------------
        if not os.path.exists(file_path):

            file_name = file_path.split("/")[-1]

            # ------------------
            # Get target content
            # ------------------

            content = self._get_target_content(soup, target_content=target_content)

            if content:
                # logger.error(f'❌ Empty content for {file_path}. Please check your targets skipping.')
                # return []

                # --------------
                # Parse markdown
                # --------------
                output = md(
                    content,
                    keep_inline_images_in=['td', 'th', 'a', 'figure'],
                    strip=strip_elements
                )

                # ------------------------------
                # Write markdown content to file
                # ------------------------------
                with open(file_path, 'w') as f:
                    f.write(output)

                logger.debug(f'Created 📝 {file_name} at {file_path}')
                    
            else:
                logger.error(f'❌ Empty content for {file_path}. Please check your targets skipping.')

        child_urls = self._get_target_links(
            soup,
            base_url,
            target_links,
            valid_paths=valid_paths,
            is_domain_match=is_domain_match,
            is_base_path_match=is_base_path_match    
        )

        logger.debug(f'Found {len(child_urls) if child_urls else 0} child URLs')
        return child_urls
    

    # ------------------
    # Worker thread logic
    # ------------------
    def _worker(
        self,
        q: object,
        base_url: str,
        max_depth: int,
        already_crawled: set,
        base_dir: str,
        target_links: Union[List[str], None] = DEFAULT_TARGET_LINKS,
        target_content: Union[List[str], None] = None,
        valid_paths: Union[List[str], None] = None,
        is_domain_match: bool = None,
        is_base_path_match: bool = None,
        is_links: Optional[bool] = False
    ) -> None:

        while not q.empty():
            depth, url = q.get()
            if depth > max_depth:
                continue
            file_name = '-'.join(re.findall(r'\w+', urllib.parse.urlparse(url).path))
            file_name = 'index' if not file_name else file_name
            file_path = f'{base_dir.rstrip("/") + "/"}{file_name}.md'

            child_urls = self._crawl(
                url,
                base_url,
                already_crawled,
                file_path,
                target_links,
                target_content,
                valid_paths,
                is_domain_match,
                is_base_path_match,
                is_links,
            )
            child_urls = [self._normalize_url(u) for u in child_urls]
            for child_url in child_urls:
                q.put((depth + 1, child_url))
            time.sleep(1)


    # -----------------
    # Thread management
    # -----------------
    def md_crawl(
        self,
        base_url: str,
        max_depth: Optional[int] = DEFAULT_MAX_DEPTH,
        num_threads: Optional[int] = DEFAULT_NUM_THREADS,
        base_dir: Optional[str] = DEFAULT_BASE_DIR,
        target_links: Union[str, List[str]] = DEFAULT_TARGET_LINKS,
        target_content: Union[str, List[str]] = None,
        valid_paths: Union[str, List[str]] = None,
        is_domain_match: Optional[bool] = None,
        is_base_path_match: Optional[bool] = None,
        is_debug: Optional[bool] = False,
        is_links: Optional[bool] = False
    ) -> None:
        if is_domain_match is False and is_base_path_match is True:
            raise ValueError('❌ Domain match must be True if base match is set to True')

        is_domain_match = DEFAULT_DOMAIN_MATCH if is_domain_match is None else is_domain_match
        is_base_path_match = DEFAULT_BASE_PATH_MATCH if is_base_path_match is None else is_base_path_match

        if not base_url:
            raise ValueError('❌ Base URL is required')

        if isinstance(target_links, str):
            target_links = target_links.split(',') if ',' in target_links else [target_links]

        if isinstance(target_content, str):
            target_content = target_content.split(',') if ',' in target_content else [target_content]

        if isinstance(valid_paths, str):
            valid_paths = valid_paths.split(',') if ',' in valid_paths else [valid_paths]

        if is_debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.debug('🐞 Debugging enabled')
        else:
            logging.basicConfig(level=logging.INFO)

        logger.info(f'🕸️ Crawling {base_url} at ⏬ depth {max_depth} with 🧵 {num_threads} threads')

        # Validate the base URL
        if not self._is_valid_url(base_url):
            raise ValueError('❌ Invalid base URL')

        # Create base_dir if it doesn't exist
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        already_crawled = set()

        # Create a queue of URLs to crawl
        q = queue.Queue()

        # Add the base URL to the queue
        q.put((0, base_url))

        threads = []

        # Create a thread for each URL in the queue
        for i in range(num_threads):
            t = threading.Thread(
                target=self._worker,
                args=(
                    q,
                    base_url,
                    max_depth,
                    already_crawled,
                    base_dir,
                    target_links,
                    target_content,
                    valid_paths,
                    is_domain_match,
                    is_base_path_match,
                    is_links
                )
            )
            threads.append(t)
            t.start()
            logger.debug(f'Started thread {i+1} of {num_threads}')

        # Wait for all threads to finish
        for t in threads:
            t.join()
        
        logger.info('🏁 All threads have finished')
        

    def load_filtered_data(
        self,
        data_source: DataSource,
        dest_dir: str,
        previous_snapshot: Dict[str, str],
        batch_size: int,
        data_ingestion_mode: DataIngestionMode,
    ) -> Iterator[List[LoadedDataPoint]]:
        """
        Loads data from a web URL and converts it to Markdown format.
        """
        # max_depth = data_source.metadata.get("max_depth", 2)
        # print("WebLoader -> max_depth: ", max_depth)
        # self.loader = RecursiveUrlLoader(
        #     url=data_source.uri,
        #     max_depth=max_depth,
        #     extractor=lambda x: self._remove_empty_lines(
        #         markdownify.markdownify(self._remove_tags(x))
        #     ),
        # )
        # webpages = self.loader.load()

        self.md_crawl(
            base_url=data_source.uri,
            max_depth=DEFAULT_MAX_DEPTH,
        )

        loaded_data_points: List[LoadedDataPoint] = []
        dest_dir = DEFAULT_BASE_DIR
        for root, d_names, f_names in os.walk(dest_dir):
            for f in f_names:
                if f.startswith("."):
                    continue
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, dest_dir)
                file_ext = os.path.splitext(f)[1]
                data_point = DataPoint(
                    data_source_fqn=data_source.fqn,
                    data_point_uri=rel_path,
                    data_point_hash=str(os.path.getsize(full_path)),
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

