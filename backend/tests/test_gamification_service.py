"""
Unit tests for GamificationService.

Uses mocked repository/db — no real database needed.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.gamification import XpSourceType
from app.services.gamification_service import (
    GamificationService,
    XP_FORMATIVE_BASE, XP_FORMATIVE_SCORE_MULT,
    XP_SUMMATIVE_BASE, XP_SUMMATIVE_SCORE_MULT,
    XP_PERFECT_BONUS, XP_FIRST_ATTEMPT_BONUS,
    XP_MASTERY_STRUGGLING_TO_PROGRESSING,
    XP_MASTERY_PROGRESSING_TO_MASTERED,
    XP_CHAPTER_C_TO_B, XP_CHAPTER_B_TO_A,
    XP_SELF_ASSESSMENT, XP_PARAGRAPH_COMPLETE,
    XP_STREAK_PER_DAY, XP_STREAK_CAP,
)


# ── Fixtures ──

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.add_xp_transaction = AsyncMock()
    repo.get_student_xp = AsyncMock(return_value=(100, 1))
    repo.update_student_level = AsyncMock()
    repo.get_student_streak_info = AsyncMock(return_value=(0, 0, None))
    repo.update_streak = AsyncMock()
    repo.get_all_active_achievements = AsyncMock(return_value=[])
    repo.upsert_student_achievement = AsyncMock()
    repo.increment_daily_quest = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def service(mock_db, mock_repo):
    svc = GamificationService(mock_db)
    svc.repo = mock_repo
    return svc


# ══════════════════════════════════════════════════════════════════════
# LEVEL CALCULATION (pure functions, no mocking)
# ══════════════════════════════════════════════════════════════════════

class TestLevelCalculation:

    def test_xp_for_level_1(self):
        assert GamificationService.xp_for_level(1) == 100

    def test_xp_for_level_2(self):
        assert GamificationService.xp_for_level(2) == int(100 * 2 ** 1.5)

    def test_xp_for_level_10(self):
        assert GamificationService.xp_for_level(10) == int(100 * 10 ** 1.5)

    def test_calculate_level_zero_xp(self):
        level, xp_in, xp_to = GamificationService.calculate_level(0)
        assert level == 1
        assert xp_in == 0
        # xp_to_next = needed for level 2 = int(100 * 2^1.5) = 282
        assert xp_to == int(100 * 2 ** 1.5)

    def test_calculate_level_exact_boundary(self):
        """Exactly enough XP to reach level 2."""
        needed_for_2 = int(100 * 2 ** 1.5)  # 282
        level, xp_in, xp_to = GamificationService.calculate_level(needed_for_2)
        assert level == 2
        assert xp_in == 0

    def test_calculate_level_mid_level(self):
        """Halfway through level 1."""
        level, xp_in, xp_to = GamificationService.calculate_level(100)
        assert level == 1
        assert xp_in == 100
        needed_for_2 = int(100 * 2 ** 1.5)
        assert xp_to == needed_for_2 - 100

    def test_calculate_level_high_xp(self):
        """Large XP value should produce a high level."""
        level, _, _ = GamificationService.calculate_level(50000)
        assert level > 5

    def test_calculate_level_consistency(self):
        """Level should increase monotonically with XP."""
        prev_level = 1
        for xp in range(0, 10001, 100):
            level, _, _ = GamificationService.calculate_level(xp)
            assert level >= prev_level
            prev_level = level


# ══════════════════════════════════════════════════════════════════════
# AWARD XP
# ══════════════════════════════════════════════════════════════════════

class TestAwardXp:

    @pytest.mark.asyncio
    async def test_award_xp_basic(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (150, 1)

        result = await service.award_xp(
            student_id=1, school_id=1, amount=50,
            source_type=XpSourceType.TEST_PASSED, source_id=10,
        )

        assert result["amount"] == 50
        assert result["level_up"] is False
        assert result["new_total_xp"] == 150
        mock_repo.add_xp_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_award_xp_level_up(self, service, mock_repo):
        """Student goes from level 1 (old) to level 2 (new_total_xp > threshold)."""
        needed_for_2 = int(100 * 2 ** 1.5)
        mock_repo.get_student_xp.return_value = (needed_for_2 + 10, 1)

        result = await service.award_xp(
            student_id=1, school_id=1, amount=300,
            source_type=XpSourceType.TEST_PASSED,
        )

        assert result["level_up"] is True
        assert result["new_level"] == 2
        mock_repo.update_student_level.assert_called_once_with(1, 2)

    @pytest.mark.asyncio
    async def test_award_xp_no_level_up(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (50, 1)

        result = await service.award_xp(
            student_id=1, school_id=1, amount=50,
            source_type=XpSourceType.TEST_PASSED,
        )

        assert result["level_up"] is False
        mock_repo.update_student_level.assert_not_called()

    @pytest.mark.asyncio
    async def test_award_xp_zero_amount(self, service, mock_repo):
        result = await service.award_xp(
            student_id=1, school_id=1, amount=0,
            source_type=XpSourceType.TEST_PASSED,
        )

        assert result["amount"] == 0
        assert result["level_up"] is False
        mock_repo.add_xp_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_award_xp_negative_amount(self, service, mock_repo):
        result = await service.award_xp(
            student_id=1, school_id=1, amount=-10,
            source_type=XpSourceType.TEST_PASSED,
        )

        assert result["amount"] == 0
        mock_repo.add_xp_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_award_xp_disabled(self, service, mock_repo):
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.GAMIFICATION_ENABLED = False

            result = await service.award_xp(
                student_id=1, school_id=1, amount=100,
                source_type=XpSourceType.TEST_PASSED,
            )

        assert result["amount"] == 0
        assert result["level_up"] is False
        mock_repo.add_xp_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_award_xp_passes_extra_data(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (50, 1)

        await service.award_xp(
            student_id=1, school_id=1, amount=10,
            source_type=XpSourceType.SELF_ASSESSMENT,
            extra_data={"key": "value"},
        )

        call_kwargs = mock_repo.add_xp_transaction.call_args.kwargs
        assert call_kwargs["extra_data"] == {"key": "value"}
        assert call_kwargs["source_type"] == XpSourceType.SELF_ASSESSMENT


# ══════════════════════════════════════════════════════════════════════
# ON TEST PASSED
# ══════════════════════════════════════════════════════════════════════

class TestOnTestPassed:

    @pytest.mark.asyncio
    async def test_formative_test_basic(self, service, mock_repo):
        """Formative test, score 0.8, attempt 2 → base + score * mult, no first-attempt bonus."""
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_test_passed(
            student_id=1, school_id=1,
            test_score=0.8, test_purpose="formative",
            attempt_number=2, test_attempt_id=10,
        )

        expected_xp = XP_FORMATIVE_BASE + round(0.8 * XP_FORMATIVE_SCORE_MULT)
        # 10 + 16 = 26
        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == expected_xp
        assert call_kwargs["source_type"] == XpSourceType.TEST_PASSED

    @pytest.mark.asyncio
    async def test_summative_test_basic(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_test_passed(
            student_id=1, school_id=1,
            test_score=0.7, test_purpose="summative",
            attempt_number=2, test_attempt_id=10,
        )

        expected_xp = XP_SUMMATIVE_BASE + round(0.7 * XP_SUMMATIVE_SCORE_MULT)
        # 25 + 35 = 60
        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == expected_xp

    @pytest.mark.asyncio
    async def test_perfect_score_bonus(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_test_passed(
            student_id=1, school_id=1,
            test_score=1.0, test_purpose="formative",
            attempt_number=2, test_attempt_id=10,
        )

        expected_xp = XP_FORMATIVE_BASE + round(1.0 * XP_FORMATIVE_SCORE_MULT) + XP_PERFECT_BONUS
        # 10 + 20 + 15 = 45
        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == expected_xp

    @pytest.mark.asyncio
    async def test_first_attempt_bonus(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_test_passed(
            student_id=1, school_id=1,
            test_score=0.8, test_purpose="formative",
            attempt_number=1, test_attempt_id=10,
        )

        expected_xp = XP_FORMATIVE_BASE + round(0.8 * XP_FORMATIVE_SCORE_MULT) + XP_FIRST_ATTEMPT_BONUS
        # 10 + 16 + 10 = 36
        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == expected_xp

    @pytest.mark.asyncio
    async def test_perfect_first_attempt_both_bonuses(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_test_passed(
            student_id=1, school_id=1,
            test_score=1.0, test_purpose="formative",
            attempt_number=1, test_attempt_id=10,
        )

        expected_xp = (
            XP_FORMATIVE_BASE + round(1.0 * XP_FORMATIVE_SCORE_MULT)
            + XP_PERFECT_BONUS + XP_FIRST_ATTEMPT_BONUS
        )
        # 10 + 20 + 15 + 10 = 55
        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == expected_xp

    @pytest.mark.asyncio
    async def test_triggers_streak_and_achievements(self, service, mock_repo):
        """on_test_passed should also call update_streak, check_achievements, and increment daily quest."""
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_test_passed(
            student_id=1, school_id=1,
            test_score=0.8, test_purpose="formative",
            attempt_number=1, test_attempt_id=10,
        )

        # update_streak calls repo.get_student_streak_info and repo.update_streak
        mock_repo.get_student_streak_info.assert_called()
        # check_achievements calls repo.get_all_active_achievements
        mock_repo.get_all_active_achievements.assert_called()
        # daily quest increment
        mock_repo.increment_daily_quest.assert_called_once()
        call_args = mock_repo.increment_daily_quest.call_args
        assert call_args[0][2] == "complete_tests"


# ══════════════════════════════════════════════════════════════════════
# ON MASTERY CHANGE
# ══════════════════════════════════════════════════════════════════════

class TestOnMasteryChange:

    @pytest.mark.asyncio
    async def test_struggling_to_progressing(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_mastery_change(
            student_id=1, school_id=1,
            old_status="struggling", new_status="progressing",
            paragraph_id=5,
        )

        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == XP_MASTERY_STRUGGLING_TO_PROGRESSING
        assert call_kwargs["source_type"] == XpSourceType.MASTERY_UP

    @pytest.mark.asyncio
    async def test_progressing_to_mastered(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_mastery_change(
            student_id=1, school_id=1,
            old_status="progressing", new_status="mastered",
            paragraph_id=5,
        )

        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == XP_MASTERY_PROGRESSING_TO_MASTERED

    @pytest.mark.asyncio
    async def test_struggling_to_mastered_both_bonuses(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_mastery_change(
            student_id=1, school_id=1,
            old_status="struggling", new_status="mastered",
            paragraph_id=5,
        )

        expected = XP_MASTERY_STRUGGLING_TO_PROGRESSING + XP_MASTERY_PROGRESSING_TO_MASTERED
        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == expected

    @pytest.mark.asyncio
    async def test_no_xp_for_same_status(self, service, mock_repo):
        await service.on_mastery_change(
            student_id=1, school_id=1,
            old_status="progressing", new_status="progressing",
            paragraph_id=5,
        )

        mock_repo.add_xp_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_xp_for_downgrade(self, service, mock_repo):
        await service.on_mastery_change(
            student_id=1, school_id=1,
            old_status="mastered", new_status="struggling",
            paragraph_id=5,
        )

        mock_repo.add_xp_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_mastered_triggers_daily_quest(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_mastery_change(
            student_id=1, school_id=1,
            old_status="progressing", new_status="mastered",
            paragraph_id=5,
        )

        mock_repo.increment_daily_quest.assert_called_once()
        call_args = mock_repo.increment_daily_quest.call_args
        assert call_args[0][2] == "master_paragraph"

    @pytest.mark.asyncio
    async def test_progressing_no_daily_quest(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_mastery_change(
            student_id=1, school_id=1,
            old_status="struggling", new_status="progressing",
            paragraph_id=5,
        )

        mock_repo.increment_daily_quest.assert_not_called()


# ══════════════════════════════════════════════════════════════════════
# ON CHAPTER LEVEL CHANGE
# ══════════════════════════════════════════════════════════════════════

class TestOnChapterLevelChange:

    @pytest.mark.asyncio
    async def test_c_to_b(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_chapter_level_change(
            student_id=1, school_id=1,
            old_level="C", new_level="B", chapter_id=3,
        )

        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == XP_CHAPTER_C_TO_B
        assert call_kwargs["source_type"] == XpSourceType.CHAPTER_COMPLETE

    @pytest.mark.asyncio
    async def test_b_to_a(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_chapter_level_change(
            student_id=1, school_id=1,
            old_level="B", new_level="A", chapter_id=3,
        )

        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == XP_CHAPTER_B_TO_A

    @pytest.mark.asyncio
    async def test_c_to_a_both_bonuses(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_chapter_level_change(
            student_id=1, school_id=1,
            old_level="C", new_level="A", chapter_id=3,
        )

        expected = XP_CHAPTER_C_TO_B + XP_CHAPTER_B_TO_A
        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == expected

    @pytest.mark.asyncio
    async def test_no_xp_for_downgrade(self, service, mock_repo):
        await service.on_chapter_level_change(
            student_id=1, school_id=1,
            old_level="A", new_level="B", chapter_id=3,
        )

        mock_repo.add_xp_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_xp_for_same_level(self, service, mock_repo):
        await service.on_chapter_level_change(
            student_id=1, school_id=1,
            old_level="B", new_level="B", chapter_id=3,
        )

        mock_repo.add_xp_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_triggers_achievement_check(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.on_chapter_level_change(
            student_id=1, school_id=1,
            old_level="C", new_level="B", chapter_id=3,
        )

        mock_repo.get_all_active_achievements.assert_called()


# ══════════════════════════════════════════════════════════════════════
# ON SELF ASSESSMENT
# ══════════════════════════════════════════════════════════════════════

class TestOnSelfAssessment:

    @pytest.mark.asyncio
    async def test_awards_flat_xp(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (100, 1)
        mock_repo.get_student_streak_info.return_value = (0, 0, None)
        mock_repo.get_all_active_achievements.return_value = []

        await service.on_self_assessment(student_id=1, school_id=1)

        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == XP_SELF_ASSESSMENT
        assert call_kwargs["source_type"] == XpSourceType.SELF_ASSESSMENT

    @pytest.mark.asyncio
    async def test_updates_streak_and_checks_achievements(self, service, mock_repo):
        """Self-assessment should also update streak and check achievements."""
        mock_repo.get_student_xp.return_value = (100, 1)
        mock_repo.get_student_streak_info.return_value = (0, 0, None)
        mock_repo.get_all_active_achievements.return_value = []

        await service.on_self_assessment(student_id=1, school_id=1, paragraph_id=42)

        mock_repo.get_student_streak_info.assert_called_once()
        mock_repo.get_all_active_achievements.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_paragraph_id_as_source(self, service, mock_repo):
        """Self-assessment should record paragraph_id as source_id."""
        mock_repo.get_student_xp.return_value = (100, 1)
        mock_repo.get_student_streak_info.return_value = (0, 0, None)
        mock_repo.get_all_active_achievements.return_value = []

        await service.on_self_assessment(student_id=1, school_id=1, paragraph_id=99)

        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["source_id"] == 99


# ══════════════════════════════════════════════════════════════════════
# ON PARAGRAPH COMPLETE
# ══════════════════════════════════════════════════════════════════════

class TestOnParagraphComplete:

    @pytest.mark.asyncio
    async def test_awards_xp(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (50, 1)
        mock_repo.get_student_streak_info.return_value = (0, 0, None)
        mock_repo.get_all_active_achievements.return_value = []

        await service.on_paragraph_complete(
            student_id=1, school_id=1, paragraph_id=42
        )

        call_kwargs = mock_repo.add_xp_transaction.call_args_list[0].kwargs
        assert call_kwargs["amount"] == XP_PARAGRAPH_COMPLETE
        assert call_kwargs["source_type"] == XpSourceType.PARAGRAPH_COMPLETE
        assert call_kwargs["source_id"] == 42

    @pytest.mark.asyncio
    async def test_updates_streak_and_checks_achievements(self, service, mock_repo):
        mock_repo.get_student_xp.return_value = (50, 1)
        mock_repo.get_student_streak_info.return_value = (0, 0, None)
        mock_repo.get_all_active_achievements.return_value = []

        await service.on_paragraph_complete(
            student_id=1, school_id=1, paragraph_id=42
        )

        mock_repo.get_student_streak_info.assert_called_once()
        mock_repo.get_all_active_achievements.assert_called_once()


# ══════════════════════════════════════════════════════════════════════
# STREAK
# ══════════════════════════════════════════════════════════════════════

class TestUpdateStreak:

    @pytest.mark.asyncio
    async def test_first_activity_starts_streak(self, service, mock_repo):
        """No prior activity → streak = 1."""
        mock_repo.get_student_streak_info.return_value = (0, 0, None)
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.update_streak(student_id=1, school_id=1)

        mock_repo.update_streak.assert_called_once()
        call_args = mock_repo.update_streak.call_args[0]
        assert call_args[1] == 1  # new_streak
        assert call_args[2] == 1  # new_longest

    @pytest.mark.asyncio
    async def test_consecutive_day_increments_streak(self, service, mock_repo):
        yesterday = date.today() - timedelta(days=1)
        mock_repo.get_student_streak_info.return_value = (5, 5, yesterday)
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.update_streak(student_id=1, school_id=1)

        call_args = mock_repo.update_streak.call_args[0]
        assert call_args[1] == 6  # new_streak
        assert call_args[2] == 6  # new_longest

    @pytest.mark.asyncio
    async def test_broken_streak_resets_to_1(self, service, mock_repo):
        two_days_ago = date.today() - timedelta(days=2)
        mock_repo.get_student_streak_info.return_value = (10, 15, two_days_ago)
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.update_streak(student_id=1, school_id=1)

        call_args = mock_repo.update_streak.call_args[0]
        assert call_args[1] == 1   # new_streak reset
        assert call_args[2] == 15  # longest preserved

    @pytest.mark.asyncio
    async def test_already_counted_today_noop(self, service, mock_repo):
        today = date.today()
        mock_repo.get_student_streak_info.return_value = (3, 5, today)

        await service.update_streak(student_id=1, school_id=1)

        mock_repo.update_streak.assert_not_called()

    @pytest.mark.asyncio
    async def test_streak_xp_scales_with_days(self, service, mock_repo):
        yesterday = date.today() - timedelta(days=1)
        mock_repo.get_student_streak_info.return_value = (9, 9, yesterday)
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.update_streak(student_id=1, school_id=1)

        # new_streak = 10, streak XP = 5 * 10 = 50
        expected_xp = XP_STREAK_PER_DAY * 10
        # award_xp calls add_xp_transaction; find the streak call
        streak_call = mock_repo.add_xp_transaction.call_args_list[-1]
        assert streak_call.kwargs["amount"] == expected_xp
        assert streak_call.kwargs["source_type"] == XpSourceType.STREAK_BONUS

    @pytest.mark.asyncio
    async def test_streak_xp_capped(self, service, mock_repo):
        """Streak XP should cap at XP_STREAK_CAP * XP_STREAK_PER_DAY."""
        yesterday = date.today() - timedelta(days=1)
        mock_repo.get_student_streak_info.return_value = (50, 50, yesterday)
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.update_streak(student_id=1, school_id=1)

        # new_streak = 51, but cap = 30, so streak XP = 5 * 30 = 150
        expected_xp = XP_STREAK_PER_DAY * XP_STREAK_CAP
        streak_call = mock_repo.add_xp_transaction.call_args_list[-1]
        assert streak_call.kwargs["amount"] == expected_xp

    @pytest.mark.asyncio
    async def test_new_longest_streak_updated(self, service, mock_repo):
        yesterday = date.today() - timedelta(days=1)
        mock_repo.get_student_streak_info.return_value = (20, 20, yesterday)
        mock_repo.get_student_xp.return_value = (100, 1)

        await service.update_streak(student_id=1, school_id=1)

        call_args = mock_repo.update_streak.call_args[0]
        assert call_args[1] == 21  # new_streak
        assert call_args[2] == 21  # new_longest = max(20, 21)


# ══════════════════════════════════════════════════════════════════════
# CHECK ACHIEVEMENTS
# ══════════════════════════════════════════════════════════════════════

class TestCheckAchievements:

    def _make_achievement(self, id=1, code="test_ach", criteria_type="tests_passed",
                          threshold=5, xp_reward=50, is_active=True):
        ach = MagicMock()
        ach.id = id
        ach.code = code
        ach.criteria = {"type": criteria_type, "threshold": threshold}
        ach.xp_reward = xp_reward
        ach.is_active = is_active
        return ach

    @pytest.mark.asyncio
    async def test_no_achievements_returns_empty(self, service, mock_repo):
        mock_repo.get_all_active_achievements.return_value = []

        result = await service.check_achievements(student_id=1, school_id=1)
        assert result == []

    @pytest.mark.asyncio
    async def test_progress_updated_not_earned(self, service, mock_repo, mock_db):
        """Progress below threshold → is_earned=False."""
        ach = self._make_achievement(threshold=10)
        mock_repo.get_all_active_achievements.return_value = [ach]

        # Mock _get_achievement_progress: student has 3 tests passed (below 10)
        result_mock = MagicMock()
        result_mock.scalar.return_value = 3
        mock_db.execute.return_value = result_mock

        sa_mock = MagicMock()
        sa_mock.is_earned = False
        sa_mock.earned_at = None
        sa_mock.notified = False
        mock_repo.upsert_student_achievement.return_value = sa_mock

        result = await service.check_achievements(student_id=1, school_id=1)

        assert result == []
        mock_repo.upsert_student_achievement.assert_called_once_with(
            student_id=1,
            achievement_id=ach.id,
            school_id=1,
            progress=0.3,  # 3/10
            is_earned=False,
        )

    @pytest.mark.asyncio
    async def test_achievement_earned(self, service, mock_repo, mock_db):
        """Progress meets threshold → is_earned=True, added to newly_earned."""
        ach = self._make_achievement(threshold=5, xp_reward=50)
        mock_repo.get_all_active_achievements.return_value = [ach]

        # _get_achievement_progress calls db.execute first (returns progress),
        # then check_achievements calls db.execute again (duplicate-XP check)
        progress_result = MagicMock()
        progress_result.scalar.return_value = 7  # above threshold
        dup_result = MagicMock()
        dup_result.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [progress_result, dup_result]

        sa_mock = MagicMock()
        sa_mock.is_earned = True
        sa_mock.earned_at = "2026-03-13T00:00:00"
        sa_mock.notified = False
        mock_repo.upsert_student_achievement.return_value = sa_mock

        result = await service.check_achievements(student_id=1, school_id=1)

        assert len(result) == 1
        assert result[0] == ach

    @pytest.mark.asyncio
    async def test_progress_capped_at_1(self, service, mock_repo, mock_db):
        """Progress should be capped at 1.0 even if actual progress exceeds threshold."""
        ach = self._make_achievement(threshold=5)
        mock_repo.get_all_active_achievements.return_value = [ach]

        progress_result = MagicMock()
        progress_result.scalar.return_value = 20  # way above threshold
        dup_result = MagicMock()
        dup_result.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [progress_result, dup_result]

        sa_mock = MagicMock()
        sa_mock.is_earned = True
        sa_mock.earned_at = "2026-03-13"
        sa_mock.notified = False
        mock_repo.upsert_student_achievement.return_value = sa_mock

        await service.check_achievements(student_id=1, school_id=1)

        call_kwargs = mock_repo.upsert_student_achievement.call_args.kwargs
        assert call_kwargs["progress"] == 1.0

    @pytest.mark.asyncio
    async def test_zero_threshold_achievement(self, service, mock_repo, mock_db):
        """Achievement with threshold=0 should have progress 0.0."""
        ach = self._make_achievement(threshold=0)
        mock_repo.get_all_active_achievements.return_value = [ach]

        result_mock = MagicMock()
        result_mock.scalar.return_value = 0
        mock_db.execute.return_value = result_mock

        sa_mock = MagicMock()
        sa_mock.is_earned = False
        sa_mock.earned_at = None
        sa_mock.notified = False
        mock_repo.upsert_student_achievement.return_value = sa_mock

        await service.check_achievements(student_id=1, school_id=1)

        call_kwargs = mock_repo.upsert_student_achievement.call_args.kwargs
        assert call_kwargs["progress"] == 0.0


# ══════════════════════════════════════════════════════════════════════
# XP CALCULATIONS (specific values)
# ══════════════════════════════════════════════════════════════════════

class TestXpCalculations:
    """Verify exact XP amounts for various scenarios."""

    def test_formative_score_0(self):
        xp = XP_FORMATIVE_BASE + round(0.0 * XP_FORMATIVE_SCORE_MULT)
        assert xp == 10

    def test_formative_score_05(self):
        xp = XP_FORMATIVE_BASE + round(0.5 * XP_FORMATIVE_SCORE_MULT)
        assert xp == 20

    def test_formative_score_1_perfect_first(self):
        xp = (
            XP_FORMATIVE_BASE + round(1.0 * XP_FORMATIVE_SCORE_MULT)
            + XP_PERFECT_BONUS + XP_FIRST_ATTEMPT_BONUS
        )
        assert xp == 55

    def test_summative_score_07(self):
        xp = XP_SUMMATIVE_BASE + round(0.7 * XP_SUMMATIVE_SCORE_MULT)
        assert xp == 60

    def test_summative_score_1_perfect_first(self):
        xp = (
            XP_SUMMATIVE_BASE + round(1.0 * XP_SUMMATIVE_SCORE_MULT)
            + XP_PERFECT_BONUS + XP_FIRST_ATTEMPT_BONUS
        )
        assert xp == 100

    def test_struggling_to_mastered_xp(self):
        xp = XP_MASTERY_STRUGGLING_TO_PROGRESSING + XP_MASTERY_PROGRESSING_TO_MASTERED
        assert xp == 45

    def test_chapter_c_to_a_xp(self):
        xp = XP_CHAPTER_C_TO_B + XP_CHAPTER_B_TO_A
        assert xp == 150

    def test_max_streak_xp(self):
        """Max daily streak XP when streak >= cap."""
        xp = XP_STREAK_PER_DAY * XP_STREAK_CAP
        assert xp == 150
