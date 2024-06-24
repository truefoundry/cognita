import enum
import uuid
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, constr, root_validator

from backend.constants import FQN_SEPARATOR


class DataIngestionMode(str, Enum):
    """
    Data Ingestion Modes
    """

    NONE = "NONE"
    INCREMENTAL = "INCREMENTAL"
    FULL = "FULL"


class DataPoint(BaseModel):
    """
    Data point describes a single data point in the data source
    Properties:
        data_source_fqn (str): Fully qualified name of the data source
        data_point_fqn (str): Fully qualified name for the data point with respect to the data source
        data_point_uri (str): URI for the data point for given data source. It could be url, file path or any other identifier
        data_point_hash (str): Hash of the data point for the given data source that is guaranteed to be updated for any update in data point at source
        metadata (Optional[Dict[str, str]]): Additional metadata for the data point
    """

    data_source_fqn: str = Field(
        title="Fully qualified name of the data source",
    )

    data_point_uri: str = Field(
        title="URI for the data point for given data source. It could be url, file path or any other identifier",
    )

    data_point_hash: str = Field(
        title="Hash of the data point for the given data source that is guaranteed to be updated for any update in data point at source",
    )

    metadata: Optional[Dict[str, str]] = Field(
        title="Additional metadata for the data point",
    )

    @property
    def data_point_fqn(self) -> str:
        return f"{FQN_SEPARATOR}".join([self.data_source_fqn, self.data_point_uri])


class DataPointVector(BaseModel):
    """
    Data point vector describes a single data point in the vector store
    Additional Properties:
        data_point_vector_id (str): Unique identifier for the data point with respect to the vector store
        data_point_fqn (str): Unique identifier for the data point with respect to the data source
        data_point_hash (str): Hash of the data point for the given data source that is guaranteed to be updated for any update in data point at source
    """

    data_point_vector_id: str = Field(
        title="Unique identifier for the data point with respect to the vector store",
    )
    data_point_fqn: str = Field(
        title="Unique identifier for the data point with respect to the data source",
    )
    data_point_hash: str = Field(
        title="Hash of the data point for the given data source that is guaranteed to be updated for any update in data point at source",
    )


class LoadedDataPoint(DataPoint):
    """
    Loaded data point describes a single data point in the data source after loading it as local file
    Additional Properties:
        local_filepath (str): Local file path of the data point
        file_extension (str): File extension of the data point
    Parent: DataPoint
    """

    local_filepath: str = Field(
        title="Local file path of the loaded data point",
    )
    file_extension: Optional[str] = Field(
        title="File extension of the loaded data point",
    )
    local_metadata_file_path: Optional[str] = Field(
        title="Local file path of the metadata file",
    )


class ModelType(str, Enum):
    """
    Model types available in LLM gateway
    """

    chat = "chat"
    embedding = "embedding"


class ModelConfig(BaseModel):
    name: str
    type: Optional[ModelType]
    parameters: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "parameters": self.parameters,
        }


class ModelProviderConfig(BaseModel):
    provider_name: str
    api_format: str
    llm_model_ids: List[str]
    embedding_model_ids: List[str]
    api_key_env_var: str
    base_url: Optional[str] = None


class EmbedderConfig(BaseModel):
    """
    Embedder configuration
    """

    model_config: ModelConfig
    config: Optional[Dict[str, Any]] = Field(
        title="Configuration for the embedder", default={}
    )


class ParserConfig(BaseModel):
    """
    Parser configuration
    """

    chunk_size: int = Field(title="Chunk Size for data parsing", ge=1, default=1000)

    chunk_overlap: int = Field(title="Chunk Overlap for indexing", ge=0, default=20)

    parser_map: Dict[str, str] = Field(
        title="Mapping of file extensions to parsers",
        default={
            ".md": "MarkdownParser",
            ".pdf": "PdfParserFast",
        },
    )

    additional_config: Optional[Dict[str, Any]] = Field(
        title="Additional optional configuration for the parser",
        default={"key": "value"},
    )


class VectorDBConfig(BaseModel):
    """
    Vector db configuration
    """

    provider: str
    local: bool = False
    url: Optional[str] = None
    api_key: Optional[str] = None
    config: Optional[dict] = None


class QdrantClientConfig(BaseModel):
    """
    Qdrant extra configuration
    """

    class Config:
        extra = "allow"

    port: Optional[int] = None
    grpc_port: int = 6334
    prefix: Optional[str] = None
    prefer_grpc: bool = False
    timeout: int = 300


class MetadataStoreConfig(BaseModel):
    """
    Metadata store configuration
    """

    provider: str
    config: Optional[dict] = Field(default_factory=dict)


class RetrieverConfig(BaseModel):
    """
    Retriever configuration
    """

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
    """
    Defined run status for data ingestion job run into vector db
    """

    INITIALIZED = "INITIALIZED"
    FETCHING_EXISTING_VECTORS = "FETCHING_EXISTING_VECTORS"
    FETCHING_EXISTING_VECTORS_FAILED = "FETCHING_EXISTING_VECTORS_FAILED"
    DATA_INGESTION_STARTED = "DATA_INGESTION_STARTED"
    DATA_INGESTION_COMPLETED = "DATA_INGESTION_COMPLETED"
    DATA_INGESTION_FAILED = "DATA_INGESTION_FAILED"
    DATA_CLEANUP_STARTED = "DATA_CLEANUP_STARTED"
    DATA_CLEANUP_FAILED = "DATA_CLEANUP_FAILED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class BaseDataIngestionRun(BaseModel):
    """
    Base data ingestion run configuration
    """

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
    status: Optional[DataIngestionRunStatus] = Field(
        title="Status of the data ingestion run",
    )


class BaseDataSource(BaseModel):
    """
    Data source configuration
    """

    type: str = Field(
        title="Type of the data source",
    )
    uri: str = Field(
        title="A unique identifier for the data source",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        title="Additional config for your data source"
    )

    @property
    def fqn(self):
        return f"{FQN_SEPARATOR}".join([self.type, self.uri])

    @root_validator
    def validate_fqn(cls, values: Dict) -> Dict:
        values["fqn"] = f"{FQN_SEPARATOR}".join([values["type"], values["uri"]])
        return values


class CreateDataSource(BaseDataSource):
    pass


class DataSource(BaseDataSource):
    pass


class AssociatedDataSources(BaseModel):
    """
    Associated data source configuration
    """

    data_source_fqn: str = Field(
        title="Fully qualified name of the data source",
    )
    parser_config: ParserConfig = Field(
        title="Parser configuration for the data transformation", default_factory=dict
    )
    data_source: Optional[DataSource] = Field(
        title="Data source associated with the collection"
    )


class IngestDataToCollectionDto(BaseModel):
    """
    Configuration to ingest data to collection
    """

    collection_name: str = Field(
        title="Name of the collection",
    )

    data_source_fqn: Optional[str] = Field(
        title="Fully qualified name of the data source",
    )

    data_ingestion_mode: DataIngestionMode = Field(
        default=DataIngestionMode.INCREMENTAL,
        title="Data ingestion mode for the data ingestion",
    )

    raise_error_on_failure: Optional[bool] = Field(
        title="Flag to configure weather to raise error on failure or not. Default is True",
        default=True,
    )

    run_as_job: bool = Field(
        title="Flag to configure weather to run the ingestion as a job or not. Default is False",
        default=False,
    )

    batch_size: int = Field(
        title="Batch size for data ingestion",
        default=100,
    )


class AssociateDataSourceWithCollection(BaseModel):
    """
    Configuration to associate data source to collection
    """

    data_source_fqn: str = Field(
        title="Fully qualified name of the data source",
    )
    parser_config: ParserConfig = Field(
        title="Parser configuration for the data transformation", default_factory=dict
    )


class AssociateDataSourceWithCollectionDto(AssociateDataSourceWithCollection):
    """
    Configuration to associate data source to collection
    """

    collection_name: str = Field(
        title="Name of the collection",
    )
    data_source_fqn: str = Field(
        title="Fully qualified name of the data source",
    )
    parser_config: ParserConfig = Field(
        title="Parser configuration for the data transformation", default_factory=dict
    )


class UnassociateDataSourceWithCollectionDto(BaseModel):
    """
    Configuration to unassociate data source to collection
    """

    collection_name: str = Field(
        title="Name of the collection",
    )
    data_source_fqn: str = Field(
        title="Fully qualified name of the data source",
    )


class BaseCollection(BaseModel):
    """
    Base collection configuration
    """

    name: constr(regex=r"^[a-z][a-z0-9-]*$") = Field(  # type: ignore
        title="a unique name to your collection",
        description="Should only contain lowercase alphanumeric character and hypen, should start with alphabet",
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
    associated_data_sources: Dict[str, AssociatedDataSources] = Field(
        title="Data sources associated with the collection", default_factory=dict
    )


class CreateCollectionDto(CreateCollection):
    associated_data_sources: Optional[List[AssociateDataSourceWithCollection]] = Field(
        title="Data sources associated with the collection"
    )


class UploadToDataDirectoryDto(BaseModel):
    filepaths: List[str]
    # allow only small case alphanumeric and hyphen, should contain at least one alphabet and begin with alphabet
    upload_name: str = Field(
        title="Name of the upload",
        regex=r"^[a-z][a-z0-9-]*$",
        default=str(uuid.uuid4()),
    )


class ListDataIngestionRunsDto(BaseModel):
    collection_name: str = Field(
        title="Name of the collection",
    )
    data_source_fqn: Optional[str] = Field(
        title="Fully qualified name of the data source", default=None
    )
