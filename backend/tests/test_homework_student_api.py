"""
Integration tests for Student Homework API.

Tests the full student workflow:
- View assigned homework (list, detail)
- Start task attempts
- Get questions (correct answers hidden)
- Submit answers (auto-graded)
- Complete submissions (score calculation)
- View results with feedback
- Access control and isolation
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select as sa_select

from app.models.homework import (
    Homework,
    HomeworkTask,
    HomeworkTaskQuestion,
    HomeworkStudent,
    HomeworkStatus,
    HomeworkTaskType,
    HomeworkQuestionType,
    HomeworkStudentStatus,
    StudentTaskSubmission,
    TaskSubmissionStatus,
    StudentTaskAnswer,
)
from app.models.user import User
from app.models.student import Student
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.class_student import ClassStudent


STUDENT_BASE = "/api/v1/students"
TEACHER_BASE = "/api/v1/teachers/homework"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Student List
# =============================================================================

class TestStudentHomeworkList:
    """View assigned homework."""

    @pytest.mark.asyncio
    async def test_list_empty_when_none_assigned(self, test_app, student_token):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(
                f"{STUDENT_BASE}/homework",
                headers=auth(student_token),
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_assigned_homework(self, test_app, student_token, published_homework):
        hw, _, _, _ = published_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(
                f"{STUDENT_BASE}/homework",
                headers=auth(student_token),
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any(h["id"] == hw.id for h in data["items"])

    @pytest.mark.asyncio
    async def test_student2_cannot_see_other_schools_homework(
        self, test_app, student2_token, published_homework
    ):
        """Student2 (school2) cannot see school1's homework."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(
                f"{STUDENT_BASE}/homework",
                headers=auth(student2_token),
            )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# =============================================================================
# Student Detail
# =============================================================================

class TestStudentHomeworkDetail:
    """View homework detail."""

    @pytest.mark.asyncio
    async def test_get_homework_detail(self, test_app, student_token, published_homework):
        hw, _, _, _ = published_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(
                f"{STUDENT_BASE}/homework/{hw.id}",
                headers=auth(student_token),
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == hw.id
        assert data["title"] == hw.title
        assert data["my_status"] == "assigned"
        assert "tasks" in data

    @pytest.mark.asyncio
    async def test_get_unassigned_homework_404(self, test_app, student_token):
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(
                f"{STUDENT_BASE}/homework/99999",
                headers=auth(student_token),
            )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_overdue_homework_shows_is_overdue(
        self, test_app, student_token, db_session, published_homework
    ):
        """Set due_date to past → is_overdue=True."""
        hw, _, _, _ = published_homework
        hw.due_date = datetime.now(timezone.utc) - timedelta(hours=1)
        await db_session.flush()
        await db_session.commit()

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(
                f"{STUDENT_BASE}/homework/{hw.id}",
                headers=auth(student_token),
            )
        assert resp.status_code == 200
        assert resp.json()["is_overdue"] is True


# =============================================================================
# Start Task
# =============================================================================

class TestStudentStartTask:
    """Start a task attempt."""

    @pytest.mark.asyncio
    async def test_start_task_success(self, test_app, student_token, published_homework):
        hw, task, _, _ = published_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "in_progress"
        assert data["submission_id"] is not None
        assert data["current_attempt"] == 1

    @pytest.mark.asyncio
    async def test_start_task_unassigned_homework_400(self, test_app, student2_token, published_homework):
        """Student2 tries to start task on homework not assigned to them."""
        hw, task, _, _ = published_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student2_token),
            )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_start_task_closed_homework_400(
        self, test_app, student_token, db_session, published_homework
    ):
        """Start task on closed homework → 400."""
        hw, task, _, _ = published_homework
        hw.status = HomeworkStatus.CLOSED
        await db_session.flush()
        await db_session.commit()

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
        assert resp.status_code == 400


# =============================================================================
# Get Questions
# =============================================================================

class TestStudentGetQuestions:
    """Get task questions (correct answers hidden)."""

    @pytest.mark.asyncio
    async def test_get_questions_hides_correct_answers(
        self, test_app, student_token, published_homework
    ):
        hw, task, question, _ = published_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/questions",
                headers=auth(student_token),
            )
        assert resp.status_code == 200
        questions = resp.json()
        assert len(questions) >= 1

        for q in questions:
            if q["options"]:
                for opt in q["options"]:
                    # is_correct should always be False in student view
                    # (Pydantic adds default=False even when endpoint strips it)
                    assert opt.get("is_correct") is False

    @pytest.mark.asyncio
    async def test_get_questions_unassigned_404(self, test_app, student2_token, published_homework):
        hw, task, _, _ = published_homework
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.get(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/questions",
                headers=auth(student2_token),
            )
        assert resp.status_code == 404


# =============================================================================
# Submit Answers
# =============================================================================

class TestStudentSubmitAnswers:
    """Submit answers to questions."""

    @pytest.mark.asyncio
    async def test_submit_correct_answer(self, test_app, student_token, published_homework):
        hw, task, question, _ = published_homework

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            # Start task
            start_resp = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
            submission_id = start_resp.json()["submission_id"]

            # Submit correct answer (option "b" is correct)
            resp = await client.post(
                f"{STUDENT_BASE}/homework/submissions/{submission_id}/answer",
                json={
                    "question_id": question.id,
                    "selected_options": ["b"],
                },
                headers=auth(student_token),
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is True
        assert data["score"] == question.points

    @pytest.mark.asyncio
    async def test_submit_incorrect_answer(self, test_app, student_token, published_homework):
        hw, task, question, _ = published_homework

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            # Start task
            start_resp = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
            submission_id = start_resp.json()["submission_id"]

            # Submit wrong answer
            resp = await client.post(
                f"{STUDENT_BASE}/homework/submissions/{submission_id}/answer",
                json={
                    "question_id": question.id,
                    "selected_options": ["a"],
                },
                headers=auth(student_token),
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is False
        assert data["score"] == 0.0


# =============================================================================
# Complete Submission
# =============================================================================

class TestStudentCompleteSubmission:
    """Complete a submission and check scores."""

    @pytest.mark.asyncio
    async def test_complete_submission_correct(self, test_app, student_token, published_homework):
        hw, task, question, _ = published_homework

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            # Start → Answer → Complete
            start = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
            sub_id = start.json()["submission_id"]

            await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/answer",
                json={"question_id": question.id, "selected_options": ["b"]},
                headers=auth(student_token),
            )

            resp = await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/complete",
                headers=auth(student_token),
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_score"] == question.points
        assert data["max_score"] == question.points
        assert data["percentage"] == 100.0
        assert data["status"] == "graded"

    @pytest.mark.asyncio
    async def test_complete_submission_incorrect(self, test_app, student_token, published_homework):
        hw, task, question, _ = published_homework

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            start = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
            sub_id = start.json()["submission_id"]

            await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/answer",
                json={"question_id": question.id, "selected_options": ["a"]},
                headers=auth(student_token),
            )

            resp = await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/complete",
                headers=auth(student_token),
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_score"] == 0.0
        assert data["percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_complete_already_completed_400(self, test_app, student_token, published_homework):
        hw, task, question, _ = published_homework

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            start = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
            sub_id = start.json()["submission_id"]

            await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/answer",
                json={"question_id": question.id, "selected_options": ["b"]},
                headers=auth(student_token),
            )

            # Complete once
            await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/complete",
                headers=auth(student_token),
            )

            # Try to complete again
            resp = await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/complete",
                headers=auth(student_token),
            )
        assert resp.status_code == 400


# =============================================================================
# View Results
# =============================================================================

class TestStudentViewResults:
    """View results after submission completion."""

    @pytest.mark.asyncio
    async def test_view_results_with_explanations(self, test_app, student_token, published_homework):
        hw, task, question, _ = published_homework

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            # Start → Answer → Complete
            start = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
            sub_id = start.json()["submission_id"]

            await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/answer",
                json={"question_id": question.id, "selected_options": ["b"]},
                headers=auth(student_token),
            )

            await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/complete",
                headers=auth(student_token),
            )

            # View results
            resp = await client.get(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/results",
                headers=auth(student_token),
            )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) >= 1
        assert results[0]["is_correct"] is True
        assert results[0]["is_answered"] is True

    @pytest.mark.asyncio
    async def test_view_results_other_student_403(
        self, test_app, student_token, student2_token, published_homework
    ):
        """Student2 cannot view student1's results."""
        hw, task, question, _ = published_homework

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            # Student1 completes submission
            start = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
            sub_id = start.json()["submission_id"]

            await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/answer",
                json={"question_id": question.id, "selected_options": ["b"]},
                headers=auth(student_token),
            )

            await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/complete",
                headers=auth(student_token),
            )

            # Student2 tries to view results
            resp = await client.get(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/results",
                headers=auth(student2_token),
            )
        assert resp.status_code == 403


# =============================================================================
# Max Attempts
# =============================================================================

class TestStudentMaxAttempts:
    """Verify max_attempts enforcement."""

    @pytest.mark.asyncio
    async def test_second_attempt_after_completing_first(
        self, test_app, student_token, published_homework
    ):
        """Task has max_attempts=2 → can start second attempt after completing first."""
        hw, task, question, _ = published_homework

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            # First attempt: start → answer → complete
            start = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
            sub_id = start.json()["submission_id"]

            await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/answer",
                json={"question_id": question.id, "selected_options": ["a"]},
                headers=auth(student_token),
            )
            await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/complete",
                headers=auth(student_token),
            )

            # Second attempt (max_attempts=2 in draft_homework fixture)
            start2 = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
        assert start2.status_code == 200
        assert start2.json()["current_attempt"] == 2

    @pytest.mark.asyncio
    async def test_exceeds_max_attempts_400(
        self, test_app, student_token, db_session, published_homework
    ):
        """Set max_attempts=1, try second start → 400."""
        hw, task, question, _ = published_homework
        task.max_attempts = 1
        await db_session.flush()
        await db_session.commit()

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            # First attempt
            start = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
            sub_id = start.json()["submission_id"]

            await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/answer",
                json={"question_id": question.id, "selected_options": ["b"]},
                headers=auth(student_token),
            )
            await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/complete",
                headers=auth(student_token),
            )

            # Second attempt should fail
            resp = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
        assert resp.status_code == 400
        assert "attempts" in resp.json()["detail"].lower()
