"""
Pydantic schemas for Textbook content.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TextbookCreate(BaseModel):
    """Schema for creating a new textbook."""

    title: str = Field(..., min_length=1, max_length=255, description="Textbook title")
    subject: str = Field(..., min_length=1, max_length=100, description="Subject name")
    grade_level: int = Field(..., ge=1, le=11, description="Grade level (1-11)")
    author: Optional[str] = Field(None, max_length=255, description="Author name")
    publisher: Optional[str] = Field(None, max_length=255, description="Publisher name")
    year: Optional[int] = Field(None, ge=1900, le=2100, description="Publication year")
    isbn: Optional[str] = Field(None, max_length=50, description="ISBN number")
    description: Optional[str] = Field(None, description="Textbook description")
    is_active: bool = Field(default=True, description="Is textbook active")


class TextbookUpdate(BaseModel):
    """Schema for updating an existing textbook."""

    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Textbook title")
    subject: Optional[str] = Field(None, min_length=1, max_length=100, description="Subject name")
    grade_level: Optional[int] = Field(None, ge=1, le=11, description="Grade level (1-11)")
    author: Optional[str] = Field(None, max_length=255, description="Author name")
    publisher: Optional[str] = Field(None, max_length=255, description="Publisher name")
    year: Optional[int] = Field(None, ge=1900, le=2100, description="Publication year")
    isbn: Optional[str] = Field(None, max_length=50, description="ISBN number")
    description: Optional[str] = Field(None, description="Textbook description")
    is_active: Optional[bool] = Field(None, description="Is textbook active")


class TextbookResponse(BaseModel):
    """Schema for textbook response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: Optional[int] = Field(None, description="School ID (None for global textbooks)")
    global_textbook_id: Optional[int] = Field(None, description="ID of global textbook if customized")
    is_customized: bool = Field(description="Is this a customized fork of a global textbook")
    version: int = Field(description="Version number of the textbook")
    source_version: Optional[int] = Field(None, description="Version of source textbook at fork time")

    title: str
    subject: str
    grade_level: int
    author: Optional[str]
    publisher: Optional[str]
    year: Optional[int]
    isbn: Optional[str]
    description: Optional[str]
    is_active: bool

    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_deleted: bool


class TextbookListResponse(BaseModel):
    """Schema for textbook list response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: Optional[int]
    title: str
    subject: str
    grade_level: int
    is_customized: bool
    is_active: bool
    version: int
    created_at: datetime
