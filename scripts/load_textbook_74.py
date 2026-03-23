#!/usr/bin/env python3
"""
Load 'Русская литература 8-класс часть 2' into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='ru'.

This is a LITERATURE textbook — no exercises, 2 раздела (III-IV), 8 тем (9-16).
Structure: Раздел → Тема N. Author (paragraph boundary).
All other headings (literary analysis sections, work titles, poems) are internal content.

Usage:
    python scripts/load_textbook_74.py --dry-run           # Parse only
    python scripts/load_textbook_74.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_74.py --update-content FILE # Update SQL
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

TEXTBOOK_ID = 74  # Already exists in DB
TEXTBOOK_TITLE = "Русская литература 8-класс часть 2"
SUBJECT_CODE = "russian_lit"
GRADE_LEVEL = 8
AUTHORS = "Шашкина Г.З., Анищенко О., Шмельцер В."
PUBLISHER = "Мектеп"
YEAR = 2018
ISBN = ""
LANGUAGE = "ru"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "74" / "textbook_74.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "74"

# ── TOC-based structure ─────────────────────────────────────────────────────

# Canonical titles from TOC (OCR-clean)
TEMA_TITLES = {
    9:  "Николай Васильевич Гоголь",
    10: "Антон Павлович Чехов",
    11: "Василий Макарович Шукшин",
    12: "Михаил Юрьевич Лермонтов",
    13: "Александр Степанович Грин",
    14: "Антуан де Сент-Экзюпери",
    15: "Марина Ивановна Цветаева",
    16: "Анна Андреевна Ахматова",
}

# Тема → chapter mapping
TEMA_TO_CHAPTER = {
    9: 3, 10: 3, 11: 3,
    12: 4, 13: 4, 14: 4, 15: 4, 16: 4,
}

CHAPTER_TITLES = {
    3: "Сатира и юмор",
    4: "Мечты и реальность",
}

# First tema in each chapter (intro content gets prepended to this tema)
FIRST_TEMA_IN_CHAPTER = {3: 9, 4: 12}

# Chapter title headings to skip (they appear right after ## Раздел)
CHAPTER_TITLE_HEADINGS = {"САТИРА И ЮМОР", "МЕЧТЫ И РЕАЛЬНОСТЬ"}

# ── OCR fixes ───────────────────────────────────────────────────────────────

OCR_FIXES = {
    "．": ".",
    "，": ",",
    "：": ":",
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
    number: int
    raw_number: str
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# ── Regex patterns ──────────────────────────────────────────────────────────

# Тема heading — handles OCR Latin/Cyrillic mix: Tema, Тема, Tема, TEMA, etc.
# Requires digit after "Тема" to avoid matching "ТЕМА ЛЮБВИ..." style headings
RE_TEMA = re.compile(
    r"^#{1,2}\s+[ТTт][еeЕE][мmМM][аaАA]\s+(\d+)\.?\s*(.*)",
    re.IGNORECASE,
)

# Раздел (chapter) heading
RE_RAZDEL = re.compile(
    r"^#{1,2}\s+Раздел\s+(I{1,3}V?|IV|V?I{0,3})\b",
    re.IGNORECASE,
)

# Stop markers — glossary, TOC, publisher info
RE_STOP = re.compile(
    r"^#{1,2}\s+(КРАТКИЙ\s+СЛОВАРЬ\b|Содержание\b|回)",
    re.IGNORECASE,
)

# Image reference in markdown
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)")

# Footnote references [^N]
RE_FOOTNOTE_REF = re.compile(r"\[\^(\d+)\]")

# Abstract block (Mathpix artifact)
RE_ABSTRACT = re.compile(r"^#{1,4}\s+Abstract", re.IGNORECASE)


# ── Helper functions ────────────────────────────────────────────────────────

def roman_to_int(s: str) -> int:
    """Convert Roman numeral string to integer."""
    vals = {"I": 1, "V": 5, "X": 10, "L": 50}
    result = 0
    for i, c in enumerate(s.upper()):
        v = vals.get(c, 0)
        if i + 1 < len(s) and v < vals.get(s[i + 1].upper(), 0):
            result -= v
        else:
            result += v
    return result


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


# ── Parser ──────────────────────────────────────────────────────────────────

def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    """Parse the MMD file into chapters and paragraphs."""
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Chapter storage
    chapter_map: dict[int, ParsedChapter] = {}
    for num, title in CHAPTER_TITLES.items():
        chapter_map[num] = ParsedChapter(title=title, number=num)

    current_chapter_num: int | None = None
    current_paragraph: ParsedParagraph | None = None
    intro_buffer: list[str] = []
    content_started = False
    in_abstract = False

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")

        # Skip watermark lines
        if should_skip_line(line):
            continue

        # Stop markers
        if RE_STOP.match(line):
            break

        # Skip Abstract blocks (Mathpix artifact)
        if RE_ABSTRACT.match(line):
            in_abstract = True
            continue
        if in_abstract:
            if line.strip() == "" or line.startswith("#"):
                in_abstract = False
                if not line.startswith("#"):
                    continue
            else:
                if current_paragraph is not None:
                    current_paragraph.content_lines.append(line)
                continue

        # Check for Раздел (chapter) heading
        m = RE_RAZDEL.match(line)
        if m:
            content_started = True
            roman = m.group(1)
            current_chapter_num = roman_to_int(roman)
            intro_buffer = []
            current_paragraph = None
            continue

        if not content_started:
            continue

        # Check for Тема heading (paragraph boundary)
        m = RE_TEMA.match(line)
        if m:
            tema_num = int(m.group(1))
            title = TEMA_TITLES.get(tema_num, fix_ocr(m.group(2).strip()))
            ch_num = TEMA_TO_CHAPTER.get(tema_num, current_chapter_num)

            current_paragraph = ParsedParagraph(
                title=title,
                number=tema_num,
                raw_number=str(tema_num),
            )

            # Prepend intro buffer to first tema of each chapter
            if ch_num and tema_num == FIRST_TEMA_IN_CHAPTER.get(ch_num):
                current_paragraph.content_lines = list(intro_buffer)
                intro_buffer = []

            if ch_num and ch_num in chapter_map:
                chapter_map[ch_num].paragraphs.append(current_paragraph)
            continue

        # If we're in a chapter but before the first Тема → buffer as intro
        if current_chapter_num is not None and current_paragraph is None:
            heading_match = re.match(r"^#{1,2}\s+(.+)", line)
            if heading_match:
                heading_text = heading_match.group(1).strip()
                if heading_text.upper() in CHAPTER_TITLE_HEADINGS:
                    continue
            intro_buffer.append(line)
            continue

        # Regular content — add to current paragraph
        if current_paragraph is not None:
            current_paragraph.content_lines.append(line)

    return [ch for ch in sorted(chapter_map.values(), key=lambda c: c.number)
            if ch.paragraphs]


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

    # Remove footnote markers
    content = RE_FOOTNOTE_REF.sub("", content)

    # Clean <br> in headings (OCR artifact)
    content = re.sub(r"<br\s*/?\s*>", " ", content)

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

        if should_skip_line(line):
            continue

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

        # Task line: "N. Text"
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

        # Subtask line: "a) text", "б) text"
        subtask_match = re.match(r"^([а-яa-z])\)\s+(.+)", line.strip())
        if subtask_match:
            flush_paragraph()
            sub_letter = subtask_match.group(1)
            sub_text = subtask_match.group(2)
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
                f"      Тема {p.raw_number:>2}. {p_title:<58} "
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
        f"-- Русская литература 8-класс часть 2 — Textbook Import",
        f"-- Generated by load_textbook_74.py",
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

            sql_lines.append(f"-- Тема {para.raw_number}: {para.title[:50]}")
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

            # ParagraphContent for 'ru'
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
        "-- Русская литература 8-класс часть 2 — Content UPDATE",
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

            sql_lines.append(f"-- Update Тема {para.raw_number}: {para.title[:50]}")
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
        description="Load Русская литература 8-класс часть 2 into AI Mentor database"
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
    print("  Русская литература 8-класс часть 2 — Textbook Import")
    print("=" * 70)

    # 1. Parse MMD file
    print(f"\nStep 1: Parsing {MD_FILE.name}...")
    if not MD_FILE.exists():
        print(f"  ERROR: File not found: {MD_FILE}")
        sys.exit(1)

    chapters = parse_textbook(MD_FILE)

    if not chapters:
        print("  ERROR: No chapters parsed!")
        sys.exit(1)

    print_parse_stats(chapters)

    # 2. Verify image directory
    if IMAGES_SRC_DIR.exists():
        img_count = len(list(IMAGES_SRC_DIR.glob("*.jpg")))
        print(f"\n  Images directory: {IMAGES_SRC_DIR}")
        print(f"  Images found: {img_count}")
    else:
        print(f"\n  WARNING: Images directory not found: {IMAGES_SRC_DIR}")

    # 3. Generate SQL or dry-run
    if args.generate_sql:
        generate_sql(chapters, Path(args.generate_sql))
    elif args.update_content:
        generate_update_sql(chapters, Path(args.update_content))
    elif args.dry_run:
        print("\n  Dry run complete. Use --generate-sql FILE to generate SQL.")
    else:
        print("\n  No action specified. Use --dry-run, --generate-sql, or --update-content.")


if __name__ == "__main__":
    main()
