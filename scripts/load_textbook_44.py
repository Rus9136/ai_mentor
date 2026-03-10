#!/usr/bin/env python3
"""
Load 'Spotlight for Kazakhstan Grade 6' (English) into the AI Mentor database.

Parses the Mathpix MMD file organized by Modules (chapters) and Sections (paragraphs).
This is an ENGLISH textbook — no exercises, no § paragraph numbers.
Chapters = 9 Modules, Paragraphs = Sections within modules.

Usage:
    python scripts/load_textbook_44.py --dry-run           # Parse only
    python scripts/load_textbook_44.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_44.py --update-content FILE # Update content
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

TEXTBOOK_ID = 44
TEXTBOOK_TITLE = "Ағылшын тілі 6-сынып"
SUBJECT_CODE = "english"
GRADE_LEVEL = 6
AUTHORS = "Virginia Evans, Jenny Dooley, Bob Obee"
PUBLISHER = "Express Publishing"
YEAR = 2018
ISBN = ""
LANGUAGE = "en"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "44" / "textbook_44.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "44"

# Module definitions: module_number → chapter info
MODULES = [
    {"number": 1, "title": "Module 1 — Our class"},
    {"number": 2, "title": "Module 2 — Helping & Heroes"},
    {"number": 3, "title": "Module 3 — Our countryside"},
    {"number": 4, "title": "Module 4 — Drama & Comedy"},
    {"number": 5, "title": "Module 5 — Our health"},
    {"number": 6, "title": "Module 6 — Travel & Holidays"},
    {"number": 7, "title": "Module 7 — Reading for Pleasure"},
    {"number": 8, "title": "Module 8 — Our neighbourhood"},
    {"number": 9, "title": "Module 9 — Transport"},
]

# Headings that indicate module intro (skip content)
MODULE_INTRO_HEADINGS = {
    "What's in this module?",
    "What's in this module",
    "Skills Focus:",
    "Themes:",
    "Language Focus:",
}

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

# Across the Curriculum with code
RE_ACROSS_CURRICULUM = re.compile(
    r"^##\s+Across the Curriculum\s+(\d+)\s*([a-z])",
    re.IGNORECASE,
)

# ACROSS CULTURES (as heading, no code)
RE_ACROSS_CULTURES = re.compile(
    r"^##\s+ACROSS CULTURES\b",
    re.IGNORECASE,
)

# Non-heading ACROSS CULTURES marker (Module 6 special case — plain text)
RE_ACROSS_CULTURES_PLAIN = re.compile(
    r"^ACROSS CULTURES\b",
    re.IGNORECASE,
)

# VALUES
RE_VALUES = re.compile(
    r"^##\s+VALUES\b",
    re.IGNORECASE,
)

# Module 7 story sections: "7a Title", "7b Title", etc.
RE_STORY_SECTION = re.compile(
    r"^##\s+(\d+)([a-d])\s+(.+)",
)

# Vocabulary intro (just "Vocabulary" — not followed by digit+letter code)
RE_VOCABULARY_INTRO = re.compile(
    r"^##\s+Vocabulary\b",
    re.IGNORECASE,
)

# MODULE heading (various OCR forms)
RE_MODULE_HEADING = re.compile(
    r"^#{1,2}\s+(?:MODULE|MOOULE|мооие|woule|module)\b",
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
    # $\mathbf{4 g}$ → 4 g
    cleaned = re.sub(r"\$\\mathbf\{([^}]*)\}\$", r"\1", line)
    # $\textbf{...}$ → content
    cleaned = re.sub(r"\$\\textbf\{([^}]*)\}\$", r"\1", cleaned)
    # \section*{...} → content
    cleaned = re.sub(r"\\section\*\{([^}]*)\}", r"\1", cleaned)
    # <br> / <br/> → space
    cleaned = re.sub(r"<br\s*/?>", " ", cleaned)
    # Collapse whitespace
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned


def detect_module_number(heading_text: str) -> int | None:
    """Return module number (1-9) if heading starts a new module, else None."""
    text = heading_text.strip()
    # Clean formatting
    clean = re.sub(r"<br\s*/?>", " ", text)
    clean = re.sub(r"\\section\*\{[^}]*\}", "", clean)

    # Extract number from LaTeX expressions: $3 \longdiv{...}$
    latex_number = None
    latex_match = re.search(r"\$\s*(\d+)\s*\\", clean)
    if latex_match:
        latex_number = int(latex_match.group(1))

    # Extract number from parentheses: (5)
    paren_match = re.search(r"\((\d+)\)", clean)
    paren_number = int(paren_match.group(1)) if paren_match else None

    # Strip LaTeX
    clean = re.sub(r"\$[^$]*\$", "", clean).strip()
    clean = re.sub(r"\s+", " ", clean).strip()

    # Check for MODULE/MOOULE/woule/мооие keyword
    has_module_kw = bool(re.match(
        r"(?:MODULE|MOOULE|woule|мооие|module)\b", clean, re.IGNORECASE
    ))

    if has_module_kw:
        # Extract explicit number after keyword
        m = re.search(
            r"(?:MODULE|MOOULE|woule|мооие|module)\s+(\d+)",
            clean, re.IGNORECASE,
        )
        if m:
            return int(m.group(1))
        # Use LaTeX number
        if latex_number:
            return latex_number
        # Use parenthesized number
        if paren_number:
            return paren_number

        # Match by title keywords (when no number found)
        lower = clean.lower()
        if "helping" in lower or "heroes" in lower:
            return 2
        if "countryside" in lower:
            return 3
        if "drama" in lower or "comedy" in lower:
            return 4
        if "health" in lower or "hosith" in lower:
            return 5
        if "travel" in lower or "holidays" in lower:
            return 6
        if "reading for pleasure" in lower:
            return 7
        if "neighbourhood" in lower:
            return 8
        if "transport" in lower:
            return 9
        if "our class" in lower:
            return 1

        # Bare "MODULE" alone — can't determine number
        return None

    # No MODULE keyword — only match Module 6 (has no MODULE prefix)
    lower = clean.lower()
    if "travel" in lower and "holidays" in lower:
        return 6

    return None


def detect_section(line: str, current_module_num: int) -> tuple[str, str | None] | None:
    """Check if line is a section heading.

    Returns (section_key, title) or None.
    If title is None, the section should be merged into an existing one.
    """
    heading_match = re.match(r"^(#{1,2})\s+(.+)", line)
    if not heading_match:
        return None

    heading_text = heading_match.group(2).strip()
    clean_line = clean_heading_for_matching(line)

    # Writing sub-heading like "## Writing (a story)" — NOT a section boundary
    if RE_WRITING_SUBHEADING.match(clean_line):
        return None

    # Coded section: Reading 1a, Use of English 2b, Writing 4g, etc.
    m = RE_SECTION_CODED.match(clean_line)
    if m:
        section_type = m.group(1)
        mod_num = m.group(2)
        letter = m.group(3)
        if letter == "¢":
            letter = "c"
        key = f"{section_type} {mod_num}{letter}"
        title = f"{section_type} {mod_num}{letter}"
        return (key, title)

    # Across the Curriculum with code
    m = RE_ACROSS_CURRICULUM.match(clean_line)
    if m:
        mod_num = m.group(1)
        letter = m.group(2) if m.group(2) else "f"
        key = f"Across the Curriculum {mod_num}{letter}"
        title = f"Across the Curriculum {mod_num}{letter}"
        return (key, title)

    # ACROSS CULTURES (heading form)
    if RE_ACROSS_CULTURES.match(clean_line):
        key = f"Across Cultures {current_module_num}"
        title = "Across Cultures"
        return (key, title)

    # Module 6 Across Cultures has a non-standard heading
    if current_module_num == 6 and "discovering the world" in heading_text.lower():
        key = f"Across Cultures {current_module_num}"
        title = "Across Cultures"
        return (key, title)

    # EDUTAINMENT (check both cleaned heading and original line)
    if "EDUTAINMENT" in clean_line.upper() or "EDUTAINMENT" in line.upper():
        key = f"Edutainment {current_module_num}"
        title = "Edutainment & Values"
        return (key, title)

    # VALUES → merge into Edutainment
    if RE_VALUES.match(clean_line):
        key = f"Edutainment {current_module_num}"
        return (key, None)  # None title means merge into existing

    # Story section (Module 7): "7a The Wonderful Wizard of Oz"
    m = RE_STORY_SECTION.match(clean_line)
    if m and int(m.group(1)) == 7:
        letter = m.group(2)
        story_title = m.group(3).strip()
        key = f"Story 7{letter}"
        title = f"7{letter}. {fix_ocr(story_title)}"
        return (key, title)

    # Vocabulary intro (just "Vocabulary" — no digit+letter code)
    # Must come AFTER RE_SECTION_CODED check to avoid matching "Vocabulary 1a"
    if RE_VOCABULARY_INTRO.match(clean_line):
        key = f"Vocabulary intro {current_module_num}"
        title = "Vocabulary"
        return (key, title)

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
    in_module_intro = False
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

        # Check for heading
        heading_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if heading_match:
            heading_text = heading_match.group(2).strip()

            # --- Module detection ---
            mod_num = detect_module_number(heading_text)
            if mod_num is not None:
                current_module = mod_num
                in_module_intro = True
                current_para = None
                if current_module not in para_counter:
                    para_counter[current_module] = 1
                continue

            # --- "What's in this module?" ---
            if "What's in this module" in heading_text or "What\u2019s in this module" in heading_text:
                in_module_intro = True
                continue

            # --- Module intro headings (skip) ---
            if any(heading_text.startswith(h) for h in MODULE_INTRO_HEADINGS):
                in_module_intro = True
                continue

            # --- Section detection (only inside modules) ---
            if current_module >= 1:
                section_info = detect_section(line, current_module)
                if section_info:
                    in_module_intro = False
                    key, title = section_info

                    if key in section_map:
                        # Merge into existing section (duplicate heading)
                        current_para = section_map[key]
                        # Add sub-section heading as content separator
                        if title is not None:
                            current_para.content_lines.append("")
                            current_para.content_lines.append(line)
                    else:
                        # New section
                        if title is None:
                            # VALUES without prior EDUTAINMENT — create standalone
                            title = "Values"
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

            # --- In module intro: skip content ---
            if in_module_intro:
                continue

            # --- Otherwise: add heading as content to current paragraph ---
            if current_para:
                current_para.content_lines.append(line)
            continue

        # --- Non-heading lines ---

        # Detect non-heading MODULE marker (start of Module 1)
        if re.match(r"^MODULE\s*$", line) and current_module == 0:
            current_module = 1
            in_module_intro = True
            current_para = None
            if 1 not in para_counter:
                para_counter[1] = 1
            continue

        # Detect non-heading ACROSS CULTURES marker (Module 6 special case)
        if RE_ACROSS_CULTURES_PLAIN.match(line) and current_module >= 1:
            key = f"Across Cultures {current_module}"
            if key not in section_map:
                ch = chapters[current_module]
                pnum = para_counter.get(current_module, 1)
                current_para = ParsedParagraph(
                    title="Across Cultures",
                    number=pnum,
                    section_key=key,
                )
                ch.paragraphs.append(current_para)
                section_map[key] = current_para
                para_counter[current_module] = pnum + 1
            else:
                current_para = section_map[key]
            continue

        if in_module_intro:
            continue

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
        f"-- Spotlight for Kazakhstan Grade 6 — Textbook Import",
        f"-- Generated by load_textbook_44.py",
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
        "-- Spotlight Grade 6 Content UPDATE",
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
        description="Load Spotlight for Kazakhstan Grade 6 into AI Mentor database"
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
    print("  Spotlight for Kazakhstan Grade 6 — Textbook Import")
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
