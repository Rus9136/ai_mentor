#!/usr/bin/env python3
"""
Load 'Биология 8-сынып' (Kazakh) into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='kk'.

This is a BIOLOGY textbook — no exercises (A/B/C), 14 бөлімдер, 60 paragraphs.
Chapters are determined by § number ranges from МАЗМУНЫ.
Mixed heading formats: §6 is plain text (no ##), §13/§42/§45/§48 use # (h1).

Usage:
    python scripts/load_textbook_51.py --dry-run           # Parse only
    python scripts/load_textbook_51.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_51.py --update-content FILE # Update SQL
"""
import re
import sys
import hashlib
import argparse
from pathlib import Path
from dataclasses import dataclass, field

# ── Path setup ──────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# ── Constants ───────────────────────────────────────────────────────────────

TEXTBOOK_ID = 51  # Already exists in DB
TEXTBOOK_TITLE = "Биология 8-сынып"
SUBJECT_CODE = "biology"
GRADE_LEVEL = 8
AUTHORS = "Соловьева А.Р., Ибраимова Б.Т."
PUBLISHER = "Атамура"
YEAR = 2018
ISBN = ""
LANGUAGE = "kk"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "51" / "textbook_51.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "51"

# Chapter mapping: § number ranges → chapter info (from МАЗМУНЫ)
CHAPTERS = [
    {"number": 1,  "title": "1-бөлім. Жасушалық биология",                           "para_from": 1,  "para_to": 2},
    {"number": 2,  "title": "2-бөлім. Молекулалық биология",                          "para_from": 3,  "para_to": 5},
    {"number": 3,  "title": "3-бөлім. Тірі ағзалардың көптүрлілігі",                  "para_from": 6,  "para_to": 9},
    {"number": 4,  "title": "4-бөлім. Қоректену",                                     "para_from": 10, "para_to": 15},
    {"number": 5,  "title": "5-бөлім. Заттардың тасымалдануы",                         "para_from": 16, "para_to": 24},
    {"number": 6,  "title": "6-бөлім. Тыныс алу",                                     "para_from": 25, "para_to": 27},
    {"number": 7,  "title": "7-бөлім. Бөліп шығару",                                  "para_from": 28, "para_to": 30},
    {"number": 8,  "title": "8-бөлім. Қозғалыс. Биофизика",                           "para_from": 31, "para_to": 37},
    {"number": 9,  "title": "9-бөлім. Координация және реттелу",                       "para_from": 38, "para_to": 44},
    {"number": 10, "title": "10-бөлім. Көбею",                                         "para_from": 45, "para_to": 48},
    {"number": 11, "title": "11-бөлім. Өсу және даму",                                 "para_from": 49, "para_to": 49},
    {"number": 12, "title": "12-бөлім. Тұқымқуалаушылық және өзгергіштік заңдылықтары", "para_from": 50, "para_to": 53},
    {"number": 13, "title": "13-бөлім. Биосфера, экожүйе, популяция",                  "para_from": 54, "para_to": 58},
    {"number": 14, "title": "14-бөлім. Адам қызметінің қоршаған ортаға әсері",          "para_from": 59, "para_to": 60},
]

# ── Internal headings (NOT paragraph boundaries) ───────────────────────────
# All headings that are NOT §N. are internal in this textbook.
# The is_internal_heading function handles this via heuristics.

INTERNAL_HEADINGS = {
    # Task/assessment sections (appear at end of every §)
    "Білу және түсіну:",
    "Білу және түсіну",
    "Қолданылуы:",
    "Қолданылуы",
    "Талдау:",
    "Талдау",
    "Синтез:",
    "Синтез",
    "Бағалау:",
    "Бағалау",
    "Пікірталас:",
    "Пікірталас",
    # Preamble
    "АЛҒЫ СӨЗ",
    "Шартты белгілер:",
    "Шартты белгілер",
    "Сабақтың мақсаты",
    "МАЗМУНЫ",
    # Lab/experiment
    "Жұмыс барысы",
    # Watermarks
    "Все учебники Казахстана",
    "OKULYK",
}

# OCR artifacts to fix
OCR_FIXES = {
    "<br>": " ",
    "<br/>": " ",
    "<br />": " ",
    "．": ". ",
    "，": ", ",
    "：": ": ",
    "－": "-",
    "（": "(",
    "）": ")",
    "？": "?",
}

# Lines to skip entirely
SKIP_PATTERNS = [
    "Все учебники Казахстана",
    "OKULYK",
]


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class ParsedParagraph:
    title: str
    number: int       # § number
    raw_number: str   # Original string
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# ── Regex patterns ──────────────────────────────────────────────────────────

# Paragraph heading: multiple formats for §N:
#   "## §1. Title"       (standard h2)
#   "# §13. Title"       (h1, OCR variant)
#   "## § 60. Title"     (space after §)
#   "§6. Title"          (plain text, no heading marker)
RE_PARAGRAPH = re.compile(
    r"^(?:#{1,2}\s+)?§\s*(\d+(?:-\d+)?)[.．\s]+(.+)", re.IGNORECASE
)

# бөлім (chapter) heading — skip these as content markers
RE_BOLIM = re.compile(
    r"^#{0,2}\s*\d+-бөлім\b", re.IGNORECASE
)

# Stop markers — everything after these is skipped (lab practicum, glossary)
RE_STOP = re.compile(
    r"^#{0,2}\s*(ЗЕРТХАНАЛЫҚ ЖАТТЫҒУ\b|ТЕРМИНДЕРДІҢ ТУСІНДІРМЕ\b"
    r"|ТЕРМИНДЕРДІҢ ТҮСІНДІРМЕ\b|МАЗМУНЫ\b"
    r"|«Атамұра» мектеп\b)",
    re.IGNORECASE,
)

# Image reference in markdown
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)")

# Footnote references [^N]
RE_FOOTNOTE_REF = re.compile(r"\[\^(\d+)\]")

# Abstract block (Mathpix artifact)
RE_ABSTRACT = re.compile(r"^#{1,4}\s+Abstract", re.IGNORECASE)


# ── Helper functions ────────────────────────────────────────────────────────

def should_skip_line(line: str) -> bool:
    """Check if a line should be skipped entirely (watermark/ad)."""
    for pattern in SKIP_PATTERNS:
        if pattern in line:
            return True
    return False


def fix_ocr(text: str) -> str:
    """Fix known OCR artifacts in text."""
    for wrong, correct in OCR_FIXES.items():
        text = text.replace(wrong, correct)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def is_internal_heading(heading: str) -> bool:
    """Check if a heading is internal content (not a paragraph boundary).
    In this textbook, ALL non-§ headings are internal."""
    clean = heading.strip()

    # Exact match
    if clean in INTERNAL_HEADINGS:
        return True

    # Check with OCR-cleaned version
    clean_fixed = fix_ocr(clean)
    if clean_fixed in INTERNAL_HEADINGS:
        return True

    # Starts with known prefix
    for prefix in INTERNAL_HEADINGS:
        if clean.startswith(prefix) or clean_fixed.startswith(prefix):
            return True

    # Skip watermarks
    if should_skip_line(clean):
        return True

    # Heading that starts with image ref
    if clean.startswith("!["):
        return True

    # Heading that starts with $ (math formula)
    if clean.startswith("$"):
        return True

    # Heading that starts with a digit (task numbers, dates, image captions like "95-cypem")
    if clean and clean[0].isdigit():
        return True

    # Very long headings are usually content, not boundaries
    if len(clean) > 80:
        return True

    # Questions (contain ?)
    if "?" in clean or "？" in clean:
        return True

    # Single letter or very short (glossary letters, etc.)
    if len(clean) <= 3:
        return True

    # бөлім headings — chapter markers, not paragraphs
    if RE_BOLIM.match(clean) or RE_BOLIM.match("## " + clean):
        return True

    # CJK characters (OCR junk)
    if any(ord(c) > 0x3000 for c in clean):
        return True

    return False


def get_chapter_for_para(para_number: int) -> dict | None:
    """Find which chapter a paragraph belongs to based on § number."""
    for ch in CHAPTERS:
        if ch["para_from"] <= para_number <= ch["para_to"]:
            return ch
    return None


# ── Parser ──────────────────────────────────────────────────────────────────

def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    """Parse the MMD file into chapters and paragraphs."""
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    paragraphs: list[ParsedParagraph] = []
    current_paragraph: ParsedParagraph | None = None
    in_abstract = False
    in_preamble = True  # Before first §

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")

        # Skip watermark lines
        if should_skip_line(line):
            continue

        # Stop markers — everything after this is appendix
        if RE_STOP.match(line):
            break

        # Skip Abstract blocks (Mathpix artifact)
        if RE_ABSTRACT.match(line):
            in_abstract = True
            continue
        if in_abstract:
            if line.strip() == "" or line.startswith("#"):
                in_abstract = False
                if line.startswith("#"):
                    pass  # Fall through to heading detection
                else:
                    continue
            else:
                if current_paragraph is not None:
                    current_paragraph.content_lines.append(line)
                continue

        # Detect § paragraph heading (any heading format or plain text)
        m = RE_PARAGRAPH.match(line)
        if m:
            in_preamble = False
            raw_num = m.group(1)
            para_num = int(raw_num.split("-")[0])
            para_title = m.group(2).strip()
            para_title = fix_ocr(para_title)

            current_paragraph = ParsedParagraph(
                title=para_title,
                number=para_num,
                raw_number=raw_num,
            )
            paragraphs.append(current_paragraph)
            continue

        # Skip preamble (before first §)
        if in_preamble:
            continue

        # бөлім headings as plain text or with ## — skip as content boundary markers
        if RE_BOLIM.match(line):
            continue

        # All other headings — treat as internal content
        heading_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if heading_match:
            heading_text = heading_match.group(2).strip()

            # бөлім headings with ## — skip
            if RE_BOLIM.match(line):
                continue

            # Everything else is internal content in this textbook
            if current_paragraph is not None:
                current_paragraph.content_lines.append(line)
            continue

        # Accumulate content lines
        if current_paragraph is not None:
            current_paragraph.content_lines.append(line)

    # Organize paragraphs into chapters
    chapter_map: dict[int, ParsedChapter] = {}
    for ch_info in CHAPTERS:
        chapter_map[ch_info["number"]] = ParsedChapter(
            title=ch_info["title"],
            number=ch_info["number"],
        )

    for para in paragraphs:
        ch_info = get_chapter_for_para(para.number)
        if ch_info:
            chapter_map[ch_info["number"]].paragraphs.append(para)
        else:
            print(f"  WARNING: §{para.number} ({para.title[:40]}) doesn't belong to any chapter!")

    return [ch for ch in sorted(chapter_map.values(), key=lambda c: c.number) if ch.paragraphs]


# ── Content conversion ──────────────────────────────────────────────────────

def md_lines_to_html(lines: list[str], textbook_id: int) -> str:
    """Convert markdown content lines to HTML with embedded LaTeX."""
    if not lines:
        return ""

    content = "\n".join(lines)

    # Replace image references
    content = RE_IMAGE.sub(
        lambda m: (
            f'<img src="/uploads/textbook-images/{textbook_id}/{m.group(2)}" '
            f'alt="{m.group(1)}" style="display:block;margin:1rem auto;max-width:100%" />'
        ),
        content,
    )

    # Remove footnote markers [^0], [^1] etc.
    content = RE_FOOTNOTE_REF.sub("", content)

    # Protect LaTeX from processing
    latex_blocks: list[str] = []

    def save_latex(match):
        idx = len(latex_blocks)
        latex_blocks.append(match.group(0))
        return f"__LATEX_{idx}__"

    content = re.sub(r"\$\$[\s\S]*?\$\$", save_latex, content)
    content = re.sub(r"\$[^$\n]+?\$", save_latex, content)

    # Simple markdown to HTML conversion
    html_parts: list[str] = []
    in_table = False
    table_rows: list[str] = []
    paragraph_lines: list[str] = []
    in_list = False
    list_items: list[str] = []

    def flush_paragraph():
        nonlocal paragraph_lines
        if paragraph_lines:
            text = " ".join(paragraph_lines)
            if text.strip():
                html_parts.append(f"<p>{text.strip()}</p>")
            paragraph_lines = []

    def flush_table():
        nonlocal in_table, table_rows
        if table_rows:
            html_parts.append(
                "<table style='width:100%;border-collapse:collapse;margin:1rem 0'>"
            )
            for i, row in enumerate(table_rows):
                cells = [c.strip() for c in row.strip("|").split("|")]
                if all(re.match(r"^:?-+:?$", c) for c in cells):
                    continue
                tag = "th" if i == 0 else "td"
                html_parts.append("<tr>")
                for cell in cells:
                    html_parts.append(
                        f"<{tag} style='border:1px solid #d1d5db;padding:0.5rem 0.75rem'>"
                        f"{cell}</{tag}>"
                    )
                html_parts.append("</tr>")
            html_parts.append("</table>")
            table_rows = []
        in_table = False

    def flush_list():
        nonlocal in_list, list_items
        if list_items:
            html_parts.append("<ul style='margin:0.5rem 0;padding-left:1.5rem'>")
            for item in list_items:
                html_parts.append(f"<li>{item}</li>")
            html_parts.append("</ul>")
            list_items = []
        in_list = False

    for raw_line in content.split("\n"):
        line = raw_line.rstrip()

        # Skip watermark lines in content
        if should_skip_line(line):
            continue

        # Blank line → flush
        if not line.strip():
            if in_table:
                flush_table()
            if in_list:
                flush_list()
            flush_paragraph()
            continue

        # Table row
        if line.strip().startswith("|"):
            if not in_table:
                flush_paragraph()
                if in_list:
                    flush_list()
                in_table = True
            table_rows.append(line)
            continue
        elif in_table:
            flush_table()

        # List item
        if line.strip().startswith("- "):
            if not in_list:
                flush_paragraph()
                in_list = True
            list_items.append(line.strip()[2:])
            continue
        elif in_list:
            flush_list()

        # Heading (## → h3, ### → h4)
        heading_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if heading_match:
            flush_paragraph()
            level = min(len(heading_match.group(1)) + 1, 6)
            heading_text = heading_match.group(2).strip()
            html_parts.append(f"<h{level}>{heading_text}</h{level}>")
            continue

        # Blockquote
        if line.startswith("> "):
            flush_paragraph()
            html_parts.append(
                f"<blockquote style='border-left:4px solid #93c5fd;padding-left:1rem;"
                f"margin:0.75rem 0;font-style:italic'>{line[2:]}</blockquote>"
            )
            continue

        # Image (already converted above)
        if line.strip().startswith("<img "):
            flush_paragraph()
            html_parts.append(
                f'<div style="margin:1rem 0;text-align:center">{line.strip()}</div>'
            )
            continue

        # Task line: "N. Text" (numbered items)
        task_match = re.match(r"^(\d+)\.\s+(.+)", line.strip())
        if task_match:
            flush_paragraph()
            task_num = task_match.group(1)
            task_text = task_match.group(2)
            html_parts.append(
                f'<div style="margin-top:0.75rem;margin-bottom:0.25rem">'
                f'<strong>{task_num}.</strong> {task_text}</div>'
            )
            continue

        # Subtask line: "N) text"
        subtask_match = re.match(r"^(\d+)\)\s+(.+)", line.strip())
        if subtask_match:
            flush_paragraph()
            sub_num = subtask_match.group(1)
            sub_text = subtask_match.group(2)
            html_parts.append(
                f'<div style="margin-left:1.5rem">{sub_num}) {sub_text}</div>'
            )
            continue

        # Subtask line: "a) text", "б) text" etc.
        subtask_match2 = re.match(r"^([а-яa-z])\)\s+(.+)", line.strip())
        if subtask_match2:
            flush_paragraph()
            sub_letter = subtask_match2.group(1)
            sub_text = subtask_match2.group(2)
            html_parts.append(
                f'<div style="margin-left:1.5rem">{sub_letter}) {sub_text}</div>'
            )
            continue

        # Regular text
        paragraph_lines.append(line)

    # Flush remaining
    if in_table:
        flush_table()
    if in_list:
        flush_list()
    flush_paragraph()

    html = "\n".join(html_parts)

    # Apply inline formatting
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", html)

    # Restore LaTeX
    for idx, latex in enumerate(latex_blocks):
        html = html.replace(f"__LATEX_{idx}__", latex)

    return html.strip()


# ── SQL helpers ─────────────────────────────────────────────────────────────

def escape_sql(s: str) -> str:
    """Escape string for SQL single-quote literals."""
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


# ── Statistics ──────────────────────────────────────────────────────────────

def print_parse_stats(chapters: list[ParsedChapter]):
    """Print parsing statistics."""
    total_paragraphs = 0
    total_lines = 0
    print("\n--- Parsing Results ---")
    for ch in chapters:
        ch_lines = sum(len(p.content_lines) for p in ch.paragraphs)
        total_paragraphs += len(ch.paragraphs)
        total_lines += ch_lines
        ch_title = ch.title[:70] + ("..." if len(ch.title) > 70 else "")
        print(f"\n  Chapter {ch.number}: {ch_title}")
        print(f"    Paragraphs: {len(ch.paragraphs)}, Content lines: {ch_lines}")
        for p in ch.paragraphs:
            p_title = p.title[:55] + ("..." if len(p.title) > 55 else "")
            print(
                f"      §{p.raw_number:>5}. {p_title:<58} "
                f"({len(p.content_lines):>4} lines)"
            )
    print(
        f"\n  Total: {len(chapters)} chapters, {total_paragraphs} paragraphs, "
        f"{total_lines} content lines"
    )
    print("---")


# ── SQL generation ──────────────────────────────────────────────────────────

def generate_sql(chapters: list[ParsedChapter], output_path: Path):
    """Generate a SQL file for importing via psql."""
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE id = {TEXTBOOK_ID} AND is_deleted = false)"
    )

    sql_lines = [
        f"-- Биология 8-сынып Textbook Import (Kazakh)",
        f"-- Generated by load_textbook_51.py",
        "",
        "BEGIN;",
        "",
    ]

    total_paragraphs = 0

    for ch_order, chapter in enumerate(chapters, 1):
        chapter_title_esc = escape_sql(chapter.title)
        chapter_where = (
            f"(SELECT id FROM chapters WHERE textbook_id = {textbook_where}"
            f" AND number = {chapter.number} AND is_deleted = false LIMIT 1)"
        )

        sql_lines.append(f"-- Chapter {chapter.number}: {chapter.title[:60]}")
        sql_lines.append(
            f'INSERT INTO chapters (textbook_id, title, number, "order", is_deleted)'
        )
        sql_lines.append(
            f"SELECT {textbook_where}, {chapter_title_esc}, {chapter.number}, {ch_order}, false"
        )
        sql_lines.append(f"WHERE NOT EXISTS (")
        sql_lines.append(
            f"    SELECT 1 FROM chapters WHERE textbook_id = {textbook_where}"
        )
        sql_lines.append(
            f"    AND number = {chapter.number} AND is_deleted = false"
        )
        sql_lines.append(f");")
        sql_lines.append("")

        for p_order, para in enumerate(chapter.paragraphs, 1):
            html_content = md_lines_to_html(para.content_lines, TEXTBOOK_ID)
            source_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]

            content_esc = escape_sql(html_content)
            title_esc = escape_sql(para.title)

            para_where = (
                f"(SELECT id FROM paragraphs WHERE chapter_id = {chapter_where}"
                f" AND number = {para.number} AND is_deleted = false LIMIT 1)"
            )

            sql_lines.append(f"-- §{para.raw_number}: {para.title[:50]}")
            sql_lines.append(
                f'INSERT INTO paragraphs (chapter_id, title, number, "order", content, is_deleted)'
            )
            sql_lines.append(
                f"SELECT {chapter_where}, {title_esc}, {para.number}, {p_order},"
            )
            sql_lines.append(f"{content_esc}, false")
            sql_lines.append(f"WHERE NOT EXISTS (")
            sql_lines.append(
                f"    SELECT 1 FROM paragraphs WHERE chapter_id = {chapter_where}"
            )
            sql_lines.append(
                f"    AND number = {para.number} AND is_deleted = false"
            )
            sql_lines.append(f");")
            sql_lines.append("")

            # ParagraphContent for 'kk'
            sql_lines.append(f"INSERT INTO paragraph_contents (")
            sql_lines.append(f"    paragraph_id, language, explain_text,")
            sql_lines.append(f"    source_hash, status_explain,")
            sql_lines.append(f"    status_audio, status_slides, status_video, status_cards")
            sql_lines.append(f") SELECT")
            sql_lines.append(f"    {para_where}, '{LANGUAGE}',")
            sql_lines.append(f"{content_esc},")
            sql_lines.append(f"    {escape_sql(source_hash)}, 'ready',")
            sql_lines.append(f"    'empty', 'empty', 'empty', 'empty'")
            sql_lines.append(f"WHERE NOT EXISTS (")
            sql_lines.append(f"    SELECT 1 FROM paragraph_contents")
            sql_lines.append(
                f"    WHERE paragraph_id = {para_where} AND language = '{LANGUAGE}'"
            )
            sql_lines.append(f");")
            sql_lines.append("")
            total_paragraphs += 1

    sql_lines.append("COMMIT;")
    sql_lines.append(f"-- Stats: {len(chapters)} chapters, {total_paragraphs} paragraphs")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))

    print(f"\n  Generated SQL: {output_path}")
    print(f"  Chapters: {len(chapters)}, Paragraphs: {total_paragraphs}")
    print(f"\n  To import:")
    print(f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/import.sql")
    print(f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/import.sql")


def generate_update_sql(chapters: list[ParsedChapter], output_path: Path):
    """Generate SQL UPDATE statements to refresh content in existing records."""
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE id = {TEXTBOOK_ID} AND is_deleted = false)"
    )

    sql_lines = [
        "-- Биология 8-сынып Content UPDATE",
        "-- Regenerated HTML with improved formatting",
        "",
        "BEGIN;",
        "",
    ]

    total = 0
    for chapter in chapters:
        chapter_where = (
            f"(SELECT id FROM chapters WHERE textbook_id = {textbook_where}"
            f" AND number = {chapter.number} AND is_deleted = false LIMIT 1)"
        )

        for para in chapter.paragraphs:
            html_content = md_lines_to_html(para.content_lines, TEXTBOOK_ID)
            content_esc = escape_sql(html_content)
            source_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]

            para_where = (
                f"(SELECT id FROM paragraphs WHERE chapter_id = {chapter_where}"
                f" AND number = {para.number} AND is_deleted = false LIMIT 1)"
            )

            sql_lines.append(f"-- Update §{para.raw_number}: {para.title[:50]}")
            sql_lines.append(f"UPDATE paragraphs SET content = {content_esc}")
            sql_lines.append(f"WHERE id = {para_where};")
            sql_lines.append("")
            sql_lines.append(
                f"UPDATE paragraph_contents SET explain_text = {content_esc},"
            )
            sql_lines.append(f"    source_hash = {escape_sql(source_hash)}")
            sql_lines.append(
                f"WHERE paragraph_id = {para_where} AND language = '{LANGUAGE}';"
            )
            sql_lines.append("")
            total += 1

    sql_lines.append("COMMIT;")
    sql_lines.append(f"-- Updated {total} paragraphs")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))

    print(f"\n  Generated UPDATE SQL: {output_path}")
    print(f"  Paragraphs to update: {total}")
    print(f"\n  To apply:")
    print(f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/update.sql")
    print(f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/update.sql")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Load Биология 8-сынып textbook into AI Mentor database"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse only, no output"
    )
    parser.add_argument(
        "--generate-sql",
        type=str,
        metavar="FILE",
        help="Generate SQL file for import",
    )
    parser.add_argument(
        "--update-content",
        type=str,
        metavar="FILE",
        help="Generate SQL UPDATE file to refresh content",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  Биология 8-сынып — Textbook Import")
    print("=" * 70)

    # 1. Parse MMD file
    print(f"\nStep 1: Parsing {MD_FILE.name}...")
    if not MD_FILE.exists():
        print(f"  ERROR: File not found: {MD_FILE}")
        sys.exit(1)

    chapters = parse_textbook(MD_FILE)
    print_parse_stats(chapters)

    if args.dry_run:
        print("\n  [DRY RUN] No output generated.")
        return

    if args.generate_sql:
        print(f"\nStep 2: Generating SQL...")
        generate_sql(chapters, Path(args.generate_sql))
        return

    if args.update_content:
        print(f"\nStep 2: Generating UPDATE SQL...")
        generate_update_sql(chapters, Path(args.update_content))
        return

    print("\n  No action specified. Use --dry-run, --generate-sql, or --update-content.")


if __name__ == "__main__":
    main()
