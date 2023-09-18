import os
import time

import mlfoundry

from backend.common.logger import logger
from backend.train.dataloaders.loader import get_loader, get_loaders_map
from backend.train.parsers.parser import get_parser, get_parsers_map


def get_parsers_configurations(input_parsers_config):
    """
    Return parsers mapping given the input parser configuration.
    """
    parsers_map = get_parsers_map()
    for file_type in parsers_map.keys():
        if (
            file_type in input_parsers_config
            and input_parsers_config[file_type] in parsers_map[file_type]
        ):
            parsers_map[file_type] = [input_parsers_config[file_type]]
        if len(parsers_map[file_type]) > 1:
            parsers_map[file_type] = [parsers_map[file_type][0]]
        parsers_map[file_type] = parsers_map[file_type][0]
    return parsers_map


def get_loader_for_source_uri(source_uri):
    """
    Returns the loader class for given source_uri
    """
    loaders_map = get_loaders_map()
    for protocol in loaders_map.keys():
        if source_uri.startswith(protocol):
            return get_loader(loaders_map[protocol])
    supported_protocols = ", ".join(loaders_map.keys())
    raise Exception(
        f"Unsupported source_uri. Supported protocols are {supported_protocols}"
    )


def count_docs_to_index_in_dir(target_dir: str) -> int:
    count = 0
    parsers_map = get_parsers_map()
    for dirpath, dirnames, filenames in os.walk(target_dir):
        for file in filenames:
            for ext in parsers_map.keys():
                if file.endswith(ext):
                    count += 1
    return count


def get_mlfoundry_run(repo_name, run_name):
    """
    Returns the mlfoundry run given repo_name and run_name.
    """
    client = mlfoundry.get_client()
    client.create_ml_repo(repo_name)
    run = client.create_run(ml_repo=repo_name, run_name=run_name)
    return run, ""


async def get_all_chunks_from_dir(
    dest_dir,
    max_chunk_size,
    dry_run,
    ml_repo,
    mlfoundry_run,
    tenant_name,
    parsers_map,
):
    """
    This function loops over all the files in the dest dir and uses
    parsers to get the chunks from all the files. It returns the chunks
    as an array where each element is the chunk along with some metadata
    """
    docs_to_embed = []
    index = 0
    last_log_time = 0
    last_index = 0
    last_docs_size = 0
    for dirpath, dirnames, filenames in os.walk(dest_dir):
        for file in filenames:
            if file.startswith("."):
                continue
            # Get the file extension using os.path
            file_ext = os.path.splitext(file)[1]
            if file_ext not in parsers_map.keys():
                continue
            parser_name = get_parser_for_file(file, parsers_map)
            if parser_name is None:
                logger.info(f"Skipping file {file} as it is not supported")
                continue
            start_time = time.time()
            parser = get_parser(
                parser_name, max_chunk_size, dry_run, ml_repo, tenant_name
            )
            filepath = os.path.join(dirpath, file)
            chunks = await parser.get_chunks(filepath)
            # Loop over all the chunks and add them to the docs_to_embed
            # array
            for chunk in chunks:
                docs_to_embed.append(chunk)

            logger.info("%s -> %s chunks", filepath, len(chunks))
            end_time = time.time()
            if dry_run != True:
                # log the update once every 5 seconds
                curr_time = time.time()
                if curr_time - last_log_time > 5:
                    mlfoundry_run.log_metrics(
                        metric_dict={
                            "processing_time": end_time - start_time,
                            "num_chunks": len(chunks),
                        },
                        step=index,
                    )
                    last_log_time = curr_time
                    last_index = index
                    last_docs_size = len(docs_to_embed)
            index += 1
    if last_index < index - 1:
        mlfoundry_run.log_metrics(
            metric_dict={
                "processing_time": time.time() - last_log_time,
                "num_chunks": len(docs_to_embed) - last_docs_size,
            },
            step=index - 1,
        )
    return docs_to_embed


def get_parser_for_file(filepath, parsers_map):
    """
    Given the input file and parsers mapping, return the appropriate mapper.
    """
    if not "." in filepath:
        return None
    file_extension = filepath.split(".")[-1]
    file_extension = "." + file_extension
    if file_extension not in parsers_map:
        return None
    return parsers_map[file_extension]
