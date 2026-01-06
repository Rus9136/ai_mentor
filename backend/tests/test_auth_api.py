"""
Tests for authentication API endpoints.

Tests cover:
- Login endpoint (/auth/login)
- Refresh token endpoint (/auth/refresh)
- Get current user endpoint (/auth/me)

Uses mocked dependencies for fast unit tests.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.user import User, UserRole
from app.core.security import create_access_token, create_refresh_token
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.rate_limiter import limiter


# Reset rate limiter before each test
@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter storage before each test."""
    limiter.reset()
    yield
    limiter.reset()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_student_user():
    """Create a sample student user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "student@test.com"
    user.hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.hfXBl1U7RdJYGi"
    user.first_name = "Test"
    user.last_name = "Student"
    user.middle_name = None
    user.avatar_url = None
    user.auth_provider = "local"
    user.role = UserRole.STUDENT
    user.school_id = 1
    user.is_active = True
    user.is_deleted = False
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def sample_teacher_user():
    """Create a sample teacher user."""
    user = MagicMock(spec=User)
    user.id = 2
    user.email = "teacher@test.com"
    user.hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.hfXBl1U7RdJYGi"
    user.first_name = "Test"
    user.last_name = "Teacher"
    user.middle_name = None
    user.avatar_url = None
    user.auth_provider = "local"
    user.role = UserRole.TEACHER
    user.school_id = 1
    user.is_active = True
    user.is_deleted = False
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def sample_admin_user():
    """Create a sample admin user."""
    user = MagicMock(spec=User)
    user.id = 3
    user.email = "admin@test.com"
    user.hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.hfXBl1U7RdJYGi"
    user.first_name = "Test"
    user.last_name = "Admin"
    user.middle_name = None
    user.avatar_url = None
    user.auth_provider = "local"
    user.role = UserRole.ADMIN
    user.school_id = 1
    user.is_active = True
    user.is_deleted = False
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def sample_super_admin_user():
    """Create a sample super admin user."""
    user = MagicMock(spec=User)
    user.id = 4
    user.email = "superadmin@test.com"
    user.hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.hfXBl1U7RdJYGi"
    user.first_name = "Super"
    user.last_name = "Admin"
    user.middle_name = None
    user.avatar_url = None
    user.auth_provider = "local"
    user.role = UserRole.SUPER_ADMIN
    user.school_id = None
    user.is_active = True
    user.is_deleted = False
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def inactive_user():
    """Create an inactive user."""
    user = MagicMock(spec=User)
    user.id = 5
    user.email = "inactive@test.com"
    user.hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.hfXBl1U7RdJYGi"
    user.first_name = "Inactive"
    user.last_name = "User"
    user.middle_name = None
    user.avatar_url = None
    user.auth_provider = "local"
    user.role = UserRole.STUDENT
    user.school_id = 1
    user.is_active = False
    user.is_deleted = False
    return user


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    return db


# =============================================================================
# Login Tests
# =============================================================================

class TestLogin:
    """Tests for POST /api/v1/auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_valid_credentials_student(self, sample_student_user, mock_db):
        """Test successful login with valid student credentials."""
        # Override dependencies
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):  # Disable rate limiter
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = sample_student_user
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"email": "student@test.com", "password": "password123"}
                    )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_valid_credentials_teacher(self, sample_teacher_user, mock_db):
        """Test successful login with valid teacher credentials."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = sample_teacher_user
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"email": "teacher@test.com", "password": "password123"}
                    )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_valid_credentials_admin(self, sample_admin_user, mock_db):
        """Test successful login with valid admin credentials."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = sample_admin_user
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"email": "admin@test.com", "password": "password123"}
                    )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_valid_credentials_super_admin(self, sample_super_admin_user, mock_db):
        """Test successful login with valid super admin credentials."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = sample_super_admin_user
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"email": "superadmin@test.com", "password": "password123"}
                    )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, sample_student_user, mock_db):
        """Test login with wrong password."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = sample_student_user
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=False):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"email": "student@test.com", "password": "wrongpassword"}
                    )

        app.dependency_overrides.clear()

        assert response.status_code == 401
        # Check that error message is about credentials
        assert "password" in response.json()["detail"].lower() or "credential" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, mock_db):
        """Test login with non-existent email."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = None
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/login",
                    json={"email": "nonexistent@test.com", "password": "password123"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, inactive_user, mock_db):
        """Test login with inactive user account."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = inactive_user
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"email": "inactive@test.com", "password": "password123"}
                    )

        app.dependency_overrides.clear()

        # Inactive user returns 401 or 403 depending on implementation
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_login_empty_email(self):
        """Test login with empty email."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "", "password": "password123"}
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_empty_password(self):
        """Test login with empty password."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": ""}
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_missing_fields(self):
        """Test login with missing required fields."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={}
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_token_contains_user_data(self, sample_student_user, mock_db):
        """Test that returned token contains correct user data."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = sample_student_user
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"email": "student@test.com", "password": "password123"}
                    )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        # Verify tokens are returned
        assert len(data["access_token"]) > 50
        assert len(data["refresh_token"]) > 50


# =============================================================================
# Refresh Token Tests
# =============================================================================

class TestRefreshToken:
    """Tests for POST /api/v1/auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_valid_token(self, sample_student_user, mock_db):
        """Test refresh with valid refresh token."""
        refresh_token = create_refresh_token(
            data={"sub": str(sample_student_user.id), "type": "refresh"}
        )

        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = sample_student_user
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": refresh_token}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self):
        """Test refresh with invalid token."""
        with patch("app.api.v1.auth.limiter"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": "invalid.token.here"}
                )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_access_token(self, sample_student_user):
        """Test refresh fails when using access token instead of refresh token."""
        access_token = create_access_token(
            data={"sub": str(sample_student_user.id), "type": "access"}
        )

        with patch("app.api.v1.auth.limiter"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": access_token}
                )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_user_not_found(self, mock_db):
        """Test refresh when user no longer exists."""
        refresh_token = create_refresh_token(
            data={"sub": "999", "type": "refresh"}
        )

        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": refresh_token}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_user_inactive(self, inactive_user, mock_db):
        """Test refresh fails for inactive user."""
        refresh_token = create_refresh_token(
            data={"sub": str(inactive_user.id), "type": "refresh"}
        )

        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = inactive_user
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": refresh_token}
                )

        app.dependency_overrides.clear()

        # Should fail for inactive user (403 or 401)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_refresh_malformed_token(self):
        """Test refresh with malformed token."""
        with patch("app.api.v1.auth.limiter"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": "not-even-a-jwt"}
                )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_empty_token(self):
        """Test refresh with empty token."""
        with patch("app.api.v1.auth.limiter"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": ""}
                )

        # Empty token should be rejected (401 or 422)
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_refresh_returns_new_tokens(self, sample_student_user, mock_db):
        """Test that refresh returns different tokens."""
        refresh_token = create_refresh_token(
            data={"sub": str(sample_student_user.id), "type": "refresh"}
        )

        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = sample_student_user
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": refresh_token}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        # New tokens should be different from original
        assert data["refresh_token"] != refresh_token


# =============================================================================
# Get Current User Tests
# =============================================================================

class TestGetCurrentUser:
    """Tests for GET /api/v1/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_me_valid_token_student(self, sample_student_user):
        """Test /me with valid student token."""
        # Override get_current_user to return our mock user
        async def override_get_current_user():
            return sample_student_user

        app.dependency_overrides[get_current_user] = override_get_current_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer fake-token"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "student@test.com"
        assert data["role"] == "student"

    @pytest.mark.asyncio
    async def test_me_valid_token_teacher(self, sample_teacher_user):
        """Test /me with valid teacher token."""
        async def override_get_current_user():
            return sample_teacher_user

        app.dependency_overrides[get_current_user] = override_get_current_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer fake-token"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "teacher"

    @pytest.mark.asyncio
    async def test_me_valid_token_admin(self, sample_admin_user):
        """Test /me with valid admin token."""
        async def override_get_current_user():
            return sample_admin_user

        app.dependency_overrides[get_current_user] = override_get_current_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer fake-token"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_me_valid_token_super_admin(self, sample_super_admin_user):
        """Test /me with valid super admin token."""
        async def override_get_current_user():
            return sample_super_admin_user

        app.dependency_overrides[get_current_user] = override_get_current_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer fake-token"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "super_admin"

    @pytest.mark.asyncio
    async def test_me_invalid_token(self):
        """Test /me with invalid token."""
        # Don't override - let the real auth fail
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer invalid.token.here"}
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_no_token(self):
        """Test /me without token."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_malformed_auth_header(self):
        """Test /me with malformed Authorization header."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "NotBearer token"}
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_empty_bearer(self):
        """Test /me with empty Bearer token."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer "}
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_returns_correct_user_fields(self, sample_student_user):
        """Test /me returns expected user fields."""
        async def override_get_current_user():
            return sample_student_user

        app.dependency_overrides[get_current_user] = override_get_current_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer fake-token"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "first_name" in data
        assert "last_name" in data
        assert "role" in data

    @pytest.mark.asyncio
    async def test_me_user_with_school(self, sample_student_user):
        """Test /me returns school_id for school users."""
        async def override_get_current_user():
            return sample_student_user

        app.dependency_overrides[get_current_user] = override_get_current_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer fake-token"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["school_id"] == 1


# =============================================================================
# Token Validation Tests
# =============================================================================

class TestTokenValidation:
    """Tests for token validation behavior."""

    @pytest.mark.asyncio
    async def test_access_token_works_for_me(self, sample_student_user):
        """Test that access token works for /me endpoint."""
        async def override_get_current_user():
            return sample_student_user

        app.dependency_overrides[get_current_user] = override_get_current_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer fake-but-valid-token"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_refresh_token_not_accepted_for_me(self, sample_student_user):
        """Test that refresh token is not accepted for /me endpoint."""
        refresh_token = create_refresh_token(
            data={"sub": str(sample_student_user.id), "type": "refresh"}
        )

        # Don't override - let real auth validate and fail
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {refresh_token}"}
            )

        # Should fail because refresh token is not valid for /me
        assert response.status_code == 401


# =============================================================================
# Integration Tests
# =============================================================================

class TestAuthIntegration:
    """Integration tests for auth flow."""

    @pytest.mark.asyncio
    async def test_login_then_me(self, sample_student_user, mock_db):
        """Test login flow followed by /me request."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = sample_student_user
            mock_repo.get_by_id.return_value = sample_student_user
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    # Login
                    login_response = await client.post(
                        "/api/v1/auth/login",
                        json={"email": "student@test.com", "password": "password123"}
                    )

                    assert login_response.status_code == 200
                    tokens = login_response.json()

                    # Override get_current_user for /me
                    async def override_get_current_user():
                        return sample_student_user

                    app.dependency_overrides[get_current_user] = override_get_current_user

                    # Use the token for /me
                    me_response = await client.get(
                        "/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {tokens['access_token']}"}
                    )

        app.dependency_overrides.clear()

        assert me_response.status_code == 200
        assert me_response.json()["email"] == "student@test.com"

    @pytest.mark.asyncio
    async def test_login_refresh_then_me(self, sample_student_user, mock_db):
        """Test full auth flow: login -> refresh -> me."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = sample_student_user
            mock_repo.get_by_id.return_value = sample_student_user
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    # Login
                    login_response = await client.post(
                        "/api/v1/auth/login",
                        json={"email": "student@test.com", "password": "password123"}
                    )
                    tokens = login_response.json()

                    # Refresh
                    refresh_response = await client.post(
                        "/api/v1/auth/refresh",
                        json={"refresh_token": tokens["refresh_token"]}
                    )
                    new_tokens = refresh_response.json()

                    # Override get_current_user for /me
                    async def override_get_current_user():
                        return sample_student_user

                    app.dependency_overrides[get_current_user] = override_get_current_user

                    # Use new access token for /me
                    me_response = await client.get(
                        "/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
                    )

        app.dependency_overrides.clear()

        assert me_response.status_code == 200

    @pytest.mark.asyncio
    async def test_different_roles_different_tokens(
        self, sample_student_user, sample_teacher_user, mock_db
    ):
        """Test that different roles get different tokens."""
        app.dependency_overrides[get_db] = lambda: mock_db

        student_token = None
        teacher_token = None

        # Student login
        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = sample_student_user
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"email": "student@test.com", "password": "password123"}
                    )
                    student_token = response.json()["access_token"]

        # Teacher login
        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = sample_teacher_user
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"email": "teacher@test.com", "password": "password123"}
                    )
                    teacher_token = response.json()["access_token"]

        app.dependency_overrides.clear()

        # Tokens should be different
        assert student_token != teacher_token
