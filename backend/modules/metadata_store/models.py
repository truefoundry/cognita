import enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from backend.utils.base import EmbedderConfig, KnowledgeSource, ParserConfig


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
    indexer_job_runs: Optional[List[CollectionIndexerJobRun]] = None
