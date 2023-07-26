import argparse
import asyncio
import json
import os
import pickle
import re
import shutil
import time

import mlfoundry
from dotenv import load_dotenv

from backend.common.logger import logger
from backend.train import utils
from backend.common.db.qdrant import put_embeddings_in_vectordb
from backend.train.utils import get_parsers_configurations
from backend.common.embedder import get_embedder
import nltk

# load environment variables
load_dotenv()
nltk.download("punkt")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_name", type=str, required=True, default=None)
    parser.add_argument("--source_uri", type=str, required=True)
    parser.add_argument("--ml_repo", type=str, required=True)
    # """
    # Enter the source of the documents. The source can be one of the following:
    # 1. Local Files: local://<path_to_directory>
    # 2. Github Repo: github://<github_repo_url>
    # 3. Mlfoundry artifact: mlfoundry://mlfoundry_artifact_fqn
    # """
    parser.add_argument("--repo_creds", type=str, required=False)
    parser.add_argument("--dry_run", required=False, default=True)
    parser.add_argument("--chunk_size", type=int, required=True, default=512)
    parser.add_argument("--embedder", type=str, required=True, default="OpenAI")
    parser.add_argument("--embedder-config", type=str, required=True)
    parser.add_argument(
        "--parsers_map",
        type=str,
        default="""{".pdf": "PdfParser"}""",
        required=False,
    )
    args = parser.parse_args()

    # args.repo_name should only have alphanumeric characters and - and _.
    # The code below validates that and throws an exception if the repo
    # name is invalid
    if not re.match("^[a-zA-Z0-9_-]*$", args.repo_name):
        raise Exception(
            "Invalid repo name. Only alphanumeric characters, - and _ are allowed"
        )

    # Check if embedder-config is a valid json
    try:
        json.loads(args.embedder_config)
    except json.decoder.JSONDecodeError as e:
        raise Exception("Invalid embedder-config. It should be a valid json")

    return args


async def main():
    # parse training arguments
    args = parse_args()

    # fetch available parsers mapping
    input_parsers_config = json.loads(args.parsers_map)
    parsers_map = get_parsers_configurations(input_parsers_config)
    logger.info("Parsers Configuration: %s", str(parsers_map))

    # output directory for temporary file handling
    dest_dir = os.path.join(os.getcwd(), "repo-data", args.repo_name)
    if os.path.exists(dest_dir):
        # delete dest dir if it already exists
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)

    logger.info("Indexing process started..")
    # Get the data in the dest dir
    load_start_time = time.time()
    utils.get_loader_for_source_uri(args.source_uri).load_data(
        args.source_uri, dest_dir, args.repo_creds
    )
    logger.info("Loading data took %s seconds", time.time() - load_start_time)
    embedder_config = json.loads(args.embedder_config)

    # Initialize mlfoundry client
    mlfoundry_run = None
    mlfoundry_tenant = None
    if args.dry_run != "True":
        logger.info("Initializing MLfoundry client")
        mlfoundry_run, mlfoundry_tenant = utils.get_mlfoundry_run(
            args.ml_repo, run_name=args.repo_name
        )
        mlfoundry_run.log_params(
            {
                "chunk_size": args.chunk_size,
                "source_uri": args.source_uri,
                "dry_run": args.dry_run,
                "repo_name": args.repo_name,
                "embedder": args.embedder,
            }
        )
        mlfoundry_run.log_params(embedder_config)

    # Count number of documents/files
    docs_to_index_count = utils.count_docs_to_index_in_dir(dest_dir)
    logger.info("Total docs to index: %s", docs_to_index_count)
    if args.dry_run != "True":
        mlfoundry_run.log_metrics(metric_dict={"num_files": docs_to_index_count})

    # Index all the documents in the dest dir
    chunks = await utils.get_all_chunks_from_dir(
        dest_dir,
        args.chunk_size,
        args.dry_run,
        args.ml_repo,
        mlfoundry_run,
        mlfoundry_tenant,
        parsers_map,
    )
    logger.info("Total number of chunks: %s", len(chunks))

    # get the embedders
    embeddings = get_embedder(args.embedder, embedder_config)

    # initialize qdrant vectordb
    if args.dry_run != "True":
        qdrant_collection_name = mlfoundry_run.run_name
        logger.info("Qdrant Indexing Collection Name: %s", qdrant_collection_name)
        start_time = time.time()
        put_embeddings_in_vectordb(
            qdrant_collection_name, chunks, embeddings, embedder_config
        )
        logger.info(
            "Put embeddings in vectordb took %s seconds", time.time() - start_time
        )
        mlfoundry_run.end()

    logger.info("Indexing successfully completed.")


if __name__ == "__main__":
    asyncio.run(main())
