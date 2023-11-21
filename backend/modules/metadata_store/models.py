from pydantic import BaseModel
import enum
from backend.utils.base import EmbedderConfig, KnowledgeSource, ParserConfig
from typing import Optional
from datetime import datetime


class CollectionIndexerJobRunStatus(str, enum.Enum):
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CollectionIndexerJobRunBase(BaseModel):
    knowledge_source: KnowledgeSource
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
    indexer_job_runs: Optional[list[CollectionIndexerJobRun]] = None
