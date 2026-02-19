"""
Unit tests for Homework PublishingService.

Tests:
- Task content validation per task type
- Status transition enforcement (DRAFT→PUBLISHED→CLOSED)
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.services.homework.publishing_service import PublishingService, PublishingServiceError
from app.models.homework import HomeworkTaskType, HomeworkStatus


# =============================================================================
# Task Content Validation
# =============================================================================

class TestTaskContentValidation:
    """Tests for PublishingService._validate_tasks_content."""

    def setup_method(self):
        # Create instance without __init__ to test pure validation method
        self.service = PublishingService.__new__(PublishingService)

    def _make_task(self, task_type, questions=None, paragraph_id=None, instructions=None, task_id=1):
        """Create a mock task for validation."""
        task = MagicMock()
        task.id = task_id
        task.task_type = task_type
        task.questions = questions
        task.paragraph_id = paragraph_id
        task.instructions = instructions
        return task

    # --- QUIZ ---

    def test_quiz_with_questions_valid(self):
        task = self._make_task(HomeworkTaskType.QUIZ, questions=[MagicMock()])
        errors = self.service._validate_tasks_content([task])
        assert errors == []

    def test_quiz_without_questions_invalid(self):
        task = self._make_task(HomeworkTaskType.QUIZ, questions=[])
        errors = self.service._validate_tasks_content([task])
        assert len(errors) == 1
        assert "QUIZ" in errors[0]

    def test_quiz_with_none_questions_invalid(self):
        task = self._make_task(HomeworkTaskType.QUIZ, questions=None)
        errors = self.service._validate_tasks_content([task])
        assert len(errors) == 1

    # --- OPEN_QUESTION ---

    def test_open_question_with_questions_valid(self):
        task = self._make_task(HomeworkTaskType.OPEN_QUESTION, questions=[MagicMock()])
        errors = self.service._validate_tasks_content([task])
        assert errors == []

    def test_open_question_without_questions_invalid(self):
        task = self._make_task(HomeworkTaskType.OPEN_QUESTION, questions=[])
        errors = self.service._validate_tasks_content([task])
        assert len(errors) == 1

    # --- PRACTICE ---

    def test_practice_without_questions_invalid(self):
        task = self._make_task(HomeworkTaskType.PRACTICE, questions=[])
        errors = self.service._validate_tasks_content([task])
        assert len(errors) == 1

    # --- CODE ---

    def test_code_without_questions_invalid(self):
        task = self._make_task(HomeworkTaskType.CODE, questions=[])
        errors = self.service._validate_tasks_content([task])
        assert len(errors) == 1

    # --- READ ---

    def test_read_with_paragraph_valid(self):
        """READ with paragraph_id (no questions) → valid."""
        task = self._make_task(HomeworkTaskType.READ, paragraph_id=1, questions=[])
        errors = self.service._validate_tasks_content([task])
        assert errors == []

    def test_read_with_questions_valid(self):
        """READ with questions (no paragraph_id) → valid."""
        task = self._make_task(
            HomeworkTaskType.READ, paragraph_id=None, questions=[MagicMock()]
        )
        errors = self.service._validate_tasks_content([task])
        assert errors == []

    def test_read_without_paragraph_or_questions_invalid(self):
        """READ with neither paragraph nor questions → error."""
        task = self._make_task(HomeworkTaskType.READ, paragraph_id=None, questions=[])
        errors = self.service._validate_tasks_content([task])
        assert len(errors) == 1
        assert "paragraph_id" in errors[0]

    # --- ESSAY ---

    def test_essay_with_questions_valid(self):
        task = self._make_task(HomeworkTaskType.ESSAY, questions=[MagicMock()], instructions=None)
        errors = self.service._validate_tasks_content([task])
        assert errors == []

    def test_essay_with_instructions_valid(self):
        """ESSAY with instructions (no questions) → valid."""
        task = self._make_task(
            HomeworkTaskType.ESSAY, questions=[], instructions="Write an essay about..."
        )
        errors = self.service._validate_tasks_content([task])
        assert errors == []

    def test_essay_without_questions_or_instructions_invalid(self):
        """ESSAY with neither → error."""
        task = self._make_task(HomeworkTaskType.ESSAY, questions=[], instructions=None)
        errors = self.service._validate_tasks_content([task])
        assert len(errors) == 1
        assert "ESSAY" in errors[0]

    # --- Multiple tasks ---

    def test_multiple_invalid_tasks_returns_multiple_errors(self):
        tasks = [
            self._make_task(HomeworkTaskType.QUIZ, questions=[], task_id=1),
            self._make_task(HomeworkTaskType.ESSAY, questions=[], instructions=None, task_id=2),
        ]
        errors = self.service._validate_tasks_content(tasks)
        assert len(errors) == 2

    def test_empty_task_list_no_errors(self):
        """Empty tasks list → no errors (publish_homework checks separately)."""
        errors = self.service._validate_tasks_content([])
        assert errors == []

    def test_mixed_valid_and_invalid(self):
        """One valid + one invalid → only 1 error."""
        tasks = [
            self._make_task(HomeworkTaskType.QUIZ, questions=[MagicMock()], task_id=1),  # valid
            self._make_task(HomeworkTaskType.CODE, questions=[], task_id=2),  # invalid
        ]
        errors = self.service._validate_tasks_content(tasks)
        assert len(errors) == 1
        assert "CODE" in errors[0]


# =============================================================================
# Status Transition Tests
# =============================================================================

class TestStatusTransitions:
    """Tests for publish/close status enforcement."""

    @pytest.mark.asyncio
    async def test_publish_requires_draft_status(self):
        """Publish non-draft homework → error."""
        service = PublishingService.__new__(PublishingService)
        service.repo = MagicMock()
        service.class_repo = MagicMock()

        # Mock homework in PUBLISHED status
        hw = MagicMock()
        hw.status = HomeworkStatus.PUBLISHED
        hw.tasks = [MagicMock()]
        service.repo.get_by_id = AsyncMock(return_value=hw)

        with pytest.raises(PublishingServiceError, match="Can only publish draft homework"):
            await service.publish_homework(1, 1)

    @pytest.mark.asyncio
    async def test_publish_requires_at_least_one_task(self):
        """Publish homework with no tasks → error."""
        service = PublishingService.__new__(PublishingService)
        service.repo = MagicMock()
        service.class_repo = MagicMock()

        hw = MagicMock()
        hw.status = HomeworkStatus.DRAFT
        hw.tasks = []
        service.repo.get_by_id = AsyncMock(return_value=hw)

        with pytest.raises(PublishingServiceError, match="at least one task"):
            await service.publish_homework(1, 1)

    @pytest.mark.asyncio
    async def test_publish_not_found_raises(self):
        """Publish nonexistent homework → error."""
        service = PublishingService.__new__(PublishingService)
        service.repo = MagicMock()
        service.class_repo = MagicMock()
        service.repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(PublishingServiceError, match="not found"):
            await service.publish_homework(1, 1)

    @pytest.mark.asyncio
    async def test_close_requires_published_status(self):
        """Close non-published homework → error."""
        service = PublishingService.__new__(PublishingService)
        service.repo = MagicMock()
        service.class_repo = MagicMock()

        hw = MagicMock()
        hw.status = HomeworkStatus.DRAFT
        service.repo.get_by_id = AsyncMock(return_value=hw)

        with pytest.raises(PublishingServiceError, match="Can only close published homework"):
            await service.close_homework(1, 1)

    @pytest.mark.asyncio
    async def test_close_already_closed_fails(self):
        """Close already-closed homework → error."""
        service = PublishingService.__new__(PublishingService)
        service.repo = MagicMock()
        service.class_repo = MagicMock()

        hw = MagicMock()
        hw.status = HomeworkStatus.CLOSED
        service.repo.get_by_id = AsyncMock(return_value=hw)

        with pytest.raises(PublishingServiceError, match="Can only close published homework"):
            await service.close_homework(1, 1)

    @pytest.mark.asyncio
    async def test_publish_no_students_raises(self):
        """Publish homework but class has no students → error."""
        service = PublishingService.__new__(PublishingService)
        service.repo = MagicMock()
        service.class_repo = MagicMock()

        hw = MagicMock()
        hw.status = HomeworkStatus.DRAFT
        hw.class_id = 1
        hw.tasks = [MagicMock(task_type=HomeworkTaskType.READ, paragraph_id=1, questions=[])]
        service.repo.get_by_id = AsyncMock(return_value=hw)
        service.class_repo.get_students = AsyncMock(return_value=[])

        with pytest.raises(PublishingServiceError, match="No students"):
            await service.publish_homework(1, 1)
