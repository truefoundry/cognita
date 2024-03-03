import enum
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Extra, Field, constr


class DataIngestionMode(str, Enum):
    """
    Data Ingestion Modes
    """

    NONE = "NONE"
    INCREMENTAL = "INCREMENTAL"
    FULL = "FULL"


class DocumentMetadata(BaseModel):
    """
    Document metadata saved in vector store
    _document_id: str unique identifier for the document source
    """

    _document_id: str

    class Config:
        extra = Extra.allow


class EmbedderConfig(BaseModel):
    provider: str = Field(
        title="Provider of the embedder",
    )
    config: Optional[Dict[str, Any]] = Field(
        title="Configuration for the embedder",
        default_factory=dict,
    )


class ParserConfig(BaseModel):

    chunk_size: int = Field(title="Chunk Size for data parsing", ge=1, default=500)

    chunk_overlap: int = Field(title="Chunk Overlap for indexing", ge=0, default=0)

    parser_map: Dict[str, str] = Field(
        title="Mapping of file extensions to parsers",
        default={
            ".md": "MarkdownParser",
            ".pdf": "PdfParserFast",
            ".txt": "TextParser",
        },
    )


class VectorDBConfig(BaseModel):
    provider: str
    url: Optional[str] = None
    api_key: Optional[str] = None
    config: Optional[dict] = None


class MetadataStoreConfig(BaseModel):
    provider: str
    config: Optional[dict] = None


class EmbeddingCacheConfig(BaseModel):
    provider: str
    url: Optional[str] = None
    config: Optional[dict] = None


class LoadedDocument(BaseModel):
    filepath: str
    file_extension: str
    metadata: DocumentMetadata


class LLMConfig(BaseModel):
    name: str = Field(title="Name of the model from the Truefoundry LLM Gateway")
    parameters: dict = None


class RetrieverConfig(BaseModel):
    search_type: Literal["mmr", "similarity"] = Field(
        default="similarity",
        title="""Defines the type of search that the Retriever should perform. Can be "similarity" (default), "mmr", or "similarity_score_threshold".""",
    )
    k: int = Field(
        default=4,
        title="""Amount of documents to return (Default: 4)""",
    )
    fetch_k: int = Field(
        default=20,
        title="""Amount of documents to pass to MMR algorithm (Default: 20)""",
    )
    filter: Optional[dict] = Field(
        default=None,
        title="""Filter by document metadata""",
    )

    @property
    def get_search_type(self) -> str:
        ## Check at langchain.schema.vectorstore.VectorStore.as_retriever
        return self.search_type

    @property
    def get_search_kwargs(self) -> dict:
        ## Check at langchain.schema.vectorstore.VectorStore.as_retriever
        match self.search_type:
            case "similarity":
                return {"k": self.k, "filter": self.filter}
            case "mmr":
                return {"k": self.k, "fetch_k": self.fetch_k, "filter": self.filter}


class DataIngestionRunStatus(str, enum.Enum):
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    DATA_LOADING_STARTED = "DATA_LOADING_STARTED"
    CHUNKING_STARTED = "CHUNKING_STARTED"
    EMBEDDING_STARTED = "EMBEDDING_STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BaseDataIngestionRun(BaseModel):
    collection_name: str = Field(
        title="Name of the collection",
    )

    data_source_fqn: str = Field(
        title="Fully qualified name of the data source",
    )

    parser_config: ParserConfig = Field(
        title="Parser configuration for the data transformation", default_factory=dict
    )

    data_ingestion_mode: DataIngestionMode = Field(
        default=DataIngestionMode.INCREMENTAL,
        title="Data ingestion mode for the data ingestion",
    )

    raise_error_on_failure: Optional[bool] = Field(
        title="Flag to configure weather to raise error on failure or not. Default is True",
        default=True,
    )


class CreateDataIngestionRun(BaseDataIngestionRun):
    pass


class DataIngestionRun(BaseDataIngestionRun):
    name: str = Field(
        title="Name of the data ingestion run",
    )
    status: DataIngestionRunStatus = Field(
        title="Status of the data ingestion run",
    )


class BaseCollection(BaseModel):
    name: constr(regex=r"^[a-z][a-z0-9]*$") = Field(  # type: ignore
        title="a unique name to your collection",
        description="Should only contain lowercase alphanumeric character",
    )
    description: Optional[str] = Field(
        title="a description for your collection",
    )
    embedder_config: EmbedderConfig = Field(
        title="Embedder configuration", default_factory=dict
    )


class CreateCollection(BaseCollection):
    pass


class Collection(BaseCollection):
    pass


class BaseDataSource(BaseModel):
    type: str = Field(
        title="Type of the data source",
    )
    uri: str = Field(
        title="A unique identifier for the data source",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        title="Additional config for your data source", default_factory=dict
    )


class CreateDataSource(BaseDataSource):
    pass


class DataSource(BaseDataSource):
    fqn: str = Field(
        title="Fully qualified name of the data source",
    )


class UploadToDataDirectoryDto(BaseModel):
    collection_name: str
    filepaths: List[str]


class ModelType(str, Enum):
    completion = "completion"
    chat = "chat"
    embedding = "embedding"
