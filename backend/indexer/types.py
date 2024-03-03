from typing import Optional

from pydantic import BaseModel, Field

from backend.types import (
    DataIngestionMode,
    DataSource,
    EmbedderConfig,
    MetadataStoreConfig,
    ParserConfig,
    VectorDBConfig,
)


class DataIngestionConfig(BaseModel):
    collection_name: str = Field(
        title="a unique name to your collection",
    )
    data_ingestion_run_name: str = Field(
        title="a unique name to your ingestion run",
    )
    data_source: DataSource = Field(
        title="Data source to ingest data from. Can be local, github or mlfoundry artifact",
    )
    embedder_config: EmbedderConfig = Field(
        title="Embedder configuration",
    )
    parser_config: ParserConfig = Field(
        title="Parser configuration to parse the documents.",
    )
    vector_db_config: VectorDBConfig = Field(
        title="Vector DB config to store the indexed documents.",
    )
    data_ingestion_mode: DataIngestionMode = Field(title="Data ingestion mode")
    raise_error_on_failure: bool = Field(default=True, title="Raise error on failure")
    batch_size: int = Field(default=100, title="Batch size for indexing", ge=1)
