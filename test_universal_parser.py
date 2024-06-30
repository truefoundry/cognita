import asyncio
import os
import random
from typing import List
from backend.modules.parsers import UniversalParser

def get_files(directory: str) -> List[str]:
    """
    Recursively get all supported files in the given directory and its subdirectories.
    """
    supported_extensions = UniversalParser.supported_file_extensions
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                files.append(os.path.join(root, filename))
    return files

async def test_universal_parser(filepaths: List[str], num_samples: int = 5):
    """
    Test the UniversalParser on a sample of files.
    """
    parser = UniversalParser()
    
    # Randomly sample files if we have more than num_samples
    if len(filepaths) > num_samples:
        filepaths = random.sample(filepaths, num_samples)
    
    for filepath in filepaths:
        print(f"Testing file: {filepath}")
        chunks = await parser.get_chunks(filepath=filepath)
        print(f"Number of chunks: {len(chunks)}")
        if chunks:
            print("First chunk:")
            print(f"Content: {chunks[0].page_content[:100]}...")  # Print first 100 characters
            print(f"Metadata: {chunks[0].metadata}")
        print("-" * 50)

async def main():
    directory = "/Users/kwasia/Downloads"
    files = get_files(directory)
    
    if not files:
        print(f"No supported files found in {directory}")
        return

    print(f"Found {len(files)} supported files")
    print("Sample of file paths:")
    for filepath in random.sample(files, min(5, len(files))):
        print(filepath)
    print("-" * 50)

    await test_universal_parser(files)

if __name__ == "__main__":
    asyncio.run(main())