"""
Weekly Tournament Service: automatic quiz generation and finalization.

Generates tournaments every Friday at 15:00 (Astana time) for classes
that studied material during the week. Uses self-paced mode with
accuracy scoring. Tournaments close Sunday 23:59.
"""
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import QuizTournament, QuizSession, QuizSessionStatus
from app.models.test import Test, TestPurpose
from app.models.test_attempt import TestAttempt, AttemptStatus
from app.models.class_student import ClassStudent
from app.models.school_class import SchoolClass
from app.models.gamification import XpSourceType
from app.repositories.quiz_repo import QuizRepository
from app.schemas.quiz import QuizSessionSettings

logger = logging.getLogger(__name__)

# Astana timezone = UTC+5
ASTANA_OFFSET = timezone(timedelta(hours=5))


class QuizTournamentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_weekly_tournaments(self) -> int:
        """
        Generate tournaments for all active classes.
        Called by cron every Friday 15:00 Astana.
        Returns number of tournaments created.
        """
        today = date.today()
        # Week: Monday to Sunday
        week_start = today - timedelta(days=today.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday

        # Get all active classes with students
        result = await self.db.execute(
            select(SchoolClass)
            .where(SchoolClass.is_deleted == False)
        )
        classes = list(result.scalars().all())

        created = 0
        for cls in classes:
            try:
                tournament = await self._generate_for_class(cls, week_start, week_end)
                if tournament:
                    created += 1
            except Exception as e:
                logger.error(f"Failed to generate tournament for class {cls.id}: {e}")

        await self.db.commit()
        logger.info(f"Generated {created} weekly tournaments for week {week_start} - {week_end}")
        return created

    async def _generate_for_class(
        self, cls: SchoolClass, week_start: date, week_end: date,
    ) -> Optional[QuizTournament]:
        """Generate tournament for a single class."""
        # Check if tournament already exists for this class + week
        existing = await self.db.execute(
            select(QuizTournament).where(
                QuizTournament.class_id == cls.id,
                QuizTournament.week_start == week_start,
            )
        )
        if existing.scalar_one_or_none():
            return None

        # Find tests attempted by this class's students this week
        week_start_dt = datetime.combine(week_start, datetime.min.time()).replace(tzinfo=timezone.utc)
        week_end_dt = datetime.combine(week_end, datetime.max.time()).replace(tzinfo=timezone.utc)

        student_ids_result = await self.db.execute(
            select(ClassStudent.student_id).where(ClassStudent.class_id == cls.id)
        )
        student_ids = [row[0] for row in student_ids_result.all()]
        if not student_ids:
            return None

        # Find formative tests attempted this week
        test_result = await self.db.execute(
            select(Test.id, func.count(TestAttempt.id).label('attempt_count'))
            .join(TestAttempt, TestAttempt.test_id == Test.id)
            .where(
                TestAttempt.student_id.in_(student_ids),
                TestAttempt.created_at >= week_start_dt,
                TestAttempt.created_at <= week_end_dt,
                TestAttempt.status == AttemptStatus.COMPLETED,
                Test.test_purpose == TestPurpose.FORMATIVE,
                Test.is_active == True,
                Test.is_deleted == False,
            )
            .group_by(Test.id)
            .order_by(func.count(TestAttempt.id).desc())
            .limit(1)
        )
        best_test = test_result.first()
        if not best_test:
            logger.debug(f"No suitable test found for class {cls.id} this week")
            return None

        test_id = best_test[0]

        # Create quiz session (self-paced, accuracy, deadline Sunday 23:59 Astana)
        from app.services.quiz_service import QuizService
        quiz_service = QuizService(self.db)

        deadline_dt = datetime.combine(week_end, datetime.max.time()).replace(tzinfo=ASTANA_OFFSET)

        settings = QuizSessionSettings(
            mode="self_paced",
            scoring_mode="accuracy",
            deadline=deadline_dt.isoformat(),
            shuffle_questions=True,
            shuffle_answers=True,
        )

        # Find teacher for this class (use first teacher assigned)
        from app.models.teacher import Teacher
        teacher_result = await self.db.execute(
            select(Teacher.id).where(Teacher.school_id == cls.school_id).limit(1)
        )
        teacher_row = teacher_result.first()
        if not teacher_row:
            return None
        teacher_id = teacher_row[0]

        session = await quiz_service.create_session(
            teacher_id=teacher_id,
            school_id=cls.school_id,
            test_id=test_id,
            class_id=cls.id,
            settings=settings,
        )

        # Start the session immediately (self-paced allows join during in_progress)
        await quiz_service.start_session(session.id, teacher_id)

        # Create tournament record
        tournament = QuizTournament(
            school_id=cls.school_id,
            class_id=cls.id,
            quiz_session_id=session.id,
            week_start=week_start,
            week_end=week_end,
            status="active",
        )
        self.db.add(tournament)
        await self.db.flush()

        logger.info(f"Tournament {tournament.id} created for class {cls.id}, session {session.id}")
        return tournament

    async def finalize_expired_tournaments(self) -> int:
        """
        Finalize tournaments past deadline. Award XP.
        Called by cron every Monday 00:00 Astana.
        """
        today = date.today()

        result = await self.db.execute(
            select(QuizTournament).where(
                QuizTournament.status == "active",
                QuizTournament.week_end < today,
            )
        )
        tournaments = list(result.scalars().all())

        finalized = 0
        for t in tournaments:
            try:
                await self._finalize_tournament(t)
                finalized += 1
            except Exception as e:
                logger.error(f"Failed to finalize tournament {t.id}: {e}")

        await self.db.commit()
        logger.info(f"Finalized {finalized} tournaments")
        return finalized

    async def _finalize_tournament(self, tournament: QuizTournament) -> None:
        """Finalize a single tournament: finish session, rank, award XP."""
        if not tournament.quiz_session_id:
            tournament.status = "cancelled"
            return

        # Finish quiz session if still active
        session = await self.db.get(QuizSession, tournament.quiz_session_id)
        if session and session.status == QuizSessionStatus.IN_PROGRESS:
            from app.services.quiz_service import QuizService
            quiz_service = QuizService(self.db)
            try:
                await quiz_service.finish_session(session.id, session.teacher_id)
            except Exception as e:
                logger.warning(f"Could not finish session {session.id}: {e}")

        # Award tournament XP bonuses
        repo = QuizRepository(self.db)
        participants = await repo.get_participants_with_names(tournament.quiz_session_id)

        from app.services.gamification_service import GamificationService
        gamification = GamificationService(self.db)

        for rank, data in enumerate(participants, 1):
            p = data["participant"]
            xp_bonus = 0
            if rank == 1:
                xp_bonus = tournament.xp_rank_1
            elif rank == 2:
                xp_bonus = tournament.xp_rank_2
            elif rank == 3:
                xp_bonus = tournament.xp_rank_3
            else:
                xp_bonus = tournament.xp_participation

            if xp_bonus > 0:
                try:
                    await gamification.award_xp(
                        student_id=p.student_id,
                        school_id=p.school_id,
                        amount=xp_bonus,
                        source_type=XpSourceType.WEEKLY_TOURNAMENT,
                        source_id=tournament.id,
                        extra_data={"rank": rank, "week": str(tournament.week_start)},
                    )
                except Exception as e:
                    logger.error(f"Failed to award tournament XP: {e}")

        tournament.status = "finished"
        logger.info(f"Tournament {tournament.id} finalized, {len(participants)} participants")

    async def get_active_tournaments(self, school_id: int, class_ids: list[int]) -> list[dict]:
        """List active/scheduled tournaments for given classes."""
        if not class_ids:
            return []

        result = await self.db.execute(
            select(QuizTournament)
            .where(
                QuizTournament.school_id == school_id,
                QuizTournament.class_id.in_(class_ids),
                QuizTournament.status.in_(["scheduled", "active"]),
            )
            .order_by(QuizTournament.week_start.desc())
        )
        tournaments = list(result.scalars().all())

        return [
            {
                "id": t.id,
                "class_id": t.class_id,
                "quiz_session_id": t.quiz_session_id,
                "week_start": str(t.week_start),
                "week_end": str(t.week_end),
                "status": t.status,
            }
            for t in tournaments
        ]

    async def get_tournament_results(self, tournament_id: int) -> Optional[dict]:
        """Get tournament leaderboard."""
        tournament = await self.db.get(QuizTournament, tournament_id)
        if not tournament or not tournament.quiz_session_id:
            return None

        repo = QuizRepository(self.db)
        participants = await repo.get_participants_with_names(tournament.quiz_session_id)

        return {
            "tournament_id": tournament.id,
            "status": tournament.status,
            "week_start": str(tournament.week_start),
            "week_end": str(tournament.week_end),
            "leaderboard": [
                {
                    "rank": rank,
                    "student_name": data["student_name"],
                    "total_score": data["participant"].total_score,
                    "correct_answers": data["participant"].correct_answers,
                }
                for rank, data in enumerate(participants, 1)
            ],
        }
