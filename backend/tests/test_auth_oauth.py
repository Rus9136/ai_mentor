"""
Tests for OAuth authentication endpoints.

Tests cover:
- Google OAuth login (/auth/google)
- Invitation code validation (/auth/onboarding/validate-code)
- Onboarding completion (/auth/onboarding/complete)

Uses mocks instead of real database connections.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token
from app.core.rate_limiter import limiter
from app.api.dependencies import get_current_user
from app.models.user import User, UserRole, AuthProvider
from app.models.student import Student
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.invitation_code import InvitationCode


# ========== Fixtures ==========

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter storage before each test."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


# ========== Mock Classes ==========

@dataclass
class MockGoogleUserInfo:
    """Mock Google user info returned by GoogleAuthService."""
    google_id: str
    email: str
    email_verified: bool
    first_name: str | None
    last_name: str | None
    avatar_url: str | None = None


class MockGoogleAuthService:
    """Mock GoogleAuthService for tests without real Google API."""

    def __init__(
        self,
        user_info: MockGoogleUserInfo | None = None,
        should_fail: bool = False,
        error_message: str = "Invalid token"
    ):
        self.user_info = user_info or MockGoogleUserInfo(
            google_id="google_123456789",
            email="newuser@gmail.com",
            email_verified=True,
            first_name="New",
            last_name="User",
            avatar_url="https://example.com/avatar.jpg"
        )
        self.should_fail = should_fail
        self.error_message = error_message
        self.verify_called = False
        self.last_token = None

    async def verify_token(self, id_token: str):
        """Mock verify_token method."""
        self.verify_called = True
        self.last_token = id_token

        if self.should_fail:
            from app.services.google_auth_service import GoogleAuthError
            raise GoogleAuthError(self.error_message)

        return self.user_info


# ========== User Mock Fixtures ==========

@pytest.fixture
def mock_new_user():
    """Mock for a newly created user."""
    user = MagicMock(spec=User)
    user.id = 100
    user.email = "newuser@gmail.com"
    user.first_name = "New"
    user.last_name = "User"
    user.middle_name = None
    user.avatar_url = "https://example.com/avatar.jpg"
    user.role = UserRole.STUDENT
    user.school_id = None
    user.google_id = "google_123456789"
    user.auth_provider = AuthProvider.GOOGLE
    user.is_active = True
    user.is_verified = True
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_existing_user_without_school():
    """Mock for an existing user without school."""
    user = MagicMock(spec=User)
    user.id = 101
    user.email = "existing@gmail.com"
    user.first_name = "Existing"
    user.last_name = "User"
    user.middle_name = None
    user.avatar_url = None
    user.role = UserRole.STUDENT
    user.school_id = None
    user.google_id = "existing_google_id"
    user.auth_provider = AuthProvider.GOOGLE
    user.is_active = True
    user.is_verified = True
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_existing_user_with_school():
    """Mock for an existing user with school."""
    user = MagicMock(spec=User)
    user.id = 102
    user.email = "student@school.com"
    user.first_name = "Student"
    user.last_name = "WithSchool"
    user.middle_name = None
    user.avatar_url = None
    user.role = UserRole.STUDENT
    user.school_id = 1
    user.google_id = "student_google_id"
    user.auth_provider = AuthProvider.GOOGLE
    user.is_active = True
    user.is_verified = True
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_inactive_user():
    """Mock for an inactive user."""
    user = MagicMock(spec=User)
    user.id = 103
    user.email = "inactive@test.com"
    user.first_name = "Inactive"
    user.last_name = "User"
    user.middle_name = None
    user.avatar_url = None
    user.role = UserRole.STUDENT
    user.school_id = None
    user.google_id = "inactive_google_id"
    user.auth_provider = AuthProvider.GOOGLE
    user.is_active = False
    user.is_verified = True
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_teacher_user():
    """Mock for a teacher user."""
    user = MagicMock(spec=User)
    user.id = 104
    user.email = "teacher@school.com"
    user.first_name = "Teacher"
    user.last_name = "User"
    user.middle_name = None
    user.avatar_url = None
    user.role = UserRole.TEACHER
    user.school_id = 1
    user.google_id = None
    user.auth_provider = AuthProvider.LOCAL
    user.is_active = True
    user.is_verified = True
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


# ========== Invitation Code Mock Fixtures ==========

@pytest.fixture
def mock_school():
    """Mock school."""
    school = MagicMock(spec=School)
    school.id = 1
    school.name = "Test School"
    school.code = "TST001"
    return school


@pytest.fixture
def mock_school_class(mock_school):
    """Mock school class."""
    school_class = MagicMock(spec=SchoolClass)
    school_class.id = 1
    school_class.name = "7A"
    school_class.grade_level = 7
    school_class.school_id = mock_school.id
    return school_class


@pytest.fixture
def mock_valid_invitation_code(mock_school, mock_school_class):
    """Mock valid invitation code."""
    code = MagicMock(spec=InvitationCode)
    code.id = 1
    code.code = "VALID123"
    code.school_id = mock_school.id
    code.school = mock_school
    code.class_id = mock_school_class.id
    code.school_class = mock_school_class
    code.grade_level = 7
    code.max_uses = 100
    code.uses_count = 5
    code.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    code.is_active = True
    return code


@pytest.fixture
def mock_expired_invitation_code(mock_school, mock_school_class):
    """Mock expired invitation code."""
    code = MagicMock(spec=InvitationCode)
    code.id = 2
    code.code = "EXPIRED1"
    code.school_id = mock_school.id
    code.school = mock_school
    code.class_id = mock_school_class.id
    code.school_class = mock_school_class
    code.grade_level = 7
    code.max_uses = 100
    code.uses_count = 5
    code.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    code.is_active = True
    return code


@pytest.fixture
def mock_exhausted_invitation_code(mock_school, mock_school_class):
    """Mock exhausted invitation code."""
    code = MagicMock(spec=InvitationCode)
    code.id = 3
    code.code = "EXHAUST1"
    code.school_id = mock_school.id
    code.school = mock_school
    code.class_id = mock_school_class.id
    code.school_class = mock_school_class
    code.grade_level = 7
    code.max_uses = 10
    code.uses_count = 10
    code.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    code.is_active = True
    return code


@pytest.fixture
def mock_student():
    """Mock student record."""
    student = MagicMock(spec=Student)
    student.id = 1
    student.user_id = 100
    student.school_id = 1
    student.student_code = "STU72026001"
    student.grade_level = 7
    student.birth_date = None
    return student


# ========== Google Login Tests ==========

class TestGoogleLogin:
    """Tests for POST /api/v1/auth/google endpoint."""

    @pytest.mark.asyncio
    async def test_google_login_new_user_creates_student(self, mock_db, mock_new_user):
        """Test that new Google user is created with STUDENT role."""
        app.dependency_overrides[get_db] = lambda: mock_db

        mock_service = MockGoogleAuthService(
            user_info=MockGoogleUserInfo(
                google_id="new_google_id_123",
                email="brandnew@gmail.com",
                email_verified=True,
                first_name="Brand",
                last_name="New",
            )
        )

        with patch("app.api.v1.auth_oauth.GoogleAuthService", return_value=mock_service), \
             patch("app.api.v1.auth_oauth.settings") as mock_settings, \
             patch("app.api.v1.auth_oauth.UserRepository") as mock_repo_class:

            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"

            mock_repo = AsyncMock()
            mock_repo.get_by_google_id.return_value = None
            mock_repo.get_by_email.return_value = None

            # Return a proper mock user on create
            created_user = MagicMock(spec=User)
            created_user.id = 100
            created_user.email = "brandnew@gmail.com"
            created_user.first_name = "Brand"
            created_user.last_name = "New"
            created_user.middle_name = None
            created_user.avatar_url = None
            created_user.role = UserRole.STUDENT
            created_user.school_id = None
            created_user.google_id = "new_google_id_123"
            created_user.auth_provider = AuthProvider.GOOGLE
            created_user.is_active = True
            created_user.is_verified = True
            created_user.created_at = datetime.now(timezone.utc)
            created_user.updated_at = datetime.now(timezone.utc)

            mock_repo.create.return_value = created_user
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/google",
                    json={"id_token": "valid_google_token"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["requires_onboarding"] is True
        assert data["user"]["role"] == UserRole.STUDENT.value
        assert data["user"]["email"] == "brandnew@gmail.com"

    @pytest.mark.asyncio
    async def test_google_login_existing_by_google_id(self, mock_db, mock_existing_user_without_school):
        """Test login for existing user found by google_id."""
        app.dependency_overrides[get_db] = lambda: mock_db

        mock_service = MockGoogleAuthService(
            user_info=MockGoogleUserInfo(
                google_id=mock_existing_user_without_school.google_id,
                email=mock_existing_user_without_school.email,
                email_verified=True,
                first_name="Google",
                last_name="User",
            )
        )

        with patch("app.api.v1.auth_oauth.GoogleAuthService", return_value=mock_service), \
             patch("app.api.v1.auth_oauth.settings") as mock_settings, \
             patch("app.api.v1.auth_oauth.UserRepository") as mock_repo_class:

            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"

            mock_repo = AsyncMock()
            mock_repo.get_by_google_id.return_value = mock_existing_user_without_school
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/google",
                    json={"id_token": "valid_google_token"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["id"] == mock_existing_user_without_school.id
        assert data["requires_onboarding"] is True

    @pytest.mark.asyncio
    async def test_google_login_existing_by_email_updates_google_id(self, mock_db, mock_existing_user_with_school):
        """Test that existing user found by email gets google_id updated."""
        app.dependency_overrides[get_db] = lambda: mock_db

        # User exists by email but not by google_id
        user_without_google = MagicMock(spec=User)
        user_without_google.id = mock_existing_user_with_school.id
        user_without_google.email = mock_existing_user_with_school.email
        user_without_google.first_name = mock_existing_user_with_school.first_name
        user_without_google.last_name = mock_existing_user_with_school.last_name
        user_without_google.middle_name = None
        user_without_google.avatar_url = None
        user_without_google.role = UserRole.STUDENT
        user_without_google.school_id = 1
        user_without_google.google_id = None  # No google_id yet
        user_without_google.auth_provider = AuthProvider.LOCAL
        user_without_google.is_active = True
        user_without_google.is_verified = True
        user_without_google.created_at = datetime.now(timezone.utc)
        user_without_google.updated_at = datetime.now(timezone.utc)

        mock_service = MockGoogleAuthService(
            user_info=MockGoogleUserInfo(
                google_id="new_google_id_for_existing",
                email=user_without_google.email,
                email_verified=True,
                first_name="Test",
                last_name="Student",
            )
        )

        with patch("app.api.v1.auth_oauth.GoogleAuthService", return_value=mock_service), \
             patch("app.api.v1.auth_oauth.settings") as mock_settings, \
             patch("app.api.v1.auth_oauth.UserRepository") as mock_repo_class:

            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"

            mock_repo = AsyncMock()
            mock_repo.get_by_google_id.return_value = None
            mock_repo.get_by_email.return_value = user_without_google
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/google",
                    json={"id_token": "valid_google_token"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["id"] == user_without_google.id
        assert data["requires_onboarding"] is False  # Has school

    @pytest.mark.asyncio
    async def test_google_login_existing_with_school_no_onboarding(self, mock_db, mock_existing_user_with_school):
        """Test that user with school doesn't require onboarding."""
        app.dependency_overrides[get_db] = lambda: mock_db

        mock_service = MockGoogleAuthService(
            user_info=MockGoogleUserInfo(
                google_id=mock_existing_user_with_school.google_id,
                email=mock_existing_user_with_school.email,
                email_verified=True,
                first_name="Test",
                last_name="Student",
            )
        )

        with patch("app.api.v1.auth_oauth.GoogleAuthService", return_value=mock_service), \
             patch("app.api.v1.auth_oauth.settings") as mock_settings, \
             patch("app.api.v1.auth_oauth.UserRepository") as mock_repo_class:

            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"

            mock_repo = AsyncMock()
            mock_repo.get_by_google_id.return_value = mock_existing_user_with_school
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/google",
                    json={"id_token": "valid_google_token"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["requires_onboarding"] is False

    @pytest.mark.asyncio
    async def test_google_login_invalid_token(self, mock_db):
        """Test login fails with invalid Google token."""
        app.dependency_overrides[get_db] = lambda: mock_db

        mock_service = MockGoogleAuthService(
            should_fail=True,
            error_message="Invalid token"
        )

        with patch("app.api.v1.auth_oauth.GoogleAuthService", return_value=mock_service), \
             patch("app.api.v1.auth_oauth.settings") as mock_settings:

            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/google",
                    json={"id_token": "invalid_token"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_google_login_inactive_user(self, mock_db, mock_inactive_user):
        """Test login fails for inactive user."""
        app.dependency_overrides[get_db] = lambda: mock_db

        mock_service = MockGoogleAuthService(
            user_info=MockGoogleUserInfo(
                google_id=mock_inactive_user.google_id,
                email=mock_inactive_user.email,
                email_verified=True,
                first_name="Inactive",
                last_name="User",
            )
        )

        with patch("app.api.v1.auth_oauth.GoogleAuthService", return_value=mock_service), \
             patch("app.api.v1.auth_oauth.settings") as mock_settings, \
             patch("app.api.v1.auth_oauth.UserRepository") as mock_repo_class:

            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"

            mock_repo = AsyncMock()
            mock_repo.get_by_google_id.return_value = mock_inactive_user
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/google",
                    json={"id_token": "valid_google_token"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 403
        assert "User account is inactive" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_google_login_oauth_not_configured(self, mock_db):
        """Test login fails when Google OAuth is not configured."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth_oauth.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = None

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/google",
                    json={"id_token": "some_token"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 503
        assert "Google OAuth is not configured" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_google_login_returns_valid_tokens(self, mock_db, mock_new_user):
        """Test that Google login returns valid JWT tokens."""
        app.dependency_overrides[get_db] = lambda: mock_db

        mock_service = MockGoogleAuthService()

        with patch("app.api.v1.auth_oauth.GoogleAuthService", return_value=mock_service), \
             patch("app.api.v1.auth_oauth.settings") as mock_settings, \
             patch("app.api.v1.auth_oauth.UserRepository") as mock_repo_class:

            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"

            mock_repo = AsyncMock()
            mock_repo.get_by_google_id.return_value = None
            mock_repo.get_by_email.return_value = None
            mock_repo.create.return_value = mock_new_user
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/google",
                    json={"id_token": "valid_google_token"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert isinstance(data["refresh_token"], str)
        assert len(data["refresh_token"]) > 0
        assert data["token_type"] == "bearer"


# ========== Validate Invitation Code Tests ==========

class TestValidateInvitationCode:
    """Tests for POST /api/v1/auth/onboarding/validate-code endpoint."""

    @pytest.mark.asyncio
    async def test_validate_code_valid(
        self,
        mock_db,
        mock_existing_user_without_school,
        mock_valid_invitation_code
    ):
        """Test validating a valid invitation code."""
        # Create token for user without school
        token = create_access_token({
            "sub": str(mock_existing_user_without_school.id),
            "email": mock_existing_user_without_school.email,
            "role": mock_existing_user_without_school.role.value,
            "school_id": mock_existing_user_without_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_without_school

        with patch("app.api.v1.auth_oauth.InvitationCodeRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.validate_code.return_value = (True, None, mock_valid_invitation_code)
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/onboarding/validate-code",
                    json={"code": mock_valid_invitation_code.code},
                    headers={"Authorization": f"Bearer {token}"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["school"]["id"] == mock_valid_invitation_code.school_id
        assert data["school_class"]["id"] == mock_valid_invitation_code.class_id

    @pytest.mark.asyncio
    async def test_validate_code_invalid(self, mock_db, mock_existing_user_without_school):
        """Test validating an invalid invitation code."""
        token = create_access_token({
            "sub": str(mock_existing_user_without_school.id),
            "email": mock_existing_user_without_school.email,
            "role": mock_existing_user_without_school.role.value,
            "school_id": mock_existing_user_without_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_without_school

        with patch("app.api.v1.auth_oauth.InvitationCodeRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.validate_code.return_value = (False, "Invalid invitation code", None)
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/onboarding/validate-code",
                    json={"code": "INVALID_CODE"},
                    headers={"Authorization": f"Bearer {token}"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_validate_code_expired(
        self,
        mock_db,
        mock_existing_user_without_school,
        mock_expired_invitation_code
    ):
        """Test validating an expired invitation code."""
        token = create_access_token({
            "sub": str(mock_existing_user_without_school.id),
            "email": mock_existing_user_without_school.email,
            "role": mock_existing_user_without_school.role.value,
            "school_id": mock_existing_user_without_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_without_school

        with patch("app.api.v1.auth_oauth.InvitationCodeRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.validate_code.return_value = (False, "Code has expired", None)
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/onboarding/validate-code",
                    json={"code": mock_expired_invitation_code.code},
                    headers={"Authorization": f"Bearer {token}"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_validate_code_exhausted(
        self,
        mock_db,
        mock_existing_user_without_school,
        mock_exhausted_invitation_code
    ):
        """Test validating an exhausted invitation code."""
        token = create_access_token({
            "sub": str(mock_existing_user_without_school.id),
            "email": mock_existing_user_without_school.email,
            "role": mock_existing_user_without_school.role.value,
            "school_id": mock_existing_user_without_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_without_school

        with patch("app.api.v1.auth_oauth.InvitationCodeRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.validate_code.return_value = (False, "Code usage limit reached", None)
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/onboarding/validate-code",
                    json={"code": mock_exhausted_invitation_code.code},
                    headers={"Authorization": f"Bearer {token}"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_validate_code_returns_school_info(
        self,
        mock_db,
        mock_existing_user_without_school,
        mock_valid_invitation_code,
        mock_school
    ):
        """Test that validation returns school information."""
        token = create_access_token({
            "sub": str(mock_existing_user_without_school.id),
            "email": mock_existing_user_without_school.email,
            "role": mock_existing_user_without_school.role.value,
            "school_id": mock_existing_user_without_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_without_school

        with patch("app.api.v1.auth_oauth.InvitationCodeRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.validate_code.return_value = (True, None, mock_valid_invitation_code)
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/onboarding/validate-code",
                    json={"code": mock_valid_invitation_code.code},
                    headers={"Authorization": f"Bearer {token}"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["school"]["name"] == mock_school.name
        assert data["school"]["code"] == mock_school.code

    @pytest.mark.asyncio
    async def test_validate_code_returns_class_info(
        self,
        mock_db,
        mock_existing_user_without_school,
        mock_valid_invitation_code,
        mock_school_class
    ):
        """Test that validation returns class information."""
        token = create_access_token({
            "sub": str(mock_existing_user_without_school.id),
            "email": mock_existing_user_without_school.email,
            "role": mock_existing_user_without_school.role.value,
            "school_id": mock_existing_user_without_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_without_school

        with patch("app.api.v1.auth_oauth.InvitationCodeRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.validate_code.return_value = (True, None, mock_valid_invitation_code)
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/onboarding/validate-code",
                    json={"code": mock_valid_invitation_code.code},
                    headers={"Authorization": f"Bearer {token}"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["school_class"]["name"] == mock_school_class.name
        assert data["school_class"]["grade_level"] == mock_school_class.grade_level

    @pytest.mark.asyncio
    async def test_validate_code_not_student_role(
        self,
        mock_db,
        mock_teacher_user,
        mock_valid_invitation_code
    ):
        """Test that non-students cannot validate codes."""
        token = create_access_token({
            "sub": str(mock_teacher_user.id),
            "email": mock_teacher_user.email,
            "role": mock_teacher_user.role.value,
            "school_id": mock_teacher_user.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_teacher_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/onboarding/validate-code",
                json={"code": mock_valid_invitation_code.code},
                headers={"Authorization": f"Bearer {token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 403
        assert "Only students can use invitation codes" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_validate_code_already_has_school(
        self,
        mock_db,
        mock_existing_user_with_school,
        mock_valid_invitation_code
    ):
        """Test that students with school cannot validate codes."""
        token = create_access_token({
            "sub": str(mock_existing_user_with_school.id),
            "email": mock_existing_user_with_school.email,
            "role": mock_existing_user_with_school.role.value,
            "school_id": mock_existing_user_with_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_with_school

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/onboarding/validate-code",
                json={"code": mock_valid_invitation_code.code},
                headers={"Authorization": f"Bearer {token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "User already belongs to a school" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_validate_code_no_auth(self, mock_db, mock_valid_invitation_code):
        """Test that unauthenticated users cannot validate codes."""
        app.dependency_overrides[get_db] = lambda: mock_db
        # Don't override get_current_user - let it fail

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/onboarding/validate-code",
                json={"code": mock_valid_invitation_code.code}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 401


# ========== Complete Onboarding Tests ==========

class TestCompleteOnboarding:
    """Tests for POST /api/v1/auth/onboarding/complete endpoint."""

    @pytest.mark.asyncio
    async def test_complete_onboarding_success(
        self,
        mock_db,
        mock_existing_user_without_school,
        mock_valid_invitation_code,
        mock_student
    ):
        """Test successful onboarding completion."""
        token = create_access_token({
            "sub": str(mock_existing_user_without_school.id),
            "email": mock_existing_user_without_school.email,
            "role": mock_existing_user_without_school.role.value,
            "school_id": mock_existing_user_without_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_without_school

        with patch("app.api.v1.auth_oauth.InvitationCodeRepository") as mock_code_repo_class, \
             patch("app.api.v1.auth_oauth.UserRepository") as mock_user_repo_class, \
             patch("app.api.v1.auth_oauth.StudentRepository") as mock_student_repo_class, \
             patch("app.repositories.school_class_repo.SchoolClassRepository") as mock_class_repo_class:

            # Setup code repo
            mock_code_repo = AsyncMock()
            mock_code_repo.validate_code.return_value = (True, None, mock_valid_invitation_code)
            mock_code_repo.use_code.return_value = None
            mock_code_repo_class.return_value = mock_code_repo

            # Setup user repo
            mock_user_repo = AsyncMock()
            mock_user_repo.update.return_value = mock_existing_user_without_school
            mock_user_repo_class.return_value = mock_user_repo

            # Setup student repo
            mock_student_repo = AsyncMock()
            mock_student_repo.get_by_user_id.return_value = None
            mock_student_repo.generate_student_code.return_value = "STU72026001"
            mock_student_repo.create.return_value = mock_student
            mock_student_repo_class.return_value = mock_student_repo

            # Setup class repo
            mock_class_repo = AsyncMock()
            mock_class_repo.add_students.return_value = None
            mock_class_repo_class.return_value = mock_class_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/onboarding/complete",
                    json={
                        "invitation_code": mock_valid_invitation_code.code,
                        "first_name": "Новый",
                        "last_name": "Ученик",
                        "middle_name": "Тестович",
                        "birth_date": "2010-05-15"
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["student"]["grade_level"] == mock_valid_invitation_code.grade_level

    @pytest.mark.asyncio
    async def test_complete_onboarding_invalid_code(
        self,
        mock_db,
        mock_existing_user_without_school
    ):
        """Test onboarding fails with invalid code."""
        token = create_access_token({
            "sub": str(mock_existing_user_without_school.id),
            "email": mock_existing_user_without_school.email,
            "role": mock_existing_user_without_school.role.value,
            "school_id": mock_existing_user_without_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_without_school

        with patch("app.api.v1.auth_oauth.InvitationCodeRepository") as mock_code_repo_class:
            mock_code_repo = AsyncMock()
            mock_code_repo.validate_code.return_value = (False, "Code not found", None)
            mock_code_repo_class.return_value = mock_code_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/onboarding/complete",
                    json={
                        "invitation_code": "INVALID_CODE",
                        "first_name": "Новый",
                        "last_name": "Ученик",
                        "birth_date": "2010-05-15"
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "Invalid invitation code" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_complete_onboarding_expired_code(
        self,
        mock_db,
        mock_existing_user_without_school,
        mock_expired_invitation_code
    ):
        """Test onboarding fails with expired code."""
        token = create_access_token({
            "sub": str(mock_existing_user_without_school.id),
            "email": mock_existing_user_without_school.email,
            "role": mock_existing_user_without_school.role.value,
            "school_id": mock_existing_user_without_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_without_school

        with patch("app.api.v1.auth_oauth.InvitationCodeRepository") as mock_code_repo_class:
            mock_code_repo = AsyncMock()
            mock_code_repo.validate_code.return_value = (False, "Code has expired", None)
            mock_code_repo_class.return_value = mock_code_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/onboarding/complete",
                    json={
                        "invitation_code": mock_expired_invitation_code.code,
                        "first_name": "Новый",
                        "last_name": "Ученик",
                        "birth_date": "2010-05-15"
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_complete_onboarding_not_student_role(
        self,
        mock_db,
        mock_teacher_user,
        mock_valid_invitation_code
    ):
        """Test that non-students cannot complete onboarding."""
        token = create_access_token({
            "sub": str(mock_teacher_user.id),
            "email": mock_teacher_user.email,
            "role": mock_teacher_user.role.value,
            "school_id": mock_teacher_user.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_teacher_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/onboarding/complete",
                json={
                    "invitation_code": mock_valid_invitation_code.code,
                    "first_name": "Новый",
                    "last_name": "Ученик",
                    "birth_date": "2010-05-15"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 403
        assert "Only students can complete onboarding" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_complete_onboarding_already_has_school(
        self,
        mock_db,
        mock_existing_user_with_school,
        mock_valid_invitation_code
    ):
        """Test that students with school cannot complete onboarding."""
        token = create_access_token({
            "sub": str(mock_existing_user_with_school.id),
            "email": mock_existing_user_with_school.email,
            "role": mock_existing_user_with_school.role.value,
            "school_id": mock_existing_user_with_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_with_school

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/onboarding/complete",
                json={
                    "invitation_code": mock_valid_invitation_code.code,
                    "first_name": "Новый",
                    "last_name": "Ученик",
                    "birth_date": "2010-05-15"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "User already belongs to a school" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_complete_onboarding_missing_fields(
        self,
        mock_db,
        mock_existing_user_without_school,
        mock_valid_invitation_code
    ):
        """Test onboarding fails with missing required fields."""
        token = create_access_token({
            "sub": str(mock_existing_user_without_school.id),
            "email": mock_existing_user_without_school.email,
            "role": mock_existing_user_without_school.role.value,
            "school_id": mock_existing_user_without_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_without_school

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/onboarding/complete",
                json={
                    "invitation_code": mock_valid_invitation_code.code,
                    # Missing first_name, last_name
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        app.dependency_overrides.clear()

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_complete_onboarding_no_auth(self, mock_db, mock_valid_invitation_code):
        """Test that unauthenticated users cannot complete onboarding."""
        app.dependency_overrides[get_db] = lambda: mock_db
        # Don't override get_current_user - let it fail

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/onboarding/complete",
                json={
                    "invitation_code": mock_valid_invitation_code.code,
                    "first_name": "Новый",
                    "last_name": "Ученик",
                    "birth_date": "2010-05-15"
                }
            )

        app.dependency_overrides.clear()

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_complete_onboarding_generates_student_code(
        self,
        mock_db,
        mock_existing_user_without_school,
        mock_valid_invitation_code,
        mock_student
    ):
        """Test that onboarding generates student code in correct format."""
        token = create_access_token({
            "sub": str(mock_existing_user_without_school.id),
            "email": mock_existing_user_without_school.email,
            "role": mock_existing_user_without_school.role.value,
            "school_id": mock_existing_user_without_school.school_id
        })

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_existing_user_without_school

        with patch("app.api.v1.auth_oauth.InvitationCodeRepository") as mock_code_repo_class, \
             patch("app.api.v1.auth_oauth.UserRepository") as mock_user_repo_class, \
             patch("app.api.v1.auth_oauth.StudentRepository") as mock_student_repo_class, \
             patch("app.repositories.school_class_repo.SchoolClassRepository") as mock_class_repo_class:

            mock_code_repo = AsyncMock()
            mock_code_repo.validate_code.return_value = (True, None, mock_valid_invitation_code)
            mock_code_repo.use_code.return_value = None
            mock_code_repo_class.return_value = mock_code_repo

            mock_user_repo = AsyncMock()
            mock_user_repo.update.return_value = mock_existing_user_without_school
            mock_user_repo_class.return_value = mock_user_repo

            mock_student_repo = AsyncMock()
            mock_student_repo.get_by_user_id.return_value = None
            mock_student_repo.generate_student_code.return_value = "STU72026001"
            mock_student_repo.create.return_value = mock_student
            mock_student_repo_class.return_value = mock_student_repo

            # Setup class repo
            mock_class_repo = AsyncMock()
            mock_class_repo.add_students.return_value = None
            mock_class_repo_class.return_value = mock_class_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/onboarding/complete",
                    json={
                        "invitation_code": mock_valid_invitation_code.code,
                        "first_name": "Новый",
                        "last_name": "Ученик",
                        "birth_date": "2010-05-15"
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["student"]["student_code"].startswith("STU")


# ========== Integration Tests ==========

class TestOAuthIntegration:
    """Integration tests for complete OAuth flows."""

    @pytest.mark.asyncio
    async def test_full_google_onboarding_flow(
        self,
        mock_db,
        mock_valid_invitation_code,
        mock_student
    ):
        """Test complete flow: Google login -> validate code -> complete onboarding."""
        # Create user that will be returned on Google login
        new_google_user = MagicMock(spec=User)
        new_google_user.id = 200
        new_google_user.email = "flowtest@gmail.com"
        new_google_user.first_name = "Flow"
        new_google_user.last_name = "Test"
        new_google_user.middle_name = None
        new_google_user.avatar_url = None
        new_google_user.role = UserRole.STUDENT
        new_google_user.school_id = None
        new_google_user.google_id = "flow_test_google_id"
        new_google_user.auth_provider = AuthProvider.GOOGLE
        new_google_user.is_active = True
        new_google_user.is_verified = True
        new_google_user.created_at = datetime.now(timezone.utc)
        new_google_user.updated_at = datetime.now(timezone.utc)

        mock_service = MockGoogleAuthService(
            user_info=MockGoogleUserInfo(
                google_id="flow_test_google_id",
                email="flowtest@gmail.com",
                email_verified=True,
                first_name="Flow",
                last_name="Test",
            )
        )

        app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Step 1: Google login (new user)
            with patch("app.api.v1.auth_oauth.GoogleAuthService", return_value=mock_service), \
                 patch("app.api.v1.auth_oauth.settings") as mock_settings, \
                 patch("app.api.v1.auth_oauth.UserRepository") as mock_user_repo_class:

                mock_settings.GOOGLE_CLIENT_ID = "test-client-id"

                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_google_id.return_value = None
                mock_user_repo.get_by_email.return_value = None
                mock_user_repo.create.return_value = new_google_user
                mock_user_repo_class.return_value = mock_user_repo

                login_response = await client.post(
                    "/api/v1/auth/google",
                    json={"id_token": "valid_google_token"}
                )

            assert login_response.status_code == 200
            login_data = login_response.json()
            assert login_data["requires_onboarding"] is True
            access_token = login_data["access_token"]

            # Step 2: Validate invitation code
            app.dependency_overrides[get_current_user] = lambda: new_google_user

            with patch("app.api.v1.auth_oauth.InvitationCodeRepository") as mock_code_repo_class:
                mock_code_repo = AsyncMock()
                mock_code_repo.validate_code.return_value = (True, None, mock_valid_invitation_code)
                mock_code_repo_class.return_value = mock_code_repo

                validate_response = await client.post(
                    "/api/v1/auth/onboarding/validate-code",
                    json={"code": mock_valid_invitation_code.code},
                    headers={"Authorization": f"Bearer {access_token}"}
                )

            assert validate_response.status_code == 200
            assert validate_response.json()["valid"] is True

            # Step 3: Complete onboarding
            with patch("app.api.v1.auth_oauth.InvitationCodeRepository") as mock_code_repo_class, \
                 patch("app.api.v1.auth_oauth.UserRepository") as mock_user_repo_class, \
                 patch("app.api.v1.auth_oauth.StudentRepository") as mock_student_repo_class, \
                 patch("app.repositories.school_class_repo.SchoolClassRepository") as mock_class_repo_class:

                mock_code_repo = AsyncMock()
                mock_code_repo.validate_code.return_value = (True, None, mock_valid_invitation_code)
                mock_code_repo.use_code.return_value = None
                mock_code_repo_class.return_value = mock_code_repo

                mock_user_repo = AsyncMock()
                mock_user_repo.update.return_value = new_google_user
                mock_user_repo_class.return_value = mock_user_repo

                mock_student_repo = AsyncMock()
                mock_student_repo.get_by_user_id.return_value = None
                mock_student_repo.generate_student_code.return_value = "STU72026001"
                mock_student_repo.create.return_value = mock_student
                mock_student_repo_class.return_value = mock_student_repo

                # Setup class repo
                mock_class_repo = AsyncMock()
                mock_class_repo.add_students.return_value = None
                mock_class_repo_class.return_value = mock_class_repo

                complete_response = await client.post(
                    "/api/v1/auth/onboarding/complete",
                    json={
                        "invitation_code": mock_valid_invitation_code.code,
                        "first_name": "Полный",
                        "last_name": "Тест",
                        "birth_date": "2010-01-01"
                    },
                    headers={"Authorization": f"Bearer {access_token}"}
                )

            assert complete_response.status_code == 200
            complete_data = complete_response.json()
            assert "student" in complete_data

        app.dependency_overrides.clear()
