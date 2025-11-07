"""
Pytest configuration and fixtures.
"""
import pytest
import pytest_asyncio
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from sqlalchemy.orm import selectinload
from sqlalchemy import select as sa_select

from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import get_password_hash, create_access_token
from app.main import app
from app.models.user import User, UserRole
from app.models.school import School
from app.models.student import Student
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.test import Test, Question, QuestionOption, DifficultyLevel, QuestionType, TestPurpose


# Test database URL (use separate test database)
# IMPORTANT: Use ai_mentor_user (SUPERUSER) for tests to bypass RLS and have DROP TABLE permissions
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://ai_mentor_user:ai_mentor_pass"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/ai_mentor_test_db"
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

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
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
