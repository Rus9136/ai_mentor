"""
Quiz Self-Paced Service: student-driven question flow via REST API.
Scoring mode is always 'accuracy' (1000 per correct, no speed bonus).
"""
import logging
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import QuizSession, QuizParticipant, QuizAnswer, QuizSessionStatus
from app.repositories.quiz_repo import QuizRepository
from app.schemas.quiz import QuizQuestionOut, SelfPacedNextQuestion, SelfPacedAnswerResult
from app.services.quiz_scoring import MAX_QUESTION_SCORE
from app.services.quiz_question_loader import (
    load_question, check_answer, get_correct_option_index,
)

logger = logging.getLogger(__name__)


class QuizSelfPacedService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = QuizRepository(db)

    async def get_next_question(self, session_id: int, student_id: int) -> Optional[SelfPacedNextQuestion]:
        """Get next unanswered question for a student in self-paced mode."""
        session = await self.repo.get_session(session_id)
        if not session or session.status != QuizSessionStatus.IN_PROGRESS:
            raise ValueError("Session not in progress")
        if session.mode != "self_paced":
            raise ValueError("Session is not self-paced")

        participant = await self.repo.get_participant(session_id, student_id)
        if not participant:
            raise ValueError("Not a participant")

        # Count how many questions this student has answered
        answered_count = await self._count_student_answers(participant.id)
        if answered_count >= session.question_count:
            return None  # All questions answered

        question_index = answered_count  # Next unanswered
        question = await load_question(
            self.db, session.test_id, question_index, session.settings, session.id,
        )
        if not question:
            return None

        return SelfPacedNextQuestion(
            question=question,
            answered_count=answered_count,
            total_questions=session.question_count,
            is_last=(answered_count + 1 >= session.question_count),
        )

    async def submit_answer(
        self,
        session_id: int,
        student_id: int,
        question_index: int,
        selected_option: int,
    ) -> SelfPacedAnswerResult:
        """Submit answer in self-paced mode. Returns immediate feedback with correct answer."""
        session = await self.repo.get_session(session_id)
        if not session or session.status != QuizSessionStatus.IN_PROGRESS:
            raise ValueError("Session not in progress")
        if session.mode != "self_paced":
            raise ValueError("Session is not self-paced")

        participant = await self.repo.get_participant(session_id, student_id)
        if not participant:
            raise ValueError("Not a participant")

        # Check not already answered
        existing = await self.repo.get_answer(participant.id, question_index)
        if existing:
            correct_option = await get_correct_option_index(
                self.db, session.test_id, question_index, session.settings, session.id,
            )
            answered_count = await self._count_student_answers(participant.id)
            return SelfPacedAnswerResult(
                is_correct=existing.is_correct,
                correct_option=correct_option or 0,
                score=existing.score,
                total_score=participant.total_score,
                correct_answers=participant.correct_answers,
                answered_count=answered_count,
                total_questions=session.question_count,
                is_finished=answered_count >= session.question_count,
            )

        # Check correctness
        is_correct = await check_answer(
            self.db, session.test_id, question_index, selected_option,
            session.settings, session.id,
        )

        # Accuracy mode: fixed score
        score = MAX_QUESTION_SCORE if is_correct else 0

        # Save answer
        await self.repo.add_answer(
            quiz_session_id=session_id,
            participant_id=participant.id,
            school_id=session.school_id,
            question_index=question_index,
            selected_option=selected_option,
            is_correct=is_correct,
            answer_time_ms=0,  # no timing in self-paced
            score=score,
        )

        # Update participant score (no streak in self-paced)
        await self.repo.update_participant_score(participant.id, score, is_correct)
        await self.db.commit()

        # Get correct option index for feedback
        correct_option = await self._quiz_service._get_correct_option_index(
            session.test_id, question_index, session.settings, session.id,
        )

        answered_count = await self._count_student_answers(participant.id)
        new_total = (participant.total_score or 0) + score
        new_correct = (participant.correct_answers or 0) + (1 if is_correct else 0)

        return SelfPacedAnswerResult(
            is_correct=is_correct,
            correct_option=correct_option or 0,
            score=score,
            total_score=new_total,
            correct_answers=new_correct,
            answered_count=answered_count,
            total_questions=session.question_count,
            is_finished=answered_count >= session.question_count,
        )

    async def get_all_student_progress(self, session_id: int) -> list[dict]:
        """Get progress for all participants (teacher view)."""
        from app.models.student import Student
        from app.models.user import User

        participants_data = await self.repo.get_participants_with_names(session_id)
        session = await self.repo.get_session(session_id)
        total_questions = session.question_count if session else 0

        result = []
        for d in participants_data:
            p = d["participant"]
            answered = await self._count_student_answers(p.id)
            result.append({
                "student_id": p.student_id,
                "student_name": d["student_name"],
                "answered": answered,
                "total": total_questions,
                "correct": p.correct_answers,
                "total_score": p.total_score,
            })
        return result

    async def _count_student_answers(self, participant_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(QuizAnswer)
            .where(QuizAnswer.participant_id == participant_id)
        )
        return result.scalar_one()
