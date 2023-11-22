from typing import Optional
from pydantic import BaseModel, Field
from typing import Literal


class EmbedderConfig(BaseModel):
    description: str | None = None
    provider: str
    config: dict = None


class SourceConfig(BaseModel):
    uri: str


class KnowledgeSource(BaseModel):
    type: Literal["mlfoundry", "github", "local"]
    credentials: Optional[dict] = None
    config: SourceConfig

    class Config:
        use_enum_values = True


class ParserConfig(BaseModel):
    pass

    class Config:
        allow_extra = True


class VectorDBConfig(BaseModel):
    provider: str
    url: str
    api_key: Optional[str]


class CreateCollection(BaseModel):
    name: str = Field(
        title="a unique name to your collection",
    )
    description: Optional[str] = Field(
        title="a description for your collection",
    )
    embedder_config: EmbedderConfig = Field(
        title="Embedder configuration",
    )
    chunk_size: int = Field(title="Chunk Size for indexing", ge=1)


class AddDocuments(BaseModel):
    knowledge_source: KnowledgeSource = Field(
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
    knowledge_source: KnowledgeSource = Field(
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
        default={
            "provider": "weaviate",
            "url": "",
            "api_key": "",
        },
        title="Vector DB config to store the indexed documents.",
    )


class LLMConfig(BaseModel):
    name: str = Field(title="Name of the model from the Truefoundry LLM Gateway")
    parameters: dict = None


class SearchQuery(BaseModel):
    collection_name: str = Field(
        default=None,
        title="Collection name on which to search",
    )
    k: int = Field(
        default=4, title="Number of chunks to send to LLM in context", ge=1, le=100
    )
    mmr: Optional[bool] = Field(
        default=True,
        title="""If true, then use Maximal Marginal Relevance(mmr), else use similarity search. 
        In similarity search, it selects text chunk vectors that are most similar to the question vector. 
        search_type="mmr" uses the maximum marginal relevance search where it optimizes for similarity to 
        query AND diversity among selected documents.""",
    )
    fetch_k: Optional[int] = Field(
        default=20, title="Number of chunks to fetch for MMR. Only relevant if mmr=True"
    )
    query: str = Field(title="Question to search for", max_length=1000)
    model_configuration: LLMConfig
    debug: bool = Field(
        default=False, title="If true, then return the complete prompt sent to LLM"
    )
    prompt_template: str = Field(
        default="""Use the context below to answer question at the end.\n\n{context}\n\nQuestion: {question}\nAnswer:""",
        title="Prompt Template to use for generating answer to the question using the context",
    )
