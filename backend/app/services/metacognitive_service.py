"""
Metacognitive Pattern Detection Service.

Analyzes the alignment between student self-assessments and actual test
performance to detect metacognitive patterns:
- overconfident: thinks they understand, but scores are low (Dunning-Kruger)
- underconfident: thinks it's difficult, but scores are high (Impostor Syndrome)
- well_calibrated: self-assessment matches test performance

Recalculated after each self-assessment when >= 5 records exist.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import ParagraphSelfAssessment
from app.models.mastery import ParagraphMastery
from app.models.student import Student

logger = logging.getLogger(__name__)

# Minimum assessments required for pattern detection
MIN_ASSESSMENTS = 5

# Thresholds for pattern detection
OVERCONFIDENT_UNDERSTOOD_MIN = 4  # out of last 5
OVERCONFIDENT_SCORE_MAX = 0.60

UNDERCONFIDENT_DIFFICULT_MIN = 4  # out of last 5
UNDERCONFIDENT_SCORE_MIN = 0.80

# Alignment scoring: maps rating → expected score range
RATING_EXPECTED = {
    "understood": (0.70, 1.0),
    "questions": (0.40, 0.70),
    "difficult": (0.0, 0.50),
}
WELL_CALIBRATED_THRESHOLD = 0.6  # 60% of assessments must align

# Coaching messages per pattern
COACHING_MESSAGES = {
    "overconfident": {
        "ru": "Ты часто оцениваешь себя выше результатов тестов. Попробуй перед самооценкой ответить на контрольный вопрос.",
        "kk": "Сен өз білімінді тест нәтижелерінен жоғары бағалайсың. Өзін-өзі бағалау алдында бақылау сұрағына жауап беріп көр.",
    },
    "underconfident": {
        "ru": "Ты знаешь больше, чем думаешь! Твои результаты тестов стабильно высокие. Доверяй себе.",
        "kk": "Сен ойлағаннан көп білесің! Тест нәтижелерің тұрақты жоғары. Өзіңе сен.",
    },
    "well_calibrated": {
        "ru": "Отлично! Ты точно оцениваешь свой уровень знаний. Это ценный навык.",
        "kk": "Керемет! Сен өз білім деңгейіңді дұрыс бағалайсың. Бұл құнды дағды.",
    },
}


class MetacognitiveService:
    """Service for detecting and managing metacognitive patterns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_and_update(
        self,
        student_id: int,
        school_id: int,
    ) -> Optional[str]:
        """
        Analyze student's metacognitive pattern and update the student record.

        Called after each self-assessment submission.
        Requires >= 5 self-assessments to produce a result.

        Returns:
            Pattern string or None if insufficient data
        """
        # Get recent self-assessments (last 10, newest first)
        assessments = await self._get_recent_assessments(student_id, limit=10)

        if len(assessments) < MIN_ASSESSMENTS:
            logger.debug(
                f"Insufficient assessments for student {student_id}: "
                f"{len(assessments)}/{MIN_ASSESSMENTS}"
            )
            return None

        # Get mastery records for the assessed paragraphs
        paragraph_ids = list({a.paragraph_id for a in assessments})
        mastery_map = await self._get_mastery_map(student_id, paragraph_ids)

        # Detect pattern using last 5 assessments
        last_5 = assessments[:5]
        pattern = self._detect_pattern(last_5, mastery_map)

        # Update student record
        await self._update_student_pattern(student_id, pattern)

        if pattern:
            logger.info(
                f"Metacognitive pattern detected: student={student_id}, "
                f"pattern={pattern}"
            )

        return pattern

    def _detect_pattern(
        self,
        assessments: List[ParagraphSelfAssessment],
        mastery_map: dict,
    ) -> Optional[str]:
        """
        Detect metacognitive pattern from assessments and mastery data.

        Priority: overconfident > underconfident > well_calibrated > None
        """
        # Count ratings
        understood_count = sum(1 for a in assessments if a.rating == "understood")
        difficult_count = sum(1 for a in assessments if a.rating == "difficult")

        # Get test scores for assessed paragraphs
        scores = []
        for a in assessments:
            mastery = mastery_map.get(a.paragraph_id)
            if mastery and mastery.effective_score > 0:
                scores.append(mastery.effective_score)

        if not scores:
            return None

        avg_score = sum(scores) / len(scores)

        # Pattern 1: Overconfident (Dunning-Kruger)
        if (understood_count >= OVERCONFIDENT_UNDERSTOOD_MIN
                and avg_score < OVERCONFIDENT_SCORE_MAX):
            return "overconfident"

        # Pattern 2: Underconfident (Impostor Syndrome)
        if (difficult_count >= UNDERCONFIDENT_DIFFICULT_MIN
                and avg_score > UNDERCONFIDENT_SCORE_MIN):
            return "underconfident"

        # Pattern 3: Well-calibrated (good alignment)
        aligned = 0
        total_with_score = 0
        for a in assessments:
            mastery = mastery_map.get(a.paragraph_id)
            if not mastery or mastery.effective_score <= 0:
                continue
            total_with_score += 1
            expected_range = RATING_EXPECTED.get(a.rating)
            if expected_range:
                lo, hi = expected_range
                if lo <= mastery.effective_score <= hi:
                    aligned += 1

        if total_with_score >= 3:
            alignment_ratio = aligned / total_with_score
            if alignment_ratio >= WELL_CALIBRATED_THRESHOLD:
                return "well_calibrated"

        return None

    async def get_student_insight(
        self,
        student_id: int,
        lang: str = "ru",
    ) -> dict:
        """
        Get metacognitive insight for a student (for API response).

        Returns:
            Dict with pattern, message, and stats
        """
        result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()

        pattern = student.metacognitive_pattern if student else None
        message = None
        if pattern and pattern in COACHING_MESSAGES:
            message = COACHING_MESSAGES[pattern].get(lang, COACHING_MESSAGES[pattern]["ru"])

        # Get assessment stats
        assessments = await self._get_recent_assessments(student_id, limit=10)
        total = len(assessments)
        understood = sum(1 for a in assessments if a.rating == "understood")
        questions = sum(1 for a in assessments if a.rating == "questions")
        difficult = sum(1 for a in assessments if a.rating == "difficult")

        return {
            "pattern": pattern,
            "message": message,
            "updated_at": student.metacognitive_updated_at if student else None,
            "recent_assessments": total,
            "rating_breakdown": {
                "understood": understood,
                "questions": questions,
                "difficult": difficult,
            },
        }

    async def _get_recent_assessments(
        self,
        student_id: int,
        limit: int = 10,
    ) -> List[ParagraphSelfAssessment]:
        """Get recent self-assessments, newest first."""
        result = await self.db.execute(
            select(ParagraphSelfAssessment)
            .where(ParagraphSelfAssessment.student_id == student_id)
            .order_by(ParagraphSelfAssessment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _get_mastery_map(
        self,
        student_id: int,
        paragraph_ids: List[int],
    ) -> dict:
        """Get mastery records as {paragraph_id: ParagraphMastery}."""
        if not paragraph_ids:
            return {}
        result = await self.db.execute(
            select(ParagraphMastery).where(
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.paragraph_id.in_(paragraph_ids),
            )
        )
        records = result.scalars().all()
        return {m.paragraph_id: m for m in records}

    async def _update_student_pattern(
        self,
        student_id: int,
        pattern: Optional[str],
    ) -> None:
        """Update metacognitive_pattern on student record."""
        result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        if student:
            student.metacognitive_pattern = pattern
            student.metacognitive_updated_at = datetime.now(timezone.utc)
            await self.db.flush()
