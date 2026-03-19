"""
Lab schemas — request/response models for lab API.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# --- Response schemas ---

class LabResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    textbook_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    lab_type: str
    config: dict = {}
    is_active: bool = True
    thumbnail_url: Optional[str] = None


class LabProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    progress_data: dict = {}
    xp_earned: int = 0
    completed_at: Optional[datetime] = None


class LabTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    title: str
    task_type: str
    task_data: dict = {}
    xp_reward: int = 10
    order_index: int = 0


class LabTaskAnswerResult(BaseModel):
    is_correct: bool
    explanation: Optional[str] = None
    xp_earned: int = 0


# --- Request schemas ---

class ProgressUpdateRequest(BaseModel):
    progress_data: dict = {}


class TaskAnswerRequest(BaseModel):
    answer_data: dict = {}
