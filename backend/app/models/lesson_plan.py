"""
Lesson Plan model for storing generated QMJ plans.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class LessonPlan(BaseModel):
    __tablename__ = "lesson_plans"

    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("school_classes.id", ondelete="SET NULL"), nullable=True)
    language = Column(String(2), nullable=False, default="kk")
    duration_min = Column(Integer, nullable=False, default=40)
    title = Column(String(500), nullable=False)
    plan_data = Column(JSONB, nullable=False)
    context_data = Column(JSONB, nullable=False)

    teacher = relationship("Teacher", lazy="selectin")
    paragraph = relationship("Paragraph", lazy="selectin")
