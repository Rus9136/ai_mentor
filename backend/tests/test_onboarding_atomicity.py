"""
Regression tests for onboarding atomicity and RLS tenant sync.

Bug 1 (Partial onboarding):
    student_repo.create() did commit() + refresh() internally. After commit(),
    SQLAlchemy could release the connection, losing RLS bypass settings.
    The refresh() then failed, returning 500. But the student was already
    committed to DB, while join request was NOT created → partial state.

Fix: Use flush() instead of commit() for all intermediate operations.
    The final commit happens in get_db() when the endpoint returns successfully.
    If any step fails, the entire transaction is rolled back.

Bug 2 (Daily quests RLS):
    After onboarding, the mobile app could use the OLD JWT (school_id=NULL)
    for subsequent requests. TenancyMiddleware set current_tenant_id=NULL,
    but get_current_user_school_id returned 5 from DB. INSERT into
    student_daily_quests with school_id=5 failed RLS because tenant_id=0.

Fix: get_student_from_user syncs RLS tenant_id with actual DB school_id
    when a mismatch is detected.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select, text

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.invitation_code import InvitationCode
from app.models.student_join_request import StudentJoinRequest


# ========== Tests: Onboarding atomicity ==========


class TestOnboardingAtomicity:
    """Ensure onboarding creates user + student + join request atomically."""

    @pytest.mark.asyncio
    async def test_onboarding_creates_student_and_join_request(
        self, test_app, google_user_token, google_user_without_school,
        invitation_code, db_session
    ):
        """
        REGRESSION: Onboarding must create both Student record AND
        join request in a single transaction.
        Previously, student_repo.create() committed the student, then
        failed on refresh(), leaving the student without a join request.
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/onboarding/complete",
                headers={"Authorization": f"Bearer {google_user_token}"},
                json={
                    "invitation_code": invitation_code.code,
                    "first_name": "Test",
                    "last_name": "Onboarding",
                },
            )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.json()}"
        )
        data = response.json()

        # Verify Student was created
        result = await db_session.execute(
            sa_select(Student).where(
                Student.user_id == google_user_without_school.id
            )
        )
        student = result.scalar_one_or_none()
        assert student is not None, "Student record must be created"
        assert student.school_id == invitation_code.school_id

        # Verify join request was created (the part that was missing before)
        result = await db_session.execute(
            sa_select(StudentJoinRequest).where(
                StudentJoinRequest.student_id == student.id,
                StudentJoinRequest.class_id == invitation_code.class_id,
            )
        )
        join_req = result.scalar_one_or_none()
        assert join_req is not None, (
            "Join request must be created together with student"
        )
        assert join_req.status.value == "pending"

        # Verify response contains pending request info
        assert data.get("student", {}).get("pending_request") is not None

    @pytest.mark.asyncio
    async def test_onboarding_updates_user_profile(
        self, test_app, google_user_token, google_user_without_school,
        invitation_code, db_session
    ):
        """Onboarding should update user's first_name, last_name, school_id."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/onboarding/complete",
                headers={"Authorization": f"Bearer {google_user_token}"},
                json={
                    "invitation_code": invitation_code.code,
                    "first_name": "Айдар",
                    "last_name": "Серікбаев",
                    "middle_name": "Қайратұлы",
                },
            )

        assert response.status_code == 200

        # Verify user was updated in DB
        await db_session.refresh(google_user_without_school)
        assert google_user_without_school.first_name == "Айдар"
        assert google_user_without_school.last_name == "Серікбаев"
        assert google_user_without_school.middle_name == "Қайратұлы"
        assert google_user_without_school.school_id == invitation_code.school_id
        assert google_user_without_school.is_verified is True

    @pytest.mark.asyncio
    async def test_onboarding_returns_new_tokens_with_school_id(
        self, test_app, google_user_token, google_user_without_school,
        invitation_code
    ):
        """
        New tokens must contain school_id so subsequent requests
        have correct tenant context.
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/onboarding/complete",
                headers={"Authorization": f"Bearer {google_user_token}"},
                json={
                    "invitation_code": invitation_code.code,
                    "first_name": "Test",
                    "last_name": "User",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["school_id"] == invitation_code.school_id


# ========== Tests: RLS tenant context sync ==========


class TestTenantContextSync:
    """
    Test that get_student_from_user syncs RLS tenant_id
    when JWT school_id doesn't match DB school_id.
    """

    @pytest.mark.asyncio
    async def test_stale_jwt_school_id_synced(self, db_session):
        """
        REGRESSION: When JWT has school_id=NULL but user.school_id=5,
        get_student_from_user should update current_tenant_id to match.
        """
        from app.api.dependencies import get_student_from_user
        from app.core.tenant_context import set_tenant_context, clear_tenant_context
        from app.core.security import get_password_hash

        # Create school, user, student
        school = School(
            name="Sync Test School", code="sync-test",
            email="sync@test.com", is_active=True,
        )
        db_session.add(school)
        await db_session.flush()

        user = User(
            email="sync-student@test.com",
            password_hash=get_password_hash("test123"),
            first_name="Sync", last_name="Student",
            role=UserRole.STUDENT,
            school_id=school.id,  # DB has school_id set
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        student = Student(
            school_id=school.id, user_id=user.id,
            student_code="SYNC001", grade_level=7,
        )
        db_session.add(student)
        await db_session.commit()

        # Simulate stale JWT: tenant context has school_id=None
        clear_tenant_context()
        set_tenant_context(
            user_id=user.id, role="student",
            school_id=None,  # Stale JWT - school_id not yet set
            is_authenticated=True,
        )

        try:
            # Call the dependency
            result = await get_student_from_user(current_user=user, db=db_session)
            assert result.id == student.id

            # Verify that current_tenant_id was updated in the session
            row = await db_session.execute(
                text("SELECT current_setting('app.current_tenant_id', true)")
            )
            tenant_id = row.scalar()
            assert tenant_id == str(school.id), (
                f"current_tenant_id should be {school.id}, got {tenant_id}"
            )
        finally:
            clear_tenant_context()

    @pytest.mark.asyncio
    async def test_correct_jwt_no_sync_needed(self, db_session):
        """
        When JWT school_id matches DB school_id, no sync should happen.
        """
        from app.api.dependencies import get_student_from_user
        from app.core.tenant_context import set_tenant_context, clear_tenant_context
        from app.core.security import get_password_hash

        school = School(
            name="NoSync School", code="nosync",
            email="nosync@test.com", is_active=True,
        )
        db_session.add(school)
        await db_session.flush()

        user = User(
            email="nosync-student@test.com",
            password_hash=get_password_hash("test123"),
            first_name="NoSync", last_name="Student",
            role=UserRole.STUDENT,
            school_id=school.id,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        student = Student(
            school_id=school.id, user_id=user.id,
            student_code="NOSYNC001", grade_level=7,
        )
        db_session.add(student)
        await db_session.commit()

        # JWT matches DB
        clear_tenant_context()
        set_tenant_context(
            user_id=user.id, role="student",
            school_id=school.id,  # Correct school_id
            is_authenticated=True,
        )

        try:
            result = await get_student_from_user(current_user=user, db=db_session)
            assert result.id == student.id
        finally:
            clear_tenant_context()
