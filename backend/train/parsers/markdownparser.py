import typing

from langchain.docstore.document import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter

from backend.common.logger import logger
from backend.train.parsers.parser import BaseParser


class MarkdownParser(BaseParser):
    name = "MarkdownParser"
    supported_file_extensions = [".md"]

    async def get_chunks(self, filepath) -> typing.List[Document]:
        content = None
        with open(filepath, "r") as f:
            content = f.read()
        if not content:
            print("Error reading file: " + filepath)
            return [], 0

        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]

        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
        md_header_splits = markdown_splitter.split_text(content)
        return md_header_splits
