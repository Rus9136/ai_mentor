#!/usr/bin/env python3
"""
Load 'Информатика 6-сынып' into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='kk'.

This is an INFORMATICS textbook — paragraphs use N.N numbering (no § symbols).
Some headings have OCR spaces in numbers (e.g., "1. 1" → "1.1").
Two paragraphs have no number prefix at all (2.3, 4.2-4.3).
Paragraph 4.4 has its number and title on separate lines.

Usage:
    python scripts/load_textbook_34.py --dry-run           # Parse only
    python scripts/load_textbook_34.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_34.py --update-content FILE # Update SQL
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

TEXTBOOK_ID = 34  # Already exists in DB
TEXTBOOK_TITLE = "Информатика 6-сынып"
SUBJECT_CODE = "informatics"
GRADE_LEVEL = 6
AUTHORS = "Қадырқұлов Р.А., Нұрмұханбетова Г.К."
PUBLISHER = "Алматыкітап"
YEAR = 2019
LANGUAGE = "kk"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "34" / "textbook_34.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "34"

# Chapter mapping based on МАЗМҰНЫ (TOC)
CHAPTERS = [
    {
        "number": 1,
        "title": "I бөлім. КОМПЬЮТЕРЛІК ЖҮЙЕЛЕР ЖӘНЕ ЖЕЛІЛЕР",
        "paragraphs": [
            {"raw": "1.1", "title": "ЭРГОНОМИКА ДЕГЕНІМІЗ НЕ?"},
            {"raw": "1.2", "title": "ҚОҒАМДАҒЫ ИНТЕРНЕТКЕ ТӘУЕЛДІЛІК МӘСЕЛЕЛЕРІ"},
            {"raw": "1.3", "title": "ЕСЕПТЕУ ТЕХНИКАСЫНЫҢ ДАМУ ТАРИХЫ"},
            {"raw": "1.4", "title": "КОМПЬЮТЕР ҚАЛАЙ ЖҰМЫС ІСТЕЙДІ?"},
            {"raw": "1.5", "title": "ОПЕРАЦИЯЛЫҚ ЖҮЙЕ"},
            {"raw": "1.6", "title": "СЫМСЫЗ ЖЕЛІЛЕР"},
            {"raw": "1.7", "title": "ПРАКТИКАЛЫҚ ТАПСЫРМАЛАР"},
        ],
    },
    {
        "number": 2,
        "title": "II бөлім. 3D БАСПА",
        "paragraphs": [
            {"raw": "2.1", "title": "3D РЕДАКТОРЫ"},
            {"raw": "2.2", "title": "3D РЕДАКТОРЫНЫҢ ҚҰРАЛДАРЫ"},
            {"raw": "2.3", "title": "ОБЪЕКТІЛЕРДІҢ ҮШӨЛШЕМДІ МОДЕЛЬДЕРІ. КОНУС, ЦИЛИНДР ЖӘНЕ СФЕРА ҚҰРУ"},
            {"raw": "2.4", "title": "3D РЕДАКТОРДАҒЫ ОБЪЕКТІЛЕРДІҢ МОДЕЛЬДЕРІН ҚҰРУ"},
            {"raw": "2.5", "title": "ОҚИҒАЛАРДЫҢ ҮШӨЛШЕМДІ МОДЕЛЬДЕРІ"},
            {"raw": "2.6", "title": "3D БАСПАСЫН БАПТАУ"},
            {"raw": "2.7", "title": "3D МОДЕЛЬДЕРДІ ПРАКТИКАЛЫҚ ТҰРҒЫДАН ҚҰРАСТЫРУ"},
        ],
    },
    {
        "number": 3,
        "title": "III бөлім. PYTHON ТІЛІНДЕ ПРОГРАММАЛАУ",
        "paragraphs": [
            {"raw": "3.1", "title": "IDE-МЕН ТАНЫСУ"},
            {"raw": "3.2", "title": "ТІЛ АЛФАВИТІ. СИНТАКСИС"},
            {"raw": "3.3", "title": "ДЕРЕКТЕРДІҢ ТИПТЕРІ"},
            {"raw": "3.4", "title": "АРИФМЕТИКАЛЫҚ ӨРНЕКТЕРДІҢ ЖАЗЫЛУ ЕРЕЖЕЛЕРІ"},
            {"raw": "3.5-3.6", "title": "ПРАКТИКАЛЫҚ ТАПСЫРМАЛАР"},
            {"raw": "3.7", "title": "САНДЫ ЕНГІЗУ ЖӘНЕ ШЫҒАРУ"},
            {"raw": "3.8", "title": "СЫЗЫҚТЫҚ АЛГОРИТМДЕРДІ ПРОГРАММАЛАУ"},
            {"raw": "3.9", "title": "ПРАКТИКАЛЫҚ ЖҰМЫС"},
        ],
    },
    {
        "number": 4,
        "title": "IV бөлім. МӘТІНДІК ҚҰЖАТПЕН ЖҰМЫС ІСТЕУ",
        "paragraphs": [
            {"raw": "4.1", "title": "НҰСҚАМА ЖӘНЕ СІЛТЕМЕЛЕР"},
            {"raw": "4.2-4.3", "title": "ГИПЕРСІЛТЕМЕЛЕР ЖӘНЕ ОНЫ ПРАКТИКАЛЫҚ ТҰРҒЫДАН ҚОЛДАНУ"},
            {"raw": "4.4", "title": "ИНТЕРНЕТТЕГІ АВТОРЛЫҚ ҚҰҚЫҚ ЖӘНЕ ПЛАГИАТ МӘСЕЛЕЛЕРІ"},
            {"raw": "4.5", "title": "МАЗМҰНЫ"},
            {"raw": "4.6", "title": "РЕФЕРАТ"},
            {"raw": "4.7", "title": "ПРАКТИКАЛЫҚ ТАПСЫРМАЛАР"},
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
TOTAL_EXPECTED_PARAGRAPHS = _seq  # 28

# OCR spaces in paragraph numbers: "1. 1" → "1.1", "4. 6" → "4.6"
SPACED_NUMBER_MAP = {
    "1. 1": "1.1",
    "3. 9": "3.9",
    "4. 1": "4.1",
    "4. 6": "4.6",
}

# Paragraphs without number prefix — match by title keyword
TITLE_MATCH_PARAGRAPHS = {
    "ОБЪЕКТІЛЕРДІҢ": "2.3",
    "ГИПЕРСІЛТЕМЕЛЕР": "4.2-4.3",
}

# OCR artifacts to fix in titles
OCR_FIXES = {
    "<br>": " ",
    "<br/>": " ",
    "<br />": " ",
    "ТУРFЫДАН": "ТҰРҒЫДАН",
    "ҚҮРМЕТТІ": "ҚҰРМЕТТІ",
    "ЭРГОНОМИКА ДЕГЕНІМІЗ НЕ?": "ЭРГОНОМИКА ДЕГЕНІМІЗ НЕ?",
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
    r"^#{1,2}\s+[IVІ]+\s+Б[ΘОоe][лl][IіiIM]+", re.IGNORECASE
)


# -- Data classes --------------------------------------------------------------


@dataclass
class ParsedParagraph:
    title: str
    number: int          # Global sequential number in DB
    raw_number: str      # Original string (e.g., "1.1", "3.5-3.6")
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# -- Regex patterns ------------------------------------------------------------

# Standard paragraph heading: "## 1.1 TITLE", "### 2.2 TITLE"
RE_PARA_STANDARD = re.compile(
    r"^#{1,3}\s+(\d+\.\d+(?:-\d+\.\d+)?)\s+(.*)", re.IGNORECASE
)

# Spaced number heading: "## 1. 1 TITLE", "## 4. 6 TITLE"
RE_PARA_SPACED = re.compile(
    r"^#{1,3}\s+(\d+)\.\s+(\d+)\s+(.*)", re.IGNORECASE
)

# Number-only heading (split title): "## 4.4" with title on next line
RE_PARA_NUMBER_ONLY = re.compile(
    r"^#{1,3}\s+(\d+\.\d+)\s*$"
)

# Chapter heading: "## I БӨЛІМ", "## II БӨЛІМ", "## IV БӨЛIM"
RE_CHAPTER = re.compile(
    r"^#{1,2}\s+(?:I{1,3}|IV|V|II?)\s+Б[ΘОоe][лl][IіiIM]+", re.IGNORECASE
)

# Stop markers
RE_STOP = re.compile(
    r"^#{1,2}\s+(ГЛОССАРИЙ\b|ПАЙДАЛАНЫЛҒАН\b|МАЗМҰНЫ\b|МАЗМУНЫ\b)",
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

    # Section repeat heading
    if RE_SECTION_REPEAT.match(f"## {clean}"):
        return True

    # Chapter intro sections ("Сен")
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
        "Ойлан", "- Ойлан",
        "Д Жаца білім", "Д Жаңа білім", "Жаңа білім",
        "© Жаңа білім", "1 Жаца білім",
        "Талдау", "Q Талдау", "Q Талдау / Жинақтау", "O Талдау",
        "Жинақтау",
        "Бағалау", "© Бағалау", "©- Бағалау",
        "Тапсырма", "Тапсырма:", "V. Тапсырма", "(z) Тапсырма",
        "- Тапсырма",
        "Үй тапсырмасы",
        "Практикада қолдану", "i Практикада қолдану",
        "1 Практикада қолдану",
        # Preamble
        "Шартты белгілер:", "ҚҮРМЕТТІ ОҚУШЫ!", "ҚҰРМЕТТІ ОҚУШЫ!",
        "Ескерту:",
        # End-of-book
        "ГЛОССАРИЙ", "ПАЙДАЛАНЫЛҒАН ӘДЕБИЕТТЕР ТІЗММ",
        "Оқулықтың үш тілді сөздігінің жинағы",
        "ИНФОРМАТИКА ИНФОРМАТИКА",
        # 1.1 internal
        "Компьютерлік эргономиканың негізгі кеңестері",
        # 1.2 internal
        "Интернетке тәуелділіктің түрлері",
        "Қызық ақпарат",
        # 1.4 internal
        "Компьютер порттары",
        # 1.5 internal
        "Операциялық жүйелердің түрлері",
        "Windows операциялық жүйесі",
        # 1.6 internal
        "Wi-Fi сымсыз желісінің артықшылықтары",
        "Wi-Fi сымсыз желісінің кемшіліктері",
        # 2.1 internal
        "SketchUp 8 терезесі", "Шаблондар:",
        "Начать использование SketchUp",
        # 2.3 internal
        "Жұмыс алацында кеңістікті басқару құралдары",
        "Следуй за мной (Соңымнан ер)",
        "Цилиндр құру", "Конус құру", "Сфера құру",
        # 2.4 internal
        "«Материалдар» модулі",
        "Параллелепипед сызу",
        "«Компоненттер» модулінің қызметін зерттеу",
        "Ол үшін:",
        # 2.5 internal
        "Шығармашылық тапсырма",
        # 2.6 internal
        "3D принтердің құрылысы",
        "3D принтердің «сиясы»",
        "Слайсер",
        "Файл Инструменты Прі",
        "3D принтер усынатын мүмкіндіктер",
        # 3.1 internal
        "Стив Джобс",
        "Python программалау тілін компьютерге орнату",
        # 3.2 internal
        "Python тілінің синтаксисі",
        "Мысал:", "Нәтиже:",
        "Сынып бөлмесінің ауданын есептеу",
        "Цифрларды қосу",
        # 3.3 internal
        "Деректер типі",
        "Айнымалылардың типі",
        # 3.4 internal
        "Python-да арифметикалық өрнектерді орындау ережелері",
        "Инкремент және декремент",
        # 3.7 internal
        "Print() функциясының толық синтаксисі",
        # 3.8 internal
        "Сызықтық құрылымдағы программаны құру қадамдары",
        "Сызықтық программаның құрылымы",
        "Сызықтық программаға тапсырмалар орындау",
        # 3.9 internal
        "Сызықтық программа құрастыр",
        # 4.1 internal
        "Нұсқама құру", "Компьютер",
        "Әлемнің жеті кереметі",
        # 4.2-4.3 internal
        "Гиперсілтеме кірістіру",
        "«Қызыл кітап» электрондық жобасы",
        # 4.5 internal
        "Мазмұнын құру кезеңдері",
        # 4.6 internal
        "Реферат қалай жазылады?",
        "Рефератты қорғауға қатысты кеңестер",
        "Рефератты қорғау кезінде ескер!",
        "Рефератты қорғауда шеберлігіңді көрсет!",
        # 4.7 internal
        "Еліміздегі ец ірі көлдер",
    }

    if clean in internal_exact:
        return True

    # Prefix matches
    internal_prefixes = [
        "1-тапсырма", "2-тапсырма", "3-тапсырма",
        "4-тапсырма", "5-тапсырма",
        "Ойлануға берілген",
        "І БӨЛІМ", "ІІ БӨЛІМ", "II БӨЛІМ", "III БӨЛІМ", "IV БӨЛІМ",
        "IV Бөлім", "IV БӨЛIM", "I БӨЛІМ",
        "Жалпы білім беретін",
        "Кадиркулов",
    ]
    for prefix in internal_prefixes:
        if clean.startswith(prefix):
            return True

    # Headings containing "сурет"/"cypem" (figure references)
    if "сурет" in clean.lower() or "cypem" in clean.lower():
        return True

    # LaTeX section headings
    if "\\section" in clean:
        return True

    return False


def get_known_title(raw_num: str) -> str | None:
    """Get the known title from CHAPTERS for a given raw number."""
    for ch in CHAPTERS:
        for p in ch["paragraphs"]:
            if p["raw"] == raw_num:
                return p["title"]
    return None


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
    # Track if we just saw a number-only heading (for split title like "## 4.4")
    pending_number: str | None = None

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

        # Handle pending number-only heading (split title case)
        if pending_number is not None:
            heading_match = RE_HEADING.match(line)
            if heading_match:
                # The next heading is the title for the pending number
                title = fix_ocr(heading_match.group(2).strip())
                info = resolve_paragraph_number(pending_number)
                if info:
                    known_title = get_known_title(pending_number) or title
                    current_paragraph = ParsedParagraph(
                        title=known_title,
                        number=info[1],
                        raw_number=pending_number,
                    )
                    paragraphs.append(current_paragraph)
                pending_number = None
                continue
            else:
                # Not a heading — use known title
                info = resolve_paragraph_number(pending_number)
                if info:
                    known_title = get_known_title(pending_number) or pending_number
                    current_paragraph = ParsedParagraph(
                        title=known_title,
                        number=info[1],
                        raw_number=pending_number,
                    )
                    paragraphs.append(current_paragraph)
                pending_number = None
                # Don't continue — process this line normally

        # Detect spaced number heading: "## 1. 1 TITLE"
        m_spaced = RE_PARA_SPACED.match(line)
        if m_spaced:
            spaced_key = f"{m_spaced.group(1)}. {m_spaced.group(2)}"
            raw_num = SPACED_NUMBER_MAP.get(spaced_key)
            if raw_num:
                title = m_spaced.group(3).strip()
                title = fix_ocr(title) if title else ""
                info = resolve_paragraph_number(raw_num)
                if info:
                    known_title = get_known_title(raw_num) or title
                    current_paragraph = ParsedParagraph(
                        title=known_title if not title else title,
                        number=info[1],
                        raw_number=raw_num,
                    )
                    paragraphs.append(current_paragraph)
                    continue

        # Detect number-only heading: "## 4.4" (title on next line)
        m_numonly = RE_PARA_NUMBER_ONLY.match(line)
        if m_numonly:
            raw_num = m_numonly.group(1)
            if raw_num in _PARA_LOOKUP:
                pending_number = raw_num
                continue

        # Detect standard paragraph heading: "## 1.2 TITLE", "## 3.5-3.6 TITLE"
        m_std = RE_PARA_STANDARD.match(line)
        if m_std:
            raw_num = m_std.group(1)  # e.g., "1.2" or "3.5-3.6"
            title = m_std.group(2).strip()
            title = fix_ocr(title)

            info = resolve_paragraph_number(raw_num)
            if info:
                known_title = get_known_title(raw_num)
                current_paragraph = ParsedParagraph(
                    title=known_title if not title else title,
                    number=info[1],
                    raw_number=raw_num,
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

            # Check for title-matched unnumbered paragraphs
            matched_raw = None
            for keyword, raw_num in TITLE_MATCH_PARAGRAPHS.items():
                if heading_text.startswith(keyword):
                    matched_raw = raw_num
                    break

            if matched_raw:
                info = resolve_paragraph_number(matched_raw)
                if info:
                    known_title = get_known_title(matched_raw)
                    current_paragraph = ParsedParagraph(
                        title=known_title or fix_ocr(heading_text),
                        number=info[1],
                        raw_number=matched_raw,
                    )
                    paragraphs.append(current_paragraph)
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
    in_code = False

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

        # Code block toggle
        if line.strip().startswith("```"):
            if in_code:
                html_parts.append("</code></pre>")
                in_code = False
            else:
                flush_paragraph()
                if in_list:
                    flush_list()
                if in_table:
                    flush_table()
                html_parts.append("<pre style='background:#f3f4f6;padding:1rem;border-radius:0.5rem;overflow-x:auto;margin:0.75rem 0'><code>")
                in_code = True
            continue

        if in_code:
            html_parts.append(line)
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

        # Numbered line: "N. Text"
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
    if in_code:
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
        f"-- Информатика 6-сынып Textbook Import (Kazakh)",
        f"-- Generated by load_textbook_34.py",
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
        "-- Информатика 6-сынып Content UPDATE",
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
        description="Load Информатика 6-сынып textbook into AI Mentor database"
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
    print("  Информатика 6-сынып — Textbook Import")
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
