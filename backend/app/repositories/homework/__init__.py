"""
Homework repositories package.

Provides modular repository classes and a facade for backward compatibility.
"""
from typing import Optional, List, Tuple, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.homework.homework_crud_repo import HomeworkCrudRepository
from app.repositories.homework.task_repo import HomeworkTaskRepository
from app.repositories.homework.question_repo import HomeworkQuestionRepository
from app.repositories.homework.student_assignment_repo import StudentAssignmentRepository
from app.repositories.homework.submission_repo import SubmissionRepository
from app.repositories.homework.answer_repo import AnswerRepository
from app.repositories.homework.stats_repo import HomeworkStatsRepository


class HomeworkRepository:
    """
    Facade repository that delegates to specialized repositories.

    Provides backward compatibility while internally using modular repos.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._crud = HomeworkCrudRepository(db)
        self._task = HomeworkTaskRepository(db)
        self._question = HomeworkQuestionRepository(db)
        self._assignment = StudentAssignmentRepository(db)
        self._submission = SubmissionRepository(db)
        self._answer = AnswerRepository(db)
        self._stats = HomeworkStatsRepository(db)

    # =========================================================================
    # Homework CRUD (delegates to HomeworkCrudRepository)
    # =========================================================================

    async def create(self, data: dict, school_id: int, teacher_id: int):
        return await self._crud.create(data, school_id, teacher_id)

    async def get_by_id(
        self,
        homework_id: int,
        school_id: int,
        load_tasks: bool = False,
        load_questions: bool = False
    ):
        return await self._crud.get_by_id(
            homework_id, school_id, load_tasks, load_questions
        )

    async def list_by_teacher(
        self,
        teacher_id: int,
        school_id: int,
        class_id: Optional[int] = None,
        status=None,
        limit: int = 50,
        offset: int = 0
    ):
        return await self._crud.list_by_teacher(
            teacher_id, school_id, class_id, status, limit, offset
        )

    async def list_by_class(
        self,
        class_id: int,
        school_id: int,
        status=None,
        include_stats: bool = False
    ):
        return await self._crud.list_by_class(
            class_id, school_id, status, include_stats
        )

    async def update(self, homework_id: int, school_id: int, data: dict):
        return await self._crud.update(homework_id, school_id, data)

    async def update_status(self, homework_id: int, school_id: int, status):
        return await self._crud.update_status(homework_id, school_id, status)

    async def soft_delete(self, homework_id: int, school_id: int) -> bool:
        return await self._crud.soft_delete(homework_id, school_id)

    # =========================================================================
    # Tasks (delegates to HomeworkTaskRepository)
    # =========================================================================

    async def add_task(self, homework_id: int, data: dict, school_id: int):
        return await self._task.add_task(homework_id, data, school_id)

    async def get_task_by_id(
        self,
        task_id: int,
        school_id: int,
        load_questions: bool = False
    ):
        return await self._task.get_task_by_id(task_id, school_id, load_questions)

    async def update_task(self, task_id: int, school_id: int, data: dict):
        return await self._task.update_task(task_id, school_id, data)

    async def delete_task(self, task_id: int, school_id: int) -> bool:
        return await self._task.delete_task(task_id, school_id)

    async def reorder_tasks(
        self,
        homework_id: int,
        school_id: int,
        task_ids: List[int]
    ) -> bool:
        return await self._task.reorder_tasks(homework_id, school_id, task_ids)

    # =========================================================================
    # Questions (delegates to HomeworkQuestionRepository)
    # =========================================================================

    async def add_question(self, task_id: int, school_id: int, data: dict):
        return await self._question.add_question(task_id, school_id, data)

    async def add_questions_batch(self, task_id: int, school_id: int, questions_data: List[dict]):
        return await self._question.add_questions_batch(task_id, school_id, questions_data)

    async def get_question_by_id(self, question_id: int):
        return await self._question.get_question_by_id(question_id)

    async def replace_question(self, question_id: int, new_data: dict):
        return await self._question.replace_question(question_id, new_data)

    async def deactivate_task_questions(self, task_id: int) -> int:
        return await self._question.deactivate_task_questions(task_id)

    async def get_active_questions_count(self, task_id: int) -> int:
        return await self._question.get_active_questions_count(task_id)

    # =========================================================================
    # Student Assignments (delegates to StudentAssignmentRepository)
    # =========================================================================

    async def assign_to_students(
        self,
        homework_id: int,
        school_id: int,
        student_ids: List[int]
    ):
        return await self._assignment.assign_to_students(
            homework_id, school_id, student_ids
        )

    async def get_student_homework(self, homework_id: int, student_id: int):
        return await self._assignment.get_student_homework(homework_id, student_id)

    async def list_student_homework(
        self,
        student_id: int,
        school_id: int,
        status=None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[list, int]:
        return await self._assignment.list_student_homework(
            student_id, school_id, status, page, page_size
        )

    async def update_student_homework_status(self, homework_student_id: int, status):
        return await self._assignment.update_student_homework_status(
            homework_student_id, status
        )

    # =========================================================================
    # Submissions (delegates to SubmissionRepository)
    # =========================================================================

    async def create_submission(
        self,
        homework_student_id: int,
        task_id: int,
        student_id: int,
        school_id: int,
        attempt_number: int
    ):
        return await self._submission.create_submission(
            homework_student_id, task_id, student_id, school_id, attempt_number
        )

    async def get_submission_by_id(
        self,
        submission_id: int,
        load_answers: bool = False
    ):
        return await self._submission.get_submission_by_id(submission_id, load_answers)

    async def get_attempts_count(self, homework_student_id: int, task_id: int) -> int:
        return await self._submission.get_attempts_count(homework_student_id, task_id)

    async def get_latest_submission(self, homework_student_id: int, task_id: int):
        return await self._submission.get_latest_submission(homework_student_id, task_id)

    async def update_submission(self, submission_id: int, data: dict):
        return await self._submission.update_submission(submission_id, data)

    # Batch methods to avoid N+1 queries
    async def get_attempts_counts_batch(
        self,
        homework_student_id: int,
        task_ids: List[int]
    ) -> dict:
        return await self._submission.get_attempts_counts_batch(
            homework_student_id, task_ids
        )

    async def get_latest_submissions_batch(
        self,
        homework_student_id: int,
        task_ids: List[int]
    ) -> dict:
        return await self._submission.get_latest_submissions_batch(
            homework_student_id, task_ids
        )

    # =========================================================================
    # Answers (delegates to AnswerRepository)
    # =========================================================================

    async def save_answer(
        self,
        submission_id: int,
        question_id: int,
        student_id: int,
        school_id: int,
        answer_text: Optional[str] = None,
        selected_options: Optional[List[str]] = None
    ):
        return await self._answer.save_answer(
            submission_id, question_id, student_id, school_id,
            answer_text, selected_options
        )

    async def get_answer_by_id(self, answer_id: int):
        return await self._answer.get_answer_by_id(answer_id)

    async def update_answer_grading(
        self,
        answer_id: int,
        is_correct: Optional[bool] = None,
        partial_score: Optional[float] = None,
        ai_score: Optional[float] = None,
        ai_confidence: Optional[float] = None,
        ai_feedback: Optional[str] = None,
        ai_rubric_scores: Optional[dict] = None,
        flagged_for_review: bool = False
    ):
        return await self._answer.update_answer_grading(
            answer_id, is_correct, partial_score, ai_score,
            ai_confidence, ai_feedback, ai_rubric_scores, flagged_for_review
        )

    async def get_answers_for_review(self, school_id: int, limit: int = 50):
        return await self._answer.get_answers_for_review(school_id, limit)

    async def teacher_review_answer(
        self,
        answer_id: int,
        score: float,
        feedback: Optional[str] = None
    ):
        return await self._answer.teacher_review_answer(answer_id, score, feedback)

    # =========================================================================
    # Stats (delegates to HomeworkStatsRepository)
    # =========================================================================

    async def get_homework_stats(self, homework_id: int, school_id: int) -> dict:
        return await self._stats.get_homework_stats(homework_id, school_id)

    async def get_homework_stats_batch(self, homework_ids: List[int]) -> Dict[int, dict]:
        """Get statistics for multiple homework in one query."""
        return await self._stats.get_homework_stats_batch(homework_ids)

    async def log_ai_operation(
        self,
        operation_type: str,
        school_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        homework_id: Optional[int] = None,
        task_id: Optional[int] = None,
        student_id: Optional[int] = None,
        input_context: Optional[dict] = None,
        prompt_used: Optional[str] = None,
        model_used: Optional[str] = None,
        raw_response: Optional[str] = None,
        parsed_output: Optional[dict] = None,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None,
        latency_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        return await self._stats.log_ai_operation(
            operation_type, school_id, teacher_id, homework_id, task_id,
            student_id, input_context, prompt_used, model_used, raw_response,
            parsed_output, tokens_input, tokens_output, latency_ms,
            success, error_message
        )


__all__ = [
    "HomeworkRepository",
    "HomeworkCrudRepository",
    "HomeworkTaskRepository",
    "HomeworkQuestionRepository",
    "StudentAssignmentRepository",
    "SubmissionRepository",
    "AnswerRepository",
    "HomeworkStatsRepository",
]
