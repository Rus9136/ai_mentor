"""
Pydantic schemas for Chapter content.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ChapterCreate(BaseModel):
    """Schema for creating a new chapter."""

    textbook_id: int = Field(..., description="ID of the parent textbook")
    title: str = Field(..., min_length=1, max_length=255, description="Chapter title")
    number: int = Field(..., ge=1, description="Chapter number in textbook")
    order: int = Field(..., ge=1, description="Display order in textbook")
    description: Optional[str] = Field(None, description="Chapter description")
    learning_objective: Optional[str] = Field(None, description="Learning objectives for this chapter")


class ChapterUpdate(BaseModel):
    """Schema for updating an existing chapter."""

    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Chapter title")
    number: Optional[int] = Field(None, ge=1, description="Chapter number in textbook")
    order: Optional[int] = Field(None, ge=1, description="Display order in textbook")
    description: Optional[str] = Field(None, description="Chapter description")
    learning_objective: Optional[str] = Field(None, description="Learning objectives for this chapter")


class ChapterResponse(BaseModel):
    """Schema for chapter response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    textbook_id: int
    title: str
    number: int
    order: int
    description: Optional[str]
    learning_objective: Optional[str]

    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_deleted: bool


class ChapterListResponse(BaseModel):
    """Schema for chapter list response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    textbook_id: int
    title: str
    number: int
    order: int
    created_at: datetime
