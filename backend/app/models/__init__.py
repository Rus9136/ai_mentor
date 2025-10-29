"""
Models package.

Import all models here so Alembic can detect them.
"""
from app.models.base import BaseModel, SoftDeleteModel

# Core models
from app.models.school import School
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.school_class import SchoolClass, class_students, class_teachers

# Content models
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph, ParagraphEmbedding
from app.models.test import Test, Question, QuestionOption, DifficultyLevel, QuestionType

# Progress tracking models
from app.models.test_attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.models.mastery import MasteryHistory, AdaptiveGroup

# Assignment models
from app.models.assignment import Assignment, AssignmentTest, StudentAssignment, AssignmentStatus

# Learning models
from app.models.learning import StudentParagraph, LearningSession, LearningActivity, ActivityType

# Analytics models
from app.models.analytics import AnalyticsEvent

# Sync models
from app.models.sync import SyncQueue, SyncStatus

# Settings models
from app.models.settings import SystemSetting

__all__ = [
    # Base
    "BaseModel",
    "SoftDeleteModel",
    # Core
    "School",
    "User",
    "UserRole",
    "Student",
    "Teacher",
    "SchoolClass",
    "class_students",
    "class_teachers",
    # Content
    "Textbook",
    "Chapter",
    "Paragraph",
    "ParagraphEmbedding",
    "Test",
    "Question",
    "QuestionOption",
    "DifficultyLevel",
    "QuestionType",
    # Progress
    "TestAttempt",
    "TestAttemptAnswer",
    "AttemptStatus",
    "MasteryHistory",
    "AdaptiveGroup",
    # Assignment
    "Assignment",
    "AssignmentTest",
    "StudentAssignment",
    "AssignmentStatus",
    # Learning
    "StudentParagraph",
    "LearningSession",
    "LearningActivity",
    "ActivityType",
    # Analytics
    "AnalyticsEvent",
    # Sync
    "SyncQueue",
    "SyncStatus",
    # Settings
    "SystemSetting",
]
