"""
GOSO (State Educational Standard) models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Text, Date, Numeric, JSON
from sqlalchemy.orm import relationship

from app.models.base import SoftDeleteModel, BaseModel


class Framework(SoftDeleteModel):
    """Framework (версия ГОСО) model."""

    __tablename__ = "frameworks"

    code = Column(String(100), unique=True, nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    title_ru = Column(String(500), nullable=False)
    title_kz = Column(String(500), nullable=True)
    description_ru = Column(Text, nullable=True)
    description_kz = Column(Text, nullable=True)

    # Normative data
    document_type = Column(String(255), nullable=True)
    order_number = Column(String(50), nullable=True)
    order_date = Column(Date, nullable=True)
    ministry = Column(String(500), nullable=True)
    appendix_number = Column(Integer, nullable=True)
    amendments = Column(JSON, nullable=True)

    # Validity period
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    subject = relationship("Subject", back_populates="frameworks")
    sections = relationship("GosoSection", back_populates="framework", cascade="all, delete-orphan")
    outcomes = relationship("LearningOutcome", back_populates="framework", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Framework(id={self.id}, code='{self.code}')>"


class GosoSection(BaseModel):
    """GOSO Section (раздел) model."""

    __tablename__ = "goso_sections"

    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name_ru = Column(String(500), nullable=False)
    name_kz = Column(String(500), nullable=True)
    description_ru = Column(Text, nullable=True)
    description_kz = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    framework = relationship("Framework", back_populates="sections")
    subsections = relationship("GosoSubsection", back_populates="section", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GosoSection(id={self.id}, code='{self.code}', name='{self.name_ru}')>"


class GosoSubsection(BaseModel):
    """GOSO Subsection (подраздел) model."""

    __tablename__ = "goso_subsections"

    section_id = Column(Integer, ForeignKey("goso_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name_ru = Column(String(500), nullable=False)
    name_kz = Column(String(500), nullable=True)
    description_ru = Column(Text, nullable=True)
    description_kz = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    section = relationship("GosoSection", back_populates="subsections")
    outcomes = relationship("LearningOutcome", back_populates="subsection")

    def __repr__(self) -> str:
        return f"<GosoSubsection(id={self.id}, code='{self.code}', name='{self.name_ru}')>"


class LearningOutcome(SoftDeleteModel):
    """Learning Outcome (цель обучения ГОСО) model."""

    __tablename__ = "learning_outcomes"

    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False, index=True)
    subsection_id = Column(Integer, ForeignKey("goso_subsections.id", ondelete="CASCADE"), nullable=False, index=True)
    grade = Column(Integer, nullable=False, index=True)
    code = Column(String(20), nullable=False, index=True)
    title_ru = Column(Text, nullable=False)
    title_kz = Column(Text, nullable=True)
    description_ru = Column(Text, nullable=True)
    description_kz = Column(Text, nullable=True)
    cognitive_level = Column(String(50), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    framework = relationship("Framework", back_populates="outcomes")
    subsection = relationship("GosoSubsection", back_populates="outcomes")
    paragraph_links = relationship("ParagraphOutcome", back_populates="outcome", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<LearningOutcome(id={self.id}, code='{self.code}')>"


class ParagraphOutcome(BaseModel):
    """Paragraph-Outcome M:N link table."""

    __tablename__ = "paragraph_outcomes"

    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)
    outcome_id = Column(Integer, ForeignKey("learning_outcomes.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence = Column(Numeric(3, 2), default=1.0)
    anchor = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    paragraph = relationship("Paragraph", back_populates="outcome_links")
    outcome = relationship("LearningOutcome", back_populates="paragraph_links")
    creator = relationship("User")

    def __repr__(self) -> str:
        return f"<ParagraphOutcome(paragraph_id={self.paragraph_id}, outcome_id={self.outcome_id})>"
