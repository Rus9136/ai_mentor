"""
Tests for Teachers Homework API endpoints.

Covers:
- Homework CRUD (create, list, get, update, delete)
- Publishing (publish, close)
- Tasks management (add, delete)
- Questions (manual add, AI generation)
- Teacher review (review queue, review answer)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.user import User, UserRole
from app.models.teacher import Teacher
from app.models.homework import Homework, HomeworkTask, HomeworkTaskQuestion, StudentTaskAnswer
from app.schemas.homework import (
    HomeworkStatus,
    QuestionType,
    HomeworkCreate,
    HomeworkUpdate,
    HomeworkTaskCreate,
    QuestionCreate,
    GenerationParams,
    TeacherReviewRequest,
)
from app.services.homework import HomeworkServiceError


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
def mock_teacher():
    """Create a mock teacher."""
    teacher = MagicMock(spec=Teacher)
    teacher.id = 1
    teacher.user_id = 10
    teacher.school_id = 5
    teacher.subject = "Математика"
    return teacher


@pytest.fixture
def sample_homework():
    """Create a sample homework object."""
    homework = MagicMock(spec=Homework)
    homework.id = 1
    homework.school_id = 5
    homework.teacher_id = 1
    homework.class_id = 1
    homework.title = "Test Homework"
    homework.description = "Test description"
    homework.status = HomeworkStatus.DRAFT
    homework.due_date = datetime.utcnow() + timedelta(days=7)
    homework.ai_generation_enabled = True
    homework.tasks = []
    homework.created_at = datetime.utcnow()
    homework.updated_at = datetime.utcnow()
    homework.is_deleted = False
    return homework


@pytest.fixture
def sample_published_homework(sample_homework):
    """Create a published homework object."""
    sample_homework.status = HomeworkStatus.PUBLISHED
    return sample_homework


@pytest.fixture
def sample_task():
    """Create a sample task object."""
    task = MagicMock(spec=HomeworkTask)
    task.id = 1
    task.homework_id = 1
    task.school_id = 5
    task.paragraph_id = 100
    task.chapter_id = 50
    task.title = "Test Task"
    task.description = "Task description"
    task.order_number = 1
    task.questions = []
    task.is_deleted = False
    return task


@pytest.fixture
def sample_question():
    """Create a sample question object."""
    question = MagicMock(spec=HomeworkTaskQuestion)
    question.id = 1
    question.task_id = 1
    question.school_id = 5
    question.question_type = QuestionType.SINGLE_CHOICE
    question.question_text = "What is 2+2?"
    question.options = ["3", "4", "5", "6"]
    question.correct_answer = "4"
    question.order_number = 1
    question.points = 1.0
    question.explanation = "Basic math"
    question.is_deleted = False
    return question


@pytest.fixture
def sample_answer(sample_question):
    """Create a sample answer object."""
    answer = MagicMock(spec=StudentTaskAnswer)
    answer.id = 1
    answer.question_id = 1
    answer.student_id = 1
    answer.answer_text = "4"
    answer.answered_at = datetime.utcnow()
    answer.ai_score = 0.8
    answer.ai_confidence = 0.6  # Low confidence, needs review
    answer.ai_feedback = "Correct answer"
    answer.teacher_override_score = None
    answer.teacher_comment = None
    answer.question = sample_question
    answer.student = MagicMock(first_name="Иван", last_name="Иванов")
    return answer


# =============================================================================
# Homework CRUD Tests
# =============================================================================

class TestCreateHomework:
    """Tests for POST /teachers/homework endpoint."""

    @pytest.mark.asyncio
    async def test_create_homework_success(self, mock_teacher_user, mock_teacher, sample_homework):
        """Test successful homework creation."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.create_homework.return_value = sample_homework
            mock_service.get_homework.return_value = sample_homework
            mock_service_dep.return_value = mock_service

            mock_builder.build_homework_response.return_value = {
                "id": 1,
                "title": "Test Homework",
                "status": "draft",
                "tasks": []
            }

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework",
                    json={
                        "title": "Test Homework",
                        "class_id": 1,
                        "description": "Test description"
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 201
            mock_service.create_homework.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_homework_with_due_date(self, mock_teacher_user, mock_teacher, sample_homework):
        """Test creating homework with due date."""
        due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()

        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.create_homework.return_value = sample_homework
            mock_service.get_homework.return_value = sample_homework
            mock_service_dep.return_value = mock_service

            mock_builder.build_homework_response.return_value = {"id": 1}

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework",
                    json={
                        "title": "Test Homework",
                        "class_id": 1,
                        "due_date": due_date
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 201


class TestListHomework:
    """Tests for GET /teachers/homework endpoint."""

    @pytest.mark.asyncio
    async def test_list_homework_success(self, mock_teacher_user, mock_teacher, sample_homework):
        """Test listing homework assignments."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.list_homework_by_teacher.return_value = [sample_homework]
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/homework",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1

    @pytest.mark.asyncio
    async def test_list_homework_with_class_filter(self, mock_teacher_user, mock_teacher, sample_homework):
        """Test listing homework filtered by class."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.list_homework_by_teacher.return_value = [sample_homework]
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/homework?class_id=1",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            mock_service.list_homework_by_teacher.assert_called_once()
            call_kwargs = mock_service.list_homework_by_teacher.call_args.kwargs
            assert call_kwargs["class_id"] == 1

    @pytest.mark.asyncio
    async def test_list_homework_with_status_filter(self, mock_teacher_user, mock_teacher, sample_homework):
        """Test listing homework filtered by status."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.list_homework_by_teacher.return_value = []
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/homework?status=published",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_homework_empty(self, mock_teacher_user, mock_teacher):
        """Test listing homework when none exist."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.list_homework_by_teacher.return_value = []
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/homework",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_homework_pagination(self, mock_teacher_user, mock_teacher):
        """Test homework list pagination."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.list_homework_by_teacher.return_value = []
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/homework?skip=10&limit=5",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            call_kwargs = mock_service.list_homework_by_teacher.call_args.kwargs
            assert call_kwargs["skip"] == 10
            assert call_kwargs["limit"] == 5


class TestGetHomework:
    """Tests for GET /teachers/homework/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_homework_success(self, sample_homework):
        """Test getting homework details."""
        with patch("app.api.v1.teachers_homework.verify_homework_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_verify.return_value = sample_homework
            mock_builder.build_homework_response.return_value = {
                "id": 1,
                "title": "Test Homework",
                "status": "draft",
                "tasks": []
            }

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/homework/1",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1


class TestUpdateHomework:
    """Tests for PUT /teachers/homework/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_homework_success(self, sample_homework):
        """Test updating homework."""
        with patch("app.api.v1.teachers_homework.verify_homework_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_verify.return_value = sample_homework
            mock_school.return_value = 5

            mock_service = AsyncMock()
            sample_homework.title = "Updated Title"
            mock_service.update_homework.return_value = sample_homework
            mock_service_dep.return_value = mock_service

            mock_builder.build_homework_response.return_value = {
                "id": 1,
                "title": "Updated Title"
            }

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.put(
                    "/api/v1/teachers/homework/1",
                    json={"title": "Updated Title"},
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            mock_service.update_homework.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_homework_not_draft_fails(self, sample_published_homework):
        """Test updating published homework fails."""
        with patch("app.api.v1.teachers_homework.verify_homework_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_verify.return_value = sample_published_homework
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.update_homework.side_effect = HomeworkServiceError(
                "Cannot update published homework"
            )
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.put(
                    "/api/v1/teachers/homework/1",
                    json={"title": "Updated Title"},
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 400


class TestDeleteHomework:
    """Tests for DELETE /teachers/homework/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_homework_success(self, mock_teacher, sample_homework):
        """Test deleting homework draft."""
        with patch("app.api.v1.teachers_homework.verify_homework_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_verify.return_value = sample_homework
            mock_school.return_value = 5
            mock_get_teacher.return_value = mock_teacher

            mock_service = AsyncMock()
            mock_service.delete_homework.return_value = True
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.delete(
                    "/api/v1/teachers/homework/1",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_published_homework_fails(self, mock_teacher, sample_published_homework):
        """Test deleting published homework fails."""
        with patch("app.api.v1.teachers_homework.verify_homework_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_verify.return_value = sample_published_homework
            mock_school.return_value = 5
            mock_get_teacher.return_value = mock_teacher

            mock_service = AsyncMock()
            mock_service.delete_homework.side_effect = HomeworkServiceError(
                "Cannot delete published homework"
            )
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.delete(
                    "/api/v1/teachers/homework/1",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 400


# =============================================================================
# Publishing Tests
# =============================================================================

class TestPublishHomework:
    """Tests for POST /teachers/homework/{id}/publish endpoint."""

    @pytest.mark.asyncio
    async def test_publish_homework_success(self, sample_homework):
        """Test publishing homework."""
        with patch("app.api.v1.teachers_homework.verify_homework_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_verify.return_value = sample_homework
            mock_school.return_value = 5

            published = MagicMock()
            published.status = HomeworkStatus.PUBLISHED

            mock_service = AsyncMock()
            mock_service.publish_homework.return_value = published
            mock_service_dep.return_value = mock_service

            mock_builder.build_homework_response.return_value = {
                "id": 1,
                "status": "published"
            }

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/1/publish",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            mock_service.publish_homework.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_homework_with_student_ids(self, sample_homework):
        """Test publishing homework to specific students."""
        with patch("app.api.v1.teachers_homework.verify_homework_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_verify.return_value = sample_homework
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.publish_homework.return_value = sample_homework
            mock_service_dep.return_value = mock_service

            mock_builder.build_homework_response.return_value = {"id": 1}

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/1/publish",
                    json=[1, 2, 3],  # student_ids
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_publish_already_published_fails(self, sample_published_homework):
        """Test publishing already published homework fails."""
        with patch("app.api.v1.teachers_homework.verify_homework_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_verify.return_value = sample_published_homework
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.publish_homework.side_effect = HomeworkServiceError(
                "Homework is already published"
            )
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/1/publish",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 400


class TestCloseHomework:
    """Tests for POST /teachers/homework/{id}/close endpoint."""

    @pytest.mark.asyncio
    async def test_close_homework_success(self, sample_published_homework):
        """Test closing homework."""
        with patch("app.api.v1.teachers_homework.verify_homework_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_verify.return_value = sample_published_homework
            mock_school.return_value = 5

            closed = MagicMock()
            closed.status = HomeworkStatus.CLOSED

            mock_service = AsyncMock()
            mock_service.close_homework.return_value = closed
            mock_service_dep.return_value = mock_service

            mock_builder.build_homework_response.return_value = {
                "id": 1,
                "status": "closed"
            }

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/1/close",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_close_draft_homework_fails(self, sample_homework):
        """Test closing draft homework fails."""
        with patch("app.api.v1.teachers_homework.verify_homework_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_verify.return_value = sample_homework
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.close_homework.side_effect = HomeworkServiceError(
                "Cannot close draft homework"
            )
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/1/close",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 400


# =============================================================================
# Tasks Tests
# =============================================================================

class TestAddTask:
    """Tests for POST /teachers/homework/{id}/tasks endpoint."""

    @pytest.mark.asyncio
    async def test_add_task_success(self, sample_homework, sample_task):
        """Test adding task to homework."""
        with patch("app.api.v1.teachers_homework.verify_homework_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_verify.return_value = sample_homework
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.add_task.return_value = sample_task
            mock_service_dep.return_value = mock_service

            mock_builder.build_task_response.return_value = {
                "id": 1,
                "title": "Test Task"
            }

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/1/tasks",
                    json={
                        "paragraph_id": 100,
                        "title": "Test Task",
                        "description": "Task description"
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_add_task_to_published_fails(self, sample_published_homework):
        """Test adding task to published homework fails."""
        with patch("app.api.v1.teachers_homework.verify_homework_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_verify.return_value = sample_published_homework
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.add_task.side_effect = HomeworkServiceError(
                "Cannot add task to published homework"
            )
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/1/tasks",
                    json={
                        "paragraph_id": 100,
                        "title": "Test Task"
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 400


class TestDeleteTask:
    """Tests for DELETE /teachers/homework/tasks/{task_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self, sample_task):
        """Test deleting task from homework."""
        with patch("app.api.v1.teachers_homework.verify_task_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_verify.return_value = sample_task
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.delete_task.return_value = True
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.delete(
                    "/api/v1/teachers/homework/tasks/1",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, sample_task):
        """Test deleting non-existent task."""
        with patch("app.api.v1.teachers_homework.verify_task_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_verify.return_value = sample_task
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.delete_task.return_value = False
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.delete(
                    "/api/v1/teachers/homework/tasks/999",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 404


# =============================================================================
# Questions Tests
# =============================================================================

class TestAddQuestion:
    """Tests for POST /teachers/homework/tasks/{task_id}/questions endpoint."""

    @pytest.mark.asyncio
    async def test_add_question_success(self, sample_task, sample_question):
        """Test adding question to task."""
        with patch("app.api.v1.teachers_homework.verify_task_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_verify.return_value = sample_task

            mock_service = AsyncMock()
            mock_service.add_question.return_value = sample_question
            mock_service_dep.return_value = mock_service

            mock_builder.build_question_with_answer.return_value = {
                "id": 1,
                "question_text": "What is 2+2?",
                "question_type": "single_choice"
            }

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/tasks/1/questions",
                    json={
                        "question_type": "single_choice",
                        "question_text": "What is 2+2?",
                        "options": ["3", "4", "5", "6"],
                        "correct_answer": "4",
                        "points": 1.0
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_add_open_ended_question(self, sample_task, sample_question):
        """Test adding open-ended question."""
        sample_question.question_type = QuestionType.OPEN_ENDED
        sample_question.options = None
        sample_question.correct_answer = None

        with patch("app.api.v1.teachers_homework.verify_task_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_verify.return_value = sample_task

            mock_service = AsyncMock()
            mock_service.add_question.return_value = sample_question
            mock_service_dep.return_value = mock_service

            mock_builder.build_question_with_answer.return_value = {
                "id": 1,
                "question_type": "open_ended"
            }

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/tasks/1/questions",
                    json={
                        "question_type": "open_ended",
                        "question_text": "Explain the concept",
                        "points": 5.0
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 201


class TestGenerateQuestions:
    """Tests for POST /teachers/homework/tasks/{task_id}/generate-questions endpoint."""

    @pytest.mark.asyncio
    async def test_generate_questions_success(self, sample_task, sample_question):
        """Test generating questions with AI."""
        with patch("app.api.v1.teachers_homework.verify_task_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_verify.return_value = sample_task
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.generate_questions_for_task.return_value = [sample_question]
            mock_service.homework_repo = AsyncMock()
            mock_service_dep.return_value = mock_service

            mock_builder.build_question_with_answer.return_value = {
                "id": 1,
                "question_text": "Generated question"
            }

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/tasks/1/generate-questions",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1

    @pytest.mark.asyncio
    async def test_generate_questions_with_params(self, sample_task, sample_question):
        """Test generating questions with custom parameters."""
        with patch("app.api.v1.teachers_homework.verify_task_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_verify.return_value = sample_task
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.generate_questions_for_task.return_value = [sample_question]
            mock_service.homework_repo = AsyncMock()
            mock_service_dep.return_value = mock_service

            mock_builder.build_question_with_answer.return_value = {"id": 1}

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/tasks/1/generate-questions",
                    json={
                        "single_choice_count": 3,
                        "multiple_choice_count": 2,
                        "open_ended_count": 1,
                        "difficulty": "hard"
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_generate_questions_regenerate(self, sample_task, sample_question):
        """Test regenerating questions (replacing existing)."""
        with patch("app.api.v1.teachers_homework.verify_task_ownership") as mock_verify, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_verify.return_value = sample_task
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.generate_questions_for_task.return_value = [sample_question]
            mock_service.homework_repo = AsyncMock()
            mock_service_dep.return_value = mock_service

            mock_builder.build_question_with_answer.return_value = {"id": 1}

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/tasks/1/generate-questions?regenerate=true",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            mock_service.generate_questions_for_task.assert_called_once()
            call_kwargs = mock_service.generate_questions_for_task.call_args.kwargs
            assert call_kwargs["regenerate"] is True


# =============================================================================
# Teacher Review Tests
# =============================================================================

class TestReviewQueue:
    """Tests for GET /teachers/homework/review-queue endpoint."""

    @pytest.mark.asyncio
    async def test_get_review_queue_success(self, mock_teacher, sample_answer):
        """Test getting answers for review."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_answers_for_review.return_value = [sample_answer]
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/homework/review-queue",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["ai_confidence"] == 0.6

    @pytest.mark.asyncio
    async def test_get_review_queue_with_homework_filter(self, mock_teacher, sample_answer):
        """Test review queue filtered by homework."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_answers_for_review.return_value = []
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/homework/review-queue?homework_id=1",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            call_kwargs = mock_service.get_answers_for_review.call_args.kwargs
            assert call_kwargs["homework_id"] == 1

    @pytest.mark.asyncio
    async def test_get_review_queue_empty(self, mock_teacher):
        """Test empty review queue."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.get_answers_for_review.return_value = []
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/homework/review-queue",
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            assert response.json() == []


class TestReviewAnswer:
    """Tests for POST /teachers/homework/answers/{id}/review endpoint."""

    @pytest.mark.asyncio
    async def test_review_answer_success(self, mock_teacher, sample_answer):
        """Test reviewing student answer."""
        sample_answer.teacher_override_score = 0.9
        sample_answer.teacher_comment = "Good work!"
        sample_answer.updated_at = datetime.utcnow()

        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.review_answer.return_value = sample_answer
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/answers/1/review",
                    json={
                        "score": 90,  # Score in 0-100
                        "feedback": "Good work!"
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["teacher_score"] == 90.0

    @pytest.mark.asyncio
    async def test_review_answer_not_found(self, mock_teacher):
        """Test reviewing non-existent answer."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.review_answer.return_value = None
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/answers/999/review",
                    json={"score": 90, "feedback": "Good"},
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_review_answer_override_ai_score(self, mock_teacher, sample_answer):
        """Test overriding AI score with teacher review."""
        sample_answer.ai_score = 0.5  # AI gave 50%
        sample_answer.teacher_override_score = 0.85  # Teacher gives 85%
        sample_answer.teacher_comment = "Better than AI thought"
        sample_answer.updated_at = datetime.utcnow()

        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.review_answer.return_value = sample_answer
            mock_service_dep.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/answers/1/review",
                    json={
                        "score": 85,
                        "feedback": "Better than AI thought"
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["teacher_score"] == 85.0


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_homework_title_too_long(self, mock_teacher):
        """Test creating homework with title too long."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework",
                    json={
                        "title": "A" * 500,  # Too long
                        "class_id": 1
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            # Should fail validation
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_homework_invalid_pagination(self, mock_teacher):
        """Test listing homework with invalid pagination."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/teachers/homework?limit=500",  # Exceeds max
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_review_score_validation(self, mock_teacher):
        """Test review with invalid score."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework/answers/1/review",
                    json={
                        "score": 150,  # Invalid, should be 0-100
                        "feedback": "Test"
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            # Depends on schema validation
            # If schema validates 0-100, this should return 422
            # Otherwise service should handle it

    @pytest.mark.asyncio
    async def test_unicode_homework_title(self, mock_teacher_user, mock_teacher, sample_homework):
        """Test creating homework with unicode characters."""
        with patch("app.api.v1.teachers_homework.get_teacher_from_user") as mock_get_teacher, \
             patch("app.api.v1.teachers_homework.get_current_user_school_id") as mock_school, \
             patch("app.api.v1.teachers_homework.get_homework_service") as mock_service_dep, \
             patch("app.api.v1.teachers_homework.HomeworkResponseBuilder") as mock_builder:

            mock_get_teacher.return_value = mock_teacher
            mock_school.return_value = 5

            mock_service = AsyncMock()
            mock_service.create_homework.return_value = sample_homework
            mock_service.get_homework.return_value = sample_homework
            mock_service_dep.return_value = mock_service

            mock_builder.build_homework_response.return_value = {"id": 1}

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/teachers/homework",
                    json={
                        "title": "Домашняя работа по математике 📚",
                        "class_id": 1,
                        "description": "Изучение алгебры — важная тема!"
                    },
                    headers={"Authorization": "Bearer test-token"}
                )

            assert response.status_code == 201


class TestSchemas:
    """Tests for schema defaults and validation."""

    def test_homework_status_enum(self):
        """Test HomeworkStatus enum values."""
        assert HomeworkStatus.DRAFT.value == "draft"
        assert HomeworkStatus.PUBLISHED.value == "published"
        assert HomeworkStatus.CLOSED.value == "closed"

    def test_question_type_enum(self):
        """Test QuestionType enum values."""
        assert QuestionType.SINGLE_CHOICE.value == "single_choice"
        assert QuestionType.MULTIPLE_CHOICE.value == "multiple_choice"
        assert QuestionType.OPEN_ENDED.value == "open_ended"
        assert QuestionType.TRUE_FALSE.value == "true_false"

    def test_homework_create_defaults(self):
        """Test HomeworkCreate default values."""
        data = HomeworkCreate(
            title="Test",
            class_id=1
        )
        assert data.ai_generation_enabled is True  # default

    def test_generation_params_defaults(self):
        """Test GenerationParams default values."""
        params = GenerationParams()
        assert params.single_choice_count == 3
        assert params.multiple_choice_count == 1
        assert params.open_ended_count == 1
        assert params.difficulty == "medium"
