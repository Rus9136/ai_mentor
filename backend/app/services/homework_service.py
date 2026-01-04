"""
Homework Service for managing homework assignments.

Business logic for:
- Creating and publishing homework
- Managing tasks and questions
- Student submissions and attempts
- Late submission handling
- Auto-grading for choice questions
"""
import logging
from typing import Optional, List, Tuple, TYPE_CHECKING
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import (
    Homework,
    HomeworkTask,
    HomeworkTaskQuestion,
    HomeworkStudent,
    StudentTaskSubmission,
    StudentTaskAnswer,
    HomeworkStatus,
    HomeworkStudentStatus,
    TaskSubmissionStatus,
)
from app.repositories.homework_repo import HomeworkRepository
from app.schemas.homework import (
    HomeworkCreate,
    HomeworkUpdate,
    HomeworkTaskCreate,
    QuestionCreate,
    GenerationParams,
    SubmissionResult,
    TaskSubmissionResult,
)

if TYPE_CHECKING:
    from app.services.homework_ai_service import HomeworkAIService

logger = logging.getLogger(__name__)


class HomeworkServiceError(Exception):
    """Exception for homework service errors."""
    pass


class HomeworkService:
    """
    Service for homework business logic.

    Handles:
    - Homework CRUD with validation
    - Publishing and student assignment
    - Task and question management
    - Student submissions with attempts tracking
    - Late submission penalties
    - Auto-grading for objective questions
    """

    def __init__(
        self,
        db: AsyncSession,
        ai_service: Optional["HomeworkAIService"] = None
    ):
        """
        Initialize HomeworkService.

        Args:
            db: AsyncSession for database operations
            ai_service: Optional AI service for question generation/grading
        """
        self.db = db
        self.homework_repo = HomeworkRepository(db)
        self.ai_service = ai_service

    # =========================================================================
    # Homework CRUD
    # =========================================================================

    async def create_homework(
        self,
        data: HomeworkCreate,
        school_id: int,
        teacher_id: int
    ) -> Homework:
        """
        Create a new homework assignment (draft).

        Args:
            data: Homework creation data
            school_id: School ID from token
            teacher_id: Teacher ID from token

        Returns:
            Created Homework in DRAFT status
        """
        logger.info(
            f"Creating homework: title='{data.title}', "
            f"class_id={data.class_id}, teacher_id={teacher_id}"
        )

        homework = await self.homework_repo.create(
            data=data.model_dump(exclude={"tasks"}),
            school_id=school_id,
            teacher_id=teacher_id
        )

        # Create tasks if provided
        if data.tasks:
            for task_data in data.tasks:
                await self.add_task(
                    homework_id=homework.id,
                    data=task_data,
                    school_id=school_id
                )

        return homework

    async def get_homework(
        self,
        homework_id: int,
        school_id: int,
        load_tasks: bool = True,
        load_questions: bool = True
    ) -> Optional[Homework]:
        """
        Get homework by ID.

        Args:
            homework_id: Homework ID
            school_id: School ID for isolation
            load_tasks: Include tasks in response
            load_questions: Include questions in response

        Returns:
            Homework or None if not found
        """
        return await self.homework_repo.get_by_id(
            homework_id=homework_id,
            school_id=school_id,
            load_tasks=load_tasks,
            load_questions=load_questions
        )

    async def update_homework(
        self,
        homework_id: int,
        data: HomeworkUpdate,
        school_id: int
    ) -> Optional[Homework]:
        """
        Update homework (only in DRAFT status).

        Args:
            homework_id: Homework ID
            data: Update data
            school_id: School ID for isolation

        Returns:
            Updated Homework

        Raises:
            HomeworkServiceError: If homework is not in DRAFT status
        """
        homework = await self.get_homework(homework_id, school_id, load_tasks=False)
        if not homework:
            return None

        if homework.status != HomeworkStatus.DRAFT:
            raise HomeworkServiceError(
                "Cannot modify homework after publishing"
            )

        return await self.homework_repo.update(
            homework_id=homework_id,
            school_id=school_id,
            data=data.model_dump(exclude_unset=True)
        )

    async def list_homework_by_teacher(
        self,
        teacher_id: int,
        school_id: int,
        status: Optional[HomeworkStatus] = None,
        class_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Homework]:
        """
        List homework created by teacher.

        Args:
            teacher_id: Teacher ID
            school_id: School ID
            status: Filter by status
            class_id: Filter by class
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of homework assignments
        """
        return await self.homework_repo.list_by_teacher(
            teacher_id=teacher_id,
            school_id=school_id,
            status=status,
            class_id=class_id,
            offset=skip,
            limit=limit
        )

    async def list_homework_by_class(
        self,
        class_id: int,
        school_id: int,
        status: Optional[HomeworkStatus] = None
    ) -> List[Homework]:
        """
        List homework for a class.

        Args:
            class_id: Class ID
            school_id: School ID
            status: Filter by status

        Returns:
            List of homework assignments
        """
        return await self.homework_repo.list_by_class(
            class_id=class_id,
            school_id=school_id,
            status=status
        )

    # =========================================================================
    # Publishing
    # =========================================================================

    async def publish_homework(
        self,
        homework_id: int,
        school_id: int,
        student_ids: Optional[List[int]] = None
    ) -> Homework:
        """
        Publish homework and assign to students.

        Args:
            homework_id: Homework ID
            school_id: School ID
            student_ids: Optional list of student IDs.
                        If None, assigns to all students in class.

        Returns:
            Published Homework

        Raises:
            HomeworkServiceError: If homework cannot be published
        """
        homework = await self.get_homework(homework_id, school_id, load_tasks=True)
        if not homework:
            raise HomeworkServiceError("Homework not found")

        if homework.status != HomeworkStatus.DRAFT:
            raise HomeworkServiceError("Can only publish draft homework")

        if not homework.tasks:
            raise HomeworkServiceError("Homework must have at least one task")

        # Validate all tasks have questions
        for task in homework.tasks:
            if not task.questions:
                raise HomeworkServiceError(
                    f"Task '{task.paragraph_id}' has no questions"
                )

        # Get students to assign
        if student_ids is None:
            # Get all students from class
            from app.repositories.school_class_repo import SchoolClassRepository
            class_repo = SchoolClassRepository(self.db)
            students = await class_repo.get_students_in_class(
                class_id=homework.class_id,
                school_id=school_id
            )
            student_ids = [s.id for s in students]

        if not student_ids:
            raise HomeworkServiceError("No students to assign homework to")

        logger.info(
            f"Publishing homework {homework_id} to {len(student_ids)} students"
        )

        # Assign to students
        await self.homework_repo.assign_to_students(
            homework_id=homework_id,
            student_ids=student_ids
        )

        # Update status
        homework = await self.homework_repo.update_status(
            homework_id=homework_id,
            school_id=school_id,
            status=HomeworkStatus.PUBLISHED
        )

        return homework

    async def close_homework(
        self,
        homework_id: int,
        school_id: int
    ) -> Homework:
        """
        Close homework for submissions.

        Args:
            homework_id: Homework ID
            school_id: School ID

        Returns:
            Closed Homework
        """
        homework = await self.get_homework(homework_id, school_id, load_tasks=False)
        if not homework:
            raise HomeworkServiceError("Homework not found")

        if homework.status != HomeworkStatus.PUBLISHED:
            raise HomeworkServiceError("Can only close published homework")

        return await self.homework_repo.update_status(
            homework_id=homework_id,
            school_id=school_id,
            status=HomeworkStatus.CLOSED
        )

    # =========================================================================
    # Tasks
    # =========================================================================

    async def add_task(
        self,
        homework_id: int,
        data: HomeworkTaskCreate,
        school_id: int
    ) -> HomeworkTask:
        """
        Add a task to homework.

        Args:
            homework_id: Homework ID
            data: Task data
            school_id: School ID

        Returns:
            Created HomeworkTask

        Raises:
            HomeworkServiceError: If homework is not in DRAFT status
        """
        homework = await self.get_homework(homework_id, school_id, load_tasks=False)
        if not homework:
            raise HomeworkServiceError("Homework not found")

        if homework.status != HomeworkStatus.DRAFT:
            raise HomeworkServiceError(
                "Cannot add tasks to published homework"
            )

        task = await self.homework_repo.add_task(
            homework_id=homework_id,
            data=data.model_dump(exclude={"questions"}),
            school_id=school_id
        )

        # Add questions if provided
        if data.questions:
            for q_data in data.questions:
                await self.add_question(
                    task_id=task.id,
                    data=q_data
                )

        return task

    async def get_task(
        self,
        task_id: int,
        school_id: int,
        load_questions: bool = True
    ) -> Optional[HomeworkTask]:
        """
        Get task by ID.

        Args:
            task_id: Task ID
            school_id: School ID for isolation
            load_questions: Include questions

        Returns:
            HomeworkTask or None
        """
        return await self.homework_repo.get_task_by_id(
            task_id=task_id,
            school_id=school_id,
            load_questions=load_questions
        )

    async def delete_task(
        self,
        task_id: int,
        school_id: int
    ) -> bool:
        """
        Delete task (soft delete).

        Args:
            task_id: Task ID
            school_id: School ID

        Returns:
            True if deleted

        Raises:
            HomeworkServiceError: If task belongs to published homework
        """
        task = await self.get_task(task_id, school_id, load_questions=False)
        if not task:
            return False

        homework = await self.get_homework(
            task.homework_id, school_id, load_tasks=False
        )
        if homework and homework.status != HomeworkStatus.DRAFT:
            raise HomeworkServiceError(
                "Cannot delete tasks from published homework"
            )

        return await self.homework_repo.delete_task(task_id, school_id)

    # =========================================================================
    # Questions
    # =========================================================================

    async def add_question(
        self,
        task_id: int,
        data: QuestionCreate
    ) -> HomeworkTaskQuestion:
        """
        Add a question to task.

        Args:
            task_id: Task ID
            data: Question data

        Returns:
            Created HomeworkTaskQuestion
        """
        return await self.homework_repo.add_question(
            task_id=task_id,
            data=data.model_dump()
        )

    async def add_questions_batch(
        self,
        task_id: int,
        questions: List[QuestionCreate]
    ) -> List[HomeworkTaskQuestion]:
        """
        Add multiple questions to task.

        Args:
            task_id: Task ID
            questions: List of question data

        Returns:
            List of created questions
        """
        return await self.homework_repo.add_questions_batch(
            task_id=task_id,
            questions=[q.model_dump() for q in questions]
        )

    async def replace_question(
        self,
        question_id: int,
        new_data: QuestionCreate
    ) -> HomeworkTaskQuestion:
        """
        Replace question with new version (versioning).

        Args:
            question_id: ID of question to replace
            new_data: New question data

        Returns:
            New version of question
        """
        return await self.homework_repo.replace_question(
            question_id=question_id,
            new_data=new_data.model_dump()
        )

    # =========================================================================
    # AI Generation
    # =========================================================================

    async def generate_questions_for_task(
        self,
        task_id: int,
        school_id: int,
        regenerate: bool = False
    ) -> List[HomeworkTaskQuestion]:
        """
        Generate questions for task using AI.

        Args:
            task_id: Task ID
            school_id: School ID
            regenerate: If True, deactivate existing and generate new

        Returns:
            List of generated questions

        Raises:
            HomeworkServiceError: If AI service not available or task misconfigured
        """
        if not self.ai_service:
            raise HomeworkServiceError("AI service not configured")

        task = await self.get_task(task_id, school_id)
        if not task:
            raise HomeworkServiceError("Task not found")

        if not task.generation_params:
            raise HomeworkServiceError(
                "Task has no generation parameters configured"
            )

        if task.questions and not regenerate:
            raise HomeworkServiceError(
                "Task already has questions. Use regenerate=True"
            )

        # Deactivate existing questions if regenerating
        if regenerate and task.questions:
            await self.homework_repo.deactivate_task_questions(task_id)

        logger.info(
            f"Generating questions for task {task_id} with params: "
            f"{task.generation_params}"
        )

        # Generate via AI service
        params = GenerationParams.model_validate(task.generation_params)
        questions = await self.ai_service.generate_questions(
            paragraph_id=task.paragraph_id,
            params=params,
            task_id=task_id
        )

        # Save generated questions
        saved = []
        for q_data in questions:
            question = await self.homework_repo.add_question(task_id, q_data)
            saved.append(question)

        # Mark task as AI-generated
        await self.homework_repo.update_task(
            task_id=task_id,
            school_id=school_id,
            data={"ai_generated": True}
        )

        return saved

    # =========================================================================
    # Student Submissions
    # =========================================================================

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
        return await self.homework_repo.get_student_homework(
            homework_id=homework_id,
            student_id=student_id
        )

    async def list_student_homework(
        self,
        student_id: int,
        school_id: int,
        status: Optional[HomeworkStudentStatus] = None,
        limit: int = 50
    ) -> List[HomeworkStudent]:
        """
        List homework assigned to student.

        Args:
            student_id: Student ID
            school_id: School ID
            status: Filter by status
            limit: Pagination limit

        Returns:
            List of HomeworkStudent assignments
        """
        return await self.homework_repo.list_student_homework(
            student_id=student_id,
            school_id=school_id,
            status=status,
            limit=limit
        )

    async def start_task(
        self,
        homework_id: int,
        task_id: int,
        student_id: int
    ) -> StudentTaskSubmission:
        """
        Start a task attempt.

        Args:
            homework_id: Homework ID
            task_id: Task ID
            student_id: Student ID

        Returns:
            Created StudentTaskSubmission

        Raises:
            HomeworkServiceError: If max attempts exceeded or not assigned
        """
        # Verify assignment
        hw_student = await self.get_student_homework(homework_id, student_id)
        if not hw_student:
            raise HomeworkServiceError("Homework not assigned to student")

        # Get homework to check deadline
        homework = await self.homework_repo.get_by_id(
            homework_id=homework_id,
            school_id=hw_student.homework.school_id,
            load_tasks=False
        )

        if not homework:
            raise HomeworkServiceError("Homework not found")

        # Check if homework is open
        if homework.status == HomeworkStatus.CLOSED:
            raise HomeworkServiceError("Homework is closed")

        if homework.status == HomeworkStatus.DRAFT:
            raise HomeworkServiceError("Homework is not published yet")

        # Get task to check max attempts
        task = await self.homework_repo.get_task_by_id(
            task_id=task_id,
            school_id=homework.school_id,
            load_questions=False
        )
        if not task or task.homework_id != homework_id:
            raise HomeworkServiceError("Task not found in this homework")

        # Check attempts
        attempts_used = await self.homework_repo.get_attempts_count(
            homework_student_id=hw_student.id,
            task_id=task_id
        )

        if attempts_used >= task.max_attempts:
            raise HomeworkServiceError(
                f"Maximum attempts ({task.max_attempts}) reached"
            )

        # Calculate late status
        is_late = False
        late_penalty = 0.0
        now = datetime.utcnow()

        if now > homework.due_date:
            is_late, late_penalty = await self.calculate_late_penalty(
                homework=homework,
                submission_time=now
            )

        # Create submission
        submission = await self.homework_repo.create_submission(
            homework_student_id=hw_student.id,
            task_id=task_id,
            attempt_number=attempts_used + 1,
            is_late=is_late,
            late_penalty=late_penalty
        )

        # Update student status if first task
        if hw_student.status == HomeworkStudentStatus.ASSIGNED:
            hw_student.status = HomeworkStudentStatus.IN_PROGRESS
            hw_student.started_at = now
            await self.db.flush()

        return submission

    async def submit_answer(
        self,
        submission_id: int,
        question_id: int,
        answer_text: str,
        selected_options: Optional[List[str]] = None,
        student_id: int = None
    ) -> SubmissionResult:
        """
        Submit an answer for a question.

        Args:
            submission_id: Submission ID
            question_id: Question ID
            answer_text: Answer text
            selected_options: Selected option IDs (for choice questions)
            student_id: Student ID (for AI grading)

        Returns:
            SubmissionResult with score and feedback
        """
        # Verify submission exists and is in progress
        submission = await self.homework_repo.get_submission_by_id(submission_id)
        if not submission:
            raise HomeworkServiceError("Submission not found")

        if submission.status != TaskSubmissionStatus.IN_PROGRESS:
            raise HomeworkServiceError("Submission is not in progress")

        # Get question
        question = await self.db.get(HomeworkTaskQuestion, question_id)
        if not question or question.task_id != submission.task_id:
            raise HomeworkServiceError("Question not found in this task")

        # Save answer
        answer = await self.homework_repo.save_answer(
            submission_id=submission_id,
            question_id=question_id,
            answer_text=answer_text,
            selected_options=selected_options
        )

        # Auto-grade based on question type
        result = await self._grade_answer(
            answer=answer,
            question=question,
            submission=submission,
            student_id=student_id
        )

        await self.db.flush()
        return result

    async def complete_submission(
        self,
        submission_id: int,
        student_id: int
    ) -> TaskSubmissionResult:
        """
        Complete a task submission.

        Args:
            submission_id: Submission ID
            student_id: Student ID

        Returns:
            TaskSubmissionResult with total score

        Raises:
            HomeworkServiceError: If submission not found or not owned
        """
        submission = await self.homework_repo.get_submission_by_id(submission_id)
        if not submission:
            raise HomeworkServiceError("Submission not found")

        # Verify ownership
        hw_student = submission.homework_student
        if hw_student.student_id != student_id:
            raise HomeworkServiceError("Not authorized")

        if submission.status != TaskSubmissionStatus.IN_PROGRESS:
            raise HomeworkServiceError("Submission is not in progress")

        # Calculate total score
        total_score = 0.0
        max_score = 0.0
        needs_review = False

        for answer in submission.answers:
            total_score += answer.score or 0.0
            max_score += answer.max_score or 0.0
            if answer.flagged_for_review:
                needs_review = True

        # Apply late penalty
        original_score = total_score
        if submission.is_late and submission.late_penalty_applied > 0:
            penalty_factor = 1 - (submission.late_penalty_applied / 100)
            total_score = total_score * penalty_factor
            submission.original_score = original_score

        submission.score = total_score
        submission.max_score = max_score
        submission.status = (
            TaskSubmissionStatus.NEEDS_REVIEW if needs_review
            else TaskSubmissionStatus.GRADED
        )
        submission.completed_at = datetime.utcnow()

        await self.db.flush()

        return TaskSubmissionResult(
            submission_id=submission_id,
            score=total_score,
            max_score=max_score,
            is_late=submission.is_late,
            late_penalty=submission.late_penalty_applied,
            original_score=original_score if submission.is_late else None,
            needs_review=needs_review,
            attempt_number=submission.attempt_number
        )

    # =========================================================================
    # Late Submission
    # =========================================================================

    async def calculate_late_penalty(
        self,
        homework: Homework,
        submission_time: datetime
    ) -> Tuple[bool, float]:
        """
        Calculate late submission penalty.

        Args:
            homework: Homework object
            submission_time: Time of submission

        Returns:
            Tuple of (is_late, penalty_percent)

        Raises:
            HomeworkServiceError: If submission too late
        """
        if submission_time <= homework.due_date:
            return False, 0.0

        if not homework.late_submission_allowed:
            raise HomeworkServiceError("Late submission not allowed")

        # Grace period
        grace_deadline = homework.due_date + timedelta(
            hours=homework.grace_period_hours
        )
        if submission_time <= grace_deadline:
            return False, 0.0

        # Calculate days late
        time_late = submission_time - grace_deadline
        days_late = time_late.days + 1  # Partial day counts as full

        if days_late > homework.max_late_days:
            raise HomeworkServiceError(
                f"Submission too late (> {homework.max_late_days} days)"
            )

        # Calculate penalty
        penalty = min(days_late * homework.late_penalty_per_day, 100)
        return True, penalty

    # =========================================================================
    # Grading
    # =========================================================================

    async def _grade_answer(
        self,
        answer: StudentTaskAnswer,
        question: HomeworkTaskQuestion,
        submission: StudentTaskSubmission,
        student_id: int
    ) -> SubmissionResult:
        """
        Grade an answer based on question type.

        Args:
            answer: Student's answer
            question: Question being answered
            submission: Parent submission
            student_id: Student ID

        Returns:
            SubmissionResult
        """
        q_type = question.question_type

        if q_type in ("single_choice", "multiple_choice", "true_false"):
            # Auto-grade choice questions
            is_correct = self._check_choice_answer(
                question=question,
                selected=answer.selected_options or []
            )
            answer.is_correct = is_correct
            answer.score = question.points if is_correct else 0.0
            answer.max_score = question.points

        elif q_type == "short_answer":
            # Fuzzy matching for short answers
            is_correct = self._check_short_answer(
                question=question,
                answer_text=answer.answer_text
            )
            answer.is_correct = is_correct
            answer.score = question.points if is_correct else 0.0
            answer.max_score = question.points

        elif q_type == "open_ended":
            # AI or manual grading
            answer.max_score = question.points

            hw_student = submission.homework_student
            homework = hw_student.homework

            if homework.ai_check_enabled and self.ai_service:
                # AI grading
                ai_result = await self.ai_service.grade_answer(
                    question=question,
                    answer_text=answer.answer_text,
                    student_id=student_id
                )
                answer.ai_score = ai_result.score
                answer.ai_confidence = ai_result.confidence
                answer.ai_feedback = ai_result.feedback
                answer.ai_rubric_scores = ai_result.rubric_scores
                answer.flagged_for_review = ai_result.confidence < 0.7
                answer.score = ai_result.score * question.points
            else:
                # Mark for manual review
                answer.flagged_for_review = True
                answer.score = 0.0

        return SubmissionResult(
            submission_id=submission.id,
            is_correct=answer.is_correct,
            score=answer.score or 0.0,
            max_score=answer.max_score or 0.0,
            ai_feedback=answer.ai_feedback,
            ai_confidence=answer.ai_confidence,
            needs_review=answer.flagged_for_review or False
        )

    def _check_choice_answer(
        self,
        question: HomeworkTaskQuestion,
        selected: List[str]
    ) -> bool:
        """Check if selected options are correct."""
        if not question.options:
            return False

        correct_ids = {
            str(opt.get("id")) for opt in question.options
            if opt.get("is_correct")
        }
        selected_set = {str(s) for s in selected}
        return selected_set == correct_ids

    def _check_short_answer(
        self,
        question: HomeworkTaskQuestion,
        answer_text: str
    ) -> bool:
        """Check short answer (case-insensitive, trimmed)."""
        if not question.correct_answer:
            return False

        normalized = answer_text.strip().lower()
        correct = question.correct_answer.strip().lower()
        return normalized == correct

    # =========================================================================
    # Teacher Review
    # =========================================================================

    async def get_answers_for_review(
        self,
        school_id: int,
        homework_id: Optional[int] = None,
        limit: int = 50
    ) -> List[StudentTaskAnswer]:
        """
        Get answers needing teacher review.

        Args:
            school_id: School ID
            homework_id: Optional filter by homework
            limit: Max results

        Returns:
            List of answers flagged for review
        """
        return await self.homework_repo.get_answers_for_review(
            school_id=school_id,
            homework_id=homework_id,
            limit=limit
        )

    async def review_answer(
        self,
        answer_id: int,
        teacher_id: int,
        score: float,
        feedback: Optional[str] = None
    ) -> StudentTaskAnswer:
        """
        Teacher reviews and grades an answer.

        Args:
            answer_id: Answer ID
            teacher_id: Teacher ID
            score: Score (0.0 to 1.0)
            feedback: Optional feedback

        Returns:
            Updated answer
        """
        return await self.homework_repo.teacher_review_answer(
            answer_id=answer_id,
            teacher_id=teacher_id,
            score=score,
            feedback=feedback
        )

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_homework_stats(
        self,
        homework_id: int,
        school_id: int
    ) -> dict:
        """
        Get homework statistics.

        Args:
            homework_id: Homework ID
            school_id: School ID

        Returns:
            Dict with stats (total_students, submitted_count, etc.)
        """
        return await self.homework_repo.get_homework_stats(
            homework_id=homework_id,
            school_id=school_id
        )
