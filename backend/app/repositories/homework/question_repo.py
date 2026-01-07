"""
Repository for HomeworkTaskQuestion operations with versioning support.
"""
from typing import Optional, List
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import HomeworkTaskQuestion


class HomeworkQuestionRepository:
    """Repository for HomeworkTaskQuestion operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_question(
        self,
        task_id: int,
        school_id: int,
        data: dict
    ) -> HomeworkTaskQuestion:
        """Add a question to task.

        Args:
            task_id: Parent task ID
            school_id: School ID for RLS (denormalized from task)
            data: Question data dict
        """
        result = await self.db.execute(
            select(func.max(HomeworkTaskQuestion.sort_order))
            .where(HomeworkTaskQuestion.homework_task_id == task_id)
        )
        max_order = result.scalar() or 0

        question = HomeworkTaskQuestion(
            **data,
            homework_task_id=task_id,
            school_id=school_id,
            sort_order=max_order + 1,
            version=1,
            is_active=True
        )
        self.db.add(question)
        await self.db.flush()
        await self.db.refresh(question)
        return question

    async def add_questions_batch(
        self,
        task_id: int,
        school_id: int,
        questions_data: List[dict]
    ) -> List[HomeworkTaskQuestion]:
        """Add multiple questions to task (for AI generation).

        Args:
            task_id: Parent task ID
            school_id: School ID for RLS (denormalized from task)
            questions_data: List of question data dicts
        """
        result = await self.db.execute(
            select(func.max(HomeworkTaskQuestion.sort_order))
            .where(HomeworkTaskQuestion.homework_task_id == task_id)
        )
        max_order = result.scalar() or 0

        questions = []
        for i, data in enumerate(questions_data):
            question = HomeworkTaskQuestion(
                **data,
                homework_task_id=task_id,
                school_id=school_id,
                sort_order=max_order + i + 1,
                version=1,
                is_active=True,
                ai_generated=True
            )
            self.db.add(question)
            questions.append(question)

        await self.db.flush()
        for q in questions:
            await self.db.refresh(q)
        return questions

    async def get_question_by_id(
        self,
        question_id: int
    ) -> Optional[HomeworkTaskQuestion]:
        """Get question by ID."""
        result = await self.db.execute(
            select(HomeworkTaskQuestion).where(
                HomeworkTaskQuestion.id == question_id,
                HomeworkTaskQuestion.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def replace_question(
        self,
        question_id: int,
        new_data: dict
    ) -> HomeworkTaskQuestion:
        """
        Create new version of question (for editing).

        Old version is deactivated, new version created.
        This preserves student answers linked to old version.
        school_id is automatically copied from old version.
        """
        old_question = await self.get_question_by_id(question_id)
        if not old_question:
            raise ValueError(f"Question {question_id} not found")

        old_question.is_active = False

        new_question = HomeworkTaskQuestion(
            **new_data,
            homework_task_id=old_question.homework_task_id,
            school_id=old_question.school_id,  # Copy school_id from old version
            sort_order=old_question.sort_order,
            version=old_question.version + 1,
            is_active=True
        )
        self.db.add(new_question)
        await self.db.flush()

        old_question.replaced_by_id = new_question.id
        await self.db.refresh(new_question)

        return new_question

    async def deactivate_task_questions(
        self,
        task_id: int
    ) -> int:
        """Deactivate all questions in task (for regeneration)."""
        result = await self.db.execute(
            update(HomeworkTaskQuestion)
            .where(
                HomeworkTaskQuestion.homework_task_id == task_id,
                HomeworkTaskQuestion.is_active == True
            )
            .values(is_active=False)
        )
        await self.db.flush()
        return result.rowcount

    async def get_active_questions_count(self, task_id: int) -> int:
        """Get count of active questions in task."""
        result = await self.db.execute(
            select(func.count())
            .select_from(HomeworkTaskQuestion)
            .where(
                HomeworkTaskQuestion.homework_task_id == task_id,
                HomeworkTaskQuestion.is_active == True,
                HomeworkTaskQuestion.is_deleted == False
            )
        )
        return result.scalar() or 0
