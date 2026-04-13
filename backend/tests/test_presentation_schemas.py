"""
Tests for presentation v2 schemas — SlideV2 validation and backward compatibility.

These tests run WITHOUT database — pure pydantic validation.
"""
import pytest

from app.schemas.presentation import (
    SlideV2,
    SlideTermV2,
    SlidesDataV2,
    validate_slides_data,
)


# ═══════════════════════════════════════════════════════════
#  BACKWARD COMPATIBILITY — old v1 JSON must parse fine
# ═══════════════════════════════════════════════════════════


V1_CONTENT_SLIDE = {
    "type": "content",
    "title": "Қасым ханның шығу тегі",
    "body": "Қазақ хандығын Бұрындық хан басқарған кезеңде...",
    "image_url": "/uploads/textbook-images/25/img_001.jpg",
}

V1_QUIZ_SLIDE = {
    "type": "quiz",
    "title": "Білімді тексер",
    "question": "Қасым хан қай жылы хан тағына отырғызылды?",
    "options": ["1509 жылы", "1511 жылы", "1503 жылы", "1510 жылы"],
    "answer": 1,
}

V1_KEY_TERMS_SLIDE = {
    "type": "key_terms",
    "title": "Негізгі ұғымдар",
    "terms": [
        {"term": "Қасым", "definition": "Қазақ хандығының ханы."},
        {"term": "Бұрындық", "definition": "Қасым ханнан бұрын билік жүргізген."},
    ],
}

V1_FULL_PRESENTATION = {
    "title": "Қасым хан",
    "slides": [
        {"type": "title", "title": "Қасым хан", "subtitle": "XVI ғасыр"},
        {"type": "objectives", "title": "Мақсат", "items": ["Білу", "Түсіну"]},
        V1_CONTENT_SLIDE,
        V1_KEY_TERMS_SLIDE,
        V1_QUIZ_SLIDE,
        {"type": "summary", "title": "Қорытынды", "items": ["Бірінші", "Екінші"]},
    ],
}


class TestBackwardCompatibility:
    def test_v1_content_slide_parses(self):
        slide = SlideV2.model_validate(V1_CONTENT_SLIDE)
        assert slide.type == "content"
        assert slide.layout_hint == "image_left"  # default for content without stat_value
        assert slide.image_query is None
        assert slide.stat_value is None

    def test_v1_quiz_slide_parses(self):
        slide = SlideV2.model_validate(V1_QUIZ_SLIDE)
        assert slide.type == "quiz"
        assert slide.answer == 1
        assert slide.layout_hint is None  # not a content slide

    def test_v1_key_terms_parses(self):
        slide = SlideV2.model_validate(V1_KEY_TERMS_SLIDE)
        assert slide.type == "key_terms"
        assert len(slide.terms) == 2
        assert slide.terms[0].term == "Қасым"

    def test_v1_full_presentation_parses(self):
        data = SlidesDataV2.model_validate(V1_FULL_PRESENTATION)
        assert data.title == "Қасым хан"
        assert len(data.slides) == 6

    def test_validate_slides_data_v1(self):
        result = validate_slides_data(V1_FULL_PRESENTATION)
        assert "slides" in result
        assert len(result["slides"]) == 6

    def test_unknown_fields_ignored(self):
        """Old JSON may contain fields like emphasis_word — should be ignored."""
        slide_data = {
            **V1_CONTENT_SLIDE,
            "emphasis_word": "беделді",
            "unknown_field": 42,
        }
        slide = SlideV2.model_validate(slide_data)
        assert slide.type == "content"
        assert not hasattr(slide, "emphasis_word")


# ═══════════════════════════════════════════════════════════
#  V2 FIELDS
# ═══════════════════════════════════════════════════════════


V2_CONTENT_IMAGE_LEFT = {
    "type": "content",
    "title": "Қасым ханның шығу тегі",
    "body": "Қазақ хандығын Бұрындық хан басқарған кезеңде...",
    "layout_hint": "image_left",
    "image_query": "lake balkhash kazakhstan",
}

V2_CONTENT_STAT = {
    "type": "content",
    "title": "Хан тағына отыруы",
    "body": "1511 жылы Түркістан аймағының билеушілері...",
    "layout_hint": "stat_callout",
    "stat_value": "1511",
    "stat_label": "хан болып сайланды",
}


class TestV2Fields:
    def test_layout_hint_image_left(self):
        slide = SlideV2.model_validate(V2_CONTENT_IMAGE_LEFT)
        assert slide.layout_hint == "image_left"
        assert slide.image_query == "lake balkhash kazakhstan"

    def test_layout_hint_image_right(self):
        data = {**V2_CONTENT_IMAGE_LEFT, "layout_hint": "image_right"}
        slide = SlideV2.model_validate(data)
        assert slide.layout_hint == "image_right"

    def test_layout_hint_stat_callout(self):
        slide = SlideV2.model_validate(V2_CONTENT_STAT)
        assert slide.layout_hint == "stat_callout"
        assert slide.stat_value == "1511"
        assert slide.stat_label == "хан болып сайланды"

    def test_default_layout_hint_with_stat_value(self):
        """If stat_value present but no layout_hint, default to stat_callout."""
        data = {
            "type": "content",
            "title": "Test",
            "body": "Test body",
            "stat_value": "1511",
        }
        slide = SlideV2.model_validate(data)
        assert slide.layout_hint == "stat_callout"

    def test_default_layout_hint_without_stat(self):
        """If no stat_value and no layout_hint, default to image_left."""
        data = {"type": "content", "title": "Test", "body": "Test body"}
        slide = SlideV2.model_validate(data)
        assert slide.layout_hint == "image_left"

    def test_non_content_slide_no_default_layout(self):
        """quiz/summary slides should NOT get default layout_hint."""
        data = {"type": "quiz", "question": "Test?", "options": ["A", "B"], "answer": 0}
        slide = SlideV2.model_validate(data)
        assert slide.layout_hint is None


# ═══════════════════════════════════════════════════════════
#  SOFT VALIDATION — truncation, not exceptions
# ═══════════════════════════════════════════════════════════


class TestSoftValidation:
    def test_long_title_truncated(self):
        data = {"type": "content", "title": "А" * 100, "body": "test"}
        slide = SlideV2.model_validate(data)
        assert len(slide.title) == 60

    def test_long_body_truncated(self):
        data = {"type": "content", "title": "Test", "body": "Б" * 500}
        slide = SlideV2.model_validate(data)
        assert len(slide.body) == 300

    def test_long_stat_value_truncated(self):
        data = {
            "type": "content",
            "title": "Test",
            "body": "Test",
            "stat_value": "12345678",
            "layout_hint": "stat_callout",
        }
        slide = SlideV2.model_validate(data)
        assert len(slide.stat_value) == 7

    def test_long_items_truncated(self):
        data = {
            "type": "objectives",
            "title": "Test",
            "items": ["X" * 100, "Short"],
        }
        slide = SlideV2.model_validate(data)
        assert len(slide.items[0]) == 80
        assert slide.items[1] == "Short"

    def test_long_option_truncated(self):
        data = {
            "type": "quiz",
            "question": "Test?",
            "options": ["O" * 60, "Short"],
            "answer": 0,
        }
        slide = SlideV2.model_validate(data)
        assert len(slide.options[0]) == 50
        assert slide.options[1] == "Short"

    def test_long_term_truncated(self):
        term = SlideTermV2(term="А" * 50, definition="Б" * 150)
        assert len(term.term) == 25
        assert len(term.definition) == 90

    def test_image_query_non_latin_cleaned(self):
        data = {
            "type": "content",
            "title": "Test",
            "body": "Test",
            "image_query": "Қазақстан тарихы kazakh steppe",
            "layout_hint": "image_left",
        }
        slide = SlideV2.model_validate(data)
        # Cyrillic chars removed, only latin+spaces remain
        assert slide.image_query == "kazakh steppe"

    def test_image_query_pure_latin_kept(self):
        data = {
            "type": "content",
            "title": "Test",
            "body": "Test",
            "image_query": "lake balkhash",
            "layout_hint": "image_left",
        }
        slide = SlideV2.model_validate(data)
        assert slide.image_query == "lake balkhash"

    def test_image_query_all_nonlatin_becomes_none(self):
        """If cleaning removes everything, image_query becomes None."""
        data = {
            "type": "content",
            "title": "Test",
            "body": "Test",
            "image_query": "Қасым хан",
            "layout_hint": "image_left",
        }
        slide = SlideV2.model_validate(data)
        assert slide.image_query is None


class TestValidateSlidesData:
    def test_returns_dict(self):
        result = validate_slides_data(V1_FULL_PRESENTATION)
        assert isinstance(result, dict)

    def test_broken_data_still_parses_with_defaults(self):
        """Data without 'slides' key still parses — slides defaults to []."""
        broken = {"not_a_slides_format": True}
        result = validate_slides_data(broken)
        assert result["slides"] == []
        assert result["title"] == ""

    def test_truly_invalid_data_returns_raw(self):
        """Non-dict input should return raw data."""
        raw = "not a dict"
        result = validate_slides_data(raw)
        assert result == raw

    def test_v2_sample_parses(self):
        """The sample_slides.json format should parse correctly."""
        v2_sample = {
            "title": "Қасым хан",
            "theme": "warm",
            "slides": [
                {
                    "type": "title",
                    "title": "Қасым хан",
                    "subtitle": "XVI ғасырдағы дамуы",
                    "image_query": "kazakh steppe historical",
                },
                {
                    "type": "content",
                    "title": "Шығу тегі",
                    "body": "Бұрындық хан кезеңінде...",
                    "layout_hint": "image_left",
                    "image_query": "lake balkhash kazakhstan",
                },
                {
                    "type": "content",
                    "title": "Билік аясы",
                    "body": "Батыста манғыттармен...",
                    "layout_hint": "stat_callout",
                    "stat_value": "Жайық",
                    "stat_label": "өзеніне дейінгі аймақ",
                },
            ],
        }
        result = validate_slides_data(v2_sample)
        slides = result["slides"]
        assert slides[1]["layout_hint"] == "image_left"
        assert slides[2]["layout_hint"] == "stat_callout"
        assert slides[2]["stat_value"] == "Жайық"

    def test_sample_slides_json_format(self):
        """Test with the exact format from sample_slides.json."""
        import json
        from pathlib import Path

        sample_path = Path(__file__).parent.parent.parent / "sample_slides.json"
        if not sample_path.exists():
            pytest.skip("sample_slides.json not found")
        with open(sample_path, encoding="utf-8") as f:
            data = json.load(f)
        result = validate_slides_data(data)
        assert "slides" in result
        assert len(result["slides"]) == 10
