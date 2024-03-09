from pydantic import BaseModel, Field

from backend.types import LLMConfig, RetrieverConfig


class DefaultQueryInput(BaseModel):
    """
    Model for Query input.
    Requires a collection name, retriever configuration, query, LLM configuration and prompt template.
    """

    collection_name: str = Field(
        default=None,
        title="Collection name on which to search",
    )

    retriever_config: RetrieverConfig = Field(
        title="Retriever configuration",
    )
    query: str = Field(title="Question to search for", max_length=1000)
    model_configuration: LLMConfig
    prompt_template: str = Field(
        default="""Here is the context information:\n\n'''\n{context}\n'''\n\nQuestion: {question}\nAnswer:""",
        title="Prompt Template to use for generating answer to the question using the context",
    )
