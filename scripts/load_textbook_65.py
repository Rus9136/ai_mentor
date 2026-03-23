#!/usr/bin/env python3
"""
Load 'История Казахстана 9-класс' (1945 — настоящее время) into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='ru'.

This is a HISTORY textbook — no exercises, no A/B/C difficulty levels.
Has 8 Разделов (chapters) and 46 paragraphs (§1-60 with compound numbering).
Special case: §19-20 has NO heading in the file (implicit paragraph).
Some § headings appear as plain text inside Abstract blocks.
Uses fullwidth characters in some places (OCR artifact).

Usage:
    python scripts/load_textbook_65.py --dry-run           # Parse only
    python scripts/load_textbook_65.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_65.py --update-content FILE # Update SQL
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

TEXTBOOK_ID = 65
TEXTBOOK_TITLE = "История Казахстана 9-класс"
SUBJECT_CODE = "history_kz"
GRADE_LEVEL = 9
AUTHORS = "Ускембаев К., Сактаганова З., Зуева Л."
PUBLISHER = "Мектеп"
YEAR = 2025
ISBN = ""
LANGUAGE = "ru"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "65" / "textbook_65.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "65"

# Chapter mapping: § number ranges → chapter info (from TOC / Содержание)
CHAPTERS = [
    {
        "number": 1,
        "title": "Раздел I. Казахстан в послевоенные годы (1946-1953 гг.)",
        "para_from": 1,
        "para_to": 6,
    },
    {
        "number": 2,
        "title": "Раздел II. Казахстан в годы хрущёвской оттепели (1953-1964 гг.)",
        "para_from": 7,
        "para_to": 14,
    },
    {
        "number": 3,
        "title": "Раздел III. Казахстан в годы застоя (1965-1985 гг.)",
        "para_from": 15,
        "para_to": 23,
    },
    {
        "number": 4,
        "title": "Раздел IV. Культура Советского Казахстана (1946-1985 гг.)",
        "para_from": 24,
        "para_to": 28,
    },
    {
        "number": 5,
        "title": "Раздел V. Казахстан в годы перестройки (1986-1991 гг.)",
        "para_from": 29,
        "para_to": 35,
    },
    {
        "number": 6,
        "title": "Раздел VI. Возрождение государственности Казахстана (1991-1996 гг.)",
        "para_from": 36,
        "para_to": 46,
    },
    {
        "number": 7,
        "title": "Раздел VII. Развитие независимого Казахстана (с 1997 года до настоящего времени)",
        "para_from": 47,
        "para_to": 56,
    },
    {
        "number": 8,
        "title": "Раздел VIII. Культура современного Казахстана (с 1991 года до настоящего времени)",
        "para_from": 57,
        "para_to": 60,
    },
]

# Headings that are internal content within a paragraph (NOT paragraph boundaries)
INTERNAL_HEADINGS = {
    # Lesson structure
    "Сегодня на уроке:", "Сегодня на уроке",
    "Сегодняна уроке:", "Сегодняна уроке",
    "Ключевые слова", "Ключевые слова:",
    "Ответьте на вопросы:", "Ответьте на вопросы",
    "Ответьте на копросы:", "Ответьте на копросы",
    "Задания:", "Задания", "Задание:", "Задание",
    "Работа с таблицей:", "Работа с таблицей.", "Работа с таблицей",
    # Chapter conclusions
    "ЗАКЛЮЧЕНИЕ",
    # Sub-topic headings (visual separators between §§, NOT paragraph boundaries)
    "Социально-экономическое развитие Казахской ССР в послевоенные годы",
    "Военно-промышленный комплекс в Казахстане",
    "Общественно-политическое развитие Казахстана в период хрущевской оттепели",
    "Казахстан в эпоху освоения целины",
    "Сырьевая направленность экономики Казахской ССР",
    "Демографические процессы в годы застоя и урбанизация",
    "Достижения казахстанских ученых в 40-80-е годы XX в.",
    "Развитие литературы и искусства в 40-80-е годы XX в.",
    "Казахстан на начальном этапе перестройки",
    "Декабрьские события 1986 г. в Казахстане",
    "Демократические процессы в Казахстане в годы перестройки",
    "Провозглашение независимости Казахстана",
    "Н. А. Назарбаев - Первый Президент Республики Казахстан",
    "Государственное строительствов первые годы независимости",
    "Казахстан - субъект международного права",
    "Социально-демографические процессы в первые годы независимости",
    'Стратегия "Казахстан-2030" - новый этап в развитии страны',
    "Социальное развитие Казахстана с 1997 г.",
    "Казахстан в системе международных отношений",
    "Столица независимого Казахстана",
    'Стратегия "Казахстан-2050"',
    "Приоритетные направления развития Казахстана на современном этапе",
    "Развитие образования и науки в годы независимости",
    "Развитие культуры независимого Казахстана",
    "Роль религии в современном казахстанском обществе",
    'Национальная идея "Мәңгілік Ел"',
    # Preamble
    "Введение",
    "Уважаемые школьники!",
    "Условные обозначения",
    # Sub-section headings inside paragraphs
    "МӘҢГІЛІК ЕЛ",
    "5 президентских реформ:",
    "Категории для участия в конкурсе \"Болашак\":",
    # Watermarks
    "Все учебники Казахстана ищите на файтах OKULYK.COM и OKULYK.KZ",
    "Все учебники Казахстана ищите на сайтах OKULYK.COM и OKULYK.KZ",
    # End of book
    "Даты наиболее важных исторических событий",
    "Литература",
    "СОДЕРЖАНИЕ",
}

# OCR artifacts to fix in paragraph titles
OCR_FIXES = {
    "<br>": " ",
    "<br/>": " ",
    "<br />": " ",
    "．": ".",
    "：": ":",
    "－": "-",
    "Сегодняна": "Сегодня на",
}

# Lines/headings to skip entirely (watermarks, ads)
SKIP_PATTERNS = [
    "Все учебники Казахстана",
    "OKULYK",
    "Книга предоставлена исключительно в образовательных целях",
]

# Fullwidth → ASCII character mapping
FULLWIDTH_MAP = {
    "．": ".",
    "：": ":",
    "－": "-",
    "，": ",",
    "（": "(",
    "）": ")",
    "；": ";",
    "＂": '"',
}

# §19-20 has no heading in the file. Its content starts after the definitions
# at the end of §17-18 with this text (mid-sentence due to OCR page break).
IMPLICIT_PARA_19_MARKER = "решала, какие вопросы рассматривать"
IMPLICIT_PARA_19_TITLE = "Особенности общественно-политической жизни в Казахстане в 1965-1985 гг."


# ── Data classes ────────────────────────────────────────────────────────────


@dataclass
class ParsedParagraph:
    title: str
    number: int       # First § number (e.g., 1 for "§ 1-2")
    raw_number: str   # Original string (e.g., "1-2")
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# ── Regex patterns ──────────────────────────────────────────────────────────

# Paragraph heading as markdown: "## § 1.", "# § 5-6.", "## §1-2.", "## § 29 - 30."
RE_PARAGRAPH_HEADING = re.compile(
    r"^#{1,2}\s+§\s*(\d+(?:\s*[－\-]\s*\d+)?)[.\s．]+(.+)", re.IGNORECASE
)

# Paragraph as plain text (no # prefix): "§7. Title", "§10-11. Title"
RE_PARAGRAPH_TEXT = re.compile(
    r"^§\s*(\d+(?:\s*[－\-]\s*\d+)?)[.\s．]+(.+)"
)

# Stop markers — everything after these is skipped
# NOTE: "Литература" requires heading prefix AND must be standalone (no trailing text)
# because "Литература и искусство..." appears as regular content in §27-28
RE_STOP = re.compile(
    r"^#{1,2}\s+(Даты наиболее важных\b|Литература\s*$|СОДЕРЖАНИЕ\b)",
    re.IGNORECASE,
)

# Image reference in markdown
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)")

# Footnote references [^N]
RE_FOOTNOTE_REF = re.compile(r"\[\^(\d+)\]")

# Abstract block (Mathpix artifact)
RE_ABSTRACT = re.compile(r"^#{1,4}\s+Abstract", re.IGNORECASE)


# ── Helper functions ────────────────────────────────────────────────────────


def normalize_fullwidth(text: str) -> str:
    """Replace fullwidth characters with ASCII equivalents."""
    for fw, ascii_char in FULLWIDTH_MAP.items():
        text = text.replace(fw, ascii_char)
    return text


def should_skip_line(line: str) -> bool:
    """Check if a line should be skipped entirely (watermark/ad)."""
    for pattern in SKIP_PATTERNS:
        if pattern in line:
            return True
    return False


def fix_ocr(text: str) -> str:
    """Fix known OCR artifacts in text."""
    text = normalize_fullwidth(text)
    for wrong, correct in OCR_FIXES.items():
        text = text.replace(wrong, correct)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def is_internal_heading(heading: str) -> bool:
    """Check if a heading is internal content (not a paragraph boundary)."""
    clean = heading.strip()

    # Exact match
    if clean in INTERNAL_HEADINGS:
        return True

    # Starts with known prefix
    for prefix in INTERNAL_HEADINGS:
        if clean.startswith(prefix):
            return True

    # Skip watermarks
    if should_skip_line(clean):
        return True

    # "Раздел" headings (chapter-level markers)
    if "раздел" in clean.lower():
        return True

    # "Выполните задание" prefix
    if clean.startswith("Выполните задание"):
        return True

    # Heading that starts with image ref
    if clean.startswith("!["):
        return True

    # Heading that starts with $ (math formula)
    if clean.startswith("$"):
        return True

    # Heading that starts with a digit (task numbers, dates)
    if clean and clean[0].isdigit():
        return True

    # Very long headings are usually content, not boundaries
    if len(clean) > 80:
        return True

    # Questions (contain ?)
    if "?" in clean:
        return True

    # Single word or very short headings that are just formatting
    if len(clean) <= 3:
        return True

    # CJK / OCR junk characters
    if any(ord(c) > 0x3000 for c in clean):
        return True

    # h1 sub-section headings with <br> (OCR artifact in multiline headings)
    if "<br>" in clean.lower():
        return True

    # Parenthetical headings like "(B)" — OCR artifact
    if clean.startswith("(") and len(clean) <= 5:
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
    stopped = False
    in_abstract = False

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")

        # Skip watermark lines
        if should_skip_line(line):
            continue

        # Normalize fullwidth characters for matching
        line_norm = normalize_fullwidth(line)

        # Stop markers — everything after this is appendix
        if RE_STOP.match(line_norm):
            stopped = True
            break

        # Skip Abstract blocks (Mathpix artifact)
        if RE_ABSTRACT.match(line):
            in_abstract = True
            continue
        if in_abstract:
            if line.strip() == "":
                in_abstract = False
                continue
            if line.startswith("#"):
                in_abstract = False
                # Fall through to heading detection below
            else:
                # Abstract content — check if it contains a § reference
                m_text = RE_PARAGRAPH_TEXT.match(normalize_fullwidth(line.strip()))
                if m_text:
                    raw_num = normalize_fullwidth(m_text.group(1))
                    raw_num = re.sub(r"\s+", "", raw_num)  # "29 - 30" → "29-30"
                    para_num = int(raw_num.split("-")[0])
                    para_title = fix_ocr(m_text.group(2).strip())
                    current_paragraph = ParsedParagraph(
                        title=para_title,
                        number=para_num,
                        raw_number=raw_num,
                    )
                    paragraphs.append(current_paragraph)
                    in_abstract = False
                    continue
                # Regular abstract content — add to current paragraph
                if current_paragraph is not None:
                    current_paragraph.content_lines.append(line)
                continue

        # Detect § paragraph heading (markdown format: ## §N.)
        m = RE_PARAGRAPH_HEADING.match(line_norm)
        if m:
            raw_num = normalize_fullwidth(m.group(1))
            raw_num = re.sub(r"\s+", "", raw_num)  # "29 - 30" → "29-30"
            para_num = int(raw_num.split("-")[0])
            para_title = fix_ocr(m.group(2).strip())
            current_paragraph = ParsedParagraph(
                title=para_title,
                number=para_num,
                raw_number=raw_num,
            )
            paragraphs.append(current_paragraph)
            continue

        # Detect § paragraph as plain text (no # prefix)
        m_text = RE_PARAGRAPH_TEXT.match(line_norm.strip())
        if m_text:
            raw_num = normalize_fullwidth(m_text.group(1))
            raw_num = re.sub(r"\s+", "", raw_num)
            para_num = int(raw_num.split("-")[0])
            para_title = fix_ocr(m_text.group(2).strip())
            current_paragraph = ParsedParagraph(
                title=para_title,
                number=para_num,
                raw_number=raw_num,
            )
            paragraphs.append(current_paragraph)
            continue

        # All other headings — check if internal
        heading_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if heading_match:
            heading_text = heading_match.group(2).strip()
            if is_internal_heading(heading_text):
                # Internal heading — include as content
                if current_paragraph is not None:
                    current_paragraph.content_lines.append(line)
                continue
            else:
                # Unknown heading before any § — skip (preamble)
                if current_paragraph is None:
                    continue
                # Unknown heading after a § — include as content
                current_paragraph.content_lines.append(line)
                continue

        # Accumulate content lines
        if current_paragraph is not None:
            current_paragraph.content_lines.append(line)

    # ── Post-processing: split §19-20 from §17-18 ──
    # §19-20 has no heading in the file; its content was appended to §17-18.
    # We detect it by the marker text and split the content.
    para_17 = None
    for p in paragraphs:
        if p.number == 17:
            para_17 = p
            break

    if para_17 is not None:
        split_idx = None
        for i, content_line in enumerate(para_17.content_lines):
            if IMPLICIT_PARA_19_MARKER in content_line:
                split_idx = i
                break

        if split_idx is not None:
            # Create §19-20 from the split content
            para_19 = ParsedParagraph(
                title=IMPLICIT_PARA_19_TITLE,
                number=19,
                raw_number="19-20",
                content_lines=para_17.content_lines[split_idx:],
            )
            # Trim §17-18's content
            para_17.content_lines = para_17.content_lines[:split_idx]

            # Insert §19-20 right after §17-18
            idx_17 = paragraphs.index(para_17)
            paragraphs.insert(idx_17 + 1, para_19)
            print(f"  INFO: Split §19-20 from §17-18 at content line {split_idx}")
        else:
            print(f"  WARNING: Could not find §19-20 split marker in §17-18 content!")

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

        # Task line: "N. Text" (numbered items in exercises/questions)
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

    lines = [
        f"-- История Казахстана 9-класс Textbook Import (Russian)",
        f"-- Generated by load_textbook_65.py",
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

        lines.append(f"-- Chapter {chapter.number}: {chapter.title[:60]}")
        lines.append(
            f'INSERT INTO chapters (textbook_id, title, number, "order", is_deleted)'
        )
        lines.append(
            f"SELECT {textbook_where}, {chapter_title_esc}, {chapter.number}, {ch_order}, false"
        )
        lines.append(f"WHERE NOT EXISTS (")
        lines.append(
            f"    SELECT 1 FROM chapters WHERE textbook_id = {textbook_where}"
        )
        lines.append(
            f"    AND number = {chapter.number} AND is_deleted = false"
        )
        lines.append(f");")
        lines.append("")

        for p_order, para in enumerate(chapter.paragraphs, 1):
            html_content = md_lines_to_html(para.content_lines, TEXTBOOK_ID)
            source_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]

            content_esc = escape_sql(html_content)
            title_esc = escape_sql(para.title)

            para_where = (
                f"(SELECT id FROM paragraphs WHERE chapter_id = {chapter_where}"
                f" AND number = {para.number} AND is_deleted = false LIMIT 1)"
            )

            lines.append(f"-- §{para.raw_number}: {para.title[:50]}")
            lines.append(
                f'INSERT INTO paragraphs (chapter_id, title, number, "order", content, is_deleted)'
            )
            lines.append(
                f"SELECT {chapter_where}, {title_esc}, {para.number}, {p_order},"
            )
            lines.append(f"{content_esc}, false")
            lines.append(f"WHERE NOT EXISTS (")
            lines.append(
                f"    SELECT 1 FROM paragraphs WHERE chapter_id = {chapter_where}"
            )
            lines.append(
                f"    AND number = {para.number} AND is_deleted = false"
            )
            lines.append(f");")
            lines.append("")

            # ParagraphContent for 'ru'
            lines.append(f"INSERT INTO paragraph_contents (")
            lines.append(f"    paragraph_id, language, explain_text,")
            lines.append(f"    source_hash, status_explain,")
            lines.append(f"    status_audio, status_slides, status_video, status_cards")
            lines.append(f") SELECT")
            lines.append(f"    {para_where}, '{LANGUAGE}',")
            lines.append(f"{content_esc},")
            lines.append(f"    {escape_sql(source_hash)}, 'ready',")
            lines.append(f"    'empty', 'empty', 'empty', 'empty'")
            lines.append(f"WHERE NOT EXISTS (")
            lines.append(f"    SELECT 1 FROM paragraph_contents")
            lines.append(
                f"    WHERE paragraph_id = {para_where} AND language = '{LANGUAGE}'"
            )
            lines.append(f");")
            lines.append("")
            total_paragraphs += 1

    lines.append("COMMIT;")
    lines.append(f"-- Stats: {len(chapters)} chapters, {total_paragraphs} paragraphs")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  Generated SQL: {output_path}")
    print(f"  Chapters: {len(chapters)}, Paragraphs: {total_paragraphs}")
    print(f"\n  To import:")
    print(
        f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/import.sql"
    )
    print(
        f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/import.sql"
    )


def generate_update_sql(chapters: list[ParsedChapter], output_path: Path):
    """Generate SQL UPDATE statements to refresh content in existing records."""
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE id = {TEXTBOOK_ID} AND is_deleted = false)"
    )

    lines = [
        "-- История Казахстана 9-класс Content UPDATE",
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

            lines.append(f"-- Update §{para.raw_number}: {para.title[:50]}")
            lines.append(f"UPDATE paragraphs SET content = {content_esc}")
            lines.append(f"WHERE id = {para_where};")
            lines.append("")
            lines.append(
                f"UPDATE paragraph_contents SET explain_text = {content_esc},"
            )
            lines.append(f"    source_hash = {escape_sql(source_hash)}")
            lines.append(
                f"WHERE paragraph_id = {para_where} AND language = '{LANGUAGE}';"
            )
            lines.append("")
            total += 1

    lines.append("COMMIT;")
    lines.append(f"-- Updated {total} paragraphs")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  Generated UPDATE SQL: {output_path}")
    print(f"  Paragraphs to update: {total}")
    print(f"\n  To apply:")
    print(
        f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/update.sql"
    )
    print(
        f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/update.sql"
    )


# ── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Load История Казахстана 9-класс textbook into AI Mentor database"
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
    print("  История Казахстана 9-класс (1945 — настоящее время) — Textbook Import")
    print("=" * 70)

    # 1. Parse MMD file
    print(f"\nStep 1: Parsing {MD_FILE.name}...")
    if not MD_FILE.exists():
        print(f"  ERROR: File not found: {MD_FILE}")
        sys.exit(1)

    chapters = parse_textbook(MD_FILE)
    print_parse_stats(chapters)

    # 2. Validate
    expected_paras = 46
    total = sum(len(ch.paragraphs) for ch in chapters)
    if total != expected_paras:
        print(f"\n  ⚠ WARNING: Expected {expected_paras} paragraphs, got {total}")
    else:
        print(f"\n  ✓ Paragraph count matches expected ({expected_paras})")

    # Check for empty paragraphs
    for ch in chapters:
        for p in ch.paragraphs:
            if len(p.content_lines) < 5:
                print(f"  ⚠ WARNING: §{p.raw_number} has very few content lines ({len(p.content_lines)})")

    if args.dry_run:
        print("\n  Dry run complete. No files written.")
        return

    if args.generate_sql:
        generate_sql(chapters, Path(args.generate_sql))
        return

    if args.update_content:
        generate_update_sql(chapters, Path(args.update_content))
        return

    print("\n  No action specified. Use --dry-run, --generate-sql, or --update-content")


if __name__ == "__main__":
    main()
