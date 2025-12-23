"""
Pydantic schemas for RAG service.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Request Schemas
# =============================================================================

class ExplainQuestionRequest(BaseModel):
    """Request to explain a test question or concept."""
    question_text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The question or concept to explain"
    )
    paragraph_id: Optional[int] = Field(
        None,
        description="Paragraph ID for context (optional)"
    )
    chapter_id: Optional[int] = Field(
        None,
        description="Chapter ID for context (optional)"
    )
    language: str = Field(
        default="ru",
        pattern="^(ru|kk)$",
        description="Response language: ru (Russian) or kk (Kazakh)"
    )


class ExplainParagraphRequest(BaseModel):
    """Request to explain paragraph content."""
    user_question: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional specific question about the paragraph"
    )
    language: str = Field(
        default="ru",
        pattern="^(ru|kk)$",
        description="Response language: ru or kk"
    )


class GenerateEmbeddingsRequest(BaseModel):
    """Request to generate embeddings for a paragraph (admin)."""
    force: bool = Field(
        default=False,
        description="Force regeneration even if embeddings exist"
    )


class BatchGenerateEmbeddingsRequest(BaseModel):
    """Request to generate embeddings for all paragraphs in a textbook."""
    force: bool = Field(
        default=False,
        description="Force regeneration even if embeddings exist"
    )


# =============================================================================
# Response Schemas
# =============================================================================

class Citation(BaseModel):
    """Citation reference to source paragraph."""
    paragraph_id: int = Field(..., description="Source paragraph ID")
    paragraph_title: Optional[str] = Field(None, description="Paragraph title")
    chapter_title: Optional[str] = Field(None, description="Chapter title")
    chunk_text: str = Field(..., description="Quoted text from source")
    relevance_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Relevance score (cosine similarity)"
    )


class ExplanationResponse(BaseModel):
    """Response with personalized explanation."""
    answer: str = Field(..., description="Generated explanation")
    citations: List[Citation] = Field(
        default_factory=list,
        description="Source citations"
    )
    mastery_level: str = Field(
        ...,
        pattern="^[ABC]$",
        description="Student's mastery level used for personalization"
    )
    model_used: str = Field(..., description="LLM model used")
    tokens_used: Optional[int] = Field(None, description="Total tokens consumed")
    processing_time_ms: Optional[int] = Field(
        None,
        description="Processing time in milliseconds"
    )


class EmbeddingChunkResponse(BaseModel):
    """Response for a single embedding chunk."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    paragraph_id: int
    chunk_index: int
    chunk_text: str = Field(
        ...,
        description="Chunk text (may be truncated for display)"
    )
    model: str


class EmbeddingStatusResponse(BaseModel):
    """Status of embeddings for a paragraph."""
    paragraph_id: int
    paragraph_title: Optional[str]
    chunks_count: int
    model: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    chunks: List[EmbeddingChunkResponse] = Field(default_factory=list)


class GenerateEmbeddingsResponse(BaseModel):
    """Response after generating embeddings."""
    paragraph_id: int
    chunks_created: int
    model: str
    total_tokens: int
    processing_time_ms: int


class BatchGenerateEmbeddingsResponse(BaseModel):
    """Response after batch generating embeddings for a textbook."""
    textbook_id: int
    textbook_title: Optional[str]
    total_paragraphs: int
    processed_paragraphs: int
    skipped_paragraphs: int
    total_chunks_created: int
    total_tokens: int
    processing_time_ms: int
    errors: List[str] = Field(default_factory=list)
