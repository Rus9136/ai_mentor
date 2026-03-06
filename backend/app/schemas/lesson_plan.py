from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# --- REQUEST ---


class LessonPlanGenerateRequest(BaseModel):
    paragraph_id: int
    class_id: Optional[int] = None
    language: str = Field(default="kk", pattern="^(kk|ru)$")
    duration_min: int = Field(default=40, ge=40, le=80)


# --- RESPONSE ---


class TaskDescriptor(BaseModel):
    text: str
    score: int


class LessonTask(BaseModel):
    number: int
    teacher_activity: str
    student_activity: str
    descriptors: list[TaskDescriptor]
    total_score: int


class LessonStage(BaseModel):
    name: str
    name_detail: str
    duration_min: int
    method_name: str
    method_purpose: str
    method_effectiveness: str
    teacher_activity: str
    student_activity: str
    assessment: str
    differentiation: Optional[str] = None
    resources: str
    tasks: list[LessonTask] = []


class LessonPlanHeader(BaseModel):
    section: str
    topic: str
    learning_objective: str
    lesson_objective: str
    monthly_value: str
    value_decomposition: str


class DifferentiationBlock(BaseModel):
    approach: str
    for_level_a: str
    for_level_b: str
    for_level_c: str


class LessonPlanResponse(BaseModel):
    header: LessonPlanHeader
    stages: list[LessonStage]
    total_score: int
    differentiation: Optional[DifferentiationBlock] = None
    health_safety: str
    reflection_template: list[str]


class LessonPlanContext(BaseModel):
    paragraph_title: str
    chapter_title: str
    textbook_title: str
    subject: str
    grade_level: int
    mastery_distribution: Optional[dict] = None
    total_students: Optional[int] = None
    struggling_topics: Optional[list[str]] = None


class LessonPlanGenerateResponse(BaseModel):
    lesson_plan: LessonPlanResponse
    context: LessonPlanContext


# --- SAVE / CRUD ---


class LessonPlanSaveRequest(BaseModel):
    paragraph_id: int
    class_id: Optional[int] = None
    language: str = Field(default="kk", pattern="^(kk|ru)$")
    duration_min: int = Field(default=40, ge=40, le=80)
    title: Optional[str] = None
    plan_data: dict
    context_data: dict


class LessonPlanUpdateRequest(BaseModel):
    title: Optional[str] = None
    plan_data: Optional[dict] = None


class LessonPlanListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    language: str
    duration_min: int
    paragraph_id: int
    class_id: Optional[int] = None
    subject: Optional[str] = None
    grade_level: Optional[int] = None
    created_at: datetime


class LessonPlanFullResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    teacher_id: int
    school_id: int
    paragraph_id: int
    class_id: Optional[int] = None
    language: str
    duration_min: int
    plan_data: dict
    context_data: dict
    created_at: datetime
    updated_at: datetime
