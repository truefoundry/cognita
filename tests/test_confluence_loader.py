import os
from multiprocessing import freeze_support
from backend.modules.dataloaders import ConfluenceLoader
from backend.types import DataSource, DataIngestionMode
from backend.settings import settings

def main():
    # Create a DataSource object
    data_source = DataSource(
        type="confluence",
        uri=settings.CONFLUENCE_URL,
        fqn="confluence_test_source"
    )

    # Initialize the ConfluenceLoader
    loader = ConfluenceLoader()

    # Set up test parameters
    dest_dir = "test/confluence_output"
    batch_size = 10
    data_ingestion_mode = DataIngestionMode.FULL

    # Create the destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)

    # Load data using the ConfluenceLoader
    loaded_data_batches = loader.load_filtered_data(
        data_source=data_source,
        dest_dir=dest_dir,
        previous_snapshot={},  # Empty for full ingestion mode
        batch_size=batch_size,
        data_ingestion_mode=data_ingestion_mode,
    )

    # Process and print the loaded data points
    total_data_points = 0
    for batch in loaded_data_batches:
        total_data_points += len(batch)
        print(f"Batch of {len(batch)} data points loaded:")
        for data_point in batch:
            print(f"- {data_point.data_point_uri}")

    print(f"\nTotal data points loaded: {total_data_points}")

if __name__ == '__main__':
    freeze_support()
    main()