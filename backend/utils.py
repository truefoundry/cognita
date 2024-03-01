import zipfile

from backend.types import DataSource

DOCUMENT_ID_SEPARATOR = "::"


def _flatten(dct, sub_dct_key_name, prefix=None):
    prefix = prefix or f"{sub_dct_key_name}."
    sub_dct = dct.pop(sub_dct_key_name) or {}
    for k, v in sub_dct.items():
        dct[f"{prefix}{k}"] = v
    return dct


def _unflatten(dct, sub_dct_key_name, prefix=None):
    prefix = prefix or f"{sub_dct_key_name}."
    new_dct = {sub_dct_key_name: {}}
    for k, v in dct.items():
        if k.startswith(prefix):
            new_k = k[len(prefix) :]
            new_dct[sub_dct_key_name][new_k] = v
        else:
            new_dct[k] = v
    return new_dct


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


def get_base_document_id(data_source: DataSource) -> str | None:
    """
    Generates unique document id for a given data source. We use the following format:
    <type>::<source_uri>
    This will be used to identify the source in the database.
    """
    return f"{DOCUMENT_ID_SEPARATOR}".join([data_source.type, data_source.uri])


def generate_document_id(data_source: DataSource, path: str):
    """
    Generates unique document id for a given document. We use the following format:
    <type>::<source_uri>::<path>
    This will be used to identify the document in the database.
    """
    return f"{DOCUMENT_ID_SEPARATOR}".join([data_source.type, data_source.uri, path])


def retrieve_source_from_document_id(_document_id: str):
    """
    Retrives params from document id for a given document. We use the following format:
    <type>::<source_uri>::<path>
    This will be used to identify the document in the database.
    reverse for `generate_document_id`
    """
    return _document_id.split(DOCUMENT_ID_SEPARATOR)
