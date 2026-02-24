#!/usr/bin/env python3
"""
Load 'Алгебра 9 сынып, 1-бөлім' (Kazakh) into the AI Mentor database.

Parses the markdown file, creates textbook/chapter/paragraph records,
copies images, and creates ParagraphContent records for language='kk'.

Usage:
    python scripts/load_algebra9_textbook.py           # Full import
    python scripts/load_algebra9_textbook.py --dry-run  # Parse only, no DB writes
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

# ── Path setup (same pattern as import_goso.py) ─────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# ── Constants ────────────────────────────────────────────────────────────────

TEXTBOOK_TITLE = "Алгебра 9 сынып, 1-бөлім"
SUBJECT_CODE = "algebra"
GRADE_LEVEL = 9
AUTHORS = "А.Е. Әбілқасымова, Т.П. Кучер, В.Е. Корчевский, З.Э. Жұмағұлова"
PUBLISHER = "Мектеп"
YEAR = 2019
ISBN = "978-601-07-1093-1"
LANGUAGE = "kk"

MD_FILE = PROJECT_ROOT / "docs" / "archive" / "parser" / "386_with_local_images.md"
IMAGES_SRC_DIR = PROJECT_ROOT / "docs" / "archive" / "parser" / "images"
UPLOADS_BASE = BACKEND_DIR / "uploads"

# Headings that are internal content within a paragraph (NOT paragraph boundaries)
INTERNAL_HEADINGS = {
    "МЫСАЛ", "Мысал", "Дысал", "Дмал", "Дмсал",
    "СЕНДЕР БІЛЕСІҢДЕР",
    "ТУСІНДІРІҢДЕР", "ТУСІНДІРІҢАЕР",
    "Жаттығулар",
    "A", "B", "C",
    "ҚАЙТАЛАУ", "Қайталау",
    "Жана білімді менгеруге дайындаламыз",
    "Жана білімді менгеруге арналған тірек ұғымдар",
    "Жана білімді менгеруте арналған тірек ұғымдар",
    "Жана білімді мецгеруге арналған тірек ұғымдар",
    "Жана білімді менгеруге арналған тірек ұтымдар",
    "Жаца білімді менгеруге дайындаламыз",
    "АЛГОРИТМ", "Алгоритм",
    "?",
    "Түйінді ұғымдар", "Түйінді уғымдар",
    "ҒАЛЫМ-МАТЕМАТИК ТУРАЛЫ ХАБАРЛАМА ДАЙЫНДАҢДАР",
    "АУЫЛ ШАРУАШЫЛЫҒЫНДАҒЫ МАТЕМАТИКА",
    "БИЗНЕСТЕГІ МАТЕМАТИКА",
    "МЕНІҢ ӨМІРІМДЕГІ МАТЕМАТИКА",
    "ЖАНҰЯ ӨМІРІНДЕГІ МАТЕМАТИКА",
}

# OCR artifacts to fix in chapter titles
OCR_FIXES = {
    "TI35EKTEP": "ТІЗБЕКТЕР",
    "ТЕНСЗДІКТЕР": "ТЕҢСІЗДІКТЕР",
    "ЖЭНЕ": "ЖӘНЕ",
    "ЖУЙЕСІ": "ЖҮЙЕСІ",
    "ЖҮИЕЛЕРІ": "ЖҮЙЕЛЕРІ",
}

# ── Data classes ─────────────────────────────────────────────────────────────


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


# ── Regex patterns ───────────────────────────────────────────────────────────

# Chapter heading: "I тарау", "ІІ тарау", "III тарау" (h1 or h2)
# Handles mixed Cyrillic І and Latin I
RE_CHAPTER = re.compile(r"^#{1,2}\s+[IІ]+\s+тарау", re.IGNORECASE)

# Paragraph heading: "§1.", "## §2.", "## § 12."
RE_PARAGRAPH = re.compile(r"^(?:#{1,2}\s+)?§\s*(\d+)[.\s](.+)", re.IGNORECASE)

# Review chapter start
RE_REVIEW_START = re.compile(r"КАЙТАЛАУҒА АРНАЛҒАН ЖАТТЫҒУЛАР")

# Self-test section
RE_SELF_TEST = re.compile(r"ӨЗІНД[ІI] ТЕКСЕР", re.IGNORECASE)

# Answers section
RE_ANSWERS = re.compile(r"^#{1,2}\s+ЖАУАПТАРЫ")

# TOC
RE_TOC = re.compile(r"^#{1,2}\s+МАЗМУНЫ")

# Image reference in markdown
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(\./images/([^)]+)\)")

# Key terms block
RE_KEY_TERMS = re.compile(r"Түйінді\s+[ұу]ғымдар", re.IGNORECASE)


# ── Parser ───────────────────────────────────────────────────────────────────


def fix_ocr(title: str) -> str:
    """Fix known OCR artifacts in text."""
    for wrong, correct in OCR_FIXES.items():
        title = title.replace(wrong, correct)
    return title


def is_internal_heading(heading: str) -> bool:
    """Check if a ## heading is an internal content heading (not a paragraph boundary)."""
    clean = heading.strip()
    # Exact match
    if clean in INTERNAL_HEADINGS:
        return True
    # Starts with known prefix
    for prefix in INTERNAL_HEADINGS:
        if clean.startswith(prefix):
            return True
    # Heading that starts with image ref
    if clean.startswith("!["):
        return True
    # Heading that is a definition/rule (lowercase start, long text)
    if len(clean) > 60:
        return True
    # AlgoRITM variants
    if "лгоритм" in clean.lower() or "АЛГОРИТМ" in clean:
        return True
    return False


def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    """Parse the markdown file into chapters and paragraphs."""
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    chapters: list[ParsedChapter] = []
    current_chapter: ParsedChapter | None = None
    current_paragraph: ParsedParagraph | None = None
    phase = "preamble"  # preamble | review | chapters | answers | end
    chapter_counter = 0

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")

        # ── Phase: preamble (skip until review section) ──────────────
        if phase == "preamble":
            if RE_REVIEW_START.search(line):
                phase = "review"
                current_chapter = ParsedChapter(
                    title="7-8-сыныптардағы алгебра курсын қайталауға арналған жаттығулар",
                    number=0,
                )
                chapters.append(current_chapter)
            continue

        # ── Stop markers ─────────────────────────────────────────────
        if RE_TOC.match(line):
            break

        if RE_ANSWERS.match(line):
            phase = "answers"
            current_paragraph = None
            continue

        if phase == "answers":
            continue

        # ── Detect chapter heading ───────────────────────────────────
        if RE_CHAPTER.match(line):
            # Finalize previous paragraph
            current_paragraph = None
            chapter_counter += 1
            title = re.sub(r"^#{1,2}\s+", "", line).strip()
            title = fix_ocr(title)
            # Clean <br> tags
            title = re.sub(r"<br\s*/?>", " ", title).strip()
            current_chapter = ParsedChapter(title=title, number=chapter_counter)
            chapters.append(current_chapter)
            phase = "chapters"
            continue

        # ── Detect § paragraph heading ───────────────────────────────
        m = RE_PARAGRAPH.match(line)
        if m:
            para_num = int(m.group(1))
            para_title = m.group(2).strip()
            para_title = re.sub(r"<br\s*/?>", " ", para_title).strip()
            para_title = fix_ocr(para_title)
            current_paragraph = ParsedParagraph(title=para_title, number=para_num)
            if current_chapter:
                current_chapter.paragraphs.append(current_paragraph)
            continue

        # ── Detect ӨЗІҢДІ ТЕКСЕР (self-test) ────────────────────────
        if RE_SELF_TEST.search(line):
            current_paragraph = ParsedParagraph(
                title="Өзіңді тексер!", number=900
            )
            if current_chapter:
                current_chapter.paragraphs.append(current_paragraph)
            continue

        # ── In review phase, detect subsection headings ──────────────
        if phase == "review" and line.startswith("## "):
            heading = line.lstrip("#").strip()
            if not is_internal_heading(heading):
                para_num = len(current_chapter.paragraphs) + 1 if current_chapter else 1
                current_paragraph = ParsedParagraph(title=heading, number=para_num)
                if current_chapter:
                    current_chapter.paragraphs.append(current_paragraph)
                continue

        # ── Accumulate content lines ─────────────────────────────────
        if current_paragraph is not None:
            current_paragraph.content_lines.append(line)

    return chapters


# ── Content conversion ───────────────────────────────────────────────────────


def md_lines_to_html(lines: list[str], textbook_id: int) -> str:
    """
    Convert markdown content lines to HTML with embedded LaTeX.

    Preserves $...$ and $$...$$ LaTeX syntax for client-side KaTeX rendering.
    Replaces markdown image refs with HTML <img> tags.
    """
    if not lines:
        return ""

    content = "\n".join(lines)

    # Replace image references
    content = RE_IMAGE.sub(
        lambda m: (
            f'<img src="/uploads/textbook-images/{textbook_id}/{m.group(2)}" '
            f'alt="{m.group(1)}" class="mx-auto my-4 max-w-full" />'
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
            html_parts.append("<table class='w-full border-collapse my-4'>")
            for i, row in enumerate(table_rows):
                cells = [c.strip() for c in row.strip("|").split("|")]
                # Skip separator rows
                if all(re.match(r"^:?-+:?$", c) for c in cells):
                    continue
                tag = "th" if i == 0 else "td"
                html_parts.append("<tr>")
                for cell in cells:
                    html_parts.append(
                        f"<{tag} class='border border-gray-300 px-3 py-2'>"
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
                f"<blockquote class='border-l-4 border-blue-300 pl-4 my-3 italic'>"
                f"{line[2:]}</blockquote>"
            )
            continue

        # Image (already converted above, but just in case)
        if line.strip().startswith("<img "):
            flush_paragraph()
            html_parts.append(f'<div class="my-4 text-center">{line.strip()}</div>')
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
    """Extract key terms from Түйінді ұғымдар section."""
    terms = []
    in_terms = False
    for line in lines:
        if RE_KEY_TERMS.search(line):
            in_terms = True
            continue
        if in_terms:
            # Table row with terms
            if line.strip().startswith("|"):
                cell = line.strip().strip("|").strip()
                if cell and not re.match(r"^:?-+:?$", cell):
                    for term in re.split(r"<br\s*/?>|,", cell):
                        t = term.strip()
                        if t:
                            terms.append(t)
            # Non-table line with terms (comma-separated)
            elif line.strip() and not line.strip().startswith("|"):
                for term in re.split(r",|;", line):
                    t = term.strip()
                    if t and len(t) > 2:
                        terms.append(t)
                in_terms = False
            else:
                if terms:
                    break
    return terms if terms else None


# ── Database operations ──────────────────────────────────────────────────────


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
        text(
            """
            INSERT INTO subjects (code, name_ru, name_kz, grade_from, grade_to, is_active)
            VALUES (:code, :name_ru, :name_kz, :grade_from, :grade_to, true)
            RETURNING id
        """
        ),
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
    """Find or create the textbook record. Returns textbook_id."""
    result = session.execute(
        text(
            """
            SELECT id FROM textbooks
            WHERE title = :title AND grade_level = :grade AND is_deleted = false
        """
        ),
        {"title": TEXTBOOK_TITLE, "grade": GRADE_LEVEL},
    )
    row = result.fetchone()
    if row:
        print(f"  Textbook already exists (id={row[0]})")
        return row[0]

    result = session.execute(
        text(
            """
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
        """
        ),
        {
            "subject_id": subject_id,
            "title": TEXTBOOK_TITLE,
            "subject": "Алгебра",
            "grade_level": GRADE_LEVEL,
            "author": AUTHORS,
            "publisher": PUBLISHER,
            "year": YEAR,
            "isbn": ISBN,
            "description": "Жалпы білім беретін мектептің 9-сыныбына арналған оқулық. 1-бөлім.",
        },
    )
    textbook_id = result.fetchone()[0]
    print(f"  Created textbook (id={textbook_id})")
    return textbook_id


def create_chapter(session, textbook_id: int, chapter: ParsedChapter, order: int) -> int:
    """Create a chapter record."""
    result = session.execute(
        text(
            """
            SELECT id FROM chapters
            WHERE textbook_id = :tid AND number = :num AND is_deleted = false
        """
        ),
        {"tid": textbook_id, "num": chapter.number},
    )
    row = result.fetchone()
    if row:
        print(f"    Chapter {chapter.number} already exists (id={row[0]})")
        return row[0]

    result = session.execute(
        text(
            """
            INSERT INTO chapters (textbook_id, title, number, "order")
            VALUES (:textbook_id, :title, :number, :order)
            RETURNING id
        """
        ),
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
    # Build HTML content
    html_content = md_lines_to_html(para.content_lines, textbook_id)
    key_terms = extract_key_terms(para.content_lines)

    # Check if paragraph already exists
    result = session.execute(
        text(
            """
            SELECT id FROM paragraphs
            WHERE chapter_id = :cid AND number = :num AND is_deleted = false
        """
        ),
        {"cid": chapter_id, "num": para.number},
    )
    row = result.fetchone()
    if row:
        print(f"      Paragraph {para.number} already exists (id={row[0]})")
        return row[0]

    result = session.execute(
        text(
            """
            INSERT INTO paragraphs (
                chapter_id, title, number, "order", content, key_terms
            ) VALUES (
                :chapter_id, :title, :number, :order, :content, :key_terms::json
            )
            RETURNING id
        """
        ),
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

    # Create ParagraphContent for Kazakh
    source_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]
    session.execute(
        text(
            """
            INSERT INTO paragraph_contents (
                paragraph_id, language, explain_text,
                source_hash, status_explain,
                status_audio, status_slides, status_video, status_cards
            ) VALUES (
                :paragraph_id, 'kk', :explain_text,
                :source_hash, 'ready',
                'empty', 'empty', 'empty', 'empty'
            )
            ON CONFLICT (paragraph_id, language) DO NOTHING
        """
        ),
        {
            "paragraph_id": paragraph_id,
            "explain_text": html_content,
            "source_hash": source_hash,
        },
    )

    title_short = para.title[:50] + ("..." if len(para.title) > 50 else "")
    print(f"      Created paragraph {para.number}: {title_short} (id={paragraph_id})")
    return paragraph_id


# ── Image copy ───────────────────────────────────────────────────────────────


def copy_images(textbook_id: int) -> int:
    """Copy images from parser directory to uploads directory."""
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


# ── Statistics ───────────────────────────────────────────────────────────────


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
    print(f"\n  Total: {len(chapters)} chapters, {total_paragraphs} paragraphs, {total_lines} content lines")
    print("---")


# ── Main ─────────────────────────────────────────────────────────────────────


def escape_sql(s: str) -> str:
    """Escape string for SQL single-quote literals."""
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


def generate_sql(chapters: list[ParsedChapter], output_path: Path):
    """Generate a SQL file for importing via psql.

    Uses individual INSERT statements (no DO $$ block) to avoid
    conflicts with LaTeX $$ dollar signs and backslash commands.
    Textbook ID is resolved via subqueries.
    """
    textbook_title_esc = escape_sql(TEXTBOOK_TITLE)
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE title = {textbook_title_esc}"
        f" AND grade_level = {GRADE_LEVEL} AND is_deleted = false LIMIT 1)"
    )

    lines = [
        "-- Algebra 9 Textbook Import (Kazakh)",
        "-- Generated by load_algebra9_textbook.py",
        "-- Run: docker exec -i ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f <file>",
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
        f"    {escape_sql('Жалпы білім беретін мектептің 9-сыныбына арналған оқулық. 1-бөлім.')},",
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

        lines.append(f"-- Chapter {chapter.number}: {chapter.title[:60]}")
        lines.append(f"INSERT INTO chapters (textbook_id, title, number, \"order\", is_deleted)")
        lines.append(f"SELECT {textbook_where}, {chapter_title_esc}, {chapter.number}, {ch_order}, false")
        lines.append(f"WHERE NOT EXISTS (")
        lines.append(f"    SELECT 1 FROM chapters WHERE textbook_id = {textbook_where}")
        lines.append(f"    AND number = {chapter.number} AND is_deleted = false")
        lines.append(f");")
        lines.append("")

        for p_order, para in enumerate(chapter.paragraphs, 1):
            para_number = para.number if para.number != 900 else 100 + p_order
            # Build HTML content with textbook_id=0 placeholder
            html_content = md_lines_to_html(para.content_lines, 0)
            key_terms = extract_key_terms(para.content_lines)
            source_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]

            # The content will have /textbook-images/0/ that we'll keep as-is
            # and update after we know the textbook_id
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

            lines.append(f"-- Paragraph {para_number}: {para.title[:50]}")
            lines.append(f"INSERT INTO paragraphs (chapter_id, title, number, \"order\", content, key_terms, is_deleted)")
            lines.append(f"SELECT {chapter_where}, {title_esc}, {para_number}, {p_order},")
            lines.append(f"{content_esc},")
            lines.append(f"{key_terms_sql}, false")
            lines.append(f"WHERE NOT EXISTS (")
            lines.append(f"    SELECT 1 FROM paragraphs WHERE chapter_id = {chapter_where}")
            lines.append(f"    AND number = {para_number} AND is_deleted = false")
            lines.append(f");")
            lines.append("")

            # ParagraphContent for 'kk'
            lines.append(f"INSERT INTO paragraph_contents (")
            lines.append(f"    paragraph_id, language, explain_text,")
            lines.append(f"    source_hash, status_explain,")
            lines.append(f"    status_audio, status_slides, status_video, status_cards")
            lines.append(f") SELECT")
            lines.append(f"    {para_where}, 'kk',")
            lines.append(f"{content_esc},")
            lines.append(f"    {escape_sql(source_hash)}, 'ready',")
            lines.append(f"    'empty', 'empty', 'empty', 'empty'")
            lines.append(f"WHERE NOT EXISTS (")
            lines.append(f"    SELECT 1 FROM paragraph_contents")
            lines.append(f"    WHERE paragraph_id = {para_where} AND language = 'kk'")
            lines.append(f");")
            lines.append("")
            total_paragraphs += 1

    # Update image paths with actual textbook_id
    lines.append("-- Update image paths with actual textbook_id")
    lines.append(f"UPDATE paragraphs SET content = REPLACE(content, '/textbook-images/0/', '/textbook-images/' || (SELECT id FROM textbooks WHERE title = {textbook_title_esc} AND grade_level = {GRADE_LEVEL} AND is_deleted = false LIMIT 1) || '/')")
    lines.append(f"WHERE chapter_id IN (SELECT id FROM chapters WHERE textbook_id = {textbook_where});")
    lines.append("")
    lines.append(f"UPDATE paragraph_contents SET explain_text = REPLACE(explain_text, '/textbook-images/0/', '/textbook-images/' || (SELECT id FROM textbooks WHERE title = {textbook_title_esc} AND grade_level = {GRADE_LEVEL} AND is_deleted = false LIMIT 1) || '/')")
    lines.append(f"WHERE paragraph_id IN (SELECT p.id FROM paragraphs p JOIN chapters c ON c.id = p.chapter_id WHERE c.textbook_id = {textbook_where});")
    lines.append("")

    lines.append("COMMIT;")
    lines.append("")
    lines.append(f"-- Stats: {len(chapters)} chapters, {total_paragraphs} paragraphs")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  Generated SQL: {output_path}")
    print(f"  Chapters: {len(chapters)}, Paragraphs: {total_paragraphs}")
    print(f"\n  To import, copy SQL file into container and run:")
    print(f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/import.sql")
    print(f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/import.sql")


def main():
    parser = argparse.ArgumentParser(
        description="Load Algebra 9 textbook (Kazakh) into AI Mentor database"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse only, no DB writes"
    )
    parser.add_argument(
        "--generate-sql", type=str, metavar="FILE",
        help="Generate SQL file instead of direct DB connection"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  Algebra 9 Textbook Import (Kazakh)")
    print("=" * 70)

    # 1. Parse MD file
    print(f"\nStep 1: Parsing {MD_FILE.name}...")
    if not MD_FILE.exists():
        print(f"  ERROR: File not found: {MD_FILE}")
        sys.exit(1)

    chapters = parse_textbook(MD_FILE)
    print_parse_stats(chapters)

    if args.dry_run:
        print("\n[DRY RUN] Stopping before DB operations.")
        return

    # Generate SQL mode
    if args.generate_sql:
        print(f"\nStep 2: Generating SQL file...")
        generate_sql(chapters, Path(args.generate_sql))
        return

    # 2. Load env and connect
    env_path = BACKEND_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
    else:
        print(f"  WARNING: .env not found at {env_path}")

    db_url = get_database_url()
    print(f"\nStep 2: Connecting to database...")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 3. Subject
        print("\nStep 3: Finding/creating subject...")
        subject_id = find_or_create_subject(session)

        # 4. Textbook
        print("\nStep 4: Finding/creating textbook...")
        textbook_id = find_or_create_textbook(session, subject_id)

        # 5. Images
        print("\nStep 5: Copying images...")
        copy_images(textbook_id)

        # 6. Chapters & paragraphs
        print("\nStep 6: Creating chapters and paragraphs...")
        total_paragraphs = 0

        for ch_order, chapter in enumerate(chapters, 1):
            chapter_id = create_chapter(session, textbook_id, chapter, ch_order)

            for p_order, para in enumerate(chapter.paragraphs, 1):
                # Renumber self-test paragraphs to proper sequence
                if para.number == 900:
                    para.number = 100 + p_order  # High number to stay last

                create_paragraph(session, chapter_id, para, p_order, textbook_id)
                total_paragraphs += 1

        # 7. Commit
        session.commit()

        print("\n" + "=" * 70)
        print(f"  Import completed!")
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
