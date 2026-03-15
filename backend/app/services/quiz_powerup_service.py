"""
Quiz Power-up Service: activation, validation, score modification.

Power-ups:
- double_points (50 XP): 2x score for the question
- fifty_fifty (75 XP): remove 2 wrong options
- time_freeze (40 XP): +10 seconds on the timer
- shield (60 XP): streak not reset on wrong answer

Constraints:
- One power-up per question per participant (DB unique constraint)
- Only available in timed pacing, classic/team mode
- XP is deducted immediately on activation
"""
import logging
import random
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import QuizSession, QuizParticipant, QuizSessionStatus, QuizParticipantPowerup
from app.models.gamification import XpSourceType
from app.repositories.quiz_powerup_repo import QuizPowerupRepository
from app.repositories.quiz_repo import QuizRepository
from app.services.quiz_question_loader import (
    load_test, get_sorted_questions, get_question_at_index, get_shuffled_options,
)

logger = logging.getLogger(__name__)

POWERUP_COSTS = {
    "double_points": 50,
    "fifty_fifty": 75,
    "time_freeze": 40,
    "shield": 60,
}

TIME_FREEZE_MS = 10000  # +10 seconds

VALID_MODES = {"classic", "team"}


class QuizPowerupService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = QuizPowerupRepository(db)
        self.quiz_repo = QuizRepository(db)

    async def activate_powerup(
        self,
        session: QuizSession,
        participant: QuizParticipant,
        student_id: int,
        powerup_type: str,
    ) -> dict:
        """Validate, deduct XP, create powerup record. Returns confirmation data."""
        # Validate powerup type
        if powerup_type not in POWERUP_COSTS:
            raise ValueError(f"Unknown power-up: {powerup_type}")

        # Validate session state
        if session.status != QuizSessionStatus.IN_PROGRESS:
            raise ValueError("Quiz not in progress")

        mode = session.mode
        pacing = (session.settings or {}).get("pacing", "timed")
        enable_powerups = (session.settings or {}).get("enable_powerups", False)

        if not enable_powerups:
            raise ValueError("Power-ups are not enabled for this quiz")
        if mode not in VALID_MODES:
            raise ValueError("Power-ups not available in this mode")
        if pacing != "timed":
            raise ValueError("Power-ups only available in timed mode")

        question_index = session.current_question_index

        # Check if already has a powerup for this question
        existing = await self.repo.get_powerup(participant.id, question_index)
        if existing:
            raise ValueError("Already used a power-up for this question")

        # Check and deduct XP
        xp_cost = POWERUP_COSTS[powerup_type]
        from app.services.gamification_service import GamificationService
        gamification = GamificationService(self.db)
        deduct_result = await gamification.deduct_xp(
            student_id=student_id,
            school_id=session.school_id,
            amount=xp_cost,
            source_type=XpSourceType.POWERUP_PURCHASE,
            source_id=session.id,
            extra_data={"powerup": powerup_type, "question": question_index},
        )

        # Create powerup record
        powerup = await self.repo.create_powerup(
            quiz_session_id=session.id,
            participant_id=participant.id,
            school_id=session.school_id,
            powerup_type=powerup_type,
            question_index=question_index,
            xp_cost=xp_cost,
        )

        result = {
            "powerup_type": powerup_type,
            "xp_cost": xp_cost,
            "xp_remaining": deduct_result["remaining"],
        }

        # For fifty_fifty: compute which options to remove
        if powerup_type == "fifty_fifty" and session.test_id:
            removed = await self._get_fifty_fifty_options(
                session.test_id, question_index, session.settings or {}, session.id, participant.id,
            )
            result["removed_options"] = removed

        # For time_freeze: return extra time
        if powerup_type == "time_freeze":
            result["extra_time_ms"] = TIME_FREEZE_MS

        await self.db.commit()
        logger.info(
            f"Power-up {powerup_type} activated by participant {participant.id} "
            f"(question {question_index}, cost {xp_cost} XP)"
        )
        return result

    async def get_active_powerup(
        self, participant_id: int, question_index: int,
    ) -> Optional[QuizParticipantPowerup]:
        """Get the active powerup for a participant on a specific question."""
        return await self.repo.get_powerup(participant_id, question_index)

    async def apply_to_score(
        self, powerup_type: str, base_score: int, is_correct: bool,
    ) -> tuple[int, dict]:
        """
        Apply power-up effect to score.
        Returns (modified_score, effects_dict).
        """
        effects = {}

        if powerup_type == "double_points" and is_correct:
            return base_score * 2, {"score_doubled": True}

        if powerup_type == "shield" and not is_correct:
            effects["streak_protected"] = True

        return base_score, effects

    async def mark_applied(self, powerup_id: int) -> None:
        """Mark a powerup as applied (used during answer submission)."""
        await self.repo.mark_applied(powerup_id)

    async def _get_fifty_fifty_options(
        self, test_id: int, question_index: int, settings: dict,
        session_id: int, participant_id: int,
    ) -> list[int]:
        """Return indices of 2 wrong options to remove."""
        test = await load_test(self.db, test_id)
        if not test:
            return []

        questions = get_sorted_questions(test)
        q = get_question_at_index(questions, question_index, settings, session_id)
        if not q:
            return []

        options = get_shuffled_options(q, settings, session_id, question_index)

        # Find wrong option indices
        wrong_indices = [i for i, o in enumerate(options) if not o.is_correct]
        if len(wrong_indices) <= 2:
            return wrong_indices

        # Deterministic random selection
        rng = random.Random(session_id * 100000 + question_index * 100 + participant_id)
        return sorted(rng.sample(wrong_indices, 2))
