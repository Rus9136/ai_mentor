#!/usr/bin/env python3
"""
Load 'Информатика 9-сынып (Атамура)' into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='kk'.

This is an INFORMATICS textbook — no exercises (A/B/C), 5 бөлім, 21 paragraphs.
Paragraphs use N.M. numbering (e.g. 1.1, 2.3, 5.4).
Chapters are determined by paragraph prefix from МАЗМҰНЫ (TOC).
Has Python code blocks in chapters 4-5 that need code block tracking.

Usage:
    python scripts/load_textbook_63.py --dry-run           # Parse only
    python scripts/load_textbook_63.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_63.py --update-content FILE # Update SQL
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

TEXTBOOK_ID = 63  # Already exists in DB
TEXTBOOK_TITLE = "Информатика 9-сынып (Атамура)"
SUBJECT_CODE = "informatics"
GRADE_LEVEL = 9
AUTHORS = "Мухаметжанова С.Т., Тен А., Голикова Н."
PUBLISHER = "Атамура"
YEAR = 2019
ISBN = ""
LANGUAGE = "kk"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "63" / "textbook_63.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "63"

# Chapter mapping: paragraph number ranges → chapter info (from МАЗМҰНЫ)
# Ch1: 1.1→1, 1.2→2, 1.3→3
# Ch2: 2.1→4, 2.2→5, 2.3→6
# Ch3: 3.1→7, 3.2→8, 3.3→9, 3.4→10, 3.5→11
# Ch4: 4.1→12, 4.2→13, 4.3→14, 4.4→15, 4.5→16, 4.6→17
# Ch5: 5.1→18, 5.2→19, 5.3→20, 5.4→21
CHAPTERS = [
    {"number": 1, "title": "Ақпаратпен жұмыс жасау",
     "para_from": 1, "para_to": 3},
    {"number": 2, "title": "Компьютер таңдаймыз",
     "para_from": 4, "para_to": 6},
    {"number": 3, "title": "Деректер базасы",
     "para_from": 7, "para_to": 11},
    {"number": 4, "title": "Python тілінде алгоритмдерді программалау",
     "para_from": 12, "para_to": 17},
    {"number": 5, "title": "Python программалау тілінде 2D ойынын құру",
     "para_from": 18, "para_to": 21},
]

# Sequential mapping: chapter_prefix → offset for global paragraph number
# global_number = _PARA_OFFSET[ch_prefix] + sub_number
_PARA_OFFSET = {1: 0, 2: 3, 3: 6, 4: 11, 5: 17}


def calc_global_number(ch_prefix: int, sub_num: int) -> int:
    """Convert N.M paragraph number to global sequential number."""
    return _PARA_OFFSET[ch_prefix] + sub_num


# ── OCR fixes ──────────────────────────────────────────────────────────────

OCR_FIXES = {
    "．": ". ",
    "，": ", ",
    "：": ": ",
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
    number: int       # Global sequential number
    raw_number: str   # Original string (e.g. "1.1", "2.3")
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# ── Regex patterns ──────────────────────────────────────────────────────────

# Paragraph heading: "## 1.1. Title", "### 5.1. Title", "## 2.2. Title <br> ..."
# Title must start with a letter (avoids false matches like "## 2.2.-кестенің жалғасы")
# Supports h1-h3 (### 5.1.)
RE_PARAGRAPH = re.compile(
    r"^#{1,3}\s+(\d+)\.(\d+)\.\s*(?:<br>\s*)?([А-ЯӘӨҮІҚҢҒҺа-яәөүіқңғһA-Za-z].+)",
    re.IGNORECASE,
)

# Stop markers — everything after these is appendix/glossary
RE_STOP = re.compile(
    r"^#{1,2}\s+(Қосымша\b|Глоссарий\b|ГЛОССАРИЙ\b|Пайдаланылған\s+әдебиеттер\b)",
    re.IGNORECASE,
)

# Test section markers (heading-based) — stop accumulating paragraph content
# Matches:
#   "## 3-БӨЛІМ БОЙЫНША НЕГІЗГІ"
#   "## «Мәліметтер қоры» бөлімі бойынша қорытынды тест"
#   "## 4-бөлім бойынша қорытынды тапсырмалар"
#   "## 4-тоқсан бойынша жиынтық бағалау"
#   "## 5-бөлім бойынша негізгі"
RE_TEST_HEADING = re.compile(
    r"^#{1,2}\s+(?:"
    r"\d+-?(?:БӨЛІМ|бөлім)\s+[Бб][Оо][Йй][Ыы][Нн][Шш][Аа]\s+(?:НЕГІЗГІ|негізгі)"
    r"|.*бөлімі?\s+бойынша\s+(?:қорытынды|негізгі)"
    r"|\d+-?тоқсан\s+бойынша\s+жиынтық\s+бағалау"
    r")",
    re.IGNORECASE,
)

# Test section markers (plain-text) — detect without ## prefix
# Matches: «Ақпаратпен жұмыс жасау» бөлімі бойынша қорытынды тапсырма
RE_TEST_PLAIN = re.compile(
    r"бөлімі\s+бойынша\s+қорытынды\s+тапсырма",
    re.IGNORECASE,
)

# Chapter marker headings (just a number or Roman numeral, or chapter title)
RE_CHAPTER_MARKER = re.compile(
    r"^#{1,2}\s+(?:[IVX]+\s*$|\d{1,2}\s*$)", re.IGNORECASE
)

# Chapter heading like "# 4-бөлім <br> TITLE"
RE_CHAPTER_BOLIM = re.compile(
    r"^#{1,2}\s+\d+-бөлім", re.IGNORECASE
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
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def clean_para_title(title: str) -> str:
    """Clean paragraph title: remove <br> and everything after it if it's meta."""
    # "Бағдарламалық қамтамасыз етуді таңдау <br> Нені үйренесіцдер?"
    # → "Бағдарламалық қамтамасыз етуді таңдау"
    if "<br>" in title:
        parts = title.split("<br>")
        main_title = parts[0].strip()
        if main_title:
            return main_title
    return fix_ocr(title.strip())


def get_chapter_for_para(para_number: int) -> dict | None:
    """Find which chapter a paragraph belongs to based on global number."""
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
    in_preamble = True  # Before first paragraph
    in_test_section = False  # Inside chapter test questions
    in_code_block = False  # Inside ``` code block

    for _line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")

        # Skip watermark lines
        if should_skip_line(line):
            continue

        # Track code blocks BEFORE heading detection
        # (Python comments start with # which matches heading regex)
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if current_paragraph is not None and not in_test_section:
                current_paragraph.content_lines.append(line)
            continue
        if in_code_block:
            if current_paragraph is not None and not in_test_section:
                current_paragraph.content_lines.append(line)
            continue

        # Stop markers — everything after this is glossary/appendix
        if RE_STOP.match(line):
            break

        # Test section markers (heading-based)
        if RE_TEST_HEADING.match(line):
            in_test_section = True
            current_paragraph = None
            continue

        # Test section markers (plain-text) — detect without ## prefix
        if not line.startswith("#") and RE_TEST_PLAIN.search(line):
            in_test_section = True
            current_paragraph = None
            continue

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
                if current_paragraph is not None and not in_test_section:
                    current_paragraph.content_lines.append(line)
                continue

        # Detect N.M. paragraph heading
        m = RE_PARAGRAPH.match(line)
        if m:
            in_preamble = False
            in_test_section = False
            ch_prefix = int(m.group(1))
            sub_num = int(m.group(2))
            para_title = m.group(3).strip()
            para_title = clean_para_title(para_title)

            if ch_prefix not in _PARA_OFFSET:
                # Unknown chapter prefix — treat as content
                if current_paragraph is not None:
                    current_paragraph.content_lines.append(line)
                continue

            global_num = calc_global_number(ch_prefix, sub_num)

            current_paragraph = ParsedParagraph(
                title=para_title,
                number=global_num,
                raw_number=f"{ch_prefix}.{sub_num}",
            )
            paragraphs.append(current_paragraph)
            continue

        # Skip preamble (before first paragraph)
        if in_preamble:
            continue

        # Skip test section content
        if in_test_section:
            continue

        # Chapter marker headings (bare numbers like "## 1", "## 9") — skip
        if RE_CHAPTER_MARKER.match(line):
            continue

        # Chapter бөлім headings ("# 4-бөлім <br> ...") — skip
        if RE_CHAPTER_BOLIM.match(line):
            continue

        # All other headings — treat as content of current paragraph
        # (simplified approach: only N.M headings create paragraph boundaries)
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
            print(f"  WARNING: §{para.raw_number} (num={para.number}, "
                  f"{para.title[:40]}) doesn't belong to any chapter!")

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
                f'border-radius:0.5rem;overflow-x:auto;margin:1rem 0">'
                f'<code>{code_text}</code></pre>'
            )
            code_lines = []
        in_code_block = False

    for raw_line in content.split("\n"):
        line = raw_line.rstrip()

        # Skip watermark lines in content
        if should_skip_line(line):
            continue

        # Code blocks
        if line.strip().startswith("```"):
            if in_code_block:
                flush_code()
            else:
                flush_paragraph()
                if in_table:
                    flush_table()
                if in_list:
                    flush_list()
                in_code_block = True
            continue
        if in_code_block:
            code_lines.append(line)
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

        # Subtask line: "a) text", "б) text", "а) text" etc.
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
                f"      {p.raw_number:>5}. {p_title:<58} "
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
        f"-- Информатика 9-сынып (Атамура) Textbook Import (Kazakh)",
        f"-- Generated by load_textbook_63.py",
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

            sql_lines.append(f"-- {para.raw_number}: {para.title[:50]}")
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

            # ParagraphContent for 'kk'
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
        "-- Информатика 9-сынып (Атамура) Content UPDATE",
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

            sql_lines.append(f"-- Update {para.raw_number}: {para.title[:50]}")
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
        description="Load Информатика 9-сынып (Атамура) textbook into AI Mentor database"
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
    print("  Информатика 9-сынып (Атамура) — Textbook Import")
    print("=" * 70)

    # 1. Parse MMD file
    print(f"\nStep 1: Parsing {MD_FILE.name}...")
    if not MD_FILE.exists():
        print(f"  ERROR: File not found: {MD_FILE}")
        sys.exit(1)

    chapters = parse_textbook(MD_FILE)
    print_parse_stats(chapters)

    if args.dry_run:
        print("\n  [DRY RUN] No output generated.")
        return

    if args.generate_sql:
        print(f"\nStep 2: Generating SQL...")
        generate_sql(chapters, Path(args.generate_sql))
        return

    if args.update_content:
        print(f"\nStep 2: Generating UPDATE SQL...")
        generate_update_sql(chapters, Path(args.update_content))
        return

    print("\n  No action specified. Use --dry-run, --generate-sql, or --update-content.")


if __name__ == "__main__":
    main()
