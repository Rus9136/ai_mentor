"""
Tests for phone-based authentication for teachers.

Tests cover:
- Login with phone number (+7XXXXXXXXXX) + password
- Login with email (backward compatibility)
- LoginRequest schema validation
- TeacherCreate schema validation (email/phone requirement)
- Teacher creation with phone-only via admin endpoint
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.user import User, UserRole, AuthProvider
from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.schemas.auth import LoginRequest
from app.schemas.teacher import TeacherCreate


# Reset rate limiter before each test
@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def teacher_with_phone():
    """Teacher user with phone number and password."""
    user = MagicMock(spec=User)
    user.id = 10
    user.email = "phone_+77771234567@phone.local"
    user.phone = "+77771234567"
    user.password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.hfXBl1U7RdJYGi"
    user.first_name = "Phone"
    user.last_name = "Teacher"
    user.middle_name = None
    user.avatar_url = None
    user.auth_provider = AuthProvider.PHONE.value
    user.role = UserRole.TEACHER
    user.school_id = 1
    user.is_active = True
    user.is_deleted = False
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def teacher_with_email():
    """Teacher user with email and password."""
    user = MagicMock(spec=User)
    user.id = 11
    user.email = "teacher@school.com"
    user.phone = None
    user.password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.hfXBl1U7RdJYGi"
    user.first_name = "Email"
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
def user_no_password():
    """User without password_hash (OAuth-only)."""
    user = MagicMock(spec=User)
    user.id = 12
    user.email = "oauth@test.com"
    user.phone = "+77779999999"
    user.password_hash = None
    user.first_name = "No"
    user.last_name = "Password"
    user.middle_name = None
    user.avatar_url = None
    user.auth_provider = "google"
    user.role = UserRole.STUDENT
    user.school_id = 1
    user.is_active = True
    user.is_deleted = False
    user.created_at = datetime.now(timezone.utc)
    return user


# =============================================================================
# LoginRequest Schema Tests
# =============================================================================

class TestLoginRequestSchema:
    """Tests for LoginRequest schema validation."""

    def test_login_with_email_field(self):
        """Backward compat: {email, password} maps to {login, password}."""
        req = LoginRequest(**{"email": "test@test.com", "password": "123456"})
        assert req.login == "test@test.com"
        assert req.is_phone is False

    def test_login_with_login_field_email(self):
        """New format: {login, password} with email."""
        req = LoginRequest(login="test@test.com", password="123456")
        assert req.login == "test@test.com"
        assert req.is_phone is False

    def test_login_with_login_field_phone(self):
        """New format: {login, password} with phone."""
        req = LoginRequest(login="+77771234567", password="123456")
        assert req.login == "+77771234567"
        assert req.is_phone is True

    def test_login_prefers_login_over_email(self):
        """If both login and email provided, login wins."""
        req = LoginRequest(**{"login": "+77771234567", "email": "test@test.com", "password": "123456"})
        assert req.login == "+77771234567"

    def test_login_requires_password(self):
        """Password is required."""
        with pytest.raises(Exception):
            LoginRequest(login="test@test.com")

    def test_login_password_min_length(self):
        """Password must be at least 6 chars."""
        with pytest.raises(Exception):
            LoginRequest(login="test@test.com", password="12345")

    def test_login_phone_normalization_8_prefix(self):
        """Phone with 8-prefix normalizes to +7 format."""
        req = LoginRequest(login="87077880094", password="123456")
        assert req.login == "+77077880094"
        assert req.is_phone is True

    def test_login_phone_normalization_no_plus(self):
        """Phone without + normalizes to +7 format."""
        req = LoginRequest(login="77077880094", password="123456")
        assert req.login == "+77077880094"
        assert req.is_phone is True

    def test_login_phone_normalization_formatted(self):
        """Formatted phone +7 (707) 788-00-94 normalizes."""
        req = LoginRequest(login="+7 (707) 788-00-94", password="123456")
        assert req.login == "+77077880094"
        assert req.is_phone is True


# =============================================================================
# TeacherCreate Schema Tests
# =============================================================================

class TestTeacherCreateSchema:
    """Tests for TeacherCreate schema validation."""

    def test_create_with_email_only(self):
        """Email only — valid."""
        tc = TeacherCreate(email="t@test.com", password="12345678", first_name="A", last_name="B")
        assert tc.email == "t@test.com"
        assert tc.phone is None

    def test_create_with_phone_only(self):
        """Phone only — valid."""
        tc = TeacherCreate(phone="+77771234567", password="12345678", first_name="A", last_name="B")
        assert tc.phone == "+77771234567"
        assert tc.email is None

    def test_create_with_both(self):
        """Email and phone — valid."""
        tc = TeacherCreate(email="t@test.com", phone="+77771234567", password="12345678", first_name="A", last_name="B")
        assert tc.email == "t@test.com"
        assert tc.phone == "+77771234567"

    def test_create_without_email_or_phone_fails(self):
        """Neither email nor phone — invalid."""
        with pytest.raises(Exception, match="email or phone"):
            TeacherCreate(password="12345678", first_name="A", last_name="B")

    def test_create_with_empty_email_and_empty_phone_fails(self):
        """Empty strings for both — invalid."""
        with pytest.raises(Exception):
            TeacherCreate(email="", phone="", password="12345678", first_name="A", last_name="B")

    def test_create_invalid_phone_format(self):
        """Truly invalid phone format — rejected."""
        with pytest.raises(Exception, match="\\+7XXXXXXXXXX"):
            TeacherCreate(phone="123", password="12345678", first_name="A", last_name="B")

    def test_create_valid_phone_format(self):
        """Valid KZ phone format +7XXXXXXXXXX."""
        tc = TeacherCreate(phone="+77001234567", password="12345678", first_name="A", last_name="B")
        assert tc.phone == "+77001234567"

    def test_create_phone_normalization_8_prefix(self):
        """Phone with 8-prefix normalizes to +7."""
        tc = TeacherCreate(phone="89991234567", password="12345678", first_name="A", last_name="B")
        assert tc.phone == "+79991234567"

    def test_create_phone_normalization_no_plus(self):
        """Phone without + normalizes to +7."""
        tc = TeacherCreate(phone="77001234567", password="12345678", first_name="A", last_name="B")
        assert tc.phone == "+77001234567"

    def test_create_password_min_length(self):
        """Password must be at least 8 chars for teacher."""
        with pytest.raises(Exception):
            TeacherCreate(email="t@test.com", password="1234567", first_name="A", last_name="B")


# =============================================================================
# Login Endpoint Tests — Phone
# =============================================================================

class TestLoginWithPhone:
    """Tests for POST /api/v1/auth/login with phone number."""

    @pytest.mark.asyncio
    async def test_login_phone_valid(self, teacher_with_phone, mock_db):
        """Login with phone + correct password returns tokens."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_phone.return_value = teacher_with_phone
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"login": "+77771234567", "password": "password123"}
                    )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify get_by_phone was called (not get_by_email)
        mock_repo.get_by_phone.assert_called_once_with("+77771234567")
        mock_repo.get_by_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_phone_not_found(self, mock_db):
        """Login with unregistered phone returns 401."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_phone.return_value = None
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/login",
                    json={"login": "+77770000000", "password": "password123"}
                )

        app.dependency_overrides.clear()
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_phone_wrong_password(self, teacher_with_phone, mock_db):
        """Login with phone + wrong password returns 401."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_phone.return_value = teacher_with_phone
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=False):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"login": "+77771234567", "password": "wrongpassword"}
                    )

        app.dependency_overrides.clear()
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_phone_no_password_hash(self, user_no_password, mock_db):
        """Login fails if user has no password_hash (OAuth-only user)."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_phone.return_value = user_no_password
            mock_repo_class.return_value = mock_repo

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/login",
                    json={"login": "+77779999999", "password": "password123"}
                )

        app.dependency_overrides.clear()
        assert response.status_code == 401


# =============================================================================
# Login Endpoint Tests — Email Backward Compatibility
# =============================================================================

class TestLoginEmailCompat:
    """Tests for POST /api/v1/auth/login with email (backward compat)."""

    @pytest.mark.asyncio
    async def test_login_email_old_format(self, teacher_with_email, mock_db):
        """Old format {email, password} still works."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = teacher_with_email
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"email": "teacher@school.com", "password": "password123"}
                    )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

        # Verify get_by_email was called (not get_by_phone)
        mock_repo.get_by_email.assert_called_once_with("teacher@school.com")
        mock_repo.get_by_phone.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_email_new_format(self, teacher_with_email, mock_db):
        """New format {login, password} with email value."""
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.v1.auth.UserRepository") as mock_repo_class, \
             patch("app.api.v1.auth.limiter"):
            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = teacher_with_email
            mock_repo_class.return_value = mock_repo

            with patch("app.api.v1.auth.verify_password", return_value=True):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={"login": "teacher@school.com", "password": "password123"}
                    )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        mock_repo.get_by_email.assert_called_once_with("teacher@school.com")


# =============================================================================
# Teacher Creation with Phone — Endpoint Tests
# =============================================================================

class TestTeacherCreationWithPhone:
    """Tests for POST /api/v1/admin/school/teachers with phone."""

    @pytest.fixture
    def admin_user_mock(self):
        user = MagicMock(spec=User)
        user.id = 20
        user.email = "admin@school.com"
        user.role = UserRole.ADMIN
        user.school_id = 1
        user.is_active = True
        return user

    @pytest.mark.asyncio
    async def test_create_teacher_phone_only(self, admin_user_mock, mock_db):
        """Admin creates teacher with phone only — synthetic email generated."""
        from app.api.dependencies import get_current_user, get_current_user_school_id

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: admin_user_mock

        async def override_school_id():
            return 1
        app.dependency_overrides[get_current_user_school_id] = override_school_id

        created_user = None

        with patch("app.api.v1.admin_school.teachers.UserRepository") as mock_user_repo_class, \
             patch("app.api.v1.admin_school.teachers.TeacherRepository") as mock_teacher_repo_class, \
             patch("app.api.v1.admin_school.teachers.GosoRepository") as mock_goso_repo_class, \
             patch("app.api.v1.admin_school.teachers.require_admin", return_value=admin_user_mock):

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_email.return_value = None  # no existing email
            mock_user_repo.get_by_phone.return_value = None  # no existing phone

            # Capture the User object passed to create
            async def capture_create(user):
                nonlocal created_user
                created_user = user
                user.id = 100
                return user

            mock_user_repo.create.side_effect = capture_create
            mock_user_repo_class.return_value = mock_user_repo

            mock_teacher_repo = AsyncMock()
            mock_teacher_repo.count_by_school.return_value = 0

            # Return a mock teacher with user relationship
            mock_teacher = MagicMock()
            mock_teacher.id = 50
            mock_teacher.school_id = 1
            mock_teacher.user_id = 100
            mock_teacher.teacher_code = "TCHR260001"
            mock_teacher.subject_id = None
            mock_teacher.subject = None
            mock_teacher.subject_rel = None
            mock_teacher.bio = None
            mock_teacher.created_at = datetime.now(timezone.utc)
            mock_teacher.updated_at = datetime.now(timezone.utc)
            mock_teacher.classes = []
            mock_teacher.user = MagicMock()
            mock_teacher.user.id = 100
            mock_teacher.user.email = "phone_+77771234567@phone.local"
            mock_teacher.user.first_name = "Phone"
            mock_teacher.user.last_name = "Teacher"
            mock_teacher.user.middle_name = None
            mock_teacher.user.phone = "+77771234567"
            mock_teacher.user.role = UserRole.TEACHER
            mock_teacher.user.is_active = True
            mock_teacher.user.avatar_url = None

            mock_teacher_repo.create.return_value = mock_teacher
            mock_teacher_repo.get_by_id.return_value = mock_teacher
            mock_teacher_repo_class.return_value = mock_teacher_repo

            mock_goso_repo_class.return_value = AsyncMock()

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/admin/school/teachers",
                    json={
                        "phone": "+77771234567",
                        "password": "teacher123",
                        "first_name": "Phone",
                        "last_name": "Teacher",
                    },
                    headers={"Authorization": "Bearer fake-admin-token"}
                )

        app.dependency_overrides.clear()

        assert response.status_code == 201

        # Verify synthetic email was generated
        assert created_user is not None
        assert created_user.email == "phone_+77771234567@phone.local"
        assert created_user.phone == "+77771234567"
        assert created_user.auth_provider == AuthProvider.PHONE

    def test_create_teacher_without_email_or_phone_fails(self):
        """Request without email or phone — Pydantic validation error."""
        with pytest.raises(Exception, match="email or phone"):
            TeacherCreate(
                password="teacher123",
                first_name="No",
                last_name="Contact",
            )
