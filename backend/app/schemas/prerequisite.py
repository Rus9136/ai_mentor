"""
Pydantic schemas for Knowledge Graph (Paragraph Prerequisites).
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Admin CRUD schemas
# =============================================================================

class PrerequisiteCreate(BaseModel):
    """Request to add a prerequisite to a paragraph."""

    prerequisite_paragraph_id: int = Field(..., description="ID of the prerequisite paragraph")
    strength: str = Field(
        default="required",
        pattern="^(required|recommended)$",
        description="'required' or 'recommended'",
    )


class PrerequisiteResponse(BaseModel):
    """A single prerequisite link (admin view)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    paragraph_id: int
    prerequisite_paragraph_id: int
    strength: str
    created_at: datetime

    # Enriched from prerequisite paragraph
    prerequisite_title: Optional[str] = None
    prerequisite_number: Optional[int] = None
    prerequisite_chapter_title: Optional[str] = None


# =============================================================================
# Textbook graph (admin visualization)
# =============================================================================

class PrerequisiteEdge(BaseModel):
    """An edge in the prerequisite graph."""

    id: int
    from_paragraph_id: int = Field(description="Prerequisite paragraph")
    to_paragraph_id: int = Field(description="Dependent paragraph")
    strength: str


class TextbookGraphResponse(BaseModel):
    """Full prerequisite graph for a textbook."""

    textbook_id: int
    edges: List[PrerequisiteEdge] = Field(default_factory=list)
    total_edges: int = 0


# =============================================================================
# Student prerequisite check
# =============================================================================

class PrerequisiteWarning(BaseModel):
    """Warning about an unmet prerequisite."""

    paragraph_id: int
    paragraph_title: Optional[str] = None
    paragraph_number: Optional[int] = None
    chapter_title: Optional[str] = None
    current_score: float = Field(0.0, description="Student's effective_score for the prerequisite")
    strength: str = Field(description="'required' or 'recommended'")
    recommendation: str = Field(description="'review_first' or 'consider_review'")


class PrerequisiteCheckResponse(BaseModel):
    """Result of checking prerequisites for a paragraph."""

    paragraph_id: int
    has_warnings: bool = False
    warnings: List[PrerequisiteWarning] = Field(default_factory=list)
    can_proceed: bool = Field(True, description="False if any 'required' prerequisite is unmet")


# =============================================================================
# Teacher analytics
# =============================================================================

class PrerequisiteAnalyticsItem(BaseModel):
    """Analytics for a single prerequisite in context of a class."""

    prerequisite_paragraph_id: int
    prerequisite_title: Optional[str] = None
    prerequisite_number: Optional[int] = None
    chapter_title: Optional[str] = None
    strength: str
    struggling_count: int = Field(0, description="Students with effective_score < 0.60")
    total_students: int = 0
    average_score: float = 0.0


class PrerequisiteAnalyticsResponse(BaseModel):
    """Teacher analytics: which prerequisites are students failing?"""

    paragraph_id: int
    paragraph_title: Optional[str] = None
    prerequisites: List[PrerequisiteAnalyticsItem] = Field(default_factory=list)
