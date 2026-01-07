"""
Tests for Teachers API endpoints.

Covers:
- Dashboard (GET /teachers/dashboard)
- Classes list and detail (GET /teachers/classes, GET /teachers/classes/{id})
- Class analytics (overview, mastery distribution)
- Student progress tracking
- Analytics (struggling topics, mastery trends)
- Content browse (textbooks, chapters, paragraphs)
- Authorization checks (requires TEACHER role)
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.user import User, UserRole
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.schemas.teacher_dashboard import (
    MasteryDistribution,
    TeacherDashboardResponse,
    TeacherClassResponse,
    TeacherClassDetailResponse,
    ClassOverviewResponse,
    StudentProgressDetailResponse,
    MasteryHistoryResponse,
    StrugglingTopicResponse,
    MasteryTrendsResponse,
    StudentWithMastery,
    StudentBriefResponse,
    ChapterProgressBrief,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_teacher_user():
    """Create a mock teacher user."""
    user = MagicMock(spec=User)
    user.id = 10
    user.email = "teacher@test.com"
    user.role = UserRole.TEACHER
    user.school_id = 5
    user.is_active = True
    return user


@pytest.fixture
def mock_student_user():
    """Create a mock student user (for unauthorized tests)."""
    user = MagicMock(spec=User)
    user.id = 20
    user.email = "student@test.com"
    user.role = UserRole.STUDENT
    user.school_id = 5
    user.is_active = True
    return user


@pytest.fixture
def sample_mastery_distribution():
    """Create sample mastery distribution."""
    return MasteryDistribution(
        level_a=5,
        level_b=10,
        level_c=3,
        not_started=2
    )


@pytest.fixture
def sample_dashboard_response(sample_mastery_distribution):
    """Create sample dashboard response."""
    return TeacherDashboardResponse(
        classes_count=3,
        total_students=20,
        students_by_level=sample_mastery_distribution,
        average_class_score=72.5,
        students_needing_help=3,
        recent_activity=[]
    )


@pytest.fixture
def sample_class_response(sample_mastery_distribution):
    """Create sample class response."""
    return TeacherClassResponse(
        id=1,
        name="7A",
        code="7A-2024",
        grade_level=7,
        academic_year="2024-2025",
        students_count=25,
        mastery_distribution=sample_mastery_distribution,
        average_score=75.0,
        progress_percentage=60
    )


@pytest.fixture
def sample_class_detail_response(sample_mastery_distribution):
    """Create sample class detail response."""
    students = [
        StudentWithMastery(
            id=1,
            student_code="STU001",
            first_name="Иван",
            last_name="Иванов",
            mastery_level="A",
            mastery_score=90.0,
            completed_paragraphs=20,
            total_paragraphs=25,
            progress_percentage=80
        ),
        StudentWithMastery(
            id=2,
            student_code="STU002",
            first_name="Мария",
            last_name="Петрова",
            mastery_level="B",
            mastery_score=72.0,
            completed_paragraphs=15,
            total_paragraphs=25,
            progress_percentage=60
        )
    ]
    return TeacherClassDetailResponse(
        id=1,
        name="7A",
        code="7A-2024",
        grade_level=7,
        academic_year="2024-2025",
        students_count=2,
        mastery_distribution=sample_mastery_distribution,
        average_score=81.0,
        progress_percentage=70,
        students=students
    )


@pytest.fixture
def sample_class_overview_response(sample_class_response):
    """Create sample class overview response."""
    chapters_progress = [
        ChapterProgressBrief(
            chapter_id=1,
            chapter_title="Введение",
            chapter_number=1,
            mastery_level="A",
            mastery_score=85.0,
            completed_paragraphs=10,
            total_paragraphs=10,
            progress_percentage=100
        ),
        ChapterProgressBrief(
            chapter_id=2,
            chapter_title="Основы",
            chapter_number=2,
            mastery_level="B",
            mastery_score=70.0,
            completed_paragraphs=8,
            total_paragraphs=12,
            progress_percentage=67
        )
    ]
    return ClassOverviewResponse(
        class_info=sample_class_response,
        chapters_progress=chapters_progress,
        trend="improving",
        trend_percentage=5.5
    )


@pytest.fixture
def sample_student_progress():
    """Create sample student progress response."""
    return StudentProgressDetailResponse(
        student=StudentBriefResponse(
            id=1,
            student_code="STU001",
            grade_level=7,
            first_name="Иван",
            last_name="Иванов"
        ),
        class_name="7A",
        overall_mastery_level="B",
        overall_mastery_score=75.0,
        total_time_spent=3600,
        chapters_progress=[],
        recent_tests=[],
        days_since_last_activity=1
    )


@pytest.fixture
def sample_mastery_history():
    """Create sample mastery history response."""
    return MasteryHistoryResponse(
        student_id=1,
        student_name="Иван Иванов",
        history=[]
    )


@pytest.fixture
def sample_struggling_topics():
    """Create sample struggling topics."""
    return [
        StrugglingTopicResponse(
            paragraph_id=10,
            paragraph_title="Сложная тема",
            chapter_id=2,
            chapter_title="Глава 2",
            struggling_count=8,
            total_students=20,
            struggling_percentage=40.0,
            average_score=45.0
        )
    ]


@pytest.fixture
def sample_mastery_trends():
    """Create sample mastery trends response."""
    return MasteryTrendsResponse(
        period="weekly",
        start_date=date.today() - timedelta(days=7),
        end_date=date.today(),
        overall_trend="improving",
        overall_change_percentage=3.5,
        class_trends=[]
    )


# =============================================================================
# Dashboard Tests
# =============================================================================

class TestDashboard:
    """Tests for GET /teachers/dashboard endpoint."""

    @pytest.mark.asyncio
    async def test_get_dashboard_success(
        self,
        mock_teacher_user,
        sample_dashboard_response
    ):
        """Test successful dashboard retrieval."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_dashboard.return_value = sample_dashboard_response
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/dashboard",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["classes_count"] == 3
            assert data["total_students"] == 20
            assert data["students_by_level"]["level_a"] == 5

    @pytest.mark.asyncio
    async def test_get_dashboard_no_classes(self, mock_teacher_user):
        """Test dashboard when teacher has no classes."""
        empty_dashboard = TeacherDashboardResponse(
            classes_count=0,
            total_students=0,
            students_by_level=MasteryDistribution()
        )

        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_dashboard.return_value = empty_dashboard
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/dashboard",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["classes_count"] == 0
            assert data["total_students"] == 0


# =============================================================================
# Classes Tests
# =============================================================================

class TestClasses:
    """Tests for classes endpoints."""

    @pytest.mark.asyncio
    async def test_get_classes_success(
        self,
        mock_teacher_user,
        sample_class_response
    ):
        """Test successful classes list retrieval."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_classes.return_value = [sample_class_response]
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/classes",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "7A"
            assert data[0]["students_count"] == 25

    @pytest.mark.asyncio
    async def test_get_classes_empty(self, mock_teacher_user):
        """Test classes list when teacher has no classes."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_classes.return_value = []
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/classes",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_class_detail_success(
        self,
        mock_teacher_user,
        sample_class_detail_response
    ):
        """Test successful class detail retrieval."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_class_detail.return_value = sample_class_detail_response
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/classes/1",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "7A"
            assert len(data["students"]) == 2

    @pytest.mark.asyncio
    async def test_get_class_detail_not_found(self, mock_teacher_user):
        """Test class detail when class not found."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_class_detail.return_value = None
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/classes/999",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_class_overview_success(
        self,
        mock_teacher_user,
        sample_class_overview_response
    ):
        """Test successful class overview retrieval."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_class_overview.return_value = sample_class_overview_response
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/classes/1/overview",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["trend"] == "improving"
            assert len(data["chapters_progress"]) == 2

    @pytest.mark.asyncio
    async def test_get_class_overview_not_found(self, mock_teacher_user):
        """Test class overview when class not found."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_class_overview.return_value = None
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/classes/999/overview",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_mastery_distribution_success(
        self,
        mock_teacher_user,
        sample_class_detail_response
    ):
        """Test successful mastery distribution retrieval."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_class_detail.return_value = sample_class_detail_response
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/classes/1/mastery-distribution",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["class_id"] == 1
            assert "distribution" in data

    @pytest.mark.asyncio
    async def test_get_mastery_distribution_with_chapter_filter(
        self,
        mock_teacher_user,
        sample_class_detail_response
    ):
        """Test mastery distribution with chapter filter."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_class_detail.return_value = sample_class_detail_response
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/classes/1/mastery-distribution?chapter_id=5",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["chapter_id"] == 5


# =============================================================================
# Student Progress Tests
# =============================================================================

class TestStudentProgress:
    """Tests for student progress endpoints."""

    @pytest.mark.asyncio
    async def test_get_student_progress_success(
        self,
        mock_teacher_user,
        sample_student_progress
    ):
        """Test successful student progress retrieval."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_student_progress.return_value = sample_student_progress
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/classes/1/students/1/progress",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["overall_mastery_level"] == "B"
            assert data["student"]["first_name"] == "Иван"

    @pytest.mark.asyncio
    async def test_get_student_progress_not_found(self, mock_teacher_user):
        """Test student progress when student not found."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_student_progress.return_value = None
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/classes/1/students/999/progress",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_mastery_history_success(
        self,
        mock_teacher_user,
        sample_mastery_history
    ):
        """Test successful mastery history retrieval."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_mastery_history.return_value = sample_mastery_history
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/students/1/mastery-history",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["student_id"] == 1
            assert data["student_name"] == "Иван Иванов"

    @pytest.mark.asyncio
    async def test_get_mastery_history_not_found(self, mock_teacher_user):
        """Test mastery history when student not found."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_mastery_history.return_value = None
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/students/999/mastery-history",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 404


# =============================================================================
# Analytics Tests
# =============================================================================

class TestAnalytics:
    """Tests for analytics endpoints."""

    @pytest.mark.asyncio
    async def test_get_struggling_topics_success(
        self,
        mock_teacher_user,
        sample_struggling_topics
    ):
        """Test successful struggling topics retrieval."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_struggling_topics.return_value = sample_struggling_topics
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/analytics/struggling-topics",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["paragraph_title"] == "Сложная тема"
            assert data[0]["struggling_percentage"] == 40.0

    @pytest.mark.asyncio
    async def test_get_struggling_topics_empty(self, mock_teacher_user):
        """Test struggling topics when none found."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_struggling_topics.return_value = []
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/analytics/struggling-topics",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_mastery_trends_weekly(
        self,
        mock_teacher_user,
        sample_mastery_trends
    ):
        """Test mastery trends with weekly period."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_mastery_trends.return_value = sample_mastery_trends
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/analytics/mastery-trends?period=weekly",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "weekly"
            assert data["overall_trend"] == "improving"

    @pytest.mark.asyncio
    async def test_get_mastery_trends_monthly(
        self,
        mock_teacher_user,
        sample_mastery_trends
    ):
        """Test mastery trends with monthly period."""
        sample_mastery_trends.period = "monthly"

        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_mastery_trends.return_value = sample_mastery_trends
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/analytics/mastery-trends?period=monthly",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "monthly"

    @pytest.mark.asyncio
    async def test_get_mastery_trends_default_period(
        self,
        mock_teacher_user,
        sample_mastery_trends
    ):
        """Test mastery trends with default period (weekly)."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TeacherAnalyticsService") as mock_service_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_mastery_trends.return_value = sample_mastery_trends
            mock_service_class.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/analytics/mastery-trends",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            # Default should be weekly
            mock_service.get_mastery_trends.assert_called_once()


# =============================================================================
# Content Browse Tests
# =============================================================================

class TestContentBrowse:
    """Tests for content browse endpoints."""

    @pytest.mark.asyncio
    async def test_list_textbooks_success(self, mock_teacher_user):
        """Test listing textbooks for teacher."""
        mock_textbooks = [
            MagicMock(
                id=1,
                title="Алгебра 7",
                subject="Математика",
                grade_level=7,
                language="ru",
                school_id=None  # Global
            )
        ]

        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TextbookRepository") as mock_repo_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_repo = AsyncMock()
            mock_repo.get_by_school.return_value = mock_textbooks
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/textbooks",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            mock_repo.get_by_school.assert_called_once_with(5, include_global=True)

    @pytest.mark.asyncio
    async def test_list_chapters_success(self, mock_teacher_user):
        """Test listing chapters for a textbook."""
        mock_textbook = MagicMock(id=1, school_id=None)  # Global textbook
        mock_chapters = [
            MagicMock(
                id=1,
                textbook_id=1,
                number=1,
                title="Глава 1"
            )
        ]

        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TextbookRepository") as mock_tb_repo_class, \
             patch("app.api.v1.teachers.ChapterRepository") as mock_ch_repo_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_tb_repo = AsyncMock()
            mock_tb_repo.get_by_id.return_value = mock_textbook
            mock_tb_repo_class.return_value = mock_tb_repo

            mock_ch_repo = AsyncMock()
            mock_ch_repo.get_by_textbook.return_value = mock_chapters
            mock_ch_repo_class.return_value = mock_ch_repo

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/textbooks/1/chapters",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_chapters_textbook_not_found(self, mock_teacher_user):
        """Test listing chapters when textbook not found."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TextbookRepository") as mock_repo_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/textbooks/999/chapters",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_chapters_access_denied(self, mock_teacher_user):
        """Test listing chapters when teacher doesn't have access."""
        mock_textbook = MagicMock(id=1, school_id=999)  # Different school

        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.TextbookRepository") as mock_repo_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5  # Teacher's school is 5

            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = mock_textbook
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/textbooks/1/chapters",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_paragraphs_success(self, mock_teacher_user):
        """Test listing paragraphs for a chapter."""
        mock_chapter = MagicMock(id=1, textbook_id=1)
        mock_textbook = MagicMock(id=1, school_id=None)  # Global
        mock_paragraphs = [
            MagicMock(id=1, chapter_id=1, number=1, title="Параграф 1")
        ]

        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.ChapterRepository") as mock_ch_repo_class, \
             patch("app.api.v1.teachers.TextbookRepository") as mock_tb_repo_class, \
             patch("app.api.v1.teachers.ParagraphRepository") as mock_p_repo_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_ch_repo = AsyncMock()
            mock_ch_repo.get_by_id.return_value = mock_chapter
            mock_ch_repo_class.return_value = mock_ch_repo

            mock_tb_repo = AsyncMock()
            mock_tb_repo.get_by_id.return_value = mock_textbook
            mock_tb_repo_class.return_value = mock_tb_repo

            mock_p_repo = AsyncMock()
            mock_p_repo.get_by_chapter.return_value = mock_paragraphs
            mock_p_repo_class.return_value = mock_p_repo

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/chapters/1/paragraphs",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_paragraphs_chapter_not_found(self, mock_teacher_user):
        """Test listing paragraphs when chapter not found."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.ChapterRepository") as mock_repo_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/chapters/999/paragraphs",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_paragraphs_access_denied(self, mock_teacher_user):
        """Test listing paragraphs when teacher doesn't have access."""
        mock_chapter = MagicMock(id=1, textbook_id=1)
        mock_textbook = MagicMock(id=1, school_id=999)  # Different school

        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers.ChapterRepository") as mock_ch_repo_class, \
             patch("app.api.v1.teachers.TextbookRepository") as mock_tb_repo_class:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            mock_ch_repo = AsyncMock()
            mock_ch_repo.get_by_id.return_value = mock_chapter
            mock_ch_repo_class.return_value = mock_ch_repo

            mock_tb_repo = AsyncMock()
            mock_tb_repo.get_by_id.return_value = mock_textbook
            mock_tb_repo_class.return_value = mock_tb_repo

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/chapters/1/paragraphs",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 403


# =============================================================================
# Assignments Tests (MVP - Not Implemented)
# =============================================================================

class TestAssignments:
    """Tests for assignments endpoints (MVP - mostly not implemented)."""

    @pytest.mark.asyncio
    async def test_get_assignments_returns_empty(self, mock_teacher_user):
        """Test assignments list returns empty (not implemented)."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/assignments",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_assignment_not_implemented(self, mock_teacher_user):
        """Test create assignment returns 501 (not implemented)."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/assignments",
                    json={
                        "class_id": 1,
                        "title": "Test Assignment"
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 501

    @pytest.mark.asyncio
    async def test_get_assignment_detail_not_found(self, mock_teacher_user):
        """Test get assignment detail returns 404."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/assignments/1",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_assignment_not_found(self, mock_teacher_user):
        """Test update assignment returns 404."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.put(
                    "/api/v1/teachers/assignments/1",
                    json={"title": "Updated Title"},
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_assignment_not_found(self, mock_teacher_user):
        """Test delete assignment returns 404."""
        with patch("app.api.v1.teachers.require_teacher") as mock_auth, \
             patch("app.api.v1.teachers.get_current_user_school_id") as mock_school:

            mock_auth.return_value = mock_teacher_user
            mock_school.return_value = 5

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.delete(
                    "/api/v1/teachers/assignments/1",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 404


# =============================================================================
# Schema Tests
# =============================================================================

class TestSchemas:
    """Tests for schema validation and behavior."""

    def test_mastery_distribution_total(self):
        """Test MasteryDistribution total property."""
        dist = MasteryDistribution(
            level_a=5,
            level_b=10,
            level_c=3,
            not_started=2
        )
        assert dist.total == 20

    def test_mastery_distribution_defaults(self):
        """Test MasteryDistribution default values."""
        dist = MasteryDistribution()
        assert dist.level_a == 0
        assert dist.level_b == 0
        assert dist.level_c == 0
        assert dist.not_started == 0
        assert dist.total == 0

    def test_student_with_mastery_optional_fields(self):
        """Test StudentWithMastery with optional fields."""
        student = StudentWithMastery(
            id=1,
            student_code="STU001",
            first_name="Иван",
            last_name="Иванов"
        )
        assert student.mastery_level is None
        assert student.mastery_score is None
        assert student.completed_paragraphs == 0

    def test_teacher_dashboard_response_defaults(self):
        """Test TeacherDashboardResponse default values."""
        dashboard = TeacherDashboardResponse(
            classes_count=0,
            total_students=0,
            students_by_level=MasteryDistribution()
        )
        assert dashboard.average_class_score == 0.0
        assert dashboard.students_needing_help == 0
        assert dashboard.recent_activity == []
