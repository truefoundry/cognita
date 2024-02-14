import zipfile

import tiktoken
from langchain.docstore.document import Document

from backend.types import DataSource

DOCUMENT_ID_SEPARATOR = "::"


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


def get_base_document_id(source: DataSource):
    """
    Generates unique document id for a given source. We use the following format:
    <type>::<source_uri>
    This will be used to identify the source in the database.
    """
    return f"{DOCUMENT_ID_SEPARATOR}".join([source.type, source.config.uri])


def generate_document_id(source_type: str, source_uri: str, path: str):
    """
    Generates unique document id for a given document. We use the following format:
    <type>::<source_uri>::<path>
    This will be used to identify the document in the database.
    """
    return f"{DOCUMENT_ID_SEPARATOR}".join([source_type, source_uri, path])


def retrieve_source_from_document_id(document_id: str):
    """
    Retrives params from document id for a given document. We use the following format:
    <type>::<source_uri>::<path>
    This will be used to identify the document in the database.
    reverse for `generate_document_id`
    """
    return document_id.split(DOCUMENT_ID_SEPARATOR)
