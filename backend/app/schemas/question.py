"""
Pydantic schemas for Question and QuestionOption content.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.models.test import QuestionType


class QuestionOptionCreate(BaseModel):
    """Schema for creating a new question option."""

    order: int = Field(..., ge=1, description="Order of the option (starting from 1)")
    option_text: str = Field(..., min_length=1, description="Option text")
    is_correct: bool = Field(default=False, description="Is this option correct")


class QuestionOptionUpdate(BaseModel):
    """Schema for updating an existing question option."""

    order: Optional[int] = Field(None, ge=1, description="Order of the option")
    option_text: Optional[str] = Field(None, min_length=1, description="Option text")
    is_correct: Optional[bool] = Field(None, description="Is this option correct")


class QuestionOptionResponse(BaseModel):
    """Schema for question option response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    order: int
    option_text: str
    is_correct: bool

    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_deleted: bool


class QuestionCreate(BaseModel):
    """Schema for creating a new question."""

    order: int = Field(..., ge=1, description="Order of the question in test (starting from 1)")
    question_type: QuestionType = Field(..., description="Type of question")
    question_text: str = Field(..., min_length=1, description="Question text")
    explanation: Optional[str] = Field(None, description="Explanation of correct answer")
    points: float = Field(default=1.0, ge=0.0, description="Points for correct answer")


class QuestionUpdate(BaseModel):
    """Schema for updating an existing question."""

    order: Optional[int] = Field(None, ge=1, description="Order of the question")
    question_type: Optional[QuestionType] = Field(None, description="Type of question")
    question_text: Optional[str] = Field(None, min_length=1, description="Question text")
    explanation: Optional[str] = Field(None, description="Explanation of correct answer")
    points: Optional[float] = Field(None, ge=0.0, description="Points for correct answer")


class QuestionResponse(BaseModel):
    """Schema for question response with options."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    test_id: int
    order: int
    question_type: QuestionType
    question_text: str
    explanation: Optional[str]
    points: float

    # Nested options
    options: List[QuestionOptionResponse] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_deleted: bool


class QuestionListResponse(BaseModel):
    """Schema for question list response (lightweight, without options)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    test_id: int
    order: int
    question_type: QuestionType
    question_text: str
    points: float
    created_at: datetime
