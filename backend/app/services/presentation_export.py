"""
PPTX export for AI-generated presentations.

Template-based: loads a .pptx template, removes existing slides,
creates new slides using template layouts, and fills them with content.
"""
import logging
from io import BytesIO
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from app.core.config import settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "presentations"

# Template configs: maps slide types to layout indices and placeholder mappings
TEMPLATE_CONFIGS = {
    "academic": {
        "file": "Academic_Presentation.pptx",
        "label": "Академический",
        "layouts": {
            "title":      0,   # TITLE: idx0=title, idx1=subtitle
            "objectives": 2,   # TITLE_AND_BODY: idx0=title, idx1=body
            "content":    2,   # TITLE_AND_BODY
            "key_terms":  3,   # TITLE_AND_TWO_COLUMNS: idx0=title, idx1=col1, idx2=col2
            "quiz":       4,   # TITLE_ONLY: idx0=title (overlay for Q+options)
            "summary":    2,   # TITLE_AND_BODY
        },
    },
    "history": {
        "file": "History_by_Yeenstudio.pptx",
        "label": "История",
        "layouts": {
            "title":      0,
            "objectives": 2,
            "content":    5,   # ONE_COLUMN_TEXT
            "key_terms":  3,
            "quiz":       4,
            "summary":    2,
        },
    },
    "biology": {
        "file": "Biology_Research_Fun_Education_Presentation.pptx",
        "label": "Биология",
        "layouts": {
            "title":      0,
            "objectives": 2,
            "content":    2,
            "key_terms":  3,
            "quiz":       2,
            "summary":    1,
        },
    },
    "lesson": {
        "file": "lesson.pptx",
        "label": "Урок",
        "layouts": {
            "title":      0,
            "objectives": 1,   # Title and Content
            "content":    1,
            "key_terms":  3,   # Two Content
            "quiz":       5,   # Title Only
            "summary":    1,
        },
    },
    "chemistry": {
        "file": "Chemistry.pptx",
        "label": "Химия",
        "layouts": {
            "title":      0,
            "objectives": 2,
            "content":    2,
            "key_terms":  3,
            "quiz":       4,
            "summary":    2,
        },
    },
}

DEFAULT_TEMPLATE = "academic"

# Colors for overlay text boxes
TEXT_DARK = RGBColor(0x33, 0x33, 0x33)
ACCENT_GREEN = RGBColor(0x0D, 0x7C, 0x3E)
QUIZ_BG = RGBColor(0xF0, 0xF4, 0xF8)
CORRECT_BG = RGBColor(0xD4, 0xED, 0xDA)


def get_available_templates() -> list[dict]:
    """Return list of available templates for the frontend."""
    result = []
    for slug, cfg in TEMPLATE_CONFIGS.items():
        template_path = TEMPLATES_DIR / cfg["file"]
        if template_path.exists():
            result.append({"slug": slug, "label": cfg["label"], "file": cfg["file"]})
    return result


def export_to_pptx(slides_data: dict, context_data: dict, template: str | None = None) -> BytesIO:
    """Convert presentation JSON to PPTX using a template."""
    template_slug = template or DEFAULT_TEMPLATE
    config = TEMPLATE_CONFIGS.get(template_slug, TEMPLATE_CONFIGS[DEFAULT_TEMPLATE])
    template_path = TEMPLATES_DIR / config["file"]

    if template_path.exists():
        prs = Presentation(str(template_path))
        _remove_all_slides(prs)
    else:
        logger.warning("Template %s not found, using blank", template_path)
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

    layout_map = config.get("layouts", {})
    textbook_id = context_data.get("textbook_id")

    for slide_data in slides_data.get("slides", []):
        slide_type = slide_data.get("type", "content")
        try:
            layout_idx = layout_map.get(slide_type, layout_map.get("content", 0))
            if layout_idx >= len(prs.slide_layouts):
                layout_idx = 0
            layout = prs.slide_layouts[layout_idx]
            slide = prs.slides.add_slide(layout)
            _fill_slide(slide, slide_data, slide_type, context_data, textbook_id, prs)
        except Exception:
            logger.exception("Error rendering slide type=%s", slide_type)
            # Fallback
            slide = prs.slides.add_slide(prs.slide_layouts[0])
            _set_placeholder_text(slide, 0, slide_data.get("title", ""))

    buf = BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


# --- Core rendering ---


def _fill_slide(slide, data, slide_type, context_data, textbook_id, prs):
    """Fill a slide based on its type."""
    if slide_type == "title":
        _fill_title(slide, data, context_data)
    elif slide_type == "objectives":
        _fill_bullet_list(slide, data, numbered=True)
    elif slide_type == "content":
        _fill_content(slide, data, textbook_id, prs)
    elif slide_type == "key_terms":
        _fill_key_terms(slide, data, prs)
    elif slide_type == "quiz":
        _fill_quiz(slide, data, prs)
    elif slide_type == "summary":
        _fill_bullet_list(slide, data, numbered=False, checkmark=True)
    else:
        _fill_content(slide, data, textbook_id, prs)


def _fill_title(slide, data, context_data):
    """Fill title slide placeholders."""
    _set_placeholder_text(slide, 0, data.get("title", ""))
    subtitle = data.get("subtitle", "")
    if not subtitle:
        subject = context_data.get("subject", "")
        grade = context_data.get("grade_level", "")
        subtitle = f"{subject} | {grade} класс" if grade else subject
    _set_placeholder_text(slide, 1, subtitle)


def _fill_bullet_list(slide, data, numbered=False, checkmark=False):
    """Fill a slide with title + bullet list in body placeholder."""
    _set_placeholder_text(slide, 0, data.get("title", ""))

    items = data.get("items", [])
    # Try to find body placeholder (idx=1)
    body_ph = _get_placeholder(slide, 1)
    if body_ph and body_ph.has_text_frame:
        tf = body_ph.text_frame
        tf.clear()
        for i, item in enumerate(items[:10]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            if numbered:
                p.text = f"{i + 1}. {item}"
            elif checkmark:
                p.text = f"\u2713  {item}"
            else:
                p.text = item
            p.space_after = Pt(8)
            if p.runs:
                p.runs[0].font.size = Pt(16)
    else:
        # No body placeholder — add text box
        _add_bullet_textbox(slide, items, numbered, checkmark, prs=None)


def _fill_content(slide, data, textbook_id, prs):
    """Fill content slide with title + body + optional image."""
    _set_placeholder_text(slide, 0, data.get("title", ""))

    body = data.get("body", "")
    body_ph = _get_placeholder(slide, 1)

    if body_ph and body_ph.has_text_frame:
        tf = body_ph.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = body
        if p.runs:
            p.runs[0].font.size = Pt(15)
        tf.word_wrap = True
    else:
        _add_body_textbox(slide, body, prs)

    # Add image if available
    image_url = data.get("image_url")
    if image_url and textbook_id:
        _add_image(slide, image_url, textbook_id, prs)


def _fill_key_terms(slide, data, prs):
    """Fill key terms slide: title + terms in two columns or as formatted list."""
    _set_placeholder_text(slide, 0, data.get("title", ""))

    terms = data.get("terms", [])
    col1_ph = _get_placeholder(slide, 1)
    col2_ph = _get_placeholder(slide, 2)

    if col1_ph and col2_ph and col1_ph.has_text_frame and col2_ph.has_text_frame:
        # Two-column layout: terms in col1, definitions in col2
        tf1 = col1_ph.text_frame
        tf1.clear()
        tf2 = col2_ph.text_frame
        tf2.clear()

        for i, t in enumerate(terms[:8]):
            p1 = tf1.paragraphs[0] if i == 0 else tf1.add_paragraph()
            p1.text = t.get("term", "")
            p1.space_after = Pt(10)
            if p1.runs:
                p1.runs[0].font.bold = True
                p1.runs[0].font.size = Pt(15)

            p2 = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
            p2.text = t.get("definition", "")
            p2.space_after = Pt(10)
            if p2.runs:
                p2.runs[0].font.size = Pt(14)
    else:
        # Single column fallback: "term — definition" list
        body_ph = _get_placeholder(slide, 1)
        if body_ph and body_ph.has_text_frame:
            tf = body_ph.text_frame
            tf.clear()
            for i, t in enumerate(terms[:8]):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.text = f"{t.get('term', '')} — {t.get('definition', '')}"
                p.space_after = Pt(8)
                if p.runs:
                    p.runs[0].font.size = Pt(14)
        else:
            _add_terms_textbox(slide, terms, prs)


def _fill_quiz(slide, data, prs):
    """Fill quiz slide: title in placeholder, question+options as text boxes."""
    _set_placeholder_text(slide, 0, data.get("title", ""))

    # Question and options always via text boxes (overlaid on template background)
    question = data.get("question", "")
    options = data.get("options", [])
    answer_idx = data.get("answer", 0)
    letters = ["A", "B", "C", "D", "E", "F"]

    sw = prs.slide_width
    margin_left = Inches(0.7)
    content_w = sw - margin_left * 2

    # Question text box
    q_top = Inches(1.5)
    txBox = slide.shapes.add_textbox(margin_left, q_top, content_w, Inches(1.2))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = question
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = TEXT_DARK

    # Option boxes
    y = Inches(3.0)
    option_w = content_w - Inches(0.4)
    for i, option in enumerate(options[:6]):
        is_correct = (i == answer_idx)
        letter = letters[i] if i < len(letters) else str(i + 1)

        # Background rectangle for each option
        bg_color = CORRECT_BG if is_correct else QUIZ_BG
        rect = slide.shapes.add_shape(1, margin_left + Inches(0.2), y, option_w, Inches(0.6))
        rect.fill.solid()
        rect.fill.fore_color.rgb = bg_color
        rect.line.fill.background()

        # Option text
        txBox = slide.shapes.add_textbox(margin_left + Inches(0.5), y + Inches(0.08), option_w - Inches(0.6), Inches(0.45))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        marker = "  \u2714" if is_correct else ""
        p.text = f"{letter})  {option}{marker}"
        p.font.size = Pt(16)
        p.font.color.rgb = ACCENT_GREEN if is_correct else TEXT_DARK
        if is_correct:
            p.font.bold = True

        y += Inches(0.75)


# --- Helpers ---


def _remove_all_slides(prs):
    """Remove all slides from the presentation, keeping layouts."""
    sldIdLst = prs.slides._sldIdLst
    for sldId in list(sldIdLst):
        rId = sldId.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        if rId is None:
            rId = sldId.get('r:id')
        if rId is not None:
            try:
                prs.part.drop_rel(rId)
            except KeyError:
                pass
        sldIdLst.remove(sldId)


def _get_placeholder(slide, idx):
    """Get placeholder by index, or None if not found."""
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == idx:
            return ph
    return None


def _set_placeholder_text(slide, idx, text):
    """Set text on a placeholder while trying to preserve template styling."""
    ph = _get_placeholder(slide, idx)
    if ph is None or not ph.has_text_frame:
        return

    tf = ph.text_frame
    # Preserve the first paragraph's format by modifying in place
    if tf.paragraphs:
        p = tf.paragraphs[0]
        # Clear existing runs but keep paragraph-level formatting
        for run in list(p.runs):
            p._p.remove(run._r)
        # Add new run with text
        run = p.add_run()
        run.text = text
    else:
        tf.text = text


def _add_body_textbox(slide, text, prs):
    """Add a text box for body content when no placeholder is available."""
    if not prs:
        return
    sw = prs.slide_width
    margin = Inches(0.7)
    txBox = slide.shapes.add_textbox(margin, Inches(1.5), sw - margin * 2, Inches(4.0))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(15)
    p.font.color.rgb = TEXT_DARK


def _add_bullet_textbox(slide, items, numbered, checkmark, prs):
    """Add a text box with bullet items when no placeholder is available."""
    margin = Inches(0.7)
    txBox = slide.shapes.add_textbox(margin, Inches(1.5), Inches(8.5), Inches(4.0))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items[:10]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if numbered:
            p.text = f"{i + 1}. {item}"
        elif checkmark:
            p.text = f"\u2713  {item}"
        else:
            p.text = item
        p.space_after = Pt(8)
        p.font.size = Pt(15)
        p.font.color.rgb = TEXT_DARK


def _add_terms_textbox(slide, terms, prs):
    """Add key terms as a formatted text box."""
    margin = Inches(0.7)
    txBox = slide.shapes.add_textbox(margin, Inches(1.5), Inches(8.5), Inches(4.0))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, t in enumerate(terms[:8]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"{t.get('term', '')} — {t.get('definition', '')}"
        p.space_after = Pt(8)
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_DARK


def _add_image(slide, image_url, textbook_id, prs):
    """Add an image to the slide if the file exists."""
    image_path = _resolve_image_path(image_url, textbook_id)
    if not image_path or not Path(image_path).exists():
        return
    try:
        sw = prs.slide_width
        slide.shapes.add_picture(
            image_path, sw - Inches(4.2), Inches(1.5), Inches(3.5), Inches(3.5),
        )
    except Exception:
        logger.warning("Failed to add image: %s", image_path)


def _resolve_image_path(url: str, textbook_id: int) -> str | None:
    """Convert /uploads/textbook-images/ID/file.jpg to absolute path."""
    if not url:
        return None
    if url.startswith("/uploads/textbook-images/"):
        filename = url.split("/")[-1]
        return str(Path(settings.UPLOAD_DIR) / "textbook-images" / str(textbook_id) / filename)
    return None
