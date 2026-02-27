#!/usr/bin/env python3
"""
Load 'Алгебра және анализ бастамалары 10 сынып, 2-бөлім' (Kazakh) into AI Mentor DB.

Adapted from load_algebra10_textbook.py for the second part of the textbook.
The source MD file uses \\section*{} instead of markdown ## headings.

Usage:
    python load_algebra10_part2_textbook.py --dry-run
    python load_algebra10_part2_textbook.py --generate-sql /tmp/algebra10p2_import.sql
    python load_algebra10_part2_textbook.py --exercises /tmp/algebra10p2_exercises.sql
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

# ── Path setup ───────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent  # docs/textbooks/algebra10 → project root
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# ── Constants ────────────────────────────────────────────────────────────────

TEXTBOOK_TITLE = "Алгебра және анализ бастамалары 10 сынып, 2-бөлім"
SUBJECT_CODE = "algebra"
GRADE_LEVEL = 10
AUTHORS = "А.Е. Әбілқасымова, Т.П. Кучер, В.Е. Корчевский, З.Ә. Жұмағұлова"
PUBLISHER = "Мектеп"
YEAR = 2019
ISBN = "978-601-07-1149-5"
LANGUAGE = "kk"

MD_FILE = SCRIPT_DIR / "490_with_local_images.md"
IMAGES_SRC_DIR = SCRIPT_DIR / "Images2"
UPLOADS_BASE = PROJECT_ROOT / "uploads"

# ── Chapter definitions (paragraph-number-based assignment) ──────────────────

CHAPTER_DEFS = [
    (6, "Көпмүшелер"),
    (7, "Функцияның шегі және үзіліссіздігі"),
    (8, "Туынды"),
    (9, "Туындыны қолдану"),
    (10, "Кездейсоқ шамалар және олардың сандық сипаттамалары"),
    (0, "10-сыныптағы алгебра және анализ бастамалары курсын қайталауға арналған жаттығулар"),
]


def get_chapter_num(para_num: int) -> int:
    """Map paragraph number to chapter number."""
    if 30 <= para_num <= 35:
        return 6
    if 36 <= para_num <= 39:
        return 7
    if 40 <= para_num <= 45:
        return 8
    if 46 <= para_num <= 51:
        return 9
    if 52 <= para_num <= 54:
        return 10
    return 0

# Headings that are internal content within a paragraph (NOT paragraph boundaries).
# These appear as \section*{HEADING} in the LaTeX source.
INTERNAL_HEADINGS = {
    # Examples / solutions
    "МЫСАЛ", "Мысал", "Дысал", "Дмал", "Дмсал",
    # "You know" sections
    "СЕНДЕР БІЛЕСІҢДЕР", "СЕНДЕР БІЛЕСІНДЕР", "СЕНДЕР БЫПСІНДЕР",
    "СЕНДЕР БЫАЕСІЯДЕР", "СЕНДЕР БМЕСІНАЕР",
    # "Explain" sections (OCR variants)
    "ТУСІНДІРІҢДЕР", "ТУСІНДІРІҢАЕР", "ТУСІНДІРІНДЕР",
    "ТЧСІНДІРІНДЕР", "ТЧСІНДІРІҢДЕР", "ТНСІНДІРІҢДЕР",
    "ТҮСІНДІРІНДЕР", "ТУСІНДІРІҢДЕР",
    # Exercises
    "Жаттығулар", "Жаттығудар",
    # Difficulty levels (handled separately for exercises, but also internal)
    "A", "B", "C",
    # Review exercises
    "ҚАЙТАЛАУ", "Қайталау", "КАЙТАЛАУ", "КАИТАЛАУ", "КАЯТАЛАУ",
    "КАЙТЛАУ", "KARTANAY",
    # Preparation sections
    "Жана білімді менгеруге дайындаламыз",
    "ЖАНА БІЛІМДІ МЕҢГЕРУГЕ АРНАЛҒАН ТІРЕК ҰҒЫМДАР",
    "ЖАНА БІЛІМДІ МЕҢГЕРУТЕ АРНАЛҒАН ТІРЕК ҰҒЫМДАР",
    "ЖАНА БІЛІМДІ МЕНГЕРУГЕ АРНАЛҒАН ТІРЕК ҰҒЫМДАР",
    "ЖАңА БІЛІМДІ МЕҢГЕРУГЕ АРНАЛҒАН ТІРЕК ҰғЫМДАР",
    "ЖАҢА БІЛІМДІ МЕҢГЕРУГЕ АРНАЛҒАН ТІРЕК ҰҒЫМДАР",
    "ЖАҢА БІЛІМДІ МЕҢГЕРУТЕ АРНАЛҒАН ТІРЕК ҰҒЫМДАР",
    # Algorithm
    "АЛГОРИТМ", "Алгоритм",
    # Self-check questions
    "?", "(?) - езіндік тексеру сұрактары",
    # Key terms (OCR variants)
    "Түйінді ұғымдар", "Түйінді уғымдар", "Туйінді уғымдар",
    "ТУЙІНДІ ¥ғымдАР", "ТУЙюндІ ¥ғымдАР", "ТУЙІндІ ¥ғымдАР",
    "ТЧЙІнДІ ұғымдАР", "ТЧЙІНДІ ҰғыМДАР", "ТЧЙІНДІ ұғЫМДАР",
    "ТУЙІНДІ ¥ғыМДАР", "ТУЙІНДІ ұғымдАР",
    # Scientist info
    "ҒАЛЫМ-МАТЕМАТИК ТУРАЛЫ ХАБАРЛАМА ДАЙЫНДАҢДАР",
    "ХАБАРЛАМА ДАЙЫНДАНДАР", "ХАБАРЛАМА ДАЙЫНДАҢДАР",
    # Applied math
    "АУЫЛ ШАРУАШЫЛЫҒЫНДАҒЫ МАТЕМАТИКА",
    "БИЗНЕСТЕГІ МАТЕМАТИКА",
    "ЕСТЕ САҚТАҢДАР",
    # Probability
    "Ыктималдыктар касиеттері",
    # Symbols / preamble
    "ШАРТТЫ БЕЛГІЛЕР:", "АЛҒЫ СӨ3",
    "Практикаға бағытталған тапсырмалар",
    "1-бөлім", "2-бөлім",
    # Chapter titles (skip as content, not paragraph boundaries)
    "ФУНКЦИЯ, ОНЫҢ ҚАСИЕТТЕРІ ЖӘНЕ ГРАФИГІ",
    "ФУНКЦИЯЛАРДЫН ГРАФИКТЕРІН САЛУ",
    "ТРИГОНОМЕТРИЯЛЫҚ ТЕҢДЕУЛЕР ЖӘНЕ ТЕҢСІЗДІКТЕР",
    # Part 2 specific
    "ШАРТТЫ БЕЛГІЛЕР:",
    "Горнер схемасы",
    "Көпмүшелераін бөлінгіштігінін каснеттері:",
    "Көпмүшелердін бөлінгіштігінін қасиеттері:",
    "Часть 2", "А.ТГЕБРА",
    "KARTAILAY",
    # Additional OCR variants for part 2
    "ТЧЙІНДІ ¥ғымдАР", "ТЧйіндІ ҰғымдАР",
    "ТЧСІНДІРІҢАЕР",
}

# OCR artifacts to fix in paragraph titles
OCR_FIXES = {
    "ЖЭНЕ": "ЖӘНЕ",
    "ЖУЙЕСІ": "ЖҮЙЕСІ",
    "ЖҮИЕЛЕРІ": "ЖҮЙЕЛЕРІ",
    "ТЕНСЗДИКТЕРД": "ТЕҢСІЗДІКТЕРДІ",
    "КАСИЕТТЕРI": "ҚАСИЕТТЕРІ",
    "ФУНКЦИЯСЫНЫН ГРАФИГI": "ФУНКЦИЯСЫНЫҢ ГРАФИГІ",
    "ФУНКЦИЯ.ЛАРДЫН": "ФУНКЦИЯЛАРДЫҢ",
    "ФУНКЦИЯ.ЛАР": "ФУНКЦИЯЛАР",
    "КОМБИНАТОРПЫК": "КОМБИНАТОРЛЫҚ",
    "КАЙТА.ІАНАТЫН": "ҚАЙТАЛАНАТЫН",
    "АРНАЛЕАН": "АРНАЛҒАН",
    "ЫКТИМАЛДЫҒЫ ҚАСИЕТТЕРІ": "ЫҚТИМАЛДЫҒЫ. ҚАСИЕТТЕРІ",
    "ОЛАРДЫЦ": "ОЛАРДЫҢ",
    "О.ІАРДЫН": "ОЛАРДЫҢ",
    "ТРИГОНОМЕТРИЯ.ЛЫК": "ТРИГОНОМЕТРИЯЛЫҚ",
    "ТРИГОНОМЕТРИЯ.ТЫК": "ТРИГОНОМЕТРИЯЛЫҚ",
    # Part 2 specific OCR fixes
    "КӨПМУШЕНІН": "КӨПМҮШЕНІҢ",
    "КӨПМУШЕЛЕР": "КӨПМҮШЕЛЕР",
    "КӨПМУШЕГЕ": "КӨПМҮШЕГЕ",
    "КӨПМУШЕНІ": "КӨПМҮШЕНІ",
    "БР АЙНЫМАЛЫСЫ": "БІР АЙНЫМАЛЫСЫ",
    "ЖАЛІЫ ТУРІ": "ЖАЛПЫ ТҮРІ",
    "БУРЫШТАП": "БҰРЫШТАП",
    "ТҮБІРПЕРІН": "ТҮБІРЛЕРІН",
    "КӨБЕЙТКІШТЕРГЕ ЖІКТЕУ ТӘСІЛМЕН": "КӨБЕЙТКІШТЕРГЕ ЖІКТЕУ ТӘСІЛІМЕН",
    "КОЭФФИЩИЕНТТЕР ӨДСІ": "КОЭФФИЦИЕНТТЕР ӘДІСІ",
    "КОЭФФИЩИЕНТТІ": "КОЭФФИЦИЕНТТІ",
    "TYEIPIEPI TYPAJI TEOPEMA": "ТҮБІРЛЕРІ ТУРАЛЫ ТЕОРЕМА",
    "ТЕНДЕУТЕ": "ТЕҢДЕУГЕ",
    "ЖОРАРЫ": "ЖОҒАРЫ",
    "УШШНШІ": "ҮШІНШІ",
    "ЖАЛІЫЛАНҒАН": "ЖАЛПЫЛАНҒАН",
    "ТЗБЕГІНІН": "ТІЗБЕГІНІҢ",
    "ФУНКЦИЯНЫИ": "ФУНКЦИЯНЫҢ",
    "ФУНКЦИЯНЫЦ": "ФУНКЦИЯНЫҢ",
    "НУКТЕДЕГІ": "НҮКТЕДЕГІ",
    "ҮЗІЛІССІЗДІІ": "ҮЗІЛІССІЗДІГІ",
    "ГРАФИГІНІН": "ГРАФИГІНІҢ",
    "ТУЫНДЫНЫИ": "ТУЫНДЫНЫҢ",
    "АНЫКТАМАСЫ": "АНЫҚТАМАСЫ",
    "ЖУРГТЗІЛГЕН": "ЖҮРГІЗІЛГЕН",
    "ЖАНАМАНЫИ": "ЖАНАМАНЫҢ",
    "ТЕНДЕУІ": "ТЕҢДЕУІ",
    "ФУНКЦИЯ.ЛАРДЫН": "ФУНКЦИЯЛАРДЫҢ",
    "КҮРДЕЛІ ФУНКЦИЯНЫН": "КҮРДЕЛІ ФУНКЦИЯНЫҢ",
    "ФУНКЦИЯЛАРДЫН": "ФУНКЦИЯЛАРДЫҢ",
    "ЕКІНшІ": "ЕКІНШІ",
    "ФИЗИКАЛЫК": "ФИЗИКАЛЫҚ",
    "МАҒЫНАСЫ": "МАҒЫНАСЫ",
    "КЕСІНДЦЕГІ": "КЕСІНДІДЕГІ",
    "ЖӘнЕ": "ЖӘНЕ",
    "КІШІІ": "КІШІ",
    "КЕЗДЕЙСОК": "КЕЗДЕЙСОҚ",
    "ЧЗЛІССІЗ": "ҮЗІЛІССІЗ",
    "ШАМАНЫН": "ШАМАНЫҢ",
    "УЛЕСТІРІМ": "ҮЛЕСТІРІМ",
    "ШАМАЛАРДЫН": "ШАМАЛАРДЫҢ",
    "УЛЕСТІРІМІНІН": "ҮЛЕСТІРІМІНІҢ",
    "ТУРЛЕРІ": "ТҮРЛЕРІ",
    "УЛКЕН": "ҮЛКЕН",
    "ДӨНЕСТІГІ": "ДӨҢЕСТІГІ",
    "КӨМЕГТМЕН": "КӨМЕГІМЕН",
    "ФУНКЦИЯНЫИ": "ФУНКЦИЯНЫҢ",
    "ЭКСТРЕМУМДАРЫ": "ЭКСТРЕМУМДАРЫ",
    "НҮКТЕЛЕРІ": "НҮКТЕЛЕРІ",
}

# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class ParsedSubExercise:
    number: str       # "1", "2", ...
    text: str         # text/formula
    answer: str = ""  # answer from ЖАУАПТАРЫ


@dataclass
class ParsedExercise:
    exercise_number: str           # "19.1", "20.12"
    difficulty: str = ""           # "A", "B", "C"
    content_lines: list[str] = field(default_factory=list)
    sub_exercises: list[ParsedSubExercise] = field(default_factory=list)
    answer_text: str = ""
    is_starred: bool = False


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
# This book uses \section*{} instead of markdown ## headings

# Extract content from \section*{...} — handles multi-part with \\
RE_SECTION = re.compile(r"^\\section\*\{(.+)\}(.*)$")

# Paragraph: \section*{§N. TITLE} or \section*{§ N. TITLE}
RE_PARA_SECTION = re.compile(r"^§\s*(\d+)\.\s*(.+)")

# Paragraph as plain text (some §3, §4, §13 lack \section*)
RE_PARA_PLAIN = re.compile(r"^§\s*(\d+)\.\s+(.+)")

# Review chapter start
RE_REVIEW_START = re.compile(r"КАЙТАЛАУҒА АРНАЛҒАН ЖАТТЫҒУЛАР")

# Self-test section
RE_SELF_TEST = re.compile(r"ӨЗІНД[ІI] ТЕКСЕР", re.IGNORECASE)

# Answers section
RE_ANSWERS = re.compile(r"^ЖАУАПТАРЫ$")

# Image reference in markdown
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(\./images/([^)]+)\)")

# Exercise patterns
RE_EXERCISE_NUM = re.compile(r"^(\d+\.\d+)\.?\s*(.*)", re.DOTALL)
RE_SUB_EXERCISE = re.compile(r"^(\d+)\)\s+(.*)")
# Difficulty: \section*{A} or plain "A" on its own line
RE_DIFFICULTY_HEADER = re.compile(r"^([ABC])$")
# Exercises start: \section*{Жаттығулар} or \section*{Жаттығулар \\ A}
RE_EXERCISES_START = re.compile(r"^Жатты[гғ]у[лд]ар", re.IGNORECASE)

# Key terms block
RE_KEY_TERMS = re.compile(r"[ТТ][үу][йи][ІіI][нн]д[іiI]\s+[ұу¥]ғымд", re.IGNORECASE)

# Chapter title patterns to skip (not content, not paragraph boundary)
RE_CHAPTER_TITLE = re.compile(
    r"^(?:"
    r"\d+[-\s]*тарау"                          # "6-тарау", "7-тарау"
    r"|КӨПМУШЕ"                                # chapter 6 title
    r"|ФУНКЦИЯ.{0,5}\s*ШЕГІ"                  # chapter 7 title
    r"|ТУЫНДЫ[НЫ]"                             # chapter 8-9 titles
    r"|КЕЗДЕЙСО"                               # chapter 10 title
    r"|\d+$"                                    # standalone numbers
    r"|МАЗМУНЫ"                                 # TOC
    r")",
    re.IGNORECASE,
)

# LaTeX environments to handle in content
RE_BEGIN_FIGURE = re.compile(r"\\begin\{figure\}")
RE_END_FIGURE = re.compile(r"\\end\{figure\}(.*)")
RE_CAPTION = re.compile(r"\\caption\{(.+?)\}")
RE_CAPTIONSETUP = re.compile(r"\\captionsetup\{.+\}")
RE_INCLUDEGRAPHICS = re.compile(r"\\includegraphics")
RE_BEGIN_TABULAR = re.compile(r"\\begin\{tabular\}")
RE_END_TABULAR = re.compile(r"\\end\{tabular\}")
RE_HLINE = re.compile(r"^\\hline\s*$")
RE_AUTHOR_BLOCK = re.compile(r"^\\author\{")
RE_TITLE_BLOCK = re.compile(r"^\\title\{")
RE_BEGIN_TABLE = re.compile(r"\\begin\{table\}")
RE_END_TABLE = re.compile(r"\\end\{table\}")


# ── Parser ───────────────────────────────────────────────────────────────────



def fix_ocr(title: str) -> str:
    """Fix known OCR artifacts in text."""
    for wrong, correct in OCR_FIXES.items():
        title = title.replace(wrong, correct)
    return title


def is_internal_heading(heading: str) -> bool:
    """Check if a heading text is internal content (not a paragraph boundary)."""
    clean = heading.strip()
    # Strip trailing LaTeX line breaks
    clean = re.sub(r"\s*\\\\.*$", "", clean).strip()
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
    # Heading that starts with $ (math formula)
    if clean.startswith("$"):
        return True
    # Heading that starts with a digit
    if clean and clean[0].isdigit():
        return True
    # Very long headings are usually content
    if len(clean) > 80:
        return True
    # Algorithm variants
    if "лгоритм" in clean.lower() or "АЛГОРИТМ" in clean:
        return True
    # "Аныктама" (definition) headings
    if clean.startswith("Аныктама") or clean.startswith("Анықтама"):
        return True
    # Headings containing function formulas (like "Функцияныи ен үлкен...")
    if clean.startswith("Функция") and "мәндер" in clean.lower():
        return True
    # Glossary headers
    if "Глоссарий" in clean or "глоссарий" in clean:
        return True
    # TOC and publisher info
    if clean.startswith("МАЗМУНЫ") or clean.startswith("Часть") or clean.startswith("А.ТГЕБРА"):
        return True
    return False


def extract_section_content(line: str) -> str | None:
    """Extract content from \\section*{CONTENT}, return None if not a section."""
    m = RE_SECTION.match(line.strip())
    if m:
        return m.group(1).strip()
    return None


def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    """Parse the LaTeX-style markdown file into chapters and paragraphs.

    This book uses \\section*{} instead of markdown ## headings.
    Chapters are assigned based on paragraph numbers, not chapter headings.
    """
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Collect all paragraphs first, then assign to chapters
    all_paragraphs: list[ParsedParagraph] = []
    current_paragraph: ParsedParagraph | None = None
    phase = "preamble"  # preamble | content | answers
    in_figure = False

    # Regex for the final review section at the end
    RE_FINAL_REVIEW = re.compile(
        r"10\s*[-–]?\s*сыныпта[гғ]ы\s+алгебра.*курсын\s+кайталау[гғ]а",
        re.IGNORECASE,
    )

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        # ── Handle \begin{figure}...\end{figure} blocks ─────────────
        # Skip figure environments (they contain external CDN URLs)
        if RE_BEGIN_FIGURE.search(stripped):
            in_figure = True
            continue
        if in_figure:
            m_end = RE_END_FIGURE.search(stripped)
            if m_end:
                in_figure = False
                # Keep text after \end{figure} if any
                after = m_end.group(1).strip()
                if after and current_paragraph is not None:
                    current_paragraph.content_lines.append(after)
            else:
                # Extract caption text from figure
                m_cap = RE_CAPTION.search(stripped)
                if m_cap and current_paragraph is not None:
                    cap_text = m_cap.group(1).strip()
                    if cap_text and not cap_text.startswith("labelformat"):
                        current_paragraph.content_lines.append(f"*{cap_text}*")
            continue

        # ── Extract \section*{} content if present ───────────────────
        section_content = extract_section_content(line)

        # ── Stop at answers section ──────────────────────────────────
        if section_content and RE_ANSWERS.match(section_content):
            break

        # ── Detect final review section ──────────────────────────────
        if section_content and RE_FINAL_REVIEW.search(section_content):
            current_paragraph = ParsedParagraph(
                title="10-сыныптағы алгебра және анализ бастамалары курсын қайталауға арналған жаттығулар",
                number=0,
            )
            all_paragraphs.append(current_paragraph)
            phase = "content"
            continue

        # ── Detect § paragraph (in \section* or plain text) ─────────
        para_match = None
        if section_content:
            para_match = RE_PARA_SECTION.match(section_content)
        if not para_match:
            # Check plain text (for §30, §42 which lack \section*)
            para_match = RE_PARA_PLAIN.match(stripped)

        if para_match:
            para_num = int(para_match.group(1))
            para_title = para_match.group(2).strip()
            # Clean title: remove trailing } from \section*, LaTeX line breaks
            para_title = re.sub(r"\}$", "", para_title).strip()
            para_title = re.sub(r"\s*\\\\.*$", "", para_title).strip()
            para_title = fix_ocr(para_title)
            current_paragraph = ParsedParagraph(
                title=para_title, number=para_num
            )
            all_paragraphs.append(current_paragraph)
            phase = "content"
            continue

        # ── Skip preamble content ────────────────────────────────────
        if phase == "preamble":
            continue

        # ── Detect self-test sections ────────────────────────────────
        if section_content and RE_SELF_TEST.search(section_content):
            current_paragraph = ParsedParagraph(
                title="Өзіңді тексер!", number=900
            )
            all_paragraphs.append(current_paragraph)
            continue

        # ── Handle \section*{} headings that are NOT paragraph boundaries ──
        if section_content:
            # Skip chapter title patterns
            if RE_CHAPTER_TITLE.match(section_content):
                continue
            # Internal headings become content (convert to ## for HTML)
            if is_internal_heading(section_content):
                if current_paragraph is not None:
                    # Handle combined patterns like "Жаттығулар \\ A"
                    clean_heading = re.sub(r"\s*\\\\.*$", "", section_content).strip()
                    current_paragraph.content_lines.append(f"## {clean_heading}")
                    # Check for difficulty after \\ in combined heading
                    if "\\\\" in section_content:
                        after_break = section_content.split("\\\\", 1)[1].strip()
                        if RE_DIFFICULTY_HEADER.match(after_break):
                            current_paragraph.content_lines.append(f"## {after_break}")
                continue
            # Unknown \section* — treat as internal heading
            if current_paragraph is not None:
                current_paragraph.content_lines.append(f"## {section_content}")
            continue

        # ── Skip LaTeX structural lines ──────────────────────────────
        if stripped.startswith("\\captionsetup{"):
            continue
        if stripped.startswith("\\begin{table}") or stripped.startswith("\\end{table}"):
            continue
        if stripped.startswith("\\author{"):
            # Extract author block content
            content = stripped[len("\\author{"):]
            if content.endswith("}"):
                content = content[:-1]
            content = content.replace("\\\\", " ").strip()
            if current_paragraph is not None and content:
                current_paragraph.content_lines.append(content)
            continue
        if stripped.startswith("\\title{"):
            continue

        # ── Accumulate content lines ─────────────────────────────────
        if current_paragraph is not None:
            current_paragraph.content_lines.append(line)

    # ── Assign paragraphs to chapters ────────────────────────────────
    return build_chapters(all_paragraphs)


def build_chapters(paragraphs: list[ParsedParagraph]) -> list[ParsedChapter]:
    """Assign parsed paragraphs to chapters based on paragraph numbers."""
    chapters_map: dict[int, ParsedChapter] = {}
    for ch_num, ch_title in CHAPTER_DEFS:
        chapters_map[ch_num] = ParsedChapter(title=ch_title, number=ch_num)

    last_ch_num = 0
    for para in paragraphs:
        if para.number == 900:
            # Self-test: attach to current chapter
            chapters_map[last_ch_num].paragraphs.append(para)
        elif para.number == 0:
            # Review
            chapters_map[0].paragraphs.append(para)
            last_ch_num = 0
        else:
            ch_num = get_chapter_num(para.number)
            chapters_map[ch_num].paragraphs.append(para)
            last_ch_num = ch_num

    # Return only chapters that have paragraphs, in order
    return [
        chapters_map[ch_num]
        for ch_num, _ in CHAPTER_DEFS
        if chapters_map[ch_num].paragraphs
    ]


# ── Content conversion ───────────────────────────────────────────────────────


def preprocess_content_lines(lines: list[str]) -> list[str]:
    r"""Preprocess content lines: strip remaining LaTeX structural commands.

    This handles LaTeX constructs that weren't caught during parsing:
    - \begin{tabular}...\end{tabular} -> strip formatting, keep text
    - \hline -> skip
    - \captionsetup -> skip
    - \caption{text} -> *text*
    - \begin{align*}...\end{align*} -> wrap in $$...$$
    - Remaining \section*{} -> ## heading
    """
    result = []
    in_tabular = False
    in_align = False

    for line in lines:
        stripped = line.strip()

        # Skip empty \begin{table}/\end{table} wrappers
        if stripped.startswith("\\begin{table}") or stripped.startswith("\\end{table}"):
            continue
        if stripped.startswith("\\captionsetup{"):
            continue
        if RE_CAPTION.match(stripped):
            m = RE_CAPTION.search(stripped)
            if m:
                cap = m.group(1).strip()
                if cap and cap != "labelformat=empty":
                    result.append(f"*{cap}*")
            continue

        # Handle tabular environments - strip formatting, keep cell text
        if RE_BEGIN_TABULAR.search(stripped):
            in_tabular = True
            continue
        if in_tabular:
            if RE_END_TABULAR.search(stripped):
                in_tabular = False
                continue
            if RE_HLINE.match(stripped):
                continue
            # Keep cell content, strip LaTeX table syntax
            cell_line = stripped
            cell_line = re.sub(r"^\\hline\s*", "", cell_line)
            cell_line = cell_line.replace("\\\\", "").strip()
            cell_line = re.sub(r"\s*&\s*", " — ", cell_line)  # column separator
            if cell_line:
                result.append(cell_line)
            continue

        # Handle align* environments - wrap in $$
        if "\\begin{align*}" in stripped:
            in_align = True
            result.append("$$")
            rest = stripped.replace("\\begin{align*}", "").strip()
            if rest:
                result.append(rest)
            continue
        if in_align:
            if "\\end{align*}" in stripped:
                in_align = False
                rest = stripped.replace("\\end{align*}", "").strip()
                if rest:
                    result.append(rest)
                result.append("$$")
                continue
            result.append(line)
            continue

        # Convert remaining \section*{HEADING} to ## HEADING
        m = RE_SECTION.match(stripped)
        if m:
            heading = m.group(1).strip()
            heading = re.sub(r"\s*\\\\.*$", "", heading).strip()
            result.append(f"## {heading}")
            continue

        # Strip \includegraphics with CDN URLs
        if RE_INCLUDEGRAPHICS.search(stripped):
            continue

        result.append(line)

    return result


def md_lines_to_html(lines: list[str], textbook_id: int) -> str:
    """
    Convert markdown content lines to HTML with embedded LaTeX.

    Preserves $...$ and $$...$$ LaTeX syntax for client-side KaTeX rendering.
    Replaces markdown image refs with HTML <img> tags.
    Preprocesses LaTeX structural commands first.
    """
    if not lines:
        return ""

    # Preprocess LaTeX constructs
    lines = preprocess_content_lines(lines)

    content = "\n".join(lines)

    # Replace image references
    content = RE_IMAGE.sub(
        lambda m: (
            f'<img src="/uploads/textbook-images/{textbook_id}/{m.group(2)}" '
            f'alt="{m.group(1)}" style="display:block;margin:1rem auto;max-width:100%" />'
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
            html_parts.append("<table style='width:100%;border-collapse:collapse;margin:1rem 0'>")
            for i, row in enumerate(table_rows):
                cells = [c.strip() for c in row.strip("|").split("|")]
                # Skip separator rows
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
                f"<blockquote style='border-left:4px solid #93c5fd;padding-left:1rem;margin:0.75rem 0;font-style:italic'>"
                f"{line[2:]}</blockquote>"
            )
            continue

        # Image (already converted above, but just in case)
        if line.strip().startswith("<img "):
            flush_paragraph()
            html_parts.append(f'<div style="margin:1rem 0;text-align:center">{line.strip()}</div>')
            continue

        # Task line: "N. Text" (main exercise number)
        task_match = re.match(r"^(\d+)\.\s+(.+)", line.strip())
        if task_match:
            flush_paragraph()
            task_num = task_match.group(1)
            task_text = task_match.group(2)
            html_parts.append(
                f'<div style="margin-top:1.5rem;margin-bottom:0.5rem">'
                f'<strong>{task_num}.</strong> {task_text}</div>'
            )
            continue

        # Subtask line: "N) formula/text"
        subtask_match = re.match(r"^(\d+)\)\s+(.+)", line.strip())
        if subtask_match:
            flush_paragraph()
            sub_num = subtask_match.group(1)
            sub_text = subtask_match.group(2)
            html_parts.append(
                f'<div style="margin-left:1.5rem;margin-top:0.25rem;margin-bottom:0.25rem">'
                f'{sub_num}) {sub_text}</div>'
            )
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
            "description": "Жалпы білім беретін мектептің жаратылыстану-математика бағытындағы 10-сыныбына арналған оқулық. 2-бөлім.",
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


# ── Exercise extraction ──────────────────────────────────────────────────────


def extract_exercises_from_paragraph(para: ParsedParagraph) -> list[ParsedExercise]:
    """Extract structured exercises from a paragraph's content lines.

    Looks for Жаттығулар section (as ## heading from preprocessing),
    then parses A/B/C difficulty levels and individual exercises.
    """
    exercises: list[ParsedExercise] = []
    in_exercises = False
    current_difficulty = ""
    current_exercise: ParsedExercise | None = None

    for line in para.content_lines:
        stripped = line.strip()

        # Detect start of exercises section (converted to ## during parsing)
        heading_match = re.match(r"^#{1,2}\s+(.+)", stripped)
        if heading_match:
            heading_text = heading_match.group(1).strip()
            if RE_EXERCISES_START.match(heading_text):
                in_exercises = True
                # Check if difficulty is on the same line (e.g., "## Жаттығулар" then next "## A")
                continue
            if in_exercises and RE_DIFFICULTY_HEADER.match(heading_text):
                current_difficulty = heading_text
                continue

        # Also detect plain text difficulty header
        if RE_EXERCISES_START.match(stripped):
            in_exercises = True
            continue

        if not in_exercises:
            continue

        # Detect difficulty header (## A, ## B, ## C, or just A, B, C)
        m_diff = RE_DIFFICULTY_HEADER.match(stripped)
        if m_diff:
            current_difficulty = m_diff.group(1)
            continue

        # Skip empty lines
        if not stripped:
            continue

        # Detect exercise number (e.g., "19.1. text" or "19.1 text")
        m_ex = RE_EXERCISE_NUM.match(stripped)
        if m_ex:
            # Save previous exercise
            if current_exercise:
                exercises.append(current_exercise)

            ex_num = m_ex.group(1)
            rest = m_ex.group(2).strip()
            is_starred = "*" in rest[:5] if rest else False
            rest = rest.lstrip("*").strip()

            current_exercise = ParsedExercise(
                exercise_number=ex_num,
                difficulty=current_difficulty,
                content_lines=[rest] if rest else [],
                is_starred=is_starred,
            )

            # Check if rest starts with a sub-exercise immediately
            if rest:
                m_sub = RE_SUB_EXERCISE.match(rest)
                if m_sub:
                    current_exercise.content_lines = []
                    current_exercise.sub_exercises.append(
                        ParsedSubExercise(number=m_sub.group(1), text=m_sub.group(2).strip())
                    )
            continue

        # Detect sub-exercise (e.g., "1) text")
        if current_exercise:
            m_sub = RE_SUB_EXERCISE.match(stripped)
            if m_sub:
                current_exercise.sub_exercises.append(
                    ParsedSubExercise(number=m_sub.group(1), text=m_sub.group(2).strip())
                )
                continue

            # Continuation of current exercise text
            current_exercise.content_lines.append(stripped)

    # Don't forget the last exercise
    if current_exercise:
        exercises.append(current_exercise)

    return exercises


def parse_answers_section(md_path: Path) -> dict[str, str]:
    """Parse the ЖАУАПТАРЫ (answers) section from the MD file.

    Returns a dict mapping exercise_number -> raw answer text.
    """
    answers: dict[str, str] = {}

    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    in_answers = False
    answer_text_lines: list[str] = []

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        # Detect \section*{ЖАУАПТАРЫ}
        section_content = extract_section_content(line)
        if section_content and RE_ANSWERS.match(section_content):
            in_answers = True
            continue

        if not in_answers:
            continue

        # Stop at МАЗМУНЫ (table of contents)
        if section_content and "МАЗМУНЫ" in section_content:
            break
        # Skip \section* subsection headers within answers (chapter sub-headers)
        if section_content:
            continue

        # Skip LaTeX table formatting in answers
        if stripped.startswith("\\begin{") or stripped.startswith("\\end{"):
            continue
        if stripped == "\\hline":
            continue
        # Skip \caption lines (sometimes used instead of \section* for chapter headers)
        if stripped.startswith("\\caption{"):
            continue

        answer_text_lines.append(line)

    # Join all answer lines into one big string
    full_text = " ".join(answer_text_lines)

    # Parse individual answers using regex
    # Answers look like: "19.6. 1) IV ширек; 2) I ширек; ..."
    # We split on exercise number patterns
    parts = re.split(r"(\d+\.\d+)\.?\s*", full_text)

    # parts will be: ['preamble', '19.6', ' answer text', '19.7', ' answer text', ...]
    i = 1  # skip preamble
    while i + 1 < len(parts):
        ex_num = parts[i]
        answer = parts[i + 1].strip().rstrip(",;.")
        if answer:
            answers[ex_num] = answer
        i += 2

    return answers


def merge_answers(
    exercises_by_para: dict[int, list[ParsedExercise]],
    answers: dict[str, str],
):
    """Merge parsed answers into exercises."""
    for para_num, exs in exercises_by_para.items():
        for ex in exs:
            if ex.exercise_number in answers:
                ex.answer_text = answers[ex.exercise_number]

                # Try to split answers into sub-exercise answers
                if ex.sub_exercises and ex.answer_text:
                    sub_parts = re.split(r"(\d+)\)\s*", ex.answer_text)
                    sub_answers: dict[str, str] = {}
                    j = 1
                    while j + 1 < len(sub_parts):
                        sub_num = sub_parts[j]
                        sub_ans = sub_parts[j + 1].strip().rstrip(";,.")
                        sub_answers[sub_num] = sub_ans
                        j += 2

                    for sub in ex.sub_exercises:
                        if sub.number in sub_answers:
                            sub.answer = sub_answers[sub.number]


def generate_exercises_sql(
    chapters: list[ParsedChapter],
    answers: dict[str, str],
    output_path: Path,
):
    """Generate SQL INSERT statements for exercises."""
    textbook_title_esc = escape_sql(TEXTBOOK_TITLE)
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE title = {textbook_title_esc}"
        f" AND grade_level = {GRADE_LEVEL} AND is_deleted = false LIMIT 1)"
    )

    lines = [
        "-- Exercises Import for Algebra 10 (Kazakh)",
        "-- Generated by load_algebra10_textbook.py --exercises",
        "",
        "BEGIN;",
        "",
    ]

    total_exercises = 0
    total_with_answers = 0
    total_sub = 0
    stats_by_difficulty: dict[str, int] = {"A": 0, "B": 0, "C": 0, "": 0}

    for chapter in chapters:
        chapter_where = (
            f"(SELECT id FROM chapters WHERE textbook_id = {textbook_where}"
            f" AND number = {chapter.number} AND is_deleted = false LIMIT 1)"
        )

        for para in chapter.paragraphs:
            exercises = extract_exercises_from_paragraph(para)
            if not exercises:
                continue

            para_number = para.number if para.number != 900 else 100
            para_where = (
                f"(SELECT id FROM paragraphs WHERE chapter_id = {chapter_where}"
                f" AND number = {para_number} AND is_deleted = false LIMIT 1)"
            )

            lines.append(f"-- Paragraph {para_number}: {para.title[:50]}")
            lines.append(f"-- {len(exercises)} exercises")
            lines.append("")

            for sort_idx, ex in enumerate(exercises, 1):
                # Merge answer
                answer = answers.get(ex.exercise_number, "")
                if answer:
                    ex.answer_text = answer

                # Build content text
                content_text = " ".join(ex.content_lines).strip()
                if not content_text and ex.sub_exercises:
                    # Exercise is only sub-exercises, use first line or number
                    content_text = f"Жаттығу {ex.exercise_number}"

                if not content_text:
                    content_text = f"Жаттығу {ex.exercise_number}"

                content_text_esc = escape_sql(content_text)

                # Build content_html
                html_parts = [f"<strong>{ex.exercise_number}.</strong> {content_text}"]
                if ex.sub_exercises:
                    for sub in ex.sub_exercises:
                        html_parts.append(
                            f'<div style="margin-left:1.5rem">{sub.number}) {sub.text}</div>'
                        )
                content_html = "\n".join(html_parts)
                content_html_esc = escape_sql(content_html)

                # Build sub_exercises JSON
                if ex.sub_exercises:
                    # Merge sub-answers
                    if answer:
                        sub_parts = re.split(r"(\d+)\)\s*", answer)
                        sub_answers_map: dict[str, str] = {}
                        j = 1
                        while j + 1 < len(sub_parts):
                            sub_answers_map[sub_parts[j]] = sub_parts[j + 1].strip().rstrip(";,.")
                            j += 2
                        for sub in ex.sub_exercises:
                            if sub.number in sub_answers_map:
                                sub.answer = sub_answers_map[sub.number]

                    sub_json_items = []
                    for sub in ex.sub_exercises:
                        sub_text_esc = sub.text.replace("\\", "\\\\").replace('"', '\\"')
                        sub_answer_esc = sub.answer.replace("\\", "\\\\").replace('"', '\\"') if sub.answer else ""
                        item = f'{{"number":"{sub.number}","text":"{sub_text_esc}"'
                        if sub_answer_esc:
                            item += f',"answer":"{sub_answer_esc}"'
                        item += "}"
                        sub_json_items.append(item)
                    sub_json = "'[" + ",".join(sub_json_items) + "]'::jsonb"
                    total_sub += len(ex.sub_exercises)
                else:
                    sub_json = "NULL"

                has_answer = bool(answer)
                answer_esc = escape_sql(answer) if answer else "NULL"
                difficulty_esc = escape_sql(ex.difficulty) if ex.difficulty else "NULL"

                if has_answer:
                    total_with_answers += 1

                stats_by_difficulty[ex.difficulty] = stats_by_difficulty.get(ex.difficulty, 0) + 1

                lines.append(f"-- Exercise {ex.exercise_number} (difficulty={ex.difficulty or '?'})")
                lines.append(f"INSERT INTO exercises (")
                lines.append(f"    paragraph_id, school_id, exercise_number, sort_order,")
                lines.append(f"    difficulty, content_text, content_html, sub_exercises,")
                lines.append(f"    answer_text, has_answer, is_starred, language, is_deleted")
                lines.append(f") SELECT")
                lines.append(f"    {para_where},")
                lines.append(f"    NULL, {escape_sql(ex.exercise_number)}, {sort_idx},")
                lines.append(f"    {difficulty_esc}, {content_text_esc},")
                lines.append(f"    {content_html_esc},")
                lines.append(f"    {sub_json},")
                lines.append(f"    {answer_esc}, {str(has_answer).lower()}, {str(ex.is_starred).lower()}, 'kk', false")
                lines.append(f"WHERE NOT EXISTS (")
                lines.append(f"    SELECT 1 FROM exercises")
                lines.append(f"    WHERE paragraph_id = {para_where}")
                lines.append(f"    AND exercise_number = {escape_sql(ex.exercise_number)}")
                lines.append(f"    AND is_deleted = false")
                lines.append(f");")
                lines.append("")
                total_exercises += 1

    lines.append("COMMIT;")
    lines.append("")
    lines.append(f"-- Stats: {total_exercises} exercises")
    lines.append(f"-- A: {stats_by_difficulty.get('A', 0)}, B: {stats_by_difficulty.get('B', 0)}, C: {stats_by_difficulty.get('C', 0)}")
    lines.append(f"-- With answers: {total_with_answers}")
    lines.append(f"-- Sub-exercises: {total_sub}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  Generated Exercises SQL: {output_path}")
    print(f"  Total exercises: {total_exercises}")
    print(f"    A: {stats_by_difficulty.get('A', 0)}")
    print(f"    B: {stats_by_difficulty.get('B', 0)}")
    print(f"    C: {stats_by_difficulty.get('C', 0)}")
    print(f"    No difficulty: {stats_by_difficulty.get('', 0)}")
    print(f"  With answers: {total_with_answers}")
    print(f"  Sub-exercises: {total_sub}")
    print(f"\n  To import:")
    print(f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/exercises.sql")
    print(f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/exercises.sql")


# ── SQL helpers ──────────────────────────────────────────────────────────────


def escape_sql(s: str) -> str:
    """Escape string for SQL single-quote literals."""
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


def generate_update_sql(chapters: list[ParsedChapter], output_path: Path):
    """Generate SQL UPDATE statements to refresh content in existing records."""
    textbook_title_esc = escape_sql(TEXTBOOK_TITLE)
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE title = {textbook_title_esc}"
        f" AND grade_level = {GRADE_LEVEL} AND is_deleted = false LIMIT 1)"
    )

    lines = [
        "-- Algebra 10 Textbook Content UPDATE",
        "-- Regenerated HTML with improved formatting",
        "",
        "BEGIN;",
        "",
    ]

    # Get the real textbook_id for image paths
    textbook_id_expr = (
        f"(SELECT id FROM textbooks WHERE title = {textbook_title_esc}"
        f" AND grade_level = {GRADE_LEVEL} AND is_deleted = false LIMIT 1)"
    )

    total = 0
    for chapter in chapters:
        chapter_where = (
            f"(SELECT id FROM chapters WHERE textbook_id = {textbook_where}"
            f" AND number = {chapter.number} AND is_deleted = false LIMIT 1)"
        )

        for p_order, para in enumerate(chapter.paragraphs, 1):
            para_number = para.number if para.number != 900 else 100 + p_order
            # Build HTML with placeholder textbook_id=0, then replace
            html_content = md_lines_to_html(para.content_lines, 0)
            content_esc = escape_sql(html_content)

            para_where = (
                f"(SELECT id FROM paragraphs WHERE chapter_id = {chapter_where}"
                f" AND number = {para_number} AND is_deleted = false LIMIT 1)"
            )

            lines.append(f"-- Update paragraph {para_number}: {para.title[:50]}")
            lines.append(f"UPDATE paragraphs SET content = {content_esc}")
            lines.append(f"WHERE id = {para_where};")
            lines.append("")
            lines.append(f"UPDATE paragraph_contents SET explain_text = {content_esc}")
            lines.append(f"WHERE paragraph_id = {para_where} AND language = 'kk';")
            lines.append("")
            total += 1

    # Fix image paths
    lines.append("-- Update image paths with actual textbook_id")
    lines.append(f"UPDATE paragraphs SET content = REPLACE(content, '/textbook-images/0/', '/textbook-images/' || {textbook_id_expr} || '/')")
    lines.append(f"WHERE chapter_id IN (SELECT id FROM chapters WHERE textbook_id = {textbook_where});")
    lines.append("")
    lines.append(f"UPDATE paragraph_contents SET explain_text = REPLACE(explain_text, '/textbook-images/0/', '/textbook-images/' || {textbook_id_expr} || '/')")
    lines.append(f"WHERE paragraph_id IN (SELECT p.id FROM paragraphs p JOIN chapters c ON c.id = p.chapter_id WHERE c.textbook_id = {textbook_where});")
    lines.append("")

    lines.append("COMMIT;")
    lines.append(f"-- Updated {total} paragraphs")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  Generated UPDATE SQL: {output_path}")
    print(f"  Paragraphs to update: {total}")
    print(f"\n  To apply:")
    print(f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/update_content.sql")
    print(f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/update_content.sql")


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
        "-- Algebra 10 Part 2 Textbook Import (Kazakh)",
        "-- Generated by load_algebra10_textbook.py",
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
        f"    {escape_sql('Жалпы білім беретін мектептің жаратылыстану-математика бағытындағы 10-сыныбына арналған оқулық. 2-бөлім.')},",
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
        description="Load Algebra 10 textbook (Kazakh) into AI Mentor database"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse only, no DB writes"
    )
    parser.add_argument(
        "--generate-sql", type=str, metavar="FILE",
        help="Generate SQL file instead of direct DB connection"
    )
    parser.add_argument(
        "--update-content", type=str, metavar="FILE",
        help="Generate SQL UPDATE file to refresh content in existing records"
    )
    parser.add_argument(
        "--exercises", type=str, metavar="FILE",
        help="Generate SQL file for exercises import"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  Algebra 10 Part 2 Textbook Import (Kazakh)")
    print("=" * 70)

    # 1. Parse MD file
    print(f"\nStep 1: Parsing {MD_FILE.name}...")
    if not MD_FILE.exists():
        print(f"  ERROR: File not found: {MD_FILE}")
        sys.exit(1)

    chapters = parse_textbook(MD_FILE)
    print_parse_stats(chapters)

    if args.dry_run:
        # Also print exercise stats in dry-run mode
        print("\n--- Exercise Parsing Preview ---")
        total_ex = 0
        for ch in chapters:
            for p in ch.paragraphs:
                exs = extract_exercises_from_paragraph(p)
                if exs:
                    print(f"  §{p.number}: {len(exs)} exercises")
                    for ex in exs[:3]:
                        sub_count = len(ex.sub_exercises)
                        text_preview = " ".join(ex.content_lines)[:60]
                        print(f"    {ex.exercise_number} [{ex.difficulty}] {text_preview}... ({sub_count} sub)")
                    if len(exs) > 3:
                        print(f"    ... and {len(exs) - 3} more")
                    total_ex += len(exs)
        print(f"\n  Total exercises found: {total_ex}")
        print("\n[DRY RUN] Stopping before DB operations.")
        return

    # Exercises mode — generate SQL for exercises import
    if args.exercises:
        print(f"\nStep 2: Parsing answers section...")
        answers = parse_answers_section(MD_FILE)
        print(f"  Found answers for {len(answers)} exercises")

        print(f"\nStep 3: Generating Exercises SQL file...")
        generate_exercises_sql(chapters, answers, Path(args.exercises))
        return

    # Update content mode — regenerate HTML and update existing records
    if args.update_content:
        print(f"\nStep 2: Generating UPDATE SQL file...")
        generate_update_sql(chapters, Path(args.update_content))
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
