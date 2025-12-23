"""
Unit tests for StudentContentService.

Tests cover:
- Textbooks with progress (batch queries, no N+1)
- Chapters with progress and status
- Paragraphs with status and practice info
- School isolation (data from other schools not visible)
- Mastery level calculation
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.student_content_service import StudentContentService
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.mastery import ParagraphMastery, ChapterMastery
from app.models.test import Test, TestPurpose, DifficultyLevel
from app.models.student import Student
from app.core.config import settings


class TestStudentContentService:
    """Tests for StudentContentService."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession):
        """Create service instance with test database session."""
        return StudentContentService(db_session)

    # ========== Textbooks with Progress Tests ==========

    async def test_get_textbooks_with_progress_empty(
        self, service: StudentContentService, student_user
    ):
        """Test returns empty list when no textbooks available."""
        user, student = student_user

        result = await service.get_textbooks_with_progress(
            student_id=student.id,
            school_id=student.school_id
        )

        assert result == []

    async def test_get_textbooks_with_progress_no_student_progress(
        self, service: StudentContentService, student_user, textbook1
    ):
        """Test textbooks are returned with zero progress for new student."""
        user, student = student_user

        result = await service.get_textbooks_with_progress(
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["textbook"].id == textbook1.id
        assert result[0]["progress"]["paragraphs_completed"] == 0
        assert result[0]["progress"]["percentage"] == 0
        assert result[0]["mastery_level"] is None

    async def test_get_textbooks_with_progress_includes_global(
        self, service: StudentContentService, student_user, global_textbook
    ):
        """Test global textbooks (school_id=NULL) are included."""
        user, student = student_user

        result = await service.get_textbooks_with_progress(
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["textbook"].id == global_textbook.id
        assert result[0]["textbook"].school_id is None

    async def test_get_textbooks_with_progress_excludes_other_school(
        self, service: StudentContentService, student_user, db_session
    ):
        """Test textbooks from other schools are not visible."""
        user, student = student_user

        # Create textbook for different school
        other_textbook = Textbook(
            school_id=student.school_id + 999,  # Different school
            title="Other School Textbook",
            subject="Math",
            grade_level=7,
            is_active=True,
        )
        db_session.add(other_textbook)
        await db_session.commit()

        result = await service.get_textbooks_with_progress(
            student_id=student.id,
            school_id=student.school_id
        )

        # Should not include other school's textbook
        assert len(result) == 0

    async def test_get_textbooks_with_progress_calculates_correctly(
        self, service: StudentContentService, student_user, db_session, textbook1, chapter1
    ):
        """Test progress is calculated correctly with completed paragraphs."""
        user, student = student_user

        # Create 3 paragraphs
        paragraphs = []
        for i in range(3):
            p = Paragraph(
                chapter_id=chapter1.id,
                number=i + 1,
                order=i + 1,
                title=f"Paragraph {i + 1}",
                content="Content...",
            )
            db_session.add(p)
            paragraphs.append(p)
        await db_session.flush()

        # Complete 2 out of 3 paragraphs
        for i in range(2):
            mastery = ParagraphMastery(
                student_id=student.id,
                paragraph_id=paragraphs[i].id,
                is_completed=True,
                last_updated_at=datetime.now(timezone.utc),
            )
            db_session.add(mastery)
        await db_session.commit()

        result = await service.get_textbooks_with_progress(
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        progress = result[0]["progress"]
        assert progress["paragraphs_total"] == 3
        assert progress["paragraphs_completed"] == 2
        assert progress["percentage"] == 66  # 2/3 = 66%

    async def test_get_textbooks_with_progress_mastery_level_a(
        self, service: StudentContentService, student_user, db_session, textbook1, chapter1
    ):
        """Test mastery level A when average score >= 85."""
        user, student = student_user

        # Add chapter mastery with score 90
        mastery = ChapterMastery(
            student_id=student.id,
            chapter_id=chapter1.id,
            mastery_score=90.0,
            mastery_level="A",
        )
        db_session.add(mastery)
        await db_session.commit()

        result = await service.get_textbooks_with_progress(
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["mastery_level"] == "A"

    async def test_get_textbooks_with_progress_mastery_level_b(
        self, service: StudentContentService, student_user, db_session, textbook1, chapter1
    ):
        """Test mastery level B when average score >= 60 and < 85."""
        user, student = student_user

        # Add chapter mastery with score 70
        mastery = ChapterMastery(
            student_id=student.id,
            chapter_id=chapter1.id,
            mastery_score=70.0,
            mastery_level="B",
        )
        db_session.add(mastery)
        await db_session.commit()

        result = await service.get_textbooks_with_progress(
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["mastery_level"] == "B"

    async def test_get_textbooks_with_progress_mastery_level_c(
        self, service: StudentContentService, student_user, db_session, textbook1, chapter1
    ):
        """Test mastery level C when average score < 60."""
        user, student = student_user

        # Add chapter mastery with score 50
        mastery = ChapterMastery(
            student_id=student.id,
            chapter_id=chapter1.id,
            mastery_score=50.0,
            mastery_level="C",
        )
        db_session.add(mastery)
        await db_session.commit()

        result = await service.get_textbooks_with_progress(
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["mastery_level"] == "C"

    # ========== Chapters with Progress Tests ==========

    async def test_get_chapters_with_progress_empty(
        self, service: StudentContentService, student_user, textbook1
    ):
        """Test returns empty list when textbook has no chapters."""
        user, student = student_user

        result = await service.get_chapters_with_progress(
            textbook_id=textbook1.id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert result == []

    async def test_get_chapters_with_progress_status_not_started(
        self, service: StudentContentService, student_user, chapter1, paragraph1
    ):
        """Test first chapter starts with 'not_started' status."""
        user, student = student_user

        result = await service.get_chapters_with_progress(
            textbook_id=chapter1.textbook_id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["status"] == "not_started"

    async def test_get_chapters_with_progress_status_in_progress(
        self, service: StudentContentService, student_user, db_session, chapter1
    ):
        """Test chapter is 'in_progress' when some paragraphs completed."""
        user, student = student_user

        # Create 2 paragraphs
        p1 = Paragraph(chapter_id=chapter1.id, number=1, order=1, title="P1", content="...")
        p2 = Paragraph(chapter_id=chapter1.id, number=2, order=2, title="P2", content="...")
        db_session.add_all([p1, p2])
        await db_session.flush()

        # Complete only 1 paragraph
        mastery = ParagraphMastery(
            student_id=student.id,
            paragraph_id=p1.id,
            is_completed=True,
            last_updated_at=datetime.now(timezone.utc),
        )
        db_session.add(mastery)
        await db_session.commit()

        result = await service.get_chapters_with_progress(
            textbook_id=chapter1.textbook_id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["status"] == "in_progress"
        assert result[0]["progress"]["paragraphs_completed"] == 1
        assert result[0]["progress"]["paragraphs_total"] == 2

    async def test_get_chapters_with_progress_status_completed(
        self, service: StudentContentService, student_user, db_session, chapter1
    ):
        """Test chapter is 'completed' when all paragraphs completed."""
        user, student = student_user

        # Create 1 paragraph
        p = Paragraph(chapter_id=chapter1.id, number=1, order=1, title="P1", content="...")
        db_session.add(p)
        await db_session.flush()

        # Complete it
        mastery = ParagraphMastery(
            student_id=student.id,
            paragraph_id=p.id,
            is_completed=True,
            last_updated_at=datetime.now(timezone.utc),
        )
        db_session.add(mastery)
        await db_session.commit()

        result = await service.get_chapters_with_progress(
            textbook_id=chapter1.textbook_id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["status"] == "completed"

    async def test_get_chapters_with_progress_second_chapter_locked(
        self, service: StudentContentService, student_user, db_session, textbook1
    ):
        """Test second chapter is 'locked' when first is not completed."""
        user, student = student_user

        # Create 2 chapters
        ch1 = Chapter(textbook_id=textbook1.id, number=1, order=1, title="Ch1")
        ch2 = Chapter(textbook_id=textbook1.id, number=2, order=2, title="Ch2")
        db_session.add_all([ch1, ch2])
        await db_session.flush()

        # Add paragraphs to both
        p1 = Paragraph(chapter_id=ch1.id, number=1, order=1, title="P1", content="...")
        p2 = Paragraph(chapter_id=ch2.id, number=1, order=1, title="P2", content="...")
        db_session.add_all([p1, p2])
        await db_session.commit()

        result = await service.get_chapters_with_progress(
            textbook_id=textbook1.id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 2
        assert result[0]["status"] == "not_started"  # First chapter unlocked
        assert result[1]["status"] == "locked"  # Second chapter locked

    async def test_get_chapters_with_progress_has_summative_test(
        self, service: StudentContentService, student_user, db_session, school1, textbook1, chapter1
    ):
        """Test has_summative_test flag when summative test exists."""
        user, student = student_user

        # Create paragraph first
        p = Paragraph(chapter_id=chapter1.id, number=1, order=1, title="P1", content="...")
        db_session.add(p)
        await db_session.flush()

        # Create summative test for chapter
        test = Test(
            school_id=school1.id,
            chapter_id=chapter1.id,
            paragraph_id=p.id,
            title="Summative Test",
            test_purpose=TestPurpose.SUMMATIVE,
            difficulty=DifficultyLevel.MEDIUM,
            time_limit=30,
            passing_score=0.7,
            is_active=True,
        )
        db_session.add(test)
        await db_session.commit()

        result = await service.get_chapters_with_progress(
            textbook_id=textbook1.id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["has_summative_test"] is True

    # ========== Paragraphs with Progress Tests ==========

    async def test_get_paragraphs_with_progress_empty(
        self, service: StudentContentService, student_user, chapter1
    ):
        """Test returns empty list when chapter has no paragraphs."""
        user, student = student_user

        result = await service.get_paragraphs_with_progress(
            chapter_id=chapter1.id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert result == []

    async def test_get_paragraphs_with_progress_status_not_started(
        self, service: StudentContentService, student_user, paragraph1
    ):
        """Test paragraph status is 'not_started' when no mastery record."""
        user, student = student_user

        result = await service.get_paragraphs_with_progress(
            chapter_id=paragraph1.chapter_id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["status"] == "not_started"
        assert result[0]["practice_score"] is None

    async def test_get_paragraphs_with_progress_status_in_progress(
        self, service: StudentContentService, student_user, db_session, paragraph1
    ):
        """Test paragraph status is 'in_progress' when mastery exists but not completed."""
        user, student = student_user

        # Create mastery record (not completed)
        mastery = ParagraphMastery(
            student_id=student.id,
            paragraph_id=paragraph1.id,
            is_completed=False,
            best_score=0.5,
            last_updated_at=datetime.now(timezone.utc),
        )
        db_session.add(mastery)
        await db_session.commit()

        result = await service.get_paragraphs_with_progress(
            chapter_id=paragraph1.chapter_id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["status"] == "in_progress"
        assert result[0]["practice_score"] == 0.5

    async def test_get_paragraphs_with_progress_status_completed(
        self, service: StudentContentService, student_user, db_session, paragraph1
    ):
        """Test paragraph status is 'completed' when mastery is completed."""
        user, student = student_user

        # Create completed mastery record
        mastery = ParagraphMastery(
            student_id=student.id,
            paragraph_id=paragraph1.id,
            is_completed=True,
            best_score=0.9,
            last_updated_at=datetime.now(timezone.utc),
        )
        db_session.add(mastery)
        await db_session.commit()

        result = await service.get_paragraphs_with_progress(
            chapter_id=paragraph1.chapter_id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["status"] == "completed"
        assert result[0]["practice_score"] == 0.9

    async def test_get_paragraphs_with_progress_has_practice(
        self, service: StudentContentService, student_user, db_session, school1, chapter1, paragraph1
    ):
        """Test has_practice flag when formative/practice test exists."""
        user, student = student_user

        # Create formative test for paragraph
        test = Test(
            school_id=school1.id,
            chapter_id=chapter1.id,
            paragraph_id=paragraph1.id,
            title="Practice Test",
            test_purpose=TestPurpose.FORMATIVE,
            difficulty=DifficultyLevel.EASY,
            time_limit=15,
            passing_score=0.6,
            is_active=True,
        )
        db_session.add(test)
        await db_session.commit()

        result = await service.get_paragraphs_with_progress(
            chapter_id=chapter1.id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        assert result[0]["has_practice"] is True

    async def test_get_paragraphs_with_progress_estimated_time(
        self, service: StudentContentService, student_user, db_session, chapter1
    ):
        """Test estimated time is calculated based on content length."""
        user, student = student_user

        # Create paragraph with long content (600 words = 3 minutes)
        long_content = " ".join(["word"] * 600)
        p = Paragraph(
            chapter_id=chapter1.id,
            number=1,
            order=1,
            title="Long Paragraph",
            content=long_content,
        )
        db_session.add(p)
        await db_session.commit()

        result = await service.get_paragraphs_with_progress(
            chapter_id=chapter1.id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert len(result) == 1
        # 600 words // 200 + 3 = 6 minutes
        assert result[0]["estimated_time"] == 6

    # ========== Mastery Level Calculation Tests ==========

    def test_calculate_mastery_level_none(self, service: StudentContentService):
        """Test mastery level is None when no score."""
        level = service._calculate_mastery_level(None)
        assert level is None

    def test_calculate_mastery_level_a(self, service: StudentContentService):
        """Test mastery level A when score >= 85."""
        level = service._calculate_mastery_level(85.0)
        assert level == "A"

        level = service._calculate_mastery_level(100.0)
        assert level == "A"

    def test_calculate_mastery_level_b(self, service: StudentContentService):
        """Test mastery level B when score >= 60 and < 85."""
        level = service._calculate_mastery_level(60.0)
        assert level == "B"

        level = service._calculate_mastery_level(84.9)
        assert level == "B"

    def test_calculate_mastery_level_c(self, service: StudentContentService):
        """Test mastery level C when score < 60."""
        level = service._calculate_mastery_level(59.9)
        assert level == "C"

        level = service._calculate_mastery_level(0.0)
        assert level == "C"

    # ========== School Isolation Tests ==========

    async def test_textbooks_school_isolation(
        self, service: StudentContentService, student_user, student2_user, db_session, textbook1
    ):
        """Test student from school2 cannot see school1's textbooks."""
        user1, student1 = student_user
        user2, student2 = student2_user

        # Student1 should see textbook1
        result1 = await service.get_textbooks_with_progress(
            student_id=student1.id,
            school_id=student1.school_id
        )
        assert len(result1) == 1

        # Student2 should NOT see textbook1 (different school)
        result2 = await service.get_textbooks_with_progress(
            student_id=student2.id,
            school_id=student2.school_id
        )
        assert len(result2) == 0  # No textbooks for school2
