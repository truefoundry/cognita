import os
import json
from typing import List, Dict, Tuple, Optional, Union
from langchain.docstore.document import Document


def contains_text(text):
    # Check if the token contains at least one alphanumeric character
    return any(char.isalnum() for char in text)


async def additional_processing(
    input_data: Union[str, List[Dict]],
    extend_metadata: bool = False,
    additional_metadata: Optional[Dict] = None,
    replace_table_text: bool = True,
    table_text_key: str = "text_as_html",
    return_langchain_docs: bool = True,
    convert_metadata_keys_to_string: bool = True,
) -> Tuple[List[str], List[Dict], List[Document]]:
    """
    Performs additional processing on the extracted documents.
    Can handle both file paths and raw lists of JSON objects.
    """
    texts = []
    metadata_list = []
    langchain_docs = []

    if isinstance(input_data, str):  # It's a file path
        if os.path.isfile(input_data):
            file_paths = [input_data]
        else:
            file_paths = [
                os.path.join(input_data, f)
                for f in os.listdir(input_data)
                if f.endswith(".json")
            ]

        for file_path in file_paths:
            with open(file_path, "r") as file:
                data = json.load(file)
            process_data(
                data,
                texts,
                metadata_list,
                extend_metadata,
                additional_metadata,
                replace_table_text,
                table_text_key,
                convert_metadata_keys_to_string,
            )

            # Write the processed data back to the file
            with open(file_path, "w") as file:
                json.dump(data, file, indent=2)

    elif isinstance(input_data, list):  # It's a raw list of JSON objects
        process_data(
            input_data,
            texts,
            metadata_list,
            extend_metadata,
            additional_metadata,
            replace_table_text,
            table_text_key,
            convert_metadata_keys_to_string,
        )

    if return_langchain_docs:
        langchain_docs = get_langchain_docs(texts, metadata_list)

    return texts, metadata_list, langchain_docs


def process_data(
    data,
    texts,
    metadata_list,
    extend_metadata,
    additional_metadata,
    replace_table_text,
    table_text_key,
    convert_metadata_keys_to_string,
):
    for element in data:
        if extend_metadata and additional_metadata:
            element["metadata"].update(additional_metadata)

        if replace_table_text and element["type"] == "Table":
            element["text"] = element["metadata"][table_text_key]

        metadata = element["metadata"].copy()
        if convert_metadata_keys_to_string:
            metadata = {
                str(key): convert_to_string(value) for key, value in metadata.items()
            }
        for key in element:
            if key not in ["text", "metadata", "embeddings"]:
                metadata[key] = element[key]
        metadata["page_num"] = metadata.get("page_number", 1)  # Changed to page_num

        metadata_list.append(metadata)
        texts.append(element["text"])


def get_langchain_docs(texts: List[str], metadata_list: List[Dict]) -> List[Document]:
    """
    Creates LangChain documents from the extracted texts and metadata.
    """
    return [
        Document(page_content=content, metadata=metadata)
        for content, metadata in zip(texts, metadata_list)
    ]


def convert_to_string(value: any) -> str:
    """
    Converts a value to a string representation.
    """
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value)
