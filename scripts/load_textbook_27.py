#!/usr/bin/env python3
"""
Load 'Қазақстан тарихы 9' (History of Kazakhstan, 1945-present) into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='kk'.

This is a HISTORY textbook — no exercises, no A/B/C difficulty levels.
Has 8 бөлім (chapters) and §1-60 paragraphs.
Special: §19-20 has NO heading marker — detected by content trigger.
Some § headings are plain text (not markdown ##).

Usage:
    python scripts/load_textbook_27.py --dry-run           # Parse only
    python scripts/load_textbook_27.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_27.py --update-content FILE # Update SQL
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

TEXTBOOK_ID = 27
TEXTBOOK_TITLE = "Қазақстан тарихы"
SUBJECT_CODE = "history_kz"
GRADE_LEVEL = 9
AUTHORS = "Өскембаев Қ., Сақтағанова З., Мұхтарұлы Ғ."
PUBLISHER = "Мектеп"
YEAR = 2024
ISBN = "978-601-07-1696-4"
LANGUAGE = "kk"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "27" / "textbook_27.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "27"

# Chapter mapping: § number ranges → chapter info (from TOC / МАЗМҰНЫ)
CHAPTERS = [
    {
        "number": 1,
        "title": "І бөлім. ҚАЗАҚСТАН СОҒЫСТАН КЕЙІНГІ ЖЫЛДАРДА (1946-1953 жж.)",
        "para_from": 1,
        "para_to": 6,
    },
    {
        "number": 2,
        "title": "ІІ бөлім. ҚАЗАҚСТАН «ЖЫЛЫМЫҚ» КЕЗЕҢІНДЕ (1953-1964 жж.)",
        "para_from": 7,
        "para_to": 14,
    },
    {
        "number": 3,
        "title": "ІІІ бөлім. ҚАЗАҚСТАН «ТОҚЫРАУ» КЕЗЕҢІНДЕ (1965-1985 жж.)",
        "para_from": 15,
        "para_to": 23,
    },
    {
        "number": 4,
        "title": "IV бөлім. КЕҢЕСТІК ҚАЗАҚСТАННЫҢ МӘДЕНИЕТІ (1946-1985 жж.)",
        "para_from": 24,
        "para_to": 28,
    },
    {
        "number": 5,
        "title": "V бөлім. ҚАЗАҚСТАН ҚАЙТА ҚҰРУ КЕЗЕҢІНДЕ (1986-1991 жж.)",
        "para_from": 29,
        "para_to": 35,
    },
    {
        "number": 6,
        "title": "VI бөлім. ҚАЗАҚСТАН МЕМЛЕКЕТТІЛІГІНІҢ ҚАЙТА ЖАҢҒЫРУЫ (1991-1996 жж.)",
        "para_from": 36,
        "para_to": 46,
    },
    {
        "number": 7,
        "title": "VII бөлім. ҚАЗАҚСТАН РЕСПУБЛИКАСЫНЫҢ ДАМУЫ (1997 жылдан бүгінгі күнге дейін)",
        "para_from": 47,
        "para_to": 56,
    },
    {
        "number": 8,
        "title": "VIII бөлім. ҚАЗІРГІ ЗАМАНҒЫ ҚАЗАҚСТАН МӘДЕНИЕТІ (1991 жылдан бүгінгі күнге дейін)",
        "para_from": 57,
        "para_to": 60,
    },
]

# §19-20 has NO heading marker in the text — use content trigger
MISSING_PARA_TRIGGERS = {
    "Саяси жүйе институттарының қоғамдағы рөлі және орны": {
        "number": 19,
        "raw_number": "19-20",
        "title": "1965-1985 жылдардағы Қазақстандағы қоғамдық-саяси өмірдің ерекшеліктері",
    },
}

# Headings that are internal content within a paragraph (NOT paragraph boundaries)
INTERNAL_HEADINGS = {
    # Lesson structure
    "Бүгін сабақта:", "Бугін сабақта:", "Бүriн сабақта:",
    "Тірек сөздер:", "Тірек сездер:",
    "Сұрақтарға жауап беріңдер.", "Сұрақтарға жауап беріңдер",
    "Тапсырмалар.", "Тапсырмалар", "Тапсырма.", "Тапсырма",
    "Кестемен жұмыс.", "Кестемен жұмыс", "Картамен жұмыс",
    "Нұсқаулық:", "Нүсқаулық:",
    # Preamble
    "Шартты белгі:",
    "Алғы сөз",
    "Қымбатты окушьллар!",
    "Өскембаев Қ., т.б.",
    "(1945 жылдан - бүгінгі күнге дейін)",
    # Section sub-headings (not § boundaries)
    "Соғыстан кейінгі жылдардағы әлеуметтікэкономикалық даму",
    "Қазақстандағы әскери-өнеркәсіптік кешен",
    "Сталиндік идеологияның Қазақстандағы қоғамдық-саяси өмірге әсері",
    "Тың игеру жылдарындағы Қазақстан",
    "Қазақ КСР экономикасының шикізатқа бағытталуы",
    "XX ғасырдың екінші жартысындағы білім беру жүйесінің дамуы",
    "XX ғасырдың 40-80-жылдарындағы Қазақстандық ғалымдардың",
    "XX ғасырдың 40-80-жылдарындағы әдебиет пен өнердің дамуы",
    "Қазақстан Қайта құрудың бастапқы кезеңінде",
    "Қазақстандағы 1986 жылғы Желтоқсан оқиғасы",
    "«Қайта құру» жылдарындағы Қазақстандағы демократиялық үдерістер",
    "Қазақстан Республикасы тәуелсіздігінің жариялануы",
    "Н.Ө.Назарбаев - Қазақстан Республикасының Тұңғыш Президенті",
    "Н.Ә.Назарбаев - Қазақстан Республикасының Тұңғыш Президенті",
    "Тәуелсіздіктің алғашқы жылдарындағы мемлекеттілікті қалыптастырудағы іс-шаралар",
    "Тәуелсіздіктің алғашқы жылдарындағы Қазақстанның экономикалық дамуы",
    "Тәуелсіздіктің алғашқы жылдарындағы әлеуметтік-демографиялық үдерістер",
    "Қазақстанның 1997 жылдан бастап экономикалық дамуы",
    "Қазақстанның 1997 жылдан бастап әлеуметтік дамуы",
    "Халықаралық қатынастар жүйесіндегі Қазақстан",
    "Тәуелсіз Қазақстанның астанасы",
    "«Қазақстан - 2050» Стратегиясы",
    "Тәуелсіз Қазақстан мәдениетінің дамуы",
    "Діннің қазіргі Қазақстан қоғамындағы рөлі",
    "Қорытынды",
    # Watermarks
    "Все учебники Казахстана ищите на сайтах OKULYK.COM и OKULYK.KZ",
    # End-of-book
    "Маңызды оқиғалардың хронологиялық көрсеткіші",
    "Пайдаланылған әдебиеттер тізімі",
    "МАЗМУНЫ",
    # Special
    "AMANAT",
    "МӘҢГІЛІК ЕЛ",
    "5 президенттік реформа:",
}

# OCR artifacts to fix in paragraph titles
OCR_FIXES = {
    "FACЫP": "ҒАСЫР",
    "FACIP": "ҒАСЫР",
    "<br>": " ",
    "<br/>": " ",
    "<br />": " ",
    "．": ".",
    "：": ":",
    "－": "-",
    "әлеуметтікэкономикалық": "әлеуметтік-экономикалық",
    "әлеуметтікдемографиялық": "әлеуметтік-демографиялық",
    "өнеркәсіптіц": "өнеркәсіптің",
    "кезендегі": "кезеңдегі",
    "Қазақстанныц": "Қазақстанның",
    "жаца": "жаңа",
    "Тұнғыш": "Тұңғыш",
    "Улттық": "Ұлттық",
    "урдісі": "үрдісі",
}

SKIP_PATTERNS = [
    "Все учебники Казахстана",
    "OKULYK",
]

FULLWIDTH_MAP = {
    "．": ".",
    "：": ":",
    "－": "-",
    "，": ",",
    "（": "(",
    "）": ")",
    "；": ";",
}


# ── Data classes ────────────────────────────────────────────────────────────


@dataclass
class ParsedParagraph:
    title: str
    number: int
    raw_number: str
    content_lines: list[str] = field(default_factory=list)


@dataclass
class ParsedChapter:
    title: str
    number: int
    paragraphs: list[ParsedParagraph] = field(default_factory=list)


# ── Regex patterns ──────────────────────────────────────────────────────────

RE_PARAGRAPH_HEADING = re.compile(
    r"^#{1,2}\s+§\s*(\d+(?:[－\-]\d+)?)[.\s．]+(.+)", re.IGNORECASE
)

RE_PARAGRAPH_TEXT = re.compile(
    r"^§\s*(\d+(?:[－\-]\d+)?)[.\s．]+(.+)"
)

RE_STOP = re.compile(
    r"^#{0,2}\s*(Маңызды оқиғалардың хронологиялық|Пайдаланылған әдебиеттер|МАЗМУНЫ|Мазмұны)",
    re.IGNORECASE,
)

RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)")
RE_FOOTNOTE_REF = re.compile(r"\[\^(\d+)\]")
RE_ABSTRACT = re.compile(r"^#{1,4}\s+Abstract", re.IGNORECASE)


# ── Helper functions ────────────────────────────────────────────────────────


def normalize_fullwidth(text: str) -> str:
    for fw, ascii_char in FULLWIDTH_MAP.items():
        text = text.replace(fw, ascii_char)
    return text


def should_skip_line(line: str) -> bool:
    for pattern in SKIP_PATTERNS:
        if pattern in line:
            return True
    return False


def fix_ocr(text: str) -> str:
    text = normalize_fullwidth(text)
    for wrong, correct in OCR_FIXES.items():
        text = text.replace(wrong, correct)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def is_internal_heading(heading: str) -> bool:
    clean = heading.strip()

    if clean in INTERNAL_HEADINGS:
        return True

    for prefix in INTERNAL_HEADINGS:
        if clean.startswith(prefix):
            return True

    if should_skip_line(clean):
        return True

    if clean.startswith("!["):
        return True

    if clean.startswith("$"):
        return True

    if clean and clean[0].isdigit():
        return True

    if len(clean) > 80:
        return True

    if "?" in clean:
        return True

    if len(clean) <= 3:
        return True

    if any(ord(c) > 0x3000 for c in clean):
        return True

    if "бөлім" in clean.lower() or "белім" in clean.lower():
        return True

    return False


def get_chapter_for_para(para_number: int) -> dict | None:
    for ch in CHAPTERS:
        if ch["para_from"] <= para_number <= ch["para_to"]:
            return ch
    return None


# ── Parser ──────────────────────────────────────────────────────────────────


def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    paragraphs: list[ParsedParagraph] = []
    current_paragraph: ParsedParagraph | None = None
    in_abstract = False

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")

        if should_skip_line(line):
            continue

        line_norm = normalize_fullwidth(line)

        if RE_STOP.match(line_norm):
            break

        # Skip Abstract blocks (Mathpix artifact)
        if RE_ABSTRACT.match(line):
            in_abstract = True
            continue
        if in_abstract:
            if line.strip() == "":
                in_abstract = False
                continue
            if line.startswith("#"):
                in_abstract = False
            else:
                # Check for § in abstract content
                m_text = RE_PARAGRAPH_TEXT.match(normalize_fullwidth(line.strip()))
                if m_text:
                    raw_num = normalize_fullwidth(m_text.group(1))
                    para_num = int(raw_num.split("-")[0])
                    para_title = fix_ocr(m_text.group(2).strip())
                    current_paragraph = ParsedParagraph(
                        title=para_title, number=para_num, raw_number=raw_num
                    )
                    paragraphs.append(current_paragraph)
                    in_abstract = False
                    continue
                if current_paragraph is not None:
                    current_paragraph.content_lines.append(line)
                continue

        # Detect § paragraph heading (markdown format)
        m = RE_PARAGRAPH_HEADING.match(line_norm)
        if m:
            raw_num = normalize_fullwidth(m.group(1))
            para_num = int(raw_num.split("-")[0])
            para_title = fix_ocr(m.group(2).strip())
            current_paragraph = ParsedParagraph(
                title=para_title, number=para_num, raw_number=raw_num
            )
            paragraphs.append(current_paragraph)
            continue

        # Detect § paragraph as plain text (no # prefix)
        m_text = RE_PARAGRAPH_TEXT.match(line_norm.strip())
        if m_text:
            raw_num = normalize_fullwidth(m_text.group(1))
            para_num = int(raw_num.split("-")[0])
            para_title = fix_ocr(m_text.group(2).strip())
            current_paragraph = ParsedParagraph(
                title=para_title, number=para_num, raw_number=raw_num
            )
            paragraphs.append(current_paragraph)
            continue

        # Check for missing paragraph triggers (§19-20 has no marker)
        stripped = line.strip()
        for trigger_text, para_info in MISSING_PARA_TRIGGERS.items():
            if stripped == trigger_text:
                current_paragraph = ParsedParagraph(
                    title=para_info["title"],
                    number=para_info["number"],
                    raw_number=para_info["raw_number"],
                )
                paragraphs.append(current_paragraph)
                # Include trigger line as content
                current_paragraph.content_lines.append(line)
                break
        else:
            # All other headings — check if internal
            heading_match = re.match(r"^(#{1,4})\s+(.+)", line)
            if heading_match:
                heading_text = heading_match.group(2).strip()
                if is_internal_heading(heading_text):
                    if current_paragraph is not None:
                        current_paragraph.content_lines.append(line)
                    continue
                else:
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
        ch_info = get_chapter_for_para(para.number)
        if ch_info:
            chapter_map[ch_info["number"]].paragraphs.append(para)
        else:
            print(f"  WARNING: §{para.number} ({para.title[:40]}) doesn't belong to any chapter!")

    return [ch for ch in sorted(chapter_map.values(), key=lambda c: c.number) if ch.paragraphs]


# ── Content conversion ──────────────────────────────────────────────────────


def md_lines_to_html(lines: list[str], textbook_id: int) -> str:
    if not lines:
        return ""

    content = "\n".join(lines)

    content = RE_IMAGE.sub(
        lambda m: (
            f'<img src="/uploads/textbook-images/{textbook_id}/{m.group(2)}" '
            f'alt="{m.group(1)}" style="display:block;margin:1rem auto;max-width:100%" />'
        ),
        content,
    )

    content = RE_FOOTNOTE_REF.sub("", content)

    latex_blocks: list[str] = []

    def save_latex(match):
        idx = len(latex_blocks)
        latex_blocks.append(match.group(0))
        return f"__LATEX_{idx}__"

    content = re.sub(r"\$\$[\s\S]*?\$\$", save_latex, content)
    content = re.sub(r"\$[^$\n]+?\$", save_latex, content)

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

        if not line.strip():
            if in_table:
                flush_table()
            if in_list:
                flush_list()
            flush_paragraph()
            continue

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

        if line.strip().startswith("- "):
            if not in_list:
                flush_paragraph()
                in_list = True
            list_items.append(line.strip()[2:])
            continue
        elif in_list:
            flush_list()

        heading_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if heading_match:
            flush_paragraph()
            level = min(len(heading_match.group(1)) + 1, 6)
            heading_text = heading_match.group(2).strip()
            html_parts.append(f"<h{level}>{heading_text}</h{level}>")
            continue

        if line.startswith("> "):
            flush_paragraph()
            html_parts.append(
                f"<blockquote style='border-left:4px solid #93c5fd;padding-left:1rem;"
                f"margin:0.75rem 0;font-style:italic'>{line[2:]}</blockquote>"
            )
            continue

        if line.strip().startswith("<img "):
            flush_paragraph()
            html_parts.append(
                f'<div style="margin:1rem 0;text-align:center">{line.strip()}</div>'
            )
            continue

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

        paragraph_lines.append(line)

    if in_table:
        flush_table()
    if in_list:
        flush_list()
    flush_paragraph()

    html = "\n".join(html_parts)

    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", html)

    for idx, latex in enumerate(latex_blocks):
        html = html.replace(f"__LATEX_{idx}__", latex)

    return html.strip()


# ── SQL helpers ─────────────────────────────────────────────────────────────


def escape_sql(s: str) -> str:
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


# ── Statistics ──────────────────────────────────────────────────────────────


def print_parse_stats(chapters: list[ParsedChapter]):
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
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE id = {TEXTBOOK_ID} AND is_deleted = false)"
    )

    lines = [
        f"-- Қазақстан тарихы 9 Textbook Import (Kazakh)",
        f"-- Generated by load_textbook_27.py",
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
    print(f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/import.sql")
    print(f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/import.sql")


def generate_update_sql(chapters: list[ParsedChapter], output_path: Path):
    textbook_where = (
        f"(SELECT id FROM textbooks WHERE id = {TEXTBOOK_ID} AND is_deleted = false)"
    )

    lines = [
        "-- Қазақстан тарихы 9 Content UPDATE",
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


# ── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Load Қазақстан тарихы 9 textbook into AI Mentor database"
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse only")
    parser.add_argument("--generate-sql", type=str, metavar="FILE", help="Generate SQL")
    parser.add_argument("--update-content", type=str, metavar="FILE", help="Generate UPDATE SQL")
    args = parser.parse_args()

    print("=" * 70)
    print("  Қазақстан тарихы 9 (1945-бүгінгі күн) — Textbook Import")
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
