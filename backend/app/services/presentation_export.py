"""
PPTX export for AI-generated presentations.

Template-based approach: loads a .pptx template and fills slide layouts
with content from the JSON slide data. Falls back to code-generated
slides if template or layout is unavailable.
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

# Template directory
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "presentations"

# Available templates and their layout mappings
# Each template maps our slide types to (layout_index, {placeholder_idx: field})
TEMPLATE_CONFIGS = {
    "academic": {
        "file": "Academic_Presentation.pptx",
        "label": "Академический",
        "layouts": {
            "title":      {"index": 0, "placeholders": {0: "title", 1: "subtitle"}},
            "objectives": {"index": 2, "placeholders": {0: "title", 1: "body"}},
            "content":    {"index": 2, "placeholders": {0: "title", 1: "body"}},
            "key_terms":  {"index": 3, "placeholders": {0: "title", 1: "col1", 2: "col2"}},
            "quiz":       {"index": 6, "placeholders": {0: "title"}},
            "summary":    {"index": 2, "placeholders": {0: "title", 1: "body"}},
        },
    },
    "history": {
        "file": "History_by_Yeenstudio.pptx",
        "label": "История",
        "layouts": {
            "title":      {"index": 0, "placeholders": {0: "title", 1: "subtitle"}},
            "objectives": {"index": 2, "placeholders": {0: "title", 1: "body"}},
            "content":    {"index": 5, "placeholders": {0: "title", 1: "body"}},
            "key_terms":  {"index": 3, "placeholders": {0: "title", 1: "col1", 2: "col2"}},
            "quiz":       {"index": 6, "placeholders": {0: "title"}},
            "summary":    {"index": 2, "placeholders": {0: "title", 1: "body"}},
        },
    },
    "biology": {
        "file": "Biology_Research_Fun_Education_Presentation.pptx",
        "label": "Биология",
        "layouts": {
            "title":      {"index": 0},
            "objectives": {"index": 1, "placeholders": {10: "title"}},
            "content":    {"index": 2, "placeholders": {10: "title"}},
            "key_terms":  {"index": 3, "placeholders": {10: "title", 11: "body"}},
            "quiz":       {"index": 2, "placeholders": {10: "title"}},
            "summary":    {"index": 1, "placeholders": {10: "title"}},
        },
    },
    "lesson": {
        "file": "lesson.pptx",
        "label": "Урок",
        "layouts": {
            "title":      {"index": 0, "placeholders": {0: "title", 1: "subtitle"}},
            "objectives": {"index": 1, "placeholders": {0: "title", 1: "body"}},
            "content":    {"index": 1, "placeholders": {0: "title", 1: "body"}},
            "key_terms":  {"index": 3, "placeholders": {0: "title", 1: "col1", 2: "col2"}},
            "quiz":       {"index": 5, "placeholders": {0: "title"}},
            "summary":    {"index": 1, "placeholders": {0: "title", 1: "body"}},
        },
    },
    "chemistry": {
        "file": "Chemistry.pptx",
        "label": "Химия",
        "layouts": {
            "title":      {"index": 0, "placeholders": {0: "title", 1: "subtitle"}},
            "objectives": {"index": 2, "placeholders": {0: "title", 1: "body"}},
            "content":    {"index": 2, "placeholders": {0: "title", 1: "body"}},
            "key_terms":  {"index": 3, "placeholders": {0: "title", 1: "col1", 2: "col2"}},
            "quiz":       {"index": 6, "placeholders": {0: "title"}},
            "summary":    {"index": 2, "placeholders": {0: "title", 1: "body"}},
        },
    },
}

DEFAULT_TEMPLATE = "academic"

# Fallback colors for overlay text boxes
TEXT_DARK = RGBColor(0x1F, 0x2A, 0x37)
TEXT_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT_GREEN = RGBColor(0x16, 0xA3, 0x4A)


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
    config = TEMPLATE_CONFIGS.get(template_slug)

    if not config:
        config = TEMPLATE_CONFIGS[DEFAULT_TEMPLATE]
        template_slug = DEFAULT_TEMPLATE

    template_path = TEMPLATES_DIR / config["file"]

    if template_path.exists():
        prs = Presentation(str(template_path))
        # Remove all existing slides from template (keep only layouts)
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
            _add_slide_from_template(prs, slide_data, slide_type, layout_map, textbook_id, context_data)
        except Exception:
            logger.exception("Error rendering slide type=%s with template=%s", slide_type, template_slug)
            # Fallback: blank slide with title
            _add_fallback_slide(prs, slide_data)

    buf = BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


def _remove_all_slides(prs):
    """Remove all slides from the presentation, keeping layouts."""
    while len(prs.slides) > 0:
        rId = prs.slides._sldIdLst[0].get('r:id')
        prs.part.drop_rel(rId)
        prs.slides._sldIdLst.remove(prs.slides._sldIdLst[0])


def _add_slide_from_template(prs, slide_data, slide_type, layout_map, textbook_id, context_data):
    """Add a slide using the template's layout and fill placeholders."""
    layout_cfg = layout_map.get(slide_type, layout_map.get("content", {}))
    layout_idx = layout_cfg.get("index", 0)
    ph_map = layout_cfg.get("placeholders", {})

    # Ensure layout index is valid
    if layout_idx >= len(prs.slide_layouts):
        layout_idx = 0

    layout = prs.slide_layouts[layout_idx]
    slide = prs.slides.add_slide(layout)

    # Fill placeholders from template layout
    _fill_placeholders(slide, slide_data, slide_type, ph_map, context_data)

    # Add overlay text boxes for content that doesn't fit in placeholders
    _add_overlay_content(slide, slide_data, slide_type, ph_map, textbook_id, prs)


def _fill_placeholders(slide, slide_data, slide_type, ph_map, context_data):
    """Fill template placeholders with slide content."""
    for ph in slide.placeholders:
        idx = ph.placeholder_format.idx
        field = ph_map.get(idx)

        if not field:
            continue

        if field == "title":
            ph.text = slide_data.get("title", "")

        elif field == "subtitle":
            subtitle = slide_data.get("subtitle", "")
            if not subtitle and slide_type == "title":
                subject = context_data.get("subject", "")
                grade = context_data.get("grade_level", "")
                subtitle = f"{subject} | {grade} класс" if grade else subject
            ph.text = subtitle

        elif field == "body":
            _fill_body_placeholder(ph, slide_data, slide_type)

        elif field == "col1":
            # Left column: terms
            if slide_type == "key_terms":
                terms = slide_data.get("terms", [])
                text = "\n".join(t.get("term", "") for t in terms[:8])
                ph.text = text

        elif field == "col2":
            # Right column: definitions
            if slide_type == "key_terms":
                terms = slide_data.get("terms", [])
                text = "\n".join(t.get("definition", "") for t in terms[:8])
                ph.text = text


def _fill_body_placeholder(ph, slide_data, slide_type):
    """Fill a body/content placeholder based on slide type."""
    if slide_type == "objectives":
        items = slide_data.get("items", [])
        ph.text = ""
        tf = ph.text_frame
        for i, item in enumerate(items[:8]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = f"{i + 1}. {item}"
            p.space_after = Pt(6)

    elif slide_type == "content":
        ph.text = slide_data.get("body", "")

    elif slide_type == "key_terms":
        terms = slide_data.get("terms", [])
        ph.text = ""
        tf = ph.text_frame
        for i, term_data in enumerate(terms[:8]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = f"{term_data.get('term', '')}: {term_data.get('definition', '')}"
            p.space_after = Pt(4)
            # Bold the term part
            if p.runs:
                pass  # Text already set

    elif slide_type == "summary":
        items = slide_data.get("items", [])
        ph.text = ""
        tf = ph.text_frame
        for i, item in enumerate(items[:8]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = f"\u2713 {item}"
            p.space_after = Pt(6)

    elif slide_type == "quiz":
        # Question + options in body
        question = slide_data.get("question", "")
        options = slide_data.get("options", [])
        answer_idx = slide_data.get("answer", 0)
        letters = ["A", "B", "C", "D", "E", "F"]

        ph.text = ""
        tf = ph.text_frame
        # Question
        p = tf.paragraphs[0]
        p.text = question
        p.font.bold = True
        p.font.size = Pt(18)
        p.space_after = Pt(12)

        # Options
        for i, option in enumerate(options[:6]):
            p = tf.add_paragraph()
            letter = letters[i] if i < len(letters) else str(i + 1)
            marker = " \u2714" if i == answer_idx else ""
            p.text = f"{letter}) {option}{marker}"
            p.space_after = Pt(6)
            if i == answer_idx:
                p.font.bold = True


def _add_overlay_content(slide, slide_data, slide_type, ph_map, textbook_id, prs):
    """Add text boxes for content that couldn't be placed in placeholders."""
    has_body_ph = any(f in ("body", "col1") for f in ph_map.values())

    # For quiz type without body placeholder: add question + options as text boxes
    if slide_type == "quiz" and not has_body_ph:
        sw = prs.slide_width
        sh = prs.slide_height
        margin = Inches(0.8)
        question = slide_data.get("question", "")
        options = slide_data.get("options", [])
        answer_idx = slide_data.get("answer", 0)
        letters = ["A", "B", "C", "D", "E", "F"]

        # Question box
        txBox = slide.shapes.add_textbox(margin, Inches(1.8), sw - margin * 2, Inches(1.2))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = question
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = TEXT_DARK

        # Options
        y = Inches(3.2)
        for i, option in enumerate(options[:6]):
            letter = letters[i] if i < len(letters) else str(i + 1)
            marker = " \u2714" if i == answer_idx else ""
            txBox = slide.shapes.add_textbox(margin + Inches(0.3), y, sw - margin * 2 - Inches(0.6), Inches(0.55))
            tf = txBox.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = f"{letter}) {option}{marker}"
            p.font.size = Pt(16)
            p.font.color.rgb = TEXT_DARK
            if i == answer_idx:
                p.font.bold = True
            y += Inches(0.7)

    # For objectives/summary without body placeholder: add items as text boxes
    if slide_type in ("objectives", "summary") and not has_body_ph:
        sw = prs.slide_width
        margin = Inches(0.8)
        items = slide_data.get("items", [])
        y = Inches(1.8)
        for i, item in enumerate(items[:8]):
            prefix = f"{i + 1}." if slide_type == "objectives" else "\u2713"
            txBox = slide.shapes.add_textbox(margin, y, sw - margin * 2, Inches(0.55))
            tf = txBox.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = f"  {prefix}  {item}"
            p.font.size = Pt(18)
            p.font.color.rgb = TEXT_DARK
            y += Inches(0.6)

    # For content without body placeholder: add body text
    if slide_type == "content" and not has_body_ph:
        sw = prs.slide_width
        margin = Inches(0.8)
        body = slide_data.get("body", "")
        txBox = slide.shapes.add_textbox(margin, Inches(1.8), sw - margin * 2, Inches(4.5))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = body
        p.font.size = Pt(16)
        p.font.color.rgb = TEXT_DARK

    # Add image if present (for content slides)
    if slide_type == "content" and textbook_id:
        image_url = slide_data.get("image_url")
        if image_url:
            image_path = _resolve_image_path(image_url, textbook_id)
            if image_path and Path(image_path).exists():
                try:
                    sw = prs.slide_width
                    slide.shapes.add_picture(
                        image_path,
                        sw - Inches(4.5), Inches(1.8),
                        Inches(3.8), Inches(3.8),
                    )
                except Exception:
                    logger.warning("Failed to add image: %s", image_path)


def _add_fallback_slide(prs, slide_data):
    """Add a basic blank slide as fallback."""
    layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(layout)
    title = slide_data.get("title", "Slide")
    txBox = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(10), Inches(1))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(24)
    p.font.bold = True


def _resolve_image_path(url: str, textbook_id: int) -> str | None:
    """Convert /uploads/textbook-images/ID/file.jpg to absolute path."""
    if not url:
        return None
    if url.startswith("/uploads/textbook-images/"):
        filename = url.split("/")[-1]
        return str(Path(settings.UPLOAD_DIR) / "textbook-images" / str(textbook_id) / filename)
    return None
