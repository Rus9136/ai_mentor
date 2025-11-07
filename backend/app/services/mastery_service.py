"""
Mastery Service для отслеживания прогресса студентов.

Итерация 8: Полная реализация A/B/C алгоритма группировки.
- Обновление ParagraphMastery после формативных тестов (Итерация 7)
- Расчет ChapterMastery с A/B/C уровнями (Итерация 8)
- Создание MasteryHistory при изменении статуса/уровня
"""

import logging
from typing import Optional, Tuple, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mastery import ParagraphMastery, MasteryHistory, ChapterMastery
from app.models.test_attempt import TestAttempt
from app.models.test import TestPurpose
from app.repositories.paragraph_mastery_repo import ParagraphMasteryRepository
from app.repositories.chapter_mastery_repo import ChapterMasteryRepository
from app.repositories.test_attempt_repo import TestAttemptRepository

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
        self.chapter_repo = ChapterMasteryRepository(db)
        self.test_attempt_repo = TestAttemptRepository(db)

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
        school_id: int,
        test_attempt: Optional[TestAttempt] = None
    ) -> Optional[ChapterMastery]:
        """
        Trigger chapter mastery recalculation.

        Called after ANY test attempt (formative or summative) is graded.

        This will:
        1. Get last 5 test attempts for the chapter
        2. Calculate weighted average, trend, consistency
        3. Determine A/B/C mastery level
        4. Update ChapterMastery record (with paragraph stats, summative results)
        5. Create MasteryHistory if level changed

        Args:
            student_id: Student ID
            chapter_id: Chapter ID
            school_id: School ID
            test_attempt: Optional test attempt that triggered recalculation

        Returns:
            Updated ChapterMastery record, or None if chapter not found
        """
        logger.info(
            f"Triggering chapter mastery recalculation: "
            f"student={student_id}, chapter={chapter_id}"
        )

        # Calculate A/B/C mastery level
        level, score = await self.calculate_chapter_mastery(
            student_id=student_id,
            chapter_id=chapter_id,
            school_id=school_id,
            test_attempt=test_attempt
        )

        logger.info(
            f"Chapter mastery recalculated: level={level}, score={score:.2f}"
        )

        # Get updated ChapterMastery record
        mastery = await self.chapter_repo.get_by_student_chapter(
            student_id=student_id,
            chapter_id=chapter_id
        )

        return mastery

    # ========================================================================
    # PRIVATE HELPER METHODS FOR A/B/C ALGORITHM (Iteration 8)
    # ========================================================================

    def _calculate_weighted_average(self, attempts: List[TestAttempt]) -> float:
        """
        Calculate weighted average score (newer attempts have higher weight).

        Weights: [0.35, 0.25, 0.20, 0.12, 0.08]

        Args:
            attempts: List of test attempts (sorted DESC by completed_at)

        Returns:
            Weighted average score (0.0 to 100.0)

        Note:
            CRITICAL: TestAttempt.score is 0.0-1.0, so we multiply by 100
        """
        weights = [0.35, 0.25, 0.20, 0.12, 0.08]

        # Convert scores from 0-1 to 0-100
        scores = [a.score * 100 for a in attempts]

        # Calculate weighted average
        total_weight = sum(weights[:len(scores)])
        weighted_sum = sum(s * w for s, w in zip(scores, weights[:len(scores)]))

        return weighted_sum / total_weight

    def _calculate_trend(self, attempts: List[TestAttempt]) -> float:
        """
        Calculate trend: improvement (+) or degradation (-).

        Compares first 2 attempts (newest) vs last 2 attempts (oldest).

        Args:
            attempts: List of test attempts (sorted DESC by completed_at)

        Returns:
            Trend value (difference in percentage points)
        """
        if len(attempts) < 3:
            return 0.0

        # Recent attempts (first 2 in DESC sorted list)
        recent_avg = sum(a.score * 100 for a in attempts[:2]) / 2

        # Older attempts (last 2)
        older_avg = sum(a.score * 100 for a in attempts[-2:]) / 2

        # Positive trend = improvement
        return recent_avg - older_avg

    def _calculate_consistency(self, attempts: List[TestAttempt], avg: float) -> float:
        """
        Calculate consistency of results (standard deviation).

        Args:
            attempts: List of test attempts
            avg: Average score (for variance calculation)

        Returns:
            Standard deviation
        """
        scores = [a.score * 100 for a in attempts]
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        return variance ** 0.5

    def _determine_mastery_level(
        self,
        weighted_avg: float,
        trend: float,
        std_dev: float
    ) -> Tuple[str, float]:
        """
        Determine A/B/C mastery level based on metrics.

        Criteria:
        - A: weighted_avg >= 85 AND (trend >= 0 OR std_dev < 10)
        - C: weighted_avg < 60 OR (weighted_avg < 70 AND trend < -10)
        - B: everything else

        Args:
            weighted_avg: Weighted average score (0-100)
            trend: Trend value (positive = improving)
            std_dev: Standard deviation (consistency)

        Returns:
            Tuple of (mastery_level, mastery_score)
        """
        if weighted_avg >= 85 and (trend >= 0 or std_dev < 10):
            level = 'A'
            score = min(100.0, weighted_avg + (trend * 0.2))
        elif weighted_avg < 60 or (weighted_avg < 70 and trend < -10):
            level = 'C'
            score = max(0.0, weighted_avg + (trend * 0.2))
        else:
            level = 'B'
            score = weighted_avg

        return (level, round(score, 2))

    # ========================================================================
    # MAIN CHAPTER MASTERY CALCULATION (Iteration 8)
    # ========================================================================

    async def calculate_chapter_mastery(
        self,
        student_id: int,
        chapter_id: int,
        school_id: int,
        test_attempt: Optional[TestAttempt] = None
    ) -> Tuple[str, float]:
        """
        Calculate A/B/C mastery level for a chapter.

        Algorithm:
        1. Get last 5 test attempts for the chapter
        2. If < 3 attempts → default to C, 0.0
        3. Calculate weighted_avg, trend, std_dev
        4. Determine mastery_level (A/B/C)
        5. Update ChapterMastery (+ summative, paragraph stats)
        6. Create MasteryHistory if level changed

        Args:
            student_id: Student ID
            chapter_id: Chapter ID
            school_id: School ID (tenant isolation)
            test_attempt: Pass if called after summative test (for summative_score)

        Returns:
            Tuple of (mastery_level, mastery_score)
        """
        logger.info(
            f"Calculating chapter mastery: student={student_id}, chapter={chapter_id}"
        )

        # 1. Get recent test attempts
        attempts = await self.test_attempt_repo.get_chapter_attempts(
            student_id=student_id,
            chapter_id=chapter_id,
            school_id=school_id,
            limit=5
        )

        logger.info(f"Found {len(attempts)} completed attempts for chapter {chapter_id}")

        # 2. Insufficient data → default to C
        if len(attempts) < 3:
            logger.info(
                f"Insufficient data ({len(attempts)} attempts), defaulting to C, 0.0"
            )
            await self._update_chapter_mastery_record(
                student_id=student_id,
                chapter_id=chapter_id,
                school_id=school_id,
                mastery_level='C',
                mastery_score=0.0,
                test_attempt=test_attempt
            )
            return ('C', 0.0)

        # 3. Calculate metrics
        weighted_avg = self._calculate_weighted_average(attempts)
        trend = self._calculate_trend(attempts)
        std_dev = self._calculate_consistency(attempts, weighted_avg)

        logger.info(
            f"Metrics: weighted_avg={weighted_avg:.2f}, "
            f"trend={trend:.2f}, std_dev={std_dev:.2f}"
        )

        # 4. Determine mastery level
        level, score = self._determine_mastery_level(weighted_avg, trend, std_dev)

        logger.info(f"Determined level: {level}, score: {score}")

        # 5. Update ChapterMastery record
        mastery = await self._update_chapter_mastery_record(
            student_id=student_id,
            chapter_id=chapter_id,
            school_id=school_id,
            mastery_level=level,
            mastery_score=score,
            test_attempt=test_attempt
        )

        # 6. Create history if changed
        await self._create_mastery_history_if_changed(
            mastery=mastery,
            new_level=level,
            new_score=score,
            test_attempt_id=test_attempt.id if test_attempt else None,
            school_id=school_id
        )

        return (level, score)

    async def _update_chapter_mastery_record(
        self,
        student_id: int,
        chapter_id: int,
        school_id: int,
        mastery_level: str,
        mastery_score: float,
        test_attempt: Optional[TestAttempt] = None
    ) -> ChapterMastery:
        """
        Update ChapterMastery record with all fields.

        Updates:
        - mastery_level, mastery_score
        - progress_percentage
        - total/completed/mastered/struggling_paragraphs counters
        - summative_score/summative_passed (if summative test)

        Args:
            student_id: Student ID
            chapter_id: Chapter ID
            school_id: School ID
            mastery_level: A, B, or C
            mastery_score: 0.0 to 100.0
            test_attempt: Optional test attempt (for summative_score)

        Returns:
            Updated or created ChapterMastery
        """
        # 1. Get existing record for old values (for history tracking)
        existing = await self.chapter_repo.get_by_student_chapter(
            student_id=student_id,
            chapter_id=chapter_id
        )

        old_level = existing.mastery_level if existing else None
        old_score = existing.mastery_score if existing else None

        # 2. Get paragraph stats
        para_stats = await self.paragraph_repo.get_chapter_stats(
            student_id=student_id,
            chapter_id=chapter_id
        )

        logger.info(
            f"Paragraph stats: total={para_stats['total']}, "
            f"completed={para_stats['completed']}, "
            f"mastered={para_stats['mastered']}, "
            f"struggling={para_stats['struggling']}"
        )

        # 3. Calculate progress percentage
        progress_pct = 0
        if para_stats['total'] > 0:
            progress_pct = int(100 * para_stats['completed'] / para_stats['total'])

        # 4. Prepare update fields
        update_fields = {
            "mastery_level": mastery_level,
            "mastery_score": mastery_score,
            "progress_percentage": progress_pct,

            # Paragraph counters
            "total_paragraphs": para_stats['total'],
            "completed_paragraphs": para_stats['completed'],
            "mastered_paragraphs": para_stats['mastered'],
            "struggling_paragraphs": para_stats['struggling'],
        }

        # 5. Summative test results (if applicable)
        if (test_attempt and
            hasattr(test_attempt, 'test') and
            test_attempt.test.test_purpose == TestPurpose.SUMMATIVE):
            update_fields["summative_score"] = test_attempt.score
            update_fields["summative_passed"] = test_attempt.passed
            logger.info(
                f"Updating summative results: score={test_attempt.score:.2f}, "
                f"passed={test_attempt.passed}"
            )

        # 6. Upsert ChapterMastery
        mastery = await self.chapter_repo.upsert(
            student_id=student_id,
            chapter_id=chapter_id,
            school_id=school_id,
            **update_fields
        )

        # 7. Attach old values for history tracking
        mastery._old_level = old_level
        mastery._old_score = old_score

        logger.info(f"ChapterMastery updated: level={mastery_level}, score={mastery_score}")

        return mastery

    async def _create_mastery_history_if_changed(
        self,
        mastery: ChapterMastery,
        new_level: str,
        new_score: float,
        test_attempt_id: Optional[int],
        school_id: int
    ) -> None:
        """
        Create MasteryHistory if level changed.

        Note:
        - Compares old_level (from mastery._old_level) vs new_level
        - On first creation (old_level=None), history is NOT created
        - Only creates history when level actually changes (C→B, B→A, etc.)

        Args:
            mastery: ChapterMastery record (with _old_level, _old_score attached)
            new_level: New mastery level (A/B/C)
            new_score: New mastery score (0-100)
            test_attempt_id: Test attempt that triggered this change
            school_id: School ID
        """
        # Get old values from attached attributes
        old_level = getattr(mastery, '_old_level', None)
        old_score = getattr(mastery, '_old_score', None)

        # Only create history if level changed (and not first creation)
        if old_level and old_level != new_level:
            history = MasteryHistory(
                student_id=mastery.student_id,
                chapter_id=mastery.chapter_id,
                paragraph_id=None,  # chapter-level history
                school_id=school_id,
                previous_level=old_level,
                new_level=new_level,
                previous_score=old_score,
                new_score=new_score,
                test_attempt_id=test_attempt_id,
                # Legacy fields for backward compatibility
                mastery_score=new_score,
                attempts_count=1,
                success_rate=new_score / 100.0
            )
            self.db.add(history)
            await self.db.commit()

            logger.info(
                f"MasteryHistory created: {old_level} → {new_level} "
                f"(score: {old_score:.2f} → {new_score:.2f})"
            )
        else:
            logger.info(
                f"MasteryHistory NOT created: level unchanged ({new_level}) "
                f"or first creation"
            )
