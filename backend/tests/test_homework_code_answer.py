"""
Integration tests for CODE type homework answers.

Tests that answer_code field works correctly through the full API flow:
- AnswerSubmit schema validates answer_code
- answer_code is saved to StudentTaskAnswer.answer_code
- answer_type is set to "code"
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
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
    StudentTaskAnswer,
)
from app.models.user import User
from app.models.student import Student
from app.models.school import School
from app.models.teacher import Teacher
from app.models.school_class import SchoolClass
from app.models.class_student import ClassStudent
from app.schemas.homework import AnswerSubmit


STUDENT_BASE = "/api/v1/students"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Schema Validation
# =============================================================================

class TestAnswerSubmitCodeValidation:
    """AnswerSubmit schema accepts answer_code."""

    def test_answer_code_passes_validation(self):
        """answer_code alone should pass validation."""
        data = AnswerSubmit(
            question_id=1,
            answer_code='print("Hello, World!")',
        )
        assert data.answer_code == 'print("Hello, World!")'
        assert data.answer_text is None
        assert data.selected_options is None

    def test_answer_code_with_text_passes(self):
        """answer_code + answer_text both present."""
        data = AnswerSubmit(
            question_id=1,
            answer_code='x = 42',
            answer_text='x = 42',
        )
        assert data.answer_code == 'x = 42'

    def test_empty_answer_fails_validation(self):
        """No answer_text, answer_code, or selected_options → error."""
        with pytest.raises(Exception):
            AnswerSubmit(question_id=1)


# =============================================================================
# API Integration: Submit Code Answer
# =============================================================================

@pytest_asyncio.fixture
async def code_homework(
    db_session: AsyncSession,
    school1: School,
    teacher_user: tuple[User, Teacher],
    school_class: SchoolClass,
    student_in_class: ClassStudent,
    student_user: tuple[User, Student],
) -> tuple[Homework, HomeworkTask, HomeworkTaskQuestion, HomeworkStudent]:
    """
    Create a published homework with one CODE task and one CODE question.
    Returns (homework, task, question, hw_student).
    """
    _, teacher = teacher_user
    _, student = student_user

    hw = Homework(
        school_id=school1.id,
        class_id=school_class.id,
        teacher_id=teacher.id,
        title="Python Homework",
        description="Write a Python program",
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        status=HomeworkStatus.PUBLISHED,
        show_explanations=True,
    )
    db_session.add(hw)
    await db_session.flush()

    task = HomeworkTask(
        homework_id=hw.id,
        school_id=school1.id,
        paragraph_id=None,
        task_type=HomeworkTaskType.CODE,
        sort_order=0,
        points=10,
        max_attempts=3,
    )
    db_session.add(task)
    await db_session.flush()

    question = HomeworkTaskQuestion(
        homework_task_id=task.id,
        school_id=school1.id,
        question_type=HomeworkQuestionType.CODE,
        question_text="Напишите программу, которая выводит числа от 1 до 10",
        points=10,
        sort_order=0,
    )
    db_session.add(question)
    await db_session.flush()

    hw_student = HomeworkStudent(
        homework_id=hw.id,
        student_id=student.id,
        school_id=school1.id,
        status=HomeworkStudentStatus.ASSIGNED,
    )
    db_session.add(hw_student)
    await db_session.commit()

    return (hw, task, question, hw_student)


class TestSubmitCodeAnswer:
    """Submit code answers via API and verify DB state."""

    @pytest.mark.asyncio
    async def test_submit_answer_code_saves_to_db(
        self, test_app, student_token, db_session, code_homework
    ):
        """Submit answer_code via API → saved in StudentTaskAnswer.answer_code."""
        hw, task, question, _ = code_homework
        code = 'for i in range(1, 11):\n    print(i)'

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Start task
            start_resp = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
            assert start_resp.status_code == 200
            submission_id = start_resp.json()["submission_id"]

            # Submit code answer
            resp = await client.post(
                f"{STUDENT_BASE}/homework/submissions/{submission_id}/answer",
                json={
                    "question_id": question.id,
                    "answer_code": code,
                },
                headers=auth(student_token),
            )

        assert resp.status_code == 200

        # Verify DB state
        result = await db_session.execute(
            sa_select(StudentTaskAnswer).where(
                StudentTaskAnswer.submission_id == submission_id,
                StudentTaskAnswer.question_id == question.id,
            )
        )
        answer = result.scalar_one()
        assert answer.answer_code == code
        assert answer.answer_type == "code"

    @pytest.mark.asyncio
    async def test_submit_code_and_complete(
        self, test_app, student_token, code_homework
    ):
        """Full flow: start → submit code → complete → flagged for review."""
        hw, task, question, _ = code_homework
        code = 'print("Hello")'

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Start
            start = await client.post(
                f"{STUDENT_BASE}/homework/{hw.id}/tasks/{task.id}/start",
                headers=auth(student_token),
            )
            sub_id = start.json()["submission_id"]

            # Submit code
            answer_resp = await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/answer",
                json={"question_id": question.id, "answer_code": code},
                headers=auth(student_token),
            )
            assert answer_resp.status_code == 200
            # CODE questions are not auto-graded (score=0, no correct answer to check)
            assert answer_resp.json()["score"] == 0

            # Complete
            complete_resp = await client.post(
                f"{STUDENT_BASE}/homework/submissions/{sub_id}/complete",
                headers=auth(student_token),
            )
            assert complete_resp.status_code == 200
            assert complete_resp.json()["status"] == "graded"
