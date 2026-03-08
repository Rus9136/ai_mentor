#!/usr/bin/env python3
"""
Load 'Алгебра және анализ бастамалары 11-сынып 2-бөлім' into the AI Mentor database.

This textbook uses ## X.Y. format for paragraph headings (no § symbol).
Exercise numbers also use X.Y. format (continuous per chapter).
Paragraphs are identified by a whitelist of known IDs from the TOC.
IX бөлім is a review chapter with exercises only (9.1-9.10).

Usage:
    python scripts/load_textbook_41.py --dry-run                # Parse only
    python scripts/load_textbook_41.py --generate-sql FILE      # Generate SQL
    python scripts/load_textbook_41.py --exercises FILE          # Exercises SQL
    python scripts/load_textbook_41.py --update-content FILE     # Update existing content
"""
import re
import sys
import os
import json
import hashlib
import argparse
from pathlib import Path
from dataclasses import dataclass, field

# -- Path setup ---------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# -- Constants -----------------------------------------------------------------

TEXTBOOK_ID = 41
TEXTBOOK_TITLE = "Алгебра және анализ бастамалары 11-сынып 2-бөлім"
SUBJECT_CODE = "algebra"
GRADE_LEVEL = 11
AUTHORS = "Шыныбеков Е.Н., Шыныбеков Д.Э., Жумбаева Р.Н."
PUBLISHER = "Атамура"
YEAR = 2020
ISBN = ""
LANGUAGE = "kk"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "41" / "textbook_41.mmd"
IMAGES_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "41"

# -- Chapter definitions ------------------------------------------------------

CHAPTER_DEFS = [
    (1, "Көрсеткіштік және логарифмдік функциялар"),
    (2, "Көрсеткіштік және логарифмдік теңдеулер мен теңсіздіктер"),
    (3, "Дифференциалдық теңдеулер"),
    (4, "Орта мектеп курсын қайталауға арналған есептер"),
]

# -- Known paragraph identifiers (from TOC) -----------------------------------

KNOWN_PARAGRAPHS = {
    "6.1": "Көрсеткіштік функция, оның қасиеттері мен графигі",
    "6.2": "Санның логарифмі және оның қасиеттері",
    "6.3": "Логарифмдік функция, оның қасиеттері мен графигі",
    "6.4": "Көрсеткіштік функцияның туындысы және интегралы",
    "6.5": "Логарифмдік функцияның туындысы",
    "7.1": "Көрсеткіштік теңдеулер және олардың жүйелері",
    "7.2": "Логарифмдік теңдеулер және олардың жүйелері",
    "7.3": "Көрсеткіштік теңсіздіктер",
    "7.4": "Логарифмдік теңсіздіктер",
    "8.1": "Дифференциалдық теңдеулер жайлы негізгі түсініктер",
    "8.2": "Айнымалылары ажыратылатын бірінші ретті дифференциалдық теңдеулер",
    "8.3": "Коэффициенттері тұрақты екінші ретті сызықтық біртекті дифференциалдық теңдеулер",
    "9.1": "Арифметика. Нақты сандар",
    "9.2": "Алгебралық өрнектерді тепе-тең түрлендіру",
    "9.3": "Сан тізбегі және прогрессиялар. Комбинаторика",
    "9.4": "Алгебралық теңдеулер",
    "9.5": "Алгебралық теңсіздіктер",
    "9.6": "Тригонометрия",
    "9.7": "Дәрежелік, көрсеткіштік және логарифмдік функциялар",
    "9.8": "Туынды және оның қолданулары",
    "9.9": "Алғашқы функция, интеграл және оның қолданулары",
    "9.10": "Теңдеу құруға берілген есептер",
}

# Sequential paragraph numbers for DB (1-22)
PARA_KEYS_SORTED = sorted(KNOWN_PARAGRAPHS.keys(), key=lambda x: tuple(map(int, x.split("."))))
PARA_DB_NUMBER = {key: i + 1 for i, key in enumerate(PARA_KEYS_SORTED)}

# Chapter assignment based on first digit
# 6 -> chapter 1, 7 -> chapter 2, 8 -> chapter 3, 9 -> chapter 4
DIGIT_TO_CHAPTER = {6: 1, 7: 2, 8: 3, 9: 4}
CHAPTER_FOR_PARA = {key: DIGIT_TO_CHAPTER[int(key.split(".")[0])] for key in KNOWN_PARAGRAPHS}

# -- OCR fixes -----------------------------------------------------------------

OCR_FIXES = {
    "ЖЭНЕ": "ЖӘНЕ",
    "ЖОНЕ": "ЖӘНЕ",
    "ТЕЦСІЗДІКТЕР": "ТЕҢСІЗДІКТЕР",
    "ТЕНДЕУЛЕР": "ТЕҢДЕУЛЕР",
    "ТЕНСІЗДІКТЕР": "ТЕҢСІЗДІКТЕР",
    "белімінің": "бөлімінің",
    "белім": "бөлім",
}

# -- Data classes --------------------------------------------------------------


@dataclass
class ParsedSubExercise:
    number: str
    text: str
    answer: str = ""


@dataclass
class ParsedExercise:
    exercise_number: str       # "6.1", "6.42"
    difficulty: str = ""       # "A", "B", "C"
    content_lines: list[str] = field(default_factory=list)
    sub_exercises: list[ParsedSubExercise] = field(default_factory=list)
    answer_text: str = ""
    is_starred: bool = False


@dataclass
class ParsedParagraph:
    title: str
    number: int                # DB number (1-22)
    para_key: str = ""         # "6.1", "7.3", etc.
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# -- Helper functions ----------------------------------------------------------


def normalize_fullwidth(s: str) -> str:
    """Replace fullwidth characters with ASCII equivalents."""
    return (s
            .replace("\uff0e", ".").replace("\uff1a", ":").replace("\uff08", "(")
            .replace("\uff09", ")").replace("\uff0c", ",").replace("\uff0f", "/")
            .replace("\uff0d", "-"))


def fix_ocr(text: str) -> str:
    """Fix known OCR artifacts."""
    for wrong, correct in OCR_FIXES.items():
        text = text.replace(wrong, correct)
    return text


def detect_paragraph(line: str) -> tuple[str, str] | None:
    """Try to match a known paragraph heading.

    Returns (para_key, title) or None.
    Handles formats:
      ## X.Y. Title
      ## X.Y Title
      ## *X.Y.  (starred heading)
      Plain text: X.Y. Title (no ## prefix, e.g. 9.7)
      ### X.Y.  (sub-heading used as paragraph, e.g. ### 9.10.)
    """
    norm = normalize_fullwidth(line.strip())
    # Remove <br> tags
    norm = re.sub(r"<br\s*/?>", " ", norm).strip()

    # Pattern 1: ## or ### heading (with optional leading *)
    # Use (?!\.\d) after X.Y to avoid matching X.Y.Z sub-sections (e.g. 6.1.1, 8.3.2)
    for prefix_re in [r"^#{1,3}\s+\*?", r"^>\s+"]:
        m = re.match(prefix_re + r"(\d+)\.(\d+)(?!\.\d)[\.\s]+(.+)", norm)
        if m:
            key = f"{m.group(1)}.{m.group(2)}"
            if key in KNOWN_PARAGRAPHS:
                return key, m.group(3).strip()
        # Also match ## X.Y without trailing title (rare)
        m = re.match(prefix_re + r"(\d+)\.(\d+)(?!\.\d)\.?\s*$", norm)
        if m:
            key = f"{m.group(1)}.{m.group(2)}"
            if key in KNOWN_PARAGRAPHS:
                return key, KNOWN_PARAGRAPHS[key]

    # Pattern 2: Plain text "X.Y. Title" (no ## prefix)
    # Only for chapter IX (9.x) where some headings lack ## prefix (e.g. "9.7. Дәрежелік...")
    # Chapters VI-VIII have ## headings, so plain text X.Y is always an exercise number.
    m = re.match(r"^(\d+)\.(\d+)(?!\.\d)[\.\s]+([А-Яа-яӘәҒғҚқҢңҮүҰұӨөІі].+)", norm)
    if m:
        key = f"{m.group(1)}.{m.group(2)}"
        if key in KNOWN_PARAGRAPHS and key.startswith("9."):
            return key, m.group(3).strip()

    return None


# -- Regex patterns ------------------------------------------------------------

# Chapter headings (VI-IX бөлім/белім)
RE_CHAPTER = re.compile(
    r"^#{0,2}\s*(?:VI+|VII|VIII|IX)\s+(?:белім|бөлім|болім)",
    re.IGNORECASE,
)

# Stop markers
RE_STOP = re.compile(r"^##\s+(?:ЖАУАПТАР\b|МАЗМҰНЫ\b|МАЗМУНЫ\b|Оку басылымы)", re.IGNORECASE)

# Topic list heading (internal content, not a paragraph boundary)
RE_TOPIC_LIST = re.compile(
    r"(?:Белімде|Бөлімде)\s+қарастырылатын\s+тақырыптар",
    re.IGNORECASE,
)

# Section summary (internal, part of last paragraph in chapter)
RE_SECTION_SUMMARY = re.compile(r"белімінің\s+қорытындысы|бөлімінің\s+қорытындысы", re.IGNORECASE)

# Exercise patterns
RE_EXERCISE_NUM = re.compile(r"^(\d+\.\d+)\.?\*?\s*(.*)", re.DOTALL)
RE_SUB_EXERCISE = re.compile(r"^(\d+)\)\s+(.*)")
RE_DIFFICULTY_HEADER = re.compile(r"^([ABC])\.?$")
RE_EXERCISES_START = re.compile(r"^Есептер\b", re.IGNORECASE)

# Image reference
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)")

# Mathpix artifacts
RE_ABSTRACT = re.compile(r"^#{1,4}\s+Abstract", re.IGNORECASE)


# -- Parser --------------------------------------------------------------------


def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    """Parse the MMD file into chapters and paragraphs."""
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    all_paragraphs: list[ParsedParagraph] = []
    current_paragraph: ParsedParagraph | None = None
    phase = "preamble"  # preamble | content | stopped
    in_topic_list = False  # suppress plain-text paragraph detection in topic lists

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        norm = normalize_fullwidth(stripped)

        # -- Skip Mathpix Abstract artifacts
        if RE_ABSTRACT.match(stripped):
            continue

        # -- Stop at answers/TOC
        if RE_STOP.match(norm) or RE_STOP.match(stripped):
            if current_paragraph:
                all_paragraphs.append(current_paragraph)
                current_paragraph = None
            phase = "stopped"
            break

        if phase == "stopped":
            break

        # -- Detect topic list heading (internal content)
        if RE_TOPIC_LIST.search(norm) or RE_TOPIC_LIST.search(stripped):
            in_topic_list = True
            if current_paragraph:
                current_paragraph.content_lines.append(line)
            continue

        # A ## heading ends the topic list zone (blank lines do NOT)
        if in_topic_list:
            if stripped.startswith("#"):
                in_topic_list = False
            else:
                # Plain text or blank in topic list — skip
                if current_paragraph:
                    current_paragraph.content_lines.append(line)
                continue

        # -- Detect chapter headings (structural markers)
        if RE_CHAPTER.match(norm) or RE_CHAPTER.match(stripped):
            if current_paragraph:
                all_paragraphs.append(current_paragraph)
                current_paragraph = None
            if phase == "preamble":
                phase = "content"
            continue

        # -- Also detect plain-text chapter intro for VIII/IX бөлім
        if phase == "content" and re.match(r"^(?:VI+I?|IX)\s+(?:белім|бөлім)", norm):
            if current_paragraph:
                all_paragraphs.append(current_paragraph)
                current_paragraph = None
            continue

        # -- Skip preamble
        if phase == "preamble":
            continue

        # -- Detect paragraph headings
        para_match = detect_paragraph(line)
        if para_match:
            key, title = para_match

            # Save previous paragraph
            if current_paragraph:
                all_paragraphs.append(current_paragraph)

            # Use canonical title from KNOWN_PARAGRAPHS
            canonical_title = KNOWN_PARAGRAPHS[key]
            current_paragraph = ParsedParagraph(
                title=canonical_title,
                number=PARA_DB_NUMBER[key],
                para_key=key,
            )
            continue

        # -- Accumulate content lines
        if current_paragraph is not None:
            current_paragraph.content_lines.append(line)

    # Save last paragraph
    if current_paragraph:
        all_paragraphs.append(current_paragraph)

    return build_chapters(all_paragraphs)


def build_chapters(paragraphs: list[ParsedParagraph]) -> list[ParsedChapter]:
    """Assign parsed paragraphs to chapters.

    Deduplicates by para_key: if multiple paragraphs have the same key,
    keeps the one with the most content (handles topic-list false matches).
    """
    # Deduplicate: keep the paragraph with the most content for each key
    best_by_key: dict[str, ParsedParagraph] = {}
    for para in paragraphs:
        key = para.para_key
        if key not in best_by_key or len(para.content_lines) > len(best_by_key[key].content_lines):
            best_by_key[key] = para

    deduped = list(best_by_key.values())

    chapters_map: dict[int, ParsedChapter] = {}
    for ch_num, ch_title in CHAPTER_DEFS:
        chapters_map[ch_num] = ParsedChapter(title=ch_title, number=ch_num)

    for para in deduped:
        ch_num = CHAPTER_FOR_PARA.get(para.para_key, 1)
        chapters_map[ch_num].paragraphs.append(para)

    # Sort paragraphs within each chapter by number
    for ch in chapters_map.values():
        ch.paragraphs.sort(key=lambda p: p.number)

    # Return only chapters that have paragraphs
    return [
        chapters_map[ch_num]
        for ch_num, _ in CHAPTER_DEFS
        if chapters_map[ch_num].paragraphs
    ]


# -- Content conversion -------------------------------------------------------


def md_lines_to_html(lines: list[str], textbook_id: int) -> str:
    """Convert markdown content lines to HTML with embedded LaTeX."""
    if not lines:
        return ""

    content = "\n".join(lines)

    # Normalize fullwidth characters
    content = normalize_fullwidth(content)

    # Clean up <br> tags in content
    content = re.sub(r"<br\s*/?>", " ", content)

    # Replace image references
    content = RE_IMAGE.sub(
        lambda m: (
            f'<img src="/uploads/textbook-images/{textbook_id}/{m.group(2)}" '
            f'alt="{m.group(1)}" style="display:block;margin:1rem auto;max-width:100%" />'
        ),
        content,
    )

    # Protect LaTeX from processing
    latex_blocks: list[str] = []

    def save_latex(match):
        idx = len(latex_blocks)
        latex_blocks.append(match.group(0))
        return f"__LATEX_{idx}__"

    # Save display math first ($$...$$), then inline ($...$)
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
                # Skip separator rows
                if all(re.match(r"^:?-+:?$", c) for c in cells if c.strip()):
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

        # Blank line -> flush
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
                if in_list:
                    flush_list()
                flush_paragraph()
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

        # Heading (## -> h3, ### -> h4)
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

        # Image (already converted)
        if line.strip().startswith("<img "):
            flush_paragraph()
            html_parts.append(
                f'<div style="margin:1rem 0;text-align:center">{line.strip()}</div>'
            )
            continue

        # Task line: "N. Text" (exercise number like 6.42. text)
        task_match = re.match(r"^(\d+(?:\.\d+)?)\.\s+(.+)", line.strip())
        if task_match:
            flush_paragraph()
            task_num = task_match.group(1)
            task_text = task_match.group(2)
            html_parts.append(
                f'<div style="margin-top:0.75rem;margin-bottom:0.25rem">'
                f'<strong>{task_num}.</strong> {task_text}</div>'
            )
            continue

        # Subtask line: "N) formula/text"
        subtask_match = re.match(r"^(\d+)\)\s+(.+)", line.strip())
        if subtask_match:
            flush_paragraph()
            sub_num = subtask_match.group(1)
            sub_text = subtask_match.group(2)
            html_parts.append(
                f'<div style="margin-left:1.5rem;margin-top:0.25rem;margin-bottom:0.25rem">'
                f'{sub_num}) {sub_text}</div>'
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


# -- Exercise extraction -------------------------------------------------------


def extract_exercises_from_paragraph(para: ParsedParagraph) -> list[ParsedExercise]:
    """Extract structured exercises from a paragraph's content lines.
    Only for chapters VI-VIII (6.x, 7.x, 8.x). Chapter IX is review-only.
    """
    # Skip review paragraphs (9.x) - they don't have A/B/C structure
    if para.para_key.startswith("9."):
        return []

    exercises: list[ParsedExercise] = []
    in_exercises = False
    current_difficulty = ""
    current_exercise: ParsedExercise | None = None

    for line in para.content_lines:
        stripped = normalize_fullwidth(line.strip())
        # Remove <br> tags from headings
        stripped = re.sub(r"<br\s*/?>", " ", stripped).strip()

        # Detect Есептер heading
        heading_match = re.match(r"^#{1,2}\s+(.+)", stripped)
        if heading_match:
            heading_text = heading_match.group(1).strip()
            if RE_EXERCISES_START.match(heading_text):
                in_exercises = True
                continue
            if in_exercises and RE_DIFFICULTY_HEADER.match(heading_text):
                current_difficulty = heading_text.rstrip(".")
                continue

        # Plain text difficulty header
        if RE_DIFFICULTY_HEADER.match(stripped):
            if in_exercises or stripped.rstrip(".") == "A":
                in_exercises = True
                current_difficulty = stripped.rstrip(".")
                continue

        if not in_exercises:
            continue

        # Skip empty
        if not stripped:
            continue

        # Detect exercise number (X.Y. text)
        m_ex = RE_EXERCISE_NUM.match(stripped)
        if m_ex:
            ex_num = m_ex.group(1)
            rest = m_ex.group(2).strip()

            # Save previous
            if current_exercise:
                exercises.append(current_exercise)

            is_starred = rest.startswith("*")
            rest = rest.lstrip("*").strip()

            current_exercise = ParsedExercise(
                exercise_number=ex_num,
                difficulty=current_difficulty,
                content_lines=[rest] if rest else [],
                is_starred=is_starred,
            )

            # Check for immediate sub-exercise
            if rest:
                m_sub = RE_SUB_EXERCISE.match(rest)
                if m_sub:
                    current_exercise.content_lines = []
                    current_exercise.sub_exercises.append(
                        ParsedSubExercise(number=m_sub.group(1), text=m_sub.group(2).strip())
                    )
            continue

        # Sub-exercise
        if current_exercise:
            m_sub = RE_SUB_EXERCISE.match(stripped)
            if m_sub:
                current_exercise.sub_exercises.append(
                    ParsedSubExercise(number=m_sub.group(1), text=m_sub.group(2).strip())
                )
                continue
            # Continuation text
            current_exercise.content_lines.append(stripped)

    if current_exercise:
        exercises.append(current_exercise)

    return exercises


def parse_answers_section(md_path: Path) -> dict[str, str]:
    """Parse the ЖАУАПТАР section. Returns dict: exercise_number -> answer text."""
    answers: dict[str, str] = {}

    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    in_answers = False
    answer_lines: list[str] = []

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        norm = normalize_fullwidth(stripped)

        # Detect ЖАУАПТАР start
        if re.match(r"^##\s+ЖАУАПТАР\b", norm, re.IGNORECASE):
            in_answers = True
            continue

        if not in_answers:
            continue

        # Stop at МАЗМУНЫ/end of file sections
        if re.match(r"^##\s+(?:МАЗМУНЫ\b|МАЗМҰНЫ\b|Оку басылымы)", norm, re.IGNORECASE):
            break

        # Stop at IX бөлім answers (review exercises don't have structured exercises)
        if re.match(r"^##\s+IX\s+(?:белім|бөлім)", norm, re.IGNORECASE):
            break

        # Skip section headings within answers (## VI белім, ## VII белім, etc.)
        if re.match(r"^##\s+", stripped):
            continue

        answer_lines.append(normalize_fullwidth(line))

    # Join and parse
    full_text = " ".join(answer_lines)

    # Split on exercise number patterns: X.Y.
    parts = re.split(r"(\d+\.\d+)\.?\s*", full_text)

    i = 1
    while i + 1 < len(parts):
        ex_num = parts[i]
        answer = parts[i + 1].strip().rstrip(",;.")
        if answer:
            answers[ex_num] = answer
        i += 2

    return answers


# -- SQL generation ------------------------------------------------------------


def escape_sql(s: str) -> str:
    """Escape string for SQL single-quote literals."""
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


def generate_sql(chapters: list[ParsedChapter], output_path: Path):
    """Generate SQL INSERT statements for importing via psql."""
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE id = {TEXTBOOK_ID} AND is_deleted = false)"
    )

    lines = [
        "-- Algebra 11 Part 2 Textbook Import (Kazakh)",
        f"-- Generated by load_textbook_{TEXTBOOK_ID}.py",
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
        lines.append(f'INSERT INTO chapters (textbook_id, title, number, "order", is_deleted)')
        lines.append(f"SELECT {textbook_where}, {chapter_title_esc}, {chapter.number}, {ch_order}, false")
        lines.append(f"WHERE NOT EXISTS (")
        lines.append(f"    SELECT 1 FROM chapters WHERE textbook_id = {textbook_where}")
        lines.append(f"    AND number = {chapter.number} AND is_deleted = false")
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

            lines.append(f"-- Paragraph {para.number}: {para.title[:50]}")
            lines.append(f'INSERT INTO paragraphs (chapter_id, title, number, "order", content, is_deleted)')
            lines.append(f"SELECT {chapter_where}, {title_esc}, {para.number}, {p_order}, {content_esc}, false")
            lines.append(f"WHERE NOT EXISTS (")
            lines.append(f"    SELECT 1 FROM paragraphs WHERE chapter_id = {chapter_where}")
            lines.append(f"    AND number = {para.number} AND is_deleted = false")
            lines.append(f");")
            lines.append("")

            # ParagraphContent for Kazakh
            lines.append(f"INSERT INTO paragraph_contents (")
            lines.append(f"    paragraph_id, language, explain_text,")
            lines.append(f"    source_hash, status_explain,")
            lines.append(f"    status_audio, status_slides, status_video, status_cards")
            lines.append(f") SELECT")
            lines.append(f"    {para_where}, 'kk', {content_esc},")
            lines.append(f"    {escape_sql(source_hash)}, 'ready',")
            lines.append(f"    'empty', 'empty', 'empty', 'empty'")
            lines.append(f"WHERE NOT EXISTS (")
            lines.append(f"    SELECT 1 FROM paragraph_contents")
            lines.append(f"    WHERE paragraph_id = {para_where} AND language = 'kk'")
            lines.append(f");")
            lines.append("")
            total_paragraphs += 1

    lines.append("COMMIT;")
    lines.append(f"-- Total: {len(chapters)} chapters, {total_paragraphs} paragraphs")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  Generated SQL: {output_path}")
    print(f"  Total: {len(chapters)} chapters, {total_paragraphs} paragraphs")
    print(f"\n  To import:")
    print(f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/import.sql")
    print(f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/import.sql")


def generate_update_sql(chapters: list[ParsedChapter], output_path: Path):
    """Generate SQL UPDATE statements to refresh content."""
    textbook_where = f"(SELECT id FROM textbooks WHERE id = {TEXTBOOK_ID} AND is_deleted = false)"

    lines = [
        f"-- Textbook {TEXTBOOK_ID} Content UPDATE",
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

            para_where = (
                f"(SELECT id FROM paragraphs WHERE chapter_id = {chapter_where}"
                f" AND number = {para.number} AND is_deleted = false LIMIT 1)"
            )

            lines.append(f"-- Update paragraph {para.number}: {para.title[:50]}")
            lines.append(f"UPDATE paragraphs SET content = {content_esc}")
            lines.append(f"WHERE id = {para_where};")
            lines.append("")
            lines.append(f"UPDATE paragraph_contents SET explain_text = {content_esc}")
            lines.append(f"WHERE paragraph_id = {para_where} AND language = 'kk';")
            lines.append("")
            total += 1

    lines.append("COMMIT;")
    lines.append(f"-- Updated {total} paragraphs")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  Generated UPDATE SQL: {output_path}")
    print(f"  Paragraphs to update: {total}")


def generate_exercises_sql(
    chapters: list[ParsedChapter],
    answers: dict[str, str],
    output_path: Path,
):
    """Generate SQL INSERT statements for exercises."""
    textbook_where = f"(SELECT id FROM textbooks WHERE id = {TEXTBOOK_ID} AND is_deleted = false)"

    lines = [
        f"-- Exercises Import for Textbook {TEXTBOOK_ID}",
        "",
        "BEGIN;",
        "",
    ]

    total_exercises = 0
    total_with_answers = 0
    total_sub = 0
    stats_by_difficulty: dict[str, int] = {"A": 0, "B": 0, "C": 0, "": 0}

    for chapter in chapters:
        chapter_where = (
            f"(SELECT id FROM chapters WHERE textbook_id = {textbook_where}"
            f" AND number = {chapter.number} AND is_deleted = false LIMIT 1)"
        )

        for para in chapter.paragraphs:
            exercises = extract_exercises_from_paragraph(para)
            if not exercises:
                continue

            para_where = (
                f"(SELECT id FROM paragraphs WHERE chapter_id = {chapter_where}"
                f" AND number = {para.number} AND is_deleted = false LIMIT 1)"
            )

            lines.append(f"-- Paragraph {para.number}: {para.title[:50]}")
            lines.append(f"-- {len(exercises)} exercises")
            lines.append("")

            for sort_idx, ex in enumerate(exercises, 1):
                # Merge answer
                answer = answers.get(ex.exercise_number, "")
                if answer:
                    ex.answer_text = answer

                content_text = " ".join(ex.content_lines).strip()
                if not content_text:
                    content_text = f"Жаттығу {ex.exercise_number}"

                content_text_esc = escape_sql(content_text)

                # Build content_html
                html_parts_ex = [f"<strong>{ex.exercise_number}.</strong> {content_text}"]
                if ex.sub_exercises:
                    for sub in ex.sub_exercises:
                        html_parts_ex.append(
                            f'<div style="margin-left:1.5rem">{sub.number}) {sub.text}</div>'
                        )
                content_html = "\n".join(html_parts_ex)
                content_html_esc = escape_sql(content_html)

                # Build sub_exercises JSON
                if ex.sub_exercises:
                    if answer:
                        sub_parts = re.split(r"(\d+)\)\s*", answer)
                        sub_answers_map: dict[str, str] = {}
                        j = 1
                        while j + 1 < len(sub_parts):
                            sub_answers_map[sub_parts[j]] = sub_parts[j + 1].strip().rstrip(";,.")
                            j += 2
                        for sub in ex.sub_exercises:
                            if sub.number in sub_answers_map:
                                sub.answer = sub_answers_map[sub.number]

                    sub_json_items = []
                    for sub in ex.sub_exercises:
                        sub_text_esc = sub.text.replace("\\", "\\\\").replace('"', '\\"')
                        sub_answer_esc = sub.answer.replace("\\", "\\\\").replace('"', '\\"') if sub.answer else ""
                        item = f'{{"number":"{sub.number}","text":"{sub_text_esc}"'
                        if sub_answer_esc:
                            item += f',"answer":"{sub_answer_esc}"'
                        item += "}"
                        sub_json_items.append(item)
                    sub_json = "'[" + ",".join(sub_json_items) + "]'::jsonb"
                    total_sub += len(ex.sub_exercises)
                else:
                    sub_json = "NULL"

                has_answer = bool(answer)
                answer_esc = escape_sql(answer) if answer else "NULL"
                difficulty_esc = escape_sql(ex.difficulty) if ex.difficulty else "NULL"

                if has_answer:
                    total_with_answers += 1

                stats_by_difficulty[ex.difficulty] = stats_by_difficulty.get(ex.difficulty, 0) + 1

                lines.append(f"INSERT INTO exercises (")
                lines.append(f"    paragraph_id, school_id, exercise_number, sort_order,")
                lines.append(f"    difficulty, content_text, content_html, sub_exercises,")
                lines.append(f"    answer_text, has_answer, is_starred, language, is_deleted")
                lines.append(f") SELECT")
                lines.append(f"    {para_where},")
                lines.append(f"    NULL, {escape_sql(ex.exercise_number)}, {sort_idx},")
                lines.append(f"    {difficulty_esc}, {content_text_esc},")
                lines.append(f"    {content_html_esc},")
                lines.append(f"    {sub_json},")
                lines.append(f"    {answer_esc}, {str(has_answer).lower()}, {str(ex.is_starred).lower()}, 'kk', false")
                lines.append(f"WHERE NOT EXISTS (")
                lines.append(f"    SELECT 1 FROM exercises")
                lines.append(f"    WHERE paragraph_id = {para_where}")
                lines.append(f"    AND exercise_number = {escape_sql(ex.exercise_number)}")
                lines.append(f"    AND is_deleted = false")
                lines.append(f");")
                lines.append("")
                total_exercises += 1

    lines.append("COMMIT;")
    lines.append(f"-- Stats: {total_exercises} exercises")
    lines.append(f"-- A: {stats_by_difficulty.get('A', 0)}, B: {stats_by_difficulty.get('B', 0)}, C: {stats_by_difficulty.get('C', 0)}")
    lines.append(f"-- With answers: {total_with_answers}")
    lines.append(f"-- Sub-exercises: {total_sub}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  Generated Exercises SQL: {output_path}")
    print(f"  Total exercises: {total_exercises}")
    print(f"    A: {stats_by_difficulty.get('A', 0)}")
    print(f"    B: {stats_by_difficulty.get('B', 0)}")
    print(f"    C: {stats_by_difficulty.get('C', 0)}")
    print(f"  With answers: {total_with_answers}")
    print(f"  Sub-exercises: {total_sub}")
    print(f"\n  To import:")
    print(f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/exercises.sql")
    print(f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/exercises.sql")


# -- Statistics ----------------------------------------------------------------


def print_parse_stats(chapters: list[ParsedChapter]):
    """Print parsing statistics."""
    total_paragraphs = 0
    total_lines = 0
    total_exercises = 0

    print("\n--- Parsing Results ---")
    for ch in chapters:
        ch_lines = sum(len(p.content_lines) for p in ch.paragraphs)
        total_paragraphs += len(ch.paragraphs)
        total_lines += ch_lines
        ch_title = ch.title[:65] + ("..." if len(ch.title) > 65 else "")
        print(f"  Chapter {ch.number}: {ch_title}")
        print(f"    Paragraphs: {len(ch.paragraphs)}, Content lines: {ch_lines}")
        for p in ch.paragraphs:
            ex_count = len(extract_exercises_from_paragraph(p))
            total_exercises += ex_count
            p_title = p.title[:55] + ("..." if len(p.title) > 55 else "")
            print(
                f"      {p.number:>3}. [{p.para_key or 'rev':>4}] {p_title:<55} "
                f"({len(p.content_lines):>4} lines, {ex_count} ex)"
            )
    print(f"\n  Total: {len(chapters)} chapters, {total_paragraphs} paragraphs, "
          f"{total_lines} content lines, {total_exercises} exercises")
    print("---")


# -- Main ----------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description=f"Load textbook {TEXTBOOK_ID} into AI Mentor DB"
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse only, no output")
    parser.add_argument("--generate-sql", type=str, help="Generate SQL to FILE")
    parser.add_argument("--update-content", type=str, help="Generate UPDATE SQL to FILE")
    parser.add_argument("--exercises", type=str, help="Generate exercises SQL to FILE")

    args = parser.parse_args()

    print(f"Parsing {MD_FILE}...")
    chapters = parse_textbook(MD_FILE)
    print_parse_stats(chapters)

    if args.generate_sql:
        generate_sql(chapters, Path(args.generate_sql))

    if args.update_content:
        generate_update_sql(chapters, Path(args.update_content))

    if args.exercises:
        print("\nParsing answers section...")
        answers = parse_answers_section(MD_FILE)
        print(f"  Found {len(answers)} answers")
        generate_exercises_sql(chapters, answers, Path(args.exercises))

    if not any([args.generate_sql, args.update_content, args.exercises]):
        if not args.dry_run:
            print("\nUse --dry-run, --generate-sql FILE, --exercises FILE, or --update-content FILE")


if __name__ == "__main__":
    main()
