from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Extra, Field, constr


class IndexingMode(str, Enum):
    """
    Indexing modes
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
    description: str | None = None
    provider: str
    config: dict = None

class DataSource(BaseModel):
    type: str
    uri: str
    class Config:
        use_enum_values = True
        extra = Extra.allow


class ParserConfig(BaseModel):
    class Config:
        extra = Extra.allow


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


class CreateCollection(BaseModel):
    name: constr(regex=r"^[a-z][a-z0-9]*$") = Field(  # type: ignore
        title="a unique name to your collection",
        description="Should only contain lowercase alphanumeric character",
    )
    description: Optional[str] = Field(
        title="a description for your collection",
    )
    embedder_config: EmbedderConfig = Field(
        title="Embedder configuration",
    )
    chunk_size: int = Field(title="Chunk Size for indexing", ge=1)


class AddDocuments(BaseModel):
    data_source: DataSource = Field(
        title="Path of the source of documents to be indexed. Can be local, github or mlfoundry artifact",
    )

    parser_config: ParserConfig = Field(
        default={
            ".md": "MarkdownParser",
            ".pdf": "PdfParserFast",
            ".txt": "TextParser",
        },
        title="Mapping of file extensions to parsers. Required only incase, multiple parsers are available for same extension. Must be a valid json",
    )

    force: bool = Field(
        default=False,
        title="If true, then force index the documents even if there is active indexer job run",
    )

    indexing_mode: IndexingMode = Field(
        default=IndexingMode.INCREMENTAL, title="Indexing mode for the documents"
    )


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


class UploadToDataDirectoryDto(BaseModel):
    collection_name: str
    filepaths: List[str]


class ModelType(str, Enum):
    completion = "completion"
    chat = "chat"
    embedding = "embedding"
