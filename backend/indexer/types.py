from typing import Optional

from pydantic import BaseModel, Field

from backend.types import (
    DataSource,
    EmbedderConfig,
    EmbeddingCacheConfig,
    IndexingDeletionMode,
    MetadataStoreConfig,
    ParserConfig,
    VectorDBConfig,
)


class IndexerConfig(BaseModel):
    collection_name: str = Field(
        title="a unique name to your collection",
    )
    indexer_job_run_name: str = Field(
        title="a unique name to your indexing run",
    )
    data_source: DataSource = Field(
        title="Path of the source of documents to be indexed. Can be local, github or mlfoundry artifact",
    )
    chunk_size: int = Field(default=1000, title="chunk size for indexing", ge=1)

    embedder_config: EmbedderConfig = Field(
        title="Embedder configuration",
    )
    parser_config: ParserConfig = Field(
        default={
            ".md": "MarkdownParser",
            ".pdf": "PdfParserFast",
            ".txt": "TextParser",
        },
        title="Mapping of file extensions to parsers. Required only incase, multiple parsers are available for same extension.",
    )
    vector_db_config: VectorDBConfig = Field(
        title="Vector DB config to store the indexed documents.",
    )
    metadata_store_config: MetadataStoreConfig = Field(
        title="Vector DB config to store the indexed documents.",
    )
    embedding_cache_config: Optional[EmbeddingCacheConfig] = Field(
        title="Embedding cache config", default=None
    )
    deletion_mode: IndexingDeletionMode = Field(
        default=IndexingDeletionMode.INCREMENTAL, title="Deletion mode for indexing"
    )
