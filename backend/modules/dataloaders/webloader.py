import os
import shutil

import markdownify
from bs4 import BeautifulSoup as Soup
from langchain.document_loaders.recursive_url_loader import RecursiveUrlLoader

from backend.modules.dataloaders.loader import BaseLoader
from backend.utils.logger import logger


class WebLoader(BaseLoader):
    """
    This loader handles web URLs
    """

    type = "web"

    def _remove_empty_lines(text):
        lines = text.split("\n")
        non_empty_lines = [line for line in lines if line.strip() != ""]
        return "\n".join(non_empty_lines)

    def _remove_tags(html):
        # parse html content
        soup = Soup(html, "html.parser")

        for data in soup(["style", "script"]):
            # Remove tags
            data.decompose()

        # return data by retrieving the tag content
        return " ".join([str(d) for d in soup])

    def load_data(self, source_uri, dest_dir):
        """
        Loads data from a local directory specified by the given source URI.

        Args:
            source_uri (str): The source URI of the website
            dest_dir (str): The destination directory where the data will be copied to.

        Returns:
            None
        """
        # Check if the source_dir is a relative path or an absolute path.
        loader = RecursiveUrlLoader(
            url=source_uri,
            max_depth=2,
            extractor=lambda x: self._remove_empty_lines(
                markdownify.markdownify(self._remove_tags(x))
            ),
        )
        docs = loader.load()
        with open(os.path.join(dest_dir, "index.md"), "w") as file:
            for doc in docs:
                text = doc.page_content
                if "description" in doc.metadata:
                    text = f"# {doc.metadata['description']}\n"
                if "title" in doc.metadata:
                    text = f"# {doc.metadata['title']}\n"
