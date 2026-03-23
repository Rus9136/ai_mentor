#!/usr/bin/env python3
"""
Load 'Информатика 8-класс (Атамура)' into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='ru'.

This is an INFORMATICS textbook — paragraphs use N.N numbering (no § symbols).
Structure: 5 разделов, 19 параграфов, bonus content after Оценивание,
end-of-chapter sections (Дополнительные задания, Проект, Тестовые задания) skipped.

Usage:
    python scripts/load_textbook_60.py --dry-run           # Parse only
    python scripts/load_textbook_60.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_60.py --update-content FILE # Update SQL
"""
import re
import sys
import hashlib
import argparse
from pathlib import Path
from dataclasses import dataclass, field

# -- Path setup ---------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# -- Constants -----------------------------------------------------------------

TEXTBOOK_ID = 60
TEXTBOOK_TITLE = "Информатика 8-класс (Атамура)"
SUBJECT_CODE = "informatics"
GRADE_LEVEL = 8
AUTHORS = "Мухаметжанова С.Т., Тен А., Демидова Л."
PUBLISHER = "Атамура"
YEAR = 2021
LANGUAGE = "ru"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "60" / "textbook_60.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "60"

# Chapter mapping based on СОДЕРЖАНИЕ (TOC)
CHAPTERS = [
    {
        "number": 1,
        "title": "Раздел I. Технические характеристики компьютера и сетей",
        "paragraphs": [
            {"raw": "1.1", "title": "Измерение информации"},
            {"raw": "1.2", "title": "Процессор и его характеристики"},
            {"raw": "1.3", "title": "Компьютерные сети"},
        ],
    },
    {
        "number": 2,
        "title": "Раздел II. Здоровье и безопасность",
        "paragraphs": [
            {"raw": "2.1", "title": "Негативные аспекты использования компьютера"},
            {"raw": "2.2", "title": "Безопасность в сети"},
        ],
    },
    {
        "number": 3,
        "title": "Раздел III. Обработка информации в электронных таблицах",
        "paragraphs": [
            {"raw": "3.1", "title": "Статистические данные"},
            {"raw": "3.2", "title": "Встроенные функции"},
            {"raw": "3.3", "title": "Анализ данных на основе имеющейся информации"},
            {"raw": "3.4", "title": "Решение прикладных задач"},
        ],
    },
    {
        "number": 4,
        "title": "Раздел IV. Программирование алгоритмов на языке Python",
        "paragraphs": [
            {"raw": "4.1", "title": "Цикл while"},
            {"raw": "4.2", "title": "Цикл for"},
            {"raw": "4.3", "title": "Управление циклом: break"},
            {"raw": "4.4", "title": "Управление циклом: continue"},
            {"raw": "4.5", "title": "Управление циклом: else"},
            {"raw": "4.6", "title": "Трассировка алгоритма"},
        ],
    },
    {
        "number": 5,
        "title": "Раздел V. Практическое программирование",
        "paragraphs": [
            {"raw": "5.1", "title": "Постановка проблемы"},
            {"raw": "5.2", "title": "Разработка алгоритма"},
            {"raw": "5.3", "title": "Программирование алгоритма"},
            {"raw": "5.4", "title": "Тестирование программы"},
        ],
    },
]

# Build paragraph lookup: raw_number -> (chapter_number, global_seq_number)
_PARA_LOOKUP: dict[str, tuple[int, int]] = {}
_seq = 0
for _ch in CHAPTERS:
    for _p in _ch["paragraphs"]:
        _seq += 1
        _PARA_LOOKUP[_p["raw"]] = (_ch["number"], _seq)
TOTAL_EXPECTED_PARAGRAPHS = _seq  # 19

# OCR artifacts to fix in titles
OCR_FIXES = {
    "<br>": " ",
    "<br/>": " ",
    "<br />": " ",
    "ПРОТРАММИРОВАНИЕ": "ПРОГРАММИРОВАНИЕ",
    "ПРОТРАММЫ": "ПРОГРАММЫ",
    "СТАТИСТИЧЕСКИЕ ААННЫЕ": "СТАТИСТИЧЕСКИЕ ДАННЫЕ",
    "РҮТНОN": "PYTHON",
    "Cnoco6": "Способ",
}

# Lines/headings to skip entirely (watermarks, ads)
SKIP_PATTERNS = [
    "Все учебники Казахстана",
    "се учебники Казахстана",
    "OKULYK",
    "Книга предоставлена исключительно",
]


# -- Data classes --------------------------------------------------------------


@dataclass
class ParsedParagraph:
    title: str
    number: int          # Global sequential number in DB
    raw_number: str      # Original string (e.g., "1.1", "3.4")
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# -- Regex patterns ------------------------------------------------------------

# Paragraph heading: "## 1.1. TITLE" or "## 3.4" (split heading, no title)
RE_PARA_HEADING = re.compile(
    r"^#{1,3}\s+(\d+\.\d+)\.?\s*(.*)"
)

# End-of-chapter sections to skip (Дополнительные задания, Проект, Тестовые задания)
RE_SKIP_SECTION = re.compile(
    r"^#{1,2}\s+(?:"
    r"(?:ТЕСТОВЫЕ\s+)?ЗАДАНИЯ\s+К\s+РАЗДЕЛУ"
    r"|ДОПОЛНИТЕЛЬНЫЕ\s+ЗАДАНИЯ"
    r"|ЗАДАНИ[ЯЕ]\s+(?:ДЛЯ\s+ПРОЕКТНОЙ|К\s+РАЗДЕЛУ)"
    r"|ПРОЕКТ\s+\d"
    r"|ТЕМЫ\s+ДЛЯ\s+ПРОЕКТНЫХ"
    r"|ТРЕБОВАНИЯ\s+К\s+(?:ВЫПОЛНЕНИЮ|ОФОРМЛЕНИЮ)"
    r")",
    re.IGNORECASE,
)

# Stop markers
RE_STOP = re.compile(
    r"^#{1,2}\s+(ГЛОССАРИЙ\b|гЛОССАРИЙ\b|СПИСОК ИСПОЛЬЗОВАННОЙ\b|ИНТЕРНЕТ-РЕСУРСЫ\b)",
    re.IGNORECASE,
)

# Image reference
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)")

# Footnote references [^N]
RE_FOOTNOTE_REF = re.compile(r"\[\^(\d+)\]")

# Abstract block (Mathpix artifact)
RE_ABSTRACT = re.compile(r"^#{1,4}\s+Abstract", re.IGNORECASE)

# Any heading
RE_HEADING = re.compile(r"^(#{1,4})\s+(.+)")


# -- Helper functions ----------------------------------------------------------


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


def _get_known_title(raw_num: str) -> str | None:
    """Get the known title from TOC for a paragraph number."""
    for ch in CHAPTERS:
        for p in ch["paragraphs"]:
            if p["raw"] == raw_num:
                return p["title"]
    return None


# -- Parser --------------------------------------------------------------------


def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    """Parse the MMD file into chapters and paragraphs."""
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    paragraphs: list[ParsedParagraph] = []
    seen_raw_numbers: set[str] = set()
    current_paragraph: ParsedParagraph | None = None
    in_abstract = False
    in_skip_section = False
    in_code_block = False

    for raw_line in lines:
        line = raw_line.rstrip("\n")

        # Skip watermark lines
        if should_skip_line(line):
            continue

        # Track code blocks to avoid matching Python comments as headings
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if current_paragraph is not None and not in_skip_section:
                current_paragraph.content_lines.append(line)
            continue
        if in_code_block:
            if current_paragraph is not None and not in_skip_section:
                current_paragraph.content_lines.append(line)
            continue

        # Stop markers (Глоссарий, etc.)
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
                    pass  # Fall through to heading detection below
                else:
                    continue
            else:
                if current_paragraph is not None:
                    current_paragraph.content_lines.append(line)
                continue

        # End-of-chapter skip sections
        if RE_SKIP_SECTION.match(line):
            in_skip_section = True
            continue

        # Try to match paragraph heading: "## X.Y. TITLE" or "## X.Y"
        m_heading = RE_PARA_HEADING.match(line)
        if m_heading:
            raw_num = m_heading.group(1)
            title = m_heading.group(2).strip()
            title = fix_ocr(title)

            info = _PARA_LOOKUP.get(raw_num)
            if info and raw_num not in seen_raw_numbers:
                in_skip_section = False
                seen_raw_numbers.add(raw_num)
                # Use TOC title (cleaner than OCR'd heading)
                known_title = _get_known_title(raw_num)
                current_paragraph = ParsedParagraph(
                    title=known_title or title,
                    number=info[1],
                    raw_number=raw_num,
                )
                paragraphs.append(current_paragraph)
                continue
            # Not in lookup or duplicate — treat as content
            if current_paragraph is not None and not in_skip_section:
                current_paragraph.content_lines.append(line)
            continue

        # If in skip section, skip content
        if in_skip_section:
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
        ch_num = _PARA_LOOKUP.get(para.raw_number, (None, None))[0]
        if ch_num and ch_num in chapter_map:
            chapter_map[ch_num].paragraphs.append(para)
        else:
            print(f"  WARNING: {para.raw_number} ({para.title[:40]}) doesn't belong to any chapter!")

    return [ch for ch in sorted(chapter_map.values(), key=lambda c: c.number) if ch.paragraphs]


# -- Content conversion -------------------------------------------------------


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

    # Remove footnote markers
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
    in_code_block = False
    code_lines: list[str] = []

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

    def flush_code():
        nonlocal in_code_block, code_lines
        if code_lines:
            code_text = "\n".join(code_lines)
            html_parts.append(
                f'<pre style="background:#1e293b;color:#e2e8f0;padding:1rem;'
                f'border-radius:0.5rem;overflow-x:auto;margin:1rem 0;font-size:0.9rem">'
                f'<code>{code_text}</code></pre>'
            )
            code_lines = []
        in_code_block = False

    for raw_line in content.split("\n"):
        line = raw_line.rstrip()

        if should_skip_line(line):
            continue

        # Code blocks (Python code is common in this textbook)
        if line.strip().startswith("```"):
            if in_code_block:
                flush_code()
            else:
                flush_paragraph()
                if in_list:
                    flush_list()
                if in_table:
                    flush_table()
                in_code_block = True
            continue
        if in_code_block:
            code_lines.append(line)
            continue

        # Blank line
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

        # Heading
        heading_match = RE_HEADING.match(line)
        if heading_match:
            flush_paragraph()
            level = min(len(heading_match.group(1)) + 1, 6)
            heading_text = heading_match.group(2).strip()
            heading_text = fix_ocr(heading_text)
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

        # Task line: "N) Text"
        task_match = re.match(r"^(\d+)\)\s+(.+)", line.strip())
        if task_match:
            flush_paragraph()
            html_parts.append(
                f'<div style="margin-left:1.5rem">{task_match.group(1)}) {task_match.group(2)}</div>'
            )
            continue

        # Numbered line: "N. Text"
        task_match2 = re.match(r"^(\d+)\.\s+(.+)", line.strip())
        if task_match2:
            flush_paragraph()
            html_parts.append(
                f'<div style="margin-top:0.75rem;margin-bottom:0.25rem">'
                f'<strong>{task_match2.group(1)}.</strong> {task_match2.group(2)}</div>'
            )
            continue

        # Letter-prefixed answer: "a) text", "б) text", etc.
        letter_match = re.match(r"^([a-zа-яёA-ZА-ЯЁ])\)\s+(.+)", line.strip())
        if letter_match:
            flush_paragraph()
            html_parts.append(
                f'<div style="margin-left:1.5rem">{letter_match.group(1)}) {letter_match.group(2)}</div>'
            )
            continue

        # Regular text
        paragraph_lines.append(line)

    # Flush remaining
    if in_code_block:
        flush_code()
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


# -- SQL helpers ---------------------------------------------------------------


def escape_sql(s: str) -> str:
    """Escape string for SQL single-quote literals."""
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


# -- Statistics ----------------------------------------------------------------


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
                f"      {p.raw_number:>7}. {p_title:<58} "
                f"({len(p.content_lines):>4} lines)"
            )
    print(
        f"\n  Total: {len(chapters)} chapters, {total_paragraphs} paragraphs, "
        f"{total_lines} content lines"
    )
    if total_paragraphs != TOTAL_EXPECTED_PARAGRAPHS:
        print(
            f"  WARNING: Expected {TOTAL_EXPECTED_PARAGRAPHS} paragraphs, "
            f"got {total_paragraphs}!"
        )
    print("---")


# -- SQL generation ------------------------------------------------------------


def generate_sql(chapters: list[ParsedChapter], output_path: Path):
    """Generate a SQL file for importing via psql."""
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE id = {TEXTBOOK_ID} AND is_deleted = false)"
    )

    lines = [
        f"-- Информатика 8-класс (Атамура) Textbook Import (Russian)",
        f"-- Generated by load_textbook_60.py",
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

            lines.append(f"-- {para.raw_number}: {para.title[:50]}")
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
        "-- Информатика 8-класс (Атамура) Content UPDATE",
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

            lines.append(f"-- Update {para.raw_number}: {para.title[:50]}")
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


# -- Main ----------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Load Информатика 8-класс (Атамура) textbook into AI Mentor database"
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
    print("  Информатика 8-класс (Атамура) — Textbook Import")
    print("=" * 70)

    print(f"\nStep 1: Parsing {MD_FILE.name}...")
    if not MD_FILE.exists():
        print(f"  ERROR: File not found: {MD_FILE}")
        sys.exit(1)

    chapters = parse_textbook(MD_FILE)
    print_parse_stats(chapters)

    if args.dry_run:
        print("\n[DRY RUN] Stopping before output generation.")
        return

    if args.update_content:
        print(f"\nStep 2: Generating UPDATE SQL file...")
        generate_update_sql(chapters, Path(args.update_content))
        return

    if args.generate_sql:
        print(f"\nStep 2: Generating SQL file...")
        generate_sql(chapters, Path(args.generate_sql))
        return


if __name__ == "__main__":
    main()
