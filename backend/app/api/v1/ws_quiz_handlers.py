"""
WebSocket message handlers for Quiz Battle.
Extracted from ws_quiz.py + new handlers for team, self-paced, quick question modes.
"""
import logging
from app.services.quiz_service import QuizService
from app.services.quiz_team_service import QuizTeamService
from app.repositories.quiz_repo import QuizRepository

logger = logging.getLogger(__name__)


async def handle_student_answer(manager, join_code: str, student_id: int, data: dict, school_id: int, session_id: int):
    """Handle student answer submission (classic + team modes)."""
    from app.api.v1.ws_quiz import _get_db_session

    question_index = data.get("question_index")
    selected_option = data.get("selected_option", -1)
    answer_time_ms = data.get("answer_time_ms", 30000)
    text_answer = data.get("text_answer")

    if question_index is None:
        return
    # For short answer, selected_option may be absent
    if selected_option is None and text_answer is None:
        return

    db = await _get_db_session(school_id)
    try:
        service = QuizService(db)
        result = await service.submit_answer(
            session_id, student_id, question_index,
            selected_option if selected_option is not None else -1,
            answer_time_ms, text_answer=text_answer,
        )

        # Send result back to student
        await manager.send_to_student(join_code, student_id, {
            "type": "answer_accepted",
            "data": {
                "is_correct": result["is_correct"],
                "score": result["score"],
                "streak_bonus": result.get("streak_bonus", 0),
                "total_score": result["total_score"],
                "current_streak": result.get("current_streak", 0),
                "max_streak": result.get("max_streak", 0),
            },
        })

        # Team mode: update team score and notify teacher
        session = await service.repo.get_session(session_id)
        if session and session.mode == "team":
            participant = await service.repo.get_participant(session_id, student_id)
            if participant and participant.team_id:
                team_service = QuizTeamService(db)
                score_delta = result["score"] + result.get("streak_bonus", 0)
                await team_service.update_team_score(participant.team_id, score_delta, result["is_correct"])
                await db.commit()

                # Send team progress to teacher
                progress = await team_service.get_team_progress(session_id)
                await manager.send_to_teacher(join_code, {
                    "type": "team_progress",
                    "data": {"teams": progress},
                })

        # Send progress to teacher
        total_participants = manager.get_student_count(join_code)
        answered_count = await service.repo.count_answers_for_question(session_id, question_index)
        await manager.send_to_teacher(join_code, {
            "type": "answer_progress",
            "data": {"answered": answered_count, "total": total_participants},
        })
    except ValueError as e:
        await manager.send_to_student(join_code, student_id, {
            "type": "error",
            "data": {"message": str(e)},
        })
    except Exception as e:
        logger.error(f"Error handling answer: {e}")
    finally:
        await db.close()


async def handle_next_question(manager, join_code: str, teacher_id: int, school_id: int, session_id: int):
    """Handle teacher advancing to next question."""
    from app.api.v1.ws_quiz import _get_db_session

    db = await _get_db_session(school_id)
    try:
        service = QuizService(db)

        # Get stats for current question before advancing
        session = await service.repo.get_session(session_id)
        if session:
            current_idx = session.current_question_index
            stats_data = await service.get_question_stats(session_id, current_idx)

            # Get top 5 leaderboard
            lb_data = await service.repo.get_participants_with_names(session_id)
            top5 = [
                {"rank": i + 1, "student_name": d["student_name"], "total_score": d["participant"].total_score}
                for i, d in enumerate(lb_data[:5])
            ]

            # Broadcast question result
            await manager.broadcast_to_all(join_code, {
                "type": "question_result",
                "data": {
                    "correct_option": stats_data["correct_option"],
                    "stats": stats_data["stats"],
                    "leaderboard_top5": top5,
                },
            })

            # Team mode: broadcast team leaderboard
            if session.mode == "team":
                team_service = QuizTeamService(db)
                team_lb = await team_service.get_team_leaderboard(session_id)
                await manager.broadcast_to_all(join_code, {
                    "type": "team_leaderboard",
                    "data": {"teams": [t.model_dump() for t in team_lb]},
                })

        # Advance to next question
        next_q = await service.advance_question(session_id, teacher_id)
        if next_q:
            await manager.broadcast_to_all(join_code, {
                "type": "question",
                "data": next_q.model_dump(),
            })
        else:
            # No more questions — auto finish
            await handle_finish_quiz(manager, join_code, teacher_id, school_id, session_id)
    except ValueError as e:
        await manager.send_to_teacher(join_code, {"type": "error", "data": {"message": str(e)}})
    except Exception as e:
        logger.error(f"Error advancing question: {e}")
    finally:
        await db.close()


async def handle_finish_quiz(manager, join_code: str, teacher_id: int, school_id: int, session_id: int):
    """Handle quiz finish: calculate ranks, award XP, send results."""
    from app.api.v1.ws_quiz import _get_db_session

    db = await _get_db_session(school_id)
    try:
        service = QuizService(db)
        session = await service.repo.get_session(session_id)
        mode = session.mode if session else "classic"

        results = await service.finish_session(session_id, teacher_id)

        # Team leaderboard for team modes
        team_leaderboard = []
        if mode == "team":
            team_service = QuizTeamService(db)
            team_lb = await team_service.get_team_leaderboard(session_id)
            team_leaderboard = [t.model_dump() for t in team_lb]

        # Send personalized results to each student
        room = manager.get_room(join_code)
        if room:
            for student_id in list(room.students.keys()):
                your_rank = None
                your_score = 0
                your_correct = 0
                xp_earned = 0
                for entry in results["leaderboard"]:
                    if entry["student_id"] == student_id:
                        your_rank = entry["rank"]
                        your_score = entry["total_score"]
                        your_correct = entry["correct_answers"]
                        xp_earned = entry["xp_earned"]
                        break

                student_data = {
                    "leaderboard": results["leaderboard"],
                    "your_rank": your_rank,
                    "your_score": your_score,
                    "your_correct": your_correct,
                    "xp_earned": xp_earned,
                    "correct_answers": your_correct,
                    "total_questions": results["total_questions"],
                }
                if team_leaderboard:
                    student_data["team_leaderboard"] = team_leaderboard

                await manager.send_to_student(join_code, student_id, {
                    "type": "quiz_finished",
                    "data": student_data,
                })

        # Send to teacher
        teacher_data = {
            "leaderboard": results["leaderboard"],
            "total_questions": results["total_questions"],
        }
        if team_leaderboard:
            teacher_data["team_leaderboard"] = team_leaderboard

        await manager.send_to_teacher(join_code, {
            "type": "quiz_finished",
            "data": teacher_data,
        })
    except ValueError as e:
        await manager.send_to_teacher(join_code, {"type": "error", "data": {"message": str(e)}})
    except Exception as e:
        logger.error(f"Error finishing quiz: {e}")
    finally:
        await db.close()


# ── Quick Question handlers ──

async def handle_quick_question(manager, join_code: str, data: dict):
    """Teacher sends an ad-hoc question to all students."""
    question_text = data.get("question_text", "")
    options = data.get("options", [])
    if not question_text or len(options) < 2:
        await manager.send_to_teacher(join_code, {
            "type": "error",
            "data": {"message": "Question must have text and at least 2 options"},
        })
        return

    room = manager.get_room(join_code)
    if not room:
        return

    # Reset quick responses in memory
    room.quick_responses = {}
    room.quick_question_data = {"question_text": question_text, "options": options}
    room.quick_answered_students = set()

    # Broadcast to students
    await manager.broadcast_to_students(join_code, {
        "type": "quick_question",
        "data": {"question_text": question_text, "options": options},
    })


async def handle_quick_answer(manager, join_code: str, student_id: int, data: dict):
    """Student answers a quick question (in-memory only)."""
    selected_option = data.get("selected_option")
    if selected_option is None:
        return

    room = manager.get_room(join_code)
    if not room or not hasattr(room, "quick_responses"):
        return

    # Prevent double answers
    if not hasattr(room, "quick_answered_students"):
        room.quick_answered_students = set()
    if student_id in room.quick_answered_students:
        return
    room.quick_answered_students.add(student_id)

    # Update in-memory response counts
    key = str(selected_option)
    room.quick_responses[key] = room.quick_responses.get(key, 0) + 1

    total = sum(room.quick_responses.values())

    # Send live update to teacher
    await manager.send_to_teacher(join_code, {
        "type": "quick_response_update",
        "data": {"responses": room.quick_responses, "total": total},
    })

    # Confirm to student
    await manager.send_to_student(join_code, student_id, {
        "type": "quick_answer_accepted",
        "data": {"selected_option": selected_option},
    })


async def handle_end_quick_question(manager, join_code: str):
    """Teacher ends the current quick question."""
    room = manager.get_room(join_code)
    if not room:
        return

    responses = getattr(room, "quick_responses", {})
    total = sum(responses.values())

    # Broadcast final results to all
    await manager.broadcast_to_all(join_code, {
        "type": "quick_question_end",
        "data": {"responses": responses, "total": total},
    })

    # Clean up
    room.quick_responses = {}
    room.quick_question_data = None
    room.quick_answered_students = set()


async def handle_go_to_question(manager, join_code: str, teacher_id: int, data: dict, school_id: int, session_id: int):
    """Handle teacher navigating to an arbitrary question (teacher-paced mode)."""
    from app.api.v1.ws_quiz import _get_db_session

    question_index = data.get("question_index")
    if question_index is None:
        await manager.send_to_teacher(join_code, {"type": "error", "data": {"message": "question_index required"}})
        return

    db = await _get_db_session(school_id)
    try:
        service = QuizService(db)

        # Get stats for current question before navigating
        session = await service.repo.get_session(session_id)
        if session and session.current_question_index >= 0:
            current_idx = session.current_question_index
            stats_data = await service.get_question_stats(session_id, current_idx)

            lb_data = await service.repo.get_participants_with_names(session_id)
            top5 = [
                {"rank": i + 1, "student_name": d["student_name"], "total_score": d["participant"].total_score}
                for i, d in enumerate(lb_data[:5])
            ]

            await manager.broadcast_to_all(join_code, {
                "type": "question_result",
                "data": {
                    "correct_option": stats_data["correct_option"],
                    "stats": stats_data["stats"],
                    "leaderboard_top5": top5,
                },
            })

            # Team leaderboard
            if session.mode == "team":
                team_service = QuizTeamService(db)
                team_lb = await team_service.get_team_leaderboard(session_id)
                await manager.broadcast_to_all(join_code, {
                    "type": "team_leaderboard",
                    "data": {"teams": [t.model_dump() for t in team_lb]},
                })

        # Navigate to the target question
        question = await service.go_to_question(session_id, teacher_id, question_index)
        if question:
            await manager.broadcast_to_all(join_code, {
                "type": "question",
                "data": question.model_dump(),
            })
    except ValueError as e:
        await manager.send_to_teacher(join_code, {"type": "error", "data": {"message": str(e)}})
    except Exception as e:
        logger.error(f"Error in go_to_question: {e}")
    finally:
        await db.close()


async def handle_selfpaced_progress_notify(manager, join_code: str, student_id: int, student_name: str, answered: int, total: int, correct: int):
    """Notify teacher about student progress in self-paced mode (called from REST endpoint)."""
    await manager.send_to_teacher(join_code, {
        "type": "student_progress",
        "data": {
            "student_id": student_id,
            "student_name": student_name,
            "answered": answered,
            "total": total,
            "correct": correct,
        },
    })
