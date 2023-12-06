import os
import typing

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .parser import BaseParser


class TextParser(BaseParser):
    """
    TextParser is a parser class for processing plain text files.

    Attributes:
        name (str): The name of the parser.
        supported_file_extensions (List[str]): List of supported file extensions (e.g., ['.txt']).
    """

    name = "TextParser"
    supported_file_extensions = [".txt"]

    def __init__(self, *args, **kwargs):
        """
        Initializes the TextParser object.
        """
        pass

    async def get_chunks(
        self, filepath: str, max_chunk_size=1000
    ) -> typing.List[Document]:
        """
        Asynchronously loads the text from a text file and returns it in chunks.

        Parameters:
            filepath (str): Path of the text file to be processed.

        Returns:
            List[Document]: A list of Document objects, each representing a chunk of the text.
        """
        content = None
        with open(filepath, "r") as f:
            content = f.read()
        if not content:
            print("Error reading file: " + filepath)
            return []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=max_chunk_size)
        texts = text_splitter.split_text(content)

        docs = [
            Document(page_content=text, metadata={"type": "text"}) for text in texts
        ]

        return docs
