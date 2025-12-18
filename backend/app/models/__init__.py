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
from app.models.parent import Parent, parent_students
from app.models.school_class import SchoolClass, class_students, class_teachers

# Content models
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph, ParagraphEmbedding
from app.models.paragraph_content import ParagraphContent, ContentStatus
from app.models.test import Test, Question, QuestionOption, DifficultyLevel, QuestionType, TestPurpose

# GOSO models
from app.models.subject import Subject
from app.models.goso import Framework, GosoSection, GosoSubsection, LearningOutcome, ParagraphOutcome

# Progress tracking models
from app.models.test_attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.models.mastery import MasteryHistory, AdaptiveGroup, ParagraphMastery, ChapterMastery

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
    "Parent",
    "parent_students",
    "SchoolClass",
    "class_students",
    "class_teachers",
    # Content
    "Textbook",
    "Chapter",
    "Paragraph",
    "ParagraphEmbedding",
    "ParagraphContent",
    "ContentStatus",
    "Test",
    "Question",
    "QuestionOption",
    "DifficultyLevel",
    "QuestionType",
    "TestPurpose",
    # GOSO
    "Subject",
    "Framework",
    "GosoSection",
    "GosoSubsection",
    "LearningOutcome",
    "ParagraphOutcome",
    # Progress
    "TestAttempt",
    "TestAttemptAnswer",
    "AttemptStatus",
    "MasteryHistory",
    "AdaptiveGroup",
    "ParagraphMastery",
    "ChapterMastery",
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
