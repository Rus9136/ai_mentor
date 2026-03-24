"""
WebSocket endpoint for Quiz Battle real-time communication.
Supports: classic, team, self-paced, quick question modes.
"""
import asyncio
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
from app.repositories.quiz_repo import QuizRepository
from app.api.v1.ws_quiz_handlers import (
    handle_student_answer,
    handle_next_question,
    handle_finish_quiz,
    handle_quick_question,
    handle_quick_answer,
    handle_end_quick_question,
    handle_go_to_question,
    handle_activate_powerup,
)
from app.api.v1.ws_quiz_factile_handlers import (
    handle_factile_select_cell,
    handle_factile_judge_correct,
    handle_factile_judge_wrong,
    handle_factile_reveal_answer,
    handle_factile_skip_cell,
)

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
    # Quick Question in-memory state
    quick_responses: dict = field(default_factory=dict)
    quick_question_data: Optional[dict] = None
    quick_answered_students: set = field(default_factory=set)
    # Auto-close / auto-advance timers (Phase 2.4.5)
    question_close_task: Optional[asyncio.Task] = None
    auto_advance_task: Optional[asyncio.Task] = None
    question_closed: bool = False


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
        if room.teacher_ws is None and not room.students:
            from app.api.v1.ws_quiz_auto import cancel_question_timers
            cancel_question_timers(room)
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
        # Set RLS bypass for auth lookup (users/teachers may have RLS)
        await db.execute(text("SELECT set_config('app.is_super_admin', 'true', false)"))
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

        # Team mode: notify student of team assignment
        if participant and participant.team_id:
            from app.repositories.quiz_team_repo import QuizTeamRepository
            db2 = await _get_db_session(school_id)
            try:
                team_repo = QuizTeamRepository(db2)
                team = await team_repo.get_team_by_id(participant.team_id)
                if team:
                    await manager.send_to_student(join_code, student_id, {
                        "type": "team_assigned",
                        "data": {"team_id": team.id, "team_name": team.name, "team_color": team.color},
                    })
            finally:
                await db2.close()

    # Message loop
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            logger.info(f"WS message from {'teacher' if is_teacher else 'student'} in {join_code}: type={msg_type}")

            if msg_type == "answer" and not is_teacher:
                await handle_student_answer(manager, join_code, student_id, data.get("data", {}), school_id, session.id)

            elif msg_type == "next_question" and is_teacher:
                await handle_next_question(manager, join_code, auth_info.get("teacher_id"), school_id, session.id)

            elif msg_type == "finish_quiz" and is_teacher:
                await handle_finish_quiz(manager, join_code, auth_info.get("teacher_id"), school_id, session.id)

            elif msg_type == "go_to_question" and is_teacher:
                await handle_go_to_question(manager, join_code, auth_info.get("teacher_id"), data.get("data", {}), school_id, session.id)

            elif msg_type == "activate_powerup" and not is_teacher:
                await handle_activate_powerup(manager, join_code, student_id, data.get("data", {}), school_id, session.id)

            # Quick Question handlers
            elif msg_type == "quick_question" and is_teacher:
                await handle_quick_question(manager, join_code, data.get("data", {}))

            elif msg_type == "quick_answer" and not is_teacher:
                await handle_quick_answer(manager, join_code, student_id, data.get("data", {}))

            elif msg_type == "end_quick_question" and is_teacher:
                await handle_end_quick_question(manager, join_code)

            # Factile mode handlers (teacher only)
            elif msg_type == "select_cell" and is_teacher:
                await handle_factile_select_cell(manager, join_code, auth_info.get("teacher_id"), data.get("data", {}), school_id, session.id)

            elif msg_type == "judge_correct" and is_teacher:
                await handle_factile_judge_correct(manager, join_code, auth_info.get("teacher_id"), school_id, session.id)

            elif msg_type == "judge_wrong" and is_teacher:
                await handle_factile_judge_wrong(manager, join_code, auth_info.get("teacher_id"), school_id, session.id)

            elif msg_type == "reveal_answer" and is_teacher:
                await handle_factile_reveal_answer(manager, join_code, auth_info.get("teacher_id"), school_id, session.id)

            elif msg_type == "skip_cell" and is_teacher:
                await handle_factile_skip_cell(manager, join_code, auth_info.get("teacher_id"), school_id, session.id)

    except WebSocketDisconnect:
        logger.info(f"{'Teacher' if is_teacher else 'Student'} disconnected from quiz {join_code}")
    except Exception as e:
        logger.error(f"WebSocket error in quiz {join_code}: {e}")
    finally:
        user_id = auth_info.get("teacher_id") if is_teacher else auth_info.get("student_id")
        manager.disconnect(join_code, user_id, is_teacher)
