#!/usr/bin/env python3
"""
Load 'Информатика 11-сынып' into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='kk'.

This is an INFORMATICS textbook — paragraphs use N.M. numbering (no § symbols).
Some paragraph headings have ## prefix, others are plain text at start of line.

Usage:
    python scripts/load_textbook_39.py --dry-run           # Parse only
    python scripts/load_textbook_39.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_39.py --update-content FILE # Update SQL
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

TEXTBOOK_ID = 39  # Already exists in DB
TEXTBOOK_TITLE = "Информатика 11-сынып"
SUBJECT_CODE = "informatics"
GRADE_LEVEL = 11
AUTHORS = "Исабаева Д.Н., Абдулкаримова Г.А., Рахимжанова Л.Б., Аубекова М.А."
PUBLISHER = "Атамура"
YEAR = 2020
LANGUAGE = "kk"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "39" / "textbook_39.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "39"

# Chapter mapping based on МАЗМҰНЫ (TOC)
CHAPTERS = [
    {
        "number": 1,
        "title": "І бөлім. ЖАСАНДЫ ИНТЕЛЛЕКТ",
        "paragraphs": [
            {"raw": "1.1", "title": "ЖАСАНДЫ ИНТЕЛЛЕКТ - ЗАМАНАУИ АҚПАРАТТЫҚ ТЕХНОЛОГИЯНЫҢ НЕГІЗІ"},
            {"raw": "1.2", "title": "МАШИНАЛЫҚ ОҚЫТУ"},
            {"raw": "1.3", "title": "НЕЙРОНДЫҚ ЖЕЛІНІ ҰЙЫМДАСТЫРУ"},
            {"raw": "1.4", "title": "НЕЙРОНДЫҚ ЖЕЛІНІ ЖОБАЛАУ"},
        ],
    },
    {
        "number": 2,
        "title": "II бөлім. 3D ЖОБАЛАУ",
        "paragraphs": [
            {"raw": "2.1", "title": "ВИРТУАЛДЫ ЖӘНЕ КЕҢЕЙТІЛГЕН ШЫНАЙЫЛЫҚ"},
            {"raw": "2.2", "title": "ВИРТУАЛДЫ ШЫНАЙЫЛЫҚТАҒЫ АДАМ"},
            {"raw": "2.3", "title": "3D ПАНОРАМА"},
            {"raw": "2.4", "title": "ВИРТУАЛДЫ ТУР"},
        ],
    },
    {
        "number": 3,
        "title": "III бөлім. АППАРАТТЫҚ ҚАМТАМАСЫЗ ЕТУ",
        "paragraphs": [
            {"raw": "3.1", "title": "ВИРТУАЛДЫ МАШИНАЛАР"},
            {"raw": "3.2", "title": "МОБИЛЬДІ ҚҰРЫЛҒЫЛАРДЫҢ СИПАТТАМАСЫ"},
        ],
    },
    {
        "number": 4,
        "title": "IV бөлім. ЗАТТАР ИНТЕРНЕТІ",
        "paragraphs": [
            {"raw": "4.1", "title": "«ЗАТТАР ИНТЕРНЕТІ» ДЕГЕНІМІЗ НЕ?"},
            {"raw": "4.2", "title": "«АҚЫЛДЫ ҮЙ»"},
            {"raw": "4.3", "title": "«АҚЫЛДЫ ҮЙ» ЖОБАСЫН ӘЗІРЛЕУ"},
            {"raw": "4.4", "title": "МОБИЛЬДІ ҚОСЫМШАНЫ ҚҰРУ ҮШІН КІРІСПЕ"},
            {"raw": "4.5", "title": "МОБИЛЬДІ ҚОСЫМШАЛАРДЫ ҚҰРУ"},
        ],
    },
    {
        "number": 5,
        "title": "V бөлім. IT STARTUP",
        "paragraphs": [
            {"raw": "5.1", "title": "STARTUP ҚАЛАЙ ІСКЕ ҚОСЫЛАДЫ?"},
            {"raw": "5.2", "title": "ЖОБАНЫ АЛҒА ЖЫЛЖЫТУ"},
            {"raw": "5.3", "title": "IT STARTUP ЖӘНЕ ЖАРНАМА"},
        ],
    },
    {
        "number": 6,
        "title": "VI бөлім. ЦИФРЛЫҚ САУАТТЫЛЫҚ",
        "paragraphs": [
            {"raw": "6.1", "title": "ҚАЗАҚСТАНДЫ ЦИФРЛАНДЫРУ"},
            {"raw": "6.2", "title": "BLOCKCHAIN (БЛОКЧЕЙН) ТЕХНОЛОГИЯСЫ"},
            {"raw": "6.3", "title": "АҚПАРАТТЫ ҚҰҚЫҚТЫҚ ҚОРҒАУ"},
            {"raw": "6.4", "title": "ЭЛЕКТРОНДЫҚ ЦИФРЛЫҚ ҚОЛТАҢБА ЖӘНЕ СЕРТИФИКАТ"},
            {"raw": "6.5", "title": "ЭЛЕКТРОНДЫҚ ҮКІМЕТ"},
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
TOTAL_EXPECTED_PARAGRAPHS = _seq  # 23

# OCR artifacts to fix in titles
OCR_FIXES = {
    "<br>": " ",
    "<br/>": " ",
    "<br />": " ",
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
    raw_number: str      # Original string (e.g., "1.1", "2.3")
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# -- Regex patterns ------------------------------------------------------------

# Paragraph heading WITH ## prefix: "## 1.1. TITLE" or "## 4.5. TITLE"
RE_PARA_HASH = re.compile(
    r"^#{1,3}\s+(\d+\.\d+)\.\s+(.+)", re.IGNORECASE
)

# Paragraph heading WITHOUT ## prefix: "1.2. TITLE" (plain text at start of line)
RE_PARA_PLAIN = re.compile(
    r"^(\d+\.\d+)\.\s+(.+)"
)

# Chapter heading: "## I белім.", "## II бөлім.", "## IV белім." etc.
RE_CHAPTER = re.compile(
    r"^#{1,2}\s+(?:I{1,3}|IV|V|VI?)\s+[Бб][ΘОоeе][лl][IіiIM]+",
    re.IGNORECASE,
)

# Stop markers — end of book content
RE_STOP = re.compile(
    r"^(?:#{1,2}\s+)?(ГЛОССАРИЙ\b|гЛОССАРИЙ\b|ПАЙДАЛАНЫЛҒАН\b|MA3M|МАЗМҰНЫ\b)",
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

# Section-level markers (tests, projects, summaries) — treated as internal
RE_SECTION_END = re.compile(
    r"(БӨЛІМ[ГНЕІ]|ТЕСТ\s+ТАПСЫРМАЛАРЫ|ЖОБАЛЫҚ\s+ЖҰМЫС|ТҮЙІНДЕМЕСІ|"
    r"тоқсанды\s+қорытындылау)",
    re.IGNORECASE,
)


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


def resolve_paragraph_number(raw_num: str) -> tuple[str, int] | None:
    """Resolve a raw paragraph number to (raw_display, global_seq_number)."""
    info = _PARA_LOOKUP.get(raw_num)
    if info:
        return (raw_num, info[1])
    return None


# -- Parser --------------------------------------------------------------------


def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    """Parse the MMD file into chapters and paragraphs."""
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    paragraphs: list[ParsedParagraph] = []
    current_paragraph: ParsedParagraph | None = None
    in_abstract = False

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")

        # Skip watermark lines
        if should_skip_line(line):
            continue

        # Stop markers
        if RE_STOP.match(line):
            break

        # Skip Abstract blocks
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

        # Try paragraph heading WITH ## prefix: "## 1.1. TITLE"
        m_hash = RE_PARA_HASH.match(line)
        if m_hash:
            raw_num = m_hash.group(1)  # e.g., "1.1"
            title = m_hash.group(2).strip()
            title = fix_ocr(title)
            info = resolve_paragraph_number(raw_num)
            if info:
                current_paragraph = ParsedParagraph(
                    title=title,
                    number=info[1],
                    raw_number=raw_num,
                )
                paragraphs.append(current_paragraph)
                continue
            # If not in lookup, treat as internal heading content
            if current_paragraph is not None:
                current_paragraph.content_lines.append(line)
            continue

        # Try paragraph heading WITHOUT ## prefix: "1.2. TITLE"
        m_plain = RE_PARA_PLAIN.match(line)
        if m_plain:
            raw_num = m_plain.group(1)  # e.g., "1.2"
            title = m_plain.group(2).strip()
            title = fix_ocr(title)
            info = resolve_paragraph_number(raw_num)
            if info:
                current_paragraph = ParsedParagraph(
                    title=title,
                    number=info[1],
                    raw_number=raw_num,
                )
                paragraphs.append(current_paragraph)
                continue
            # If not in lookup, treat as regular content
            if current_paragraph is not None:
                current_paragraph.content_lines.append(line)
            continue

        # Chapter headings — skip
        if RE_CHAPTER.match(line):
            continue

        # All other headings — treated as internal content
        heading_match = RE_HEADING.match(line)
        if heading_match:
            if current_paragraph is not None:
                current_paragraph.content_lines.append(line)
            continue

        # Accumulate content lines
        if current_paragraph is not None:
            current_paragraph.content_lines.append(line)

    # Use known titles from TOC instead of OCR-mangled ones
    for para in paragraphs:
        for ch in CHAPTERS:
            for p in ch["paragraphs"]:
                if p["raw"] == para.raw_number:
                    para.title = p["title"]
                    break

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

        # Task line: "N. Text"
        task_match2 = re.match(r"^(\d+)\.\s+(.+)", line.strip())
        if task_match2:
            flush_paragraph()
            html_parts.append(
                f'<div style="margin-top:0.75rem;margin-bottom:0.25rem">'
                f'<strong>{task_match2.group(1)}.</strong> {task_match2.group(2)}</div>'
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
        f"-- Информатика 11-сынып Textbook Import (Kazakh)",
        f"-- Generated by load_textbook_39.py",
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

            # ParagraphContent for 'kk'
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
        "-- Информатика 11-сынып Content UPDATE",
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
        description="Load Информатика 11-сынып textbook into AI Mentor database"
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
    print("  Информатика 11-сынып — Textbook Import")
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

    print("\nNo action specified. Use --dry-run, --generate-sql, or --update-content.")


if __name__ == "__main__":
    main()
