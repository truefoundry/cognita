import zipfile

import tiktoken
from langchain.docstore.document import Document


def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_openai_cost_for_str(str):
    tokens = num_tokens_from_string(str)
    return tokens * 0.001 * 0.03


def get_openai_cost_for_tokens(num_tokens):
    return num_tokens * 0.001 * 0.03


def merge_strings(filepath, arr, chunk_size):
    """
    Merge elements of a string array into chunks of size less than or equal to chunk_size.
    """
    merged_array = []
    current_chunk = ""

    for string in arr:
        if len(current_chunk) + len(string) <= chunk_size:
            current_chunk += string
        else:
            merged_array.append(current_chunk)
            current_chunk = string

    if current_chunk:
        merged_array.append(current_chunk)

    # transform to Document langchain structure
    merged_array = [
        Document(page_content=str_elm, metadata={"filepath": filepath})
        for str_elm in merged_array
    ]

    return merged_array


def unzip_file(file_path, dest_dir):
    """
    Unzip the data given the input and output path
    """
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(dest_dir)
