"""
Student Quiz Battle API endpoints.
Supports: join, results, self-paced question flow.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_student_from_user, get_current_user_school_id
from app.models.student import Student
from app.services.quiz_service import QuizService
from app.services.quiz_selfpaced_service import QuizSelfPacedService
from app.services.quiz_team_service import QuizTeamService
from app.repositories.quiz_repo import QuizRepository
from app.schemas.quiz import (
    JoinQuizRequest,
    JoinQuizResponse,
    QuizResultsResponse,
    QuizParticipantResponse,
    QuizTeamResponse,
    SelfPacedNextQuestion,
    SelfPacedAnswerResult,
    SelfPacedSubmitRequest,
    StudentQuizListItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/students/quiz-sessions")


@router.get("/my-quizzes", response_model=list[StudentQuizListItem])
async def get_my_quizzes(
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get quizzes for student's classes (My Quizzes widget)."""
    repo = QuizRepository(db)
    class_ids = await repo.get_student_class_ids(student.id)
    if not class_ids:
        return []
    items = await repo.get_sessions_for_classes(class_ids, school_id, student.id)
    return [StudentQuizListItem(**item) for item in items]


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
        logger.warning(f"Quiz join failed: student_id={student.id}, school_id={school_id}, code={data.join_code}, error={e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    ws_url = f"wss://api.ai-mentor.kz/api/v1/ws/quiz/{data.join_code}"
    return JoinQuizResponse(
        quiz_session_id=result["quiz_session_id"],
        ws_url=ws_url,
        status=result["status"],
        participant_count=result["participant_count"],
        mode=result.get("mode", "classic"),
        team_id=result.get("team_id"),
        team_name=result.get("team_name"),
        team_color=result.get("team_color"),
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

    # Team leaderboard (if team mode)
    team_leaderboard = []
    if session.mode == "team":
        team_service = QuizTeamService(db)
        team_leaderboard = await team_service.get_team_leaderboard(session_id)

    return QuizResultsResponse(
        quiz_session_id=session_id,
        total_questions=session.question_count,
        leaderboard=leaderboard,
        team_leaderboard=team_leaderboard,
        your_rank=participant.rank,
        your_score=participant.total_score,
        your_correct=participant.correct_answers,
        xp_earned=participant.xp_earned,
    )


# ── Self-Paced endpoints ──

@router.get("/{session_id}/next-question", response_model=SelfPacedNextQuestion)
async def get_next_question(
    session_id: int,
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the next unanswered question (self-paced mode)."""
    selfpaced = QuizSelfPacedService(db)
    try:
        result = await selfpaced.get_next_question(session_id, student.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if result is None:
        raise HTTPException(status_code=404, detail="No more questions")

    return result


@router.post("/{session_id}/submit-answer", response_model=SelfPacedAnswerResult)
async def submit_selfpaced_answer(
    session_id: int,
    data: SelfPacedSubmitRequest,
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Submit answer and get immediate feedback (self-paced mode)."""
    selfpaced = QuizSelfPacedService(db)
    try:
        result = await selfpaced.submit_answer(
            session_id, student.id, data.question_index, data.selected_option,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Notify teacher via WebSocket
    if result.answered_count > 0:
        try:
            from app.api.v1.ws_quiz import manager, _get_student_name
            service = QuizService(db)
            session = await service.repo.get_session(session_id)
            if session:
                student_name = await _get_student_name(student.id)
                from app.api.v1.ws_quiz_handlers import handle_selfpaced_progress_notify
                await handle_selfpaced_progress_notify(
                    manager, session.join_code, student.id, student_name,
                    result.answered_count, result.total_questions, result.correct_answers,
                )
        except Exception as e:
            logger.warning(f"Failed to notify teacher of self-paced progress: {e}")

    return result
