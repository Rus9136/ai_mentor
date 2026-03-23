#!/usr/bin/env python3
"""
Load 'Русский язык 9-класс' into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='ru'.

Structure: 8 Глав (chapters I-VIII), 23 параграфа (numbered 1-23).
Special cases:
  - §1 has plain-text heading (no ## prefix)
  - Review sections at end of each chapter are repeated chapter headings
  - Chapter headings use Roman numerals (mixed Cyrillic І / Latin I)
  - §5 title merged with grammar subtitle in OCR
  - 433 images (Mathpix crops)

Usage:
    python scripts/load_textbook_69.py --dry-run           # Parse only
    python scripts/load_textbook_69.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_69.py --update-content FILE # Update SQL
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

TEXTBOOK_ID = 69
TEXTBOOK_TITLE = "Русский язык 9-класс"
SUBJECT_CODE = "russian"
GRADE_LEVEL = 9
AUTHORS = "Сабитова З.К., Бейсембаев А."
PUBLISHER = "Мектеп"
YEAR = 2019
ISBN = "978-601-07-1266-9"
LANGUAGE = "ru"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "69" / "textbook_69.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "69"

# Chapter mapping from TOC
CHAPTERS = [
    {"number": 1, "title": "Глава I. Конфликты и миротворчество",
     "para_from": 1, "para_to": 3},
    {"number": 2, "title": "Глава II. Сухопутные страны",
     "para_from": 4, "para_to": 5},
    {"number": 3, "title": "Глава III. Традиции и культура",
     "para_from": 6, "para_to": 8},
    {"number": 4, "title": "Глава IV. Ресурсы планеты Земля",
     "para_from": 9, "para_to": 11},
    {"number": 5, "title": "Глава V. Подросток в современном мире",
     "para_from": 12, "para_to": 15},
    {"number": 6, "title": "Глава VI. Всемирная связь в XXI веке",
     "para_from": 16, "para_to": 18},
    {"number": 7, "title": "Глава VII. Дилеммы и выбор",
     "para_from": 19, "para_to": 21},
    {"number": 8, "title": "Глава VIII. Средства массовой информации",
     "para_from": 22, "para_to": 23},
]

# Known paragraph titles from TOC — used as canonical clean titles
PARA_TITLES = {
    1: "Конфликт",
    2: "Что такое миротворчество",
    3: "Миротворческая деятельность Казахстана",
    4: "Проблемы сухопутных стран",
    5: "Казахстан - сухопутная страна",
    6: "Национальная специфика культуры",
    7: "Что такое традиции",
    8: "Язык и культура",
    9: "Виды ресурсов",
    10: "Рациональное использование природных ресурсов",
    11: "Охрана ресурсов Земли",
    12: "Современный подросток",
    13: "Занятия, увлечения подростков",
    14: "Книги в нашей жизни",
    15: "Молодежь и волонтерская деятельность",
    16: "Виды современной связи",
    17: "Всемирная сеть как часть нашей жизни",
    18: "Связь вчера и сейчас",
    19: "Что такое дилемма",
    20: "Проблема выбора",
    21: "Перед вами дилемма",
    22: "Виды средств массовой информации",
    23: "Электронные средства массовой информации",
}

# Lines to skip entirely (watermarks, ads)
SKIP_PATTERNS = [
    "Все учебники Казахстана",
    "OKULYK",
    "Книга предоставлена исключительно в образовательных целях",
]

# Fullwidth → ASCII character mapping
FULLWIDTH_MAP = {
    "．": ".", "：": ":", "－": "-", "，": ",",
    "（": "(", "）": ")", "；": ";", "＂": '"',
}


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

# Paragraph heading: ## N. TITLE, # N. TITLE, or plain N. TITLE (N=1..23)
RE_PARA = re.compile(r"^#{0,2}\s*(\d{1,2})\.\s+(.+)")

# Chapter/review heading: Roman numeral (I-VIII) followed by chapter title
# Uses both Ukrainian І (U+0406) and Latin I/V/X
# Requires at least #{1} to avoid matching plain-text Roman numerals in exercises
RE_CHAPTER_HEADING = re.compile(r"^#{1,2}\s+([ІIVX]{1,5})\.?\s+(.+)")

# Stop markers — everything after these is appendix
# Require #{1,2} to avoid matching "Содержание" in regular content text
RE_STOP = re.compile(
    r"^#{1,2}\s+(ЧТО Я УМЕЮ|ОРФОГРАФИЧЕСКИЙ|СОДЕРЖАНИЕ\b)",
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
    return any(pattern in line for pattern in SKIP_PATTERNS)


def is_allcaps_title(title: str) -> bool:
    """Check if title starts with ALL CAPS words (paragraph titles are uppercase)."""
    words = title.split()
    for word in words:
        clean = word.strip(",-!?.;:«»\"'()")
        if len(clean) <= 1:
            continue  # Skip single chars like "О", "В"
        if "$" in clean:
            continue  # Skip LaTeX expressions like "$B$"
        if not any(c.isalpha() for c in clean):
            continue  # Skip non-letter tokens
        return clean == clean.upper()
    return False


def get_chapter_for_para(para_number: int) -> dict | None:
    """Find which chapter a paragraph belongs to based on paragraph number."""
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
    seen_paras: set[int] = set()
    in_skip: bool = True  # Start in skip mode (preamble before §1)
    in_abstract: bool = False

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        line_norm = normalize_fullwidth(line)

        # Skip watermark lines
        if should_skip_line(line):
            continue

        # Stop markers — everything after is appendix
        if RE_STOP.match(line_norm):
            break

        # ── Abstract block handling (Mathpix artifact) ──
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
                if current_paragraph is not None and not in_skip:
                    current_paragraph.content_lines.append(line)
                continue

        # ── 1. Check for paragraph heading: ## N. TITLE or N. TITLE ──
        m = RE_PARA.match(line_norm)
        if m:
            num = int(m.group(1))
            title_raw = m.group(2)
            if (num in PARA_TITLES
                    and num not in seen_paras
                    and is_allcaps_title(title_raw)):
                # Valid paragraph boundary — use canonical title from TOC
                in_skip = False
                current_paragraph = ParsedParagraph(
                    title=PARA_TITLES[num],
                    number=num,
                    raw_number=str(num),
                )
                paragraphs.append(current_paragraph)
                seen_paras.add(num)
                continue

        # ── 2. Check for chapter/review heading (Roman numeral + ALL CAPS) ──
        # This catches both chapter starts AND review sections.
        # Chapter starts are harmless (we're already in skip from preamble
        # or previous review). Review sections correctly enter skip mode.
        m_ch = RE_CHAPTER_HEADING.match(line_norm)
        if m_ch:
            rest = m_ch.group(2)
            if is_allcaps_title(rest):
                in_skip = True
                continue

        # ── 3. Skip content during review or preamble ──
        if in_skip:
            continue

        # ── 4. Accumulate content lines ──
        if current_paragraph is not None:
            current_paragraph.content_lines.append(line)

    # ── Organize paragraphs into chapters ──
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
            print(
                f"  WARNING: §{para.number} ({para.title[:40]}) "
                f"doesn't belong to any chapter!"
            )

    return [
        ch for ch in sorted(chapter_map.values(), key=lambda c: c.number)
        if ch.paragraphs
    ]


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
            html_parts.append(
                "<ul style='margin:0.5rem 0;padding-left:1.5rem'>"
            )
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

        # Task line: "N. Text" or "NА. Text" (numbered items)
        task_match = re.match(r"^(\d+[А-Яа-яA-Za-z]?)\.\s+(.+)", line.strip())
        if task_match:
            flush_paragraph()
            task_num = task_match.group(1)
            task_text = task_match.group(2)
            html_parts.append(
                f'<div style="margin-top:0.75rem;margin-bottom:0.25rem">'
                f'<strong>{task_num}.</strong> {task_text}</div>'
            )
            continue

        # Subtask line: "N) text" or "а) text"
        sub_match = re.match(
            r"^([а-яa-z\d]+)\)\s+(.+)", line.strip()
        )
        if sub_match:
            flush_paragraph()
            html_parts.append(
                f'<div style="margin-left:1.5rem">'
                f'{sub_match.group(1)}) {sub_match.group(2)}</div>'
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
                f"      §{p.raw_number:>3}. {p_title:<58} "
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
        f"-- Русский язык 9-класс Textbook Import",
        f"-- Generated by load_textbook_69.py",
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
            f"SELECT {textbook_where}, {chapter_title_esc}, "
            f"{chapter.number}, {ch_order}, false"
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
                f'INSERT INTO paragraphs (chapter_id, title, number, "order", '
                f"content, is_deleted)"
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
            lines.append(
                f"    source_hash, status_explain,"
            )
            lines.append(
                f"    status_audio, status_slides, status_video, status_cards"
            )
            lines.append(f") SELECT")
            lines.append(f"    {para_where}, '{LANGUAGE}',")
            lines.append(f"{content_esc},")
            lines.append(
                f"    {escape_sql(source_hash)}, 'ready',"
            )
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
    lines.append(
        f"-- Stats: {len(chapters)} chapters, {total_paragraphs} paragraphs"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

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


def generate_update_sql(chapters: list[ParsedChapter], output_path: Path):
    """Generate SQL UPDATE statements to refresh content in existing records."""
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE id = {TEXTBOOK_ID} AND is_deleted = false)"
    )

    lines = [
        "-- Русский язык 9-класс Content UPDATE",
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
            source_hash = hashlib.sha256(
                html_content.encode()
            ).hexdigest()[:64]

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
        f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user "
        f"-d ai_mentor_db -f /tmp/update.sql"
    )


# ── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Load Русский язык 9-класс textbook into AI Mentor database"
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
    print("  Русский язык 9-класс — Textbook Import")
    print("=" * 70)

    # 1. Parse MMD file
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

    print(
        "\nNo action specified. Use --dry-run, --generate-sql, or --update-content"
    )


if __name__ == "__main__":
    main()
