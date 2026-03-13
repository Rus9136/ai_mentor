"""
Gamification models: XP transactions, achievements, daily quests.
"""
import enum
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Date, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import func

from app.models.base import BaseModel


# ── Enums ──

class XpSourceType(str, enum.Enum):
    TEST_PASSED = "test_passed"
    MASTERY_UP = "mastery_up"
    STREAK_BONUS = "streak_bonus"
    CHAPTER_COMPLETE = "chapter_complete"
    DAILY_QUEST = "daily_quest"
    SELF_ASSESSMENT = "self_assessment"
    REVIEW_COMPLETED = "review_completed"
    PARAGRAPH_COMPLETE = "paragraph_complete"


class AchievementCategory(str, enum.Enum):
    LEARNING = "learning"
    STREAK = "streak"
    MASTERY = "mastery"
    SOCIAL = "social"
    MILESTONE = "milestone"


class AchievementRarity(str, enum.Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class QuestType(str, enum.Enum):
    COMPLETE_TESTS = "complete_tests"
    STUDY_TIME = "study_time"
    MASTER_PARAGRAPH = "master_paragraph"
    REVIEW_SPACED = "review_spaced"


# ── Models ──

class XpTransaction(BaseModel):
    """Append-only XP transaction log."""

    __tablename__ = "xp_transactions"

    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    source_type = Column(Enum(XpSourceType, name="xp_source_type", create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False)
    source_id = Column(Integer, nullable=True)
    extra_data = Column("metadata", JSONB, default=dict)

    student = relationship("Student", back_populates="xp_transactions")

    def __repr__(self) -> str:
        return f"<XpTransaction(id={self.id}, student={self.student_id}, amount={self.amount}, source={self.source_type})>"


class Achievement(BaseModel):
    """Global achievement/badge definition."""

    __tablename__ = "achievements"

    code = Column(String(50), nullable=False, unique=True)
    name_kk = Column(String(200), nullable=False)
    name_ru = Column(String(200), nullable=False)
    description_kk = Column(String, nullable=True)
    description_ru = Column(String, nullable=True)
    icon = Column(String(100), nullable=False, default="star")
    category = Column(Enum(AchievementCategory, name="achievement_category", create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False)
    criteria = Column(JSONB, nullable=False, default=dict)
    xp_reward = Column(Integer, nullable=False, default=0)
    rarity = Column(Enum(AchievementRarity, name="achievement_rarity", create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False, default=AchievementRarity.COMMON)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    student_achievements = relationship("StudentAchievement", back_populates="achievement")

    def __repr__(self) -> str:
        return f"<Achievement(id={self.id}, code='{self.code}', rarity={self.rarity})>"


class StudentAchievement(BaseModel):
    """Per-student achievement progress and earned status."""

    __tablename__ = "student_achievements"

    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    progress = Column(Float, nullable=False, default=0.0)
    is_earned = Column(Boolean, nullable=False, default=False)
    earned_at = Column(DateTime(timezone=True), nullable=True)
    notified = Column(Boolean, nullable=False, default=False)

    student = relationship("Student", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="student_achievements")

    def __repr__(self) -> str:
        return f"<StudentAchievement(student={self.student_id}, achievement={self.achievement_id}, earned={self.is_earned})>"


class DailyQuest(BaseModel):
    """Global daily quest template."""

    __tablename__ = "daily_quests"

    code = Column(String(50), nullable=False)
    name_kk = Column(String(200), nullable=False)
    name_ru = Column(String(200), nullable=False)
    description_kk = Column(String, nullable=True)
    description_ru = Column(String, nullable=True)
    quest_type = Column(Enum(QuestType, name="quest_type", create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False)
    target_value = Column(Integer, nullable=False)
    xp_reward = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    textbook_id = Column(Integer, ForeignKey("textbooks.id", ondelete="SET NULL"), nullable=True)
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="SET NULL"), nullable=True)

    school = relationship("School")
    subject = relationship("Subject")
    textbook = relationship("Textbook")
    paragraph = relationship("Paragraph")
    student_quests = relationship("StudentDailyQuest", back_populates="quest")

    def __repr__(self) -> str:
        return f"<DailyQuest(id={self.id}, code='{self.code}', type={self.quest_type})>"


class StudentDailyQuest(BaseModel):
    """Per-student daily quest assignment and progress."""

    __tablename__ = "student_daily_quests"

    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    quest_id = Column(Integer, ForeignKey("daily_quests.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    quest_date = Column(Date, nullable=False, server_default=func.current_date())
    current_value = Column(Integer, nullable=False, default=0)
    is_completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("Student", back_populates="daily_quests")
    quest = relationship("DailyQuest", back_populates="student_quests")

    def __repr__(self) -> str:
        return f"<StudentDailyQuest(student={self.student_id}, quest={self.quest_id}, date={self.quest_date})>"
