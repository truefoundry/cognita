from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Extra, Field, constr


class DocumentMetadata(BaseModel):
    """
    Document metadata saved in vector store
    document_id: str unique identifier for the document source
    """

    document_id: str
    source: Optional[str]

    class Config:
        extra = Extra.allow


class EmbedderConfig(BaseModel):
    description: str | None = None
    provider: str
    config: dict = None


class SourceConfig(BaseModel):
    uri: str

    class Config:
        extra = Extra.allow


class DataSource(BaseModel):
    type: Literal["mlfoundry", "github", "local", "web"]
    credentials: Optional[dict] = None
    config: SourceConfig

    class Config:
        use_enum_values = True


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
    name: constr(regex=r"^[a-z][a-z0-9]*$") = Field(
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


class LLMConfig(BaseModel):
    name: str = Field(title="Name of the model from the Truefoundry LLM Gateway")
    parameters: dict = None


class RetrieverConfig(BaseModel):
    class_name: Literal["VectorStoreRetriever", "CustomRetriever"] = Field(
        default="VectorStoreRetriever"
    )
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


class SearchQuery(BaseModel):
    collection_name: str = Field(
        default=None,
        title="Collection name on which to search",
    )
    retrieval_chain_name: Literal["RetrievalQA", "CustomRetrievalQA"] = Field(
        default="RetrievalQA",
        title="Name of the retrieval chain to use for retrieving documents",
    )
    retriever_config: RetrieverConfig = Field(
        title="Retriever configuration",
    )
    query: str = Field(title="Question to search for", max_length=1000)
    model_configuration: LLMConfig
    debug: bool = Field(
        default=False, title="If true, then return the complete prompt sent to LLM"
    )
    prompt_template: str = Field(
        default="""Here is the context information:\n\n'''\n{context}\n'''\n\nQuestion: {question}\nAnswer:""",
        title="Prompt Template to use for generating answer to the question using the context",
    )


class UploadToDataDirectoryDto(BaseModel):
    collection_name: str
    filepaths: List[str]


class ModelType(str, Enum):
    completion = "completion"
    chat = "chat"
    embedding = "embedding"
