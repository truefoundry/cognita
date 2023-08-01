from typing import Optional

from pydantic import BaseModel, Field


class RepoModel(BaseModel):
    repo_name: str
    job_fqn: str
    source_uri: str
    embedder: str
    chunk_size: str
    embedder_config: Optional[str] = ""
    repo_creds: Optional[str] = ""
    parsers_map: Optional[str] = ""


class LLMConfig(BaseModel):
    name: str = Field(title="Name of the model from the Truefoundry Playground")
    provider: str = Field(title="Provider of the model from the Truefoundry Playground")
    parameters: dict


class SearchQuery(BaseModel):
    # Name of the document repo on which to run the query
    repo_name: str = Field(
        default=None,
        title="""Document repo name on which to search. This name should be in the 
                           list of already indexed repositories""",
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
