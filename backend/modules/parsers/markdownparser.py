import typing

from langchain.docstore.document import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
        chunks_arr = self.recurse_split(
            content, 0, headers_to_split_on, self.max_chunk_size
        )
        return chunks_arr
    
    def recurse_split(self, content, i, headers_to_split_on, max_chunk_size):
        if (i >= len(headers_to_split_on)):
            # Use recursive text splitter in this case
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size = max_chunk_size,
                chunk_overlap = 0,
                length_function = len,
            )
            texts = text_splitter.create_documents([content])
            print("Total texts: " + str(len(texts)))
            return texts
        
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on[i:i+1])
        md_header_splits = markdown_splitter.split_text(content)
        chunks_arr = []
        for document in md_header_splits:
            chunk_length = len(document.page_content)
            if (chunk_length <= max_chunk_size):
                chunks_arr.append(document)
                continue
            chunks_arr.extend(self.recurse_split(document.page_content, i+1, headers_to_split_on, max_chunk_size))
        return chunks_arr
