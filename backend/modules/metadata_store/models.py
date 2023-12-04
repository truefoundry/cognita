import enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from backend.utils.base import DataSource, EmbedderConfig, ParserConfig


class CollectionIndexerJobRunStatus(str, enum.Enum):
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    DATA_LOADING_STARTED = "DATA_LOADING_STARTED"
    CHUNKING_STARTED = "CHUNKING_STARTED"
    EMBEDDING_STARTED = "EMBEDDING_STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CollectionIndexerJobRunBase(BaseModel):
    data_source: DataSource
    parser_config: ParserConfig


class CollectionIndexerJobRunCreate(CollectionIndexerJobRunBase):
    pass


class CollectionIndexerJobRun(CollectionIndexerJobRunBase):
    name: str
    status: CollectionIndexerJobRunStatus
    created_at: datetime = None


class CollectionBase(BaseModel):
    name: str
    description: str | None = None
    embedder_config: EmbedderConfig
    chunk_size: int


class CollectionCreate(CollectionBase):
    pass


class Collection(CollectionBase):
    indexer_job_runs: Optional[List[CollectionIndexerJobRun]] = None
