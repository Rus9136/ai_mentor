"""
WebSocket message handlers for Factile (Jeopardy-style) quiz mode.

Teacher sends: select_cell, judge_correct, judge_wrong, reveal_answer, skip_cell
Server broadcasts: factile_board, cell_selected, judge_result, answer_revealed, factile_finished
"""
import logging

from app.services.quiz_factile_service import QuizFactileService

logger = logging.getLogger(__name__)


async def handle_factile_select_cell(manager, join_code: str, teacher_id: int, data: dict, school_id: int, session_id: int):
    """Teacher selects a cell on the Factile board."""
    from app.api.v1.ws_quiz import _get_db_session

    category_index = data.get("category")
    row_index = data.get("row")
    if category_index is None or row_index is None:
        await manager.send_to_teacher(join_code, {
            "type": "error", "data": {"message": "category and row required"},
        })
        return

    db = await _get_db_session(school_id)
    try:
        service = QuizFactileService(db)
        result = await service.select_cell(session_id, category_index, row_index)

        # Build question data for broadcast (hide correct answer from students)
        question_for_display = {
            "text": result["question"]["text"],
            "options": [opt["text"] for opt in result["question"]["options"]],
            "question_type": result["question"]["question_type"],
            "image_url": result["question"].get("image_url"),
        }

        # Broadcast cell selection to all
        logger.info(f"Factile: broadcasting cell_selected for {join_code}, cat={category_index}, row={row_index}")
        await manager.broadcast_to_all(join_code, {
            "type": "cell_selected",
            "data": {
                "category_index": result["category_index"],
                "category_name": result["category_name"],
                "row_index": result["row_index"],
                "points": result["points"],
                "question": question_for_display,
                "team_name": result["team_name"],
            },
        })
        logger.info(f"Factile: cell_selected broadcast done for {join_code}")
    except ValueError as e:
        logger.warning(f"Factile select_cell ValueError: {e}")
        await manager.send_to_teacher(join_code, {"type": "error", "data": {"message": str(e)}})
    except Exception as e:
        logger.error(f"Error in factile select_cell: {e}", exc_info=True)
    finally:
        await db.close()


async def handle_factile_judge_correct(manager, join_code: str, teacher_id: int, school_id: int, session_id: int):
    """Teacher judges the answer as correct."""
    from app.api.v1.ws_quiz import _get_db_session

    db = await _get_db_session(school_id)
    try:
        service = QuizFactileService(db)
        result = await service.judge_correct(session_id)

        logger.info(f"Factile: judge_correct result={result}")
        await manager.broadcast_to_all(join_code, {
            "type": "judge_result",
            "data": result,
        })
        logger.info(f"Factile: judge_result broadcast done for {join_code}")

        # Broadcast updated board
        board_msg = await service.get_board_message(session_id)
        await manager.broadcast_to_all(join_code, {
            "type": "factile_board",
            "data": board_msg,
        })

        # Check if game is over
        if result["cells_remaining"] == 0:
            await _finish_factile(manager, join_code, teacher_id, school_id, session_id, db)

    except ValueError as e:
        logger.warning(f"Factile judge_correct ValueError: {e}")
        await manager.send_to_teacher(join_code, {"type": "error", "data": {"message": str(e)}})
    except Exception as e:
        logger.error(f"Error in factile judge_correct: {e}", exc_info=True)
    finally:
        await db.close()


async def handle_factile_judge_wrong(manager, join_code: str, teacher_id: int, school_id: int, session_id: int):
    """Teacher judges the answer as wrong."""
    from app.api.v1.ws_quiz import _get_db_session

    db = await _get_db_session(school_id)
    try:
        service = QuizFactileService(db)
        result = await service.judge_wrong(session_id)

        await manager.broadcast_to_all(join_code, {
            "type": "judge_result",
            "data": result,
        })

        # Broadcast updated board
        board_msg = await service.get_board_message(session_id)
        await manager.broadcast_to_all(join_code, {
            "type": "factile_board",
            "data": board_msg,
        })

        # Check if game is over (both teams wrong → cell closed)
        if result["cells_remaining"] == 0:
            await _finish_factile(manager, join_code, teacher_id, school_id, session_id, db)

    except ValueError as e:
        logger.warning(f"Factile judge_wrong ValueError: {e}")
        await manager.send_to_teacher(join_code, {"type": "error", "data": {"message": str(e)}})
    except Exception as e:
        logger.error(f"Error in factile judge_wrong: {e}", exc_info=True)
    finally:
        await db.close()


async def handle_factile_reveal_answer(manager, join_code: str, teacher_id: int, school_id: int, session_id: int):
    """Teacher reveals the correct answer."""
    from app.api.v1.ws_quiz import _get_db_session

    db = await _get_db_session(school_id)
    try:
        service = QuizFactileService(db)
        result = await service.reveal_answer(session_id)

        await manager.broadcast_to_all(join_code, {
            "type": "answer_revealed",
            "data": result,
        })
    except ValueError as e:
        await manager.send_to_teacher(join_code, {"type": "error", "data": {"message": str(e)}})
    except Exception as e:
        logger.error(f"Error in factile reveal_answer: {e}", exc_info=True)
    finally:
        await db.close()


async def handle_factile_skip_cell(manager, join_code: str, teacher_id: int, school_id: int, session_id: int):
    """Teacher skips the active cell without awarding points."""
    from app.api.v1.ws_quiz import _get_db_session

    db = await _get_db_session(school_id)
    try:
        service = QuizFactileService(db)
        result = await service.skip_cell(session_id)

        await manager.broadcast_to_all(join_code, {
            "type": "cell_skipped",
            "data": result,
        })

        # Broadcast updated board
        board_msg = await service.get_board_message(session_id)
        await manager.broadcast_to_all(join_code, {
            "type": "factile_board",
            "data": board_msg,
        })

        if result["cells_remaining"] == 0:
            await _finish_factile(manager, join_code, teacher_id, school_id, session_id, db)

    except ValueError as e:
        await manager.send_to_teacher(join_code, {"type": "error", "data": {"message": str(e)}})
    except Exception as e:
        logger.error(f"Error in factile skip_cell: {e}", exc_info=True)
    finally:
        await db.close()


async def _finish_factile(manager, join_code: str, teacher_id: int, school_id: int, session_id: int, db):
    """Finish the Factile game — determine winner, award XP, broadcast results."""
    from app.services.quiz_service import QuizService
    from app.services.quiz_factile_service import QuizFactileService

    try:
        factile_service = QuizFactileService(db)
        quiz_service = QuizService(db)

        # Get winner info
        winner_data = await factile_service.get_winner(session_id)

        # Finish session (calculates XP, sets ranks)
        results = await quiz_service.finish_session(session_id, teacher_id)

        # Send personalized results to each student
        room = manager.get_room(join_code)
        if room:
            for student_id in list(room.students.keys()):
                your_rank = None
                your_score = 0
                xp_earned = 0
                for entry in results["leaderboard"]:
                    if entry["student_id"] == student_id:
                        your_rank = entry["rank"]
                        your_score = entry["total_score"]
                        xp_earned = entry["xp_earned"]
                        break

                await manager.send_to_student(join_code, student_id, {
                    "type": "factile_finished",
                    "data": {
                        **winner_data,
                        "your_rank": your_rank,
                        "your_score": your_score,
                        "xp_earned": xp_earned,
                        "leaderboard": results["leaderboard"],
                    },
                })

        # Send to teacher
        await manager.send_to_teacher(join_code, {
            "type": "factile_finished",
            "data": {
                **winner_data,
                "leaderboard": results["leaderboard"],
                "total_questions": results["total_questions"],
            },
        })
    except Exception as e:
        logger.error(f"Error finishing factile game: {e}")
