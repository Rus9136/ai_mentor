"""
Repository for Homework data access.

Provides CRUD operations for:
- Homework assignments
- Homework tasks
- Homework questions (with versioning)
- Student assignments and submissions
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.homework import (
    Homework,
    HomeworkTask,
    HomeworkTaskQuestion,
    HomeworkStudent,
    StudentTaskSubmission,
    StudentTaskAnswer,
    AIGenerationLog,
    HomeworkStatus,
    HomeworkStudentStatus,
    TaskSubmissionStatus,
)


class HomeworkRepository:
    """Repository for Homework CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Homework CRUD
    # =========================================================================

    async def create(
        self,
        data: dict,
        school_id: int,
        teacher_id: int
    ) -> Homework:
        """
        Create a new homework assignment.

        Args:
            data: Homework data (from HomeworkCreate schema)
            school_id: School ID (from token)
            teacher_id: Teacher ID (from token)

        Returns:
            Created Homework
        """
        homework = Homework(
            **data,
            school_id=school_id,
            teacher_id=teacher_id,
            status=HomeworkStatus.DRAFT
        )
        self.db.add(homework)
        await self.db.flush()
        await self.db.refresh(homework)
        return homework

    async def get_by_id(
        self,
        homework_id: int,
        school_id: int,
        load_tasks: bool = False,
        load_questions: bool = False
    ) -> Optional[Homework]:
        """
        Get homework by ID with optional eager loading.

        Args:
            homework_id: Homework ID
            school_id: School ID for isolation
            load_tasks: Load tasks
            load_questions: Load questions (requires load_tasks=True)

        Returns:
            Homework or None
        """
        query = select(Homework).where(
            Homework.id == homework_id,
            Homework.school_id == school_id,
            Homework.is_deleted == False
        )

        if load_tasks:
            if load_questions:
                query = query.options(
                    selectinload(Homework.tasks)
                    .selectinload(HomeworkTask.questions.and_(
                        HomeworkTaskQuestion.is_active == True,
                        HomeworkTaskQuestion.is_deleted == False
                    ))
                )
            else:
                query = query.options(selectinload(Homework.tasks))

        result = await self.db.execute(query)
        homework = result.unique().scalar_one_or_none()

        # Sort tasks by sort_order
        if homework and homework.tasks:
            homework.tasks.sort(key=lambda t: t.sort_order)
            if load_questions:
                for task in homework.tasks:
                    if task.questions:
                        task.questions.sort(key=lambda q: q.sort_order)

        return homework

    async def list_by_teacher(
        self,
        teacher_id: int,
        school_id: int,
        class_id: Optional[int] = None,
        status: Optional[HomeworkStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Homework]:
        """
        List homework assignments for a teacher.

        Args:
            teacher_id: Teacher ID
            school_id: School ID
            class_id: Optional class filter
            status: Optional status filter
            limit: Max results
            offset: Offset for pagination

        Returns:
            List of Homework
        """
        query = (
            select(Homework)
            .where(
                Homework.teacher_id == teacher_id,
                Homework.school_id == school_id,
                Homework.is_deleted == False
            )
        )

        if class_id:
            query = query.where(Homework.class_id == class_id)

        if status:
            query = query.where(Homework.status == status)

        query = query.order_by(Homework.due_date.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_class(
        self,
        class_id: int,
        school_id: int,
        status: Optional[HomeworkStatus] = None,
        include_stats: bool = False
    ) -> List[Homework]:
        """
        List homework for a class.

        Args:
            class_id: Class ID
            school_id: School ID
            status: Optional status filter
            include_stats: Include submission stats

        Returns:
            List of Homework
        """
        query = (
            select(Homework)
            .where(
                Homework.class_id == class_id,
                Homework.school_id == school_id,
                Homework.is_deleted == False
            )
        )

        if status:
            query = query.where(Homework.status == status)

        query = query.order_by(Homework.due_date.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        homework_id: int,
        school_id: int,
        data: dict
    ) -> Optional[Homework]:
        """
        Update homework assignment.

        Args:
            homework_id: Homework ID
            school_id: School ID
            data: Update data

        Returns:
            Updated Homework or None
        """
        homework = await self.get_by_id(homework_id, school_id)
        if not homework:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(homework, key, value)

        homework.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(homework)
        return homework

    async def update_status(
        self,
        homework_id: int,
        school_id: int,
        status: HomeworkStatus
    ) -> Optional[Homework]:
        """
        Update homework status.

        Args:
            homework_id: Homework ID
            school_id: School ID
            status: New status

        Returns:
            Updated Homework or None
        """
        homework = await self.get_by_id(homework_id, school_id)
        if homework:
            homework.status = status
            homework.updated_at = datetime.utcnow()
            await self.db.flush()
        return homework

    async def soft_delete(self, homework_id: int, school_id: int) -> bool:
        """
        Soft delete homework.

        Args:
            homework_id: Homework ID
            school_id: School ID

        Returns:
            True if deleted
        """
        homework = await self.get_by_id(homework_id, school_id)
        if homework:
            homework.is_deleted = True
            homework.deleted_at = datetime.utcnow()
            await self.db.flush()
            return True
        return False

    # =========================================================================
    # Tasks
    # =========================================================================

    async def add_task(
        self,
        homework_id: int,
        data: dict,
        school_id: int
    ) -> HomeworkTask:
        """
        Add a task to homework.

        Args:
            homework_id: Homework ID
            data: Task data
            school_id: School ID (denormalized for RLS)

        Returns:
            Created HomeworkTask
        """
        task = HomeworkTask(
            **data,
            homework_id=homework_id,
            school_id=school_id
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def get_task_by_id(
        self,
        task_id: int,
        school_id: int,
        load_questions: bool = False
    ) -> Optional[HomeworkTask]:
        """
        Get task by ID.

        Args:
            task_id: Task ID
            school_id: School ID
            load_questions: Load active questions

        Returns:
            HomeworkTask or None
        """
        query = select(HomeworkTask).where(
            HomeworkTask.id == task_id,
            HomeworkTask.school_id == school_id,
            HomeworkTask.is_deleted == False
        )

        if load_questions:
            query = query.options(
                selectinload(HomeworkTask.questions.and_(
                    HomeworkTaskQuestion.is_active == True,
                    HomeworkTaskQuestion.is_deleted == False
                ))
            )

        result = await self.db.execute(query)
        task = result.unique().scalar_one_or_none()

        if task and task.questions:
            task.questions.sort(key=lambda q: q.sort_order)

        return task

    async def update_task(
        self,
        task_id: int,
        school_id: int,
        data: dict
    ) -> Optional[HomeworkTask]:
        """
        Update a task.

        Args:
            task_id: Task ID
            school_id: School ID
            data: Update data

        Returns:
            Updated HomeworkTask or None
        """
        task = await self.get_task_by_id(task_id, school_id)
        if not task:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(task, key, value)

        task.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task_id: int, school_id: int) -> bool:
        """Soft delete a task."""
        task = await self.get_task_by_id(task_id, school_id)
        if task:
            task.is_deleted = True
            task.deleted_at = datetime.utcnow()
            await self.db.flush()
            return True
        return False

    async def reorder_tasks(
        self,
        homework_id: int,
        school_id: int,
        task_ids: List[int]
    ) -> bool:
        """
        Reorder tasks in homework.

        Args:
            homework_id: Homework ID
            school_id: School ID
            task_ids: List of task IDs in new order

        Returns:
            True if successful
        """
        for order, task_id in enumerate(task_ids):
            await self.db.execute(
                update(HomeworkTask)
                .where(
                    HomeworkTask.id == task_id,
                    HomeworkTask.homework_id == homework_id,
                    HomeworkTask.school_id == school_id
                )
                .values(sort_order=order)
            )
        await self.db.flush()
        return True

    # =========================================================================
    # Questions (with versioning)
    # =========================================================================

    async def add_question(
        self,
        task_id: int,
        data: dict
    ) -> HomeworkTaskQuestion:
        """
        Add a question to task.

        Args:
            task_id: Task ID
            data: Question data

        Returns:
            Created HomeworkTaskQuestion
        """
        # Get current max sort_order
        result = await self.db.execute(
            select(func.max(HomeworkTaskQuestion.sort_order))
            .where(HomeworkTaskQuestion.homework_task_id == task_id)
        )
        max_order = result.scalar() or 0

        question = HomeworkTaskQuestion(
            **data,
            homework_task_id=task_id,
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
        questions_data: List[dict]
    ) -> List[HomeworkTaskQuestion]:
        """
        Add multiple questions to task (for AI generation).

        Args:
            task_id: Task ID
            questions_data: List of question data

        Returns:
            List of created questions
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

        Args:
            question_id: ID of question to replace
            new_data: New question data

        Returns:
            New HomeworkTaskQuestion version
        """
        old_question = await self.get_question_by_id(question_id)
        if not old_question:
            raise ValueError(f"Question {question_id} not found")

        # Deactivate old version
        old_question.is_active = False

        # Create new version
        new_question = HomeworkTaskQuestion(
            **new_data,
            homework_task_id=old_question.homework_task_id,
            sort_order=old_question.sort_order,
            version=old_question.version + 1,
            is_active=True
        )
        self.db.add(new_question)
        await self.db.flush()

        # Link versions
        old_question.replaced_by_id = new_question.id
        await self.db.refresh(new_question)

        return new_question

    async def deactivate_task_questions(
        self,
        task_id: int
    ) -> int:
        """
        Deactivate all questions in task (for regeneration).

        Args:
            task_id: Task ID

        Returns:
            Number of deactivated questions
        """
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

    # =========================================================================
    # Student Assignments
    # =========================================================================

    async def assign_to_students(
        self,
        homework_id: int,
        school_id: int,
        student_ids: List[int]
    ) -> List[HomeworkStudent]:
        """
        Assign homework to students.

        Args:
            homework_id: Homework ID
            school_id: School ID
            student_ids: List of student IDs

        Returns:
            List of HomeworkStudent assignments
        """
        assignments = []
        for student_id in student_ids:
            # Check if already assigned
            existing = await self.db.execute(
                select(HomeworkStudent).where(
                    HomeworkStudent.homework_id == homework_id,
                    HomeworkStudent.student_id == student_id
                )
            )
            if existing.scalar_one_or_none():
                continue

            assignment = HomeworkStudent(
                homework_id=homework_id,
                student_id=student_id,
                school_id=school_id,
                status=HomeworkStudentStatus.ASSIGNED
            )
            self.db.add(assignment)
            assignments.append(assignment)

        await self.db.flush()
        for a in assignments:
            await self.db.refresh(a)
        return assignments

    async def get_student_homework(
        self,
        homework_id: int,
        student_id: int
    ) -> Optional[HomeworkStudent]:
        """
        Get student's homework assignment.

        Args:
            homework_id: Homework ID
            student_id: Student ID

        Returns:
            HomeworkStudent or None
        """
        result = await self.db.execute(
            select(HomeworkStudent)
            .options(selectinload(HomeworkStudent.task_submissions))
            .where(
                HomeworkStudent.homework_id == homework_id,
                HomeworkStudent.student_id == student_id,
                HomeworkStudent.is_deleted == False
            )
        )
        return result.unique().scalar_one_or_none()

    async def list_student_homework(
        self,
        student_id: int,
        school_id: int,
        status: Optional[HomeworkStudentStatus] = None,
        limit: int = 50
    ) -> List[HomeworkStudent]:
        """
        List homework assigned to a student.

        Args:
            student_id: Student ID
            school_id: School ID
            status: Optional status filter
            limit: Max results

        Returns:
            List of HomeworkStudent
        """
        query = (
            select(HomeworkStudent)
            .options(selectinload(HomeworkStudent.homework))
            .where(
                HomeworkStudent.student_id == student_id,
                HomeworkStudent.school_id == school_id,
                HomeworkStudent.is_deleted == False
            )
        )

        if status:
            query = query.where(HomeworkStudent.status == status)

        # Join with homework to filter by published status and order by due_date
        query = (
            query
            .join(Homework)
            .where(
                Homework.status == HomeworkStatus.PUBLISHED,
                Homework.is_deleted == False
            )
            .order_by(Homework.due_date.asc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.unique().scalars().all())

    async def update_student_homework_status(
        self,
        homework_student_id: int,
        status: HomeworkStudentStatus
    ) -> Optional[HomeworkStudent]:
        """Update student homework status."""
        result = await self.db.execute(
            select(HomeworkStudent).where(HomeworkStudent.id == homework_student_id)
        )
        hw_student = result.scalar_one_or_none()
        if hw_student:
            hw_student.status = status
            hw_student.updated_at = datetime.utcnow()
            await self.db.flush()
        return hw_student

    # =========================================================================
    # Submissions
    # =========================================================================

    async def create_submission(
        self,
        homework_student_id: int,
        task_id: int,
        student_id: int,
        school_id: int,
        attempt_number: int
    ) -> StudentTaskSubmission:
        """
        Create a task submission.

        Args:
            homework_student_id: HomeworkStudent ID
            task_id: Task ID
            student_id: Student ID
            school_id: School ID
            attempt_number: Attempt number

        Returns:
            Created StudentTaskSubmission
        """
        submission = StudentTaskSubmission(
            homework_student_id=homework_student_id,
            homework_task_id=task_id,
            student_id=student_id,
            school_id=school_id,
            attempt_number=attempt_number,
            status=TaskSubmissionStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )
        self.db.add(submission)
        await self.db.flush()
        await self.db.refresh(submission)
        return submission

    async def get_submission_by_id(
        self,
        submission_id: int,
        load_answers: bool = False
    ) -> Optional[StudentTaskSubmission]:
        """Get submission by ID."""
        query = select(StudentTaskSubmission).where(
            StudentTaskSubmission.id == submission_id,
            StudentTaskSubmission.is_deleted == False
        )

        if load_answers:
            query = query.options(selectinload(StudentTaskSubmission.answers))

        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_attempts_count(
        self,
        homework_student_id: int,
        task_id: int
    ) -> int:
        """Get number of attempts for a task."""
        result = await self.db.execute(
            select(func.count())
            .select_from(StudentTaskSubmission)
            .where(
                StudentTaskSubmission.homework_student_id == homework_student_id,
                StudentTaskSubmission.homework_task_id == task_id,
                StudentTaskSubmission.is_deleted == False
            )
        )
        return result.scalar() or 0

    async def get_latest_submission(
        self,
        homework_student_id: int,
        task_id: int
    ) -> Optional[StudentTaskSubmission]:
        """Get latest submission for a task."""
        result = await self.db.execute(
            select(StudentTaskSubmission)
            .where(
                StudentTaskSubmission.homework_student_id == homework_student_id,
                StudentTaskSubmission.homework_task_id == task_id,
                StudentTaskSubmission.is_deleted == False
            )
            .order_by(StudentTaskSubmission.attempt_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_submission(
        self,
        submission_id: int,
        data: dict
    ) -> Optional[StudentTaskSubmission]:
        """Update submission."""
        submission = await self.get_submission_by_id(submission_id)
        if not submission:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(submission, key, value)

        submission.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(submission)
        return submission

    # =========================================================================
    # Answers
    # =========================================================================

    async def save_answer(
        self,
        submission_id: int,
        question_id: int,
        student_id: int,
        school_id: int,
        answer_text: Optional[str] = None,
        selected_options: Optional[List[str]] = None
    ) -> StudentTaskAnswer:
        """
        Save an answer to a question.

        Args:
            submission_id: Submission ID
            question_id: Question ID
            student_id: Student ID
            school_id: School ID
            answer_text: Text answer
            selected_options: Selected option IDs

        Returns:
            Created or updated StudentTaskAnswer
        """
        # Check if answer already exists
        result = await self.db.execute(
            select(StudentTaskAnswer).where(
                StudentTaskAnswer.submission_id == submission_id,
                StudentTaskAnswer.question_id == question_id
            )
        )
        answer = result.scalar_one_or_none()

        if answer:
            # Update existing
            answer.answer_text = answer_text
            answer.selected_option_ids = selected_options
            answer.answered_at = datetime.utcnow()
        else:
            # Create new
            answer = StudentTaskAnswer(
                submission_id=submission_id,
                question_id=question_id,
                student_id=student_id,
                school_id=school_id,
                answer_text=answer_text,
                selected_option_ids=selected_options,
                answered_at=datetime.utcnow()
            )
            self.db.add(answer)

        await self.db.flush()
        await self.db.refresh(answer)
        return answer

    async def get_answer_by_id(
        self,
        answer_id: int
    ) -> Optional[StudentTaskAnswer]:
        """Get answer by ID."""
        result = await self.db.execute(
            select(StudentTaskAnswer).where(
                StudentTaskAnswer.id == answer_id,
                StudentTaskAnswer.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

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
    ) -> Optional[StudentTaskAnswer]:
        """Update answer with grading info."""
        answer = await self.get_answer_by_id(answer_id)
        if not answer:
            return None

        if is_correct is not None:
            answer.is_correct = is_correct
        if partial_score is not None:
            answer.partial_score = partial_score
        if ai_score is not None:
            answer.ai_score = ai_score
            answer.ai_graded_at = datetime.utcnow()
        if ai_confidence is not None:
            answer.ai_confidence = ai_confidence
        if ai_feedback is not None:
            answer.ai_feedback = ai_feedback
        if ai_rubric_scores is not None:
            answer.ai_rubric_scores = ai_rubric_scores

        answer.flagged_for_review = flagged_for_review
        answer.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(answer)
        return answer

    async def get_answers_for_review(
        self,
        school_id: int,
        limit: int = 50
    ) -> List[StudentTaskAnswer]:
        """
        Get answers flagged for teacher review.

        Args:
            school_id: School ID
            limit: Max results

        Returns:
            List of StudentTaskAnswer
        """
        result = await self.db.execute(
            select(StudentTaskAnswer)
            .options(
                selectinload(StudentTaskAnswer.question),
                selectinload(StudentTaskAnswer.student)
            )
            .where(
                StudentTaskAnswer.school_id == school_id,
                StudentTaskAnswer.flagged_for_review == True,
                StudentTaskAnswer.teacher_override_score.is_(None),
                StudentTaskAnswer.is_deleted == False
            )
            .order_by(StudentTaskAnswer.answered_at)
            .limit(limit)
        )
        return list(result.unique().scalars().all())

    async def teacher_review_answer(
        self,
        answer_id: int,
        score: float,
        feedback: Optional[str] = None
    ) -> Optional[StudentTaskAnswer]:
        """
        Teacher reviews an answer.

        Args:
            answer_id: Answer ID
            score: Teacher score
            feedback: Teacher feedback

        Returns:
            Updated StudentTaskAnswer
        """
        answer = await self.get_answer_by_id(answer_id)
        if not answer:
            return None

        answer.teacher_override_score = score
        answer.teacher_comment = feedback
        answer.flagged_for_review = False
        answer.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(answer)
        return answer

    # =========================================================================
    # Stats
    # =========================================================================

    async def get_homework_stats(
        self,
        homework_id: int,
        school_id: int
    ) -> dict:
        """
        Get statistics for a homework.

        Args:
            homework_id: Homework ID
            school_id: School ID

        Returns:
            Dict with stats
        """
        # Total students
        total_result = await self.db.execute(
            select(func.count())
            .select_from(HomeworkStudent)
            .where(
                HomeworkStudent.homework_id == homework_id,
                HomeworkStudent.is_deleted == False
            )
        )
        total_students = total_result.scalar() or 0

        # Submitted count
        submitted_result = await self.db.execute(
            select(func.count())
            .select_from(HomeworkStudent)
            .where(
                HomeworkStudent.homework_id == homework_id,
                HomeworkStudent.status.in_([
                    HomeworkStudentStatus.SUBMITTED,
                    HomeworkStudentStatus.GRADED
                ]),
                HomeworkStudent.is_deleted == False
            )
        )
        submitted_count = submitted_result.scalar() or 0

        # Graded count
        graded_result = await self.db.execute(
            select(func.count())
            .select_from(HomeworkStudent)
            .where(
                HomeworkStudent.homework_id == homework_id,
                HomeworkStudent.status == HomeworkStudentStatus.GRADED,
                HomeworkStudent.is_deleted == False
            )
        )
        graded_count = graded_result.scalar() or 0

        # Average score
        avg_result = await self.db.execute(
            select(func.avg(HomeworkStudent.percentage))
            .where(
                HomeworkStudent.homework_id == homework_id,
                HomeworkStudent.percentage.isnot(None),
                HomeworkStudent.is_deleted == False
            )
        )
        average_score = avg_result.scalar()

        return {
            "total_students": total_students,
            "submitted_count": submitted_count,
            "graded_count": graded_count,
            "average_score": round(average_score, 2) if average_score else None
        }

    # =========================================================================
    # AI Logging
    # =========================================================================

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
    ) -> AIGenerationLog:
        """
        Log an AI operation for auditing.

        Args:
            operation_type: Type of operation
            Various context and metrics

        Returns:
            Created AIGenerationLog
        """
        log = AIGenerationLog(
            operation_type=operation_type,
            school_id=school_id,
            teacher_id=teacher_id,
            homework_id=homework_id,
            homework_task_id=task_id,
            student_id=student_id,
            input_context=input_context,
            prompt_used=prompt_used,
            model_used=model_used,
            raw_response=raw_response,
            parsed_output=parsed_output,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log
