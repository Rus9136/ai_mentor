"""
Mastery Service для отслеживания прогресса студентов.

Базовая версия для Итерации 7:
- Обновление ParagraphMastery после формативных тестов
- Создание MasteryHistory при изменении статуса
- Placeholder для ChapterMastery (полная реализация в Итерации 8)
"""

import logging
from typing import Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mastery import ParagraphMastery, MasteryHistory
from app.repositories.paragraph_mastery_repo import ParagraphMasteryRepository

logger = logging.getLogger(__name__)


class MasteryService:
    """Service for tracking student mastery and progress."""

    def __init__(self, db: AsyncSession):
        """
        Initialize MasteryService.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self.paragraph_repo = ParagraphMasteryRepository(db)

    async def update_paragraph_mastery(
        self,
        student_id: int,
        paragraph_id: int,
        test_score: float,
        test_attempt_id: int,
        school_id: int
    ) -> ParagraphMastery:
        """
        Update paragraph mastery after a formative test.

        This method:
        1. Gets or creates ParagraphMastery record
        2. Updates scores (latest, average, best)
        3. Calculates status (struggling, progressing, mastered)
        4. Creates MasteryHistory if status changed
        5. Marks paragraph as completed (first time)

        Args:
            student_id: Student ID
            paragraph_id: Paragraph ID
            test_score: Test score (0.0 to 1.0)
            test_attempt_id: Test attempt ID (for history tracking)
            school_id: School ID (tenant isolation)

        Returns:
            Updated or created ParagraphMastery

        Status thresholds:
        - mastered: best_score >= 0.85 (85%)
        - progressing: 0.60 <= best_score < 0.85
        - struggling: best_score < 0.60 (60%)
        """
        logger.info(
            f"Updating paragraph mastery: student={student_id}, "
            f"paragraph={paragraph_id}, score={test_score:.2f}"
        )

        # 1. Get existing mastery record
        mastery = await self.paragraph_repo.get_by_student_paragraph(
            student_id=student_id,
            paragraph_id=paragraph_id
        )

        # Store old status for history tracking
        old_status = mastery.status if mastery else None
        old_score = mastery.test_score if mastery else None

        # 2. Calculate new values
        if mastery:
            # Update existing record
            new_attempts_count = mastery.attempts_count + 1
            new_best_score = max(mastery.best_score or 0.0, test_score)

            # Calculate new average (weighted by attempts)
            current_average = mastery.average_score or 0.0
            new_average_score = (
                (current_average * mastery.attempts_count + test_score) /
                new_attempts_count
            )

            update_fields = {
                "test_score": test_score,
                "average_score": new_average_score,
                "best_score": new_best_score,
                "attempts_count": new_attempts_count
            }

            # Mark as completed if not already
            if not mastery.is_completed:
                update_fields["is_completed"] = True
                update_fields["completed_at"] = datetime.utcnow()
                logger.info(
                    f"Marking paragraph {paragraph_id} as completed for student {student_id}"
                )

        else:
            # Create new record
            update_fields = {
                "test_score": test_score,
                "average_score": test_score,
                "best_score": test_score,
                "attempts_count": 1,
                "is_completed": True,
                "completed_at": datetime.utcnow()
            }

        # 3. Calculate new status based on best_score
        new_best_score = update_fields.get("best_score", test_score)

        if new_best_score >= 0.85:
            new_status = "mastered"
        elif new_best_score < 0.60:
            new_status = "struggling"
        else:
            new_status = "progressing"

        update_fields["status"] = new_status

        # 4. Upsert mastery record
        mastery = await self.paragraph_repo.upsert(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            **update_fields
        )

        # 5. Create MasteryHistory if status changed
        if old_status != new_status:
            history = MasteryHistory(
                student_id=student_id,
                paragraph_id=paragraph_id,
                school_id=school_id,
                previous_level=old_status,
                new_level=new_status,
                previous_score=old_score,
                new_score=test_score,
                test_attempt_id=test_attempt_id,
                # Legacy fields (for backward compatibility)
                mastery_score=test_score,
                attempts_count=mastery.attempts_count,
                success_rate=mastery.average_score or 0.0
            )
            self.db.add(history)
            await self.db.commit()

            logger.info(
                f"Mastery status changed for student {student_id}, "
                f"paragraph {paragraph_id}: {old_status} -> {new_status}"
            )
        else:
            logger.info(
                f"Mastery status unchanged: {new_status} "
                f"(score: {test_score:.2f})"
            )

        return mastery

    async def trigger_chapter_recalculation(
        self,
        student_id: int,
        chapter_id: int,
        school_id: int
    ) -> None:
        """
        Trigger chapter mastery recalculation.

        PLACEHOLDER for Iteration 8.

        This will:
        1. Aggregate all paragraph mastery for the chapter
        2. Calculate chapter-level mastery score
        3. Determine A/B/C group
        4. Update ChapterMastery record
        5. Create MasteryHistory if group changed

        Args:
            student_id: Student ID
            chapter_id: Chapter ID
            school_id: School ID

        Note:
            Full implementation will be in Iteration 8 (Mastery Service).
            For now, this is a no-op.
        """
        logger.info(
            f"Chapter mastery recalculation triggered (placeholder): "
            f"student={student_id}, chapter={chapter_id}"
        )

        # TODO: Iteration 8 - Full implementation
        # 1. Get all ParagraphMastery for chapter
        # 2. Calculate aggregated scores
        # 3. Determine mastery_level (A/B/C)
        # 4. Update ChapterMastery
        # 5. Create MasteryHistory if level changed

        pass
