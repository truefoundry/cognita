import typing
from typing import Optional

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from backend.modules.parsers.parser import BaseParser
from backend.types import LoadedDataPoint


class TextParser(BaseParser):
    """
    TextParser is a parser class for processing plain text files.
    """

    supported_file_extensions = [".txt"]

    def __init__(self, max_chunk_size: int = 1000, *args, **kwargs):
        """
        Initializes the TextParser object.
        """
        self.max_chunk_size = max_chunk_size

    async def get_chunks(
        self, 
        filepath: str,
        metadata: Optional[dict],
        *args, 
        **kwargs
    ) -> typing.List[Document]:
        """
        Asynchronously loads the text from a text file and returns it in chunks.
        """
        content = None
        with open(filepath, "r") as f:
            content = f.read()
        if not content:
            print("Error reading file: " + filepath)
            return []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.max_chunk_size)
        texts = text_splitter.split_text(content)

        docs = [
            Document(
                page_content=text,
                metadata={
                    "type": "text",
                },
            )
            for text in texts
        ]

        return docs
