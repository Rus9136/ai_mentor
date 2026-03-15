"""
Teacher Quiz Battle API endpoints.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.dependencies import get_teacher_from_user, get_current_user_school_id
from app.models.teacher import Teacher
from app.models.test import Test, Question, QuestionType
from app.services.quiz_service import QuizService
from app.services.quiz_team_service import QuizTeamService
from app.services.quiz_selfpaced_service import QuizSelfPacedService
from app.schemas.quiz import (
    QuizSessionCreate,
    QuizSessionResponse,
    QuizSessionDetailResponse,
    QuizParticipantResponse,
    QuizResultsResponse,
    QuizTestInfo,
    QuizTeamResponse,
    QuickQuestionCreate,
    StudentProgressItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teachers/quiz-sessions")


@router.post("/", response_model=QuizSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz_session(
    data: QuizSessionCreate,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new quiz session from an existing test."""
    service = QuizService(db)
    try:
        session = await service.create_session(
            teacher_id=teacher.id,
            school_id=school_id,
            test_id=data.test_id,
            class_id=data.class_id,
            settings=data.settings,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return QuizSessionResponse(
        id=session.id,
        school_id=session.school_id,
        teacher_id=session.teacher_id,
        class_id=session.class_id,
        test_id=session.test_id,
        join_code=session.join_code,
        status=session.status.value if hasattr(session.status, 'value') else session.status,
        settings=session.settings,
        question_count=session.question_count,
        current_question_index=session.current_question_index,
        participant_count=0,
        started_at=session.started_at,
        finished_at=session.finished_at,
        created_at=session.created_at,
    )


@router.get("/", response_model=list[QuizSessionResponse])
async def list_quiz_sessions(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """List quiz sessions for this teacher."""
    service = QuizService(db)
    sessions = await service.repo.get_sessions_by_teacher(teacher.id, school_id, status=status_filter)

    result = []
    for s in sessions:
        count = await service.repo.get_participant_count(s.id)
        test_title = ""
        class_name = ""
        if s.test:
            test_title = s.test.title
        if s.school_class:
            class_name = s.school_class.name

        result.append(QuizSessionResponse(
            id=s.id,
            school_id=s.school_id,
            teacher_id=s.teacher_id,
            class_id=s.class_id,
            test_id=s.test_id,
            test_title=test_title,
            class_name=class_name,
            join_code=s.join_code,
            status=s.status.value if hasattr(s.status, 'value') else s.status,
            settings=s.settings,
            question_count=s.question_count,
            current_question_index=s.current_question_index,
            participant_count=count,
            started_at=s.started_at,
            finished_at=s.finished_at,
            created_at=s.created_at,
        ))
    return result


@router.get("/tests", response_model=list[QuizTestInfo])
async def list_tests_for_quiz(
    paragraph_id: Optional[int] = Query(None),
    chapter_id: Optional[int] = Query(None),
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """List available tests for quiz creation, filtered by paragraph or chapter."""
    query = (
        select(Test)
        .options(selectinload(Test.questions))
        .where(Test.is_active == True, Test.is_deleted == False)
    )
    if paragraph_id:
        query = query.where(Test.paragraph_id == paragraph_id)
    elif chapter_id:
        query = query.where(Test.chapter_id == chapter_id)
    else:
        raise HTTPException(status_code=400, detail="Provide paragraph_id or chapter_id")

    # Include global tests + school-specific tests
    query = query.where((Test.school_id == None) | (Test.school_id == school_id))

    result = await db.execute(query.order_by(Test.title))
    tests = result.scalars().all()

    return [
        QuizTestInfo(
            id=t.id,
            title=t.title,
            description=t.description,
            question_count=len([q for q in t.questions if q.question_type == QuestionType.SINGLE_CHOICE and not q.is_deleted]),
            difficulty=t.difficulty.value if hasattr(t.difficulty, 'value') else t.difficulty,
            test_purpose=t.test_purpose.value if hasattr(t.test_purpose, 'value') else t.test_purpose,
        )
        for t in tests
        if any(q.question_type == QuestionType.SINGLE_CHOICE and not q.is_deleted for q in t.questions)
    ]


@router.get("/{session_id}", response_model=QuizSessionDetailResponse)
async def get_quiz_session(
    session_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get quiz session detail with participants."""
    service = QuizService(db)
    session = await service.repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Not the session owner")

    participants_data = await service.repo.get_participants_with_names(session_id)

    return QuizSessionDetailResponse(
        id=session.id,
        school_id=session.school_id,
        teacher_id=session.teacher_id,
        class_id=session.class_id,
        test_id=session.test_id,
        join_code=session.join_code,
        status=session.status.value if hasattr(session.status, 'value') else session.status,
        settings=session.settings,
        question_count=session.question_count,
        current_question_index=session.current_question_index,
        participant_count=len(participants_data),
        started_at=session.started_at,
        finished_at=session.finished_at,
        created_at=session.created_at,
        participants=[
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
        ],
    )


@router.patch("/{session_id}/start")
async def start_quiz(
    session_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Start the quiz (transition from lobby to in_progress)."""
    service = QuizService(db)
    try:
        session = await service.start_session(session_id, teacher.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Broadcast quiz_started via WebSocket
    from app.api.v1.ws_quiz import manager

    mode = session.mode
    await manager.broadcast_to_all(session.join_code, {
        "type": "quiz_started",
        "data": {"total_questions": session.question_count, "mode": mode},
    })

    # Self-paced: don't send first question (students fetch via REST)
    if mode != "self_paced" and mode != "quick_question" and session.test_id:
        first_question = await service._load_question(
            session.test_id, 0, session.settings, session.id,
        )
        if first_question:
            await manager.broadcast_to_all(session.join_code, {
                "type": "question",
                "data": first_question.model_dump(),
            })

    return {"status": "in_progress", "message": "Quiz started"}


@router.patch("/{session_id}/cancel")
async def cancel_quiz(
    session_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel the quiz session."""
    service = QuizService(db)
    try:
        await service.cancel_session(session_id, teacher.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"status": "cancelled", "message": "Quiz cancelled"}


@router.get("/{session_id}/results", response_model=QuizResultsResponse)
async def get_quiz_results(
    session_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Get quiz results with leaderboard."""
    service = QuizService(db)
    session = await service.repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Not the session owner")

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

    # Stats
    total_participants = len(leaderboard)
    avg_score = sum(p.total_score for p in leaderboard) / total_participants if total_participants else 0

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
        stats={"average_score": round(avg_score), "total_participants": total_participants},
    )


@router.post("/quick-question", response_model=QuizSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_quick_question(
    data: QuickQuestionCreate,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a quick question session (no test needed, in-memory answers)."""
    from app.schemas.quiz import QuizSessionSettings

    settings = QuizSessionSettings(
        mode="quick_question",
        time_per_question_ms=data.time_per_question_ms,
    )
    service = QuizService(db)
    try:
        session = await service.create_session(
            teacher_id=teacher.id,
            school_id=school_id,
            test_id=None,
            class_id=data.class_id,
            settings=settings,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return QuizSessionResponse(
        id=session.id,
        school_id=session.school_id,
        teacher_id=session.teacher_id,
        class_id=session.class_id,
        test_id=session.test_id,
        join_code=session.join_code,
        status=session.status.value if hasattr(session.status, 'value') else session.status,
        settings=session.settings,
        question_count=session.question_count,
        current_question_index=session.current_question_index,
        participant_count=0,
        started_at=session.started_at,
        finished_at=session.finished_at,
        created_at=session.created_at,
    )


@router.get("/{session_id}/student-progress", response_model=list[StudentProgressItem])
async def get_student_progress(
    session_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get per-student progress for self-paced quiz."""
    service = QuizService(db)
    session = await service.repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Not the session owner")

    selfpaced_service = QuizSelfPacedService(db)
    progress = await selfpaced_service.get_all_student_progress(session_id)
    return [StudentProgressItem(**p) for p in progress]


@router.get("/{session_id}/team-leaderboard", response_model=list[QuizTeamResponse])
async def get_team_leaderboard(
    session_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get team leaderboard for team mode quiz."""
    service = QuizService(db)
    session = await service.repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Not the session owner")
    if session.mode != "team":
        raise HTTPException(status_code=400, detail="Not a team mode session")

    team_service = QuizTeamService(db)
    return await team_service.get_team_leaderboard(session_id)
