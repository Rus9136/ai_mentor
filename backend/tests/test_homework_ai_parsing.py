"""
Standalone unit tests for HomeworkAIService parsing methods.

These tests don't require database or full app initialization.
They test only the JSON parsing logic.
"""
import pytest
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


# =============================================================================
# Inline implementations for standalone testing
# =============================================================================

@dataclass
class AIGradingResult:
    """Result of AI grading."""
    score: float
    confidence: float
    feedback: str
    rubric_scores: Optional[List[Dict[str, Any]]] = None
    strengths: List[str] = None
    improvements: List[str] = None

    def __post_init__(self):
        if self.strengths is None:
            self.strengths = []
        if self.improvements is None:
            self.improvements = []


class QuestionParser:
    """
    Standalone parser for testing.
    Contains the same logic as HomeworkAIService._parse_questions_response.
    """

    @staticmethod
    def parse_questions_response(response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into question dicts."""
        import re

        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    json_lines.append(line)
            response = "\n".join(json_lines)

        # Try to parse as JSON
        try:
            questions = json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON array in response
            match = re.search(r'\[[\s\S]*\]', response)
            if match:
                questions = json.loads(match.group())
            else:
                raise ValueError("Could not find JSON array in response")

        if not isinstance(questions, list):
            raise ValueError("Response is not a JSON array")

        # Validate and normalize questions
        validated = []
        for i, q in enumerate(questions):
            try:
                validated_q = QuestionParser.validate_question(q, i)
                validated.append(validated_q)
            except ValueError:
                continue

        if not validated:
            raise ValueError("No valid questions in response")

        return validated

    @staticmethod
    def validate_question(q: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Validate and normalize a question dict."""
        # Required fields
        if "question_text" not in q or not q["question_text"]:
            raise ValueError(f"Question {index}: missing question_text")

        q_type = q.get("question_type", "single_choice")
        valid_types = [
            "single_choice", "multiple_choice", "short_answer",
            "open_ended", "true_false"
        ]
        if q_type not in valid_types:
            q_type = "single_choice"

        # Validate options for choice questions
        if q_type in ("single_choice", "multiple_choice", "true_false"):
            options = q.get("options", [])
            if not options or len(options) < 2:
                raise ValueError(
                    f"Question {index}: choice questions need at least 2 options"
                )
            # Ensure at least one correct option
            has_correct = any(opt.get("is_correct") for opt in options)
            if not has_correct:
                options[0]["is_correct"] = True

        # Normalize bloom level
        bloom = q.get("bloom_level", "understand")
        valid_blooms = [
            "remember", "understand", "apply",
            "analyze", "evaluate", "create"
        ]
        if bloom not in valid_blooms:
            bloom = "understand"

        return {
            "question_text": q["question_text"].strip(),
            "question_type": q_type,
            "options": q.get("options"),
            "correct_answer": q.get("correct_answer"),
            "bloom_level": bloom,
            "points": max(1, min(10, q.get("points") or 1)),
            "grading_rubric": q.get("grading_rubric"),
        }


class GradingParser:
    """
    Standalone parser for grading responses.
    Contains the same logic as HomeworkAIService._parse_grading_response.
    """

    @staticmethod
    def parse_grading_response(response: str) -> AIGradingResult:
        """Parse grading response from LLM."""
        import re

        response = response.strip()

        # Remove markdown code blocks
        if response.startswith("```"):
            lines = response.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    json_lines.append(line)
            response = "\n".join(json_lines)

        # Parse JSON
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                data = json.loads(match.group())
            else:
                raise ValueError("Could not find JSON in response")

        # Validate and normalize
        score = float(data.get("score", 0.5))
        score = max(0.0, min(1.0, score))

        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        return AIGradingResult(
            score=score,
            confidence=confidence,
            feedback=data.get("feedback", ""),
            rubric_scores=data.get("rubric_scores"),
            strengths=data.get("strengths", []),
            improvements=data.get("improvements", [])
        )


# =============================================================================
# Test Fixtures
# =============================================================================

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
        questions = QuestionParser.parse_questions_response(valid_questions_json)

        assert len(questions) == 2
        assert questions[0]["question_text"] == "Что такое фотосинтез?"
        assert questions[0]["question_type"] == "single_choice"
        assert len(questions[0]["options"]) == 4
        assert questions[1]["question_type"] == "open_ended"

    def test_parse_json_with_markdown_code_block(self):
        """Test parsing JSON wrapped in markdown code blocks."""
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

        questions = QuestionParser.parse_questions_response(response)

        assert len(questions) == 1
        assert questions[0]["question_text"] == "Тестовый вопрос?"

    def test_parse_json_with_text_before_after(self):
        """Test parsing JSON with extra text before/after."""
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

        questions = QuestionParser.parse_questions_response(response)

        assert len(questions) == 1
        assert questions[0]["question_type"] == "true_false"

    def test_parse_invalid_json_raises_error(self):
        """Test that invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Could not find JSON array"):
            QuestionParser.parse_questions_response("This is not JSON at all")

    def test_parse_empty_array_raises_error(self):
        """Test that empty array raises ValueError."""
        with pytest.raises(ValueError, match="No valid questions"):
            QuestionParser.parse_questions_response("[]")

    def test_parse_object_instead_of_array_raises_error(self):
        """Test that JSON object (not array) raises ValueError."""
        with pytest.raises(ValueError, match="not a JSON array"):
            QuestionParser.parse_questions_response('{"question": "test"}')

    def test_parse_skips_invalid_questions(self):
        """Test that invalid questions are skipped with warning."""
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

        questions = QuestionParser.parse_questions_response(response)

        assert len(questions) == 1
        assert questions[0]["question_text"] == "Valid question?"

    def test_parse_multiple_code_blocks(self):
        """Test parsing with multiple code block markers."""
        response = '''```json
[
    {
        "question_text": "Test question?",
        "question_type": "single_choice",
        "options": [
            {"id": "a", "text": "A", "is_correct": true},
            {"id": "b", "text": "B", "is_correct": false}
        ],
        "points": 1
    }
]
```
Some text after
```python
print("hello")
```'''

        questions = QuestionParser.parse_questions_response(response)
        assert len(questions) == 1


# =============================================================================
# Tests: JSON Parsing - Grading
# =============================================================================

class TestParseGradingResponse:
    """Tests for _parse_grading_response method."""

    def test_parse_valid_grading(self, valid_grading_json: str):
        """Test parsing valid grading JSON."""
        result = GradingParser.parse_grading_response(valid_grading_json)

        assert isinstance(result, AIGradingResult)
        assert result.score == 0.85
        assert result.confidence == 0.9
        assert "Отличный ответ" in result.feedback
        assert len(result.strengths) == 2
        assert len(result.improvements) == 1

    def test_parse_grading_with_code_block(self):
        """Test parsing grading wrapped in code block."""
        response = '''```json
{
    "score": 0.5,
    "confidence": 0.7,
    "feedback": "Средний ответ"
}
```'''

        result = GradingParser.parse_grading_response(response)

        assert result.score == 0.5
        assert result.confidence == 0.7

    def test_parse_grading_clamps_score_high(self):
        """Test that score > 1 is clamped to 1.0."""
        response = '{"score": 1.5, "confidence": 0.8, "feedback": "test"}'
        result = GradingParser.parse_grading_response(response)
        assert result.score == 1.0

    def test_parse_grading_clamps_score_low(self):
        """Test that score < 0 is clamped to 0.0."""
        response = '{"score": -0.5, "confidence": 0.8, "feedback": "test"}'
        result = GradingParser.parse_grading_response(response)
        assert result.score == 0.0

    def test_parse_grading_clamps_confidence(self):
        """Test that confidence is clamped to 0-1 range."""
        response = '{"score": 0.5, "confidence": 2.0, "feedback": "test"}'
        result = GradingParser.parse_grading_response(response)
        assert result.confidence == 1.0

    def test_parse_grading_with_missing_optional_fields(self):
        """Test parsing with missing optional fields."""
        response = '{"score": 0.7, "confidence": 0.8}'
        result = GradingParser.parse_grading_response(response)

        assert result.score == 0.7
        assert result.confidence == 0.8
        assert result.feedback == ""
        assert result.strengths == []
        assert result.improvements == []

    def test_parse_grading_invalid_json_raises(self):
        """Test that invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Could not find JSON"):
            GradingParser.parse_grading_response("Not valid JSON")

    def test_parse_grading_with_text_around_json(self):
        """Test parsing grading with text before/after JSON."""
        response = '''Here is my evaluation:
{
    "score": 0.6,
    "confidence": 0.8,
    "feedback": "Good effort"
}
Hope this helps!'''

        result = GradingParser.parse_grading_response(response)
        assert result.score == 0.6
        assert result.confidence == 0.8


# =============================================================================
# Tests: Question Validation
# =============================================================================

class TestValidateQuestion:
    """Tests for _validate_question method."""

    def test_validate_valid_single_choice(self):
        """Test validation of valid single choice question."""
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

        validated = QuestionParser.validate_question(question, 0)

        assert validated["question_text"] == "Test question?"
        assert validated["question_type"] == "single_choice"
        assert validated["points"] == 2

    def test_validate_missing_question_text_raises(self):
        """Test that missing question_text raises ValueError."""
        question = {
            "question_type": "single_choice",
            "options": [{"id": "a", "text": "A", "is_correct": True}]
        }

        with pytest.raises(ValueError, match="missing question_text"):
            QuestionParser.validate_question(question, 0)

    def test_validate_empty_question_text_raises(self):
        """Test that empty question_text raises ValueError."""
        question = {
            "question_text": "",
            "question_type": "single_choice"
        }

        with pytest.raises(ValueError, match="missing question_text"):
            QuestionParser.validate_question(question, 0)

    def test_validate_choice_without_options_raises(self):
        """Test that choice question without options raises ValueError."""
        question = {
            "question_text": "Test?",
            "question_type": "single_choice",
            "options": []
        }

        with pytest.raises(ValueError, match="at least 2 options"):
            QuestionParser.validate_question(question, 0)

    def test_validate_choice_with_one_option_raises(self):
        """Test that choice question with only 1 option raises ValueError."""
        question = {
            "question_text": "Test?",
            "question_type": "single_choice",
            "options": [{"id": "a", "text": "A", "is_correct": True}]
        }

        with pytest.raises(ValueError, match="at least 2 options"):
            QuestionParser.validate_question(question, 0)

    def test_validate_adds_correct_option_if_missing(self):
        """Test that at least one correct option is ensured."""
        question = {
            "question_text": "Test?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "text": "A", "is_correct": False},
                {"id": "b", "text": "B", "is_correct": False}
            ]
        }

        validated = QuestionParser.validate_question(question, 0)

        # First option should be marked as correct
        assert validated["options"][0]["is_correct"] is True

    def test_validate_invalid_question_type_defaults_to_single_choice(self):
        """Test that invalid question type defaults to single_choice."""
        question = {
            "question_text": "Test?",
            "question_type": "invalid_type",
            "options": [
                {"id": "a", "text": "A", "is_correct": True},
                {"id": "b", "text": "B", "is_correct": False}
            ]
        }

        validated = QuestionParser.validate_question(question, 0)

        assert validated["question_type"] == "single_choice"

    def test_validate_invalid_bloom_level_defaults_to_understand(self):
        """Test that invalid bloom level defaults to understand."""
        question = {
            "question_text": "Test?",
            "question_type": "open_ended",
            "bloom_level": "invalid_bloom"
        }

        validated = QuestionParser.validate_question(question, 0)

        assert validated["bloom_level"] == "understand"

    def test_validate_clamps_points_high(self):
        """Test that points > 10 are clamped to 10."""
        question = {
            "question_text": "Test?",
            "question_type": "open_ended",
            "points": 100
        }
        validated = QuestionParser.validate_question(question, 0)
        assert validated["points"] == 10

    def test_validate_clamps_points_low(self):
        """Test that points < 1 are clamped to 1."""
        question = {
            "question_text": "Test?",
            "question_type": "open_ended",
            "points": 0
        }
        validated = QuestionParser.validate_question(question, 0)
        assert validated["points"] == 1

    def test_validate_strips_whitespace(self):
        """Test that question_text whitespace is stripped."""
        question = {
            "question_text": "  Test question?  \n",
            "question_type": "open_ended"
        }

        validated = QuestionParser.validate_question(question, 0)

        assert validated["question_text"] == "Test question?"

    def test_validate_open_ended_without_options(self):
        """Test that open_ended questions don't need options."""
        question = {
            "question_text": "Explain something",
            "question_type": "open_ended",
            "options": None
        }

        validated = QuestionParser.validate_question(question, 0)
        assert validated["options"] is None


# =============================================================================
# Tests: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_parse_unicode_content(self):
        """Test parsing questions with unicode characters."""
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

        questions = QuestionParser.parse_questions_response(response)

        assert len(questions) == 1
        assert "Қазақ" in questions[0]["question_text"]

    def test_parse_cyrillic_content(self):
        """Test parsing questions with Cyrillic characters."""
        response = '''[
            {
                "question_text": "Что такое Москва?",
                "question_type": "single_choice",
                "options": [
                    {"id": "a", "text": "Столица", "is_correct": true},
                    {"id": "b", "text": "Деревня", "is_correct": false}
                ],
                "points": 1
            }
        ]'''

        questions = QuestionParser.parse_questions_response(response)
        assert "Москва" in questions[0]["question_text"]

    def test_parse_very_long_content(self):
        """Test parsing response with very long content."""
        long_text = "A" * 5000
        response = f'''[
            {{
                "question_text": "{long_text}?",
                "question_type": "open_ended",
                "bloom_level": "understand",
                "points": 1
            }}
        ]'''

        questions = QuestionParser.parse_questions_response(response)

        assert len(questions) == 1
        assert len(questions[0]["question_text"]) > 4000

    def test_parse_special_characters_in_json(self):
        """Test parsing JSON with special characters."""
        response = '''[
            {
                "question_text": "What is 2 + 2? Answer: 4",
                "question_type": "single_choice",
                "options": [
                    {"id": "a", "text": "3 < 4", "is_correct": false},
                    {"id": "b", "text": "4 == 4", "is_correct": true}
                ],
                "bloom_level": "remember",
                "points": 1
            }
        ]'''

        questions = QuestionParser.parse_questions_response(response)
        assert len(questions) == 1

    def test_parse_nested_quotes(self):
        """Test parsing JSON with nested quotes in text."""
        response = '''[
            {
                "question_text": "Who said \\"Hello, World\\"?",
                "question_type": "single_choice",
                "options": [
                    {"id": "a", "text": "Programmer", "is_correct": true},
                    {"id": "b", "text": "Writer", "is_correct": false}
                ],
                "points": 1
            }
        ]'''

        questions = QuestionParser.parse_questions_response(response)
        assert len(questions) == 1

    def test_grading_defaults_for_missing_values(self):
        """Test that grading uses defaults for missing values."""
        response = '{}'  # Empty JSON object

        result = GradingParser.parse_grading_response(response)

        assert result.score == 0.5  # Default
        assert result.confidence == 0.5  # Default
        assert result.feedback == ""

    def test_parse_questions_with_null_values(self):
        """Test parsing questions with explicit null values."""
        response = '''[
            {
                "question_text": "Test?",
                "question_type": "open_ended",
                "options": null,
                "correct_answer": null,
                "bloom_level": null,
                "points": null
            }
        ]'''

        questions = QuestionParser.parse_questions_response(response)

        assert len(questions) == 1
        assert questions[0]["bloom_level"] == "understand"  # Default
        assert questions[0]["points"] == 1  # Default


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
