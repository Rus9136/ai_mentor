"""
Integration tests for Teacher Homework API.

Tests the full HTTP request-response cycle with real database:
- Homework CRUD (create, get, list, update, delete)
- Permission and ownership checks
- Task management (add, delete)
- Manual question creation
- Publishing and closing workflow
- Full workflow end-to-end
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient, ASGITransport

from app.models.homework import (
    Homework,
    HomeworkTask,
    HomeworkTaskQuestion,
    HomeworkStudent,
    HomeworkStatus,
    HomeworkTaskType,
    HomeworkQuestionType,
    HomeworkStudentStatus,
)
from app.models.user import User
from app.models.teacher import Teacher
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.paragraph import Paragraph


BASE = "/api/v1/teachers/homework"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def homework_payload(class_id: int, **overrides) -> dict:
    data = {
        "title": "Тест по алгебре",
        "description": "Домашнее задание по линейным уравнениям",
        "class_id": class_id,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    }
    data.update(overrides)
    return data


# =============================================================================
# CRUD
# =============================================================================

class TestTeacherHomeworkCRUD:
    """Homework CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_homework_success(self, test_app, teacher_token, school_class):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                BASE,
                json=homework_payload(school_class.id),
                headers=auth(teacher_token),
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Тест по алгебре"
        assert data["status"] == "draft"
        assert data["class_id"] == school_class.id
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_homework_missing_title_422(self, test_app, teacher_token, school_class):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                BASE,
                json={
                    "class_id": school_class.id,
                    "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                },
                headers=auth(teacher_token),
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_homework_missing_due_date_422(self, test_app, teacher_token, school_class):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                BASE,
                json={"title": "Test", "class_id": school_class.id},
                headers=auth(teacher_token),
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_get_homework_detail(self, test_app, teacher_token, draft_homework):
        hw, _, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(f"{BASE}/{hw.id}", headers=auth(teacher_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == hw.id
        assert data["title"] == hw.title
        assert "tasks" in data

    @pytest.mark.asyncio
    async def test_get_homework_not_found(self, test_app, teacher_token):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(f"{BASE}/99999", headers=auth(teacher_token))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_homework_empty(self, test_app, teacher_token):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(BASE, headers=auth(teacher_token))
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_homework_returns_own(self, test_app, teacher_token, draft_homework):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(BASE, headers=auth(teacher_token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == draft_homework[0].title

    @pytest.mark.asyncio
    async def test_list_homework_filter_by_status(self, test_app, teacher_token, draft_homework):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(f"{BASE}?status=draft", headers=auth(teacher_token))
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(f"{BASE}?status=published", headers=auth(teacher_token))
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    @pytest.mark.asyncio
    async def test_update_draft_homework(self, test_app, teacher_token, draft_homework):
        hw, _, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.put(
                f"{BASE}/{hw.id}",
                json={"title": "Updated Title"},
                headers=auth(teacher_token),
            )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_published_homework_400(self, test_app, teacher_token, published_homework):
        hw, _, _, _ = published_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.put(
                f"{BASE}/{hw.id}",
                json={"title": "New Title"},
                headers=auth(teacher_token),
            )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_draft_homework(self, test_app, teacher_token, draft_homework):
        hw, _, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.delete(f"{BASE}/{hw.id}", headers=auth(teacher_token))
        assert resp.status_code == 204

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(f"{BASE}/{hw.id}", headers=auth(teacher_token))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_published_homework_400(self, test_app, teacher_token, published_homework):
        hw, _, _, _ = published_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.delete(f"{BASE}/{hw.id}", headers=auth(teacher_token))
        assert resp.status_code == 400


# =============================================================================
# Permissions
# =============================================================================

class TestTeacherHomeworkPermissions:
    """Ownership and school isolation checks."""

    @pytest.mark.asyncio
    async def test_student_cannot_access_teacher_endpoints(self, test_app, student_token, school_class):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                BASE,
                json=homework_payload(school_class.id),
                headers=auth(student_token),
            )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_teacher2_cannot_see_teacher1_homework(
        self, test_app, teacher2_token, draft_homework
    ):
        hw, _, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(f"{BASE}/{hw.id}", headers=auth(teacher2_token))
        # Different school → 404 (school_id filter)
        assert resp.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_teacher2_list_empty_for_other_school(
        self, test_app, teacher2_token, draft_homework
    ):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(BASE, headers=auth(teacher2_token))
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    @pytest.mark.asyncio
    async def test_unauthenticated_request_401(self, test_app):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(BASE)
        assert resp.status_code in (401, 403)


# =============================================================================
# Task Management
# =============================================================================

class TestTeacherTaskManagement:
    """Add and delete tasks within homework."""

    @pytest.mark.asyncio
    async def test_add_quiz_task(self, test_app, teacher_token, draft_homework, paragraph1):
        hw, _, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                f"{BASE}/{hw.id}/tasks",
                json={
                    "paragraph_id": paragraph1.id,
                    "task_type": "quiz",
                    "points": 15,
                    "max_attempts": 3,
                },
                headers=auth(teacher_token),
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["task_type"] == "quiz"
        assert data["points"] == 15
        assert data["max_attempts"] == 3

    @pytest.mark.asyncio
    async def test_add_read_task(self, test_app, teacher_token, draft_homework, paragraph1):
        hw, _, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                f"{BASE}/{hw.id}/tasks",
                json={"paragraph_id": paragraph1.id, "task_type": "read"},
                headers=auth(teacher_token),
            )
        assert resp.status_code == 201
        assert resp.json()["task_type"] == "read"

    @pytest.mark.asyncio
    async def test_add_essay_task_with_instructions(self, test_app, teacher_token, draft_homework, paragraph1):
        hw, _, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                f"{BASE}/{hw.id}/tasks",
                json={
                    "paragraph_id": paragraph1.id,
                    "task_type": "essay",
                    "instructions": "Write an essay about linear equations",
                },
                headers=auth(teacher_token),
            )
        assert resp.status_code == 201
        assert resp.json()["task_type"] == "essay"

    @pytest.mark.asyncio
    async def test_add_task_to_published_homework_400(
        self, test_app, teacher_token, published_homework, paragraph1
    ):
        hw, _, _, _ = published_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                f"{BASE}/{hw.id}/tasks",
                json={"paragraph_id": paragraph1.id, "task_type": "quiz"},
                headers=auth(teacher_token),
            )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_task(self, test_app, teacher_token, draft_homework):
        _, task, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.delete(
                f"{BASE}/tasks/{task.id}",
                headers=auth(teacher_token),
            )
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_task_from_published_homework_400(
        self, test_app, teacher_token, published_homework
    ):
        _, task, _, _ = published_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.delete(
                f"{BASE}/tasks/{task.id}",
                headers=auth(teacher_token),
            )
        assert resp.status_code == 400


# =============================================================================
# Question Management
# =============================================================================

class TestTeacherQuestionManagement:
    """Manual question creation for tasks."""

    @pytest.mark.asyncio
    async def test_add_single_choice_question(self, test_app, teacher_token, draft_homework):
        _, task, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                f"{BASE}/tasks/{task.id}/questions",
                json={
                    "question_text": "What is the capital of France?",
                    "question_type": "single_choice",
                    "options": [
                        {"id": "1", "text": "London", "is_correct": False},
                        {"id": "2", "text": "Paris", "is_correct": True},
                        {"id": "3", "text": "Berlin", "is_correct": False},
                    ],
                    "points": 5,
                },
                headers=auth(teacher_token),
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["question_type"] == "single_choice"
        assert data["points"] == 5
        # Teacher view includes correct_answer info
        assert "correct_answer" in data

    @pytest.mark.asyncio
    async def test_add_short_answer_question(self, test_app, teacher_token, draft_homework):
        _, task, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                f"{BASE}/tasks/{task.id}/questions",
                json={
                    "question_text": "What is 2 + 2?",
                    "question_type": "short_answer",
                    "correct_answer": "4",
                    "points": 3,
                },
                headers=auth(teacher_token),
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["question_type"] == "short_answer"
        assert data["correct_answer"] == "4"

    @pytest.mark.asyncio
    async def test_add_open_ended_question(self, test_app, teacher_token, draft_homework):
        _, task, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                f"{BASE}/tasks/{task.id}/questions",
                json={
                    "question_text": "Explain the concept of linear equations.",
                    "question_type": "open_ended",
                    "points": 20,
                    "expected_answer_hints": "Should mention variables, coefficients, and solutions",
                },
                headers=auth(teacher_token),
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["question_type"] == "open_ended"


# =============================================================================
# Publishing
# =============================================================================

class TestTeacherPublishing:
    """Homework publish and close lifecycle."""

    @pytest.mark.asyncio
    async def test_publish_homework_success(
        self, test_app, teacher_token, draft_homework, student_in_class
    ):
        hw, _, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(f"{BASE}/{hw.id}/publish", headers=auth(teacher_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "published"
        assert data["total_students"] >= 1

    @pytest.mark.asyncio
    async def test_publish_empty_homework_400(
        self, test_app, teacher_token, school_class, student_in_class, school1, teacher_user
    ):
        """Create homework with no tasks, try to publish → 400."""
        _, teacher = teacher_user
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            # Create empty homework
            create_resp = await client.post(
                BASE,
                json=homework_payload(school_class.id),
                headers=auth(teacher_token),
            )
            hw_id = create_resp.json()["id"]

            # Try to publish
            resp = await client.post(f"{BASE}/{hw_id}/publish", headers=auth(teacher_token))
        assert resp.status_code == 400
        assert "task" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_publish_already_published_400(
        self, test_app, teacher_token, published_homework
    ):
        hw, _, _, _ = published_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(f"{BASE}/{hw.id}/publish", headers=auth(teacher_token))
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_close_published_homework(
        self, test_app, teacher_token, published_homework
    ):
        hw, _, _, _ = published_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(f"{BASE}/{hw.id}/close", headers=auth(teacher_token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    @pytest.mark.asyncio
    async def test_close_draft_homework_400(self, test_app, teacher_token, draft_homework):
        hw, _, _ = draft_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(f"{BASE}/{hw.id}/close", headers=auth(teacher_token))
        assert resp.status_code == 400


# =============================================================================
# Review Queue
# =============================================================================

class TestTeacherReview:
    """Teacher review queue."""

    @pytest.mark.asyncio
    async def test_get_review_queue_empty(self, test_app, teacher_token):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(f"{BASE}/review-queue", headers=auth(teacher_token))
        assert resp.status_code == 200
        assert resp.json() == []


# =============================================================================
# Full Workflow
# =============================================================================

class TestHomeworkFullWorkflow:
    """End-to-end teacher + student workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow(
        self,
        test_app,
        teacher_token,
        student_token,
        school_class,
        student_in_class,
        paragraph1,
    ):
        """
        1. Teacher creates homework
        2. Teacher adds QUIZ task
        3. Teacher adds single_choice question
        4. Teacher publishes
        5. Student sees homework
        6. Student starts task
        7. Student submits correct answer
        8. Student completes submission
        9. Student views results
        10. Teacher closes homework
        """
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            # 1. Create homework
            resp = await client.post(
                BASE,
                json=homework_payload(school_class.id),
                headers=auth(teacher_token),
            )
            assert resp.status_code == 201
            hw_id = resp.json()["id"]

            # 2. Add QUIZ task
            resp = await client.post(
                f"{BASE}/{hw_id}/tasks",
                json={
                    "paragraph_id": paragraph1.id,
                    "task_type": "quiz",
                    "points": 10,
                    "max_attempts": 1,
                },
                headers=auth(teacher_token),
            )
            assert resp.status_code == 201
            task_id = resp.json()["id"]

            # 3. Add question
            resp = await client.post(
                f"{BASE}/tasks/{task_id}/questions",
                json={
                    "question_text": "What is 2 + 2?",
                    "question_type": "single_choice",
                    "options": [
                        {"id": "a", "text": "3", "is_correct": False},
                        {"id": "b", "text": "4", "is_correct": True},
                    ],
                    "points": 10,
                },
                headers=auth(teacher_token),
            )
            assert resp.status_code == 201
            question_id = resp.json()["id"]

            # 4. Publish
            resp = await client.post(
                f"{BASE}/{hw_id}/publish",
                headers=auth(teacher_token),
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "published"

            # 5. Student sees homework
            resp = await client.get(
                "/api/v1/students/homework",
                headers=auth(student_token),
            )
            assert resp.status_code == 200
            items = resp.json()["items"]
            assert len(items) >= 1
            assert any(h["id"] == hw_id for h in items)

            # 6. Student starts task
            resp = await client.post(
                f"/api/v1/students/homework/{hw_id}/tasks/{task_id}/start",
                headers=auth(student_token),
            )
            assert resp.status_code == 200
            submission_id = resp.json()["submission_id"]
            assert resp.json()["status"] == "in_progress"

            # 7. Submit correct answer
            resp = await client.post(
                f"/api/v1/students/homework/submissions/{submission_id}/answer",
                json={
                    "question_id": question_id,
                    "selected_options": ["b"],
                },
                headers=auth(student_token),
            )
            assert resp.status_code == 200
            assert resp.json()["is_correct"] is True

            # 8. Complete submission
            resp = await client.post(
                f"/api/v1/students/homework/submissions/{submission_id}/complete",
                headers=auth(student_token),
            )
            assert resp.status_code == 200
            result = resp.json()
            assert result["total_score"] == 10.0
            assert result["max_score"] == 10.0
            assert result["percentage"] == 100.0

            # 9. View results
            resp = await client.get(
                f"/api/v1/students/homework/submissions/{submission_id}/results",
                headers=auth(student_token),
            )
            assert resp.status_code == 200
            results = resp.json()
            assert len(results) == 1
            assert results[0]["is_correct"] is True

            # 10. Teacher closes homework
            resp = await client.post(
                f"{BASE}/{hw_id}/close",
                headers=auth(teacher_token),
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "closed"
