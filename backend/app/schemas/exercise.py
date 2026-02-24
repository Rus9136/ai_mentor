"""
Pydantic schemas for Exercise (structured textbook exercises).
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SubExercise(BaseModel):
    """Single sub-exercise (подпункт) within an exercise."""
    number: str = Field(..., description="Sub-exercise number (1, 2, 3...)")
    text: str = Field(..., description="Sub-exercise text/formula")
    answer: Optional[str] = Field(None, description="Answer for this sub-exercise")


class ExerciseResponse(BaseModel):
    """Exercise as seen by students (without answers)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    paragraph_id: int
    exercise_number: str
    sort_order: int
    difficulty: Optional[str] = None
    content_text: str
    content_html: Optional[str] = None
    sub_exercises: Optional[List[SubExercise]] = None
    is_starred: bool = False
    language: str = "kk"
    created_at: datetime


class ExerciseWithAnswerResponse(ExerciseResponse):
    """Exercise with answers (for teachers)."""
    answer_text: Optional[str] = None
    answer_html: Optional[str] = None
    has_answer: bool = False


class ExerciseListResponse(BaseModel):
    """List of exercises for a paragraph."""
    paragraph_id: int
    total: int
    count_a: int = 0
    count_b: int = 0
    count_c: int = 0
    exercises: List[ExerciseResponse] = []


class ExerciseListWithAnswersResponse(BaseModel):
    """List of exercises with answers (for teachers)."""
    paragraph_id: int
    total: int
    count_a: int = 0
    count_b: int = 0
    count_c: int = 0
    exercises: List[ExerciseWithAnswerResponse] = []


class ExerciseBrief(BaseModel):
    """Brief exercise info for embedding in HomeworkTask responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    exercise_number: str
    difficulty: Optional[str] = None
    content_text: str
    has_answer: bool = False
