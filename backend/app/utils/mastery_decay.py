"""
Time Decay utility for mastery system.

Implements exponential decay of mastery scores based on time since last activity.
Without reinforcement (re-testing), knowledge gradually fades following
Ebbinghaus's forgetting curve.

Usage:
    from app.utils.mastery_decay import calculate_effective_score, get_effective_status

    effective = calculate_effective_score(best_score=0.90, last_updated_at=some_datetime)
    status = get_effective_status(effective)
"""

import math
from datetime import datetime, timezone

# Decay rate: 0.002 per day
# ~94% retained after 30 days
# ~83% retained after 90 days
# ~70% retained after 180 days
# ~48% retained after 365 days
DECAY_RATE = 0.002

# Status thresholds (same as mastery_service.py)
MASTERED_THRESHOLD = 0.85
PROGRESSING_THRESHOLD = 0.60


def calculate_effective_score(
    best_score: float,
    last_updated_at: datetime,
    decay_rate: float = DECAY_RATE,
) -> float:
    """
    Calculate effective score with exponential time decay.

    Args:
        best_score: Best test score (0.0-1.0)
        last_updated_at: When mastery was last updated (test taken)
        decay_rate: Decay rate per day (default 0.002)

    Returns:
        Effective score (0.0-1.0), decayed by time elapsed
    """
    if best_score is None or best_score <= 0:
        return 0.0

    now = datetime.now(timezone.utc)

    # Handle naive datetimes (make them UTC)
    if last_updated_at.tzinfo is None:
        last_updated_at = last_updated_at.replace(tzinfo=timezone.utc)

    delta = now - last_updated_at
    days_elapsed = max(0, delta.total_seconds() / 86400)

    effective = best_score * math.exp(-decay_rate * days_elapsed)
    return round(effective, 4)


def get_effective_status(effective_score: float) -> str:
    """
    Determine mastery status from effective score.

    Args:
        effective_score: Decayed score (0.0-1.0)

    Returns:
        Status string: 'mastered', 'progressing', or 'struggling'
    """
    if effective_score >= MASTERED_THRESHOLD:
        return "mastered"
    elif effective_score >= PROGRESSING_THRESHOLD:
        return "progressing"
    else:
        return "struggling"


def needs_review(best_score: float, last_updated_at: datetime) -> bool:
    """
    Check if a mastered paragraph needs review (decay > 15%).

    Args:
        best_score: Best test score (0.0-1.0)
        last_updated_at: When mastery was last updated

    Returns:
        True if the paragraph has decayed significantly
    """
    if best_score is None or best_score < MASTERED_THRESHOLD:
        return False

    effective = calculate_effective_score(best_score, last_updated_at)
    decay_pct = 1 - (effective / best_score) if best_score > 0 else 0
    return decay_pct > 0.15
