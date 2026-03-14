"""
WebSocket endpoint for Quiz Battle real-time communication.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.quiz import QuizSession, QuizSessionStatus
from app.services.quiz_service import QuizService
from app.repositories.quiz_repo import QuizRepository

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Connection Manager ──

@dataclass
class QuizRoom:
    join_code: str
    session_id: int
    school_id: int
    teacher_ws: Optional[WebSocket] = None
    teacher_id: Optional[int] = None
    students: dict[int, WebSocket] = field(default_factory=dict)  # student_id -> ws


class QuizConnectionManager:
    def __init__(self):
        self.rooms: dict[str, QuizRoom] = {}

    def get_or_create_room(self, join_code: str, session_id: int, school_id: int) -> QuizRoom:
        if join_code not in self.rooms:
            self.rooms[join_code] = QuizRoom(join_code=join_code, session_id=session_id, school_id=school_id)
        return self.rooms[join_code]

    def get_room(self, join_code: str) -> Optional[QuizRoom]:
        return self.rooms.get(join_code)

    async def connect_teacher(self, join_code: str, session_id: int, school_id: int, teacher_id: int, ws: WebSocket):
        room = self.get_or_create_room(join_code, session_id, school_id)
        room.teacher_ws = ws
        room.teacher_id = teacher_id

    async def connect_student(self, join_code: str, session_id: int, school_id: int, student_id: int, ws: WebSocket):
        room = self.get_or_create_room(join_code, session_id, school_id)
        room.students[student_id] = ws

    def disconnect(self, join_code: str, user_id: int, is_teacher: bool):
        room = self.rooms.get(join_code)
        if not room:
            return
        if is_teacher:
            room.teacher_ws = None
        else:
            room.students.pop(user_id, None)
        # Clean up empty rooms
        if room.teacher_ws is None and not room.students:
            self.rooms.pop(join_code, None)

    async def send_to_teacher(self, join_code: str, message: dict):
        room = self.rooms.get(join_code)
        if room and room.teacher_ws:
            try:
                await room.teacher_ws.send_json(message)
            except Exception:
                pass

    async def send_to_student(self, join_code: str, student_id: int, message: dict):
        room = self.rooms.get(join_code)
        if room and student_id in room.students:
            try:
                await room.students[student_id].send_json(message)
            except Exception:
                pass

    async def broadcast_to_students(self, join_code: str, message: dict):
        room = self.rooms.get(join_code)
        if not room:
            return
        disconnected = []
        for sid, ws in room.students.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(sid)
        for sid in disconnected:
            room.students.pop(sid, None)

    async def broadcast_to_all(self, join_code: str, message: dict):
        await self.send_to_teacher(join_code, message)
        await self.broadcast_to_students(join_code, message)

    def get_student_count(self, join_code: str) -> int:
        room = self.rooms.get(join_code)
        return len(room.students) if room else 0


manager = QuizConnectionManager()


# ── Helpers ──

async def _get_db_session(school_id: int) -> AsyncSession:
    """Create a DB session with RLS context for WebSocket operations."""
    session = AsyncSessionLocal()
    await session.execute(text("SELECT set_config('app.current_tenant_id', :tid, false)"), {"tid": str(school_id)})
    await session.execute(text("SELECT set_config('app.is_super_admin', 'false', false)"))
    return session


async def _authenticate_ws(token: str) -> Optional[dict]:
    """Authenticate WebSocket connection via JWT token."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            return None

        role = user.role.value if hasattr(user.role, 'value') else user.role
        info = {"user_id": user.id, "role": role, "school_id": user.school_id}

        if role == UserRole.STUDENT.value:
            result = await db.execute(select(Student).where(Student.user_id == user.id))
            student = result.scalar_one_or_none()
            if student:
                info["student_id"] = student.id
                info["school_id"] = student.school_id
        elif role == UserRole.TEACHER.value:
            result = await db.execute(select(Teacher).where(Teacher.user_id == user.id))
            teacher = result.scalar_one_or_none()
            if teacher:
                info["teacher_id"] = teacher.id
                info["school_id"] = teacher.school_id

        return info


async def _get_student_name(student_id: int) -> str:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User.first_name, User.last_name)
            .join(Student, Student.user_id == User.id)
            .where(Student.id == student_id)
        )
        row = result.one_or_none()
        return f"{row[0]} {row[1]}".strip() if row else "Unknown"


# ── WebSocket Endpoint ──

@router.websocket("/ws/quiz/{join_code}")
async def quiz_websocket(
    websocket: WebSocket,
    join_code: str,
    token: str = Query(...),
):
    # Authenticate
    auth_info = await _authenticate_ws(token)
    if not auth_info:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    role = auth_info["role"]
    school_id = auth_info.get("school_id")
    is_teacher = role == UserRole.TEACHER.value

    # Validate session exists
    db = await _get_db_session(school_id)
    try:
        repo = QuizRepository(db)
        session = await repo.get_session_by_join_code(join_code)
        if not session:
            await websocket.close(code=4004, reason="Quiz not found")
            return

        if is_teacher:
            teacher_id = auth_info.get("teacher_id")
            if session.teacher_id != teacher_id:
                await websocket.close(code=4003, reason="Not the session owner")
                return
        else:
            student_id = auth_info.get("student_id")
            if not student_id:
                await websocket.close(code=4003, reason="Student not found")
                return
            participant = await repo.get_participant(session.id, student_id)
            if not participant:
                await websocket.close(code=4003, reason="Not a participant")
                return
    finally:
        await db.close()

    # Accept connection
    await websocket.accept()

    # Register in connection manager
    if is_teacher:
        await manager.connect_teacher(join_code, session.id, school_id, auth_info.get("teacher_id"), websocket)
        logger.info(f"Teacher connected to quiz {join_code}")
    else:
        student_id = auth_info["student_id"]
        await manager.connect_student(join_code, session.id, school_id, student_id, websocket)
        student_name = await _get_student_name(student_id)
        logger.info(f"Student {student_name} connected to quiz {join_code}")

        # Notify all about new participant
        count = manager.get_student_count(join_code)
        await manager.broadcast_to_all(join_code, {
            "type": "participant_joined",
            "data": {"student_name": student_name, "count": count},
        })

    # Message loop
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "answer" and not is_teacher:
                await _handle_student_answer(join_code, student_id, data.get("data", {}), school_id, session.id)

            elif msg_type == "next_question" and is_teacher:
                await _handle_next_question(join_code, auth_info.get("teacher_id"), school_id, session.id)

            elif msg_type == "finish_quiz" and is_teacher:
                await _handle_finish_quiz(join_code, auth_info.get("teacher_id"), school_id, session.id)

    except WebSocketDisconnect:
        logger.info(f"{'Teacher' if is_teacher else 'Student'} disconnected from quiz {join_code}")
    except Exception as e:
        logger.error(f"WebSocket error in quiz {join_code}: {e}")
    finally:
        user_id = auth_info.get("teacher_id") if is_teacher else auth_info.get("student_id")
        manager.disconnect(join_code, user_id, is_teacher)


# ── Message Handlers ──

async def _handle_student_answer(join_code: str, student_id: int, data: dict, school_id: int, session_id: int):
    question_index = data.get("question_index")
    selected_option = data.get("selected_option")
    answer_time_ms = data.get("answer_time_ms", 30000)

    if question_index is None or selected_option is None:
        return

    db = await _get_db_session(school_id)
    try:
        service = QuizService(db)
        result = await service.submit_answer(session_id, student_id, question_index, selected_option, answer_time_ms)

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


async def _handle_next_question(join_code: str, teacher_id: int, school_id: int, session_id: int):
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

        # Advance to next question
        next_q = await service.advance_question(session_id, teacher_id)
        if next_q:
            await manager.broadcast_to_all(join_code, {
                "type": "question",
                "data": next_q.model_dump(),
            })
        else:
            # No more questions — auto finish
            await _handle_finish_quiz(join_code, teacher_id, school_id, session_id)
    except ValueError as e:
        await manager.send_to_teacher(join_code, {"type": "error", "data": {"message": str(e)}})
    except Exception as e:
        logger.error(f"Error advancing question: {e}")
    finally:
        await db.close()


async def _handle_finish_quiz(join_code: str, teacher_id: int, school_id: int, session_id: int):
    db = await _get_db_session(school_id)
    try:
        service = QuizService(db)
        results = await service.finish_session(session_id, teacher_id)

        # Send personalized results to each student
        room = manager.get_room(join_code)
        if room:
            for student_id in list(room.students.keys()):
                # Find this student's data
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

                await manager.send_to_student(join_code, student_id, {
                    "type": "quiz_finished",
                    "data": {
                        "leaderboard": results["leaderboard"],
                        "your_rank": your_rank,
                        "your_score": your_score,
                        "your_correct": your_correct,
                        "xp_earned": xp_earned,
                        "correct_answers": your_correct,
                        "total_questions": results["total_questions"],
                    },
                })

        # Send to teacher
        await manager.send_to_teacher(join_code, {
            "type": "quiz_finished",
            "data": {
                "leaderboard": results["leaderboard"],
                "total_questions": results["total_questions"],
            },
        })
    except ValueError as e:
        await manager.send_to_teacher(join_code, {"type": "error", "data": {"message": str(e)}})
    except Exception as e:
        logger.error(f"Error finishing quiz: {e}")
    finally:
        await db.close()
