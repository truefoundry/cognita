import asyncio

from dotenv import load_dotenv

from backend.indexer.argument_parser import parse_args
from backend.indexer.indexer import index_collection

# load environment variables
load_dotenv()

async def main():
    # parse training arguments
    index_config = parse_args()
    await index_collection(index_config)


if __name__ == "__main__":
    asyncio.run(main())
