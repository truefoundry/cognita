from typing import Dict

from pydantic import Field

from backend.types import (
    ConfiguredBaseModel,
    DataIngestionMode,
    DataSource,
    EmbedderConfig,
    ParserConfig,
)


class DataIngestionConfig(ConfiguredBaseModel):
    """
    Configuration to store Data Ingestion Configuration
    """

    collection_name: str = Field(
        title="a unique name to your collection",
    )
    data_ingestion_run_name: str = Field(
        title="a unique name to your ingestion run",
    )
    data_source: DataSource = Field(
        title="Data source to ingest data from. Can be local, github or truefoundry data-dir/artifact",
    )
    embedder_config: EmbedderConfig = Field(
        title="Embedder configuration",
    )
    parser_config: Dict[str, ParserConfig] = Field(
        title="Parser configuration to parse the documents.",
    )
    data_ingestion_mode: DataIngestionMode = Field(title="Data ingestion mode")
    raise_error_on_failure: bool = Field(default=True, title="Raise error on failure")
    batch_size: int = Field(default=100, title="Batch size for indexing", ge=1)
