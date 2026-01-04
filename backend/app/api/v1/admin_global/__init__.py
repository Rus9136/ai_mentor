"""
Global Admin API Router Package.

This package contains all global admin-facing API endpoints for SUPER_ADMIN,
organized by domain:
- textbooks.py: Global Textbook CRUD
- chapters.py: Global Chapter CRUD
- paragraphs.py: Global Paragraph CRUD
- tests.py: Global Test CRUD
- questions.py: Global Question CRUD
- question_options.py: Global QuestionOption CRUD
- goso.py: Paragraph Outcomes (GOSO mapping)

The router is exported as a single aggregated router that can be included
in the main app with the same import path as before:

    from app.api.v1.admin_global import router as admin_global_router
"""

from fastapi import APIRouter

from .textbooks import router as textbooks_router
from .chapters import router as chapters_router
from .paragraphs import router as paragraphs_router
from .tests import router as tests_router
from .questions import router as questions_router
from .question_options import router as question_options_router
from .goso import router as goso_router


router = APIRouter()

# Content Management
router.include_router(textbooks_router)
router.include_router(chapters_router)
router.include_router(paragraphs_router)

# Test Management
router.include_router(tests_router)
router.include_router(questions_router)
router.include_router(question_options_router)

# GOSO Mapping
router.include_router(goso_router)
