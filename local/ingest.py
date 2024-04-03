# Fill up local.metadata.json
# Load the env file for local setup
from backend.settings import Settings
import asyncio
import time

# Data ingestion
from backend.modules.metadata_store.client import METADATA_STORE_CLIENT
from backend.types import IngestDataToCollectionDto
from backend.server.routers.collection import ingest_data

settings = Settings()


async def ingest():

    collection = METADATA_STORE_CLIENT.get_collection_by_name(no_cache=True)

    data_source = METADATA_STORE_CLIENT.get_data_source_from_fqn()

    # Create a data ingestion request
    # It requires collection name & data source FQN
    request = IngestDataToCollectionDto(
        collection_name = collection.name,
        data_source_fqn = data_source.fqn,
    )

    await ingest_data(request=request)



if __name__ == "__main__":
    
    start = time.time()
    # Run only when u have to ingest data
    print("Ingesting Data....")
    asyncio.run(ingest())

    end = time.time()
    print(f"Time taken to ingest data: {end-start} seconds")