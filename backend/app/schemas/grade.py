"""
Pydantic schemas for Grade (school gradebook).
"""
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

from app.models.grade import GradeType


class GradeCreate(BaseModel):
    """Schema for creating a new grade."""

    student_id: int = Field(..., description="Student ID")
    subject_id: int = Field(..., description="Subject ID")
    class_id: Optional[int] = Field(None, description="Class ID (optional)")
    grade_value: int = Field(..., ge=1, le=10, description="Grade value (1-10)")
    grade_type: GradeType = Field(default=GradeType.CURRENT, description="Grade type: CURRENT, SOR, SOCH, EXAM")
    grade_date: date = Field(..., description="Date of the grade")
    quarter: int = Field(..., ge=1, le=4, description="Quarter (1-4)")
    academic_year: str = Field(..., min_length=9, max_length=9, description="Academic year, e.g. 2025-2026")
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment")


class GradeUpdate(BaseModel):
    """Schema for updating an existing grade."""

    grade_value: Optional[int] = Field(None, ge=1, le=10, description="Grade value (1-10)")
    grade_type: Optional[GradeType] = Field(None, description="Grade type")
    grade_date: Optional[date] = Field(None, description="Date of the grade")
    quarter: Optional[int] = Field(None, ge=1, le=4, description="Quarter (1-4)")
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment")


class GradeResponse(BaseModel):
    """Schema for grade response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    school_id: int
    subject_id: int
    class_id: Optional[int] = None
    teacher_id: Optional[int] = None
    created_by: int
    grade_value: int
    grade_type: GradeType
    grade_date: date
    quarter: int
    academic_year: str
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class GradeWithDetailsResponse(BaseModel):
    """Grade response with student and subject names."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    school_id: int
    subject_id: int
    class_id: Optional[int] = None
    teacher_id: Optional[int] = None
    grade_value: int
    grade_type: GradeType
    grade_date: date
    quarter: int
    academic_year: str
    comment: Optional[str] = None
    created_at: datetime

    # Nested details
    student_name: Optional[str] = None
    subject_name: Optional[str] = None


class GradeFilterParams(BaseModel):
    """Filter parameters for grade queries."""

    subject_id: Optional[int] = None
    quarter: Optional[int] = Field(None, ge=1, le=4)
    academic_year: Optional[str] = None
    grade_type: Optional[GradeType] = None
