"""
Pydantic schemas for SchoolClass management.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
import re


class SchoolClassCreate(BaseModel):
    """Schema for creating a new school class."""

    name: str = Field(..., min_length=1, max_length=100, description="Class name (e.g., '7А')")
    code: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Class code (unique within school, e.g., '7a-2024')",
    )
    grade_level: int = Field(..., ge=1, le=11, description="Grade level (1-11)")
    academic_year: str = Field(
        ...,
        min_length=7,
        max_length=20,
        description="Academic year (e.g., '2024-2025')",
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate that code contains only uppercase alphanumeric characters, dashes, and underscores."""
        if not re.match(r"^[A-Z0-9_-]+$", v):
            raise ValueError(
                "Code must contain only uppercase letters, numbers, dashes, and underscores"
            )
        return v


class SchoolClassUpdate(BaseModel):
    """Schema for updating an existing school class."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Class name")
    grade_level: Optional[int] = Field(None, ge=1, le=11, description="Grade level (1-11)")
    academic_year: Optional[str] = Field(
        None,
        min_length=7,
        max_length=20,
        description="Academic year (e.g., '2024-2025')",
    )
    # Note: code is NOT updatable


class AddStudentsRequest(BaseModel):
    """Schema for adding students to class."""

    student_ids: List[int] = Field(..., description="List of student IDs to add to class")


class AddTeachersRequest(BaseModel):
    """Schema for adding teachers to class."""

    teacher_ids: List[int] = Field(..., description="List of teacher IDs to add to class")


class SchoolClassResponse(BaseModel):
    """Schema for school class response (detailed)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    name: str
    code: str
    grade_level: int
    academic_year: str
    created_at: datetime
    updated_at: datetime

    # Nested data (optional, loaded when needed)
    students: Optional[List["StudentListResponse"]] = None
    teachers: Optional[List["TeacherListResponse"]] = None

    # Computed fields (calculated from nested data)
    @computed_field
    @property
    def students_count(self) -> int:
        """Calculate students count from nested data."""
        return len(self.students) if self.students else 0

    @computed_field
    @property
    def teachers_count(self) -> int:
        """Calculate teachers count from nested data."""
        return len(self.teachers) if self.teachers else 0


class SchoolClassListResponse(BaseModel):
    """Schema for school class list response (brief)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    grade_level: int
    academic_year: str
    students_count: Optional[int] = 0
    teachers_count: Optional[int] = 0
    created_at: datetime


# Import after class definition to avoid circular import
from app.schemas.student import StudentListResponse
from app.schemas.teacher import TeacherListResponse

SchoolClassResponse.model_rebuild()
