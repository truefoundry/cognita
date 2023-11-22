import zipfile

import tiktoken
from langchain.docstore.document import Document


def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """
    Returns the number of tokens in a text string using the specified encoding.

    Args:
        string (str): The input text string.
        encoding_name (str, optional): The name of the encoding to use. Defaults to "cl100k_base".

    Returns:
        int: The number of tokens in the input text string.
    """
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_openai_cost_for_str(str):
    """
    Calculates the OpenAI cost for a given text string.

    Args:
        str (str): The input text string.

    Returns:
        float: The cost in USD for using OpenAI GPT-3.5 API for the given text string.
    """
    tokens = num_tokens_from_string(str)
    return tokens * 0.001 * 0.03


def get_openai_cost_for_tokens(num_tokens):
    """
    Calculates the OpenAI cost for a given number of tokens.

    Args:
        num_tokens (int): The number of tokens.

    Returns:
        float: The cost in USD for using OpenAI GPT-3.5 API for the given number of tokens.
    """
    return num_tokens * 0.001 * 0.03


def merge_strings(filepath, arr, chunk_size):
    """
    Merge elements of a string array into chunks of size less than or equal to chunk_size.

    Args:
        filepath (str): The file path or identifier associated with the merged strings.
        arr (List[str]): The input array of strings to be merged.
        chunk_size (int): The maximum size of each merged chunk.

    Returns:
        List[Document]: The merged strings transformed into Document langchain structures,
                        each with associated metadata containing the filepath.
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

    # Transform each merged string into a Document with associated metadata.
    merged_array = [
        Document(page_content=str_elm, metadata={"filepath": filepath})
        for str_elm in merged_array
    ]

    return merged_array


def unzip_file(file_path, dest_dir):
    """
    Unzip the data given the input and output path.

    Args:
        file_path (str): The path of the ZIP file to be extracted.
        dest_dir (str): The destination directory where the contents will be extracted.

    Returns:
        None
    """
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(dest_dir)
