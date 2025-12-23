"""
Pydantic schemas for GOSO (State Educational Standard).
"""
from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


# ==================== Subject ====================

class SubjectBrief(BaseModel):
    """Brief subject info for embedding in other responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_ru: str
    name_kz: str


class SubjectCreate(BaseModel):
    """Schema for creating a new subject."""

    code: str = Field(..., min_length=1, max_length=50, description="Subject code (e.g., 'history_kz')")
    name_ru: str = Field(..., min_length=1, max_length=255, description="Name in Russian")
    name_kz: str = Field(..., min_length=1, max_length=255, description="Name in Kazakh")
    description_ru: Optional[str] = Field(None, description="Description in Russian")
    description_kz: Optional[str] = Field(None, description="Description in Kazakh")
    grade_from: int = Field(default=1, ge=1, le=11, description="Starting grade")
    grade_to: int = Field(default=11, ge=1, le=11, description="Ending grade")
    is_active: bool = Field(default=True, description="Is subject active")


class SubjectUpdate(BaseModel):
    """Schema for updating a subject."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name_ru: Optional[str] = Field(None, min_length=1, max_length=255)
    name_kz: Optional[str] = Field(None, min_length=1, max_length=255)
    description_ru: Optional[str] = None
    description_kz: Optional[str] = None
    grade_from: Optional[int] = Field(None, ge=1, le=11)
    grade_to: Optional[int] = Field(None, ge=1, le=11)
    is_active: Optional[bool] = None


class SubjectResponse(BaseModel):
    """Schema for subject response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_ru: str
    name_kz: str
    description_ru: Optional[str]
    description_kz: Optional[str]
    grade_from: int
    grade_to: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SubjectListResponse(BaseModel):
    """Schema for subject list response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_ru: str
    name_kz: str
    grade_from: int
    grade_to: int
    is_active: bool


# ==================== Framework ====================

class FrameworkCreate(BaseModel):
    """Schema for creating a new framework."""

    code: str = Field(..., min_length=1, max_length=100, description="Framework code")
    subject_id: int = Field(..., description="Subject ID")
    title_ru: str = Field(..., min_length=1, max_length=500, description="Title in Russian")
    title_kz: Optional[str] = Field(None, max_length=500, description="Title in Kazakh")
    description_ru: Optional[str] = Field(None, description="Description in Russian")
    description_kz: Optional[str] = Field(None, description="Description in Kazakh")
    document_type: Optional[str] = Field(None, max_length=255)
    order_number: Optional[str] = Field(None, max_length=50)
    order_date: Optional[date] = None
    ministry: Optional[str] = Field(None, max_length=500)
    appendix_number: Optional[int] = None
    amendments: Optional[List[dict]] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: bool = Field(default=True)


class FrameworkUpdate(BaseModel):
    """Schema for updating a framework."""

    code: Optional[str] = Field(None, min_length=1, max_length=100)
    subject_id: Optional[int] = None
    title_ru: Optional[str] = Field(None, min_length=1, max_length=500)
    title_kz: Optional[str] = Field(None, max_length=500)
    description_ru: Optional[str] = None
    description_kz: Optional[str] = None
    document_type: Optional[str] = Field(None, max_length=255)
    order_number: Optional[str] = Field(None, max_length=50)
    order_date: Optional[date] = None
    ministry: Optional[str] = Field(None, max_length=500)
    appendix_number: Optional[int] = None
    amendments: Optional[List[dict]] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: Optional[bool] = None


class FrameworkResponse(BaseModel):
    """Schema for framework response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    subject_id: int
    title_ru: str
    title_kz: Optional[str]
    description_ru: Optional[str]
    description_kz: Optional[str]
    document_type: Optional[str]
    order_number: Optional[str]
    order_date: Optional[date]
    ministry: Optional[str]
    appendix_number: Optional[int]
    amendments: Optional[List[dict]]
    valid_from: Optional[date]
    valid_to: Optional[date]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    is_deleted: bool


class FrameworkListResponse(BaseModel):
    """Schema for framework list response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    subject_id: int
    title_ru: str
    title_kz: Optional[str]
    is_active: bool
    valid_from: Optional[date]
    valid_to: Optional[date]


# ==================== GosoSection ====================

class GosoSectionCreate(BaseModel):
    """Schema for creating a GOSO section."""

    framework_id: int = Field(..., description="Framework ID")
    code: str = Field(..., min_length=1, max_length=20, description="Section code (e.g., '1', '2')")
    name_ru: str = Field(..., min_length=1, max_length=500, description="Name in Russian")
    name_kz: Optional[str] = Field(None, max_length=500, description="Name in Kazakh")
    description_ru: Optional[str] = None
    description_kz: Optional[str] = None
    display_order: int = Field(default=0, description="Display order")
    is_active: bool = Field(default=True)


class GosoSectionUpdate(BaseModel):
    """Schema for updating a GOSO section."""

    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name_ru: Optional[str] = Field(None, min_length=1, max_length=500)
    name_kz: Optional[str] = Field(None, max_length=500)
    description_ru: Optional[str] = None
    description_kz: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class GosoSectionResponse(BaseModel):
    """Schema for GOSO section response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    framework_id: int
    code: str
    name_ru: str
    name_kz: Optional[str]
    description_ru: Optional[str]
    description_kz: Optional[str]
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GosoSectionListResponse(BaseModel):
    """Schema for GOSO section list response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    framework_id: int
    code: str
    name_ru: str
    name_kz: Optional[str]
    display_order: int
    is_active: bool


# ==================== GosoSubsection ====================

class GosoSubsectionCreate(BaseModel):
    """Schema for creating a GOSO subsection."""

    section_id: int = Field(..., description="Section ID")
    code: str = Field(..., min_length=1, max_length=20, description="Subsection code (e.g., '1.1', '2.1')")
    name_ru: str = Field(..., min_length=1, max_length=500, description="Name in Russian")
    name_kz: Optional[str] = Field(None, max_length=500, description="Name in Kazakh")
    description_ru: Optional[str] = None
    description_kz: Optional[str] = None
    display_order: int = Field(default=0, description="Display order")
    is_active: bool = Field(default=True)


class GosoSubsectionUpdate(BaseModel):
    """Schema for updating a GOSO subsection."""

    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name_ru: Optional[str] = Field(None, min_length=1, max_length=500)
    name_kz: Optional[str] = Field(None, max_length=500)
    description_ru: Optional[str] = None
    description_kz: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class GosoSubsectionResponse(BaseModel):
    """Schema for GOSO subsection response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    section_id: int
    code: str
    name_ru: str
    name_kz: Optional[str]
    description_ru: Optional[str]
    description_kz: Optional[str]
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GosoSubsectionListResponse(BaseModel):
    """Schema for GOSO subsection list response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    section_id: int
    code: str
    name_ru: str
    name_kz: Optional[str]
    display_order: int
    is_active: bool


# ==================== LearningOutcome ====================

class LearningOutcomeCreate(BaseModel):
    """Schema for creating a learning outcome."""

    framework_id: int = Field(..., description="Framework ID")
    subsection_id: int = Field(..., description="Subsection ID")
    grade: int = Field(..., ge=1, le=11, description="Grade level (1-11)")
    code: str = Field(..., min_length=1, max_length=20, description="Outcome code (e.g., '5.1.1.1')")
    title_ru: str = Field(..., min_length=1, description="Title in Russian")
    title_kz: Optional[str] = Field(None, description="Title in Kazakh")
    description_ru: Optional[str] = None
    description_kz: Optional[str] = None
    cognitive_level: Optional[str] = Field(None, max_length=50, description="Cognitive level")
    display_order: int = Field(default=0, description="Display order")
    is_active: bool = Field(default=True)


class LearningOutcomeUpdate(BaseModel):
    """Schema for updating a learning outcome."""

    subsection_id: Optional[int] = None
    grade: Optional[int] = Field(None, ge=1, le=11)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    title_ru: Optional[str] = Field(None, min_length=1)
    title_kz: Optional[str] = None
    description_ru: Optional[str] = None
    description_kz: Optional[str] = None
    cognitive_level: Optional[str] = Field(None, max_length=50)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class LearningOutcomeResponse(BaseModel):
    """Schema for learning outcome response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    framework_id: int
    subsection_id: int
    grade: int
    code: str
    title_ru: str
    title_kz: Optional[str]
    description_ru: Optional[str]
    description_kz: Optional[str]
    cognitive_level: Optional[str]
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    is_deleted: bool


class LearningOutcomeListResponse(BaseModel):
    """Schema for learning outcome list response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    framework_id: int
    subsection_id: int
    grade: int
    code: str
    title_ru: str
    title_kz: Optional[str]
    is_active: bool


# ==================== ParagraphOutcome ====================

class ParagraphOutcomeCreate(BaseModel):
    """Schema for creating a paragraph-outcome link."""

    paragraph_id: int = Field(..., description="Paragraph ID")
    outcome_id: int = Field(..., description="Learning outcome ID")
    confidence: Decimal = Field(default=Decimal("1.0"), ge=0, le=1, description="Confidence score (0-1)")
    anchor: Optional[str] = Field(None, max_length=100, description="Anchor in text")
    notes: Optional[str] = Field(None, description="Notes about the link")


class ParagraphOutcomeUpdate(BaseModel):
    """Schema for updating a paragraph-outcome link."""

    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    anchor: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class ParagraphOutcomeResponse(BaseModel):
    """Schema for paragraph-outcome link response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    paragraph_id: int
    outcome_id: int
    confidence: Decimal
    anchor: Optional[str]
    notes: Optional[str]
    created_by: Optional[int]
    created_at: datetime


class ParagraphOutcomeListResponse(BaseModel):
    """Schema for paragraph-outcome link list response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    paragraph_id: int
    outcome_id: int
    confidence: Decimal
    created_at: datetime


# ==================== Nested responses (for API convenience) ====================

class GosoSubsectionWithOutcomes(GosoSubsectionListResponse):
    """Subsection with nested learning outcomes."""

    outcomes: List[LearningOutcomeListResponse] = []


class GosoSectionWithSubsections(GosoSectionResponse):
    """Section with nested subsections."""

    subsections: List[GosoSubsectionListResponse] = []


class GosoSectionWithFullStructure(GosoSectionListResponse):
    """Section with nested subsections and outcomes (full structure)."""

    subsections: List[GosoSubsectionWithOutcomes] = []


class FrameworkWithSections(FrameworkResponse):
    """Framework with nested sections."""

    sections: List[GosoSectionListResponse] = []


class FrameworkWithFullStructure(FrameworkResponse):
    """Framework with full nested structure (sections -> subsections -> outcomes)."""

    sections: List[GosoSectionWithFullStructure] = []


class LearningOutcomeWithContext(LearningOutcomeResponse):
    """Learning outcome with section/subsection context."""

    section_code: Optional[str] = None
    section_name_ru: Optional[str] = None
    subsection_code: Optional[str] = None
    subsection_name_ru: Optional[str] = None


class ParagraphOutcomeWithDetails(ParagraphOutcomeResponse):
    """Paragraph-outcome link with outcome details."""

    outcome_code: Optional[str] = None
    outcome_title_ru: Optional[str] = None
    outcome_grade: Optional[int] = None
