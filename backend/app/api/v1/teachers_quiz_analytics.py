"""
Quiz Battle analytics & exit ticket endpoints (Phase 2.3).
Separated from teachers_quiz.py to respect file size limits.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_teacher_from_user, get_current_user_school_id
from app.models.teacher import Teacher
from app.repositories.quiz_repo import QuizRepository
from app.schemas.quiz import QuizMatrixResponse, QuizMatrixStudent, QuizMatrixAnswer, QuizSessionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teachers/quiz-sessions", tags=["Teachers - Quiz Analytics"])


class ExitTicketCreate(BaseModel):
    class_id: int
    paragraph_id: int


@router.get("/{session_id}/matrix", response_model=QuizMatrixResponse)
async def get_quiz_matrix(
    session_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Get student x question matrix for live monitoring or post-quiz review."""
    repo = QuizRepository(db)
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Not the session owner")

    # Get participants with names
    participants_data = await repo.get_participants_with_names(session_id)
    # Get all answers
    answers = await repo.get_answers_matrix(session_id)

    # Index answers by participant_id -> question_index
    answer_map: dict[int, dict[int, object]] = {}
    for a in answers:
        answer_map.setdefault(a.participant_id, {})[a.question_index] = a

    # Build matrix
    students = []
    for data in participants_data:
        p = data["participant"]
        p_answers = answer_map.get(p.id, {})
        row = []
        for qi in range(session.question_count):
            ans = p_answers.get(qi)
            if ans:
                row.append(QuizMatrixAnswer(
                    question_index=qi,
                    is_correct=ans.is_correct,
                    answer_time_ms=ans.answer_time_ms,
                    text_answer=getattr(ans, "text_answer", None),
                ))
            else:
                row.append(None)
        students.append(QuizMatrixStudent(
            student_id=p.student_id,
            student_name=data["student_name"],
            answers=row,
        ))

    return QuizMatrixResponse(students=students, question_count=session.question_count)


# ── Exit Ticket ──

@router.post("/exit-ticket")
async def create_exit_ticket(
    data: ExitTicketCreate,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Create an exit ticket session for a paragraph."""
    from app.services.quiz_exit_ticket_service import QuizExitTicketService
    service = QuizExitTicketService(db)
    try:
        session = await service.create_exit_ticket(
            teacher_id=teacher.id,
            school_id=school_id,
            class_id=data.class_id,
            paragraph_id=data.paragraph_id,
        )
        return {
            "id": session.id,
            "join_code": session.join_code,
            "status": "lobby",
            "question_count": session.question_count,
            "settings": session.settings,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/exit-ticket/finalize")
async def finalize_exit_ticket(
    session_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Finalize exit ticket and create self-assessments."""
    from app.services.quiz_exit_ticket_service import QuizExitTicketService
    service = QuizExitTicketService(db)
    try:
        result = await service.finalize_exit_ticket(session_id, teacher.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
