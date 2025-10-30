"""
Tests for content data isolation between schools.
Critical tests to verify multi-tenancy works correctly.
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import School
from app.models.user import User, UserRole
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.core.security import hash_password
from app.repositories.textbook_repo import TextbookRepository


@pytest.mark.asyncio
async def test_super_admin_creates_global_textbook(db_session: AsyncSession):
    """
    Test that SUPER_ADMIN can create a global textbook with school_id = NULL.
    """
    # Create SUPER_ADMIN user (no school_id)
    super_admin = User(
        email="superadmin@test.com",
        hashed_password=hash_password("password"),
        first_name="Super",
        last_name="Admin",
        role=UserRole.SUPER_ADMIN,
        school_id=None,
        is_active=True,
        is_verified=True,
    )
    db_session.add(super_admin)
    await db_session.commit()

    # Create global textbook
    textbook_repo = TextbookRepository(db_session)
    global_textbook = Textbook(
        school_id=None,  # Global textbook
        title="Global Algebra 7",
        subject="Mathematics",
        grade_level=7,
        is_active=True,
        version=1,
    )
    await textbook_repo.create(global_textbook)

    # Verify
    assert global_textbook.id is not None
    assert global_textbook.school_id is None
    assert global_textbook.title == "Global Algebra 7"


@pytest.mark.asyncio
async def test_school_admin_sees_global_and_own_textbooks(db_session: AsyncSession):
    """
    Test that School ADMIN sees both global textbooks and their school's textbooks.
    """
    # Create two schools
    school1 = School(name="School 1", code="SCH1")
    school2 = School(name="School 2", code="SCH2")
    db_session.add_all([school1, school2])
    await db_session.commit()

    # Create global textbook
    global_textbook = Textbook(
        school_id=None,
        title="Global Physics 8",
        subject="Physics",
        grade_level=8,
        is_active=True,
        version=1,
    )
    db_session.add(global_textbook)

    # Create school1 textbook
    school1_textbook = Textbook(
        school_id=school1.id,
        title="School1 Chemistry 9",
        subject="Chemistry",
        grade_level=9,
        is_active=True,
        version=1,
    )
    db_session.add(school1_textbook)

    # Create school2 textbook
    school2_textbook = Textbook(
        school_id=school2.id,
        title="School2 Biology 10",
        subject="Biology",
        grade_level=10,
        is_active=True,
        version=1,
    )
    db_session.add(school2_textbook)

    await db_session.commit()

    # School1 admin should see global + school1 textbooks
    textbook_repo = TextbookRepository(db_session)
    school1_textbooks = await textbook_repo.get_by_school(school1.id, include_global=True)

    school1_titles = [t.title for t in school1_textbooks]
    assert "Global Physics 8" in school1_titles
    assert "School1 Chemistry 9" in school1_titles
    assert "School2 Biology 10" not in school1_titles  # Should NOT see school2's textbook


@pytest.mark.asyncio
async def test_school_admin_cannot_see_other_school_textbooks(db_session: AsyncSession):
    """
    Test that School ADMIN 1 cannot see School 2's textbooks (isolation).
    """
    # Create two schools
    school1 = School(name="School 1", code="SCH1")
    school2 = School(name="School 2", code="SCH2")
    db_session.add_all([school1, school2])
    await db_session.commit()

    # Create textbooks for each school
    school1_textbook = Textbook(
        school_id=school1.id,
        title="School1 Textbook",
        subject="Math",
        grade_level=7,
        is_active=True,
        version=1,
    )
    school2_textbook = Textbook(
        school_id=school2.id,
        title="School2 Textbook",
        subject="Math",
        grade_level=7,
        is_active=True,
        version=1,
    )
    db_session.add_all([school1_textbook, school2_textbook])
    await db_session.commit()

    # School1 should only see their own textbooks
    textbook_repo = TextbookRepository(db_session)
    school1_textbooks = await textbook_repo.get_by_school(school1.id, include_global=False)

    assert len(school1_textbooks) == 1
    assert school1_textbooks[0].title == "School1 Textbook"
    assert school1_textbooks[0].school_id == school1.id


@pytest.mark.asyncio
async def test_fork_creates_customized_textbook(db_session: AsyncSession):
    """
    Test that fork creates a customized copy with is_customized=True.
    """
    # Create school
    school = School(name="Test School", code="TEST")
    db_session.add(school)
    await db_session.commit()

    # Create global textbook with chapter and paragraph
    global_textbook = Textbook(
        school_id=None,
        title="Global Algebra 7",
        subject="Mathematics",
        grade_level=7,
        is_active=True,
        version=2,  # Version 2
    )
    db_session.add(global_textbook)
    await db_session.flush()

    chapter = Chapter(
        textbook_id=global_textbook.id,
        title="Chapter 1",
        number=1,
        order=1,
    )
    db_session.add(chapter)
    await db_session.flush()

    paragraph = Paragraph(
        chapter_id=chapter.id,
        title="Paragraph 1.1",
        number=1,
        order=1,
        content="Content here",
    )
    db_session.add(paragraph)
    await db_session.commit()

    # Fork textbook
    textbook_repo = TextbookRepository(db_session)
    forked_textbook = await textbook_repo.fork_textbook(global_textbook, school.id)

    # Verify fork properties
    assert forked_textbook.school_id == school.id
    assert forked_textbook.is_customized is True
    assert forked_textbook.global_textbook_id == global_textbook.id
    assert forked_textbook.source_version == 2  # Captured source version
    assert forked_textbook.version == 1  # New fork starts at version 1
    assert "Customized" in forked_textbook.title

    # Verify chapters and paragraphs were copied
    result = await db_session.execute(
        select(Chapter).where(Chapter.textbook_id == forked_textbook.id)
    )
    forked_chapters = result.scalars().all()
    assert len(forked_chapters) == 1
    assert forked_chapters[0].title == "Chapter 1"

    result = await db_session.execute(
        select(Paragraph).where(Paragraph.chapter_id == forked_chapters[0].id)
    )
    forked_paragraphs = result.scalars().all()
    assert len(forked_paragraphs) == 1
    assert forked_paragraphs[0].title == "Paragraph 1.1"


@pytest.mark.asyncio
async def test_versioning_works(db_session: AsyncSession):
    """
    Test that version and source_version fields work correctly.
    """
    # Create global textbook
    textbook = Textbook(
        school_id=None,
        title="Test Textbook",
        subject="Math",
        grade_level=7,
        is_active=True,
        version=1,
    )
    db_session.add(textbook)
    await db_session.commit()

    # Update should increment version (this would be done in API)
    textbook.version += 1
    textbook.title = "Updated Textbook"
    await db_session.commit()
    await db_session.refresh(textbook)

    assert textbook.version == 2
    assert textbook.title == "Updated Textbook"


@pytest.mark.asyncio
async def test_global_textbooks_visible_to_all_schools(db_session: AsyncSession):
    """
    Test that global textbooks (school_id = NULL) are visible to all schools.
    """
    # Create schools
    school1 = School(name="School 1", code="SCH1")
    school2 = School(name="School 2", code="SCH2")
    db_session.add_all([school1, school2])
    await db_session.commit()

    # Create global textbook
    global_textbook = Textbook(
        school_id=None,
        title="Global Textbook",
        subject="Math",
        grade_level=7,
        is_active=True,
        version=1,
    )
    db_session.add(global_textbook)
    await db_session.commit()

    # Both schools should see the global textbook
    textbook_repo = TextbookRepository(db_session)
    school1_textbooks = await textbook_repo.get_by_school(school1.id, include_global=True)
    school2_textbooks = await textbook_repo.get_by_school(school2.id, include_global=True)

    school1_titles = [t.title for t in school1_textbooks]
    school2_titles = [t.title for t in school2_textbooks]

    assert "Global Textbook" in school1_titles
    assert "Global Textbook" in school2_titles
