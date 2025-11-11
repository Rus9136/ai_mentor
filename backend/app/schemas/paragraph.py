"""
Pydantic schemas for Paragraph content.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ParagraphQuestion(BaseModel):
    """Schema for paragraph question."""

    order: int = Field(..., ge=1, description="Question order/number")
    text: str = Field(..., min_length=1, description="Question text")


class ParagraphCreate(BaseModel):
    """Schema for creating a new paragraph."""

    chapter_id: int = Field(..., description="ID of the parent chapter")
    title: str = Field(..., min_length=1, max_length=255, description="Paragraph title")
    number: int = Field(..., ge=1, description="Paragraph number in chapter")
    order: int = Field(..., ge=1, description="Display order in chapter")
    content: str = Field(..., min_length=1, description="Paragraph content (HTML/Markdown)")
    summary: Optional[str] = Field(None, description="Brief summary of the paragraph")
    learning_objective: Optional[str] = Field(None, description="Learning objectives for this paragraph")
    lesson_objective: Optional[str] = Field(None, description="Lesson-specific objectives")
    key_terms: Optional[List[str]] = Field(None, description="Array of key terms for this paragraph")
    questions: Optional[List[ParagraphQuestion]] = Field(None, description="Array of questions for this paragraph")


class ParagraphUpdate(BaseModel):
    """Schema for updating an existing paragraph."""

    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Paragraph title")
    number: Optional[int] = Field(None, ge=1, description="Paragraph number in chapter")
    order: Optional[int] = Field(None, ge=1, description="Display order in chapter")
    content: Optional[str] = Field(None, min_length=1, description="Paragraph content (HTML/Markdown)")
    summary: Optional[str] = Field(None, description="Brief summary of the paragraph")
    learning_objective: Optional[str] = Field(None, description="Learning objectives for this paragraph")
    lesson_objective: Optional[str] = Field(None, description="Lesson-specific objectives")
    key_terms: Optional[List[str]] = Field(None, description="Array of key terms for this paragraph")
    questions: Optional[List[ParagraphQuestion]] = Field(None, description="Array of questions for this paragraph")


class ParagraphResponse(BaseModel):
    """Schema for paragraph response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_id: int
    title: str
    number: int
    order: int
    content: str
    summary: Optional[str]
    learning_objective: Optional[str]
    lesson_objective: Optional[str]
    key_terms: Optional[List[str]] = None
    questions: Optional[List[dict]] = None

    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_deleted: bool


class ParagraphListResponse(BaseModel):
    """Schema for paragraph list response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_id: int
    title: str
    number: int
    order: int
    summary: Optional[str]
    key_terms: Optional[List[str]] = None
    questions: Optional[List[dict]] = None
    created_at: datetime
