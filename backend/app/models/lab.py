"""
Lab models — interactive laboratory experiments.

Tables:
- labs: Lab definitions (map, molecule_3d, simulation, anatomy)
- lab_progress: Student progress in labs
- lab_tasks: Interactive tasks within labs
- lab_task_answers: Student answers to lab tasks
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Lab(BaseModel):
    __tablename__ = "labs"

    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    textbook_id = Column(Integer, ForeignKey("textbooks.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    lab_type = Column(String(50), nullable=False)  # 'map', 'molecule_3d', 'simulation', 'anatomy'
    config = Column(JSONB, nullable=False, server_default='{}')
    content_path = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default='true')
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)

    # Relationships
    tasks = relationship("LabTask", back_populates="lab", cascade="all, delete-orphan")
    progress = relationship("LabProgress", back_populates="lab", cascade="all, delete-orphan")


class LabProgress(BaseModel):
    __tablename__ = "lab_progress"

    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    progress_data = Column(JSONB, nullable=False, server_default='{}')
    xp_earned = Column(Integer, nullable=False, default=0, server_default='0')
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    lab = relationship("Lab", back_populates="progress")


class LabTask(BaseModel):
    __tablename__ = "lab_tasks"

    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    task_type = Column(String(50), nullable=False)  # 'find_on_map', 'order_events', 'choose_epoch', 'quiz'
    task_data = Column(JSONB, nullable=False, server_default='{}')
    xp_reward = Column(Integer, nullable=False, default=10, server_default='10')
    order_index = Column(Integer, nullable=False, default=0, server_default='0')
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    lab = relationship("Lab", back_populates="tasks")
    answers = relationship("LabTaskAnswer", back_populates="task", cascade="all, delete-orphan")


class LabTaskAnswer(BaseModel):
    __tablename__ = "lab_task_answers"

    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    lab_task_id = Column(Integer, ForeignKey("lab_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_data = Column(JSONB, nullable=False, server_default='{}')
    is_correct = Column(Boolean, nullable=False)
    xp_earned = Column(Integer, nullable=False, default=0, server_default='0')
    answered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    task = relationship("LabTask", back_populates="answers")
