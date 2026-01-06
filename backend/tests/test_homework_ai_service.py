"""
Unit tests for HomeworkAIService.

Tests:
- Question generation with mocked LLM
- Answer grading with mocked LLM
- JSON parsing (valid, invalid, edge cases)
- Question validation logic
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.homework.ai import (
    HomeworkAIService,
    HomeworkAIServiceError,
    AIGradingResult,
)
from app.services.llm_service import LLMResponse, LLMServiceError
from app.schemas.homework import GenerationParams, QuestionType, BloomLevel
from app.models.homework import HomeworkTaskQuestion


# =============================================================================
# Mock LLM Service
# =============================================================================

@dataclass
class MockLLMResponse:
    """Mock LLM response for testing."""
    content: str
    model: str = "mock-model"
    tokens_used: Optional[int] = 100
    finish_reason: str = "stop"


class MockLLMService:
    """
    Mock LLM Service for testing without real API calls.

    Usage:
        mock_llm = MockLLMService(response_content="...")
        service = HomeworkAIService(db, llm_service=mock_llm)
    """

    def __init__(
        self,
        response_content: str = "",
        should_fail: bool = False,
        error_message: str = "Mock LLM error"
    ):
        self.response_content = response_content
        self.should_fail = should_fail
        self.error_message = error_message
        self.call_count = 0
        self.last_messages = None
        self.last_temperature = None
        self.last_max_tokens = None

    async def generate(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        model: Optional[str] = None,
        fallback_on_error: bool = True
    ) -> MockLLMResponse:
        """Mock generate method."""
        self.call_count += 1
        self.last_messages = messages
        self.last_temperature = temperature
        self.last_max_tokens = max_tokens

        if self.should_fail:
            raise LLMServiceError(self.error_message)

        return MockLLMResponse(content=self.response_content)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_generation_params() -> GenerationParams:
    """Sample generation parameters for tests."""
    return GenerationParams(
        questions_count=3,
        question_types=[QuestionType.SINGLE_CHOICE, QuestionType.OPEN_ENDED],
        bloom_levels=[BloomLevel.UNDERSTAND, BloomLevel.APPLY],
        include_explanation=True,
        language="ru"
    )


@pytest.fixture
def valid_questions_json() -> str:
    """Valid JSON response with questions."""
    return '''[
        {
            "question_text": "Что такое фотосинтез?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "text": "Процесс дыхания", "is_correct": false},
                {"id": "b", "text": "Процесс питания растений", "is_correct": true},
                {"id": "c", "text": "Процесс роста", "is_correct": false},
                {"id": "d", "text": "Процесс размножения", "is_correct": false}
            ],
            "correct_answer": null,
            "bloom_level": "understand",
            "points": 1
        },
        {
            "question_text": "Объясните роль хлорофилла в фотосинтезе",
            "question_type": "open_ended",
            "options": null,
            "correct_answer": null,
            "bloom_level": "analyze",
            "points": 3,
            "grading_rubric": {
                "criteria": [
                    {"name": "Полнота", "max_score": 10, "description": "Полнота ответа"}
                ],
                "max_total_score": 10
            }
        }
    ]'''


@pytest.fixture
def valid_grading_json() -> str:
    """Valid JSON response for grading."""
    return '''{
        "score": 0.85,
        "confidence": 0.9,
        "feedback": "Отличный ответ! Ты правильно объяснил основные концепции.",
        "rubric_scores": [
            {"name": "Полнота", "score": 8, "max_score": 10, "comment": "Хорошо раскрыта тема"}
        ],
        "strengths": ["Правильное понимание концепции", "Хорошие примеры"],
        "improvements": ["Можно добавить больше деталей"]
    }'''


# =============================================================================
# Tests: JSON Parsing - Questions
# =============================================================================

class TestParseQuestionsResponse:
    """Tests for _parse_questions_response method."""

    def test_parse_valid_json(self, valid_questions_json: str):
        """Test parsing valid JSON array."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        questions = service._parse_questions_response(valid_questions_json)

        assert len(questions) == 2
        assert questions[0]["question_text"] == "Что такое фотосинтез?"
        assert questions[0]["question_type"] == "single_choice"
        assert len(questions[0]["options"]) == 4
        assert questions[1]["question_type"] == "open_ended"

    def test_parse_json_with_markdown_code_block(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        response = '''```json
[
    {
        "question_text": "Тестовый вопрос?",
        "question_type": "single_choice",
        "options": [
            {"id": "a", "text": "Вариант А", "is_correct": true},
            {"id": "b", "text": "Вариант Б", "is_correct": false}
        ],
        "bloom_level": "remember",
        "points": 1
    }
]
```'''

        questions = service._parse_questions_response(response)

        assert len(questions) == 1
        assert questions[0]["question_text"] == "Тестовый вопрос?"

    def test_parse_json_with_text_before_after(self):
        """Test parsing JSON with extra text before/after."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        response = '''Вот вопросы:
[
    {
        "question_text": "Вопрос 1?",
        "question_type": "true_false",
        "options": [
            {"id": "a", "text": "True", "is_correct": true},
            {"id": "b", "text": "False", "is_correct": false}
        ],
        "bloom_level": "understand",
        "points": 1
    }
]
Надеюсь, они подходят!'''

        questions = service._parse_questions_response(response)

        assert len(questions) == 1
        assert questions[0]["question_type"] == "true_false"

    def test_parse_invalid_json_raises_error(self):
        """Test that invalid JSON raises ValueError."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        with pytest.raises(ValueError, match="Could not find JSON array"):
            service._parse_questions_response("This is not JSON at all")

    def test_parse_empty_array_raises_error(self):
        """Test that empty array raises ValueError."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        with pytest.raises(ValueError, match="No valid questions"):
            service._parse_questions_response("[]")

    def test_parse_object_instead_of_array_raises_error(self):
        """Test that JSON object (not array) raises ValueError."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        with pytest.raises(ValueError, match="not a JSON array"):
            service._parse_questions_response('{"question": "test"}')

    def test_parse_skips_invalid_questions(self):
        """Test that invalid questions are skipped with warning."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        # First question is invalid (no question_text), second is valid
        response = '''[
            {"question_type": "single_choice"},
            {
                "question_text": "Valid question?",
                "question_type": "single_choice",
                "options": [
                    {"id": "a", "text": "A", "is_correct": true},
                    {"id": "b", "text": "B", "is_correct": false}
                ],
                "bloom_level": "understand",
                "points": 1
            }
        ]'''

        questions = service._parse_questions_response(response)

        assert len(questions) == 1
        assert questions[0]["question_text"] == "Valid question?"


# =============================================================================
# Tests: JSON Parsing - Grading
# =============================================================================

class TestParseGradingResponse:
    """Tests for _parse_grading_response method."""

    def test_parse_valid_grading(self, valid_grading_json: str):
        """Test parsing valid grading JSON."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        result = service._parse_grading_response(valid_grading_json)

        assert isinstance(result, AIGradingResult)
        assert result.score == 0.85
        assert result.confidence == 0.9
        assert "Отличный ответ" in result.feedback
        assert len(result.strengths) == 2
        assert len(result.improvements) == 1

    def test_parse_grading_with_code_block(self):
        """Test parsing grading wrapped in code block."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        response = '''```json
{
    "score": 0.5,
    "confidence": 0.7,
    "feedback": "Средний ответ"
}
```'''

        result = service._parse_grading_response(response)

        assert result.score == 0.5
        assert result.confidence == 0.7

    def test_parse_grading_clamps_score(self):
        """Test that score is clamped to 0-1 range."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        # Score > 1
        response1 = '{"score": 1.5, "confidence": 0.8, "feedback": "test"}'
        result1 = service._parse_grading_response(response1)
        assert result1.score == 1.0

        # Score < 0
        response2 = '{"score": -0.5, "confidence": 0.8, "feedback": "test"}'
        result2 = service._parse_grading_response(response2)
        assert result2.score == 0.0

    def test_parse_grading_clamps_confidence(self):
        """Test that confidence is clamped to 0-1 range."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        response = '{"score": 0.5, "confidence": 2.0, "feedback": "test"}'
        result = service._parse_grading_response(response)

        assert result.confidence == 1.0

    def test_parse_grading_with_missing_optional_fields(self):
        """Test parsing with missing optional fields."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        response = '{"score": 0.7, "confidence": 0.8}'
        result = service._parse_grading_response(response)

        assert result.score == 0.7
        assert result.confidence == 0.8
        assert result.feedback == ""
        assert result.strengths == []
        assert result.improvements == []

    def test_parse_grading_invalid_json_raises(self):
        """Test that invalid JSON raises ValueError."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        with pytest.raises(ValueError, match="Could not find JSON"):
            service._parse_grading_response("Not valid JSON")


# =============================================================================
# Tests: Question Validation
# =============================================================================

class TestValidateQuestion:
    """Tests for _validate_question method."""

    def test_validate_valid_single_choice(self):
        """Test validation of valid single choice question."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        question = {
            "question_text": "Test question?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "text": "Option A", "is_correct": True},
                {"id": "b", "text": "Option B", "is_correct": False}
            ],
            "bloom_level": "understand",
            "points": 2
        }

        validated = service._validate_question(question, 0)

        assert validated["question_text"] == "Test question?"
        assert validated["question_type"] == "single_choice"
        assert validated["points"] == 2

    def test_validate_missing_question_text_raises(self):
        """Test that missing question_text raises ValueError."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        question = {
            "question_type": "single_choice",
            "options": [{"id": "a", "text": "A", "is_correct": True}]
        }

        with pytest.raises(ValueError, match="missing question_text"):
            service._validate_question(question, 0)

    def test_validate_empty_question_text_raises(self):
        """Test that empty question_text raises ValueError."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        question = {
            "question_text": "",
            "question_type": "single_choice"
        }

        with pytest.raises(ValueError, match="missing question_text"):
            service._validate_question(question, 0)

    def test_validate_choice_without_options_raises(self):
        """Test that choice question without options raises ValueError."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        question = {
            "question_text": "Test?",
            "question_type": "single_choice",
            "options": []
        }

        with pytest.raises(ValueError, match="at least 2 options"):
            service._validate_question(question, 0)

    def test_validate_adds_correct_option_if_missing(self):
        """Test that at least one correct option is ensured."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        question = {
            "question_text": "Test?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "text": "A", "is_correct": False},
                {"id": "b", "text": "B", "is_correct": False}
            ]
        }

        validated = service._validate_question(question, 0)

        # First option should be marked as correct
        assert validated["options"][0]["is_correct"] is True

    def test_validate_invalid_question_type_defaults_to_single_choice(self):
        """Test that invalid question type defaults to single_choice."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        question = {
            "question_text": "Test?",
            "question_type": "invalid_type",
            "options": [
                {"id": "a", "text": "A", "is_correct": True},
                {"id": "b", "text": "B", "is_correct": False}
            ]
        }

        validated = service._validate_question(question, 0)

        assert validated["question_type"] == "single_choice"

    def test_validate_invalid_bloom_level_defaults_to_understand(self):
        """Test that invalid bloom level defaults to understand."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        question = {
            "question_text": "Test?",
            "question_type": "open_ended",
            "bloom_level": "invalid_bloom"
        }

        validated = service._validate_question(question, 0)

        assert validated["bloom_level"] == "understand"

    def test_validate_clamps_points(self):
        """Test that points are clamped to 1-10 range."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        # Points too high
        q1 = {
            "question_text": "Test?",
            "question_type": "open_ended",
            "points": 100
        }
        validated1 = service._validate_question(q1, 0)
        assert validated1["points"] == 10

        # Points too low
        q2 = {
            "question_text": "Test?",
            "question_type": "open_ended",
            "points": 0
        }
        validated2 = service._validate_question(q2, 0)
        assert validated2["points"] == 1

    def test_validate_strips_whitespace(self):
        """Test that question_text whitespace is stripped."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        question = {
            "question_text": "  Test question?  \n",
            "question_type": "open_ended"
        }

        validated = service._validate_question(question, 0)

        assert validated["question_text"] == "Test question?"


# =============================================================================
# Tests: Question Generation with Mock LLM
# =============================================================================

class TestGenerateQuestions:
    """Tests for generate_questions method with mocked LLM."""

    @pytest.mark.asyncio
    async def test_generate_questions_success(
        self,
        db_session: AsyncSession,
        valid_questions_json: str,
        sample_generation_params: GenerationParams,
        paragraph1
    ):
        """Test successful question generation."""
        mock_llm = MockLLMService(response_content=valid_questions_json)
        service = HomeworkAIService(db_session, llm_service=mock_llm)

        questions = await service.generate_questions(
            paragraph_id=paragraph1.id,
            params=sample_generation_params,
            task_id=1
        )

        assert len(questions) == 2
        assert mock_llm.call_count == 1
        assert mock_llm.last_temperature == 0.7

    @pytest.mark.asyncio
    async def test_generate_questions_paragraph_not_found(
        self,
        db_session: AsyncSession,
        sample_generation_params: GenerationParams
    ):
        """Test error when paragraph not found."""
        mock_llm = MockLLMService()
        service = HomeworkAIService(db_session, llm_service=mock_llm)

        with pytest.raises(HomeworkAIServiceError, match="not found"):
            await service.generate_questions(
                paragraph_id=99999,  # Non-existent
                params=sample_generation_params,
                task_id=1
            )

    @pytest.mark.asyncio
    async def test_generate_questions_llm_failure(
        self,
        db_session: AsyncSession,
        sample_generation_params: GenerationParams,
        paragraph1
    ):
        """Test error handling when LLM fails."""
        mock_llm = MockLLMService(should_fail=True, error_message="API Error")
        service = HomeworkAIService(db_session, llm_service=mock_llm)

        with pytest.raises(HomeworkAIServiceError, match="AI generation failed"):
            await service.generate_questions(
                paragraph_id=paragraph1.id,
                params=sample_generation_params,
                task_id=1
            )

    @pytest.mark.asyncio
    async def test_generate_questions_invalid_response(
        self,
        db_session: AsyncSession,
        sample_generation_params: GenerationParams,
        paragraph1
    ):
        """Test error handling when LLM returns invalid JSON."""
        mock_llm = MockLLMService(response_content="This is not JSON")
        service = HomeworkAIService(db_session, llm_service=mock_llm)

        with pytest.raises(HomeworkAIServiceError, match="Failed to parse"):
            await service.generate_questions(
                paragraph_id=paragraph1.id,
                params=sample_generation_params,
                task_id=1
            )


# =============================================================================
# Tests: Answer Grading with Mock LLM
# =============================================================================

class TestGradeAnswer:
    """Tests for grade_answer method with mocked LLM."""

    @pytest.fixture
    def mock_question(self) -> HomeworkTaskQuestion:
        """Create mock question for testing."""
        question = MagicMock(spec=HomeworkTaskQuestion)
        question.id = 1
        question.question_text = "Объясните фотосинтез"
        question.grading_rubric = {
            "criteria": [
                {"name": "Полнота", "max_score": 10, "description": "..."}
            ],
            "max_total_score": 10
        }
        return question

    @pytest.mark.asyncio
    async def test_grade_answer_success(
        self,
        db_session: AsyncSession,
        valid_grading_json: str,
        mock_question: HomeworkTaskQuestion
    ):
        """Test successful answer grading."""
        mock_llm = MockLLMService(response_content=valid_grading_json)
        service = HomeworkAIService(db_session, llm_service=mock_llm)

        result = await service.grade_answer(
            question=mock_question,
            answer_text="Фотосинтез - это процесс...",
            student_id=1
        )

        assert isinstance(result, AIGradingResult)
        assert result.score == 0.85
        assert result.confidence == 0.9
        assert mock_llm.call_count == 1
        assert mock_llm.last_temperature == 0.3  # Lower for grading

    @pytest.mark.asyncio
    async def test_grade_answer_llm_failure_returns_uncertain(
        self,
        db_session: AsyncSession,
        mock_question: HomeworkTaskQuestion
    ):
        """Test that LLM failure returns uncertain result."""
        mock_llm = MockLLMService(should_fail=True)
        service = HomeworkAIService(db_session, llm_service=mock_llm)

        result = await service.grade_answer(
            question=mock_question,
            answer_text="Some answer",
            student_id=1
        )

        # Should return uncertain result, not raise
        assert result.score == 0.5
        assert result.confidence == 0.0
        assert "Требуется проверка учителем" in result.feedback

    @pytest.mark.asyncio
    async def test_grade_answer_invalid_response_returns_uncertain(
        self,
        db_session: AsyncSession,
        mock_question: HomeworkTaskQuestion
    ):
        """Test that invalid LLM response returns uncertain result."""
        mock_llm = MockLLMService(response_content="Invalid JSON response")
        service = HomeworkAIService(db_session, llm_service=mock_llm)

        result = await service.grade_answer(
            question=mock_question,
            answer_text="Some answer",
            student_id=1
        )

        assert result.confidence == 0.0
        assert "Ошибка обработки" in result.feedback

    @pytest.mark.asyncio
    async def test_grade_answer_without_rubric(
        self,
        db_session: AsyncSession,
        valid_grading_json: str
    ):
        """Test grading question without rubric."""
        mock_question = MagicMock(spec=HomeworkTaskQuestion)
        mock_question.id = 1
        mock_question.question_text = "Simple question?"
        mock_question.grading_rubric = None

        mock_llm = MockLLMService(response_content=valid_grading_json)
        service = HomeworkAIService(db_session, llm_service=mock_llm)

        result = await service.grade_answer(
            question=mock_question,
            answer_text="Answer",
            student_id=1
        )

        assert result.score == 0.85


# =============================================================================
# Tests: Personalization
# =============================================================================

class TestPersonalizeDifficulty:
    """Tests for personalize_difficulty method."""

    @pytest.mark.asyncio
    async def test_personalize_for_mastered_student(
        self,
        db_session: AsyncSession,
        sample_generation_params: GenerationParams
    ):
        """Test personalization for student who mastered the topic."""
        service = HomeworkAIService(db_session)

        # Mock the mastery service response
        with patch.object(service, 'db') as mock_db:
            # Create mock mastery with "mastered" status
            from app.services.mastery_service import MasteryService

            with patch('app.services.homework_ai_service.MasteryService') as MockMasteryService:
                mock_mastery = MagicMock()
                mock_mastery.status = "mastered"

                mock_repo = MagicMock()
                mock_repo.get_by_student_paragraph = AsyncMock(return_value=mock_mastery)
                MockMasteryService.return_value.paragraph_repo = mock_repo

                result = await service.personalize_difficulty(
                    student_id=1,
                    paragraph_id=1,
                    base_params=sample_generation_params
                )

                # Should have harder bloom levels
                assert BloomLevel.ANALYZE in result.bloom_levels
                assert BloomLevel.EVALUATE in result.bloom_levels
                # Should have fewer questions
                assert result.questions_count <= sample_generation_params.questions_count

    @pytest.mark.asyncio
    async def test_personalize_for_struggling_student(
        self,
        db_session: AsyncSession,
        sample_generation_params: GenerationParams
    ):
        """Test personalization for struggling student."""
        service = HomeworkAIService(db_session)

        with patch('app.services.homework_ai_service.MasteryService') as MockMasteryService:
            mock_mastery = MagicMock()
            mock_mastery.status = "struggling"

            mock_repo = MagicMock()
            mock_repo.get_by_student_paragraph = AsyncMock(return_value=mock_mastery)
            MockMasteryService.return_value.paragraph_repo = mock_repo

            result = await service.personalize_difficulty(
                student_id=1,
                paragraph_id=1,
                base_params=sample_generation_params
            )

            # Should have easier bloom levels
            assert BloomLevel.REMEMBER in result.bloom_levels
            assert BloomLevel.UNDERSTAND in result.bloom_levels
            # Should have more questions
            assert result.questions_count >= sample_generation_params.questions_count


# =============================================================================
# Tests: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_parse_unicode_content(self):
        """Test parsing questions with unicode characters."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        response = '''[
            {
                "question_text": "Қазақ тілінде сұрақ?",
                "question_type": "single_choice",
                "options": [
                    {"id": "a", "text": "Иә", "is_correct": true},
                    {"id": "b", "text": "Жоқ", "is_correct": false}
                ],
                "bloom_level": "remember",
                "points": 1
            }
        ]'''

        questions = service._parse_questions_response(response)

        assert len(questions) == 1
        assert "Қазақ" in questions[0]["question_text"]

    def test_parse_very_long_content(self):
        """Test parsing response with very long content."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        long_text = "A" * 5000
        response = f'''[
            {{
                "question_text": "{long_text}?",
                "question_type": "open_ended",
                "bloom_level": "understand",
                "points": 1
            }}
        ]'''

        questions = service._parse_questions_response(response)

        assert len(questions) == 1
        assert len(questions[0]["question_text"]) > 4000

    def test_parse_special_characters_in_json(self):
        """Test parsing JSON with special characters."""
        service = HomeworkAIService.__new__(HomeworkAIService)

        response = '''[
            {
                "question_text": "What is 2 + 2? \\n Answer: 4",
                "question_type": "single_choice",
                "options": [
                    {"id": "a", "text": "3 < 4", "is_correct": false},
                    {"id": "b", "text": "4 == 4", "is_correct": true}
                ],
                "bloom_level": "remember",
                "points": 1
            }
        ]'''

        questions = service._parse_questions_response(response)

        assert len(questions) == 1
