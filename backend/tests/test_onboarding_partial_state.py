"""
Regression tests for onboarding partial state bug.

Bug: User has school_id set but no Student record (partial onboarding).
POST /auth/onboarding/complete returned VAL_006 without creating Student,
leaving the user stuck — all /students/* endpoints returned 400.

Fix: Before raising VAL_006, check if Student record exists.
If Student is missing, allow onboarding to continue.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.invitation_code import InvitationCode


# ========== Fixtures ==========


@pytest_asyncio.fixture
async def partial_user(db_session: AsyncSession, school1: School) -> User:
    """
    User with school_id set but NO Student record.
    Simulates partial onboarding failure.
    """
    from app.core.security import get_password_hash

    user = User(
        email="partial@test.com",
        password_hash=get_password_hash("test123"),
        first_name="Partial",
        last_name="User",
        role=UserRole.STUDENT,
        school_id=school1.id,  # Already assigned
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def partial_user_token(partial_user: User) -> str:
    """JWT token for partial user (has school_id in token)."""
    return create_access_token(data={
        "sub": str(partial_user.id),
        "email": partial_user.email,
        "role": partial_user.role.value,
        "school_id": partial_user.school_id,
    })


# ========== Tests: POST /auth/onboarding/complete ==========


class TestOnboardingPartialState:
    """Tests for partial onboarding recovery."""

    @pytest.mark.asyncio
    async def test_complete_onboarding_creates_student_when_missing(
        self, test_app, partial_user_token, partial_user, invitation_code, db_session
    ):
        """
        REGRESSION: User has school_id but no Student record.
        Onboarding should create Student instead of returning VAL_006.
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/onboarding/complete",
                headers={"Authorization": f"Bearer {partial_user_token}"},
                json={
                    "invitation_code": invitation_code.code,
                    "first_name": "Partial",
                    "last_name": "User",
                },
            )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
        data = response.json()
        assert "access_token" in data
        assert data["student"]["grade_level"] == invitation_code.grade_level

        # Verify Student record was created in DB
        result = await db_session.execute(
            sa_select(Student).where(Student.user_id == partial_user.id)
        )
        student = result.scalar_one_or_none()
        assert student is not None, "Student record should be created"
        assert student.school_id == invitation_code.school_id

    @pytest.mark.asyncio
    async def test_complete_onboarding_rejects_fully_onboarded(
        self, test_app, student_token, student_user, invitation_code
    ):
        """
        User has school_id AND Student record → VAL_006.
        Normal rejection path should still work.
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/onboarding/complete",
                headers={"Authorization": f"Bearer {student_token}"},
                json={
                    "invitation_code": invitation_code.code,
                    "first_name": "Test",
                    "last_name": "Student",
                },
            )

        assert response.status_code == 400
        assert "VAL_006" in response.text

    @pytest.mark.asyncio
    async def test_validate_code_allows_partial_state(
        self, test_app, partial_user_token, invitation_code
    ):
        """
        REGRESSION: validate-code should also allow partial state
        (school_id set, no Student).
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/onboarding/validate-code",
                headers={"Authorization": f"Bearer {partial_user_token}"},
                json={"code": invitation_code.code},
            )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
        data = response.json()
        assert data["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_code_rejects_fully_onboarded(
        self, test_app, student_token, invitation_code
    ):
        """
        User has school_id AND Student record → VAL_006 on validate too.
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/onboarding/validate-code",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"code": invitation_code.code},
            )

        assert response.status_code == 400
        assert "VAL_006" in response.text
