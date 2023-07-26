import os
import typing

from langchain.docstore.document import Document
from langchain.document_loaders import TextLoader
from langchain.text_splitter import SpacyTextSplitter, NLTKTextSplitter

from .parser import BaseParser


class TextParser(BaseParser):
    name = "TextParser"
    supported_file_extensions = [".txt"]

    def __init__(self, chunk_size, *args, **kwargs):
        self.text_splitter = NLTKTextSplitter(chunk_size=chunk_size)

    async def get_chunks(self, filepath) -> typing.List[Document]:
        loader = TextLoader(filepath)
        loader_data = loader.load()
        loader_data[0].metadata = {"filepath": os.path.basename(filepath)}
        loader_data = self.text_splitter.split_documents(loader_data)
        return loader_data
