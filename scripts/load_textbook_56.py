#!/usr/bin/env python3
"""
Load 'Информатика 6-сынып (Атамура)' into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='kk'.

This is an INFORMATICS textbook — no exercises section, 4 бөлімдер, 19 paragraphs.
Paragraphs use N.N format (1.1, 2.3, etc.) instead of § signs.
Chapters determined by first digit of paragraph number (TOC mapping).
Paragraph 3.4 has NO heading marker (plain text, not ## or ###).

Usage:
    python scripts/load_textbook_56.py --dry-run           # Parse only
    python scripts/load_textbook_56.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_56.py --update-content FILE # Update SQL
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

TEXTBOOK_ID = 56  # Already exists in DB
TEXTBOOK_TITLE = "Информатика 6-сынып (Атамура)"
SUBJECT_CODE = "informatics"
GRADE_LEVEL = 6
AUTHORS = "Мухаметжанова С.Т., Тен А.С., Комова И.В."
PUBLISHER = "Атамура"
YEAR = 2020
ISBN = "978-601-331-880-6"
LANGUAGE = "kk"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "56" / "textbook_56.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "56"

# Chapter mapping from МАЗМҰНЫ (TOC)
# Paragraphs mapped by first digit of N.N number
CHAPTERS = [
    {
        "number": 1,
        "title": "І бөлім. Компьютерлік жүйелер және желілер",
        "para_range": (1,),  # paragraphs 1.1-1.4
    },
    {
        "number": 2,
        "title": "ІІ бөлім. 3D баспа",
        "para_range": (2,),  # paragraphs 2.1-2.5
    },
    {
        "number": 3,
        "title": "ІІІ бөлім. Python тілінде программалау",
        "para_range": (3,),  # paragraphs 3.1-3.6
    },
    {
        "number": 4,
        "title": "IV бөлім. Мәтіндік құжатпен жұмыс",
        "para_range": (4,),  # paragraphs 4.1-4.4
    },
]

# ── Internal headings (NOT paragraph boundaries) ───────────────────────────

INTERNAL_HEADINGS = {
    # Learning objectives (OCR variants)
    "НЕНІ ҮЙРЕНЕСІҢДЕР?",
    "НЕНІ УЙРЕНЕСІҢДЕР?",
    "НЕНІ ҮЙРЕНЕСІҢАЕР?",
    "НЕНІ УЙРЕНЕСІҢ ДЕР?",
    "НЕНІ УЙРЕНЕСІҢ/ДЕР?",
    "НЕНІ ҮЙРЕНЕСІҢ ДЕР?",
    "НЕНТ УЙРЕНЕСІҢДЕР?",
    # Key terms (OCR variants)
    "ТІРЕК СӨЗДЕР",
    "ТІРЕК СеЗДЕР",
    "TIPEK CO3AEP",
    "TIPEK Сез дЕР",
    "TIPEK СездЕР",
    "TIPEK CO3AEP",
    # Assessment sections
    "Білу және түсіну",
    "Қолдану",
    "Қолдану. Талдау",
    "Колдану. Талдау",
    "Талдау",
    "Жинақтау",
    "Жинақтау. Бағалау",
    "Бағалау",
    "Бағалау критерийлері",
    # Algorithm / procedure sections
    "Әрекеттерді орындау алгоритмі",
    "Тапсырманы орындауға арналған ұсыныстар",
    "Тапсырманы орындау алгоритмі",
    "Үй тапсырмасын орындауға арналған ұсыныстар",
    # Step-by-step headings
    "1-қадам",
    "2-қадам",
    "3-қадам",
    # Region headings (ergonomics lesson)
    "1-аймақ - бел мен аяқ",
    "2-аймақ - қол білегі",
    "3-аймақ - мойын, иық, көз",
    "4-аймақ - жұмыс орнын ұйымдастыру",
    # Specific internal headings from content
    "Компьютер кабинетіндегі эргономика ережелері",
    "Сымсыз желінің артықшылықтары мен кемшіліктері.",
    "Сымсыз желілерді қолдануда:",
    "3D модельді әзірлеу кезеңдері",
    "Paint 3D редакторындағы параметрлер",
    "Кенеп",
    "Үшөлшемді модель",
    "«Сиқырлы таңдау» функциясы",
    "3D принтермен жұмыс істеу кезіндегі қауіпсіздік техникасы",
    "Python тілінің алфавиті",
    "Математикалық амалдар",
    "Айнымалының мәнін меншіктеу",
    "Стандартты арифметикалық амалдар",
    "Программадағы қателер",
    "Рефератты жазу алгоритмі",
    "Реферат құрылымы",
    "Рефератта бейнелерді орналастыру бойынша кейбір ұсыныстар",
    "Usecubes - 3D объектілерінің генераторы",
    # OCR junk
    "Биологические науки",
    "Microscft --",
    "File Edit Format Run Options Window Help",
    "⟷ํ ำ",
    # Preamble headings
    "Құрметті оқушылар!",
    "Шартты белгілер",
    "Алғы сөз",
    # Appendix headings
    "Көзге арналған жаттығулар",
    "Иық пен қолдың шаршағанын басуға арналған жаттығулар",
    "Ескерту.",
    # Chapter-level summary headings (not paragraphs)
    "1 белім бойынша қорытынды тапсырмалар",
    "II белім бойынша қорытынды тапсырмалар",
    "III белімге қорытынды тест пен тапсырмалар",
    # Method / approach headings
    "Есептерді шешудің 1-тәсілі",
    "Есепті шешудің 2-тәсілі",
    "Програама коды:",
    "Программа коды:",
    # Hyperlink lesson headings
    "Бетбелгіні пайдаланып, гиперсілтемені орнатып көріңдер.",
    # Home task headings
    "Үй компьютеріне Python программасын орнату Программаны орнату алгоритмі:",
}

# OCR artifacts to fix (general)
OCR_FIXES = {
    "<br>": " ",
    "<br/>": " ",
    "<br />": " ",
    "．": ".",
    "，": ",",
    "：": ":",
    "－": "-",
    "（": "(",
    "）": ")",
    "？": "?",
}

# Title-specific OCR fixes (applied to paragraph titles)
TITLE_OCR_FIXES = {
    "Ecenteyiw техникасының даму тарихы": "Есептеуіш техникасының даму тарихы",
    "3D 6acnacb": "3D баспасы",
    "Арифметикалық ернектердің жазылу ережелері": "Арифметикалық өрнектердің жазылу ережелері",
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
    chapter_num: int    # First digit (1-4)
    para_num: int       # Second digit (1-6)
    raw_number: str     # Original string like "1.1", "3.4"
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# ── Regex patterns ──────────────────────────────────────────────────────────

# Paragraph heading with ## or ###: "## 1.1. Title" or "### 2.1. Title"
RE_PARAGRAPH_HEADING = re.compile(
    r"^#{1,3}\s+(\d+)\.(\d+)[.．]?\s+(.+)", re.IGNORECASE
)

# Paragraph without heading marker (like "3.4. Title" as plain text)
RE_PARAGRAPH_PLAIN = re.compile(
    r"^(\d+)\.(\d+)\.\s+(\S.+)"
)

# Figure caption headings: "### 2.1.1-сурет. ..." or "### 3.5.7-сурет. ..."
RE_FIGURE_CAPTION = re.compile(
    r"^#{1,3}\s+\d+\.\d+\.\d+-(?:сурет|сүрет|cypet|cyper|суреттегі)", re.IGNORECASE
)

# Section summary / chapter review
RE_SECTION_SUMMARY = re.compile(
    r"^#{1,2}\s+[IVX\d]+\s*бел[іi]м\S*\s+бойынша\b", re.IGNORECASE
)
RE_SECTION_SUMMARY2 = re.compile(
    r"^#{1,2}\s+[IVX\d]+\s*бел[іi]мге\b", re.IGNORECASE
)

# Stop markers — everything after these is appendix
RE_STOP = re.compile(
    r"^#{1,2}\s+(ГЛОССАРИЙ\b|МАЗМҰНЫ\b|Әдебиеттер тізімі\b"
    r"|Көзге арналған жаттығулар\b|Интернет-ресурстар\b)",
    re.IGNORECASE,
)

# Chapter title lines (OCR for Roman numerals + chapter names)
RE_CHAPTER_TITLE = re.compile(
    r"^#{1,2}\s+(3D БАСПА|РУТНОN ТІЛІНДЕ ПРОГРАММАЛАУ|PYTHON\b"
    r"|МӘТІНДІК ҚҰЖАТПЕН ЖҰМЫС|КОМПЬЮТЕРЛІК ЖҮЙЕЛЕР)",
    re.IGNORECASE,
)

# Roman numeral / section number lines: "## 111", "## IV"
RE_ROMAN_OR_NUM = re.compile(r"^#{1,2}\s+([IVX]+|111|1V)\s*$")

# Image reference in markdown
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)")

# Footnote references [^N]
RE_FOOTNOTE_REF = re.compile(r"\[\^(\d+)\]")

# Abstract block (Mathpix artifact)
RE_ABSTRACT = re.compile(r"^#{1,4}\s+Abstract", re.IGNORECASE)

# Table line in markdown (start with |)
RE_TABLE_LINE = re.compile(r"^#{1,2}\s+TIPEK", re.IGNORECASE)


# ── Helper functions ────────────────────────────────────────────────────────

def should_skip_line(line: str) -> bool:
    """Check if a line should be skipped entirely."""
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


def fix_title(text: str) -> str:
    """Fix OCR artifacts specific to paragraph titles."""
    result = fix_ocr(text)
    for wrong, correct in TITLE_OCR_FIXES.items():
        if wrong in result:
            result = result.replace(wrong, correct)
    return result


def is_internal_heading(heading: str) -> bool:
    """Check if a heading is internal content (not a paragraph boundary)."""
    clean = heading.strip()

    # Exact match
    if clean in INTERNAL_HEADINGS:
        return True

    # OCR-cleaned version
    clean_fixed = fix_ocr(clean)
    if clean_fixed in INTERNAL_HEADINGS:
        return True

    # Prefix match
    for prefix in INTERNAL_HEADINGS:
        if clean.startswith(prefix) or clean_fixed.startswith(prefix):
            return True

    # Watermarks
    if should_skip_line(clean):
        return True

    # Image ref as heading
    if clean.startswith("!["):
        return True

    # Math formula as heading
    if clean.startswith("$"):
        return True

    # Digit-starting heading (task numbers, figure refs, step numbers)
    if clean and clean[0].isdigit():
        return True

    # Very long headings (content, not boundaries)
    if len(clean) > 80:
        return True

    # Questions
    if "?" in clean or "？" in clean:
        return True

    # Single letter or very short
    if len(clean) <= 3:
        return True

    # Contains "сурет" / "сүрет" / "cypet" — figure caption
    if re.search(r"сурет|сүрет|cypet|cyper", clean, re.IGNORECASE):
        return True

    # Contains "кесте" — table caption
    if re.search(r"кесте", clean, re.IGNORECASE):
        return True

    # Chapter-level summary
    if re.search(r"бел[іi]м\S*\s+бойынша", clean, re.IGNORECASE):
        return True
    if re.search(r"бел[іi]мге\s+қорытынды", clean, re.IGNORECASE):
        return True

    # Roman numeral or "111" (OCR for chapter breaks)
    if RE_ROMAN_OR_NUM.match("## " + clean):
        return True

    # Chapter title lines
    if RE_CHAPTER_TITLE.match("## " + clean):
        return True

    # "0 Іске қосу" and similar UI/OCR junk
    if clean.startswith("0 "):
        return True

    # "N-нұсқа" (variant headings)
    if re.match(r"^\d+-нұсқа$", clean):
        return True

    # Headings starting with TIPEK (OCR for key terms as table)
    if clean.startswith("TIPEK"):
        return True

    # "Програама коды" and similar
    if "Програ" in clean and "коды" in clean:
        return True

    return False


def get_chapter_for_para(chapter_digit: int) -> dict | None:
    """Find which chapter a paragraph belongs to based on first digit."""
    for ch in CHAPTERS:
        if chapter_digit in ch["para_range"]:
            return ch
    return None


# ── Parser ──────────────────────────────────────────────────────────────────

def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    """Parse the MMD file into chapters and paragraphs."""
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    paragraphs: list[ParsedParagraph] = []
    current_paragraph: ParsedParagraph | None = None
    in_preamble = True  # Before first paragraph (1.1)
    in_abstract = False
    in_section_summary = False  # Chapter summary/test sections (skip)

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")

        # Skip watermark lines
        if should_skip_line(line):
            continue

        # Stop markers — everything after is appendix
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
                if current_paragraph is not None and not in_section_summary:
                    current_paragraph.content_lines.append(line)
                continue

        # Detect section summary (chapter review/test) — skip content
        if RE_SECTION_SUMMARY.match(line) or RE_SECTION_SUMMARY2.match(line):
            in_section_summary = True
            continue

        # Chapter title lines and Roman numeral markers — skip
        if RE_CHAPTER_TITLE.match(line) or RE_ROMAN_OR_NUM.match(line):
            continue

        # Skip TOC-like lines (contain ..... page numbers)
        if "....." in line or "……" in line:
            if current_paragraph is not None:
                current_paragraph.content_lines.append(line)
            continue

        # Detect paragraph heading: ## N.N. Title or ### N.N. Title
        m = RE_PARAGRAPH_HEADING.match(line)
        if m:
            ch_num = int(m.group(1))
            p_num = int(m.group(2))
            title = fix_title(m.group(3).strip())

            in_preamble = False
            in_section_summary = False
            current_paragraph = ParsedParagraph(
                title=title,
                chapter_num=ch_num,
                para_num=p_num,
                raw_number=f"{ch_num}.{p_num}",
            )
            paragraphs.append(current_paragraph)
            continue

        # Detect paragraph without heading marker (plain text N.N. Title)
        # Only match if it looks like a real paragraph number pattern
        if not line.startswith("#"):
            m2 = RE_PARAGRAPH_PLAIN.match(line)
            if m2:
                ch_num = int(m2.group(1))
                p_num = int(m2.group(2))
                candidate_title = m2.group(3).strip()
                # Validate: must be in expected range and title must be substantial
                if 1 <= ch_num <= 4 and 1 <= p_num <= 6 and len(candidate_title) > 10:
                    # Also check it's not a figure ref like "3.4.1-кесте"
                    if not re.match(r"^\d+-", candidate_title):
                        title = fix_title(candidate_title)
                        in_preamble = False
                        in_section_summary = False
                        current_paragraph = ParsedParagraph(
                            title=title,
                            chapter_num=ch_num,
                            para_num=p_num,
                            raw_number=f"{ch_num}.{p_num}",
                        )
                        paragraphs.append(current_paragraph)
                        continue

        # Skip preamble lines
        if in_preamble:
            continue

        # Skip section summary content
        if in_section_summary:
            # Check if next paragraph starts — exit summary mode
            continue

        # Figure caption headings — include as content
        if RE_FIGURE_CAPTION.match(line):
            if current_paragraph is not None:
                current_paragraph.content_lines.append(line)
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
                # Unknown heading — include as content (conservative approach)
                if current_paragraph is not None:
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
        ch_info = get_chapter_for_para(para.chapter_num)
        if ch_info:
            chapter_map[ch_info["number"]].paragraphs.append(para)
        else:
            print(
                f"  WARNING: {para.raw_number} ({para.title[:40]}) "
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
    in_code_block = False

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

        # Code blocks (``` ... ```)
        if line.strip().startswith("```"):
            if in_code_block:
                in_code_block = False
                html_parts.append("</code></pre>")
            else:
                flush_paragraph()
                if in_list:
                    flush_list()
                if in_table:
                    flush_table()
                in_code_block = True
                html_parts.append(
                    "<pre style='background:#1e293b;color:#e2e8f0;padding:1rem;"
                    "border-radius:0.5rem;overflow-x:auto;margin:1rem 0'><code>"
                )
            continue

        if in_code_block:
            # Escape HTML in code blocks
            escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_parts.append(escaped)
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

        # Task line: "N. Text" (numbered items) — but not "N.N" pattern
        task_match = re.match(r"^(\d+)\.\s+([^.\d].+)", line.strip())
        if task_match:
            flush_paragraph()
            task_num = task_match.group(1)
            task_text = task_match.group(2)
            html_parts.append(
                f'<div style="margin-top:0.75rem;margin-bottom:0.25rem">'
                f'<strong>{task_num}.</strong> {task_text}</div>'
            )
            continue

        # Subtask line: "a) text", "б) text" etc.
        subtask_match = re.match(r"^([а-яa-z])\)\s+(.+)", line.strip())
        if subtask_match:
            flush_paragraph()
            sub_letter = subtask_match.group(1)
            sub_text = subtask_match.group(2)
            html_parts.append(
                f'<div style="margin-left:1.5rem">{sub_letter}) {sub_text}</div>'
            )
            continue

        # Numbered sub-items: "1) text", "2) text"
        num_sub_match = re.match(r"^(\d+)\)\s+(.+)", line.strip())
        if num_sub_match:
            flush_paragraph()
            sub_num = num_sub_match.group(1)
            sub_text = num_sub_match.group(2)
            html_parts.append(
                f'<div style="margin-left:1.5rem">{sub_num}) {sub_text}</div>'
            )
            continue

        # Regular text
        paragraph_lines.append(line)

    # Flush remaining
    if in_code_block:
        html_parts.append("</code></pre>")
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
        f"-- Информатика 6-сынып (Атамура) Textbook Import (Kazakh)",
        f"-- Generated by load_textbook_56.py",
        "",
        "BEGIN;",
        "",
    ]

    total_paragraphs = 0
    global_para_order = 0

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
            global_para_order += 1
            html_content = md_lines_to_html(para.content_lines, TEXTBOOK_ID)
            source_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]

            content_esc = escape_sql(html_content)
            title_esc = escape_sql(para.title)

            # Use global sequential number for paragraph.number
            # to avoid duplicates across chapters (e.g., 1.1 and 2.1 both have para_num=1)
            para_number = global_para_order

            para_where = (
                f"(SELECT id FROM paragraphs WHERE chapter_id = {chapter_where}"
                f" AND number = {para_number} AND is_deleted = false LIMIT 1)"
            )

            sql_lines.append(f"-- {para.raw_number}: {para.title[:50]}")
            sql_lines.append(
                f'INSERT INTO paragraphs (chapter_id, title, number, "order", content, is_deleted)'
            )
            sql_lines.append(
                f"SELECT {chapter_where}, {title_esc}, {para_number}, {p_order},"
            )
            sql_lines.append(f"{content_esc}, false")
            sql_lines.append(f"WHERE NOT EXISTS (")
            sql_lines.append(
                f"    SELECT 1 FROM paragraphs WHERE chapter_id = {chapter_where}"
            )
            sql_lines.append(
                f"    AND number = {para_number} AND is_deleted = false"
            )
            sql_lines.append(f");")
            sql_lines.append("")

            # ParagraphContent for 'kk'
            sql_lines.append(f"INSERT INTO paragraph_contents (")
            sql_lines.append(f"    paragraph_id, language, explain_text,")
            sql_lines.append(f"    source_hash, status_explain,")
            sql_lines.append(
                f"    status_audio, status_slides, status_video, status_cards"
            )
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
    sql_lines.append(
        f"-- Stats: {len(chapters)} chapters, {total_paragraphs} paragraphs"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))

    print(f"\n  Generated SQL: {output_path}")
    print(f"  Chapters: {len(chapters)}, Paragraphs: {total_paragraphs}")
    print(f"\n  To import:")
    print(
        f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/import.sql"
    )
    print(
        f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user"
        f" -d ai_mentor_db -f /tmp/import.sql"
    )


def generate_update_sql(chapters: list[ParsedChapter], output_path: Path):
    """Generate SQL UPDATE statements to refresh content in existing records."""
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE id = {TEXTBOOK_ID} AND is_deleted = false)"
    )

    sql_lines = [
        "-- Информатика 6-сынып (Атамура) Content UPDATE",
        "-- Regenerated HTML with improved formatting",
        "",
        "BEGIN;",
        "",
    ]

    total = 0
    global_para_order = 0

    for chapter in chapters:
        chapter_where = (
            f"(SELECT id FROM chapters WHERE textbook_id = {textbook_where}"
            f" AND number = {chapter.number} AND is_deleted = false LIMIT 1)"
        )

        for para in chapter.paragraphs:
            global_para_order += 1
            para_number = global_para_order
            html_content = md_lines_to_html(para.content_lines, TEXTBOOK_ID)
            content_esc = escape_sql(html_content)
            source_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]

            para_where = (
                f"(SELECT id FROM paragraphs WHERE chapter_id = {chapter_where}"
                f" AND number = {para_number} AND is_deleted = false LIMIT 1)"
            )

            sql_lines.append(
                f"-- Update {para.raw_number}: {para.title[:50]}"
            )
            sql_lines.append(
                f"UPDATE paragraphs SET content = {content_esc}"
            )
            sql_lines.append(f"WHERE id = {para_where};")
            sql_lines.append("")
            sql_lines.append(
                f"UPDATE paragraph_contents SET explain_text = {content_esc},"
            )
            sql_lines.append(
                f"    source_hash = {escape_sql(source_hash)}"
            )
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
    print(
        f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/update.sql"
    )
    print(
        f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user"
        f" -d ai_mentor_db -f /tmp/update.sql"
    )


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Load Информатика 6-сынып (Атамура) into AI Mentor database"
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
    print("  Информатика 6-сынып (Атамура) — Textbook Import")
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


if __name__ == "__main__":
    main()
