import os
import typing

from langchain.docstore.document import Document
from langchain.document_loaders import TextLoader
from langchain.text_splitter import SpacyTextSplitter, NLTKTextSplitter

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

    def __init__(self, chunk_size, *args, **kwargs):
        """
        Initializes the TextParser object.

        Parameters:
            chunk_size (int): Maximum size for each chunk.
        """
        # Initialize the NLTKTextSplitter for splitting the text into chunks
        self.text_splitter = NLTKTextSplitter(chunk_size=chunk_size)

    async def get_chunks(self, filepath) -> typing.List[Document]:
        """
        Asynchronously loads the text from a text file and returns it in chunks.

        Parameters:
            filepath (str): Path of the text file to be processed.

        Returns:
            List[Document]: A list of Document objects, each representing a chunk of the text.
        """
        # Load the text from the text file using the TextLoader
        loader = TextLoader(filepath)
        loader_data = loader.load()

        # Set the file path as metadata for the Document
        loader_data[0].metadata = {"filepath": os.path.basename(filepath)}

        # Split the document into chunks using the NLTKTextSplitter
        loader_data = self.text_splitter.split_documents(loader_data)

        return loader_data
