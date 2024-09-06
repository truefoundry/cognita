from typing import Any, ClassVar, Dict, List, Optional, Sequence, Union

from pydantic import Field, model_validator
from qdrant_client.models import Filter as QdrantFilter

from backend.types import ConfiguredBaseModel, ModelConfig

GENERATION_TIMEOUT_SEC = 60.0 * 10


class Document(ConfiguredBaseModel):
    page_content: str
    metadata: dict = Field(default_factory=dict)


class Answer(ConfiguredBaseModel):
    type: str = "answer"
    content: str


class Docs(ConfiguredBaseModel):
    type: str = "docs"
    content: List[Document] = Field(default_factory=list)


# TODO (chiragjn): Remove all asserts and replace them with proper pydantic validations or raises


class VectorStoreRetrieverConfig(ConfiguredBaseModel):
    """
    Configuration for VectorStore Retriever
    """

    search_type: str = Field(
        default="similarity",
        title="""Defines the type of search that the Retriever should perform.
Can be 'similarity' (default), 'mmr', or 'similarity_score_threshold'.
    - "similarity": Retrieve the top k most similar documents to the query.,
    - "mmr": Retrieve the top k most similar documents to the query and then rerank them using Maximal Marginal Relevance (MMR).,
    - "similarity_score_threshold": Retrieve all documents with similarity score greater than a threshold.
""",
    )

    search_kwargs: dict = Field(default_factory=dict)

    filter: Optional[Dict[Any, Any]] = Field(
        default_factory=dict,
        title="""Filter by document metadata""",
    )

    allowed_search_types: ClassVar[Sequence[str]] = (
        "similarity",
        "similarity_score_threshold",
        "mmr",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_search_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate search type."""
        if not isinstance(values, dict):
            raise ValueError(
                f"Unexpected Pydantic v2 Validation: values are of type {type(values)}"
            )

        search_type = values.get("search_type")

        assert (
            search_type in cls.allowed_search_types
        ), f"search_type of {search_type} not allowed. Valid values are: {cls.allowed_search_types}"

        search_kwargs = values.get("search_kwargs")

        if search_type == "similarity":
            assert "k" in search_kwargs, "k is required for similarity search"

        elif search_type == "mmr":
            assert "k" in search_kwargs, "k is required in search_kwargs for mmr search"
            assert (
                "fetch_k" in search_kwargs
            ), "fetch_k is required in search_kwargs for mmr search"

        elif search_type == "similarity_score_threshold":
            assert (
                "score_threshold" in search_kwargs
            ), "score_threshold with a float value(0~1) is required in search_kwargs for similarity_score_threshold search"

        filters = values.get("filter")
        if filters:
            search_kwargs["filter"] = QdrantFilter.model_validate(filters)
        return values


class MultiQueryRetrieverConfig(VectorStoreRetrieverConfig):
    retriever_llm_configuration: ModelConfig = Field(
        title="LLM configuration for the retriever",
    )


class ContextualCompressionRetrieverConfig(VectorStoreRetrieverConfig):
    compressor_model_name: str = Field(
        title="model name of the compressor",
    )

    top_k: int = Field(
        title="Top K docs to collect post compression",
    )

    allowed_compressor_model_providers: ClassVar[Sequence[str]]


class ContextualCompressionMultiQueryRetrieverConfig(
    ContextualCompressionRetrieverConfig, MultiQueryRetrieverConfig
):
    pass


class BaseQueryInput(ConfiguredBaseModel):
    """
    Model for Query input.
    Requires a Sequence name, retriever configuration, query, LLM configuration and prompt template.
    """

    collection_name: str = Field(
        default=None,
        title="Collection name on which to search",
    )

    query: str = Field(title="Question to search for")

    # TODO (chiragjn): pydantic v2 does not like fields that start with model_
    model_configuration: ModelConfig

    prompt_template: str = Field(
        title="Prompt Template to use for generating answer to the question using the context",
    )

    retriever_name: str = Field(
        title="Retriever name",
    )

    retriever_config: Union[
        VectorStoreRetrieverConfig,
        MultiQueryRetrieverConfig,
        ContextualCompressionRetrieverConfig,
        ContextualCompressionMultiQueryRetrieverConfig,
    ] = Field(
        title="Retriever configuration",
    )

    allowed_retriever_types: ClassVar[Sequence[str]] = (
        "vectorstore",
        "multi-query",
        "contextual-compression",
        "contextual-compression-multi-query",
    )

    internet_search_enabled: Optional[bool] = Field(
        title="Enable internet search", default=False
    )

    stream: bool = Field(title="Stream the results", default=False)

    @model_validator(mode="before")
    @classmethod
    def validate_retriever_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(values, dict):
            raise ValueError(
                f"Unexpected Pydantic v2 Validation: values are of type {type(values)}"
            )

        retriever_name = values.get("retriever_name")

        if retriever_name == "vectorstore":
            values["retriever_config"] = VectorStoreRetrieverConfig(
                **values.get("retriever_config")
            )

        elif retriever_name == "multi-query":
            values["retriever_config"] = MultiQueryRetrieverConfig(
                **values.get("retriever_config")
            )

        elif retriever_name == "contextual-compression":
            values["retriever_config"] = ContextualCompressionRetrieverConfig(
                **values.get("retriever_config")
            )

        elif retriever_name == "contextual-compression-multi-query":
            values["retriever_config"] = ContextualCompressionMultiQueryRetrieverConfig(
                **values.get("retriever_config")
            )
        else:
            raise ValueError(
                f"Unexpected retriever name: {retriever_name}. "
                f"Valid values are: {cls.allowed_retriever_types}"
            )

        return values
