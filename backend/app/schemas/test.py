"""
Pydantic schemas for Test content.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.test import DifficultyLevel, TestPurpose


class TestCreate(BaseModel):
    """Schema for creating a new test."""

    title: str = Field(..., min_length=1, max_length=255, description="Test title")
    description: Optional[str] = Field(None, description="Test description")
    chapter_id: Optional[int] = Field(None, description="Chapter ID (optional)")
    paragraph_id: Optional[int] = Field(None, description="Paragraph ID (optional)")
    test_purpose: TestPurpose = Field(default=TestPurpose.FORMATIVE, description="Test purpose (diagnostic, formative, summative, practice)")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM, description="Difficulty level")
    time_limit: Optional[int] = Field(None, ge=1, description="Time limit in minutes (must be positive)")
    passing_score: float = Field(default=0.7, ge=0.0, le=1.0, description="Passing score (0.0 to 1.0)")
    is_active: bool = Field(default=True, description="Is test active")


class TestUpdate(BaseModel):
    """Schema for updating an existing test."""

    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Test title")
    description: Optional[str] = Field(None, description="Test description")
    chapter_id: Optional[int] = Field(None, description="Chapter ID")
    paragraph_id: Optional[int] = Field(None, description="Paragraph ID")
    test_purpose: Optional[TestPurpose] = Field(None, description="Test purpose")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Difficulty level")
    time_limit: Optional[int] = Field(None, ge=1, description="Time limit in minutes")
    passing_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Passing score (0.0 to 1.0)")
    is_active: Optional[bool] = Field(None, description="Is test active")


class TestResponse(BaseModel):
    """Schema for test response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: Optional[int] = Field(None, description="School ID (None for global tests)")
    chapter_id: Optional[int]
    paragraph_id: Optional[int]

    title: str
    description: Optional[str]
    test_purpose: TestPurpose
    difficulty: DifficultyLevel
    time_limit: Optional[int]
    passing_score: float
    is_active: bool

    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_deleted: bool


class TestListResponse(BaseModel):
    """Schema for test list response (lightweight)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: Optional[int]
    chapter_id: Optional[int]
    title: str
    test_purpose: TestPurpose
    difficulty: DifficultyLevel
    is_active: bool
    created_at: datetime
