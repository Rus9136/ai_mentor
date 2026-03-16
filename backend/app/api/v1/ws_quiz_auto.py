"""
Auto-close and auto-advance logic for Quiz Battle (Phase 2.4.5).

Server-side timers that automatically:
1. Close the question (broadcast question_result) when timer expires or all answered
2. Advance to the next question after a configurable delay (if auto_advance enabled)
"""
import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.api.v1.ws_quiz import QuizConnectionManager, QuizRoom

logger = logging.getLogger(__name__)


def cancel_question_timers(room: "QuizRoom"):
    """Cancel both close and advance timers."""
    if room.question_close_task and not room.question_close_task.done():
        room.question_close_task.cancel()
    if room.auto_advance_task and not room.auto_advance_task.done():
        room.auto_advance_task.cancel()
    room.question_close_task = None
    room.auto_advance_task = None


async def start_question_close_timer(
    manager: "QuizConnectionManager",
    join_code: str,
    time_limit_ms: int,
    school_id: int,
    session_id: int,
):
    """Start a server-side timer to auto-close the question when time expires."""
    room = manager.get_room(join_code)
    if not room:
        return

    # Cancel any existing timers and reset state
    cancel_question_timers(room)
    room.question_closed = False

    async def _timer():
        try:
            # +1s grace for network latency
            await asyncio.sleep(time_limit_ms / 1000.0 + 1.0)
            await auto_close_question(manager, join_code, school_id, session_id)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in question close timer for {join_code}: {e}")

    room.question_close_task = asyncio.create_task(_timer())


async def auto_close_question(
    manager: "QuizConnectionManager",
    join_code: str,
    school_id: int,
    session_id: int,
):
    """Auto-close the current question: broadcast question_result to all."""
    room = manager.get_room(join_code)
    if not room or room.question_closed:
        return

    room.question_closed = True

    # Cancel close timer if still running (e.g. called from all-answered path)
    if room.question_close_task and not room.question_close_task.done():
        room.question_close_task.cancel()
        room.question_close_task = None

    from app.api.v1.ws_quiz import _get_db_session
    from app.services.quiz_service import QuizService

    db = await _get_db_session(school_id)
    try:
        service = QuizService(db)
        session = await service.repo.get_session(session_id)
        if not session or session.status.value != "in_progress":
            return

        current_idx = session.current_question_index
        stats_data = await service.get_question_stats(session_id, current_idx)

        settings = session.settings or {}
        every_n = settings.get("show_leaderboard_every_n", 1)
        question_number = current_idx + 1  # 1-based
        show_lb = (question_number % every_n == 0) or (question_number == session.question_count)

        # Conditional leaderboard
        top5 = []
        if show_lb:
            lb_data = await service.repo.get_participants_with_names(session_id)
            top5 = [
                {"rank": i + 1, "student_name": d["student_name"], "total_score": d["participant"].total_score}
                for i, d in enumerate(lb_data[:5])
            ]

        # Build question_result payload
        auto_advance = settings.get("auto_advance", False)
        auto_advance_delay_ms = settings.get("auto_advance_delay_ms", 5000)

        result_data = {
            "correct_option": stats_data["correct_option"],
            "stats": stats_data["stats"],
            "leaderboard_top5": top5,
        }
        if auto_advance:
            result_data["auto_advance_ms"] = auto_advance_delay_ms

        await manager.broadcast_to_all(join_code, {
            "type": "question_result",
            "data": result_data,
        })

        # Team leaderboard
        if session.mode == "team" and show_lb:
            from app.services.quiz_team_service import QuizTeamService
            team_service = QuizTeamService(db)
            team_lb = await team_service.get_team_leaderboard(session_id)
            await manager.broadcast_to_all(join_code, {
                "type": "team_leaderboard",
                "data": {"teams": [t.model_dump() for t in team_lb]},
            })

        # Notify teacher that question was auto-closed
        await manager.send_to_teacher(join_code, {
            "type": "question_auto_closed",
            "data": {"question_index": current_idx},
        })

        # Start auto-advance timer if enabled
        if auto_advance:
            await _start_auto_advance_timer(
                manager, join_code, auto_advance_delay_ms, school_id, session_id,
            )
    except Exception as e:
        logger.error(f"Error in auto_close_question for {join_code}: {e}")
    finally:
        await db.close()


async def _start_auto_advance_timer(
    manager: "QuizConnectionManager",
    join_code: str,
    delay_ms: int,
    school_id: int,
    session_id: int,
):
    """After result display, auto-advance to next question."""
    room = manager.get_room(join_code)
    if not room:
        return

    async def _advance():
        try:
            await asyncio.sleep(delay_ms / 1000.0)
            await _auto_advance_to_next(manager, join_code, school_id, session_id)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in auto-advance timer for {join_code}: {e}")

    room.auto_advance_task = asyncio.create_task(_advance())


async def _auto_advance_to_next(
    manager: "QuizConnectionManager",
    join_code: str,
    school_id: int,
    session_id: int,
):
    """Advance to next question automatically."""
    from app.api.v1.ws_quiz import _get_db_session
    from app.services.quiz_service import QuizService
    from app.api.v1.ws_quiz_handlers import handle_finish_quiz

    room = manager.get_room(join_code)
    if not room:
        return

    db = await _get_db_session(school_id)
    try:
        service = QuizService(db)
        session = await service.repo.get_session(session_id)
        if not session or session.status.value != "in_progress":
            return

        teacher_id = room.teacher_id or session.teacher_id
        next_q = await service.advance_question(session_id, teacher_id)

        if next_q:
            room.question_closed = False
            await manager.broadcast_to_all(join_code, {
                "type": "question",
                "data": next_q.model_dump(),
            })
            # Start the close timer for the new question
            settings = session.settings or {}
            time_limit = settings.get("time_per_question_ms", 30000)
            await start_question_close_timer(manager, join_code, time_limit, school_id, session_id)
        else:
            # No more questions — finish
            await handle_finish_quiz(manager, join_code, teacher_id, school_id, session_id)
    except Exception as e:
        logger.error(f"Error in auto_advance_to_next for {join_code}: {e}")
    finally:
        await db.close()
