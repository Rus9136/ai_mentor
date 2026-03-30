"""
Integration tests for teacher self-registration flow.

Tests the full chain:
  GET  /auth/teacher/subjects  → public subjects list
  POST /auth/teacher/register  → create User + Teacher + TeacherSubjects + return tokens

Covers:
- Happy path: register by email, register by phone
- School code validation: invalid code, inactive school
- Duplicate checks: email, phone
- Subject validation: invalid subject ID, empty subjects
- Password validation: too short
- Token validity: can call /auth/me after registration
- Multi-subject assignment
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select

from app.models.user import User, UserRole
from app.models.school import School
from app.models.teacher import Teacher
from app.models.teacher_subject import TeacherSubject
from app.models.subject import Subject
from app.core.rate_limiter import limiter


# Reset rate limiter before each test
@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


# ========== Fixtures ==========


@pytest_asyncio.fixture
async def subject_math(db_session: AsyncSession) -> Subject:
    """Create Math subject."""
    subject = Subject(
        code="math",
        name_ru="Математика",
        name_kz="Математика",
        grade_from=1,
        grade_to=11,
        is_active=True,
    )
    db_session.add(subject)
    await db_session.flush()
    await db_session.commit()
    return subject


@pytest_asyncio.fixture
async def subject_physics(db_session: AsyncSession) -> Subject:
    """Create Physics subject."""
    subject = Subject(
        code="physics",
        name_ru="Физика",
        name_kz="Физика",
        grade_from=7,
        grade_to=11,
        is_active=True,
    )
    db_session.add(subject)
    await db_session.flush()
    await db_session.commit()
    return subject


@pytest_asyncio.fixture
async def subject_inactive(db_session: AsyncSession) -> Subject:
    """Create an inactive subject."""
    subject = Subject(
        code="art",
        name_ru="Рисование",
        name_kz="Сурет",
        grade_from=1,
        grade_to=11,
        is_active=False,
    )
    db_session.add(subject)
    await db_session.flush()
    await db_session.commit()
    return subject


@pytest_asyncio.fixture
async def inactive_school(db_session: AsyncSession) -> School:
    """Create an inactive school."""
    school = School(
        name="Inactive School",
        code="inactive-school",
        email="inactive@school.com",
        is_active=False,
    )
    db_session.add(school)
    await db_session.flush()
    await db_session.commit()
    return school


# ========== Tests: GET /auth/teacher/subjects ==========


class TestGetSubjects:
    """Tests for public subjects endpoint."""

    @pytest.mark.asyncio
    async def test_get_subjects_returns_active_only(
        self,
        test_app,
        subject_math,
        subject_physics,
        subject_inactive,
    ):
        """Should return only active subjects without requiring auth."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/auth/teacher/subjects")

        assert response.status_code == 200
        data = response.json()
        codes = [s["code"] for s in data]
        assert "math" in codes
        assert "physics" in codes
        assert "art" not in codes  # inactive

    @pytest.mark.asyncio
    async def test_get_subjects_no_auth_required(self, test_app):
        """Should work without Authorization header."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/auth/teacher/subjects")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_subjects_returns_expected_fields(
        self,
        test_app,
        subject_math,
    ):
        """Response should contain all needed fields for frontend."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/auth/teacher/subjects")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        subj = data[0]
        assert "id" in subj
        assert "code" in subj
        assert "name_ru" in subj
        assert "name_kz" in subj


# ========== Tests: POST /auth/teacher/register ==========


class TestRegisterTeacherByEmail:
    """Tests for teacher registration with email."""

    @pytest.mark.asyncio
    async def test_register_success_email(
        self,
        test_app,
        school1,
        subject_math,
        db_session,
    ):
        """Happy path: register teacher by email → get tokens + user created."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "school-1",
                    "email": "new.teacher@school.com",
                    "password": "secure123",
                    "first_name": "Иван",
                    "last_name": "Иванов",
                    "middle_name": "Иванович",
                    "subject_ids": [subject_math.id],
                },
            )

        assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
        data = response.json()

        # Check tokens
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Check user in response
        user = data["user"]
        assert user["first_name"] == "Иван"
        assert user["last_name"] == "Иванов"
        assert user["middle_name"] == "Иванович"
        assert user["role"] == "teacher"
        assert user["school_id"] == school1.id
        assert user["email"] == "new.teacher@school.com"

        # Verify User in DB
        result = await db_session.execute(
            sa_select(User).where(User.email == "new.teacher@school.com")
        )
        db_user = result.scalar_one()
        assert db_user.role == UserRole.TEACHER
        assert db_user.school_id == school1.id
        assert db_user.is_active is True

        # Verify Teacher record in DB
        result = await db_session.execute(
            sa_select(Teacher).where(Teacher.user_id == db_user.id)
        )
        teacher = result.scalar_one()
        assert teacher.school_id == school1.id
        assert teacher.teacher_code.startswith("TCHR")

        # Verify TeacherSubject in DB
        result = await db_session.execute(
            sa_select(TeacherSubject).where(TeacherSubject.teacher_id == teacher.id)
        )
        teacher_subjects = list(result.scalars().all())
        assert len(teacher_subjects) == 1
        assert teacher_subjects[0].subject_id == subject_math.id

    @pytest.mark.asyncio
    async def test_register_token_works_for_auth_me(
        self,
        test_app,
        school1,
        subject_math,
    ):
        """After registration, returned token should work for GET /auth/me."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Register
            reg_response = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "school-1",
                    "email": "token.test@school.com",
                    "password": "secure123",
                    "first_name": "Тест",
                    "last_name": "Токен",
                    "subject_ids": [subject_math.id],
                },
            )
            assert reg_response.status_code == 200
            token = reg_response.json()["access_token"]

            # Use token for /auth/me
            me_response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["role"] == "teacher"
        assert me_data["first_name"] == "Тест"

    @pytest.mark.asyncio
    async def test_register_multi_subject(
        self,
        test_app,
        school1,
        subject_math,
        subject_physics,
        db_session,
    ):
        """Teacher can select multiple subjects during registration."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "school-1",
                    "email": "multi.subject@school.com",
                    "password": "secure123",
                    "first_name": "Мульти",
                    "last_name": "Предмет",
                    "subject_ids": [subject_math.id, subject_physics.id],
                },
            )

        assert response.status_code == 200
        user_id = response.json()["user"]["id"]

        # Verify TeacherSubjects in DB
        result = await db_session.execute(
            sa_select(Teacher).where(Teacher.user_id == user_id)
        )
        teacher = result.scalar_one()

        result = await db_session.execute(
            sa_select(TeacherSubject).where(TeacherSubject.teacher_id == teacher.id)
        )
        teacher_subjects = list(result.scalars().all())
        subject_ids = {ts.subject_id for ts in teacher_subjects}
        assert subject_ids == {subject_math.id, subject_physics.id}


class TestRegisterTeacherByPhone:
    """Tests for teacher registration with phone."""

    @pytest.mark.asyncio
    async def test_register_success_phone(
        self,
        test_app,
        school1,
        subject_math,
        db_session,
    ):
        """Happy path: register teacher by phone → get tokens."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "school-1",
                    "phone": "+77071234567",
                    "password": "secure123",
                    "first_name": "Айбек",
                    "last_name": "Касымов",
                    "subject_ids": [subject_math.id],
                },
            )

        assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
        assert data["user"]["phone"] == "+77071234567"

        # Verify synthetic email generated
        result = await db_session.execute(
            sa_select(User).where(User.phone == "+77071234567")
        )
        db_user = result.scalar_one()
        assert db_user.email == "phone_+77071234567@phone.local"
        assert db_user.auth_provider.value == "phone"

    @pytest.mark.asyncio
    async def test_register_phone_normalization(
        self,
        test_app,
        school1,
        subject_math,
        db_session,
    ):
        """Phone in 87077880094 format should be normalized to +7..."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "school-1",
                    "phone": "87077880094",
                    "password": "secure123",
                    "first_name": "Нормал",
                    "last_name": "Телефон",
                    "subject_ids": [subject_math.id],
                },
            )

        assert response.status_code == 200
        assert response.json()["user"]["phone"] == "+77077880094"


class TestRegisterValidationErrors:
    """Tests for validation errors during registration."""

    @pytest.mark.asyncio
    async def test_invalid_school_code(
        self,
        test_app,
        subject_math,
    ):
        """Invalid school code → 400 with VAL_011."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "nonexistent-school",
                    "email": "teacher@test.com",
                    "password": "secure123",
                    "first_name": "Test",
                    "last_name": "Teacher",
                    "subject_ids": [subject_math.id],
                },
            )

        assert response.status_code == 400
        detail = response.json()["detail"]
        if isinstance(detail, dict):
            assert detail["code"] == "VAL_011"
        else:
            assert "VAL_011" in str(detail) or "school code" in str(detail).lower()

    @pytest.mark.asyncio
    async def test_inactive_school_code(
        self,
        test_app,
        inactive_school,
        subject_math,
    ):
        """Inactive school code → 400 with VAL_011."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "inactive-school",
                    "email": "teacher@test.com",
                    "password": "secure123",
                    "first_name": "Test",
                    "last_name": "Teacher",
                    "subject_ids": [subject_math.id],
                },
            )

        assert response.status_code == 400
        detail = response.json()["detail"]
        if isinstance(detail, dict):
            assert detail["code"] == "VAL_011"
        else:
            assert "VAL_011" in str(detail) or "school code" in str(detail).lower()

    @pytest.mark.asyncio
    async def test_duplicate_email(
        self,
        test_app,
        school1,
        subject_math,
    ):
        """Registering same email twice → 409 conflict."""
        payload = {
            "school_code": "school-1",
            "email": "duplicate@school.com",
            "password": "secure123",
            "first_name": "First",
            "last_name": "Teacher",
            "subject_ids": [subject_math.id],
        }
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # First registration → success
            resp1 = await client.post("/api/v1/auth/teacher/register", json=payload)
            assert resp1.status_code == 200

            # Second registration → conflict
            payload["first_name"] = "Second"
            resp2 = await client.post("/api/v1/auth/teacher/register", json=payload)

        assert resp2.status_code == 409

    @pytest.mark.asyncio
    async def test_duplicate_phone(
        self,
        test_app,
        school1,
        subject_math,
    ):
        """Registering same phone twice → 409 conflict."""
        payload = {
            "school_code": "school-1",
            "phone": "+77079999999",
            "password": "secure123",
            "first_name": "First",
            "last_name": "Teacher",
            "subject_ids": [subject_math.id],
        }
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp1 = await client.post("/api/v1/auth/teacher/register", json=payload)
            assert resp1.status_code == 200

            payload["first_name"] = "Second"
            resp2 = await client.post("/api/v1/auth/teacher/register", json=payload)

        assert resp2.status_code == 409

    @pytest.mark.asyncio
    async def test_no_email_no_phone(self, test_app, school1, subject_math):
        """Neither email nor phone provided → 422 validation error."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "school-1",
                    "password": "secure123",
                    "first_name": "Test",
                    "last_name": "Teacher",
                    "subject_ids": [subject_math.id],
                },
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_password_too_short(self, test_app, school1, subject_math):
        """Password < 8 chars → 422 validation error."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "school-1",
                    "email": "short.pass@school.com",
                    "password": "123",
                    "first_name": "Test",
                    "last_name": "Teacher",
                    "subject_ids": [subject_math.id],
                },
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_subject_ids(self, test_app, school1):
        """Empty subject_ids list → 422 validation error."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "school-1",
                    "email": "no.subjects@school.com",
                    "password": "secure123",
                    "first_name": "Test",
                    "last_name": "Teacher",
                    "subject_ids": [],
                },
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_subject_id(
        self,
        test_app,
        school1,
    ):
        """Non-existent subject ID → 400."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "school-1",
                    "email": "bad.subject@school.com",
                    "password": "secure123",
                    "first_name": "Test",
                    "last_name": "Teacher",
                    "subject_ids": [99999],
                },
            )

        assert response.status_code == 400


class TestRegisterTeacherCode:
    """Tests for auto-generated teacher code."""

    @pytest.mark.asyncio
    async def test_teacher_code_auto_generated(
        self,
        test_app,
        school1,
        subject_math,
        db_session,
    ):
        """Teacher code should be auto-generated in TCHR{YY}{NNNN} format."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "school-1",
                    "email": "code.test@school.com",
                    "password": "secure123",
                    "first_name": "Код",
                    "last_name": "Учитель",
                    "subject_ids": [subject_math.id],
                },
            )

        assert response.status_code == 200
        user_id = response.json()["user"]["id"]

        result = await db_session.execute(
            sa_select(Teacher).where(Teacher.user_id == user_id)
        )
        teacher = result.scalar_one()
        assert teacher.teacher_code.startswith("TCHR")
        assert len(teacher.teacher_code) == 10  # TCHR + 2 digits year + 4 digits count


class TestRegisterLoginAfterRegistration:
    """Test that teacher can log in after self-registration."""

    @pytest.mark.asyncio
    async def test_login_with_email_after_register(
        self,
        test_app,
        school1,
        subject_math,
    ):
        """After registration, teacher can log in with email + password."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Register
            reg = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "school-1",
                    "email": "login.test@school.com",
                    "password": "mysecure123",
                    "first_name": "Логин",
                    "last_name": "Тест",
                    "subject_ids": [subject_math.id],
                },
            )
            assert reg.status_code == 200

            # Login
            login = await client.post(
                "/api/v1/auth/login",
                json={
                    "login": "login.test@school.com",
                    "password": "mysecure123",
                },
            )

        assert login.status_code == 200
        assert "access_token" in login.json()

    @pytest.mark.asyncio
    async def test_login_with_phone_after_register(
        self,
        test_app,
        school1,
        subject_math,
    ):
        """After registration by phone, teacher can log in with phone + password."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Register
            reg = await client.post(
                "/api/v1/auth/teacher/register",
                json={
                    "school_code": "school-1",
                    "phone": "+77071112233",
                    "password": "mysecure123",
                    "first_name": "Телефон",
                    "last_name": "Тест",
                    "subject_ids": [subject_math.id],
                },
            )
            assert reg.status_code == 200

            # Login by phone
            login = await client.post(
                "/api/v1/auth/login",
                json={
                    "login": "+77071112233",
                    "password": "mysecure123",
                },
            )

        assert login.status_code == 200
        assert "access_token" in login.json()
