"""
Tests for Schools API (SUPER_ADMIN endpoints).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User, UserRole
from app.models.school import School
from app.core.security import get_password_hash, create_access_token


@pytest_asyncio.fixture
async def test_school(db_session: AsyncSession) -> School:
    """Create a test school."""
    school = School(
        name="Test School",
        code="test-school",
        email="test@school.com",
        is_active=True,
    )
    db_session.add(school)
    await db_session.commit()
    await db_session.refresh(school)
    return school


@pytest_asyncio.fixture
async def super_admin_user(db_session: AsyncSession, test_school: School) -> User:
    """Create a SUPER_ADMIN user for testing."""
    user = User(
        email="superadmin@test.com",
        password_hash=get_password_hash("password123"),
        first_name="Super",
        last_name="Admin",
        role=UserRole.SUPER_ADMIN,
        school_id=None,  # SUPER_ADMIN has no school_id
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def school_admin_user(db_session: AsyncSession, test_school: School) -> User:
    """Create a school ADMIN user for testing."""
    user = User(
        email="admin@test.com",
        password_hash=get_password_hash("password123"),
        first_name="School",
        last_name="Admin",
        role=UserRole.ADMIN,
        school_id=test_school.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def super_admin_token(super_admin_user: User) -> str:
    """Create access token for SUPER_ADMIN."""
    return create_access_token(data={"sub": str(super_admin_user.id)})


@pytest_asyncio.fixture
async def school_admin_token(school_admin_user: User) -> str:
    """Create access token for school ADMIN."""
    return create_access_token(data={"sub": str(school_admin_user.id)})


@pytest.mark.asyncio
async def test_list_schools_only_super_admin(
    db_session: AsyncSession,
    super_admin_token: str,
    school_admin_token: str,
    test_school: School,
):
    """
    Test that only SUPER_ADMIN can list schools.
    School ADMIN should get 403 Forbidden.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # SUPER_ADMIN can list schools
        response = await client.get(
            "/api/v1/admin/schools",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 200
        schools = response.json()
        assert len(schools) >= 1
        assert any(s["code"] == "test-school" for s in schools)

        # School ADMIN gets 403
        response = await client.get(
            "/api/v1/admin/schools",
            headers={"Authorization": f"Bearer {school_admin_token}"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_school_only_super_admin(
    db_session: AsyncSession,
    super_admin_token: str,
    school_admin_token: str,
):
    """
    Test that only SUPER_ADMIN can create schools.
    School ADMIN should get 403 Forbidden.
    """
    school_data = {
        "name": "New School",
        "code": "new-school",
        "email": "new@school.com",
        "description": "A new test school",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # SUPER_ADMIN can create school
        response = await client.post(
            "/api/v1/admin/schools",
            json=school_data,
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 201
        school = response.json()
        assert school["name"] == "New School"
        assert school["code"] == "new-school"
        assert school["is_active"] is True

        # School ADMIN gets 403
        response = await client.post(
            "/api/v1/admin/schools",
            json=school_data,
            headers={"Authorization": f"Bearer {school_admin_token}"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_school_unique_code(
    db_session: AsyncSession, super_admin_token: str, test_school: School
):
    """
    Test that creating a school with duplicate code returns 409 Conflict.
    """
    school_data = {
        "name": "Duplicate School",
        "code": "test-school",  # Already exists
        "email": "duplicate@school.com",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/admin/schools",
            json=school_data,
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_school(
    db_session: AsyncSession, super_admin_token: str, test_school: School
):
    """Test getting a specific school by ID."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/api/v1/admin/schools/{test_school.id}",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 200
        school = response.json()
        assert school["id"] == test_school.id
        assert school["code"] == "test-school"
        assert school["name"] == "Test School"


@pytest.mark.asyncio
async def test_get_school_not_found(db_session: AsyncSession, super_admin_token: str):
    """Test getting a non-existent school returns 404."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/admin/schools/99999",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_school(
    db_session: AsyncSession, super_admin_token: str, test_school: School
):
    """Test updating a school."""
    update_data = {"name": "Updated School Name", "email": "updated@school.com"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            f"/api/v1/admin/schools/{test_school.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 200
        school = response.json()
        assert school["name"] == "Updated School Name"
        assert school["email"] == "updated@school.com"
        assert school["code"] == "test-school"  # Code should not change


@pytest.mark.asyncio
async def test_block_unblock_school(
    db_session: AsyncSession, super_admin_token: str, test_school: School
):
    """Test blocking and unblocking a school."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Block school
        response = await client.patch(
            f"/api/v1/admin/schools/{test_school.id}/block",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 200
        school = response.json()
        assert school["is_active"] is False

        # Unblock school
        response = await client.patch(
            f"/api/v1/admin/schools/{test_school.id}/unblock",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 200
        school = response.json()
        assert school["is_active"] is True


@pytest.mark.asyncio
async def test_soft_delete_school(
    db_session: AsyncSession, super_admin_token: str, test_school: School
):
    """Test soft deleting a school."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Delete school
        response = await client.delete(
            f"/api/v1/admin/schools/{test_school.id}",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 204

        # School should not appear in list anymore
        response = await client.get(
            "/api/v1/admin/schools",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 200
        schools = response.json()
        assert not any(s["id"] == test_school.id for s in schools)

        # Trying to get deleted school should return 404
        response = await client.get(
            f"/api/v1/admin/schools/{test_school.id}",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_code_validation(db_session: AsyncSession, super_admin_token: str):
    """Test that school code validation works correctly."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Valid code
        response = await client.post(
            "/api/v1/admin/schools",
            json={
                "name": "Valid School",
                "code": "valid-school-123",
                "email": "valid@school.com",
            },
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 201

        # Invalid code (uppercase)
        response = await client.post(
            "/api/v1/admin/schools",
            json={
                "name": "Invalid School",
                "code": "Invalid-School",
                "email": "invalid@school.com",
            },
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 422

        # Invalid code (special characters)
        response = await client.post(
            "/api/v1/admin/schools",
            json={
                "name": "Invalid School 2",
                "code": "invalid@school!",
                "email": "invalid2@school.com",
            },
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 422
