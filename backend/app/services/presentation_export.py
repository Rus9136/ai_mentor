"""
PPTX export for AI-generated presentations.

Converts slide JSON data into a .pptx file using python-pptx.
Code-generated slides (no template file required).
"""
import logging
from io import BytesIO
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Color scheme ---
PRIMARY = RGBColor(0x1A, 0x56, 0xDB)       # Blue
PRIMARY_DARK = RGBColor(0x16, 0x3C, 0x9C)  # Dark blue
ACCENT = RGBColor(0x16, 0xA3, 0x4A)        # Green
ACCENT_WARM = RGBColor(0xEA, 0x58, 0x0C)   # Orange
TEXT_DARK = RGBColor(0x1F, 0x2A, 0x37)      # Near-black
TEXT_LIGHT = RGBColor(0xFF, 0xFF, 0xFF)     # White
BG_LIGHT = RGBColor(0xF1, 0xF5, 0xF9)      # Light gray
BG_CARD = RGBColor(0xE2, 0xE8, 0xF0)       # Card gray

# Slide dimensions (16:9)
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# Margins
LEFT_MARGIN = Inches(0.8)
TOP_CONTENT = Inches(1.6)
CONTENT_W = Inches(11.733)


def export_to_pptx(slides_data: dict, context_data: dict) -> BytesIO:
    """Convert presentation JSON to PPTX document."""
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    blank_layout = prs.slide_layouts[6]  # Blank
    textbook_id = context_data.get("textbook_id")

    slides = slides_data.get("slides", [])

    for slide_data in slides:
        slide_type = slide_data.get("type", "content")
        slide = prs.slides.add_slide(blank_layout)

        try:
            if slide_type == "title":
                _render_title_slide(slide, slide_data, context_data)
            elif slide_type == "objectives":
                _render_objectives_slide(slide, slide_data)
            elif slide_type == "content":
                _render_content_slide(slide, slide_data, textbook_id)
            elif slide_type == "key_terms":
                _render_key_terms_slide(slide, slide_data)
            elif slide_type == "quiz":
                _render_quiz_slide(slide, slide_data)
            elif slide_type == "summary":
                _render_summary_slide(slide, slide_data)
            else:
                _render_content_slide(slide, slide_data, textbook_id)
        except Exception:
            logger.exception("Error rendering slide type=%s", slide_type)
            # Add fallback text
            _add_text_box(slide, LEFT_MARGIN, TOP_CONTENT, CONTENT_W, Inches(4),
                          slide_data.get("title", "Slide"), Pt(24), TEXT_DARK, bold=True)

    buf = BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


# --- Slide Renderers ---


def _render_title_slide(slide, data, context):
    """Title slide with blue background."""
    # Full blue background
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, SLIDE_H, PRIMARY)

    # Title
    title = data.get("title", "")
    _add_text_box(slide, Inches(1.5), Inches(2.0), Inches(10.333), Inches(2),
                  title, Pt(40), TEXT_LIGHT, bold=True, align=PP_ALIGN.CENTER)

    # Subtitle
    subtitle = data.get("subtitle", "")
    if subtitle:
        _add_text_box(slide, Inches(1.5), Inches(4.2), Inches(10.333), Inches(1.2),
                      subtitle, Pt(22), TEXT_LIGHT, align=PP_ALIGN.CENTER)

    # Context line at bottom
    subject = context.get("subject", "")
    grade = context.get("grade_level", "")
    if subject or grade:
        footer = f"{subject} | {grade} класс" if grade else subject
        _add_text_box(slide, Inches(1.5), Inches(6.2), Inches(10.333), Inches(0.6),
                      footer, Pt(14), RGBColor(0xBF, 0xDB, 0xFE), align=PP_ALIGN.CENTER)


def _render_objectives_slide(slide, data):
    """Learning objectives slide."""
    # Header bar
    _add_header_bar(slide, data.get("title", "Сабақтың мақсаты"))

    items = data.get("items", [])
    y = TOP_CONTENT + Inches(0.3)
    for i, item in enumerate(items[:8]):
        bullet_text = f"  {i + 1}.  {item}"
        _add_text_box(slide, LEFT_MARGIN, y, CONTENT_W, Inches(0.6),
                      bullet_text, Pt(20), TEXT_DARK)
        y += Inches(0.65)


def _render_content_slide(slide, data, textbook_id):
    """Content slide with optional image."""
    _add_header_bar(slide, data.get("title", ""))

    image_url = data.get("image_url")
    image_path = _resolve_image_path(image_url, textbook_id) if image_url and textbook_id else None
    has_image = image_path and Path(image_path).exists()

    body_width = Inches(7.0) if has_image else CONTENT_W
    body = data.get("body", "")

    _add_text_box(slide, LEFT_MARGIN, TOP_CONTENT + Inches(0.2), body_width, Inches(4.5),
                  body, Pt(18), TEXT_DARK, wrap=True)

    if has_image:
        try:
            slide.shapes.add_picture(
                image_path, Inches(8.5), TOP_CONTENT + Inches(0.2),
                Inches(4.0), Inches(4.0),
            )
        except Exception:
            logger.warning("Failed to add image: %s", image_path)


def _render_key_terms_slide(slide, data):
    """Key terms slide with term-definition pairs."""
    _add_header_bar(slide, data.get("title", "Негізгі ұғымдар"))

    terms = data.get("terms", [])
    y = TOP_CONTENT + Inches(0.3)

    for term_data in terms[:8]:
        term = term_data.get("term", "")
        definition = term_data.get("definition", "")

        # Term card background
        _add_rect(slide, LEFT_MARGIN, y, CONTENT_W, Inches(0.7), BG_LIGHT)

        # Term (bold)
        _add_text_box(slide, Inches(1.0), y + Inches(0.05), Inches(3.5), Inches(0.6),
                      term, Pt(18), PRIMARY, bold=True)

        # Definition
        _add_text_box(slide, Inches(4.8), y + Inches(0.05), Inches(7.5), Inches(0.6),
                      f"— {definition}", Pt(16), TEXT_DARK)

        y += Inches(0.8)


def _render_quiz_slide(slide, data):
    """Quiz question slide."""
    # Green header bar
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(1.3), ACCENT)
    _add_text_box(slide, LEFT_MARGIN, Inches(0.25), CONTENT_W, Inches(0.8),
                  data.get("title", "Білімді тексер"), Pt(28), TEXT_LIGHT, bold=True)

    # Question
    question = data.get("question", "")
    _add_text_box(slide, LEFT_MARGIN, Inches(1.8), CONTENT_W, Inches(1.0),
                  question, Pt(22), TEXT_DARK, bold=True, wrap=True)

    # Options
    options = data.get("options", [])
    answer_idx = data.get("answer", 0)
    y = Inches(3.2)
    letters = ["A", "B", "C", "D", "E", "F"]

    for i, option in enumerate(options[:6]):
        is_answer = (i == answer_idx)
        bg_color = RGBColor(0xDC, 0xFC, 0xE7) if is_answer else BG_LIGHT
        text_color = ACCENT if is_answer else TEXT_DARK

        _add_rect(slide, LEFT_MARGIN, y, Inches(10), Inches(0.65), bg_color)

        letter = letters[i] if i < len(letters) else str(i + 1)
        _add_text_box(slide, Inches(1.0), y + Inches(0.05), Inches(9.5), Inches(0.55),
                      f"{letter})  {option}", Pt(18), text_color)
        y += Inches(0.8)


def _render_summary_slide(slide, data):
    """Summary slide."""
    # Dark blue header bar
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(1.3), PRIMARY_DARK)
    _add_text_box(slide, LEFT_MARGIN, Inches(0.25), CONTENT_W, Inches(0.8),
                  data.get("title", "Қорытынды"), Pt(28), TEXT_LIGHT, bold=True)

    items = data.get("items", [])
    y = Inches(1.8)
    for i, item in enumerate(items[:8]):
        # Checkmark icon + text
        _add_text_box(slide, LEFT_MARGIN, y, CONTENT_W, Inches(0.6),
                      f"  \u2713  {item}", Pt(18), TEXT_DARK)
        y += Inches(0.65)


# --- Helpers ---


def _add_header_bar(slide, title: str):
    """Add a blue header bar at the top of a content slide."""
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(1.3), PRIMARY)
    _add_text_box(slide, LEFT_MARGIN, Inches(0.25), CONTENT_W, Inches(0.8),
                  title, Pt(28), TEXT_LIGHT, bold=True)


def _add_rect(slide, left, top, width, height, fill_color):
    """Add a filled rectangle shape."""
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE.RECTANGLE
        left, top, width, height,
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()  # No border


def _add_text_box(slide, left, top, width, height, text, font_size,
                  font_color, bold=False, align=PP_ALIGN.LEFT, wrap=True):
    """Add a text box with styled text."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    tf.auto_size = None

    p = tf.paragraphs[0]
    p.text = text
    p.font.size = font_size
    p.font.color.rgb = font_color
    p.font.bold = bold
    p.alignment = align

    return txBox


def _resolve_image_path(url: str, textbook_id: int) -> str | None:
    """Convert /uploads/textbook-images/ID/file.jpg to absolute path."""
    if not url:
        return None
    if url.startswith("/uploads/textbook-images/"):
        filename = url.split("/")[-1]
        return str(Path(settings.UPLOAD_DIR) / "textbook-images" / str(textbook_id) / filename)
    return None
