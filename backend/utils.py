import zipfile


def flatten(dct, sub_dct_key_name, prefix=None):
    prefix = prefix or f"{sub_dct_key_name}."
    sub_dct = dct.pop(sub_dct_key_name) or {}
    for k, v in sub_dct.items():
        dct[f"{prefix}{k}"] = v
    return dct


def unflatten(dct, sub_dct_key_name, prefix=None):
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
