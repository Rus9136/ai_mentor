"""
Pytest configuration and fixtures.
"""
import pytest
import pytest_asyncio
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from sqlalchemy.orm import selectinload
from sqlalchemy import select as sa_select

from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import get_password_hash, create_access_token, create_refresh_token
from app.main import app
from app.models.user import User, UserRole
from app.models.school import School
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.school_class import SchoolClass
from app.models.invitation_code import InvitationCode
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.test import Test, Question, QuestionOption, DifficultyLevel, QuestionType, TestPurpose
from app.models.class_student import ClassStudent
from app.models.homework import (
    Homework,
    HomeworkTask,
    HomeworkTaskQuestion,
    HomeworkStudent,
    HomeworkStatus,
    HomeworkTaskType,
    HomeworkQuestionType,
    HomeworkStudentStatus,
)


# Test database URL (use separate test database)
# IMPORTANT: Use ai_mentor_user (SUPERUSER) for tests to bypass RLS and have DROP TABLE permissions
# Allow override via environment variables for running outside Docker
import os
_test_db_host = os.environ.get("TEST_DB_HOST", settings.POSTGRES_HOST)
_test_db_port = os.environ.get("TEST_DB_PORT", str(settings.POSTGRES_PORT))
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://ai_mentor_user:ai_mentor_pass"
    f"@{_test_db_host}:{_test_db_port}/ai_mentor_test_db"
)


# ========== Base Database Fixture ==========

@pytest_asyncio.fixture
async def db_session():
    """
    Create a fresh database session for each test.
    Uses a test database and rolls back after each test.
    """
    # Create async engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    # Recreate schema from scratch.
    # test_attempts is a partitioned table with composite PK (id, started_at) in production.
    # create_all can't handle partitioning, so we pre-create it as a regular table
    # with simple PK (id), then let create_all handle all other tables.
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Pre-create test_attempts as a non-partitioned table (simple PK for tests)
        await conn.execute(text("""
            CREATE TABLE test_attempts (
                id SERIAL PRIMARY KEY,
                started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                student_id INTEGER NOT NULL,
                test_id INTEGER NOT NULL,
                school_id INTEGER NOT NULL,
                attempt_number INTEGER NOT NULL DEFAULT 1,
                status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
                completed_at TIMESTAMPTZ,
                score FLOAT,
                points_earned FLOAT,
                total_points FLOAT,
                passed BOOLEAN,
                time_spent INTEGER,
                synced_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        # Now create_all will skip test_attempts (already exists) and create everything else
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()

    # Dispose engine
    await engine.dispose()


# ========== App Fixture ==========

@pytest_asyncio.fixture
async def test_app(db_session: AsyncSession):
    """
    Override app's get_db dependency to use test database session.
    Remove TenancyMiddleware to avoid event loop conflicts in tests.
    """
    # Remove TenancyMiddleware for testing
    # (It conflicts with test database session and causes async event loop issues)
    original_middleware = app.user_middleware.copy()
    app.user_middleware = [
        m for m in app.user_middleware
        if 'TenancyMiddleware' not in str(m.cls)
    ]
    app.middleware_stack = None  # Force rebuild

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield app

    # Restore original state
    app.dependency_overrides.clear()
    app.user_middleware = original_middleware
    app.middleware_stack = None


# ========== School Fixtures ==========

@pytest_asyncio.fixture
async def school1(db_session: AsyncSession) -> School:
    """Create first test school."""
    school = School(
        name="School 1",
        code="school-1",
        email="school1@test.com",
        is_active=True,
    )
    db_session.add(school)
    await db_session.commit()
    await db_session.refresh(school)
    return school


@pytest_asyncio.fixture
async def school2(db_session: AsyncSession) -> School:
    """Create second test school for isolation tests."""
    school = School(
        name="School 2",
        code="school-2",
        email="school2@test.com",
        is_active=True,
    )
    db_session.add(school)
    await db_session.commit()
    await db_session.refresh(school)
    return school


# ========== User & Student Fixtures ==========

@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession, school1: School) -> tuple[User, Student]:
    """
    Create a test student with user account.
    Returns tuple of (User, Student).
    """
    # Create user
    user = User(
        email="student@test.com",
        password_hash=get_password_hash("student123"),
        first_name="Test",
        last_name="Student",
        role=UserRole.STUDENT,
        school_id=school1.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    # Create student
    student = Student(
        school_id=school1.id,
        user_id=user.id,
        student_code="STU0720250001",
        grade_level=7,
        birth_date=date(2010, 1, 1),
    )
    db_session.add(student)
    await db_session.commit()

    # Eager load relationships to avoid lazy loading issues
    result = await db_session.execute(
        sa_select(User)
        .where(User.id == user.id)
        .options(selectinload(User.student))
    )
    user = result.scalar_one()

    result = await db_session.execute(
        sa_select(Student)
        .where(Student.id == student.id)
        .options(selectinload(Student.user))
    )
    student = result.scalar_one()

    return (user, student)


@pytest_asyncio.fixture
async def student2_user(db_session: AsyncSession, school2: School) -> tuple[User, Student]:
    """
    Create a second test student in school2 (for isolation tests).
    Returns tuple of (User, Student).
    """
    user = User(
        email="student2@test.com",
        password_hash=get_password_hash("student123"),
        first_name="Student",
        last_name="Two",
        role=UserRole.STUDENT,
        school_id=school2.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    student = Student(
        school_id=school2.id,
        user_id=user.id,
        student_code="STU0720250002",
        grade_level=7,
        birth_date=date(2010, 2, 2),
    )
    db_session.add(student)
    await db_session.commit()

    # Eager load relationships
    result = await db_session.execute(
        sa_select(User)
        .where(User.id == user.id)
        .options(selectinload(User.student))
    )
    user = result.scalar_one()

    result = await db_session.execute(
        sa_select(Student)
        .where(Student.id == student.id)
        .options(selectinload(Student.user))
    )
    student = result.scalar_one()

    return (user, student)


@pytest_asyncio.fixture
async def student_token(student_user: tuple[User, Student]) -> str:
    """Create access token for student."""
    user, _ = student_user
    return create_access_token(data={"sub": str(user.id)})


@pytest_asyncio.fixture
async def student2_token(student2_user: tuple[User, Student]) -> str:
    """Create access token for student2."""
    user, _ = student2_user
    return create_access_token(data={"sub": str(user.id)})


# ========== Content Fixtures (Textbook, Chapter, Paragraph) ==========

@pytest_asyncio.fixture
async def textbook1(db_session: AsyncSession, school1: School) -> Textbook:
    """Create a test textbook in school1."""
    textbook = Textbook(
        school_id=school1.id,
        title="Алгебра 7 класс",
        subject="Математика",
        grade_level=7,
        is_active=True,
    )
    db_session.add(textbook)
    await db_session.commit()
    await db_session.refresh(textbook)
    return textbook


@pytest_asyncio.fixture
async def global_textbook(db_session: AsyncSession) -> Textbook:
    """Create a global textbook (school_id=NULL)."""
    textbook = Textbook(
        school_id=None,  # Global
        title="Физика 8 класс (Глобальный)",
        subject="Физика",
        grade_level=8,
        is_active=True,
    )
    db_session.add(textbook)
    await db_session.commit()
    await db_session.refresh(textbook)
    return textbook


@pytest_asyncio.fixture
async def chapter1(db_session: AsyncSession, textbook1: Textbook) -> Chapter:
    """Create a test chapter in textbook1."""
    chapter = Chapter(
        textbook_id=textbook1.id,
        number=1,
        order=1,
        title="Линейные уравнения",
        description="Основы линейных уравнений",
    )
    db_session.add(chapter)
    await db_session.commit()
    await db_session.refresh(chapter)
    return chapter


@pytest_asyncio.fixture
async def paragraph1(db_session: AsyncSession, chapter1: Chapter) -> Paragraph:
    """Create a test paragraph in chapter1."""
    paragraph = Paragraph(
        chapter_id=chapter1.id,
        number=1,
        order=1,
        title="Простейшие линейные уравнения",
        content="Содержание параграфа...",
    )
    db_session.add(paragraph)
    await db_session.commit()
    await db_session.refresh(paragraph)
    return paragraph


# ========== Test Fixtures (with Questions) ==========

@pytest_asyncio.fixture
async def test_with_questions(
    db_session: AsyncSession,
    school1: School,
    chapter1: Chapter,
    paragraph1: Paragraph
) -> Test:
    """
    Create a formative test with 4 questions (one of each type).

    Questions:
    1. SINGLE_CHOICE: 2x + 3 = 7
    2. MULTIPLE_CHOICE: Select all prime numbers
    3. TRUE_FALSE: Is 0 positive?
    4. SHORT_ANSWER: Explain Pythagorean theorem
    """
    test = Test(
        school_id=school1.id,
        chapter_id=chapter1.id,
        paragraph_id=paragraph1.id,
        title="Тест по линейным уравнениям",
        description="Формативный тест",
        test_purpose=TestPurpose.FORMATIVE,
        difficulty=DifficultyLevel.MEDIUM,
        time_limit=30,
        passing_score=0.7,
        is_active=True,
    )
    db_session.add(test)
    await db_session.flush()

    # Question 1: SINGLE_CHOICE
    q1 = Question(
        test_id=test.id,
        order=1,
        question_type=QuestionType.SINGLE_CHOICE,
        question_text="Решите уравнение: 2x + 3 = 7",
        explanation="x = 2",
        points=1.0,
    )
    db_session.add(q1)
    await db_session.flush()

    # Options for Q1
    q1_opt1 = QuestionOption(question_id=q1.id, order=1, option_text="x = 1", is_correct=False)
    q1_opt2 = QuestionOption(question_id=q1.id, order=2, option_text="x = 2", is_correct=True)
    q1_opt3 = QuestionOption(question_id=q1.id, order=3, option_text="x = 3", is_correct=False)
    db_session.add_all([q1_opt1, q1_opt2, q1_opt3])

    # Question 2: MULTIPLE_CHOICE
    q2 = Question(
        test_id=test.id,
        order=2,
        question_type=QuestionType.MULTIPLE_CHOICE,
        question_text="Выберите все простые числа:",
        explanation="2, 3, 5 - простые числа",
        points=2.0,
    )
    db_session.add(q2)
    await db_session.flush()

    # Options for Q2
    q2_opt1 = QuestionOption(question_id=q2.id, order=1, option_text="2", is_correct=True)
    q2_opt2 = QuestionOption(question_id=q2.id, order=2, option_text="3", is_correct=True)
    q2_opt3 = QuestionOption(question_id=q2.id, order=3, option_text="4", is_correct=False)
    q2_opt4 = QuestionOption(question_id=q2.id, order=4, option_text="5", is_correct=True)
    db_session.add_all([q2_opt1, q2_opt2, q2_opt3, q2_opt4])

    # Question 3: TRUE_FALSE
    q3 = Question(
        test_id=test.id,
        order=3,
        question_type=QuestionType.TRUE_FALSE,
        question_text="Число 0 является положительным числом",
        explanation="False - 0 не является положительным",
        points=1.0,
    )
    db_session.add(q3)
    await db_session.flush()

    # Options for Q3
    q3_opt1 = QuestionOption(question_id=q3.id, order=1, option_text="True", is_correct=False)
    q3_opt2 = QuestionOption(question_id=q3.id, order=2, option_text="False", is_correct=True)
    db_session.add_all([q3_opt1, q3_opt2])

    # Question 4: SHORT_ANSWER
    q4 = Question(
        test_id=test.id,
        order=4,
        question_type=QuestionType.SHORT_ANSWER,
        question_text="Объясните теорему Пифагора своими словами",
        explanation="a² + b² = c²",
        points=2.0,
    )
    db_session.add(q4)

    await db_session.commit()

    # Eager load relationships to avoid lazy loading issues in tests
    result = await db_session.execute(
        sa_select(Test)
        .where(Test.id == test.id)
        .options(
            selectinload(Test.questions).selectinload(Question.options)
        )
    )
    test = result.scalar_one()
    return test


@pytest_asyncio.fixture
async def global_test(db_session: AsyncSession, global_textbook: Textbook) -> Test:
    """Create a global test (school_id=NULL)."""
    # Create chapter and paragraph for global textbook
    chapter = Chapter(
        textbook_id=global_textbook.id,
        number=1,
        order=1,
        title="Механика",
        description="Основы механики",
    )
    db_session.add(chapter)
    await db_session.flush()

    paragraph = Paragraph(
        chapter_id=chapter.id,
        number=1,
        order=1,
        title="Законы Ньютона",
        content="Содержание параграфа...",
    )
    db_session.add(paragraph)
    await db_session.flush()

    # Create global test
    test = Test(
        school_id=None,  # Global
        chapter_id=chapter.id,
        paragraph_id=paragraph.id,
        title="Тест по законам Ньютона (Глобальный)",
        description="Диагностический тест",
        test_purpose=TestPurpose.DIAGNOSTIC,
        difficulty=DifficultyLevel.EASY,
        time_limit=20,
        passing_score=0.6,
        is_active=True,
    )
    db_session.add(test)
    await db_session.flush()

    # Add 1 simple question
    q = Question(
        test_id=test.id,
        order=1,
        question_type=QuestionType.SINGLE_CHOICE,
        question_text="Сколько законов Ньютона существует?",
        explanation="Три закона",
        points=1.0,
    )
    db_session.add(q)
    await db_session.flush()

    opt1 = QuestionOption(question_id=q.id, order=1, option_text="2", is_correct=False)
    opt2 = QuestionOption(question_id=q.id, order=2, option_text="3", is_correct=True)
    opt3 = QuestionOption(question_id=q.id, order=3, option_text="4", is_correct=False)
    db_session.add_all([opt1, opt2, opt3])

    await db_session.commit()
    await db_session.refresh(test)
    return test


@pytest_asyncio.fixture
async def inactive_test(
    db_session: AsyncSession,
    school1: School,
    chapter1: Chapter,
    paragraph1: Paragraph
) -> Test:
    """Create an inactive test (is_active=False)."""
    test = Test(
        school_id=school1.id,
        chapter_id=chapter1.id,
        paragraph_id=paragraph1.id,
        title="Неактивный тест",
        description="Этот тест не активен",
        test_purpose=TestPurpose.PRACTICE,
        difficulty=DifficultyLevel.EASY,
        time_limit=15,
        passing_score=0.5,
        is_active=False,  # INACTIVE
    )
    db_session.add(test)
    await db_session.commit()
    await db_session.refresh(test)
    return test


# ========== Auth Fixtures (Admin, Teacher, Inactive User) ==========

@pytest_asyncio.fixture
async def super_admin_user(db_session: AsyncSession) -> User:
    """Create a SUPER_ADMIN user (no school_id)."""
    user = User(
        email="superadmin@test.com",
        password_hash=get_password_hash("admin123"),
        first_name="Super",
        last_name="Admin",
        role=UserRole.SUPER_ADMIN,
        school_id=None,  # Super admin has no school
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, school1: School) -> User:
    """Create an ADMIN user for school1."""
    user = User(
        email="admin@test.com",
        password_hash=get_password_hash("admin123"),
        first_name="School",
        last_name="Admin",
        role=UserRole.ADMIN,
        school_id=school1.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def teacher_user(db_session: AsyncSession, school1: School) -> tuple[User, Teacher]:
    """
    Create a TEACHER user with Teacher record.
    Returns tuple of (User, Teacher).
    """
    user = User(
        email="teacher@test.com",
        password_hash=get_password_hash("teacher123"),
        first_name="Test",
        last_name="Teacher",
        role=UserRole.TEACHER,
        school_id=school1.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    teacher = Teacher(
        user_id=user.id,
        school_id=school1.id,
        teacher_code="TCH0720250001",
        subject="Математика",
    )
    db_session.add(teacher)
    await db_session.commit()

    # Eager load relationships
    result = await db_session.execute(
        sa_select(User)
        .where(User.id == user.id)
        .options(selectinload(User.teacher))
    )
    user = result.scalar_one()

    result = await db_session.execute(
        sa_select(Teacher)
        .where(Teacher.id == teacher.id)
        .options(selectinload(Teacher.user))
    )
    teacher = result.scalar_one()

    return (user, teacher)


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession, school1: School) -> User:
    """Create an inactive user (is_active=False)."""
    user = User(
        email="inactive@test.com",
        password_hash=get_password_hash("inactive123"),
        first_name="Inactive",
        last_name="User",
        role=UserRole.STUDENT,
        school_id=school1.id,
        is_active=False,  # INACTIVE
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def super_admin_token(super_admin_user: User) -> str:
    """Create access token for super admin."""
    return create_access_token(data={
        "sub": str(super_admin_user.id),
        "email": super_admin_user.email,
        "role": super_admin_user.role.value,
        "school_id": super_admin_user.school_id,
    })


@pytest_asyncio.fixture
async def admin_token(admin_user: User) -> str:
    """Create access token for admin."""
    return create_access_token(data={
        "sub": str(admin_user.id),
        "email": admin_user.email,
        "role": admin_user.role.value,
        "school_id": admin_user.school_id,
    })


@pytest_asyncio.fixture
async def teacher_token(teacher_user: tuple[User, Teacher]) -> str:
    """Create access token for teacher."""
    user, _ = teacher_user
    return create_access_token(data={
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "school_id": user.school_id,
    })


# ========== School Class & Invitation Code Fixtures ==========

@pytest_asyncio.fixture
async def school_class(db_session: AsyncSession, school1: School) -> SchoolClass:
    """Create a test class in school1."""
    school_class = SchoolClass(
        school_id=school1.id,
        name="7А",
        code="7A-2025",
        grade_level=7,
        academic_year="2024-2025",
    )
    db_session.add(school_class)
    await db_session.commit()
    await db_session.refresh(school_class)
    return school_class


@pytest_asyncio.fixture
async def invitation_code(
    db_session: AsyncSession,
    school1: School,
    school_class: SchoolClass,
    admin_user: User
) -> InvitationCode:
    """Create a valid invitation code for school1."""
    code = InvitationCode(
        school_id=school1.id,
        class_id=school_class.id,
        code="TEST123",
        grade_level=7,
        max_uses=10,
        uses_count=0,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        created_by=admin_user.id,
        is_active=True,
    )
    db_session.add(code)
    await db_session.commit()

    # Eager load relationships
    result = await db_session.execute(
        sa_select(InvitationCode)
        .where(InvitationCode.id == code.id)
        .options(
            selectinload(InvitationCode.school),
            selectinload(InvitationCode.school_class)
        )
    )
    code = result.scalar_one()
    return code


@pytest_asyncio.fixture
async def expired_invitation_code(
    db_session: AsyncSession,
    school1: School,
    admin_user: User
) -> InvitationCode:
    """Create an expired invitation code."""
    code = InvitationCode(
        school_id=school1.id,
        class_id=None,
        code="EXPIRED123",
        grade_level=7,
        max_uses=10,
        uses_count=0,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
        created_by=admin_user.id,
        is_active=True,
    )
    db_session.add(code)
    await db_session.commit()
    await db_session.refresh(code)
    return code


@pytest_asyncio.fixture
async def exhausted_invitation_code(
    db_session: AsyncSession,
    school1: School,
    admin_user: User
) -> InvitationCode:
    """Create an exhausted invitation code (max_uses reached)."""
    code = InvitationCode(
        school_id=school1.id,
        class_id=None,
        code="EXHAUSTED123",
        grade_level=7,
        max_uses=5,
        uses_count=5,  # Exhausted
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        created_by=admin_user.id,
        is_active=True,
    )
    db_session.add(code)
    await db_session.commit()
    await db_session.refresh(code)
    return code


# ========== OAuth Fixtures ==========

@pytest_asyncio.fixture
async def google_user_without_school(db_session: AsyncSession) -> User:
    """Create a Google OAuth user without school_id (requires onboarding)."""
    from app.models.user import AuthProvider
    user = User(
        email="googleuser@gmail.com",
        google_id="google_123456789",
        auth_provider=AuthProvider.GOOGLE,
        first_name="Google",
        last_name="User",
        role=UserRole.STUDENT,
        school_id=None,  # Requires onboarding
        is_active=True,
        password_hash=None,  # No password for OAuth users
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def google_user_token(google_user_without_school: User) -> str:
    """Create access token for Google user without school."""
    return create_access_token(data={
        "sub": str(google_user_without_school.id),
        "email": google_user_without_school.email,
        "role": google_user_without_school.role.value,
        "school_id": google_user_without_school.school_id,
    })


# ========== Teacher2 Fixtures (for school isolation tests) ==========

@pytest_asyncio.fixture
async def teacher2_user(db_session: AsyncSession, school2: School) -> tuple[User, Teacher]:
    """Create a second TEACHER in school2 for isolation tests."""
    user = User(
        email="teacher2@test.com",
        password_hash=get_password_hash("teacher123"),
        first_name="Second",
        last_name="Teacher",
        role=UserRole.TEACHER,
        school_id=school2.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    teacher = Teacher(
        user_id=user.id,
        school_id=school2.id,
        teacher_code="TCH0720250002",
        subject="Физика",
    )
    db_session.add(teacher)
    await db_session.commit()

    result = await db_session.execute(
        sa_select(User).where(User.id == user.id).options(selectinload(User.teacher))
    )
    user = result.scalar_one()

    result = await db_session.execute(
        sa_select(Teacher).where(Teacher.id == teacher.id).options(selectinload(Teacher.user))
    )
    teacher = result.scalar_one()

    return (user, teacher)


@pytest_asyncio.fixture
async def teacher2_token(teacher2_user: tuple[User, Teacher]) -> str:
    """Create access token for teacher2."""
    user, _ = teacher2_user
    return create_access_token(data={
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "school_id": user.school_id,
    })


# ========== Homework Fixtures ==========

@pytest_asyncio.fixture
async def student_in_class(
    db_session: AsyncSession,
    student_user: tuple[User, Student],
    school_class: SchoolClass
) -> ClassStudent:
    """Enroll student in school_class via ClassStudent association."""
    _, student = student_user
    cs = ClassStudent(class_id=school_class.id, student_id=student.id)
    db_session.add(cs)
    await db_session.commit()
    await db_session.refresh(cs)
    return cs


@pytest_asyncio.fixture
async def draft_homework(
    db_session: AsyncSession,
    school1: School,
    teacher_user: tuple[User, Teacher],
    school_class: SchoolClass,
    paragraph1: Paragraph,
) -> tuple[Homework, HomeworkTask, HomeworkTaskQuestion]:
    """
    Create a DRAFT homework with one QUIZ task and one single_choice question.
    Returns (homework, task, question).
    """
    _, teacher = teacher_user
    hw = Homework(
        school_id=school1.id,
        class_id=school_class.id,
        teacher_id=teacher.id,
        title="Test Homework Draft",
        description="Homework for testing",
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        status=HomeworkStatus.DRAFT,
        late_submission_allowed=True,
        late_penalty_per_day=10,
        grace_period_hours=2,
        max_late_days=7,
        show_explanations=True,
    )
    db_session.add(hw)
    await db_session.flush()

    task = HomeworkTask(
        homework_id=hw.id,
        school_id=school1.id,
        paragraph_id=paragraph1.id,
        task_type=HomeworkTaskType.QUIZ,
        sort_order=0,
        points=10,
        max_attempts=2,
    )
    db_session.add(task)
    await db_session.flush()

    question = HomeworkTaskQuestion(
        homework_task_id=task.id,
        school_id=school1.id,
        question_type=HomeworkQuestionType.SINGLE_CHOICE,
        question_text="Чему равно 2 + 2?",
        options=[
            {"id": "a", "text": "3", "is_correct": False},
            {"id": "b", "text": "4", "is_correct": True},
            {"id": "c", "text": "5", "is_correct": False},
        ],
        points=10,
        sort_order=0,
    )
    db_session.add(question)
    await db_session.commit()

    # Eager reload
    result = await db_session.execute(
        sa_select(Homework)
        .where(Homework.id == hw.id)
        .options(
            selectinload(Homework.tasks).selectinload(HomeworkTask.questions),
            selectinload(Homework.school_class),
        )
    )
    hw = result.scalar_one()
    task = hw.tasks[0]
    question = task.questions[0]

    return (hw, task, question)


@pytest_asyncio.fixture
async def published_homework(
    db_session: AsyncSession,
    draft_homework: tuple[Homework, HomeworkTask, HomeworkTaskQuestion],
    student_in_class: ClassStudent,
    student_user: tuple[User, Student],
) -> tuple[Homework, HomeworkTask, HomeworkTaskQuestion, HomeworkStudent]:
    """
    Publish draft_homework and assign to student.
    Returns (homework, task, question, hw_student).
    """
    hw, task, question = draft_homework
    _, student = student_user

    hw.status = HomeworkStatus.PUBLISHED
    await db_session.flush()

    hw_student = HomeworkStudent(
        homework_id=hw.id,
        student_id=student.id,
        school_id=hw.school_id,
        status=HomeworkStudentStatus.ASSIGNED,
    )
    db_session.add(hw_student)
    await db_session.commit()
    await db_session.refresh(hw_student)

    return (hw, task, question, hw_student)
