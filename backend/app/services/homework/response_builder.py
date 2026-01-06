"""
Homework Response Builder.

Converts Homework models to response schemas for teacher API.
"""
from typing import List

from app.models.homework import Homework, HomeworkTask, HomeworkTaskQuestion
from app.schemas.homework import (
    HomeworkResponse,
    HomeworkTaskResponse,
    QuestionResponse,
    QuestionResponseWithAnswer,
)


class HomeworkResponseBuilder:
    """Builder for homework API responses."""

    @staticmethod
    def build_question_response(question: HomeworkTaskQuestion) -> QuestionResponse:
        """Build question response without correct answer."""
        return QuestionResponse(
            id=question.id,
            question_text=question.question_text,
            question_type=question.question_type,
            options=question.options,
            points=question.points,
            difficulty=question.difficulty,
            bloom_level=question.bloom_level,
            explanation=question.explanation,
            version=question.version,
            is_active=question.is_active,
            ai_generated=question.ai_generated,
            created_at=question.created_at
        )

    @staticmethod
    def build_question_with_answer(
        question: HomeworkTaskQuestion
    ) -> QuestionResponseWithAnswer:
        """Build question response with correct answer (for teacher view)."""
        return QuestionResponseWithAnswer(
            id=question.id,
            question_text=question.question_text,
            question_type=question.question_type,
            options=question.options,
            points=question.points,
            difficulty=question.difficulty,
            bloom_level=question.bloom_level,
            explanation=question.explanation,
            version=question.version,
            is_active=question.is_active,
            ai_generated=question.ai_generated,
            created_at=question.created_at,
            correct_answer=question.correct_answer,
            grading_rubric=question.grading_rubric,
            expected_answer_hints=question.expected_answer_hints
        )

    @staticmethod
    def build_task_response(
        task: HomeworkTask,
        include_questions: bool = True
    ) -> HomeworkTaskResponse:
        """Build task response with optional questions."""
        questions_response: List[QuestionResponse] = []

        if include_questions and hasattr(task, 'questions') and task.questions:
            questions_response = [
                HomeworkResponseBuilder.build_question_response(q)
                for q in task.questions
            ]

        return HomeworkTaskResponse(
            id=task.id,
            paragraph_id=task.paragraph_id,
            chapter_id=task.chapter_id,
            task_type=task.task_type,
            sort_order=task.sort_order,
            is_required=task.is_required,
            points=task.points,
            time_limit_minutes=task.time_limit_minutes,
            max_attempts=task.max_attempts,
            ai_generated=task.ai_generated,
            instructions=task.instructions,
            questions_count=len(questions_response),
            questions=questions_response
        )

    @staticmethod
    def build_homework_response(homework: Homework) -> HomeworkResponse:
        """Build complete homework response with tasks and questions."""
        tasks_response: List[HomeworkTaskResponse] = []

        if homework.tasks:
            tasks_response = [
                HomeworkResponseBuilder.build_task_response(task)
                for task in homework.tasks
            ]

        return HomeworkResponse(
            id=homework.id,
            title=homework.title,
            description=homework.description,
            status=homework.status,
            due_date=homework.due_date,
            class_id=homework.class_id,
            teacher_id=homework.teacher_id,
            ai_generation_enabled=homework.ai_generation_enabled,
            ai_check_enabled=homework.ai_check_enabled,
            target_difficulty=homework.target_difficulty,
            personalization_enabled=homework.personalization_enabled,
            auto_check_enabled=homework.auto_check_enabled,
            show_answers_after=homework.show_answers_after,
            show_explanations=homework.show_explanations,
            late_submission_allowed=homework.late_submission_allowed,
            late_penalty_per_day=homework.late_penalty_per_day,
            grace_period_hours=homework.grace_period_hours,
            max_late_days=homework.max_late_days,
            tasks=tasks_response,
            created_at=homework.created_at,
            updated_at=homework.updated_at
        )
