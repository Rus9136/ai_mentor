"""
Integration tests for join request approval flow.

Bug: MissingGreenlet when approving a join request — add_students()
accessed lazy-loaded `school_class.class_students` in async context.

Fix: Replaced lazy relationship access with direct SQL query.

These tests exercise the full chain:
  POST /teachers/join-requests/{id}/approve
  → JoinRequestService.approve_request
  → SchoolClassRepository.add_students
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select

from app.models.user import User, UserRole
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.class_student import ClassStudent
from app.models.class_teacher import ClassTeacher
from app.models.invitation_code import InvitationCode
from app.models.student_join_request import StudentJoinRequest, JoinRequestStatus


# ========== Fixtures ==========


@pytest_asyncio.fixture
async def teacher_in_class(
    db_session: AsyncSession,
    teacher_user: tuple[User, Teacher],
    school_class: SchoolClass,
) -> ClassTeacher:
    """Assign teacher to school_class so they can approve requests."""
    _, teacher = teacher_user
    ct = ClassTeacher(class_id=school_class.id, teacher_id=teacher.id)
    db_session.add(ct)
    await db_session.commit()
    await db_session.refresh(ct)
    return ct


@pytest_asyncio.fixture
async def pending_join_request(
    db_session: AsyncSession,
    student_user: tuple[User, Student],
    school_class: SchoolClass,
    school1: School,
    invitation_code: InvitationCode,
) -> StudentJoinRequest:
    """Create a PENDING join request for student → school_class."""
    _, student = student_user
    request = StudentJoinRequest(
        student_id=student.id,
        class_id=school_class.id,
        school_id=school1.id,
        invitation_code_id=invitation_code.id,
        status=JoinRequestStatus.PENDING,
        first_name="Test",
        last_name="Student",
    )
    db_session.add(request)
    await db_session.commit()
    await db_session.refresh(request)
    return request


# ========== Tests: POST /teachers/join-requests/{id}/approve ==========


class TestApproveJoinRequest:
    """Tests for join request approval (full integration)."""

    @pytest.mark.asyncio
    async def test_approve_adds_student_to_class(
        self,
        test_app,
        teacher_token,
        teacher_in_class,
        pending_join_request,
        student_user,
        school_class,
        db_session,
    ):
        """
        REGRESSION: Approving a join request should not raise
        MissingGreenlet. Student must be added to class_students.
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/teachers/join-requests/{pending_join_request.id}/approve",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["status"] == "approved"

        # Verify student is in class_students
        _, student = student_user
        result = await db_session.execute(
            sa_select(ClassStudent).where(
                ClassStudent.class_id == school_class.id,
                ClassStudent.student_id == student.id,
            )
        )
        cs = result.scalar_one_or_none()
        assert cs is not None, "Student should be added to class after approval"

    @pytest.mark.asyncio
    async def test_approve_updates_request_status(
        self,
        test_app,
        teacher_token,
        teacher_in_class,
        pending_join_request,
    ):
        """After approval, response should have status='approved' and reviewed_at."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/teachers/join-requests/{pending_join_request.id}/approve",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["reviewed_at"] is not None

    @pytest.mark.asyncio
    async def test_approve_nonexistent_request_returns_404(
        self,
        test_app,
        teacher_token,
        teacher_in_class,
    ):
        """Approve request that doesn't exist → 404."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/teachers/join-requests/99999/approve",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_approve_without_auth_returns_401(
        self,
        test_app,
        pending_join_request,
    ):
        """No auth → 401/403."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/teachers/join-requests/{pending_join_request.id}/approve",
            )

        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_student_cannot_approve_request(
        self,
        test_app,
        student_token,
        pending_join_request,
    ):
        """Student role cannot approve → 403."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/teachers/join-requests/{pending_join_request.id}/approve",
                headers={"Authorization": f"Bearer {student_token}"},
            )

        assert response.status_code == 403


class TestCrossSchoolApproval:
    """
    REGRESSION: Cross-school join request approval.

    Bug: When a student from school A joins a class in school B,
    approve_request used multiple commit()s which released DB connections
    and lost set_config('app.is_super_admin') needed to bypass RLS.

    Fix: All operations now run in a single transaction with flush().
    """

    @pytest.mark.asyncio
    async def test_cross_school_approve(
        self,
        test_app,
        db_session,
        school1,
        school2,
        school_class,          # class in school1
        teacher_user,
        teacher_in_class,
    ):
        """
        Student from school2 requests to join class in school1.
        Teacher approves → student moves to school1 and joins the class.
        """
        from app.core.security import create_access_token

        # Create student in school2 (different school from teacher/class)
        cross_user = User(
            email="cross_student@test.com",
            password_hash="hashed",
            first_name="Cross",
            last_name="Student",
            role=UserRole.STUDENT,
            school_id=school2.id,
            is_active=True,
        )
        db_session.add(cross_user)
        await db_session.flush()

        cross_student = Student(
            school_id=school2.id,
            user_id=cross_user.id,
            student_code="STU_CROSS_001",
            grade_level=7,
        )
        db_session.add(cross_student)
        await db_session.flush()

        # Create pending join request for school1's class
        request = StudentJoinRequest(
            student_id=cross_student.id,
            class_id=school_class.id,
            school_id=school1.id,
            status=JoinRequestStatus.PENDING,
            first_name="Cross",
            last_name="Student",
        )
        db_session.add(request)
        await db_session.commit()
        await db_session.refresh(request)

        teacher_user_obj, _ = teacher_user
        token = create_access_token(data={
            "sub": str(teacher_user_obj.id),
            "email": teacher_user_obj.email,
            "role": teacher_user_obj.role.value,
            "school_id": teacher_user_obj.school_id,
        })

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/teachers/join-requests/{request.id}/approve",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200, (
            f"Cross-school approve failed: {response.status_code}: {response.text}"
        )
        data = response.json()
        assert data["status"] == "approved"

        # Verify student moved to school1
        result = await db_session.execute(
            sa_select(Student).where(Student.id == cross_student.id)
        )
        updated_student = result.scalar_one()
        assert updated_student.school_id == school1.id

        # Verify student is in the class
        result = await db_session.execute(
            sa_select(ClassStudent).where(
                ClassStudent.class_id == school_class.id,
                ClassStudent.student_id == cross_student.id,
            )
        )
        cs = result.scalar_one_or_none()
        assert cs is not None, "Cross-school student should be added to class"


class TestRejectJoinRequest:
    """Tests for join request rejection."""

    @pytest.mark.asyncio
    async def test_reject_request(
        self,
        test_app,
        teacher_token,
        teacher_in_class,
        pending_join_request,
        db_session,
    ):
        """Reject sets status to 'rejected'."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/teachers/join-requests/{pending_join_request.id}/reject",
                headers={"Authorization": f"Bearer {teacher_token}"},
                json={"reason": "Неверный класс"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
