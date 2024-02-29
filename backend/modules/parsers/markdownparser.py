import typing

from langchain.docstore.document import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter, MarkdownTextSplitter

from backend.modules.parsers.parser import BaseParser
from backend.types import LoadedDocument


class MarkdownParser(BaseParser):
    """
    Custom Markdown parser for extracting chunks from Markdown files.
    """

    name = "MarkdownParser"
    supported_file_extensions = [".md"]

    def __init__(self, *args, **kwargs):
        """
        Initializes the MarkdownParser object.
        """
        pass

    async def get_chunks(
        self,
        document: LoadedDocument,
        max_chunk_size: int,
        *args,
        **kwargs,
    ) -> typing.List[Document]:
        """
        Extracts chunks of content from a given Markdown file.

        Parameters:
            filepath (str): The path to the Markdown file.

        Returns:
            typing.List[Document]: A list of Document objects representing the extracted chunks.

        Note:
            The UnstructuredMarkdownLoader is used to load the markdown file.
        """
        filepath = document.filepath
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
            ("####", "Header4"),
        ]
        chunks_arr = self._recurse_split(
            content, {}, 0, headers_to_split_on, max_chunk_size
        )
        final_chunks = []
        lastAddedChunkSize = max_chunk_size + 1
        for chunk in chunks_arr:
            page_content = self._include_headers_in_content(
                content=chunk.page_content,
                metadata=chunk.metadata,
            )
            chunk_length = len(page_content)
            if chunk_length + lastAddedChunkSize <= max_chunk_size:
                lastAddedChunk: Document = final_chunks.pop()
                lastAddedChunk.page_content = (
                    f"{lastAddedChunk.page_content}\n{page_content}"
                )
                lastAddedChunk.metadata.update(document.metadata)
                final_chunks.append(lastAddedChunk)
                lastAddedChunkSize = chunk_length + lastAddedChunkSize
                continue
            lastAddedChunkSize = chunk_length
            chunk.metadata.update(document.metadata)
            final_chunks.append(
                Document(
                    page_content=page_content,
                    metadata=chunk.metadata,
                )
            )
        return final_chunks

    def _include_headers_in_content(self, content: str, metadata: dict):
        if "Header4" in metadata:
            content = "#### " + metadata["Header4"] + "\n" + content
        if "Header3" in metadata:
            content = "### " + metadata["Header3"] + "\n" + content
        if "Header2" in metadata:
            content = "## " + metadata["Header2"] + "\n" + content
        if "Header1" in metadata:
            content = "# " + metadata["Header1"] + "\n" + content
        return content

    def _recurse_split(self, content, metadata, i, headers_to_split_on, max_chunk_size):
        if i >= len(headers_to_split_on):
            # Use Markdown Text Splitter in this case
            text_splitter = MarkdownTextSplitter(
                chunk_size=max_chunk_size,
                chunk_overlap=0,
                length_function=len,
            )
            texts = text_splitter.split_text(content)
            chunks_arr = [
                Document(
                    page_content=text,
                    metadata=metadata,
                )
                for text in texts
            ]
            return chunks_arr

        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on[i : i + 1]
        )
        md_header_splits = markdown_splitter.split_text(content)
        chunks_arr = []
        for document in md_header_splits:
            document.metadata.update(metadata)
            chunk_length = len(document.page_content)
            if chunk_length <= max_chunk_size:
                chunks_arr.append(
                    Document(
                        page_content=document.page_content,
                        metadata=document.metadata,
                    )
                )
                continue
            chunks_arr.extend(
                self._recurse_split(
                    document.page_content,
                    document.metadata,
                    i + 1,
                    headers_to_split_on,
                    max_chunk_size,
                )
            )
        return chunks_arr
