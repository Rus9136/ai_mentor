"""
Quiz scoring: constants and pure calculation functions.
Extracted from quiz_service.py for reuse across quiz modules.
"""

# ── Score / XP constants ──
MAX_QUESTION_SCORE = 1000
XP_PARTICIPATION = 10
XP_PER_CORRECT = 5
XP_RANK_1 = 50
XP_RANK_2 = 30
XP_RANK_3 = 15
XP_PERFECT = 25

# Streak bonus thresholds
STREAK_BONUSES = {2: 100, 3: 200, 4: 300}
STREAK_BONUS_CAP = 500  # 5+ streak


CONFIDENCE_SAFE_SCORE = 500


def calculate_score(
    is_correct: bool,
    answer_time_ms: int,
    time_limit_ms: int,
    scoring_mode: str = "speed",
    confidence_mode: str | None = None,
) -> int:
    """Calculate question score based on correctness, speed, mode, and confidence."""
    if not is_correct:
        return 0
    # Confidence "safe" mode: fixed 500 points
    if confidence_mode == "safe":
        return CONFIDENCE_SAFE_SCORE
    if scoring_mode == "accuracy":
        return MAX_QUESTION_SCORE
    # Speed mode: faster = more points
    time_factor = max(0, 1 - (answer_time_ms / time_limit_ms) / 2)
    return round(MAX_QUESTION_SCORE * time_factor)


def calculate_streak_bonus(streak: int) -> int:
    """Calculate bonus points for answer streak."""
    if streak < 2:
        return 0
    if streak >= 5:
        return STREAK_BONUS_CAP
    return STREAK_BONUSES.get(streak, 0)


def calculate_xp(rank: int, correct_answers: int, total_questions: int) -> int:
    """Calculate XP earned from quiz placement."""
    xp = XP_PARTICIPATION
    xp += correct_answers * XP_PER_CORRECT
    if rank == 1:
        xp += XP_RANK_1
    elif rank == 2:
        xp += XP_RANK_2
    elif rank == 3:
        xp += XP_RANK_3
    if correct_answers == total_questions and total_questions > 0:
        xp += XP_PERFECT
    return xp
