"""
Self-Assessment Service.

Handles self-assessment submission:
- Smart mastery_impact calculation with practice_score correction (Stage 2)
- Practice-aware next_recommendation logic
- Idempotency for offline sync scenarios
- Append-only history recording
- StudentParagraph latest-state update
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import StudentParagraph, ParagraphSelfAssessment
from app.repositories.self_assessment_repo import SelfAssessmentRepository

logger = logging.getLogger(__name__)

# Base impact values (used when practice_score is None)
MASTERY_IMPACT_MAP = {
    "understood": 5.0,
    "questions": 0.0,
    "difficult": -5.0,
}


class SelfAssessmentService:
    """Service for processing student self-assessments."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SelfAssessmentRepository(db)

    async def submit_assessment(
        self,
        student_id: int,
        paragraph_id: int,
        school_id: int,
        rating: str,
        practice_score: Optional[float] = None,
        time_spent: Optional[int] = None,
    ) -> Tuple[ParagraphSelfAssessment, str]:
        """
        Process a self-assessment submission.

        1. Check idempotency (duplicate within 60s)
        2. Calculate mastery_impact with practice_score correction
        3. Determine next_recommendation
        4. Create append-only history record
        5. Update StudentParagraph latest self_assessment fields

        Returns:
            Tuple of (ParagraphSelfAssessment record, next_recommendation string)
        """
        # 1. Idempotency: check for recent duplicate
        existing = await self.repo.find_recent_duplicate(
            student_id=student_id,
            paragraph_id=paragraph_id,
            rating=rating,
        )
        if existing:
            next_recommendation = self._determine_recommendation(rating, practice_score)
            logger.info(
                f"Idempotent hit: student={student_id}, paragraph={paragraph_id}, "
                f"existing_id={existing.id}"
            )
            return existing, next_recommendation

        # 2. Calculate mastery_impact with practice_score correction
        mastery_impact = self._calculate_mastery_impact(rating, practice_score)

        # 3. Determine recommendation
        next_recommendation = self._determine_recommendation(rating, practice_score)

        logger.info(
            f"Processing self-assessment: student={student_id}, "
            f"paragraph={paragraph_id}, rating={rating}, "
            f"practice_score={practice_score}, impact={mastery_impact}, "
            f"recommendation={next_recommendation}"
        )

        # 4. Create append-only history record
        assessment = await self.repo.create(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            rating=rating,
            mastery_impact=mastery_impact,
            practice_score=practice_score,
            time_spent=time_spent,
        )

        # 5. Update StudentParagraph with latest self-assessment state
        await self._update_student_paragraph(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            rating=rating,
        )

        logger.info(
            f"Self-assessment recorded: id={assessment.id}, "
            f"recommendation={next_recommendation}"
        )

        return assessment, next_recommendation

    def _calculate_mastery_impact(
        self, rating: str, practice_score: Optional[float]
    ) -> float:
        """
        Calculate mastery_impact with practice_score correction.

        Based on TASK_SELF_ASSESSMENT_BACKEND.md section 5.1:
        - understood + practice >= 60%: +5.0 (confirmed)
        - understood + practice < 60%:  -2.0 (overconfidence)
        - questions  + practice >= 80%: +2.0 (underconfidence)
        - questions  + practice < 80%:   0.0 (adequate)
        - difficult  + practice >= 80%: +2.0 (underconfidence)
        - difficult  + practice 60-79%: -2.0 (partial)
        - difficult  + practice < 60%:  -5.0 (real problem)
        - No practice data: base values
        """
        if practice_score is None:
            return MASTERY_IMPACT_MAP[rating]

        if rating == "understood":
            return 5.0 if practice_score >= 60 else -2.0
        elif rating == "questions":
            return 2.0 if practice_score >= 80 else 0.0
        elif rating == "difficult":
            if practice_score >= 80:
                return 2.0
            elif practice_score >= 60:
                return -2.0
            else:
                return -5.0

        return MASTERY_IMPACT_MAP.get(rating, 0.0)

    def _determine_recommendation(
        self, rating: str, practice_score: Optional[float]
    ) -> str:
        """
        Determine next_recommendation based on rating and practice_score.

        Based on TASK_SELF_ASSESSMENT_BACKEND.md section 5.2:
        - difficult:                       "review"
        - questions + practice >= 80%:     "next_paragraph"
        - questions + practice < 80%:      "chat_tutor"
        - questions + no practice:         "chat_tutor"
        - understood + practice < 60%:     "practice_retry"
        - understood + practice >= 60%:    "next_paragraph"
        - understood + no practice:        "next_paragraph"
        """
        if rating == "difficult":
            return "review"
        elif rating == "questions":
            if practice_score is not None and practice_score >= 80:
                return "next_paragraph"
            return "chat_tutor"
        elif rating == "understood":
            if practice_score is not None and practice_score < 60:
                return "practice_retry"
            return "next_paragraph"

        return "next_paragraph"

    async def _update_student_paragraph(
        self,
        student_id: int,
        paragraph_id: int,
        school_id: int,
        rating: str,
    ) -> None:
        """Update StudentParagraph with latest self-assessment (preserves existing behavior)."""
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(StudentParagraph).where(
                StudentParagraph.paragraph_id == paragraph_id,
                StudentParagraph.student_id == student_id,
            )
        )
        student_para = result.scalar_one_or_none()

        if not student_para:
            student_para = StudentParagraph(
                student_id=student_id,
                paragraph_id=paragraph_id,
                school_id=school_id,
                self_assessment=rating,
                self_assessment_at=now,
                last_accessed_at=now,
            )
            self.db.add(student_para)
        else:
            student_para.self_assessment = rating
            student_para.self_assessment_at = now
            student_para.last_accessed_at = now

        await self.db.commit()
