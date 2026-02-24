"""
Student API Router Package.

This package contains all student-facing API endpoints organized by domain:
- tests.py: Test-taking workflow (start test, submit answers, view attempts)
- content.py: Content browsing (textbooks, chapters, paragraphs)
- learning.py: Learning progress (step tracking, self-assessment)
- mastery.py: Mastery levels (A/B/C grading per chapter)
- embedded.py: Embedded questions (check yourself questions)
- stats.py: Dashboard statistics (streak, progress)
- homework.py: Homework assignments (view, submit, feedback)

The router is exported as a single aggregated router that can be included
in the main app with the same import path as before:

    from app.api.v1.students import router as students_router
"""

from fastapi import APIRouter

from .tests import router as tests_router
from .content import router as content_router
from .learning import router as learning_router
from .mastery import router as mastery_router
from .embedded import router as embedded_router
from .stats import router as stats_router
from .homework import router as homework_router
from .profile import router as profile_router
from .exercises import router as exercises_router


router = APIRouter()

# Test-taking workflow
router.include_router(tests_router, tags=["Student Tests"])

# Content browsing (textbooks, chapters, paragraphs)
router.include_router(content_router, tags=["Student Content"])

# Learning progress (steps, self-assessment)
router.include_router(learning_router, tags=["Student Learning"])

# Mastery levels (A/B/C)
router.include_router(mastery_router, tags=["Student Mastery"])

# Embedded questions
router.include_router(embedded_router, tags=["Embedded Questions"])

# Dashboard stats
router.include_router(stats_router, tags=["Student Stats"])

# Homework assignments
router.include_router(homework_router, tags=["Student Homework"])

# Profile
router.include_router(profile_router, tags=["Student Profile"])

# Exercises (textbook exercises)
router.include_router(exercises_router, tags=["Student Exercises"])
