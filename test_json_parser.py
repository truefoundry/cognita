import asyncio
import os
import random
from typing import List
from backend.modules.parsers import JSONParser


def get_json_files(directory: str) -> List[str]:
    """
    Recursively get all JSON files in the given directory and its subdirectories.
    """
    json_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))
    return json_files


async def test_json_parser(filepaths: List[str], num_samples: int = 5):
    """
    Test the JSONParser on a sample of JSON files.
    """
    parser = JSONParser()

    # Randomly sample files if we have more than num_samples
    if len(filepaths) > num_samples:
        filepaths = random.sample(filepaths, num_samples)

    for filepath in filepaths:
        print(f"Testing file: {filepath}")
        chunks = await parser.get_chunks(filepath=filepath)
        print(f"Number of chunks: {len(chunks)}")
        if chunks:
            print("First chunk:")
            print(
                f"Content: {chunks[0].page_content[:100]}..."
            )  # Print first 100 characters
            print(f"Metadata: {chunks[0].metadata}")
        print("-" * 50)


async def main():
    directory = "test/confluence_output"
    json_files = get_json_files(directory)

    if not json_files:
        print(f"No JSON files found in {directory} or its subdirectories")
        return

    print(f"Found {len(json_files)} JSON files")
    print("Sample of file paths:")
    for filepath in random.sample(json_files, min(5, len(json_files))):
        print(filepath)
    print("-" * 50)

    await test_json_parser(json_files)


if __name__ == "__main__":
    asyncio.run(main())
