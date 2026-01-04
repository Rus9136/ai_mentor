"""
School Admin API Router Package.

This package contains all school admin-facing API endpoints organized by domain:
- textbooks.py: Textbook CRUD
- chapters.py: Chapter CRUD
- paragraphs.py: Paragraph CRUD
- tests.py: Test CRUD
- questions.py: Question CRUD
- question_options.py: QuestionOption CRUD
- users.py: User management
- students.py: Student CRUD
- teachers.py: Teacher CRUD
- parents.py: Parent CRUD
- classes.py: SchoolClass CRUD
- class_members.py: Class membership (students, teachers)
- settings.py: School settings
- paragraph_outcomes.py: GOSO mapping

The router is exported as a single aggregated router that can be included
in the main app with the same import path as before:

    from app.api.v1.admin_school import router as admin_school_router
"""

from fastapi import APIRouter

from .textbooks import router as textbooks_router
from .chapters import router as chapters_router
from .paragraphs import router as paragraphs_router
from .tests import router as tests_router
from .questions import router as questions_router
from .question_options import router as question_options_router
from .users import router as users_router
from .students import router as students_router
from .teachers import router as teachers_router
from .parents import router as parents_router
from .classes import router as classes_router
from .class_members import router as class_members_router
from .settings import router as settings_router
from .paragraph_outcomes import router as paragraph_outcomes_router


router = APIRouter()

# Content Management
router.include_router(textbooks_router)
router.include_router(chapters_router)
router.include_router(paragraphs_router)

# Test Management
router.include_router(tests_router)
router.include_router(questions_router)
router.include_router(question_options_router)

# User Management
router.include_router(users_router)
router.include_router(students_router)
router.include_router(teachers_router)
router.include_router(parents_router)

# Class Management
router.include_router(classes_router)
router.include_router(class_members_router)

# Settings & GOSO
router.include_router(settings_router)
router.include_router(paragraph_outcomes_router)
