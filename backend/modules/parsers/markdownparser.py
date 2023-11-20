import typing

from langchain.docstore.document import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter

from backend.utils.logger import logger
from backend.modules.parsers.parser import BaseParser


class MarkdownParser(BaseParser):
    """
    Custom Markdown parser for extracting chunks from Markdown files.
    """

    name = "MarkdownParser"
    supported_file_extensions = [".md"]

    async def get_chunks(self, filepath) -> typing.List[Document]:
        """
        Extracts chunks of content from a given Markdown file.

        Parameters:
            filepath (str): The path to the Markdown file.

        Returns:
            typing.List[Document]: A list of Document objects representing the extracted chunks.

        Note:
            The MarkdownHeaderTextSplitter is used to split the content based on specific header patterns.
        """
        content = None
        with open(filepath, "r") as f:
            content = f.read()
        if not content:
            print("Error reading file: " + filepath)
            return []

        # Define the header patterns to split on (e.g., "# Header 1", "## Header 2", "### Header 3").
        headers_to_split_on = [
            ("#", "Header1"),
            ("##", "Header2"),
            ("###", "Header3"),
        ]

        # Initialize the MarkdownHeaderTextSplitter with the defined header patterns.
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )

        # Split the content into chunks based on the specified headers.
        md_header_splits = markdown_splitter.split_text(content)

        return md_header_splits
