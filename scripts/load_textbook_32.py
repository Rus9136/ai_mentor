#!/usr/bin/env python3
"""
Load 'Қазақстан тарихы 5-сынып' (Kazakh) into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='kk'.

This is a HISTORY textbook — no exercises.
Chapters are determined by § number ranges from the TOC (МАЗМУНЫ).
7 chapters, 64 paragraph sections (§1 through §64).

Usage:
    python scripts/load_textbook_32.py --dry-run           # Parse only
    python scripts/load_textbook_32.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_32.py --update-content FILE # Update SQL
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

TEXTBOOK_ID = 32  # Already exists in DB
TEXTBOOK_TITLE = "Қазақстан тарихы 5-сынып"
SUBJECT_CODE = "history_kz"
GRADE_LEVEL = 5
AUTHORS = "Т.Омарбеков, Г.Хабижанова, Т.Қартаева, М.Ноғайбаева"
PUBLISHER = "Мектеп"
YEAR = 2017
ISBN = ""
LANGUAGE = "kk"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "32" / "textbook_32.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "32"

# Chapter mapping: § number ranges → chapter info
# Based on МАЗМУНЫ (Table of Contents)
CHAPTERS = [
    {
        "number": 1,
        "title": "I бөлім. ҚАЗАҚСТАНДАҒЫ ЕЖЕЛГІ АДАМДАРДЫҢ ӨМІРІ",
        "para_from": 1,
        "para_to": 18,
    },
    {
        "number": 2,
        "title": "II бөлім. ЕЖЕЛГІ КӨШПЕЛІЛЕР ӨМІРІ",
        "para_from": 19,
        "para_to": 26,
    },
    {
        "number": 3,
        "title": "III бөлім. САҚТАР",
        "para_from": 27,
        "para_to": 42,
    },
    {
        "number": 4,
        "title": "IV бөлім. ҮЙСІНДЕР МЕН ҚАҢЛЫЛАР",
        "para_from": 43,
        "para_to": 50,
    },
    {
        "number": 5,
        "title": "V бөлім. ҒҰНДАР",
        "para_from": 51,
        "para_to": 56,
    },
    {
        "number": 6,
        "title": "VI бөлім. САРМАТТАР",
        "para_from": 57,
        "para_to": 60,
    },
    {
        "number": 7,
        "title": "VII бөлім. ЕЖЕЛГІ ҚАЗАҚСТАН ТАРИХЫНА ШОЛУ",
        "para_from": 61,
        "para_to": 64,
    },
]

# Headings that are internal content within a paragraph (NOT paragraph boundaries)
INTERNAL_HEADINGS = {
    # Lesson structure
    "Бүгінгі сабақта:", "Бугінгі сабақта:", "Бугінті сабақта:", "Бүгінті сабақта:",
    "Бүтінгі сабақта:", "Бүтінті сабақта:", "Бүrінгі сабақта:",
    "Тірек сездер:", "Тірек сөздер:", "Тірек сездер",
    # Activities / research
    "Ойлан!", "Ізден!", "lзденt", "Анықта!",
    "Тапсырма", "Тапсырмалар",
    "Біліміңді тексер!", "Біліміңді тексер1",
    "Есте сақта!", "Еске түсір!",
    # Fun facts / info blocks
    "Бұл қызық!", "Бул қызық!", "Бұл қызық",
    "Бұл маңызды!", "Бұл кызык!",
    # End-of-chapter review
    "Бекіту сұрақтары", "Бекіту сұрақтары мен тапсырмалары",
    # Preamble
    "Алғы сез", "Алғы сөз",
    "КІРІСПЕ САБАҚ",
    # Title page / book header
    "ҚАЗАҚСТАН тарихы",
    "Жалпы білім беретін мектептін 5 -сыныбына арналған окулык",
    "МАЗМУНЫ",
    # Chapter sub-section headings (NOT paragraph boundaries)
    "АЛҒАШҚЫ АДАМДАРДЫҢ",
    "ҚАЗАҚСТАН АУМАҒЫНДАҒЫ ТАС ДӘУІРІНІҢ ТҰРАҚТАРЫ",
    "АДАМДАРДЫҢ ШАРУАШЫЛЫҚ",
    "БОТАЙ МӘДЕНИЕТІ",
    "АНДРОН ЖӘНЕ БЕҒАЗЫДӘНДІБАЙ МӘДЕНИЕТТЕРІ",
    "ЕЖЕЛГІ КӨШПЕЛІЛЕРДІҢ МАТЕРИАЛДЫҚ МӘДЕНИЕТІ",
    "САҚТАР ТУРАЛЫ ТАРИХИ МӘЛІМЕТТЕР",
    '"АЛТЫН АДАМ" АРХЕОЛОГИЯЛЫҚ ОЛЖАСЫ',
    "ШІЛІКТІ ЖӘНЕ БЕСШАТЫР ПАТША ҚОРҒАНДАРЫ",
    "БЕРЕЛ ҚОРҒАНДАРЫ",
    "ТАСМОЛА АРХЕОЛОГИЯЛЫҚ МӘДЕНИЕТІ",
    "САҚ ПАТШАЙЫМЫ ТОМИРИС",
    "ШЫРАҚТЫҢ ЕРЛІГІ",
    "САҚТАРДЫҢ АЛЕКСАНДР МАКЕДОНСКИЙ ӘСКЕРІНЕ ҚАРСЫ КҮРЕСI",
    "ҚАҢЛыЛАРДЫҢ ҚАЛАЛЫқ МӘДЕНИЕТІНІҢ ДАМУЫ",
    "ҚАҢЛыЛАРДЫҢ қОҒАМДЫҚ ҚҰРЫЛЫСЫ",
    "ҒҰН ТАЙПАЛАРЫНЫҢ БІРІГУІ",
    "ҒҰНДАРДЫҢ КӨРШІ МЕМЛЕКЕТТЕРМЕН ҚАРЫМ-ҚАТЫНАСТАРЫ",
    "ҒҰНДАРДЫҢ БАТЫСҚА ҚОНЫС АУДАРУЫ",
    "АТТИЛА ЖӘНЕ ОНЫҢ ЖАУЛАУШЫЛЫҚ ЖОРЫҚТАРЫ",
    "САРМАТТАРДЫҢ ҚОҒАМДЫҚ ҚҰРЫЛЫСЫ МЕН ШАРУАШЫЛЫҚ ӨМІРІ",
    "САРМАТТАРДЫҢ САЯСИ ТАРИХЫ",
    "ЕЖЕЛГІ ҚАЗАҚСТАН АДАМДАРЫНЫҢ АНТРОПОЛОГИЯЛЫҚ ТҰРПАТЫ",
    "ЕЖЕЛГІ ҚАЗАҚСТАНҒА САЯХАТ",
    # Sub-topic headings within paragraphs
    "Ежелгі Қазакстан тарихы нені окытады",
    "Уакыт сызбасы",
    "Археология ғылымы туралы не білеміз",
    "Ежелгі адамдардын Казакстан жеріндегі коныстары мен тұрактары",
    "Ботай мадениеті дегеніміз не",
    "Кешпелі малшаруашылығынын кандай түрлері болған",
    "Жылқының сақтар өміріндегі маңызы",
    "Уйсіндер мен канлылардын тілі мен жазуы",
    "Уйсіндердін археологиялык ескерткіштері",
    "Аққу - киелі құс",
    "Алтын қорыған самұрық",
    # Watermarks
    "Все учебники Казахстана",
    "OKULYK",
    # End-of-book sections (will also be caught by RE_STOP)
    "КАЙТАЛАУҒА АРНАЛҒАН",
    "ПЛОССАРИЙ",
    "ИСТОРИЯ КАЗАХСТАНА",
}

# OCR artifacts to fix in paragraph titles
OCR_FIXES = {
    "<br>": " ",
    "<br/>": " ",
    "<br />": " ",
    # Fullwidth characters (Mathpix OCR)
    "．": ".",
    "？": "?",
    "：": ":",
    "（": "(",
    "）": ")",
    "，": ",",
}

# Lines/headings to skip entirely (watermarks, ads)
SKIP_PATTERNS = [
    "Все учебники Казахстана",
    "OKULYK",
]


# ── Data classes ────────────────────────────────────────────────────────────


@dataclass
class ParsedParagraph:
    title: str
    number: int      # First § number
    raw_number: str   # Original string
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# ── Regex patterns ──────────────────────────────────────────────────────────

# Paragraph heading: "## § 1.", "## §19.", "§5.", "§51．" (fullwidth dot)
RE_PARAGRAPH = re.compile(
    r"^(?:#{1,2}\s+)?§\s*(\d+(?:-\d+)?)[.．\s]+(.+)", re.IGNORECASE
)

# Stop markers — everything after these is skipped
RE_STOP = re.compile(
    r"^#{1,2}\s+(КАЙТАЛАУҒА\b|ПЛОССАРИЙ\b|ГЛОССАРИЙ\b|ИСТОРИЯ\s+КАЗАХСТАНА\b)",
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
    # Collapse multiple spaces
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

    # Heading that starts with image ref
    if clean.startswith("!["):
        return True

    # Heading that starts with $ (math formula)
    if clean.startswith("$"):
        return True

    # Heading that starts with a digit (task numbers, dates)
    if clean and clean[0].isdigit():
        return True

    # Heading starting with 0 (icon marker)
    if clean.startswith("0 ") or clean.startswith("0«"):
        return True

    # Very long headings are usually content, not boundaries
    if len(clean) > 80:
        return True

    # Questions (contain ?)
    if "?" in clean or "？" in clean:
        return True

    # Single word or very short headings that are just formatting
    if len(clean) <= 3:
        return True

    # Contains \section* (LaTeX OCR artifact embedded in heading)
    if "\\section*" in clean:
        return True

    # Roman numeral chapter markers (I, II, III, IV, V, VI, VII)
    if re.match(r"^[IVX]+$", clean):
        return True

    # OCR junk — CJK characters or garbled text
    if any(ord(c) > 0x3000 for c in clean):
        return True

    # Headings starting with > (blockquote text parsed as heading)
    if clean.startswith(">"):
        return True

    # Headings with only lowercase (likely OCR junk mid-sentence)
    if clean[0].islower():
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

        # Detect § paragraph heading (with or without ## prefix)
        # Skip TOC lines like "§ 1. Title ..... 8"
        if "....." in line:
            continue
        m = RE_PARAGRAPH.match(line)
        if m:
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

    # Return only chapters that have paragraphs, sorted by number
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
        f"-- Қазақстан тарихы 5-сынып Textbook Import (Kazakh)",
        f"-- Generated by load_textbook_32.py",
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
        "-- Қазақстан тарихы 5-сынып Content UPDATE",
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
        description="Load Қазақстан тарихы 5-сынып textbook into AI Mentor database"
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
    print("  Қазақстан тарихы 5-сынып — Textbook Import")
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

    print("\nNo action specified. Use --dry-run, --generate-sql, or --update-content.")


if __name__ == "__main__":
    main()
