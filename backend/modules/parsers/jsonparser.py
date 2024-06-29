import json
import os
from typing import List, Dict, Optional, Tuple
from langchain.docstore.document import Document
from backend.modules.parsers.parser import BaseParser

class JSONParser(BaseParser):
    """
    JSONParser is a parser class for processing JSON files.
    """

    supported_file_extensions = [".json"]

    def __init__(self, max_chunk_size: int = 1000, *args, **kwargs):
        """
        Initializes the JSONParser object.
        """
        self.max_chunk_size = max_chunk_size

    async def get_chunks(
        self, 
        filepath: str, 
        metadata: Optional[dict] = None,
        *args, 
        **kwargs
    ) -> List[Document]:
        """
        Asynchronously loads the JSON from a file and returns LangChain documents.
        """
        try:
            # Call additional_processing with the filepath as the directory
            _, _, langchain_docs = await self.additional_processing(
                directory=filepath,
                extend_metadata=kwargs.get('extend_metadata', False),
                additional_metadata=kwargs.get('additional_metadata'),
                replace_table_text=kwargs.get('replace_table_text', False),
                table_text_key=kwargs.get('table_text_key', ''),
                return_langchain_docs=True,
                convert_metadata_keys_to_string=kwargs.get('convert_metadata_keys_to_string', True)
            )
            return langchain_docs
        except Exception as e:
            print(f"Error processing JSON file at {filepath}: {str(e)}")
            return []

    @staticmethod
    async def additional_processing(
        directory: str,
        extend_metadata: bool = False,
        additional_metadata: Optional[Dict] = None,
        replace_table_text: bool = False,
        table_text_key: str = "",
        return_langchain_docs: bool = True,
        convert_metadata_keys_to_string: bool = True,
    ) -> Tuple[List[str], List[Dict], List[Document]]:
        """
        Performs additional processing on the extracted documents.
        """
        if os.path.isfile(directory):
            file_paths = [directory]
        else:
            file_paths = [
                os.path.join(directory, f)
                for f in os.listdir(directory)
                if f.endswith(".json")
            ]

        texts = []
        metadata_list = []
        langchain_docs = []

        for file_path in file_paths:
            with open(file_path, "r") as file:
                data = json.load(file)

            for element in data:
                if extend_metadata and additional_metadata:
                    element["metadata"].update(additional_metadata)

                if replace_table_text and element["type"] == "Table":
                    element["text"] = element["metadata"][table_text_key]

                metadata = element["metadata"].copy()
                if convert_metadata_keys_to_string:
                    metadata = {
                        str(key): JSONParser.convert_to_string(value)
                        for key, value in metadata.items()
                    }
                for key in element:
                    if key not in ["text", "metadata", "embeddings"]:
                        metadata[key] = element[key]
                metadata["page_num"] = metadata.get("page_number", 1)  # Changed to page_num

                metadata_list.append(metadata)
                texts.append(element["text"])

            if return_langchain_docs:
                langchain_docs.extend(JSONParser.get_langchain_docs(texts, metadata_list))

            with open(file_path, "w") as file:
                json.dump(data, file, indent=2)

        return texts, metadata_list, langchain_docs

    @staticmethod
    def get_langchain_docs(texts: List[str], metadata_list: List[Dict]) -> List[Document]:
        """
        Creates LangChain documents from the extracted texts and metadata.
        """
        return [
            Document(page_content=content, metadata=metadata)
            for content, metadata in zip(texts, metadata_list)
        ]

    @staticmethod
    def convert_to_string(value: any) -> str:
        """
        Converts a value to a string representation.
        """
        if isinstance(value, (list, dict)):
            return json.dumps(value)
        return str(value)