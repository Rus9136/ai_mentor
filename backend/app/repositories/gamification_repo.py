"""
Gamification repository: XP transactions, achievements, leaderboard, daily quests.
"""
import logging
from datetime import date, datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func, update, and_, case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student import Student
from app.models.user import User
from app.models.class_student import ClassStudent
from app.models.gamification import (
    XpTransaction, Achievement, StudentAchievement,
    DailyQuest, StudentDailyQuest, XpSourceType,
)

logger = logging.getLogger(__name__)


class GamificationRepository:
    """Data access for gamification tables."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── XP Transactions ──

    async def add_xp_transaction(
        self,
        student_id: int,
        school_id: int,
        amount: int,
        source_type: XpSourceType,
        source_id: Optional[int] = None,
        extra_data: Optional[dict] = None,
    ) -> XpTransaction:
        """Create XP transaction and update student total_xp atomically."""
        txn = XpTransaction(
            student_id=student_id,
            school_id=school_id,
            amount=amount,
            source_type=source_type,
            source_id=source_id,
            extra_data=extra_data or {},
        )
        self.db.add(txn)

        # Atomic increment
        await self.db.execute(
            update(Student)
            .where(Student.id == student_id)
            .values(total_xp=Student.total_xp + amount)
        )

        await self.db.flush()
        return txn

    async def get_xp_history(
        self, student_id: int, days: int = 7
    ) -> List[XpTransaction]:
        """Get recent XP transactions for a student."""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(XpTransaction)
            .where(
                XpTransaction.student_id == student_id,
                XpTransaction.created_at >= cutoff,
            )
            .order_by(XpTransaction.created_at.desc())
            .limit(100)
        )
        return list(result.scalars().all())

    # ── Student XP / Level ──

    async def get_student_xp(self, student_id: int) -> Tuple[int, int]:
        """Get student's (total_xp, level)."""
        result = await self.db.execute(
            select(Student.total_xp, Student.level)
            .where(Student.id == student_id)
        )
        row = result.one_or_none()
        return (row[0], row[1]) if row else (0, 1)

    async def update_student_level(self, student_id: int, new_level: int) -> None:
        """Update student's level."""
        await self.db.execute(
            update(Student)
            .where(Student.id == student_id)
            .values(level=new_level)
        )

    # ── Leaderboard ──

    async def get_school_leaderboard(
        self, school_id: int, limit: int = 50
    ) -> List[dict]:
        """Get school leaderboard sorted by XP."""
        result = await self.db.execute(
            select(
                Student.id.label("student_id"),
                (User.first_name + " " + func.coalesce(User.last_name, "")).label("student_name"),
                Student.total_xp,
                Student.level,
            )
            .join(User, Student.user_id == User.id)
            .where(
                Student.school_id == school_id,
                Student.is_deleted == False,
            )
            .order_by(Student.total_xp.desc())
            .limit(limit)
        )
        rows = result.all()
        return [
            {
                "rank": i + 1,
                "student_id": row.student_id,
                "student_name": row.student_name.strip(),
                "total_xp": row.total_xp,
                "level": row.level,
            }
            for i, row in enumerate(rows)
        ]

    async def get_class_leaderboard(
        self, school_id: int, class_id: int, limit: int = 50
    ) -> List[dict]:
        """Get class leaderboard sorted by XP."""
        result = await self.db.execute(
            select(
                Student.id.label("student_id"),
                (User.first_name + " " + func.coalesce(User.last_name, "")).label("student_name"),
                Student.total_xp,
                Student.level,
            )
            .join(User, Student.user_id == User.id)
            .join(ClassStudent, ClassStudent.student_id == Student.id)
            .where(
                Student.school_id == school_id,
                ClassStudent.class_id == class_id,
                Student.is_deleted == False,
            )
            .order_by(Student.total_xp.desc())
            .limit(limit)
        )
        rows = result.all()
        return [
            {
                "rank": i + 1,
                "student_id": row.student_id,
                "student_name": row.student_name.strip(),
                "total_xp": row.total_xp,
                "level": row.level,
            }
            for i, row in enumerate(rows)
        ]

    async def get_student_rank(
        self, student_id: int, school_id: int, class_id: Optional[int] = None
    ) -> int:
        """Get student's rank in school or class."""
        # Get student's XP
        xp_result = await self.db.execute(
            select(Student.total_xp).where(Student.id == student_id)
        )
        student_xp = xp_result.scalar() or 0

        # Count students with higher XP
        query = select(func.count(Student.id)).where(
            Student.school_id == school_id,
            Student.is_deleted == False,
            Student.total_xp > student_xp,
        )
        if class_id:
            query = query.join(ClassStudent, ClassStudent.student_id == Student.id).where(
                ClassStudent.class_id == class_id
            )

        result = await self.db.execute(query)
        higher_count = result.scalar() or 0
        return higher_count + 1

    async def get_school_student_count(
        self, school_id: int, class_id: Optional[int] = None
    ) -> int:
        """Count students in school or class."""
        query = select(func.count(Student.id)).where(
            Student.school_id == school_id,
            Student.is_deleted == False,
        )
        if class_id:
            query = query.join(ClassStudent, ClassStudent.student_id == Student.id).where(
                ClassStudent.class_id == class_id
            )
        result = await self.db.execute(query)
        return result.scalar() or 0

    # ── Achievements ──

    async def get_all_active_achievements(self) -> List[Achievement]:
        """Get all active achievement definitions."""
        result = await self.db.execute(
            select(Achievement)
            .where(Achievement.is_active == True)
            .order_by(Achievement.sort_order)
        )
        return list(result.scalars().all())

    async def get_student_achievements(
        self, student_id: int
    ) -> List[StudentAchievement]:
        """Get all student achievements with achievement details."""
        result = await self.db.execute(
            select(StudentAchievement)
            .options(selectinload(StudentAchievement.achievement))
            .where(StudentAchievement.student_id == student_id)
            .order_by(StudentAchievement.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_unnotified_achievements(
        self, student_id: int
    ) -> List[StudentAchievement]:
        """Get earned but unnotified achievements."""
        result = await self.db.execute(
            select(StudentAchievement)
            .options(selectinload(StudentAchievement.achievement))
            .where(
                StudentAchievement.student_id == student_id,
                StudentAchievement.is_earned == True,
                StudentAchievement.notified == False,
            )
        )
        return list(result.scalars().all())

    async def mark_achievements_notified(
        self, student_id: int, achievement_ids: List[int]
    ) -> None:
        """Mark achievements as notified."""
        if not achievement_ids:
            return
        await self.db.execute(
            update(StudentAchievement)
            .where(
                StudentAchievement.student_id == student_id,
                StudentAchievement.achievement_id.in_(achievement_ids),
            )
            .values(notified=True)
        )

    async def upsert_student_achievement(
        self,
        student_id: int,
        achievement_id: int,
        school_id: int,
        progress: float,
        is_earned: bool = False,
    ) -> StudentAchievement:
        """Create or update student achievement progress."""
        result = await self.db.execute(
            select(StudentAchievement).where(
                StudentAchievement.student_id == student_id,
                StudentAchievement.achievement_id == achievement_id,
            )
        )
        sa = result.scalar_one_or_none()

        if sa:
            sa.progress = progress
            if is_earned and not sa.is_earned:
                sa.is_earned = True
                sa.earned_at = datetime.now(timezone.utc)
        else:
            sa = StudentAchievement(
                student_id=student_id,
                achievement_id=achievement_id,
                school_id=school_id,
                progress=progress,
                is_earned=is_earned,
                earned_at=datetime.now(timezone.utc) if is_earned else None,
            )
            self.db.add(sa)

        await self.db.flush()
        return sa

    async def count_earned_achievements(self, student_id: int) -> int:
        """Count earned achievements for a student."""
        result = await self.db.execute(
            select(func.count(StudentAchievement.id)).where(
                StudentAchievement.student_id == student_id,
                StudentAchievement.is_earned == True,
            )
        )
        return result.scalar() or 0

    # ── Daily Quests ──

    async def get_active_quests(self) -> List[DailyQuest]:
        """Get all active quest templates."""
        result = await self.db.execute(
            select(DailyQuest).where(DailyQuest.is_active == True)
        )
        return list(result.scalars().all())

    async def get_student_daily_quests(
        self, student_id: int, quest_date: date
    ) -> List[Tuple[DailyQuest, Optional[StudentDailyQuest]]]:
        """Get daily quests with student progress for a given date."""
        result = await self.db.execute(
            select(DailyQuest, StudentDailyQuest)
            .outerjoin(
                StudentDailyQuest,
                and_(
                    StudentDailyQuest.quest_id == DailyQuest.id,
                    StudentDailyQuest.student_id == student_id,
                    StudentDailyQuest.quest_date == quest_date,
                )
            )
            .where(DailyQuest.is_active == True)
        )
        return list(result.all())

    async def ensure_daily_quests_assigned(
        self, student_id: int, school_id: int, quest_date: date
    ) -> None:
        """Ensure all active quests are assigned for today (lazy init)."""
        quests = await self.get_active_quests()
        for quest in quests:
            result = await self.db.execute(
                select(StudentDailyQuest).where(
                    StudentDailyQuest.student_id == student_id,
                    StudentDailyQuest.quest_id == quest.id,
                    StudentDailyQuest.quest_date == quest_date,
                )
            )
            if not result.scalar_one_or_none():
                self.db.add(StudentDailyQuest(
                    student_id=student_id,
                    quest_id=quest.id,
                    school_id=school_id,
                    quest_date=quest_date,
                ))
        await self.db.flush()

    async def increment_daily_quest(
        self,
        student_id: int,
        school_id: int,
        quest_type: str,
        quest_date: date,
        increment: int = 1,
    ) -> Optional[StudentDailyQuest]:
        """Increment progress on matching daily quests. Returns completed quest if any."""
        # Find matching quest
        result = await self.db.execute(
            select(StudentDailyQuest)
            .join(DailyQuest, DailyQuest.id == StudentDailyQuest.quest_id)
            .where(
                StudentDailyQuest.student_id == student_id,
                StudentDailyQuest.quest_date == quest_date,
                StudentDailyQuest.is_completed == False,
                DailyQuest.quest_type == quest_type,
            )
        )
        sdq = result.scalar_one_or_none()
        if not sdq:
            return None

        sdq.current_value = sdq.current_value + increment

        # Check if quest target is met
        quest_result = await self.db.execute(
            select(DailyQuest).where(DailyQuest.id == sdq.quest_id)
        )
        quest = quest_result.scalar_one()

        if sdq.current_value >= quest.target_value and not sdq.is_completed:
            sdq.is_completed = True
            sdq.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            return sdq

        await self.db.flush()
        return None

    # ── Streak ──

    async def get_student_streak_info(
        self, student_id: int
    ) -> Tuple[int, int, Optional[date]]:
        """Get (current_streak, longest_streak, last_activity_date) for a student."""
        result = await self.db.execute(
            select(Student.current_streak, Student.longest_streak, Student.last_activity_date)
            .where(Student.id == student_id)
        )
        row = result.one_or_none()
        return (row[0], row[1], row[2]) if row else (0, 0, None)

    async def update_streak(
        self, student_id: int, current_streak: int, longest_streak: int, last_activity_date: date
    ) -> None:
        """Update student streak fields."""
        await self.db.execute(
            update(Student)
            .where(Student.id == student_id)
            .values(
                current_streak=current_streak,
                longest_streak=longest_streak,
                last_activity_date=last_activity_date,
            )
        )
