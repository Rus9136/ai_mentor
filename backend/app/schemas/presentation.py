"""
Pydantic schemas for Presentation generation and CRUD.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# --- REQUEST ---


class PresentationGenerateRequest(BaseModel):
    paragraph_id: int
    class_id: Optional[int] = None
    language: str = Field(default="kk", pattern="^(kk|ru)$")
    slide_count: int = Field(default=10)

    @field_validator("slide_count")
    @classmethod
    def validate_slide_count(cls, v: int) -> int:
        if v not in (5, 10, 15):
            raise ValueError("slide_count must be 5, 10, or 15")
        return v


# --- RESPONSE ---


class PresentationContext(BaseModel):
    paragraph_title: str
    chapter_title: str
    textbook_title: str
    subject: str
    grade_level: int
    textbook_id: int


class PresentationGenerateResponse(BaseModel):
    presentation: dict
    context: PresentationContext


# --- SAVE / CRUD ---


class PresentationSaveRequest(BaseModel):
    paragraph_id: int
    class_id: Optional[int] = None
    language: str = Field(default="kk", pattern="^(kk|ru)$")
    slide_count: int = Field(default=10)
    title: Optional[str] = None
    slides_data: dict
    context_data: dict


class PresentationUpdateRequest(BaseModel):
    title: Optional[str] = None
    slides_data: Optional[dict] = None


class PresentationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    language: str
    slide_count: int
    paragraph_id: int
    class_id: Optional[int] = None
    subject: Optional[str] = None
    grade_level: Optional[int] = None
    created_at: datetime


class PresentationFullResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    teacher_id: int
    school_id: int
    paragraph_id: int
    class_id: Optional[int] = None
    language: str
    slide_count: int
    slides_data: dict
    context_data: dict
    created_at: datetime
    updated_at: datetime
