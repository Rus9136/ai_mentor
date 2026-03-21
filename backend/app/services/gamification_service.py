"""
Gamification Service: XP awards, level-up, achievement checks, streaks.

This is the core service that other services call via hooks when
gamification-relevant events occur (test passed, mastery changed, etc.).
"""
import logging
import math
from datetime import date, datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.gamification import XpSourceType, Achievement, StudentAchievement
from app.models.mastery import ParagraphMastery
from app.models.test_attempt import TestAttempt, AttemptStatus
from app.repositories.gamification_repo import GamificationRepository

logger = logging.getLogger(__name__)

# ── XP Reward Constants ──
XP_FORMATIVE_BASE = 10
XP_FORMATIVE_SCORE_MULT = 20
XP_SUMMATIVE_BASE = 25
XP_SUMMATIVE_SCORE_MULT = 50
XP_PERFECT_BONUS = 15
XP_FIRST_ATTEMPT_BONUS = 10
XP_MASTERY_STRUGGLING_TO_PROGRESSING = 15
XP_MASTERY_PROGRESSING_TO_MASTERED = 30
XP_CHAPTER_C_TO_B = 50
XP_CHAPTER_B_TO_A = 100
XP_STREAK_PER_DAY = 5
XP_STREAK_CAP = 30  # max streak multiplier
XP_SELF_ASSESSMENT = 5
XP_SPACED_REVIEW = 10
XP_PARAGRAPH_COMPLETE = 5


class GamificationService:
    """Service for awarding XP, checking levels, achievements, and streaks."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GamificationRepository(db)

    # ══════════════════════════════════════════════════════════════════════
    # LEVEL CALCULATION
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def xp_for_level(level: int) -> int:
        """XP required to go FROM level to level+1."""
        return int(100 * level ** 1.5)

    @staticmethod
    def calculate_level(total_xp: int) -> tuple[int, int, int]:
        """
        Calculate level from total XP.

        Returns:
            (level, xp_in_current_level, xp_to_next_level)
        """
        level = 1
        cumulative = 0
        while True:
            needed = int(100 * (level + 1) ** 1.5)
            if cumulative + needed > total_xp:
                xp_in_current = total_xp - cumulative
                xp_to_next = needed - xp_in_current
                return level, xp_in_current, xp_to_next
            cumulative += needed
            level += 1

    # ══════════════════════════════════════════════════════════════════════
    # CORE: AWARD XP
    # ══════════════════════════════════════════════════════════════════════

    async def award_xp(
        self,
        student_id: int,
        school_id: int,
        amount: int,
        source_type: XpSourceType,
        source_id: Optional[int] = None,
        extra_data: Optional[dict] = None,
    ) -> dict:
        """
        Award XP to a student. Returns summary with level-up info.

        This is the single point of XP entry — all hooks call this.
        """
        from app.core.config import settings
        if not settings.GAMIFICATION_ENABLED:
            return {"amount": 0, "level_up": False}

        if amount <= 0:
            return {"amount": 0, "level_up": False}

        # Record transaction + atomic increment
        await self.repo.add_xp_transaction(
            student_id=student_id,
            school_id=school_id,
            amount=amount,
            source_type=source_type,
            source_id=source_id,
            extra_data=extra_data,
        )

        # Check level up
        new_total_xp, old_level = await self.repo.get_student_xp(student_id)
        new_level, _, _ = self.calculate_level(new_total_xp)
        level_up = new_level > old_level

        if level_up:
            await self.repo.update_student_level(student_id, new_level)
            logger.info(f"Student {student_id} leveled up: {old_level} -> {new_level}")

        logger.info(
            f"Awarded {amount} XP to student {student_id} "
            f"(source={source_type.value}, total={new_total_xp})"
        )

        return {
            "amount": amount,
            "new_total_xp": new_total_xp,
            "new_level": new_level,
            "level_up": level_up,
        }

    async def deduct_xp(
        self,
        student_id: int,
        school_id: int,
        amount: int,
        source_type: XpSourceType,
        source_id: Optional[int] = None,
        extra_data: Optional[dict] = None,
    ) -> dict:
        """
        Deduct XP for purchases (power-ups, etc.). Amount must be positive.
        Creates a negative XP transaction and decrements student.total_xp.
        Raises ValueError if insufficient XP.
        """
        from app.core.config import settings
        if not settings.GAMIFICATION_ENABLED:
            return {"deducted": 0, "remaining": 0}

        if amount <= 0:
            raise ValueError("Deduction amount must be positive")

        from app.models.student import Student
        student = await self.db.get(Student, student_id)
        if not student or (student.total_xp or 0) < amount:
            raise ValueError("Not enough XP")

        await self.repo.add_xp_transaction(
            student_id=student_id,
            school_id=school_id,
            amount=-amount,
            source_type=source_type,
            source_id=source_id,
            extra_data=extra_data,
        )

        remaining = (student.total_xp or 0) - amount
        logger.info(f"Deducted {amount} XP from student {student_id} (source={source_type.value}, remaining={remaining})")
        return {"deducted": amount, "remaining": remaining}

    # ══════════════════════════════════════════════════════════════════════
    # CONTENT CHAIN RESOLUTION
    # ══════════════════════════════════════════════════════════════════════

    async def _resolve_content_chain(self, paragraph_id: int) -> tuple[Optional[int], Optional[int]]:
        """Resolve paragraph -> textbook -> subject chain. Returns (subject_id, textbook_id)."""
        from app.models.paragraph import Paragraph
        from app.models.chapter import Chapter
        from app.models.textbook import Textbook
        result = await self.db.execute(
            select(Textbook.subject_id, Textbook.id)
            .join(Chapter, Chapter.textbook_id == Textbook.id)
            .join(Paragraph, Paragraph.chapter_id == Chapter.id)
            .where(Paragraph.id == paragraph_id)
        )
        row = result.one_or_none()
        if row:
            return row[0], row[1]
        return None, None

    # ══════════════════════════════════════════════════════════════════════
    # HOOKS (called from other services)
    # ══════════════════════════════════════════════════════════════════════

    async def on_test_passed(
        self,
        student_id: int,
        school_id: int,
        test_score: float,
        test_purpose: str,
        attempt_number: int,
        test_attempt_id: int,
        paragraph_id: Optional[int] = None,
        textbook_id: Optional[int] = None,
        subject_id: Optional[int] = None,
    ) -> None:
        """Hook: called when a student passes a test."""
        # Calculate base XP
        if test_purpose == "summative":
            xp = XP_SUMMATIVE_BASE + round(test_score * XP_SUMMATIVE_SCORE_MULT)
        else:
            xp = XP_FORMATIVE_BASE + round(test_score * XP_FORMATIVE_SCORE_MULT)

        # Bonuses
        if test_score >= 1.0:
            xp += XP_PERFECT_BONUS
        if attempt_number == 1:
            xp += XP_FIRST_ATTEMPT_BONUS

        await self.award_xp(
            student_id=student_id,
            school_id=school_id,
            amount=xp,
            source_type=XpSourceType.TEST_PASSED,
            source_id=test_attempt_id,
            extra_data={"score": test_score, "purpose": test_purpose, "attempt": attempt_number},
        )

        # Update streak
        await self.update_streak(student_id, school_id)

        # Check achievements (learning only — not coding)
        await self.check_achievements(student_id, school_id, context="learning")

        # Resolve content chain if we have paragraph_id but not subject/textbook
        if paragraph_id and not subject_id:
            subject_id, textbook_id = await self._resolve_content_chain(paragraph_id)

        # Increment daily quest (complete_tests)
        today = date.today()
        completed_quests = await self.repo.increment_daily_quest(
            student_id, school_id, "complete_tests", today,
            subject_id=subject_id, textbook_id=textbook_id, paragraph_id=paragraph_id,
        )
        # Award XP for completed quests
        for cq in completed_quests:
            quest = cq.quest
            if quest and quest.xp_reward > 0:
                await self.award_xp(
                    student_id=student_id,
                    school_id=school_id,
                    amount=quest.xp_reward,
                    source_type=XpSourceType.DAILY_QUEST,
                    source_id=cq.id,
                )

    async def on_mastery_change(
        self,
        student_id: int,
        school_id: int,
        old_status: Optional[str],
        new_status: str,
        paragraph_id: int,
        test_attempt_id: Optional[int] = None,
    ) -> None:
        """Hook: called when paragraph mastery status changes."""
        xp = 0
        if old_status == "struggling" and new_status == "progressing":
            xp = XP_MASTERY_STRUGGLING_TO_PROGRESSING
        elif old_status == "progressing" and new_status == "mastered":
            xp = XP_MASTERY_PROGRESSING_TO_MASTERED
        elif old_status == "struggling" and new_status == "mastered":
            # struggling -> mastered directly = both bonuses
            xp = XP_MASTERY_STRUGGLING_TO_PROGRESSING + XP_MASTERY_PROGRESSING_TO_MASTERED

        if xp > 0:
            await self.award_xp(
                student_id=student_id,
                school_id=school_id,
                amount=xp,
                source_type=XpSourceType.MASTERY_UP,
                source_id=paragraph_id,
                extra_data={"old_status": old_status, "new_status": new_status},
            )

        # Check mastery-related achievements (learning only)
        await self.check_achievements(student_id, school_id, context="learning")

        # Daily quest: master_paragraph
        if new_status == "mastered":
            today = date.today()
            # Resolve content chain
            subject_id_resolved, textbook_id_resolved = await self._resolve_content_chain(paragraph_id)
            completed_quests = await self.repo.increment_daily_quest(
                student_id, school_id, "master_paragraph", today,
                subject_id=subject_id_resolved, textbook_id=textbook_id_resolved,
                paragraph_id=paragraph_id,
            )
            for cq in completed_quests:
                quest = cq.quest
                if quest and quest.xp_reward > 0:
                    await self.award_xp(
                        student_id=student_id,
                        school_id=school_id,
                        amount=quest.xp_reward,
                        source_type=XpSourceType.DAILY_QUEST,
                        source_id=cq.id,
                    )

    async def on_chapter_level_change(
        self,
        student_id: int,
        school_id: int,
        old_level: str,
        new_level: str,
        chapter_id: int,
    ) -> None:
        """Hook: called when chapter mastery level changes (A/B/C)."""
        xp = 0
        if old_level == "C" and new_level == "B":
            xp = XP_CHAPTER_C_TO_B
        elif old_level == "B" and new_level == "A":
            xp = XP_CHAPTER_B_TO_A
        elif old_level == "C" and new_level == "A":
            xp = XP_CHAPTER_C_TO_B + XP_CHAPTER_B_TO_A

        if xp > 0:
            await self.award_xp(
                student_id=student_id,
                school_id=school_id,
                amount=xp,
                source_type=XpSourceType.CHAPTER_COMPLETE,
                source_id=chapter_id,
                extra_data={"old_level": old_level, "new_level": new_level},
            )
            await self.check_achievements(student_id, school_id, context="learning")

    async def on_self_assessment(
        self,
        student_id: int,
        school_id: int,
        paragraph_id: Optional[int] = None,
    ) -> None:
        """Hook: called when student submits a self-assessment."""
        await self.award_xp(
            student_id=student_id,
            school_id=school_id,
            amount=XP_SELF_ASSESSMENT,
            source_type=XpSourceType.SELF_ASSESSMENT,
            source_id=paragraph_id,
        )

        # Update streak
        await self.update_streak(student_id, school_id)

        # Check achievements (learning only)
        await self.check_achievements(student_id, school_id, context="learning")

    async def on_paragraph_complete(
        self,
        student_id: int,
        school_id: int,
        paragraph_id: int,
    ) -> None:
        """Hook: called when student completes a paragraph (all steps done)."""
        await self.award_xp(
            student_id=student_id,
            school_id=school_id,
            amount=XP_PARAGRAPH_COMPLETE,
            source_type=XpSourceType.PARAGRAPH_COMPLETE,
            source_id=paragraph_id,
        )

        # Update streak
        await self.update_streak(student_id, school_id)

        # Check achievements (learning only)
        await self.check_achievements(student_id, school_id, context="learning")

    async def on_coding_challenge_solved(
        self,
        student_id: int,
        school_id: int,
        challenge_id: int,
        xp_earned: int,
        difficulty: str = "easy",
        execution_time_ms: Optional[int] = None,
    ) -> None:
        """Hook: called when student solves a coding challenge for the first time."""
        # 1. Award XP
        await self.award_xp(
            student_id=student_id,
            school_id=school_id,
            amount=xp_earned,
            source_type=XpSourceType.CODING_CHALLENGE,
            source_id=challenge_id,
            extra_data={
                "difficulty": difficulty,
                "execution_time_ms": execution_time_ms,
            },
        )

        # 2. Update streak
        await self.update_streak(student_id, school_id)

        # 3. Check achievements (coding only — not learning)
        await self.check_achievements(student_id, school_id, context="coding")

        # 4. Increment daily quest (solve_challenge)
        today = date.today()
        completed_quests = await self.repo.increment_daily_quest(
            student_id, school_id, "solve_challenge", today,
        )
        # 5. Award XP for completed daily quests
        for cq in completed_quests:
            quest = cq.quest
            if quest and quest.xp_reward > 0:
                await self.award_xp(
                    student_id=student_id,
                    school_id=school_id,
                    amount=quest.xp_reward,
                    source_type=XpSourceType.DAILY_QUEST,
                    source_id=cq.id,
                )

    async def on_course_completed(
        self,
        student_id: int,
        school_id: int,
        course_id: int,
    ) -> None:
        """Hook: called when student completes a coding course."""
        await self.award_xp(
            student_id=student_id,
            school_id=school_id,
            amount=100,
            source_type=XpSourceType.COURSE_COMPLETE,
            source_id=course_id,
        )
        await self.check_achievements(student_id, school_id, context="coding")

    # ══════════════════════════════════════════════════════════════════════
    # STREAK
    # ══════════════════════════════════════════════════════════════════════

    async def update_streak(self, student_id: int, school_id: int) -> None:
        """Update daily streak. Called on any significant learning activity."""
        today = date.today()
        current_streak, longest_streak, last_activity = await self.repo.get_student_streak_info(student_id)

        if last_activity == today:
            return  # Already counted today

        from datetime import timedelta

        if last_activity == today - timedelta(days=1):
            # Consecutive day
            new_streak = current_streak + 1
        elif last_activity is None or last_activity < today - timedelta(days=1):
            # Streak broken or first activity
            new_streak = 1
        else:
            new_streak = current_streak

        new_longest = max(longest_streak, new_streak)

        await self.repo.update_streak(student_id, new_streak, new_longest, today)

        # Award streak XP
        streak_xp = XP_STREAK_PER_DAY * min(new_streak, XP_STREAK_CAP)
        await self.award_xp(
            student_id=student_id,
            school_id=school_id,
            amount=streak_xp,
            source_type=XpSourceType.STREAK_BONUS,
            extra_data={"streak_day": new_streak},
        )

        logger.info(f"Student {student_id} streak: {new_streak} days (XP: +{streak_xp})")

    # ══════════════════════════════════════════════════════════════════════
    # ACHIEVEMENTS
    # ══════════════════════════════════════════════════════════════════════

    # Criteria types that belong to coding domain
    CODING_CRITERIA = {
        "challenges_solved", "topic_completed", "topic_first_solved",
        "hard_challenges_solved", "fast_challenge", "courses_completed",
    }
    # Criteria types that belong to learning domain
    LEARNING_CRITERIA = {
        "tests_passed", "perfect_test", "paragraphs_mastered",
        "chapter_a", "struggling_to_mastered",
    }
    # Shared criteria (both domains update streak)
    SHARED_CRITERIA = {"streak_days"}

    async def check_achievements(
        self, student_id: int, school_id: int, context: Optional[str] = None
    ) -> List[Achievement]:
        """
        Check achievements and update progress. Returns newly earned achievements.

        context: "coding" — only check coding + shared achievements
                 "learning" — only check learning + shared achievements
                 None — check all (backward compat)
        """
        achievements = await self.repo.get_all_active_achievements()
        newly_earned = []

        # Determine which criteria types to check based on context
        if context == "coding":
            allowed = self.CODING_CRITERIA | self.SHARED_CRITERIA
        elif context == "learning":
            allowed = self.LEARNING_CRITERIA | self.SHARED_CRITERIA
        else:
            allowed = None  # check all

        for achievement in achievements:
            criteria = achievement.criteria
            criteria_type = criteria.get("type")
            threshold = criteria.get("threshold", 0)

            # Skip achievements not relevant to this context
            if allowed is not None and criteria_type not in allowed:
                continue

            progress = await self._get_achievement_progress(
                student_id, criteria_type, school_id, criteria=criteria
            )

            normalized = min(progress / threshold, 1.0) if threshold > 0 else 0.0
            is_earned = progress >= threshold

            sa = await self.repo.upsert_student_achievement(
                student_id=student_id,
                achievement_id=achievement.id,
                school_id=school_id,
                progress=normalized,
                is_earned=is_earned,
            )

            if is_earned and sa.earned_at and not sa.notified:
                # Award XP for newly earned achievement
                if achievement.xp_reward > 0:
                    # Check if we already awarded XP for this achievement
                    # (by checking if there's an xp_transaction with this source_id)
                    from app.models.gamification import XpTransaction
                    existing = await self.db.execute(
                        select(XpTransaction).where(
                            XpTransaction.student_id == student_id,
                            XpTransaction.source_type == XpSourceType.ACHIEVEMENT,
                            XpTransaction.source_id == achievement.id,
                        ).limit(1)
                    )
                    if not existing.scalar_one_or_none():
                        await self.repo.add_xp_transaction(
                            student_id=student_id,
                            school_id=school_id,
                            amount=achievement.xp_reward,
                            source_type=XpSourceType.ACHIEVEMENT,
                            source_id=achievement.id,
                            extra_data={"achievement_code": achievement.code},
                        )

                newly_earned.append(achievement)

        return newly_earned

    async def _get_achievement_progress(
        self, student_id: int, criteria_type: str, school_id: int,
        criteria: Optional[dict] = None,
    ) -> float:
        """Get numeric progress for a specific achievement criteria type."""

        if criteria_type == "tests_passed":
            result = await self.db.execute(
                select(func.count(TestAttempt.id)).where(
                    TestAttempt.student_id == student_id,
                    TestAttempt.status == AttemptStatus.COMPLETED,
                    TestAttempt.passed == True,
                )
            )
            return float(result.scalar() or 0)

        elif criteria_type == "perfect_test":
            result = await self.db.execute(
                select(func.count(TestAttempt.id)).where(
                    TestAttempt.student_id == student_id,
                    TestAttempt.status == AttemptStatus.COMPLETED,
                    TestAttempt.score >= 1.0,
                )
            )
            return float(result.scalar() or 0)

        elif criteria_type == "streak_days":
            _, longest, _ = await self.repo.get_student_streak_info(student_id)
            return float(longest)

        elif criteria_type == "paragraphs_mastered":
            result = await self.db.execute(
                select(func.count(ParagraphMastery.id)).where(
                    ParagraphMastery.student_id == student_id,
                    ParagraphMastery.status == "mastered",
                )
            )
            return float(result.scalar() or 0)

        elif criteria_type == "chapter_a":
            from app.models.mastery import ChapterMastery
            result = await self.db.execute(
                select(func.count(ChapterMastery.id)).where(
                    ChapterMastery.student_id == student_id,
                    ChapterMastery.mastery_level == "A",
                )
            )
            return float(result.scalar() or 0)

        elif criteria_type == "struggling_to_mastered":
            from app.models.mastery import MasteryHistory
            result = await self.db.execute(
                select(func.count(MasteryHistory.id)).where(
                    MasteryHistory.student_id == student_id,
                    MasteryHistory.previous_level == "struggling",
                    MasteryHistory.new_level == "mastered",
                    MasteryHistory.paragraph_id.isnot(None),
                )
            )
            return float(result.scalar() or 0)

        # ── Coding achievements ──

        elif criteria_type == "challenges_solved":
            from app.models.coding import CodingSubmission
            result = await self.db.execute(
                select(func.count(func.distinct(CodingSubmission.challenge_id))).where(
                    CodingSubmission.student_id == student_id,
                    CodingSubmission.status == "passed",
                )
            )
            return float(result.scalar() or 0)

        elif criteria_type == "topic_completed":
            # All challenges in topic solved
            topic_slug = (criteria or {}).get("topic_slug")
            if not topic_slug:
                return 0.0
            from app.models.coding import CodingTopic, CodingChallenge, CodingSubmission
            # Count total active challenges in topic
            total_q = await self.db.execute(
                select(func.count(CodingChallenge.id))
                .join(CodingTopic, CodingTopic.id == CodingChallenge.topic_id)
                .where(CodingTopic.slug == topic_slug, CodingChallenge.is_active == True)
            )
            total = total_q.scalar() or 0
            if total == 0:
                return 0.0
            # Count solved by student
            solved_q = await self.db.execute(
                select(func.count(func.distinct(CodingSubmission.challenge_id)))
                .join(CodingChallenge, CodingChallenge.id == CodingSubmission.challenge_id)
                .join(CodingTopic, CodingTopic.id == CodingChallenge.topic_id)
                .where(
                    CodingSubmission.student_id == student_id,
                    CodingSubmission.status == "passed",
                    CodingTopic.slug == topic_slug,
                )
            )
            solved = solved_q.scalar() or 0
            return 1.0 if solved >= total else 0.0

        elif criteria_type == "topic_first_solved":
            # At least 1 challenge in topic solved
            topic_slug = (criteria or {}).get("topic_slug")
            if not topic_slug:
                return 0.0
            from app.models.coding import CodingTopic, CodingChallenge, CodingSubmission
            result = await self.db.execute(
                select(func.count(func.distinct(CodingSubmission.challenge_id)))
                .join(CodingChallenge, CodingChallenge.id == CodingSubmission.challenge_id)
                .join(CodingTopic, CodingTopic.id == CodingChallenge.topic_id)
                .where(
                    CodingSubmission.student_id == student_id,
                    CodingSubmission.status == "passed",
                    CodingTopic.slug == topic_slug,
                )
            )
            count = result.scalar() or 0
            return 1.0 if count >= 1 else 0.0

        elif criteria_type == "hard_challenges_solved":
            from app.models.coding import CodingChallenge, CodingSubmission
            result = await self.db.execute(
                select(func.count(func.distinct(CodingSubmission.challenge_id)))
                .join(CodingChallenge, CodingChallenge.id == CodingSubmission.challenge_id)
                .where(
                    CodingSubmission.student_id == student_id,
                    CodingSubmission.status == "passed",
                    CodingChallenge.difficulty == "hard",
                )
            )
            return float(result.scalar() or 0)

        elif criteria_type == "fast_challenge":
            # Count challenges solved faster than time_limit_ms
            from app.models.coding import CodingSubmission
            time_limit = (criteria or {}).get("time_limit_ms", 120000)
            result = await self.db.execute(
                select(func.count(func.distinct(CodingSubmission.challenge_id))).where(
                    CodingSubmission.student_id == student_id,
                    CodingSubmission.status == "passed",
                    CodingSubmission.execution_time_ms.isnot(None),
                    CodingSubmission.execution_time_ms < time_limit,
                )
            )
            return float(result.scalar() or 0)

        elif criteria_type == "courses_completed":
            from app.models.coding import CodingCourseProgress
            result = await self.db.execute(
                select(func.count(CodingCourseProgress.id)).where(
                    CodingCourseProgress.student_id == student_id,
                    CodingCourseProgress.completed_at.isnot(None),
                )
            )
            return float(result.scalar() or 0)

        return 0.0
