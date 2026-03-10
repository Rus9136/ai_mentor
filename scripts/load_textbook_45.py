#!/usr/bin/env python3
"""
Load 'Spotlight for Kazakhstan Grade 7' (English) into the AI Mentor database.

Parses the Mathpix MMD file organized by Modules (chapters) and Sections (paragraphs).
This is an ENGLISH textbook — no exercises, no § paragraph numbers.
Chapters = 9 Modules, Paragraphs = Sections within modules.

Module 5 is special: "Reading for Pleasure" with story sections (5a-5d).

Usage:
    python scripts/load_textbook_45.py --dry-run           # Parse only
    python scripts/load_textbook_45.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_45.py --update-content FILE # Update content
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

TEXTBOOK_ID = 45
TEXTBOOK_TITLE = "Ағылшын тілі 7-сынып"
SUBJECT_CODE = "english"
GRADE_LEVEL = 7
AUTHORS = "Dooley J., Mukhamedjianova B., Obee N., Manapbayeva Zh."
PUBLISHER = "EDU Stream и Express Publishing"
YEAR = 2022
ISBN = ""
LANGUAGE = "en"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "45" / "textbook_45.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "45"

# Module definitions
MODULES = [
    {"number": 1, "title": "Module 1 — Hobbies & Leisure"},
    {"number": 2, "title": "Module 2 — Communication & Technology"},
    {"number": 3, "title": "Module 3 — Holidays & Travel"},
    {"number": 4, "title": "Module 4 — Space & Earth"},
    {"number": 5, "title": "Module 5 — Reading for Pleasure"},
    {"number": 6, "title": "Module 6 — Entertainment & Media"},
    {"number": 7, "title": "Module 7 — Natural Disasters"},
    {"number": 8, "title": "Module 8 — Health & Habits"},
    {"number": 9, "title": "Module 9 — Clothes & Fashion"},
]

# Lines to skip entirely (watermarks, ads)
SKIP_PATTERNS = [
    "Все учебники Казахстана",
    "OKULYK",
]

# OCR artifacts to fix
OCR_FIXES = {
    "<br>": " ",
    "<br/>": " ",
    "<br />": " ",
    "：": ":",
    "（": "(",
    "）": ")",
    "，": ",",
    "＇": "'",
    "．": ".",
    "；": ";",
    "！": "!",
    "？": "?",
    "＂": '"',
    "＝": "=",
    "＋": "+",
    "＃": "#",
    "＆": "&",
    "＊": "*",
    "＿": "_",
    "－": "-",
}


# ── Data classes ────────────────────────────────────────────────────────────


@dataclass
class ParsedParagraph:
    title: str
    number: int        # Sequential number within chapter
    section_key: str   # Unique key for merging duplicates
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# ── Regex patterns ──────────────────────────────────────────────────────────

# Image reference in markdown
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)")

# Footnote references [^N]
RE_FOOTNOTE_REF = re.compile(r"\[\^(\d+)\]")

# Abstract block (Mathpix artifact)
RE_ABSTRACT = re.compile(r"^#{1,4}\s+Abstract", re.IGNORECASE)

# Stop marker — everything after this is review/reference material
RE_STOP = re.compile(r"^##\s+Language Review\b", re.IGNORECASE)

# Section headings with module number and code letter
# Matches: Reading 1a, Use of English 2b, Writing 4g, Skills 8c, etc.
RE_SECTION_CODED = re.compile(
    r"^##\s+(Reading|Vocabulary|Use of English|Skills|Everyday English|Writing|Listening)\s+(\d+)\s*([a-z¢])",
    re.IGNORECASE,
)

# Across the Curriculum with code: "Across the Curriculum 3f", "Across the Curriculum 8 f"
RE_ACROSS_CURRICULUM = re.compile(
    r"^##\s+Across the Curriculum\s+(\d+)\s*([a-z])",
    re.IGNORECASE,
)

# Across cultures with code: "Across cultures 6e", "Across cultures9f"
RE_ACROSS_CULTURES_CODED = re.compile(
    r"^##\s+Across\s+cultures?\s*(\d+)\s*([a-z])",
    re.IGNORECASE,
)

# Module 5 story sections: "5a", "5b The Time Machine", "(5c", "5d The Magic Garden"
RE_STORY_SECTION = re.compile(
    r"^##\s+\(?(\d+)([a-d])\b\s*(.*)",
)

# MODULE marker (heading or plain text) — skip, not a section boundary
RE_MODULE_MARKER_HEADING = re.compile(
    r"^#{1,2}\s+MODULE\b",
    re.IGNORECASE,
)
RE_MODULE_MARKER_PLAIN = re.compile(
    r"^MODULE\s+\d+\s*$",
    re.IGNORECASE,
)

# Writing sub-heading like "## Writing (a story)" — NOT a section boundary
RE_WRITING_SUBHEADING = re.compile(
    r"^##\s+Writing\s+\(",
    re.IGNORECASE,
)


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
    return re.sub(r"\s{2,}", " ", text).strip()


def clean_heading_for_matching(line: str) -> str:
    """Remove LaTeX/HTML formatting from heading for pattern matching."""
    cleaned = re.sub(r"\$\\mathbf\{([^}]*)\}\$", r"\1", line)
    cleaned = re.sub(r"\$\\textbf\{([^}]*)\}\$", r"\1", cleaned)
    cleaned = re.sub(r"\\section\*\{([^}]*)\}", r"\1", cleaned)
    cleaned = re.sub(r"<br\s*/?>", " ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned


# Story section titles for Module 5
STORY_TITLES = {
    "5a": "5a. The Hound of the Baskervilles",
    "5b": "5b. The Time Machine",
    "5c": "5c. Korkyt Ata and the Kobyz",
    "5d": "5d. The Magic Garden of the Poor",
}


def detect_section(line: str) -> tuple[str, str | None, int | None] | None:
    """Check if line is a section heading.

    Returns (section_key, title, module_number) or None.
    If title is None, the section should be merged into an existing one.
    """
    heading_match = re.match(r"^(#{1,2})\s+(.+)", line)
    if not heading_match:
        return None

    clean_line = clean_heading_for_matching(line)

    # Skip Writing sub-heading like "## Writing (a story)"
    if RE_WRITING_SUBHEADING.match(clean_line):
        return None

    # Skip MODULE marker headings
    if RE_MODULE_MARKER_HEADING.match(clean_line):
        return None

    # Coded section: Reading 1a, Use of English 2b, Writing 4g, etc.
    m = RE_SECTION_CODED.match(clean_line)
    if m:
        section_type = m.group(1)
        mod_num = int(m.group(2))
        letter = m.group(3)
        if letter == "¢":
            letter = "c"
        key = f"{section_type} {mod_num}{letter}"
        title = f"{section_type} {mod_num}{letter}"
        return (key, title, mod_num)

    # Across the Curriculum with code
    m = RE_ACROSS_CURRICULUM.match(clean_line)
    if m:
        mod_num = int(m.group(1))
        letter = m.group(2)
        key = f"Across the Curriculum {mod_num}{letter}"
        title = f"Across the Curriculum {mod_num}{letter}"
        return (key, title, mod_num)

    # Across cultures with code
    m = RE_ACROSS_CULTURES_CODED.match(clean_line)
    if m:
        mod_num = int(m.group(1))
        letter = m.group(2)
        key = f"Across Cultures {mod_num}{letter}"
        title = f"Across Cultures {mod_num}{letter}"
        return (key, title, mod_num)

    # Module 5 story sections: "5a", "5b The Time Machine", "(5c", etc.
    m = RE_STORY_SECTION.match(clean_line)
    if m and int(m.group(1)) == 5:
        mod_num = 5
        letter = m.group(2)
        key = f"Story 5{letter}"
        title = STORY_TITLES.get(f"5{letter}", f"5{letter}")
        return (key, title, mod_num)

    return None


# ── Parser ──────────────────────────────────────────────────────────────────


def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    """Parse the MMD file into chapters and paragraphs."""
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Initialize chapters
    chapters: dict[int, ParsedChapter] = {}
    for mod in MODULES:
        chapters[mod["number"]] = ParsedChapter(
            title=mod["title"],
            number=mod["number"],
        )

    # State variables
    current_module = 0       # 0 = preamble, 1-9 = module number
    current_para: ParsedParagraph | None = None
    section_map: dict[str, ParsedParagraph] = {}  # section_key → paragraph
    para_counter: dict[int, int] = {}             # chapter_num → next para number
    in_abstract = False

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")

        # Skip watermarks
        if should_skip_line(line):
            continue

        # Stop at Language Review
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
                # Fall through to heading detection
            else:
                if current_para is not None:
                    current_para.content_lines.append(line)
                continue

        # Skip MODULE plain-text markers
        if RE_MODULE_MARKER_PLAIN.match(line):
            continue

        # Check for heading
        heading_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if heading_match:
            # --- Section detection ---
            section_info = detect_section(line)
            if section_info:
                key, title, mod_num = section_info

                # Update current module from section code
                if mod_num is not None:
                    current_module = mod_num
                    if current_module not in para_counter:
                        para_counter[current_module] = 1

                if key in section_map:
                    # Merge into existing section (duplicate heading)
                    current_para = section_map[key]
                    if title is not None:
                        current_para.content_lines.append("")
                        current_para.content_lines.append(line)
                else:
                    # New section
                    if title is None:
                        title = key
                    ch = chapters[current_module]
                    pnum = para_counter.get(current_module, 1)
                    current_para = ParsedParagraph(
                        title=title,
                        number=pnum,
                        section_key=key,
                    )
                    ch.paragraphs.append(current_para)
                    section_map[key] = current_para
                    para_counter[current_module] = pnum + 1
                continue

            # Non-section heading → add as content to current paragraph
            if current_para:
                current_para.content_lines.append(line)
            continue

        # --- Non-heading lines ---
        if current_para is not None:
            current_para.content_lines.append(line)

    return [ch for ch in sorted(chapters.values(), key=lambda c: c.number) if ch.paragraphs]


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
                f"      {p.number:>3}. {p_title:<58} "
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
        f"-- Spotlight for Kazakhstan Grade 7 — Textbook Import",
        f"-- Generated by load_textbook_45.py",
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

            lines.append(f"-- {para.number}: {para.title[:50]}")
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

            # ParagraphContent for 'en'
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
        "-- Spotlight Grade 7 Content UPDATE",
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

            lines.append(f"-- Update {para.number}: {para.title[:50]}")
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
        description="Load Spotlight for Kazakhstan Grade 7 into AI Mentor database"
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
    print("  Spotlight for Kazakhstan Grade 7 — Textbook Import")
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

    if args.generate_sql:
        print(f"\nStep 2: Generating SQL...")
        generate_sql(chapters, Path(args.generate_sql))

    if args.update_content:
        print(f"\nStep 2: Generating UPDATE SQL...")
        generate_update_sql(chapters, Path(args.update_content))

    if not args.generate_sql and not args.update_content:
        print("\nNo output mode specified. Use --dry-run, --generate-sql, or --update-content.")


if __name__ == "__main__":
    main()
