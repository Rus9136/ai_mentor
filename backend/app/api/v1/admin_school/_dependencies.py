"""
Reusable dependencies for School Admin API.

These dependencies encapsulate common access checks to eliminate code duplication
across admin_school endpoints. Each dependency handles:
1. Entity existence check (404 if not found)
2. School ownership verification (403 if wrong school)
3. Global vs school content distinction (403 for write ops on global)
"""

from typing import Tuple
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user_school_id
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.test import Test, Question, QuestionOption
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.parent import Parent
from app.models.school_class import SchoolClass
from app.models.user import User

from app.api.v1.admin_school._dependency_factories import (
    create_entity_dependency,
    create_content_dependency,
    create_hierarchical_dependency,
)


# =============================================================================
# User Management Dependencies
# =============================================================================

get_user_for_school_admin = create_entity_dependency(
    entity_name="User",
    repo_class_path="app.repositories.user_repo.UserRepository",
    repo_method="get_by_id"
)

get_student_for_school_admin = create_entity_dependency(
    entity_name="Student",
    repo_class_path="app.repositories.student_repo.StudentRepository",
    repo_method="get_by_id",
    extra_kwargs={"load_user": True, "load_classes": True}
)

get_teacher_for_school_admin = create_entity_dependency(
    entity_name="Teacher",
    repo_class_path="app.repositories.teacher_repo.TeacherRepository",
    repo_method="get_by_id",
    extra_kwargs={"load_user": True, "load_classes": True}
)

get_parent_for_school_admin = create_entity_dependency(
    entity_name="Parent",
    repo_class_path="app.repositories.parent_repo.ParentRepository",
    repo_method="get_by_id",
    extra_kwargs={"load_user": True, "load_children": True}
)

get_class_for_school_admin = create_entity_dependency(
    entity_name="Class",
    repo_class_path="app.repositories.school_class_repo.SchoolClassRepository",
    repo_method="get_by_id",
    id_param_name="class_id",
    extra_kwargs={"load_students": True, "load_teachers": True}
)


# =============================================================================
# Content Access Dependencies (Textbook/Test - with read/write variants)
# =============================================================================

# Textbook - Read (allows global)
get_textbook_for_school_admin = create_content_dependency(
    entity_name="Textbook",
    repo_class_path="app.repositories.textbook_repo.TextbookRepository",
    write_mode=False
)

# Textbook - Write (rejects global)
require_school_textbook = create_content_dependency(
    entity_name="Textbook",
    repo_class_path="app.repositories.textbook_repo.TextbookRepository",
    write_mode=True
)

# Test - Read (allows global)
get_test_for_school_admin = create_content_dependency(
    entity_name="Test",
    repo_class_path="app.repositories.test_repo.TestRepository",
    repo_method="get_by_id",
    extra_kwargs={"load_questions": False},
    write_mode=False
)

# Test - Write (rejects global)
require_school_test = create_content_dependency(
    entity_name="Test",
    repo_class_path="app.repositories.test_repo.TestRepository",
    repo_method="get_by_id",
    extra_kwargs={"load_questions": False},
    write_mode=True
)


# =============================================================================
# Hierarchical Dependencies (Textbook hierarchy)
# =============================================================================

# Chapter -> Textbook (Read)
get_chapter_for_school_admin = create_hierarchical_dependency(
    entity_name="Chapter",
    entity_repo_path="app.repositories.chapter_repo.ChapterRepository",
    parent_chain=[
        ("textbook", "app.repositories.textbook_repo.TextbookRepository", "textbook_id")
    ],
    write_mode=False
)

# Chapter -> Textbook (Write) - Returns tuple
require_school_chapter = create_hierarchical_dependency(
    entity_name="Chapter",
    entity_repo_path="app.repositories.chapter_repo.ChapterRepository",
    parent_chain=[
        ("textbook", "app.repositories.textbook_repo.TextbookRepository", "textbook_id")
    ],
    write_mode=True,
    return_chain=True
)

# Paragraph -> Chapter -> Textbook (Read)
get_paragraph_for_school_admin = create_hierarchical_dependency(
    entity_name="Paragraph",
    entity_repo_path="app.repositories.paragraph_repo.ParagraphRepository",
    parent_chain=[
        ("chapter", "app.repositories.chapter_repo.ChapterRepository", "chapter_id"),
        ("textbook", "app.repositories.textbook_repo.TextbookRepository", "textbook_id")
    ],
    write_mode=False
)

# Paragraph -> Chapter -> Textbook (Write) - Returns tuple
require_school_paragraph = create_hierarchical_dependency(
    entity_name="Paragraph",
    entity_repo_path="app.repositories.paragraph_repo.ParagraphRepository",
    parent_chain=[
        ("chapter", "app.repositories.chapter_repo.ChapterRepository", "chapter_id"),
        ("textbook", "app.repositories.textbook_repo.TextbookRepository", "textbook_id")
    ],
    write_mode=True,
    return_chain=True
)


# =============================================================================
# Hierarchical Dependencies (Test hierarchy)
# =============================================================================

# Question -> Test (Read)
get_question_for_school_admin = create_hierarchical_dependency(
    entity_name="Question",
    entity_repo_path="app.repositories.question_repo.QuestionRepository",
    parent_chain=[
        ("test", "app.repositories.test_repo.TestRepository", "test_id")
    ],
    write_mode=False
)

# Question -> Test (Write) - Returns tuple
require_school_question = create_hierarchical_dependency(
    entity_name="Question",
    entity_repo_path="app.repositories.question_repo.QuestionRepository",
    parent_chain=[
        ("test", "app.repositories.test_repo.TestRepository", "test_id")
    ],
    write_mode=True,
    return_chain=True
)

# Option -> Question -> Test (Read)
get_option_for_school_admin = create_hierarchical_dependency(
    entity_name="Option",
    entity_repo_path="app.repositories.question_repo.QuestionOptionRepository",
    parent_chain=[
        ("question", "app.repositories.question_repo.QuestionRepository", "question_id"),
        ("test", "app.repositories.test_repo.TestRepository", "test_id")
    ],
    write_mode=False
)

# Option -> Question -> Test (Write) - Returns tuple
require_school_option = create_hierarchical_dependency(
    entity_name="Option",
    entity_repo_path="app.repositories.question_repo.QuestionOptionRepository",
    parent_chain=[
        ("question", "app.repositories.question_repo.QuestionRepository", "question_id"),
        ("test", "app.repositories.test_repo.TestRepository", "test_id")
    ],
    write_mode=True,
    return_chain=True
)
