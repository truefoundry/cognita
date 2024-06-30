import os
from typing import List, Optional
from langchain.docstore.document import Document
from backend.modules.parsers.parser import BaseParser
from unstructured.partition.auto import partition
from unstructured.chunking.basic import chunk_elements
from backend.modules.parsers.utils import additional_processing
from unstructured.staging.base import convert_to_dict


class UniversalParser(BaseParser):
    """
    UniversalParser is a parser class for processing various file types using unstructured.
    """

    supported_file_extensions = [
        ".txt",
        ".docx",
        ".pptx",
        ".eml",
        ".html",
        ".xlsx",
        ".js",
        ".py",
        ".java",
        ".cpp",
        ".cc",
        ".cxx",
        ".c",
        ".cs",
        ".php",
        ".rb",
        ".swift",
        ".ts",
        ".go",
        ".xml",
        ".yaml",
    ]

    def __init__(self, max_chunk_size: int = 1000, *args, **kwargs):
        """
        Initializes the UniversalParser object.
        """
        self.max_chunk_size = max_chunk_size

    async def get_chunks(
        self, filepath: str, metadata: Optional[dict] = None, *args, **kwargs
    ) -> List[Document]:
        """
        Asynchronously processes a file and returns LangChain documents.
        """
        try:
            # Step 1: Use partition_auto to get elements
            elements = partition(filename=filepath)

            # Step 2: Use chunker to get chunks and then convert to dict for addn processing
            chunks = chunk_elements(
                elements,
                max_characters=self.max_chunk_size,
                new_after_n_chars=kwargs.get("new_after_n_chars", self.max_chunk_size),
                overlap=kwargs.get("overlap", 0),
            )
            chunks = convert_to_dict(chunks)

            # Step 3: Process the chunks using additional_processing
            _, _, langchain_docs = await additional_processing(
                chunks,
                extend_metadata=kwargs.get("extend_metadata", False),
                additional_metadata=kwargs.get("additional_metadata"),
                replace_table_text=kwargs.get("replace_table_text", False),
                table_text_key=kwargs.get("table_text_key", ""),
                return_langchain_docs=True,
                convert_metadata_keys_to_string=kwargs.get(
                    "convert_metadata_keys_to_string", True
                ),
            )

            return langchain_docs
        except Exception as e:
            print(f"Error processing file at {filepath}: {str(e)}")
            return []
