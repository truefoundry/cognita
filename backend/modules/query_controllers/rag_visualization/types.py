from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from pydantic import Field

from backend.modules.query_controllers.types import BaseQueryInput, Document
from backend.types import ConfiguredBaseModel


class RAGStepType(str, Enum):
    """Types of steps in the RAG pipeline"""

    QUERY_PROCESSING = "query_processing"
    EMBEDDING_GENERATION = "embedding_generation"
    VECTOR_SEARCH = "vector_search"
    DOCUMENT_RETRIEVAL = "document_retrieval"
    RERANKING = "reranking"
    CONTEXT_PREPARATION = "context_preparation"
    PROMPT_CONSTRUCTION = "prompt_construction"
    LLM_GENERATION = "llm_generation"
    RESPONSE_FORMATTING = "response_formatting"


class RAGStepStatus(str, Enum):
    """Status of each RAG step"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RAGStep(ConfiguredBaseModel):
    """Individual step in the RAG pipeline"""

    step_id: str = Field(title="Unique identifier for the step")
    step_type: RAGStepType = Field(title="Type of the RAG step")
    step_name: str = Field(title="Human-readable name of the step")
    status: RAGStepStatus = Field(
        default=RAGStepStatus.PENDING, title="Current status of the step"
    )
    start_time: Optional[datetime] = Field(None, title="When the step started")
    end_time: Optional[datetime] = Field(None, title="When the step completed")
    duration_ms: Optional[int] = Field(None, title="Duration in milliseconds")
    input_data: Optional[Dict[str, Any]] = Field(None, title="Input data for the step")
    output_data: Optional[Dict[str, Any]] = Field(
        None, title="Output data from the step"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, title="Additional metadata for the step"
    )
    error_message: Optional[str] = Field(None, title="Error message if step failed")


class RetrievedDocument(ConfiguredBaseModel):
    """Document retrieved during the RAG process with additional visualization metadata"""

    document: Document = Field(title="The retrieved document")
    similarity_score: Optional[float] = Field(
        None, title="Similarity score with the query"
    )
    rerank_score: Optional[float] = Field(
        None, title="Reranking score if reranking was applied"
    )
    retrieval_method: Optional[str] = Field(
        None, title="Method used to retrieve this document"
    )
    chunk_index: Optional[int] = Field(
        None, title="Index of the chunk within the document"
    )


class RAGVisualizationData(ConfiguredBaseModel):
    """Complete visualization data for a RAG query"""

    query_id: str = Field(title="Unique identifier for the query")
    original_query: str = Field(title="The original user query")
    processed_query: Optional[str] = Field(
        None, title="Processed/modified query if applicable"
    )
    collection_name: str = Field(title="Name of the collection used")
    model_configuration: Dict[str, Any] = Field(title="Configuration of the model used")
    retriever_config: Dict[str, Any] = Field(
        title="Configuration of the retriever used"
    )

    # Pipeline steps
    steps: List[RAGStep] = Field(
        default_factory=list, title="List of all pipeline steps"
    )

    # Retrieved documents with scores
    retrieved_documents: List[RetrievedDocument] = Field(
        default_factory=list, title="Documents retrieved during the process"
    )

    # Final results
    final_answer: Optional[str] = Field(None, title="Final generated answer")
    total_duration_ms: Optional[int] = Field(None, title="Total query processing time")

    # Metrics
    metrics: Optional[Dict[str, Any]] = Field(
        None, title="Performance and quality metrics"
    )


class RAGVisualizationQueryInput(BaseQueryInput):
    """Query input for RAG visualization with additional visualization options"""

    include_embeddings: bool = Field(
        default=False, title="Whether to include embedding vectors in the response"
    )
    include_intermediate_steps: bool = Field(
        default=True, title="Whether to include detailed intermediate step information"
    )
    include_timing_info: bool = Field(
        default=True, title="Whether to include timing information for each step"
    )


class RAGVisualizationResponse(ConfiguredBaseModel):
    """Response containing both the answer and visualization data"""

    answer: str = Field(title="The generated answer")
    visualization_data: RAGVisualizationData = Field(
        title="Complete visualization data"
    )
    docs: List[Document] = Field(default_factory=list, title="Retrieved documents")


class RAGVisualizationStreamChunk(ConfiguredBaseModel):
    """Streaming chunk for RAG visualization"""

    type: str = Field(title="Type of the chunk")
    content: Union[str, RAGStep, List[RetrievedDocument], Dict[str, Any]] = Field(
        title="Content of the chunk"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, title="Timestamp of the chunk"
    )
