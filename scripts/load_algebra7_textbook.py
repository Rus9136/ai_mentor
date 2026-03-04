#!/usr/bin/env python3
r"""
Load 'Алгебра 7 класс' (Russian) into the AI Mentor database.

Parses the markdown file with \section*{} LaTeX headings,
creates textbook/chapter/paragraph records,
copies images, and creates ParagraphContent records for language='ru'.

Usage:
    python scripts/load_algebra7_textbook.py --dry-run        # Parse only
    python scripts/load_algebra7_textbook.py --generate-sql FILE  # Generate SQL
    python scripts/load_algebra7_textbook.py --exercises FILE     # Exercises SQL
    python scripts/load_algebra7_textbook.py --update-content FILE # Update SQL
"""
import re
import sys
import os
import json
import shutil
import hashlib
import argparse
from pathlib import Path
from dataclasses import dataclass, field

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from dotenv import load_dotenv

# ── Path setup ──────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# ── Constants ───────────────────────────────────────────────────────────────

TEXTBOOK_TITLE = "Алгебра 7 класс"
SUBJECT_CODE = "algebra"
GRADE_LEVEL = 7
AUTHORS = "А.Е. Абылкасымова, Т.П. Кучер, В.Е. Корчевский, З.А. Жумагулова"
PUBLISHER = "Мектеп"
YEAR = 2025
ISBN = "978-601-07-1742-8"
LANGUAGE = "ru"

MD_FILE = PROJECT_ROOT / "docs" / "textbooks" / "algebra7" / "1513_with_local_images.md"
IMAGES_SRC_DIR = PROJECT_ROOT / "docs" / "textbooks" / "algebra7" / "images"
UPLOADS_BASE = PROJECT_ROOT / "uploads"

# Known chapter titles → chapter numbers
CHAPTER_TITLES = {
    "СТЕПЕНЬ С ЦЕЛЫМ ПОКАЗАТЕЛЕМ": 1,
    "МНОГОЧЛЕНЫ": 2,
    "ФУНКЦИЯ. ГРАФИК ФУНКЦИИ": 3,
    "ЭЛЕМЕНТЫ СТАТИСТИКИ": 4,
    "ФОРМУЛЫ СОКРАЩЕННОГО УМНОЖЕНИЯ": 5,
    "АЛГЕБРАИЧЕСКИЕ ДРОБИ": 6,
}

# Headings that are internal content within a paragraph (NOT paragraph boundaries)
INTERNAL_HEADINGS = {
    # Exercise sections
    "Упражнения",
    "А", "A", "B", "в", "C", "С",
    # Preparation sections
    "Подготовьтесь к овладению новыми знаниями",
    "Подготовьте сообщение",
    # Theory sections
    "Запомните！", "Запомните!",
    "Доказательство.", "Доказательство",
    "Решение.", "Решение",
    "Самостоятельно докажите свойства 2)-5).",
    "Докажите тождества (7.15-7.16):",
    "Как сравнивать числа, записанные в стандартном виде?",
    "Свойство 2", "Свойство 3",
    # Preamble/meta
    "Условные обозначения：",
    "Авторы：",
    "СОДЕРЖАНИЕ",
    "ВВЕДЕНИЕ",
    "Уважаемые ученики!",
    "Упростите выражения (11-12):",
    # End-of-book sections
    "ГРАФИКИ ФУНКЦИИ",
    "СТЕПЕНЬ",
    # TOC items
    "Упражнения для повторения курса математики для 5-6 классов",
    "Раздел І. Степень с целым показателем",
    "Раздел II. Многочлены",
    "Раздел III. Функция. График функции",
    "Раздел IV. Элементы статистики",
    "Раздел V. Формулы сокращенного умножения",
    "Раздел VI. Алгебраические дроби",
}

# Headings that are review subsections (paragraph boundaries in review chapters)
REVIEW_SUBSECTIONS = {
    "Вычисления",
    "Преобразования выражений",
    "Уравнения и их системы",
    "Неравенства и их системы",
    "Координатная плоскость",
    "Формулы",
    "Тождественные преобразования выражений",
    "Функция",
}

# OCR artifacts to fix
OCR_FIXES = {
    "：": ":",  # Fullwidth colon → normal colon
    "（": "(",  # Fullwidth brackets
    "）": ")",
    "，": ",",  # Fullwidth comma
    "＂": '"',  # Fullwidth quotes
    "！": "!",
    "．": ".",  # Fullwidth period
}

# Lines/headings to skip entirely (watermarks, ads)
SKIP_PATTERNS = [
    "Все учебники Казахстана",
    "се учебники Казахстана",  # OCR variant
    "]се учебники Казахстана",
    "OKULYK",
]

# ── Data classes ────────────────────────────────────────────────────────────


@dataclass
class ParsedSubExercise:
    number: str       # "1", "2", ...
    text: str         # text/formula
    answer: str = ""  # answer from ОТВЕТЫ


@dataclass
class ParsedExercise:
    exercise_number: str           # "1.1", "9.23"
    difficulty: str = ""           # "A", "B", "C"
    content_lines: list[str] = field(default_factory=list)
    sub_exercises: list[ParsedSubExercise] = field(default_factory=list)
    answer_text: str = ""
    is_starred: bool = False


@dataclass
class ParsedParagraph:
    title: str
    number: int
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# ── Regex patterns ──────────────────────────────────────────────────────────

# \section*{CONTENT} heading
RE_SECTION = re.compile(r"^\\section\*\{(.+)\}\s*$")

# Paragraph heading: \section*{§ N. TITLE} or bare "§ N. TITLE"
RE_PARAGRAPH = re.compile(r"^§\s*(\d+)[.\s]+(.+)")

# Self-test section
RE_SELF_TEST = re.compile(r"ПРОВЕРЬ СЕБЯ", re.IGNORECASE)

# Answers section
RE_ANSWERS = re.compile(r"^ОТВЕТЫ$")

# Index section
RE_INDEX = re.compile(r"^ПРЕДМЕТНЫЙ УКАЗАТЕЛЬ$")

# Image reference in markdown
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(\./images/([^)]+)\)")

# Exercise patterns
RE_EXERCISE_NUM = re.compile(r"^(\d+\.\d+)\.?\s*(.*)", re.DOTALL)
RE_SUB_EXERCISE = re.compile(r"^(\d+)\)\s+(.*)")
RE_DIFFICULTY_HEADER = re.compile(r"^([ABCАВСвас])$")
RE_EXERCISES_START = re.compile(r"^Упражнения$", re.IGNORECASE)

# \author{...} blocks (OCR junk)
RE_AUTHOR_START = re.compile(r"^\\author\{")
RE_AUTHOR_END = re.compile(r"^\}")

# LaTeX table environments
RE_TABLE_START = re.compile(r"^\\begin\{table\}")
RE_TABLE_END = re.compile(r"^\\end\{table\}")
RE_TABULAR_START = re.compile(r"^\\begin\{tabular\}")
RE_TABULAR_END = re.compile(r"^\\end\{tabular\}")

# LaTeX figure environments
RE_FIGURE_START = re.compile(r"^\\begin\{figure\}")
RE_FIGURE_END = re.compile(r"^\\end\{figure\}")

# Review start
RE_REVIEW_START = re.compile(
    r"УПРАЖНЕНИЯ ДЛЯ ПОВТОРЕНИЯ КУРСА", re.IGNORECASE
)

# End-of-book review
RE_REVIEW_END = re.compile(
    r"УПРАЖНЕНИЯ ДЛЯ ПОВТОРЕНИЯ КУРСА\s*\n?АЛГЕБРЫ", re.IGNORECASE
)


# ── Helper functions ────────────────────────────────────────────────────────


def should_skip_line(line: str) -> bool:
    """Check if a line should be skipped entirely (watermark/ad)."""
    for pattern in SKIP_PATTERNS:
        if pattern in line:
            return True
    return False


def is_latex_junk(line: str) -> bool:
    """Check if a line is LaTeX formatting junk to strip from content."""
    stripped = line.strip()
    if not stripped:
        return False
    junk_patterns = [
        r"^\\captionsetup\{",
        r"^\\caption\{",
        r"^\\includegraphics\[",
        r"^\\begin\{figure\}",
        r"^\\end\{figure\}",
        r"^\\begin\{table\}",
        r"^\\end\{table\}",
        r"^\\begin\{tabular\}",
        r"^\\end\{tabular\}",
        r"^\\hline\s*$",
        r"^\\author\{",
    ]
    return any(re.match(p, stripped) for p in junk_patterns)


def fix_ocr(text: str) -> str:
    """Fix known OCR artifacts in text."""
    for wrong, correct in OCR_FIXES.items():
        text = text.replace(wrong, correct)
    return text


def extract_section_heading(line: str) -> str | None:
    """Extract heading text from \\section*{...} line."""
    m = RE_SECTION.match(line.strip())
    if m:
        return m.group(1).strip()
    return None


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

    # Heading that starts with image ref
    if clean.startswith("!["):
        return True

    # Heading that starts with $ (math formula)
    if clean.startswith("$"):
        return True

    # Heading that starts with a digit
    if clean and clean[0].isdigit():
        return True

    # Very long headings are usually content, not boundaries
    if len(clean) > 60:
        return True

    # Single character headings (usually OCR artifacts or difficulty markers)
    if len(clean) <= 2 and clean.isalpha():
        return True

    # Starts with (1) or similar
    if re.match(r"^\(\d+\)", clean):
        return True

    return False


def is_chapter_title(heading: str) -> int | None:
    """Check if heading is a known chapter title. Returns chapter number or None."""
    clean = heading.strip()
    # Check both with and without trailing punctuation
    for title, num in CHAPTER_TITLES.items():
        if clean == title or clean.startswith(title):
            return num
    return None


# ── Parser ──────────────────────────────────────────────────────────────────


def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    """Parse the markdown file into chapters and paragraphs."""
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    chapters: list[ParsedChapter] = []
    current_chapter: ParsedChapter | None = None
    current_paragraph: ParsedParagraph | None = None
    phase = "preamble"  # preamble | review | chapters | answers | end
    in_author_block = False
    in_figure_block = False
    review_para_counter = 0

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        # ── Skip watermarks and ads ─────────────────────────────────
        if should_skip_line(line):
            continue

        # ── Handle \author{...} blocks (extract inner content) ──────
        if RE_AUTHOR_START.match(stripped):
            in_author_block = True
            continue
        if in_author_block:
            if stripped == "}":
                in_author_block = False
                continue
            # Process inner line (might be a § heading)
            # Fall through to normal processing

        # ── Handle \begin{figure}...\end{figure} blocks ────────────
        if RE_FIGURE_START.match(stripped):
            in_figure_block = True
            continue
        if in_figure_block:
            if RE_FIGURE_END.match(stripped):
                in_figure_block = False
            continue

        # ── Extract heading from \section*{...} ─────────────────────
        heading = extract_section_heading(line)

        # ── Check for bare paragraph heading (§ N. TITLE) ──────────
        # Skip TOC entries (contain ".....")
        bare_para = None
        if not heading and "....." not in stripped:
            bare_para = RE_PARAGRAPH.match(stripped)

        # If heading is a paragraph, extract paragraph info
        para_from_heading = None
        if heading and "....." not in heading:
            # Apply OCR fixes before matching (e.g., fullwidth period ．→ .)
            heading_clean = fix_ocr(heading)
            m = RE_PARAGRAPH.match(heading_clean)
            if m:
                para_from_heading = (int(m.group(1)), m.group(2).strip())

        # ── Stop markers ────────────────────────────────────────────
        check_text = heading or stripped
        if RE_INDEX.match(check_text):
            break
        if RE_ANSWERS.match(check_text):
            phase = "answers"
            current_paragraph = None
            continue

        if phase == "answers":
            continue

        # ── Phase: preamble (skip until first chapter or review) ────
        if phase == "preamble":
            # Check for chapter title
            if heading:
                ch_num = is_chapter_title(heading)
                if ch_num:
                    phase = "chapters"
                    current_paragraph = None
                    current_chapter = ParsedChapter(
                        title=heading, number=ch_num
                    )
                    chapters.append(current_chapter)
                    continue

            # Check for review exercises start (skip TOC entries with .....)
            if RE_REVIEW_START.search(line) and "....." not in line:
                phase = "review"
                current_chapter = ParsedChapter(
                    title="Упражнения для повторения курса математики 5 и 6 классов",
                    number=0,
                )
                chapters.append(current_chapter)
                continue

            # Check for first review subsection (Вычисления)
            if heading == "Вычисления" and not chapters:
                phase = "review"
                current_chapter = ParsedChapter(
                    title="Упражнения для повторения курса математики 5 и 6 классов",
                    number=0,
                )
                chapters.append(current_chapter)
                review_para_counter = 1
                current_paragraph = ParsedParagraph(
                    title="Вычисления", number=review_para_counter
                )
                current_chapter.paragraphs.append(current_paragraph)
                continue

            continue

        # ── Check for chapter title in heading ──────────────────────
        if heading:
            ch_num = is_chapter_title(heading)
            if ch_num:
                current_paragraph = None
                current_chapter = ParsedChapter(
                    title=heading, number=ch_num
                )
                chapters.append(current_chapter)
                phase = "chapters"
                continue

        # Check for bare chapter title (no \section*{})
        if not heading and stripped in CHAPTER_TITLES:
            ch_num = CHAPTER_TITLES[stripped]
            current_paragraph = None
            current_chapter = ParsedChapter(
                title=stripped, number=ch_num
            )
            chapters.append(current_chapter)
            phase = "chapters"
            continue

        # ── Check for end-of-book review ────────────────────────────
        if RE_REVIEW_START.search(line) and phase == "chapters" and "....." not in line:
            current_paragraph = None
            review_para_counter = 0
            current_chapter = ParsedChapter(
                title="Упражнения для повторения курса алгебры для 7 класса",
                number=7,
            )
            chapters.append(current_chapter)
            phase = "review"
            continue

        # ── Detect § paragraph heading ──────────────────────────────
        if para_from_heading:
            para_num, para_title = para_from_heading
            para_title = fix_ocr(para_title)
            current_paragraph = ParsedParagraph(
                title=para_title, number=para_num
            )
            if current_chapter:
                current_chapter.paragraphs.append(current_paragraph)
            continue

        if bare_para:
            para_num = int(bare_para.group(1))
            para_title = bare_para.group(2).strip()
            para_title = fix_ocr(para_title)
            current_paragraph = ParsedParagraph(
                title=para_title, number=para_num
            )
            if current_chapter:
                current_chapter.paragraphs.append(current_paragraph)
            continue

        # ── Detect ПРОВЕРЬ СЕБЯ! (self-test) ────────────────────────
        if heading and RE_SELF_TEST.search(heading):
            current_paragraph = ParsedParagraph(
                title="Проверь себя!", number=900
            )
            if current_chapter:
                current_chapter.paragraphs.append(current_paragraph)
            continue

        # ── Detect missing §30 (no heading in OCR) ──────────────────
        if (
            current_chapter
            and current_chapter.number == 4
            and current_paragraph
            and current_paragraph.number == 29
            and stripped.startswith("Варианта, абсолютная частота")
        ):
            current_paragraph = ParsedParagraph(
                title="ПОЛИГОН ЧАСТОТ", number=30
            )
            current_chapter.paragraphs.append(current_paragraph)
            current_paragraph.content_lines.append(line)
            continue

        # ── In review phase, detect subsection headings ─────────────
        if phase == "review" and heading:
            # Review subsections ARE paragraph boundaries in review chapters
            if heading in REVIEW_SUBSECTIONS or not is_internal_heading(heading):
                review_para_counter += 1
                current_paragraph = ParsedParagraph(
                    title=heading, number=review_para_counter
                )
                if current_chapter:
                    current_chapter.paragraphs.append(current_paragraph)
                continue

        # ── Handle internal headings within content ─────────────────
        if heading and is_internal_heading(heading):
            # Include as content (will be rendered as <h3>)
            if current_paragraph is not None:
                current_paragraph.content_lines.append(f"## {heading}")
            continue

        # ── Skip LaTeX formatting junk ──────────────────────────────
        if is_latex_junk(line):
            continue

        # Skip \hline in table content (preserve table rows with &)
        if stripped == "\\hline":
            continue

        # ── Accumulate content lines ────────────────────────────────
        if current_paragraph is not None:
            current_paragraph.content_lines.append(line)

    return chapters


# ── Content conversion ──────────────────────────────────────────────────────


def preprocess_content_lines(lines: list[str]) -> list[str]:
    """Preprocess content lines: handle LaTeX constructs."""
    result = []
    in_tabular = False
    tabular_rows = []
    caption_text = ""

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty \author blocks
        if RE_AUTHOR_START.match(stripped):
            # Skip until closing }
            i += 1
            while i < len(lines) and lines[i].strip() != "}":
                i += 1
            i += 1
            continue

        # Handle \begin{table}
        if RE_TABLE_START.match(stripped):
            i += 1
            continue

        if RE_TABLE_END.match(stripped):
            i += 1
            continue

        # Handle \captionsetup
        if stripped.startswith("\\captionsetup{"):
            i += 1
            continue

        # Handle \caption{...}
        if stripped.startswith("\\caption{"):
            m = re.match(r"\\caption\{(.+)\}", stripped)
            if m:
                caption_text = m.group(1)
                result.append(f"**{caption_text}**")
            i += 1
            continue

        # Handle \begin{tabular}
        if RE_TABULAR_START.match(stripped):
            in_tabular = True
            tabular_rows = []
            i += 1
            continue

        if in_tabular:
            if RE_TABULAR_END.match(stripped):
                # Convert accumulated rows to markdown table
                if tabular_rows:
                    md_table = convert_tabular_to_markdown(tabular_rows)
                    result.extend(md_table)
                in_tabular = False
                i += 1
                continue
            tabular_rows.append(stripped)
            i += 1
            continue

        # Handle \begin{figure}...\end{figure}
        if RE_FIGURE_START.match(stripped):
            # Skip entire figure block
            i += 1
            while i < len(lines) and not RE_FIGURE_END.match(lines[i].strip()):
                i += 1
            i += 1  # skip \end{figure}
            continue

        # Handle \hline (standalone)
        if stripped == "\\hline":
            i += 1
            continue

        # Handle \section*{} within content → ## heading
        heading = extract_section_heading(line)
        if heading and not should_skip_line(heading):
            result.append(f"## {heading}")
            i += 1
            continue

        # Skip watermarks
        if should_skip_line(line):
            i += 1
            continue

        # Skip isolated LaTeX commands
        if stripped.startswith("\\includegraphics["):
            i += 1
            continue

        result.append(line)
        i += 1

    return result


def convert_tabular_to_markdown(rows: list[str]) -> list[str]:
    """Convert LaTeX tabular rows to markdown table lines."""
    md_rows = []
    current_cells = []
    cell_buffer = ""

    for row_line in rows:
        # Skip pure \hline lines
        clean = row_line.replace("\\hline", "").strip()
        if not clean or clean == "\\\\":
            continue

        # Handle nested \begin{tabular} (multi-line cells)
        if "\\begin{tabular}" in clean:
            clean = re.sub(r"\\begin\{tabular\}\{[^}]*\}", "", clean)
        if "\\end{tabular}" in clean:
            clean = clean.replace("\\end{tabular}", "")

        # Accumulate row content
        cell_buffer += " " + clean

        # Row ends with \\
        if "\\\\" in cell_buffer:
            parts = cell_buffer.split("\\\\")
            row_content = parts[0].strip()

            if "&" in row_content:
                cells = [c.strip() for c in row_content.split("&")]
                md_rows.append(cells)
            elif row_content:
                # Single-cell continuation
                if md_rows and len(md_rows[-1]) > 0:
                    md_rows[-1][0] += " " + row_content
            cell_buffer = parts[1] if len(parts) > 1 else ""

    # Handle remaining buffer
    if cell_buffer.strip():
        clean = cell_buffer.replace("\\hline", "").strip()
        if "&" in clean:
            cells = [c.strip() for c in clean.split("&")]
            md_rows.append(cells)

    if not md_rows:
        return []

    # Generate markdown table
    result = []
    max_cols = max(len(r) for r in md_rows)

    for i, row in enumerate(md_rows):
        # Pad row to max_cols
        while len(row) < max_cols:
            row.append("")
        result.append("| " + " | ".join(row) + " |")
        if i == 0:
            result.append("| " + " | ".join(["---"] * max_cols) + " |")

    return result


def md_lines_to_html(lines: list[str], textbook_id: int) -> str:
    """Convert markdown content lines to HTML with embedded LaTeX."""
    if not lines:
        return ""

    # Preprocess LaTeX constructs
    lines = preprocess_content_lines(lines)

    content = "\n".join(lines)

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

    for raw_line in content.split("\n"):
        line = raw_line.rstrip()

        # Blank line → flush paragraph
        if not line.strip():
            if in_table:
                flush_table()
            flush_paragraph()
            continue

        # Table row
        if line.strip().startswith("|"):
            if not in_table:
                flush_paragraph()
                in_table = True
            table_rows.append(line)
            continue
        elif in_table:
            flush_table()

        # Heading (## → h3, ### → h4)
        heading_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if heading_match:
            flush_paragraph()
            level = min(len(heading_match.group(1)) + 1, 6)  # Demote by 1
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

        # List items (- text)
        if line.strip().startswith("- "):
            flush_paragraph()
            item_text = line.strip()[2:]
            html_parts.append(
                f'<div style="margin-left:1.5rem;margin-top:0.25rem">• {item_text}</div>'
            )
            continue

        # Task line: "N. Text" (main exercise number)
        task_match = re.match(r"^(\d+)\.\s+(.+)", line.strip())
        if task_match:
            flush_paragraph()
            task_num = task_match.group(1)
            task_text = task_match.group(2)
            html_parts.append(
                f'<div style="margin-top:1.5rem;margin-bottom:0.5rem">'
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
    flush_paragraph()

    html = "\n".join(html_parts)

    # Apply inline formatting
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", html)

    # Restore LaTeX
    for idx, latex in enumerate(latex_blocks):
        html = html.replace(f"__LATEX_{idx}__", latex)

    return html.strip()


def extract_key_terms(lines: list[str]) -> list[str] | None:
    """Extract key terms from content (first line often has key terms)."""
    terms = []
    # In this textbook, key terms appear at the start of paragraphs
    # as comma-separated words, often prefixed with (1) or 0
    for line in lines[:5]:  # Check first 5 lines
        stripped = line.strip()
        # Clean OCR artifacts
        stripped = re.sub(r"^[0（\(]\d*\)?\s*", "", stripped)
        # Check if it looks like key terms (short comma-separated words)
        if "," in stripped and len(stripped) < 200:
            parts = [t.strip() for t in stripped.split(",")]
            if all(len(p) < 80 for p in parts) and len(parts) >= 2:
                terms.extend(p for p in parts if p and len(p) > 2)
                break
    return terms if terms else None


# ── Database operations ─────────────────────────────────────────────────────


def get_database_url() -> str:
    """Build database URL from environment variables."""
    user = os.getenv("POSTGRES_USER", "ai_mentor_user")
    password = os.getenv("POSTGRES_PASSWORD", "ai_mentor_pass")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ai_mentor_db")
    encoded_password = quote_plus(password)
    return f"postgresql://{user}:{encoded_password}@{host}:{port}/{db}"


def find_or_create_subject(session) -> int:
    """Find 'algebra' subject or create it."""
    result = session.execute(
        text("SELECT id FROM subjects WHERE code = :code"),
        {"code": SUBJECT_CODE},
    )
    row = result.fetchone()
    if row:
        print(f"  Found subject '{SUBJECT_CODE}' (id={row[0]})")
        return row[0]

    result = session.execute(
        text("""
            INSERT INTO subjects (code, name_ru, name_kz, grade_from, grade_to, is_active)
            VALUES (:code, :name_ru, :name_kz, :grade_from, :grade_to, true)
            RETURNING id
        """),
        {
            "code": SUBJECT_CODE,
            "name_ru": "Алгебра",
            "name_kz": "Алгебра",
            "grade_from": 7,
            "grade_to": 11,
        },
    )
    subject_id = result.fetchone()[0]
    print(f"  Created subject '{SUBJECT_CODE}' (id={subject_id})")
    return subject_id


def find_or_create_textbook(session, subject_id: int) -> int:
    """Find or create the textbook record."""
    result = session.execute(
        text("""
            SELECT id FROM textbooks
            WHERE title = :title AND grade_level = :grade AND is_deleted = false
        """),
        {"title": TEXTBOOK_TITLE, "grade": GRADE_LEVEL},
    )
    row = result.fetchone()
    if row:
        print(f"  Textbook already exists (id={row[0]})")
        return row[0]

    result = session.execute(
        text("""
            INSERT INTO textbooks (
                school_id, subject_id, title, subject, grade_level,
                author, publisher, year, isbn, description,
                is_active, is_customized, version
            ) VALUES (
                NULL, :subject_id, :title, :subject, :grade_level,
                :author, :publisher, :year, :isbn, :description,
                true, false, 1
            )
            RETURNING id
        """),
        {
            "subject_id": subject_id,
            "title": TEXTBOOK_TITLE,
            "subject": "Алгебра",
            "grade_level": GRADE_LEVEL,
            "author": AUTHORS,
            "publisher": PUBLISHER,
            "year": YEAR,
            "isbn": ISBN,
            "description": "Учебник для 7 класса общеобразовательных школ. 2-е издание.",
        },
    )
    textbook_id = result.fetchone()[0]
    print(f"  Created textbook (id={textbook_id})")
    return textbook_id


def create_chapter(session, textbook_id: int, chapter: ParsedChapter, order: int) -> int:
    """Create a chapter record."""
    result = session.execute(
        text("""
            SELECT id FROM chapters
            WHERE textbook_id = :tid AND number = :num AND is_deleted = false
        """),
        {"tid": textbook_id, "num": chapter.number},
    )
    row = result.fetchone()
    if row:
        print(f"    Chapter {chapter.number} already exists (id={row[0]})")
        return row[0]

    result = session.execute(
        text("""
            INSERT INTO chapters (textbook_id, title, number, "order")
            VALUES (:textbook_id, :title, :number, :order)
            RETURNING id
        """),
        {
            "textbook_id": textbook_id,
            "title": chapter.title,
            "number": chapter.number,
            "order": order,
        },
    )
    chapter_id = result.fetchone()[0]
    title_short = chapter.title[:60] + ("..." if len(chapter.title) > 60 else "")
    print(f"    Created chapter {chapter.number}: {title_short} (id={chapter_id})")
    return chapter_id


def create_paragraph(
    session, chapter_id: int, para: ParsedParagraph, order: int, textbook_id: int
) -> int:
    """Create paragraph + ParagraphContent records."""
    html_content = md_lines_to_html(para.content_lines, textbook_id)
    key_terms = extract_key_terms(para.content_lines)

    result = session.execute(
        text("""
            SELECT id FROM paragraphs
            WHERE chapter_id = :cid AND number = :num AND is_deleted = false
        """),
        {"cid": chapter_id, "num": para.number},
    )
    row = result.fetchone()
    if row:
        print(f"      Paragraph {para.number} already exists (id={row[0]})")
        return row[0]

    result = session.execute(
        text("""
            INSERT INTO paragraphs (
                chapter_id, title, number, "order", content, key_terms
            ) VALUES (
                :chapter_id, :title, :number, :order, :content, :key_terms::json
            )
            RETURNING id
        """),
        {
            "chapter_id": chapter_id,
            "title": para.title,
            "number": para.number,
            "order": order,
            "content": html_content,
            "key_terms": json.dumps(key_terms, ensure_ascii=False) if key_terms else None,
        },
    )
    paragraph_id = result.fetchone()[0]

    # Create ParagraphContent for Russian
    source_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]
    session.execute(
        text("""
            INSERT INTO paragraph_contents (
                paragraph_id, language, explain_text,
                source_hash, status_explain,
                status_audio, status_slides, status_video, status_cards
            ) VALUES (
                :paragraph_id, :lang, :explain_text,
                :source_hash, 'ready',
                'empty', 'empty', 'empty', 'empty'
            )
            ON CONFLICT (paragraph_id, language) DO NOTHING
        """),
        {
            "paragraph_id": paragraph_id,
            "lang": LANGUAGE,
            "explain_text": html_content,
            "source_hash": source_hash,
        },
    )

    title_short = para.title[:50] + ("..." if len(para.title) > 50 else "")
    print(f"      Created paragraph {para.number}: {title_short} (id={paragraph_id})")
    return paragraph_id


# ── Image copy ──────────────────────────────────────────────────────────────


def copy_images(textbook_id: int) -> int:
    """Copy images from source directory to uploads directory."""
    dest_dir = UPLOADS_BASE / "textbook-images" / str(textbook_id)
    dest_dir.mkdir(parents=True, exist_ok=True)

    if not IMAGES_SRC_DIR.exists():
        print(f"  WARNING: Source images directory not found: {IMAGES_SRC_DIR}")
        return 0

    copied = 0
    skipped = 0
    for img_file in sorted(IMAGES_SRC_DIR.iterdir()):
        if img_file.is_file() and img_file.suffix.lower() in (
            ".jpg", ".jpeg", ".png", ".gif", ".webp",
        ):
            dest_path = dest_dir / img_file.name
            if dest_path.exists():
                skipped += 1
            else:
                shutil.copy2(img_file, dest_path)
                copied += 1

    print(f"  Copied {copied} images, skipped {skipped} existing -> {dest_dir}")
    return copied


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
        ch_title = ch.title[:65] + ("..." if len(ch.title) > 65 else "")
        print(f"  Chapter {ch.number}: {ch_title}")
        print(f"    Paragraphs: {len(ch.paragraphs)}, Content lines: {ch_lines}")
        for p in ch.paragraphs:
            p_title = p.title[:55] + ("..." if len(p.title) > 55 else "")
            terms = extract_key_terms(p.content_lines) or []
            print(
                f"      {p.number:>3}. {p_title:<58} "
                f"({len(p.content_lines):>4} lines, {len(terms)} terms)"
            )
    print(
        f"\n  Total: {len(chapters)} chapters, {total_paragraphs} paragraphs, "
        f"{total_lines} content lines"
    )
    print("---")


# ── Exercise extraction ─────────────────────────────────────────────────────


def extract_exercises_from_paragraph(para: ParsedParagraph) -> list[ParsedExercise]:
    """Extract structured exercises from a paragraph's content lines."""
    exercises: list[ParsedExercise] = []
    in_exercises = False
    current_difficulty = ""
    current_exercise: ParsedExercise | None = None

    for line in para.content_lines:
        stripped = line.strip()

        # Detect start of exercises section (## Упражнения)
        if stripped == "## Упражнения" or RE_EXERCISES_START.match(stripped):
            in_exercises = True
            continue

        # Detect difficulty header (## A, ## B, ## C, or just A, B, C)
        clean_diff = stripped.lstrip("#").strip()
        m_diff = RE_DIFFICULTY_HEADER.match(clean_diff)
        if m_diff and len(stripped) <= 5:
            # Also trigger exercise mode if not yet active (e.g., §35 has no
            # "Упражнения" heading, exercises start directly with ## A)
            if not in_exercises:
                in_exercises = True
            diff_char = m_diff.group(1).upper()
            # Normalize Cyrillic to Latin
            diff_map = {"А": "A", "В": "B", "С": "C"}
            current_difficulty = diff_map.get(diff_char, diff_char)
            continue

        if not in_exercises:
            continue

        # Skip empty lines
        if not stripped:
            continue

        # Detect exercise number (e.g., "1.1. text")
        m_ex = RE_EXERCISE_NUM.match(stripped)
        if m_ex:
            if current_exercise:
                exercises.append(current_exercise)

            ex_num = m_ex.group(1)
            rest = m_ex.group(2).strip()
            is_starred = "*" in rest[:5] if rest else False
            rest = rest.lstrip("*").strip()

            current_exercise = ParsedExercise(
                exercise_number=ex_num,
                difficulty=current_difficulty,
                content_lines=[rest] if rest else [],
                is_starred=is_starred,
            )

            if rest:
                m_sub = RE_SUB_EXERCISE.match(rest)
                if m_sub:
                    current_exercise.content_lines = []
                    current_exercise.sub_exercises.append(
                        ParsedSubExercise(
                            number=m_sub.group(1), text=m_sub.group(2).strip()
                        )
                    )
            continue

        # Detect sub-exercise (e.g., "1) text")
        if current_exercise:
            m_sub = RE_SUB_EXERCISE.match(stripped)
            if m_sub:
                current_exercise.sub_exercises.append(
                    ParsedSubExercise(
                        number=m_sub.group(1), text=m_sub.group(2).strip()
                    )
                )
                continue

            current_exercise.content_lines.append(stripped)

    if current_exercise:
        exercises.append(current_exercise)

    return exercises


def parse_answers_section(md_path: Path) -> dict[str, str]:
    """Parse the ОТВЕТЫ (answers) section from the MD file."""
    answers: dict[str, str] = {}

    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    in_answers = False
    answer_text_lines: list[str] = []

    for raw_line in lines:
        line = raw_line.rstrip("\n").strip()

        heading = extract_section_heading(raw_line.rstrip("\n"))
        if heading and RE_ANSWERS.match(heading):
            in_answers = True
            continue

        if not in_answers:
            continue

        # Skip section headings within answers (subsection titles)
        if heading:
            continue

        answer_text_lines.append(line)

    full_text = " ".join(answer_text_lines)

    # Parse individual answers
    parts = re.split(r"(\d+\.\d+)\.?\s*", full_text)
    i = 1
    while i + 1 < len(parts):
        ex_num = parts[i]
        answer = parts[i + 1].strip().rstrip(",;.")
        if answer:
            answers[ex_num] = answer
        i += 2

    return answers


# ── SQL helpers ─────────────────────────────────────────────────────────────


def escape_sql(s: str) -> str:
    """Escape string for SQL single-quote literals."""
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


def generate_exercises_sql(
    chapters: list[ParsedChapter],
    answers: dict[str, str],
    output_path: Path,
):
    """Generate SQL INSERT statements for exercises."""
    textbook_title_esc = escape_sql(TEXTBOOK_TITLE)
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE title = {textbook_title_esc}"
        f" AND grade_level = {GRADE_LEVEL} AND is_deleted = false LIMIT 1)"
    )

    lines = [
        f"-- Exercises Import for {TEXTBOOK_TITLE}",
        "-- Generated by load_algebra7_textbook.py --exercises",
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

            para_number = para.number if para.number != 900 else 100
            para_where = (
                f"(SELECT id FROM paragraphs WHERE chapter_id = {chapter_where}"
                f" AND number = {para_number} AND is_deleted = false LIMIT 1)"
            )

            lines.append(f"-- Paragraph {para_number}: {para.title[:50]}")
            lines.append(f"-- {len(exercises)} exercises")
            lines.append("")

            for sort_idx, ex in enumerate(exercises, 1):
                answer = answers.get(ex.exercise_number, "")
                if answer:
                    ex.answer_text = answer

                content_text = " ".join(ex.content_lines).strip()
                if not content_text:
                    content_text = f"Упражнение {ex.exercise_number}"

                content_text_esc = escape_sql(content_text)

                html_parts_ex = [
                    f"<strong>{ex.exercise_number}.</strong> {content_text}"
                ]
                if ex.sub_exercises:
                    for sub in ex.sub_exercises:
                        html_parts_ex.append(
                            f'<div style="margin-left:1.5rem">{sub.number}) {sub.text}</div>'
                        )
                content_html = "\n".join(html_parts_ex)
                content_html_esc = escape_sql(content_html)

                if ex.sub_exercises:
                    if answer:
                        sub_parts = re.split(r"(\d+)\)\s*", answer)
                        sub_answers_map: dict[str, str] = {}
                        j = 1
                        while j + 1 < len(sub_parts):
                            sub_answers_map[sub_parts[j]] = (
                                sub_parts[j + 1].strip().rstrip(";,.")
                            )
                            j += 2
                        for sub in ex.sub_exercises:
                            if sub.number in sub_answers_map:
                                sub.answer = sub_answers_map[sub.number]

                    sub_json_items = []
                    for sub in ex.sub_exercises:
                        sub_text_esc = sub.text.replace("\\", "\\\\").replace(
                            '"', '\\"'
                        )
                        sub_answer_esc = (
                            sub.answer.replace("\\", "\\\\").replace('"', '\\"')
                            if sub.answer
                            else ""
                        )
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
                difficulty_esc = (
                    escape_sql(ex.difficulty) if ex.difficulty else "NULL"
                )

                if has_answer:
                    total_with_answers += 1
                stats_by_difficulty[ex.difficulty] = (
                    stats_by_difficulty.get(ex.difficulty, 0) + 1
                )

                lines.append(
                    f"-- Exercise {ex.exercise_number} (difficulty={ex.difficulty or '?'})"
                )
                lines.append("INSERT INTO exercises (")
                lines.append(
                    "    paragraph_id, school_id, exercise_number, sort_order,"
                )
                lines.append(
                    "    difficulty, content_text, content_html, sub_exercises,"
                )
                lines.append(
                    "    answer_text, has_answer, is_starred, language, is_deleted"
                )
                lines.append(") SELECT")
                lines.append(f"    {para_where},")
                lines.append(
                    f"    NULL, {escape_sql(ex.exercise_number)}, {sort_idx},"
                )
                lines.append(f"    {difficulty_esc}, {content_text_esc},")
                lines.append(f"    {content_html_esc},")
                lines.append(f"    {sub_json},")
                lines.append(
                    f"    {answer_esc}, {str(has_answer).lower()}, "
                    f"{str(ex.is_starred).lower()}, '{LANGUAGE}', false"
                )
                lines.append("WHERE NOT EXISTS (")
                lines.append("    SELECT 1 FROM exercises")
                lines.append(f"    WHERE paragraph_id = {para_where}")
                lines.append(
                    f"    AND exercise_number = {escape_sql(ex.exercise_number)}"
                )
                lines.append("    AND is_deleted = false")
                lines.append(");")
                lines.append("")
                total_exercises += 1

    lines.append("COMMIT;")
    lines.append("")
    lines.append(f"-- Stats: {total_exercises} exercises")
    lines.append(
        f"-- A: {stats_by_difficulty.get('A', 0)}, "
        f"B: {stats_by_difficulty.get('B', 0)}, "
        f"C: {stats_by_difficulty.get('C', 0)}"
    )
    lines.append(f"-- With answers: {total_with_answers}")
    lines.append(f"-- Sub-exercises: {total_sub}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  Generated Exercises SQL: {output_path}")
    print(f"  Total exercises: {total_exercises}")
    print(f"    A: {stats_by_difficulty.get('A', 0)}")
    print(f"    B: {stats_by_difficulty.get('B', 0)}")
    print(f"    C: {stats_by_difficulty.get('C', 0)}")
    print(f"    No difficulty: {stats_by_difficulty.get('', 0)}")
    print(f"  With answers: {total_with_answers}")
    print(f"  Sub-exercises: {total_sub}")


def generate_update_sql(chapters: list[ParsedChapter], output_path: Path):
    """Generate SQL UPDATE statements to refresh content."""
    textbook_title_esc = escape_sql(TEXTBOOK_TITLE)
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE title = {textbook_title_esc}"
        f" AND grade_level = {GRADE_LEVEL} AND is_deleted = false LIMIT 1)"
    )

    sql_lines = [
        f"-- {TEXTBOOK_TITLE} Content UPDATE",
        "-- Regenerated HTML with improved formatting",
        "",
        "BEGIN;",
        "",
    ]

    textbook_id_expr = textbook_where

    total = 0
    for chapter in chapters:
        chapter_where = (
            f"(SELECT id FROM chapters WHERE textbook_id = {textbook_where}"
            f" AND number = {chapter.number} AND is_deleted = false LIMIT 1)"
        )

        for p_order, para in enumerate(chapter.paragraphs, 1):
            para_number = para.number if para.number != 900 else 100 + p_order
            html_content = md_lines_to_html(para.content_lines, 0)
            content_esc = escape_sql(html_content)

            para_where = (
                f"(SELECT id FROM paragraphs WHERE chapter_id = {chapter_where}"
                f" AND number = {para_number} AND is_deleted = false LIMIT 1)"
            )

            sql_lines.append(f"-- Update paragraph {para_number}: {para.title[:50]}")
            sql_lines.append(f"UPDATE paragraphs SET content = {content_esc}")
            sql_lines.append(f"WHERE id = {para_where};")
            sql_lines.append("")
            sql_lines.append(
                f"UPDATE paragraph_contents SET explain_text = {content_esc}"
            )
            sql_lines.append(
                f"WHERE paragraph_id = {para_where} AND language = '{LANGUAGE}';"
            )
            sql_lines.append("")
            total += 1

    # Fix image paths
    sql_lines.append("-- Update image paths with actual textbook_id")
    sql_lines.append(
        f"UPDATE paragraphs SET content = REPLACE(content, "
        f"'/textbook-images/0/', '/textbook-images/' || {textbook_id_expr} || '/')"
    )
    sql_lines.append(
        f"WHERE chapter_id IN "
        f"(SELECT id FROM chapters WHERE textbook_id = {textbook_where});"
    )
    sql_lines.append("")
    sql_lines.append(
        f"UPDATE paragraph_contents SET explain_text = REPLACE(explain_text, "
        f"'/textbook-images/0/', '/textbook-images/' || {textbook_id_expr} || '/')"
    )
    sql_lines.append(
        f"WHERE paragraph_id IN (SELECT p.id FROM paragraphs p "
        f"JOIN chapters c ON c.id = p.chapter_id "
        f"WHERE c.textbook_id = {textbook_where});"
    )
    sql_lines.append("")
    sql_lines.append("COMMIT;")
    sql_lines.append(f"-- Updated {total} paragraphs")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))

    print(f"\n  Generated UPDATE SQL: {output_path}")
    print(f"  Paragraphs to update: {total}")


def generate_sql(chapters: list[ParsedChapter], output_path: Path):
    """Generate a SQL file for importing via psql."""
    textbook_title_esc = escape_sql(TEXTBOOK_TITLE)
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE title = {textbook_title_esc}"
        f" AND grade_level = {GRADE_LEVEL} AND is_deleted = false LIMIT 1)"
    )

    sql_lines = [
        f"-- {TEXTBOOK_TITLE} Import (Russian)",
        "-- Generated by load_algebra7_textbook.py",
        "",
        "BEGIN;",
        "",
        "-- Step 1: Create textbook (idempotent)",
        "INSERT INTO textbooks (",
        "    school_id, subject_id, title, subject, grade_level,",
        "    author, publisher, year, isbn, description,",
        "    is_active, is_customized, version, is_deleted",
        ") SELECT",
        f"    NULL, 24, {textbook_title_esc}, 'Алгебра', {GRADE_LEVEL},",
        f"    {escape_sql(AUTHORS)}, {escape_sql(PUBLISHER)}, {YEAR}, {escape_sql(ISBN)},",
        f"    {escape_sql('Учебник для 7 класса общеобразовательных школ. 2-е издание.')},",
        "    true, false, 1, false",
        "WHERE NOT EXISTS (",
        f"    SELECT 1 FROM textbooks WHERE title = {textbook_title_esc}",
        f"    AND grade_level = {GRADE_LEVEL} AND is_deleted = false",
        ");",
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
            f"SELECT {textbook_where}, {chapter_title_esc}, "
            f"{chapter.number}, {ch_order}, false"
        )
        sql_lines.append("WHERE NOT EXISTS (")
        sql_lines.append(
            f"    SELECT 1 FROM chapters WHERE textbook_id = {textbook_where}"
        )
        sql_lines.append(
            f"    AND number = {chapter.number} AND is_deleted = false"
        )
        sql_lines.append(");")
        sql_lines.append("")

        for p_order, para in enumerate(chapter.paragraphs, 1):
            para_number = para.number if para.number != 900 else 100 + p_order
            html_content = md_lines_to_html(para.content_lines, 0)
            key_terms = extract_key_terms(para.content_lines)
            source_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]

            content_esc = escape_sql(html_content)
            title_esc = escape_sql(para.title)
            key_terms_sql = (
                escape_sql(json.dumps(key_terms, ensure_ascii=False)) + "::json"
                if key_terms
                else "NULL"
            )

            para_where = (
                f"(SELECT id FROM paragraphs WHERE chapter_id = {chapter_where}"
                f" AND number = {para_number} AND is_deleted = false LIMIT 1)"
            )

            sql_lines.append(f"-- Paragraph {para_number}: {para.title[:50]}")
            sql_lines.append(
                'INSERT INTO paragraphs (chapter_id, title, number, "order", '
                "content, key_terms, is_deleted)"
            )
            sql_lines.append(
                f"SELECT {chapter_where}, {title_esc}, {para_number}, {p_order},"
            )
            sql_lines.append(f"{content_esc},")
            sql_lines.append(f"{key_terms_sql}, false")
            sql_lines.append("WHERE NOT EXISTS (")
            sql_lines.append(
                f"    SELECT 1 FROM paragraphs WHERE chapter_id = {chapter_where}"
            )
            sql_lines.append(
                f"    AND number = {para_number} AND is_deleted = false"
            )
            sql_lines.append(");")
            sql_lines.append("")

            # ParagraphContent
            sql_lines.append("INSERT INTO paragraph_contents (")
            sql_lines.append("    paragraph_id, language, explain_text,")
            sql_lines.append("    source_hash, status_explain,")
            sql_lines.append(
                "    status_audio, status_slides, status_video, status_cards"
            )
            sql_lines.append(") SELECT")
            sql_lines.append(f"    {para_where}, '{LANGUAGE}',")
            sql_lines.append(f"{content_esc},")
            sql_lines.append(
                f"    {escape_sql(source_hash)}, 'ready',"
            )
            sql_lines.append("    'empty', 'empty', 'empty', 'empty'")
            sql_lines.append("WHERE NOT EXISTS (")
            sql_lines.append("    SELECT 1 FROM paragraph_contents")
            sql_lines.append(
                f"    WHERE paragraph_id = {para_where} AND language = '{LANGUAGE}'"
            )
            sql_lines.append(");")
            sql_lines.append("")
            total_paragraphs += 1

    # Update image paths with actual textbook_id
    sql_lines.append("-- Update image paths with actual textbook_id")
    sql_lines.append(
        f"UPDATE paragraphs SET content = REPLACE(content, "
        f"'/textbook-images/0/', '/textbook-images/' || "
        f"(SELECT id FROM textbooks WHERE title = {textbook_title_esc} "
        f"AND grade_level = {GRADE_LEVEL} AND is_deleted = false LIMIT 1) || '/')"
    )
    sql_lines.append(
        f"WHERE chapter_id IN "
        f"(SELECT id FROM chapters WHERE textbook_id = {textbook_where});"
    )
    sql_lines.append("")
    sql_lines.append(
        f"UPDATE paragraph_contents SET explain_text = REPLACE(explain_text, "
        f"'/textbook-images/0/', '/textbook-images/' || "
        f"(SELECT id FROM textbooks WHERE title = {textbook_title_esc} "
        f"AND grade_level = {GRADE_LEVEL} AND is_deleted = false LIMIT 1) || '/')"
    )
    sql_lines.append(
        f"WHERE paragraph_id IN (SELECT p.id FROM paragraphs p "
        f"JOIN chapters c ON c.id = p.chapter_id "
        f"WHERE c.textbook_id = {textbook_where});"
    )
    sql_lines.append("")
    sql_lines.append("COMMIT;")
    sql_lines.append("")
    sql_lines.append(f"-- Stats: {len(chapters)} chapters, {total_paragraphs} paragraphs")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))

    print(f"\n  Generated SQL: {output_path}")
    print(f"  Chapters: {len(chapters)}, Paragraphs: {total_paragraphs}")
    print(f"\n  To import:")
    print(
        f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/import.sql"
    )
    print(
        f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user "
        f"-d ai_mentor_db -f /tmp/import.sql"
    )


# ── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Load Algebra 7 textbook (Russian) into AI Mentor database"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse only, no DB writes"
    )
    parser.add_argument(
        "--generate-sql",
        type=str,
        metavar="FILE",
        help="Generate SQL file instead of direct DB connection",
    )
    parser.add_argument(
        "--update-content",
        type=str,
        metavar="FILE",
        help="Generate SQL UPDATE file to refresh content",
    )
    parser.add_argument(
        "--exercises",
        type=str,
        metavar="FILE",
        help="Generate SQL file for exercises import",
    )
    args = parser.parse_args()

    print("=" * 70)
    print(f"  {TEXTBOOK_TITLE} Import (Russian)")
    print("=" * 70)

    # 1. Parse MD file
    print(f"\nStep 1: Parsing {MD_FILE.name}...")
    if not MD_FILE.exists():
        print(f"  ERROR: File not found: {MD_FILE}")
        sys.exit(1)

    chapters = parse_textbook(MD_FILE)
    print_parse_stats(chapters)

    if args.dry_run:
        # Print exercise stats
        print("\n--- Exercise Parsing Preview ---")
        total_ex = 0
        for ch in chapters:
            for p in ch.paragraphs:
                exs = extract_exercises_from_paragraph(p)
                if exs:
                    print(f"  §{p.number}: {len(exs)} exercises")
                    for ex in exs[:3]:
                        sub_count = len(ex.sub_exercises)
                        text_preview = " ".join(ex.content_lines)[:60]
                        print(
                            f"    {ex.exercise_number} [{ex.difficulty}] "
                            f"{text_preview}... ({sub_count} sub)"
                        )
                    if len(exs) > 3:
                        print(f"    ... and {len(exs) - 3} more")
                    total_ex += len(exs)
        print(f"\n  Total exercises found: {total_ex}")
        print("\n[DRY RUN] Stopping before DB operations.")
        return

    # Exercises mode
    if args.exercises:
        print("\nStep 2: Parsing answers section...")
        answers = parse_answers_section(MD_FILE)
        print(f"  Found answers for {len(answers)} exercises")

        print("\nStep 3: Generating Exercises SQL file...")
        generate_exercises_sql(chapters, answers, Path(args.exercises))
        return

    # Update content mode
    if args.update_content:
        print("\nStep 2: Generating UPDATE SQL file...")
        generate_update_sql(chapters, Path(args.update_content))
        return

    # Generate SQL mode
    if args.generate_sql:
        print("\nStep 2: Generating SQL file...")
        generate_sql(chapters, Path(args.generate_sql))
        return

    # Direct DB connection mode
    env_path = BACKEND_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
    else:
        print(f"  WARNING: .env not found at {env_path}")

    db_url = get_database_url()
    print("\nStep 2: Connecting to database...")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("\nStep 3: Finding/creating subject...")
        subject_id = find_or_create_subject(session)

        print("\nStep 4: Finding/creating textbook...")
        textbook_id = find_or_create_textbook(session, subject_id)

        print("\nStep 5: Copying images...")
        copy_images(textbook_id)

        print("\nStep 6: Creating chapters and paragraphs...")
        total_paragraphs = 0

        for ch_order, chapter in enumerate(chapters, 1):
            chapter_id = create_chapter(session, textbook_id, chapter, ch_order)

            for p_order, para in enumerate(chapter.paragraphs, 1):
                if para.number == 900:
                    para.number = 100 + p_order
                create_paragraph(
                    session, chapter_id, para, p_order, textbook_id
                )
                total_paragraphs += 1

        session.commit()

        print("\n" + "=" * 70)
        print("  Import completed!")
        print(f"  Textbook ID: {textbook_id}")
        print(f"  Chapters:    {len(chapters)}")
        print(f"  Paragraphs:  {total_paragraphs}")
        print("=" * 70)

    except Exception as e:
        session.rollback()
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
