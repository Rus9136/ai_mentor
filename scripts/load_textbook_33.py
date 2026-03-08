#!/usr/bin/env python3
"""
Load 'Информатика 5-сынып' into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='kk'.

This is an INFORMATICS textbook — paragraphs use N.N numbering (no § symbols).
Some compound paragraphs have OCR artifacts (e.g., "1.61 .7" → "1.6-1.7").

Usage:
    python scripts/load_textbook_33.py --dry-run           # Parse only
    python scripts/load_textbook_33.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_33.py --update-content FILE # Update SQL
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

TEXTBOOK_ID = 33  # Already exists in DB
TEXTBOOK_TITLE = "Информатика 5-сынып"
SUBJECT_CODE = "informatics"
GRADE_LEVEL = 5
AUTHORS = "Кадыркулов Р., Нурмуханбетова Г."
PUBLISHER = "Алматыкітап"
YEAR = 2020
LANGUAGE = "kk"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "33" / "textbook_33.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "33"

# Chapter mapping based on МАЗМҰНЫ (TOC)
# Paragraphs use chapter.para format (1.1, 1.2, etc.)
# We assign global sequential numbers for the DB
CHAPTERS = [
    {
        "number": 1,
        "title": "I бөлім. АҚПАРАТТЫ ҰСЫНУ",
        "paragraphs": [
            {"raw": "1.1", "title": "БІЗДІҢ АЙНАЛАМЫЗДАҒЫ АҚПАРАТ"},
            {"raw": "1.2", "title": "АҚПАРАТ БЕРУ"},
            {"raw": "1.3", "title": "АҚПАРАТТЫ ШИФРЛАУ"},
            {"raw": "1.4", "title": "ЕКІЛІК АҚПАРАТТЫ ҰСЫНУ"},
            {"raw": "1.5", "title": "ГРАФИКАЛЫҚ АҚПАРАТТЫ ЕКІЛІК КОДТА ҰСЫНУ"},
            {"raw": "1.6-1.7", "title": "ШЫҒАРМАШЫЛЫҚ-ПРАКТИКАЛЫҚ ТАПСЫРМАЛАР"},
        ],
    },
    {
        "number": 2,
        "title": "II бөлім. КОМПЬЮТЕРЛІК ГРАФИКА",
        "paragraphs": [
            {"raw": "2.1", "title": "РАСТРЛЫҚ ЖӘНЕ ВЕКТОРЛЫҚ ГРАФИКАЛЫҚ РЕДАКТОРЛАР"},
            {"raw": "2.2", "title": "РАСТРЛЫҚ СУРЕТТЕРДІ ҚҰРУ ЖӘНЕ РЕДАКЦИЯЛАУ"},
            {"raw": "2.3", "title": "РАСТРЛЫҚ СУРЕТТЕРДІ ӨҢДЕУ"},
            {"raw": "2.4", "title": "РАСТРЛЫҚ СУРЕТТЕРДІ ӨҢДЕУ. ПРАКТИКАЛЫҚ ЖҰМЫС"},
            {"raw": "2.5", "title": "ВЕКТОРЛЫҚ СУРЕТТЕРДІ ҚҰРУ"},
            {"raw": "2.6", "title": "ҚИСЫҚ БЕТІМЕН ЖҰМЫС"},
            {"raw": "2.7", "title": "РАСТРЛЫҚ ЖӘНЕ ВЕКТОРЛЫҚ СУРЕТТЕРДІ САЛЫСТЫРУ"},
        ],
    },
    {
        "number": 3,
        "title": "III бөлім. РОБОТТЕХНИКА",
        "paragraphs": [
            {"raw": "3.1", "title": "РОБОТТЫҢ ТҮРЛЕРІ ЖӘНЕ ОЛАРДЫ ҚОЛДАНУ"},
            {"raw": "3.2", "title": "РОБОТТЕХНИКАНЫҢ ТАРИХЫ ЖӘНЕ ОНЫҢ КЕЛЕШЕГІ"},
            {"raw": "3.3", "title": "ГИРОСКОПИЯЛЫҚ ДАТЧИК"},
            {"raw": "3.4-3.5", "title": "БҰРЫЛЫСТАР. ПРАКТИКАЛЫҚ ЖҰМЫС"},
        ],
    },
    {
        "number": 4,
        "title": "IV бөлім. РОБОТТАРДЫҢ ЖАРЫСЫ",
        "paragraphs": [
            {"raw": "4.1-4.2", "title": "РОБОТТЫҢ СЫЗЫҚ БОЙЫМЕН ҚОЗҒАЛЫСЫ. ПРАКТИКАЛЫҚ ЖҰМЫС"},
            {"raw": "4.3-4.4", "title": "РОБО-СУМО"},
            {"raw": "4.5", "title": "ПРАКТИКАЛЫҚ ТАПСЫРМАЛАР"},
        ],
    },
    {
        "number": 5,
        "title": "V бөлім. КОМПЬЮТЕР ЖӘНЕ ҚАУІПСІЗДІК",
        "paragraphs": [
            {"raw": "5.1", "title": "КОМПЬЮТЕРДЕ ӨЗІҢЕ ЗИЯН КЕЛТІРМЕЙ ҚАЛАЙ ЖҰМЫС ІСТЕУГЕ БОЛАДЫ?"},
            {"raw": "5.2", "title": "АҚПАРАТТЫ ЦИФРЛЫҚ ТАСЫМАЛДАҒЫШТАР"},
            {"raw": "5.3", "title": "ИНТЕРНЕТТЕ ЖҰМЫС ІСТЕУ ҚАНШАЛЫҚ ҚАУІПТІ?"},
            {"raw": "5.4", "title": "КОМПЬЮТЕРДЕГІ ДЕРЕКТІ ҚАЛАЙ ҚОРҒАУҒА БОЛАДЫ?"},
            {"raw": "5.5", "title": "ЖАЛПЫҒА ҚОЛЖЕТІМДІ БУМАЛАР МЕН ФАЙЛДАР ЖАСАУ"},
            {"raw": "5.6-5.7", "title": "ШАҒЫН ЖОБАЛАРДЫ ОРЫНДАУ"},
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
TOTAL_EXPECTED_PARAGRAPHS = _seq  # 26

# OCR fixes for compound paragraph headings in the MMD file
# OCR merged two numbers: "1.6\n1.7" -> "1.61 .7", "3.4\n3.5" -> "3.43 .5"
COMPOUND_OCR_MAP = {
    "1.61": "1.6-1.7",   # ### 1.61 .7
    "3.43": "3.4-3.5",   # ### 3.43 .5
    "4.34": "4.3-4.4",   # ### 4.34 .4
    "5.65": "5.6-5.7",   # ### 5.65 .7
}

# When MMD uses only the first number but TOC says it's compound
SINGLE_TO_COMPOUND = {
    "4.1": "4.1-4.2",    # ## 4.1 but TOC says 4.1-4.2
}

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

# Section repeat headings that contain chapter label
RE_SECTION_REPEAT = re.compile(
    r"^#{1,2}\s+[IVІ]+\s+БӨЛІМ\s+", re.IGNORECASE
)


# -- Data classes --------------------------------------------------------------


@dataclass
class ParsedParagraph:
    title: str
    number: int          # Global sequential number in DB
    raw_number: str      # Original string (e.g., "1.1", "1.6-1.7")
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# -- Regex patterns ------------------------------------------------------------

# Standard paragraph heading: "## 1.1 TITLE", "## 2.3 TITLE"
RE_PARA_STANDARD = re.compile(
    r"^#{1,3}\s+(\d+\.\d+)\s+(.+)", re.IGNORECASE
)

# Compound paragraph with OCR artifact: "### 1.61 .7 TITLE"
RE_PARA_COMPOUND = re.compile(
    r"^#{1,3}\s+(\d+\.\d{2,})\s+\.(\d+)\s+(.*)", re.IGNORECASE
)

# LaTeX-wrapped heading: "## $2.1 \begin{aligned}..."
RE_PARA_LATEX = re.compile(
    r"^#{1,2}\s+\$(\d+\.\d+)\s+\\begin\{aligned\}.*?\\text\s*\{\s*(.+?)(?:\s*\}|$)",
    re.IGNORECASE
)

# Chapter heading: "## I БӨЛІМ", "## II БΘЛІМ", "## IV БелIM"
RE_CHAPTER = re.compile(
    r"^#{1,2}\s+(?:I{1,3}|IV|V|II?)\s+Б[ΘОоe][лl][IіiIM]+", re.IGNORECASE
)

# Stop markers
RE_STOP = re.compile(
    r"^#{1,2}\s+(ГЛОССАРИЙ\b|ПАЙДАЛАНЫЛҒАН\b|MA3M|МАЗМҰНЫ\b)",
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


def is_internal_heading(heading: str) -> bool:
    """Check if a heading is internal content (not a paragraph boundary)."""
    clean = heading.strip()

    # Skip watermarks
    if should_skip_line(clean):
        return True

    # Section repeat heading (e.g., "І БӨЛІМ Ақпаратты ұсыну")
    if RE_SECTION_REPEAT.match(f"## {clean}"):
        return True

    # Chapter intro sections
    if clean == "Сен":
        return True

    # Heading starts with image, formula, digit
    if clean.startswith("![") or clean.startswith("$"):
        return True
    if clean and clean[0].isdigit():
        return True

    # OCR junk: CJK characters
    if any(ord(c) > 0x3000 for c in clean):
        return True

    # Very long headings are content, not boundaries
    if len(clean) > 80:
        return True

    # Very short headings (single chars, "0", etc.)
    if len(clean) <= 2:
        return True

    # Questions
    if "?" in clean:
        return True

    # Known internal headings — exact or prefix match
    internal_exact = {
        # Lesson structure
        "Ойлан", "Д Жаңа білім", "Жаңа білім", "(I) Жаңа білім",
        "(1) Жаңа білім", "1 Жаңа білім",
        "Талдау", "Талдау-жинақтау", "O Талдау",
        "Жинақтау", "Жинақтау-бағалау",
        "Бағалау",
        "Тапсырма", "Тапсырма:",
        "Үй тапсырмасы",
        "Практикада қолдану", "i Практикада қолдану",
        # Preamble
        "Шартты белгілер:", "ҚҰPMETTI ОҚУШЫ!",
        "Р.А. Қадырқұлов, Г.К. Нұрмұханбетова",
        # End-of-book
        "ГЛОССАРИЙ", "ПАЙДАЛАНЫЛҒАН ӘДЕБИЕТТЕР МЕН СІЛТЕМЕЛЕР",
        "MA3M¥HЫ",
        "ИНФОРМАТИКА ИНФОРМАТИКА",
        # Misc content headings inside paragraphs
        "Ақпараттың қабылдау түріне қарай жіктелуі",
        "Ақпараттың ұсыну түріне қарай жіктелуі",
        "Байланыс арналары",
        "Ақпарат көзі мен ақпарат қабылдаушы",
        "Морзе коды (әліппесі)",
        "Шифрлаудың алмастыру әдісі",
        "Ақпаратты кодтау түрлері",
        "Ақпаратты екілік кодтау түрлері",
        "ASCII коды кестесінен үзінді",
        "Юникодта кодтау",
        "Ақпаратты ұсыну нысандары",
        "Растрлық және векторлық графикалық редакторлар",
        "Растрлық және векторлық графикалық редакторлар Векторлық графикалық редакторлар",
        "Paint.NET растрлық графикалық редакторы",
        "Photo Brush векторлық графикалық редакторы",
        "Палитра (түстер) терезесі",
        "Сабын көпіршігін модельдеу",
        "Түс терезесі",
        "Роботтың анықтамасы",
        "Гироскопиялық датчиктің командалық блогы мен режімдері",
        "Измерение (Өлшеу) режімі",
        "Сравнение (Салыстыру) режімі",
        "Роботтың шаршы бойымен қозғалуы",
        "Роботтың шаршы бойымен қозғалу программасын құру",
        "«Сақшы» роботы",
        "«Сақшы» роботының программасы",
        "«Сақшы» роботының программасына түсініктеме",
        "«Балара» роботы",
        "Роботтың сызық бойымен қозғалатын жарысының талаптары:",
        "Жарыс өтетін алацға қойылатын талаптар:",
        "Роботқа қойылатын талаптар:",
        "Бір түс датчигі бар роботтың сызық бойымен қозғалу алгоритмі",
        "Екі түс датчигі бар роботтың сызық бойымен қозғалу алгоритмі",
        "Екі түс датчигі бар роботтың сызық бойымен қозғалу программасы",
        "Робо-сумо жарысының негізгі талаптары:",
        "Lego Mindstroms EV 3 жинағынан дайындалған түрлі жобалар",
        "Компьютердің көзге зияны",
        "Компьютердің омыртқаға, буын мен бұлшық етке кері әсері",
        "Компьютердің жүйкеге кері әсері",
        "Компьютерге тәуелділік",
        "Компьютермен жұмыс кезінде:",
        "Көзге арналған жаттығулар:",
        "Омыртқаға арналған жаттығулар:",
        "Жұмыс орнын дұрыс ұйымдастыру",
        "Электрондық жеке күнделік",
        "Парольдің сипаттамасы",
        "Күрделілігі", "Ұзындығы", "Белгісіздік",
        "Сенімді пароль құрастырудың 5 ережесі",
        "Пароль күрделілігінің 3 деңгейі",
        "Компьютерде жалпыға қолжетімді бумаларды қалай жасаймыз?",
        "Желідегі жалпыға қолжетімді бумаларды пайдалану",
        "RICOH Aficio SP 100SF DDST", "Users",
        "Жоба түрлері",
        "Зерттеу элементтері бар жоба жұмысын жоспарлау парағының үлгісі",
        "Жобаны рәсімдеу үлгісі",
        "Жоба тақырыбы:",
        "Дайын болған жобаларды қағазға басып шығару",
        "Кодты шешу кілті:",
        "Растрлық графикалық редакторлар Векторлық графикалық редакторлар",
        "Туған жер",
        "А тапсырма (1-сурет).",
        "«Ойшыл» робот жобасы",
    }

    if clean in internal_exact:
        return True

    # Prefix matches for numbered tasks, images
    internal_prefixes = [
        "1-тапсырма", "2-тапсырма", "3-тапсырма", "4-тапсырма",
        "5-тапсырма", "6-тапсырма", "7-тапсырма",
        "Ойлануға берілген сұрақтар",
        "І БӨЛІМ", "ІІ БӨЛІМ", "III БӨЛІМ", "IV бөлім", "V бөлім",
        "I БӨЛІМ",
        "Ақпаратты", "Растрлық",
        "Жалпы білім беретін",
        "Кадиркулов",
    ]
    for prefix in internal_prefixes:
        if clean.startswith(prefix):
            return True

    # Headings containing "сурет" (figure references)
    if "сурет" in clean.lower() or "cypem" in clean.lower():
        return True

    return False


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

        # Detect compound paragraph with OCR artifact: "### 1.61 .7 TITLE"
        m_compound = RE_PARA_COMPOUND.match(line)
        if m_compound:
            merged_num = m_compound.group(1)  # e.g., "1.61"
            raw_num = COMPOUND_OCR_MAP.get(merged_num)
            if raw_num:
                # Extract title: group(3) or fallback
                title = m_compound.group(3).strip() if m_compound.group(3) else ""
                title = fix_ocr(title)

                info = resolve_paragraph_number(raw_num)
                if info:
                    current_paragraph = ParsedParagraph(
                        title=title or raw_num,
                        number=info[1],
                        raw_number=raw_num,
                    )
                    paragraphs.append(current_paragraph)
                    continue

        # Detect LaTeX-wrapped heading: "## $2.1 \begin{aligned}..."
        m_latex = RE_PARA_LATEX.match(line)
        if m_latex:
            raw_num = m_latex.group(1)  # e.g., "2.1"
            # For 2.1, extract a cleaner title from the LaTeX
            title_part = m_latex.group(2).strip()
            # Clean up LaTeX artifacts
            title_part = re.sub(r"\\\\.*", "", title_part).strip()
            title_part = re.sub(r"\s*\}.*", "", title_part).strip()
            title_part = fix_ocr(title_part)

            info = resolve_paragraph_number(raw_num)
            if info:
                # Use the known title from TOC instead of OCR mess
                known_title = None
                for ch in CHAPTERS:
                    for p in ch["paragraphs"]:
                        if p["raw"] == raw_num:
                            known_title = p["title"]
                            break

                current_paragraph = ParsedParagraph(
                    title=known_title or title_part,
                    number=info[1],
                    raw_number=raw_num,
                )
                paragraphs.append(current_paragraph)
                continue

        # Detect standard paragraph heading: "## 1.1 TITLE"
        m_std = RE_PARA_STANDARD.match(line)
        if m_std:
            raw_num = m_std.group(1)  # e.g., "1.1"
            title = m_std.group(2).strip()
            title = fix_ocr(title)

            # Check if single number maps to a compound
            resolved_num = SINGLE_TO_COMPOUND.get(raw_num, raw_num)
            info = resolve_paragraph_number(resolved_num)
            if info:
                current_paragraph = ParsedParagraph(
                    title=title,
                    number=info[1],
                    raw_number=resolved_num,
                )
                paragraphs.append(current_paragraph)
                continue
            # If not in lookup, treat as internal heading
            if current_paragraph is not None:
                current_paragraph.content_lines.append(line)
            continue

        # All other headings
        heading_match = RE_HEADING.match(line)
        if heading_match:
            heading_text = heading_match.group(2).strip()

            # Chapter headings — skip
            if RE_CHAPTER.match(line):
                continue

            if is_internal_heading(heading_text):
                if current_paragraph is not None:
                    current_paragraph.content_lines.append(line)
                continue
            else:
                # Unknown heading — before any paragraph = preamble, after = content
                if current_paragraph is None:
                    continue
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
        # Find chapter by looking up raw_number
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

        # Task line: "N. Text" or "N) Text"
        task_match = re.match(r"^(\d+)\)\s+(.+)", line.strip())
        if task_match:
            flush_paragraph()
            html_parts.append(
                f'<div style="margin-left:1.5rem">{task_match.group(1)}) {task_match.group(2)}</div>'
            )
            continue

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
        f"-- Информатика 5-сынып Textbook Import (Kazakh)",
        f"-- Generated by load_textbook_33.py",
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
        "-- Информатика 5-сынып Content UPDATE",
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
        description="Load Информатика 5-сынып textbook into AI Mentor database"
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
    print("  Информатика 5-сынып — Textbook Import")
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
