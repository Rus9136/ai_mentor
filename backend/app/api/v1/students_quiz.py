"""
Student Quiz Battle API endpoints.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_student_from_user, get_current_user_school_id
from app.models.student import Student
from app.services.quiz_service import QuizService
from app.schemas.quiz import JoinQuizRequest, JoinQuizResponse, QuizResultsResponse, QuizParticipantResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/students/quiz-sessions")


@router.post("/join", response_model=JoinQuizResponse)
async def join_quiz(
    data: JoinQuizRequest,
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Join a quiz session by code."""
    service = QuizService(db)
    try:
        result = await service.join_session(data.join_code, student.id, school_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    ws_url = f"wss://api.ai-mentor.kz/api/v1/ws/quiz/{data.join_code}"
    return JoinQuizResponse(
        quiz_session_id=result["quiz_session_id"],
        ws_url=ws_url,
        status=result["status"],
        participant_count=result["participant_count"],
    )


@router.get("/{session_id}/results", response_model=QuizResultsResponse)
async def get_quiz_results(
    session_id: int,
    student: Student = Depends(get_student_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Get personal quiz results."""
    service = QuizService(db)
    session = await service.repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    participant = await service.repo.get_participant(session_id, student.id)
    if not participant:
        raise HTTPException(status_code=403, detail="Not a participant")

    participants_data = await service.repo.get_participants_with_names(session_id)

    leaderboard = [
        QuizParticipantResponse(
            id=d["participant"].id,
            student_id=d["participant"].student_id,
            student_name=d["student_name"],
            total_score=d["participant"].total_score,
            correct_answers=d["participant"].correct_answers,
            rank=d["participant"].rank,
            xp_earned=d["participant"].xp_earned,
            joined_at=d["participant"].joined_at,
        )
        for d in participants_data
    ]

    return QuizResultsResponse(
        quiz_session_id=session_id,
        total_questions=session.question_count,
        leaderboard=leaderboard,
        your_rank=participant.rank,
        your_score=participant.total_score,
        your_correct=participant.correct_answers,
        xp_earned=participant.xp_earned,
    )
