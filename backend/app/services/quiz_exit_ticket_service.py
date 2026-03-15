"""
Exit Ticket service for Quiz Battle (Phase 2.3).
3-question mini-quiz: self-assessment, reflection (text), topic question.
"""
import logging
import random
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quiz import QuizSession, QuizSessionStatus
from app.models.test import Test, Question, QuestionType
from app.repositories.quiz_repo import QuizRepository
from app.schemas.quiz import QuizQuestionOut

logger = logging.getLogger(__name__)

# Self-assessment options (Q0)
SELF_ASSESSMENT_OPTIONS = ["Понял(а)", "Есть вопросы", "Сложно"]
RATING_MAP = {0: "understood", 1: "questions", 2: "difficult"}

# Reflection question (Q1)
REFLECTION_TEXT = "Что было интересным или сложным в этой теме?"


class QuizExitTicketService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = QuizRepository(db)

    async def create_exit_ticket(
        self,
        teacher_id: int,
        school_id: int,
        class_id: int,
        paragraph_id: int,
    ) -> QuizSession:
        """Create an exit ticket session (2-3 questions)."""
        from app.services.quiz_service import QuizService
        service = QuizService(self.db)

        # Try to find a topic question from paragraph's test
        topic_question = await self._find_topic_question(paragraph_id)
        question_count = 3 if topic_question else 2

        join_code = await service.generate_join_code()
        settings = {
            "mode": "exit_ticket",
            "pacing": "teacher_paced",
            "scoring_mode": "accuracy",
            "show_leaderboard": False,
            "time_per_question_ms": 0,
        }

        session = await self.repo.create_session(
            school_id=school_id,
            teacher_id=teacher_id,
            test_id=topic_question["test_id"] if topic_question else None,
            class_id=class_id,
            join_code=join_code,
            question_count=question_count,
            settings=settings,
        )
        # Store paragraph_id for self-assessment integration
        from sqlalchemy import update as sa_update
        await self.db.execute(
            sa_update(QuizSession).where(QuizSession.id == session.id).values(paragraph_id=paragraph_id)
        )
        await self.db.commit()
        logger.info(f"Exit ticket session {session.id} created for paragraph {paragraph_id}")
        return session

    async def get_exit_ticket_question(self, session_id: int, question_index: int) -> Optional[QuizQuestionOut]:
        """Get exit ticket question by index."""
        session = await self.repo.get_session(session_id)
        if not session:
            return None

        if question_index == 0:
            # Q0: Self-assessment
            return QuizQuestionOut(
                index=0,
                text="Оцените своё понимание темы",
                question_type="single_choice",
                options=SELF_ASSESSMENT_OPTIONS,
                time_limit_ms=0,
                image_url=None,
            )
        elif question_index == 1:
            # Q1: Reflection (short answer)
            return QuizQuestionOut(
                index=1,
                text=REFLECTION_TEXT,
                question_type="short_answer",
                options=[],
                time_limit_ms=0,
                image_url=None,
            )
        elif question_index == 2 and session.test_id:
            # Q2: Topic question from test
            from app.services.quiz_service import QuizService
            service = QuizService(self.db)
            return await service._load_question(session.test_id, 0, session.settings, session.id)
        return None

    async def finalize_exit_ticket(self, session_id: int, teacher_id: int) -> dict:
        """Finalize exit ticket: create self-assessments from Q0 answers."""
        session = await self.repo.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.teacher_id != teacher_id:
            raise ValueError("Not the session owner")
        if not session.paragraph_id:
            raise ValueError("No paragraph linked")

        # Get all participants and their Q0 answers
        participants = await self.repo.get_participants_with_names(session_id)
        results = []

        from app.services.self_assessment_service import SelfAssessmentService
        sa_service = SelfAssessmentService(self.db)

        for data in participants:
            p = data["participant"]
            # Get Q0 answer (self-assessment)
            q0_answer = await self.repo.get_answer(p.id, 0)
            if not q0_answer:
                continue

            rating = RATING_MAP.get(q0_answer.selected_option, "understood")

            # Get Q2 answer (topic question) for practice_score
            practice_score = None
            q2_answer = await self.repo.get_answer(p.id, 2)
            if q2_answer:
                practice_score = 100.0 if q2_answer.is_correct else 0.0

            try:
                assessment, recommendation = await sa_service.submit_assessment(
                    student_id=p.student_id,
                    paragraph_id=session.paragraph_id,
                    school_id=session.school_id,
                    rating=rating,
                    practice_score=practice_score,
                )
                results.append({
                    "student_id": p.student_id,
                    "student_name": data["student_name"],
                    "rating": rating,
                    "practice_score": practice_score,
                })
            except Exception as e:
                logger.error(f"Failed to create self-assessment for student {p.student_id}: {e}")

        # Mark session as finished
        now = datetime.now(timezone.utc)
        await self.repo.update_session(session_id, status=QuizSessionStatus.FINISHED, finished_at=now)
        await self.db.commit()

        return {"session_id": session_id, "assessments_created": len(results), "results": results}

    async def _find_topic_question(self, paragraph_id: int) -> Optional[dict]:
        """Find a single-choice question from the paragraph's formative test."""
        result = await self.db.execute(
            select(Test)
            .options(selectinload(Test.questions).selectinload(Question.options))
            .where(
                Test.paragraph_id == paragraph_id,
                Test.is_active == True,
                Test.is_deleted == False,
            )
            .limit(1)
        )
        test = result.scalar_one_or_none()
        if not test:
            return None

        sc_questions = [
            q for q in test.questions
            if q.question_type == QuestionType.SINGLE_CHOICE and not q.is_deleted
        ]
        if not sc_questions:
            return None

        return {"test_id": test.id, "question": random.choice(sc_questions)}
