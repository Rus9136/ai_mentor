"""
Diagnostic Analytics Service.

Provides class-level aggregation of diagnostic test results
for the Teacher Dashboard "Diagnostics" tab.
"""

import logging
from typing import List, Optional, Dict

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.test import Test, TestPurpose, Question, QuestionOption
from app.models.test_attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.models.student import Student
from app.models.textbook import Textbook
from app.models.subject import Subject
from app.schemas.teacher_dashboard import (
    DiagnosticAnswerDetail,
    DiagnosticAttemptAnswersResponse,
    DiagnosticResultsResponse,
    DiagnosticScoreDistribution,
    DiagnosticStudentResult,
)

logger = logging.getLogger(__name__)


class DiagnosticAnalyticsService:
    """Aggregates diagnostic test results for teacher analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_diagnostic_results(
        self,
        student_ids: List[int],
        total_students: int,
    ) -> DiagnosticResultsResponse:
        """
        Get aggregated diagnostic test results for a set of students.

        For each student, picks the BEST completed diagnostic attempt
        (window function: row_number partitioned by student_id, ordered by score DESC).
        """
        if not student_ids:
            return DiagnosticResultsResponse(total_students=total_students)

        # Subquery: best diagnostic attempt per student
        best_attempt = (
            select(
                TestAttempt.id.label("attempt_id"),
                TestAttempt.student_id,
                TestAttempt.test_id,
                TestAttempt.score,
                TestAttempt.passed,
                TestAttempt.completed_at,
                TestAttempt.time_spent,
                TestAttempt.started_at,
                func.row_number().over(
                    partition_by=TestAttempt.student_id,
                    order_by=desc(TestAttempt.score),
                ).label("rn"),
            )
            .join(Test, Test.id == TestAttempt.test_id)
            .where(
                and_(
                    TestAttempt.student_id.in_(student_ids),
                    TestAttempt.status == AttemptStatus.COMPLETED.value,
                    Test.test_purpose == TestPurpose.DIAGNOSTIC,
                    Test.is_deleted == False,
                )
            )
            .subquery()
        )

        rows = await self.db.execute(
            select(best_attempt).where(best_attempt.c.rn == 1)
        )
        attempts_data = rows.fetchall()

        if not attempts_data:
            return DiagnosticResultsResponse(total_students=total_students)

        # Batch load: students, tests, textbooks
        attempt_student_ids = [r.student_id for r in attempts_data]
        test_ids = list({r.test_id for r in attempts_data})

        students_map = await self._batch_load_students(attempt_student_ids)
        tests_map = await self._batch_load_tests(test_ids)

        # Count correct answers per attempt
        attempt_ids = [r.attempt_id for r in attempts_data]
        correct_counts = await self._batch_count_correct(attempt_ids)

        # Build results
        results: List[DiagnosticStudentResult] = []
        scores: List[float] = []
        dist = DiagnosticScoreDistribution()

        for row in attempts_data:
            student = students_map.get(row.student_id)
            test_info = tests_map.get(row.test_id)

            if not student:
                continue

            score_pct = round(row.score * 100, 1) if row.score is not None else None
            if score_pct is not None:
                scores.append(score_pct)
                if score_pct >= 85:
                    dist.range_85_100 += 1
                elif score_pct >= 60:
                    dist.range_60_85 += 1
                elif score_pct >= 40:
                    dist.range_40_60 += 1
                else:
                    dist.range_0_40 += 1

            q_total, q_correct = correct_counts.get(row.attempt_id, (0, 0))

            results.append(DiagnosticStudentResult(
                student_id=student["id"],
                student_code=student["code"],
                first_name=student["first_name"],
                last_name=student["last_name"],
                attempt_id=row.attempt_id,
                test_id=row.test_id,
                test_title=test_info["title"] if test_info else "—",
                textbook_title=test_info.get("textbook_title") if test_info else None,
                subject_name=test_info.get("subject_name") if test_info else None,
                score=row.score,
                score_percent=score_pct,
                passed=row.passed,
                completed_at=row.completed_at,
                time_spent=row.time_spent,
                questions_total=q_total,
                questions_correct=q_correct,
            ))

        # Sort: lowest score first (struggling students at top)
        results.sort(key=lambda r: r.score_percent if r.score_percent is not None else -1)

        avg = round(sum(scores) / len(scores), 1) if scores else None

        return DiagnosticResultsResponse(
            total_students=total_students,
            students_tested=len(results),
            average_score=avg,
            distribution=dist,
            results=results,
        )

    async def get_diagnostic_attempt_answers(
        self,
        attempt_id: int,
        school_id: int,
    ) -> Optional[DiagnosticAttemptAnswersResponse]:
        """
        Get detailed answers for a specific diagnostic test attempt.

        Validates that the attempt belongs to the school and is a diagnostic test.
        """
        # Load attempt with test
        attempt_result = await self.db.execute(
            select(TestAttempt)
            .options(selectinload(TestAttempt.test))
            .where(
                and_(
                    TestAttempt.id == attempt_id,
                    TestAttempt.school_id == school_id,
                )
            )
        )
        attempt = attempt_result.scalar_one_or_none()
        if not attempt or not attempt.test:
            return None

        if attempt.test.test_purpose != TestPurpose.DIAGNOSTIC:
            return None

        # Load student
        student_result = await self.db.execute(
            select(Student)
            .options(selectinload(Student.user))
            .where(Student.id == attempt.student_id)
        )
        student = student_result.scalar_one_or_none()
        student_name = ""
        if student and student.user:
            student_name = f"{student.user.last_name} {student.user.first_name}"

        # Load questions with options (ordered)
        questions_result = await self.db.execute(
            select(Question)
            .options(selectinload(Question.options))
            .where(Question.test_id == attempt.test_id)
            .order_by(Question.sort_order)
        )
        questions = list(questions_result.scalars().all())

        # Load student's answers for this attempt
        answers_result = await self.db.execute(
            select(TestAttemptAnswer)
            .where(TestAttemptAnswer.attempt_id == attempt_id)
        )
        answers_by_question: Dict[int, TestAttemptAnswer] = {
            a.question_id: a for a in answers_result.scalars().all()
        }

        # Build answer details
        answer_details: List[DiagnosticAnswerDetail] = []
        for q in questions:
            student_answer = answers_by_question.get(q.id)
            sorted_options = sorted(q.options, key=lambda o: o.sort_order)

            answer_details.append(DiagnosticAnswerDetail(
                question_id=q.id,
                question_text=q.question_text,
                question_type=q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type),
                options=[
                    {
                        "id": opt.id,
                        "text": opt.option_text,
                        "is_correct": opt.is_correct,
                    }
                    for opt in sorted_options
                ],
                selected_option_ids=student_answer.selected_option_ids if student_answer else None,
                answer_text=student_answer.answer_text if student_answer else None,
                is_correct=student_answer.is_correct if student_answer else None,
                points_earned=student_answer.points_earned if student_answer else None,
                points_possible=q.points,
                explanation=q.explanation,
            ))

        return DiagnosticAttemptAnswersResponse(
            attempt_id=attempt_id,
            test_id=attempt.test_id,
            test_title=attempt.test.title,
            student_id=attempt.student_id,
            student_name=student_name,
            score=attempt.score,
            passed=attempt.passed,
            completed_at=attempt.completed_at,
            time_spent=attempt.time_spent,
            answers=answer_details,
        )

    # ========================================================================
    # BATCH HELPERS
    # ========================================================================

    async def _batch_load_students(self, student_ids: List[int]) -> Dict:
        """Batch load students with user info."""
        result = await self.db.execute(
            select(Student)
            .options(selectinload(Student.user))
            .where(Student.id.in_(student_ids))
        )
        students = {}
        for s in result.scalars().all():
            if s.user:
                students[s.id] = {
                    "id": s.id,
                    "code": s.student_code,
                    "first_name": s.user.first_name,
                    "last_name": s.user.last_name,
                }
        return students

    async def _batch_load_tests(self, test_ids: List[int]) -> Dict:
        """Batch load tests with textbook and subject info."""
        result = await self.db.execute(
            select(
                Test.id,
                Test.title,
                Textbook.title.label("textbook_title"),
                Subject.name.label("subject_name"),
            )
            .outerjoin(Textbook, Textbook.id == Test.textbook_id)
            .outerjoin(Subject, Subject.id == Textbook.subject_id)
            .where(Test.id.in_(test_ids))
        )
        tests = {}
        for row in result.fetchall():
            tests[row.id] = {
                "title": row.title,
                "textbook_title": row.textbook_title,
                "subject_name": row.subject_name,
            }
        return tests

    async def _batch_count_correct(self, attempt_ids: List[int]) -> Dict:
        """Batch count total and correct answers per attempt."""
        result = await self.db.execute(
            select(
                TestAttemptAnswer.attempt_id,
                func.count(TestAttemptAnswer.id).label("total"),
                func.count(TestAttemptAnswer.id).filter(
                    TestAttemptAnswer.is_correct == True
                ).label("correct"),
            )
            .where(TestAttemptAnswer.attempt_id.in_(attempt_ids))
            .group_by(TestAttemptAnswer.attempt_id)
        )
        return {
            row.attempt_id: (row.total, row.correct)
            for row in result.fetchall()
        }
