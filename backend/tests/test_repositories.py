"""
Tests for Repository layer.

Covers core repositories:
- UserRepository
- StudentRepository
- TeacherRepository
- SchoolRepository
- InvitationCodeRepository

Uses mocked database sessions for fast unit tests.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.user import User, UserRole
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.school import School
from app.models.invitation_code import InvitationCode
from app.repositories.user_repo import UserRepository
from app.repositories.student_repo import StudentRepository
from app.repositories.teacher_repo import TeacherRepository
from app.repositories.school_repo import SchoolRepository
from app.repositories.invitation_code_repo import InvitationCodeRepository


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def sample_user():
    """Create a sample user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.role = UserRole.STUDENT
    user.school_id = 5
    user.is_active = True
    user.is_deleted = False
    user.google_id = None
    user.deleted_at = None
    return user


@pytest.fixture
def sample_student():
    """Create a sample student."""
    student = MagicMock(spec=Student)
    student.id = 1
    student.user_id = 1
    student.school_id = 5
    student.student_code = "STU52401"
    student.grade_level = 7
    student.is_deleted = False
    student.deleted_at = None
    student.user = MagicMock(spec=User)
    student.user.first_name = "Test"
    student.user.last_name = "Student"
    student.user.is_active = True
    return student


@pytest.fixture
def sample_teacher():
    """Create a sample teacher."""
    teacher = MagicMock(spec=Teacher)
    teacher.id = 1
    teacher.user_id = 10
    teacher.school_id = 5
    teacher.subject = "Математика"
    teacher.is_deleted = False
    teacher.deleted_at = None
    teacher.user = MagicMock(spec=User)
    teacher.user.first_name = "Test"
    teacher.user.last_name = "Teacher"
    return teacher


@pytest.fixture
def sample_school():
    """Create a sample school."""
    school = MagicMock(spec=School)
    school.id = 5
    school.name = "Test School"
    school.code = "TEST001"
    school.is_active = True
    school.is_deleted = False
    return school


@pytest.fixture
def sample_invitation_code():
    """Create a sample invitation code."""
    code = MagicMock(spec=InvitationCode)
    code.id = 1
    code.code = "ABC123"
    code.school_id = 5
    code.class_id = 1
    code.role = UserRole.STUDENT
    code.max_uses = 30
    code.current_uses = 0
    code.expires_at = datetime.utcnow() + timedelta(days=30)
    code.is_active = True
    return code


# =============================================================================
# UserRepository Tests
# =============================================================================

class TestUserRepository:
    """Tests for UserRepository."""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, mock_db, sample_user):
        """Test getting user by ID."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = result

        repo = UserRepository(mock_db)
        user = await repo.get_by_id(1)

        assert user == sample_user
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_db):
        """Test getting non-existent user."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        repo = UserRepository(mock_db)
        user = await repo.get_by_id(999)

        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_email_success(self, mock_db, sample_user):
        """Test getting user by email."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = result

        repo = UserRepository(mock_db)
        user = await repo.get_by_email("test@example.com")

        assert user == sample_user

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, mock_db):
        """Test getting user by non-existent email."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        repo = UserRepository(mock_db)
        user = await repo.get_by_email("nonexistent@example.com")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_google_id_success(self, mock_db, sample_user):
        """Test getting user by Google ID."""
        sample_user.google_id = "google123"
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = result

        repo = UserRepository(mock_db)
        user = await repo.get_by_google_id("google123")

        assert user == sample_user

    @pytest.mark.asyncio
    async def test_get_by_google_id_not_found(self, mock_db):
        """Test getting user by non-existent Google ID."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        repo = UserRepository(mock_db)
        user = await repo.get_by_google_id("nonexistent")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_school(self, mock_db, sample_user):
        """Test getting users by school."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_user]
        mock_db.execute.return_value = result

        repo = UserRepository(mock_db)
        users = await repo.get_by_school(school_id=5)

        assert len(users) == 1
        assert users[0] == sample_user

    @pytest.mark.asyncio
    async def test_get_by_school_with_role_filter(self, mock_db, sample_user):
        """Test getting users by school with role filter."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_user]
        mock_db.execute.return_value = result

        repo = UserRepository(mock_db)
        users = await repo.get_by_school(school_id=5, role="student")

        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_get_by_school_with_active_filter(self, mock_db, sample_user):
        """Test getting users by school with active filter."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_user]
        mock_db.execute.return_value = result

        repo = UserRepository(mock_db)
        users = await repo.get_by_school(school_id=5, is_active=True)

        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_get_by_school_empty(self, mock_db):
        """Test getting users when school has none."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = result

        repo = UserRepository(mock_db)
        users = await repo.get_by_school(school_id=5)

        assert len(users) == 0

    @pytest.mark.asyncio
    async def test_create_user(self, mock_db, sample_user):
        """Test creating a user."""
        repo = UserRepository(mock_db)
        user = await repo.create(sample_user)

        mock_db.add.assert_called_once_with(sample_user)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_user)

    @pytest.mark.asyncio
    async def test_update_user(self, mock_db, sample_user):
        """Test updating a user."""
        repo = UserRepository(mock_db)
        user = await repo.update(sample_user)

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_user)

    @pytest.mark.asyncio
    async def test_soft_delete(self, mock_db, sample_user):
        """Test soft deleting a user."""
        repo = UserRepository(mock_db)
        user = await repo.soft_delete(sample_user)

        assert sample_user.is_deleted is True
        assert sample_user.deleted_at is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate(self, mock_db, sample_user):
        """Test deactivating a user."""
        sample_user.is_active = True
        repo = UserRepository(mock_db)
        user = await repo.deactivate(sample_user)

        assert sample_user.is_active is False
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate(self, mock_db, sample_user):
        """Test activating a user."""
        sample_user.is_active = False
        repo = UserRepository(mock_db)
        user = await repo.activate(sample_user)

        assert sample_user.is_active is True
        mock_db.commit.assert_called_once()


# =============================================================================
# StudentRepository Tests
# =============================================================================

class TestStudentRepository:
    """Tests for StudentRepository."""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, mock_db, sample_student):
        """Test getting student by ID with school isolation."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_student
        mock_db.execute.return_value = result

        repo = StudentRepository(mock_db)
        student = await repo.get_by_id(student_id=1, school_id=5)

        assert student == sample_student

    @pytest.mark.asyncio
    async def test_get_by_id_wrong_school(self, mock_db):
        """Test getting student with wrong school returns None."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        repo = StudentRepository(mock_db)
        student = await repo.get_by_id(student_id=1, school_id=999)

        assert student is None

    @pytest.mark.asyncio
    async def test_get_by_id_with_user_loaded(self, mock_db, sample_student):
        """Test getting student with user data loaded."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_student
        mock_db.execute.return_value = result

        repo = StudentRepository(mock_db)
        student = await repo.get_by_id(student_id=1, school_id=5, load_user=True)

        assert student == sample_student
        assert student.user is not None

    @pytest.mark.asyncio
    async def test_get_all_for_school(self, mock_db, sample_student):
        """Test getting all students for a school."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_student]
        mock_db.execute.return_value = result

        repo = StudentRepository(mock_db)
        students = await repo.get_all(school_id=5)

        assert len(students) == 1

    @pytest.mark.asyncio
    async def test_get_all_empty(self, mock_db):
        """Test getting students when school has none."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = result

        repo = StudentRepository(mock_db)
        students = await repo.get_all(school_id=5)

        assert len(students) == 0

    @pytest.mark.asyncio
    async def test_get_by_filters_grade_level(self, mock_db, sample_student):
        """Test getting students filtered by grade level."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_student]
        mock_db.execute.return_value = result

        repo = StudentRepository(mock_db)
        students = await repo.get_by_filters(school_id=5, grade_level=7)

        assert len(students) == 1

    @pytest.mark.asyncio
    async def test_get_by_student_code(self, mock_db, sample_student):
        """Test getting student by student code."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_student
        mock_db.execute.return_value = result

        repo = StudentRepository(mock_db)
        student = await repo.get_by_student_code("STU52401", school_id=5)

        assert student == sample_student

    @pytest.mark.asyncio
    async def test_get_by_student_code_not_found(self, mock_db):
        """Test getting student by non-existent code."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        repo = StudentRepository(mock_db)
        student = await repo.get_by_student_code("NONEXISTENT", school_id=5)

        assert student is None

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, mock_db, sample_student):
        """Test getting student by user ID."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_student
        mock_db.execute.return_value = result

        repo = StudentRepository(mock_db)
        student = await repo.get_by_user_id(user_id=1)

        assert student == sample_student

    @pytest.mark.asyncio
    async def test_generate_student_code(self, mock_db):
        """Test generating unique student code."""
        # Mock count
        count_result = MagicMock()
        count_result.scalar_one.return_value = 5

        # Mock code uniqueness check
        unique_result = MagicMock()
        unique_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [count_result, unique_result]

        repo = StudentRepository(mock_db)
        code = await repo.generate_student_code(school_id=5)

        assert code.startswith("STU5")
        assert len(code) >= 8

    @pytest.mark.asyncio
    async def test_create_student(self, mock_db, sample_student):
        """Test creating a student."""
        repo = StudentRepository(mock_db)
        student = await repo.create(sample_student)

        mock_db.add.assert_called_once_with(sample_student)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_student(self, mock_db, sample_student):
        """Test updating a student."""
        repo = StudentRepository(mock_db)
        student = await repo.update(sample_student)

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_student(self, mock_db, sample_student):
        """Test soft deleting a student."""
        repo = StudentRepository(mock_db)
        student = await repo.soft_delete(sample_student)

        assert sample_student.is_deleted is True
        assert sample_student.deleted_at is not None

    @pytest.mark.asyncio
    async def test_count_by_school(self, mock_db):
        """Test counting students in a school."""
        result = MagicMock()
        result.scalar_one.return_value = 25
        mock_db.execute.return_value = result

        repo = StudentRepository(mock_db)
        count = await repo.count_by_school(school_id=5)

        assert count == 25


# =============================================================================
# TeacherRepository Tests
# =============================================================================

class TestTeacherRepository:
    """Tests for TeacherRepository."""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, mock_db, sample_teacher):
        """Test getting teacher by ID."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_teacher
        mock_db.execute.return_value = result

        repo = TeacherRepository(mock_db)
        teacher = await repo.get_by_id(teacher_id=1, school_id=5)

        assert teacher == sample_teacher

    @pytest.mark.asyncio
    async def test_get_by_id_wrong_school(self, mock_db):
        """Test getting teacher with wrong school returns None."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        repo = TeacherRepository(mock_db)
        teacher = await repo.get_by_id(teacher_id=1, school_id=999)

        assert teacher is None

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, mock_db, sample_teacher):
        """Test getting teacher by user ID."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_teacher
        mock_db.execute.return_value = result

        repo = TeacherRepository(mock_db)
        teacher = await repo.get_by_user_id(user_id=10, school_id=5)

        assert teacher == sample_teacher

    @pytest.mark.asyncio
    async def test_get_all_for_school(self, mock_db, sample_teacher):
        """Test getting all teachers for a school."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_teacher]
        mock_db.execute.return_value = result

        repo = TeacherRepository(mock_db)
        teachers = await repo.get_all(school_id=5)

        assert len(teachers) == 1

    @pytest.mark.asyncio
    async def test_get_by_subject(self, mock_db, sample_teacher):
        """Test getting teachers by subject."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_teacher]
        mock_db.execute.return_value = result

        repo = TeacherRepository(mock_db)
        teachers = await repo.get_by_subject(school_id=5, subject="Математика")

        assert len(teachers) == 1

    @pytest.mark.asyncio
    async def test_create_teacher(self, mock_db, sample_teacher):
        """Test creating a teacher."""
        repo = TeacherRepository(mock_db)
        teacher = await repo.create(sample_teacher)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_teacher(self, mock_db, sample_teacher):
        """Test updating a teacher."""
        repo = TeacherRepository(mock_db)
        teacher = await repo.update(sample_teacher)

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_teacher(self, mock_db, sample_teacher):
        """Test soft deleting a teacher."""
        repo = TeacherRepository(mock_db)
        teacher = await repo.soft_delete(sample_teacher)

        assert sample_teacher.is_deleted is True


# =============================================================================
# SchoolRepository Tests
# =============================================================================

class TestSchoolRepository:
    """Tests for SchoolRepository."""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, mock_db, sample_school):
        """Test getting school by ID."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_school
        mock_db.execute.return_value = result

        repo = SchoolRepository(mock_db)
        school = await repo.get_by_id(5)

        assert school == sample_school

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_db):
        """Test getting non-existent school."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        repo = SchoolRepository(mock_db)
        school = await repo.get_by_id(999)

        assert school is None

    @pytest.mark.asyncio
    async def test_get_by_code(self, mock_db, sample_school):
        """Test getting school by code."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_school
        mock_db.execute.return_value = result

        repo = SchoolRepository(mock_db)
        school = await repo.get_by_code("TEST001")

        assert school == sample_school

    @pytest.mark.asyncio
    async def test_get_all(self, mock_db, sample_school):
        """Test getting all schools."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_school]
        mock_db.execute.return_value = result

        repo = SchoolRepository(mock_db)
        schools = await repo.get_all()

        assert len(schools) == 1

    @pytest.mark.asyncio
    async def test_get_active_only(self, mock_db, sample_school):
        """Test getting only active schools."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_school]
        mock_db.execute.return_value = result

        repo = SchoolRepository(mock_db)
        schools = await repo.get_all(is_active=True)

        assert len(schools) == 1

    @pytest.mark.asyncio
    async def test_create_school(self, mock_db, sample_school):
        """Test creating a school."""
        repo = SchoolRepository(mock_db)
        school = await repo.create(sample_school)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_school(self, mock_db, sample_school):
        """Test updating a school."""
        repo = SchoolRepository(mock_db)
        school = await repo.update(sample_school)

        mock_db.commit.assert_called_once()


# =============================================================================
# InvitationCodeRepository Tests
# =============================================================================

class TestInvitationCodeRepository:
    """Tests for InvitationCodeRepository."""

    @pytest.mark.asyncio
    async def test_get_by_code_success(self, mock_db, sample_invitation_code):
        """Test getting invitation code by code string."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_invitation_code
        mock_db.execute.return_value = result

        repo = InvitationCodeRepository(mock_db)
        code = await repo.get_by_code("ABC123")

        assert code == sample_invitation_code

    @pytest.mark.asyncio
    async def test_get_by_code_not_found(self, mock_db):
        """Test getting non-existent invitation code."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        repo = InvitationCodeRepository(mock_db)
        code = await repo.get_by_code("NONEXISTENT")

        assert code is None

    @pytest.mark.asyncio
    async def test_get_by_id(self, mock_db, sample_invitation_code):
        """Test getting invitation code by ID."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_invitation_code
        mock_db.execute.return_value = result

        repo = InvitationCodeRepository(mock_db)
        code = await repo.get_by_id(1)

        assert code == sample_invitation_code

    @pytest.mark.asyncio
    async def test_get_by_school(self, mock_db, sample_invitation_code):
        """Test getting all invitation codes for a school."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_invitation_code]
        mock_db.execute.return_value = result

        repo = InvitationCodeRepository(mock_db)
        codes = await repo.get_by_school(school_id=5)

        assert len(codes) == 1

    @pytest.mark.asyncio
    async def test_validate_code_valid(self, mock_db, sample_invitation_code):
        """Test validating a valid invitation code."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_invitation_code
        mock_db.execute.return_value = result

        repo = InvitationCodeRepository(mock_db)
        is_valid, error = await repo.validate_code("ABC123")

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_code_not_found(self, mock_db):
        """Test validating non-existent code."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        repo = InvitationCodeRepository(mock_db)
        is_valid, error = await repo.validate_code("NONEXISTENT")

        assert is_valid is False
        assert error is not None

    @pytest.mark.asyncio
    async def test_validate_code_expired(self, mock_db, sample_invitation_code):
        """Test validating expired invitation code."""
        sample_invitation_code.expires_at = datetime.utcnow() - timedelta(days=1)

        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_invitation_code
        mock_db.execute.return_value = result

        repo = InvitationCodeRepository(mock_db)
        is_valid, error = await repo.validate_code("ABC123")

        assert is_valid is False
        assert "expired" in error.lower() or "истек" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_code_exhausted(self, mock_db, sample_invitation_code):
        """Test validating exhausted invitation code."""
        sample_invitation_code.max_uses = 5
        sample_invitation_code.current_uses = 5

        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_invitation_code
        mock_db.execute.return_value = result

        repo = InvitationCodeRepository(mock_db)
        is_valid, error = await repo.validate_code("ABC123")

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_code_inactive(self, mock_db, sample_invitation_code):
        """Test validating inactive invitation code."""
        sample_invitation_code.is_active = False

        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_invitation_code
        mock_db.execute.return_value = result

        repo = InvitationCodeRepository(mock_db)
        is_valid, error = await repo.validate_code("ABC123")

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_increment_usage(self, mock_db, sample_invitation_code):
        """Test incrementing invitation code usage."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_invitation_code
        mock_db.execute.return_value = result

        repo = InvitationCodeRepository(mock_db)
        code = await repo.increment_usage(1)

        assert sample_invitation_code.current_uses == 1
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_code(self, mock_db, sample_invitation_code):
        """Test creating an invitation code."""
        repo = InvitationCodeRepository(mock_db)
        code = await repo.create(sample_invitation_code)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_code(self, mock_db, sample_invitation_code):
        """Test deactivating an invitation code."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_invitation_code
        mock_db.execute.return_value = result

        repo = InvitationCodeRepository(mock_db)
        code = await repo.deactivate(1)

        assert sample_invitation_code.is_active is False


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestRepositoryEdgeCases:
    """Tests for edge cases in repositories."""

    @pytest.mark.asyncio
    async def test_user_with_unicode_name(self, mock_db):
        """Test handling user with unicode characters in name."""
        user = MagicMock(spec=User)
        user.first_name = "Алексей"
        user.last_name = "Иванов"
        user.email = "alexey@test.com"

        repo = UserRepository(mock_db)
        await repo.create(user)

        mock_db.add.assert_called_once_with(user)

    @pytest.mark.asyncio
    async def test_student_code_generation_collision_handling(self, mock_db):
        """Test student code generation handles collisions."""
        # First call returns count
        count_result = MagicMock()
        count_result.scalar_one.return_value = 10

        # First uniqueness check returns existing (collision)
        collision_result = MagicMock()
        collision_result.scalar_one_or_none.return_value = MagicMock()  # Code exists

        # Second uniqueness check returns None (unique)
        unique_result = MagicMock()
        unique_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [count_result, collision_result, unique_result]

        repo = StudentRepository(mock_db)
        code = await repo.generate_student_code(school_id=5)

        assert code.startswith("STU5")

    @pytest.mark.asyncio
    async def test_school_isolation_enforced(self, mock_db):
        """Test that school isolation is enforced in queries."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        repo = StudentRepository(mock_db)

        # Trying to access student from different school
        student = await repo.get_by_id(student_id=1, school_id=999)

        assert student is None  # School isolation prevents access

    @pytest.mark.asyncio
    async def test_soft_delete_preserves_data(self, mock_db, sample_user):
        """Test that soft delete preserves data while marking as deleted."""
        original_email = sample_user.email
        original_name = sample_user.first_name

        repo = UserRepository(mock_db)
        await repo.soft_delete(sample_user)

        # Data should be preserved
        assert sample_user.email == original_email
        assert sample_user.first_name == original_name
        # But marked as deleted
        assert sample_user.is_deleted is True
        assert sample_user.deleted_at is not None

    @pytest.mark.asyncio
    async def test_multiple_role_filters(self, mock_db):
        """Test filtering by multiple criteria."""
        users = []
        for i in range(3):
            u = MagicMock(spec=User)
            u.id = i
            u.role = UserRole.TEACHER
            u.is_active = True
            users.append(u)

        result = MagicMock()
        result.scalars.return_value.all.return_value = users
        mock_db.execute.return_value = result

        repo = UserRepository(mock_db)
        filtered = await repo.get_by_school(
            school_id=5,
            role="teacher",
            is_active=True
        )

        assert len(filtered) == 3


class TestRepositoryTransactions:
    """Tests for repository transaction handling."""

    @pytest.mark.asyncio
    async def test_create_commits_transaction(self, mock_db, sample_user):
        """Test that create commits the transaction."""
        repo = UserRepository(mock_db)
        await repo.create(sample_user)

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_commits_transaction(self, mock_db, sample_user):
        """Test that update commits the transaction."""
        repo = UserRepository(mock_db)
        await repo.update(sample_user)

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_commits_transaction(self, mock_db, sample_user):
        """Test that soft delete commits the transaction."""
        repo = UserRepository(mock_db)
        await repo.soft_delete(sample_user)

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_after_create(self, mock_db, sample_user):
        """Test that refresh is called after create."""
        repo = UserRepository(mock_db)
        await repo.create(sample_user)

        mock_db.refresh.assert_called_once_with(sample_user)
