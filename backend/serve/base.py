from typing import Optional

from pydantic import BaseModel


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
    name: str
    provider: str
    tag: str
    parameters: dict


class SearchQuery(BaseModel):
    repo_name: str
    k: int = 4
    maximal_marginal_relevance: Optional[bool] = True
    query: str  # Question to ask about the data
    model_configuration: LLMConfig
    debug: bool = False
    prompt_template: str = """Use the context below to answer question at the end.\n\n{context}\n\nQuestion: {question}\nAnswer:"""
