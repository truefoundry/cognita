import os
import re
import typing
from typing import Optional

from langchain.docstore.document import Document
from langchain.text_splitter import Language, RecursiveCharacterTextSplitter

from backend.modules.parsers.parser import BaseParser
from backend.modules.parsers.utils import contains_text


class CodeParser(BaseParser):
    """
    CodeParser is a parser class for processing code files.
    """

    supported_file_extensions = [
        ".cpp",
        ".go",
        ".java",
        ".kt",
        ".js",
        ".ts",
        ".php",
        ".proto",
        ".py",
        ".rs",
        ".rb",
        ".scala",
        ".swift",
        ".latex",
        ".cs",
        ".c",
    ]
    supported_file_extensions_map = {
        ".cpp": Language.CPP,
        ".go": Language.GO,
        ".java": Language.JAVA,
        ".kt": Language.KOTLIN,
        ".js": Language.JS,
        ".ts": Language.TS,
        ".php": Language.PHP,
        ".proto": Language.PROTO,
        ".py": Language.PYTHON,
        ".rs": Language.RUST,
        ".rb": Language.RUBY,
        ".scala": Language.SCALA,
        ".swift": Language.SWIFT,
        ".latex": Language.LATEX,
        ".cs": Language.CSHARP,
        ".c": Language.C,
    }

    def __init__(self, max_chunk_size: int = 1000, *args, **kwargs):
        """
        Initializes the CodeParser object.
        """
        self.max_chunk_size = max_chunk_size

    async def get_chunks(
        self, filepath: str, metadata: Optional[dict], *args, **kwargs
    ) -> typing.List[Document]:
        """
        Asynchronously loads the text from a text file and returns it in chunks.
        """
        content = None
        _, file_extension = os.path.splitext(filepath)

        if file_extension not in self.supported_file_extensions_map:
            print("Unsupported file extension: " + file_extension)
            return []

        with open(filepath, "r") as f:
            content = f.read()
        if not content:
            print("Error reading file: " + filepath)
            return []

        # clean up text for any problematic characters
        content = re.sub("\n", " ", content).strip()
        content = content.encode("ascii", errors="ignore").decode("ascii")
        content = re.sub(r"([^\w\s])\1{4,}", " ", content)
        content = re.sub(" +", " ", content).strip()

        code_splitter = RecursiveCharacterTextSplitter.from_language(
            language=self.supported_file_extensions_map[file_extension],
            chunk_size=self.max_chunk_size,
        )

        code_splits = code_splitter.split_text(content)

        docs = [
            Document(
                page_content=code,
                metadata={
                    "type": "text",
                },
            )
            for code in code_splits
            if contains_text(code)
        ]

        return docs
