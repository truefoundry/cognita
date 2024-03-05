import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.types import DataIngestionMode, DataSource, EmbedderConfig, ParserConfig


class CollectionIndexerJobRunStatus(str, enum.Enum):
    """
    Configuration for job run status allowed for indexer job
    """
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    DATA_LOADING_STARTED = "DATA_LOADING_STARTED"
    CHUNKING_STARTED = "CHUNKING_STARTED"
    EMBEDDING_STARTED = "EMBEDDING_STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CollectionIndexerJobRunBase(BaseModel):
    """
    Base configuration for Collection Indexer Job Run
    """
    data_source: DataSource
    parser_config: ParserConfig
    data_ingestion_mode: DataIngestionMode


class CollectionIndexerJobRunCreate(CollectionIndexerJobRunBase):
    pass


class CollectionIndexerJobRun(CollectionIndexerJobRunBase):
    name: str
    status: CollectionIndexerJobRunStatus
    created_at: datetime = None
