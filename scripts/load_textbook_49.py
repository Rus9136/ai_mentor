#!/usr/bin/env python3
"""
Load 'Биология 7-сынып' into the AI Mentor database.

Parses the Mathpix MMD file, creates chapter/paragraph records,
and creates ParagraphContent records for language='kk'.

This is a BIOLOGY textbook — no exercises. Paragraphs are detected by
"Бугін сабақта:" markers (lesson objectives) rather than § headings,
because many §s lack explicit heading markers in the OCR output.

Usage:
    python scripts/load_textbook_49.py --dry-run           # Parse only
    python scripts/load_textbook_49.py --generate-sql FILE  # Generate SQL
    python scripts/load_textbook_49.py --update-content FILE # Update SQL
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

TEXTBOOK_ID = 49  # Already exists in DB
TEXTBOOK_TITLE = "Биология 7-сынып"
SUBJECT_CODE = "biology"
GRADE_LEVEL = 7
AUTHORS = "Соловьева А., Ибраимова Б., Алина Ж."
PUBLISHER = "Мектеп"
YEAR = 2025
ISBN = ""
LANGUAGE = "kk"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "49" / "textbook_49.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "49"

# ── Chapter and paragraph mapping from TOC ──────────────────────────────────

CHAPTERS = [
    {"number": 1, "title": "I бөлім. Экожүйелер", "para_from": 1, "para_to": 7},
    {"number": 2, "title": "II бөлім. Тірі организмдерді жүйелеу", "para_from": 8, "para_to": 11},
    {"number": 3, "title": "III бөлім. Жасушалық биология. Су және органикалық заттар", "para_from": 12, "para_to": 15},
    {"number": 4, "title": "IV бөлім. Заттардың тасымалдануы", "para_from": 16, "para_to": 22},
    {"number": 5, "title": "V бөлім. Тірі организмдердің қоректенуі", "para_from": 23, "para_to": 24},
    {"number": 6, "title": "VI бөлім. Тыныс алу", "para_from": 25, "para_to": 30},
    {"number": 7, "title": "VII бөлім. Бөліп шығару", "para_from": 31, "para_to": 33},
    {"number": 8, "title": "VIII бөлім. Қозғалыс", "para_from": 34, "para_to": 36},
    {"number": 9, "title": "IX бөлім. Координация және реттелу", "para_from": 37, "para_to": 48},
    {"number": 10, "title": "X бөлім. Тұқым қуалау мен өзгергіштік", "para_from": 49, "para_to": 53},
    {"number": 11, "title": "XI бөлім. Көбею. Өсу және даму", "para_from": 54, "para_to": 60},
    {"number": 12, "title": "XII бөлім. Микробиология және биотехнология", "para_from": 61, "para_to": 64},
]

# Paragraph titles from TOC (§1 through §64)
PARA_TITLES = {
    1: "Қоршаған ортаның экологиялық факторлары: абиотикалық және биотикалық",
    2: "Табиғи қоректік тізбектер және қоректік торлар",
    3: "Экологиялық сукцессиялар. Экожүйелердің алмасуы",
    4: "Адам — экожүйенің бір бөлігі",
    5: "Адам іс-әрекетінің экожүйеге жағымсыз әсері",
    6: "Қазақстанда ерекше қорғалатын аймақтар. Жергілікті жердің ерекше қорғалатын аймақтары",
    7: "Қазақстан Республикасының Қызыл кітабы",
    8: "Тірі организмдердің бес патшалығына жалпы сипаттама",
    9: "Өсімдіктер мен жануарлардың негізгі жүйелік топтары. Жүйелеудің маңызы",
    10: "Омыртқасыз және омыртқалы жануарлардың сыртқы құрылысындағы ерекшеліктер",
    11: "Дихотомиялық әдіс. Дихотомиялық кілттерді қолдану",
    12: "Өсімдіктер мен жануарлар жасушаларын салыстыру: ұлпалар, мүшелер, мүшелер жүйесі",
    13: "Судың қасиеттері және биологиялық маңызы",
    14: "Организмдер тіршілігіндегі микроэлементтер мен макроэлементтердің маңызы. Өсімдіктердегі макроэлементтердің тапшылығы. Тыңайтқыштар",
    15: "Азық-түліктердегі органикалық заттар: нәруыздар, майлар, көмірсулар",
    16: "Заттар тасымалдануының тірі организмдердің тіршілік әрекеті үшін маңызы",
    17: "Өсімдіктердің зат тасымалдауға қатысушы мүшелері мен мүшелер жүйесі",
    18: "Сабақтың ішкі құрылысы",
    19: "Тамырдың ішкі құрылысы",
    20: "Атқаратын қызметіне қарай тамыр мен сабақтың құрылысындағы өзара байланыс",
    21: "Ксилема, флоэма және олардың құрылымдық элементтері",
    22: "Жануарлардағы қанайналым мүшелері: буылтық құрттар, ұлулар, буынаяқтылар және омыртқалылар",
    23: "Жапырақтың құрылысы мен қызметі",
    24: "Фотосинтез процесіне қажетті жағдайлар",
    25: "Өсімдіктер мен жануарлар үшін тыныс алудың маңызы",
    26: "Тыныс алудың анаэробты және аэробты типтері",
    27: "Өсімдіктердің тыныс алуы",
    28: "Омыртқасыз және омыртқалы жануарлардың тыныс алу мүшелері",
    29: "Адамның тыныс алу мүшелері",
    30: "Тыныс алу мүшелері ауруларының себептері және алдын алу жолдары",
    31: "Бөліп шығарудың тірі организмдер үшін маңызы",
    32: "Өсімдік бөлінділері",
    33: "Жануарлардың бөліп шығару жүйелері",
    34: "Өсімдіктердің қозғалысы. Қозғалыстың өсімдіктер тіршілігіндегі маңызы",
    35: "Өсімдіктердегі фотопериодизм",
    36: "Жануарлардың қозғалыс мүшелері",
    37: "Жануарлардың жүйке жүйесі типтерін салыстыру",
    38: "Нейронның құрылымы және қызметі",
    39: "Жүйке жүйесінің құрамбөліктері. Жүйке жүйесінің атқаратын қызметі",
    40: "Жүйке жүйесінің орталық және шеткі бөлімдері. Жұлын",
    41: "Ми. Ми бөлімдерінің құрылысы мен қызметі",
    42: "Үлкен ми сыңарлары",
    43: "Рефлекс доғасы",
    44: "Мінез-құлықтың рефлекторлық табиғаты",
    45: "Ішкі мүшелер жұмысының жүйкелік реттелуі",
    46: "Адам организмі үшін ұйқының маңызы. Биологиялық ритмдер",
    47: "Жұмысқа қабілеттілік. Күн тәртібі",
    48: "Жүйке жүйесінің қызметіне ішімдіктің, шылым шегудің және басқа да есірткі заттарының әсері",
    49: "Адамда белгілердің тұқым қуалауында гендер мен дезоксирибонуклеин қышқылының рөлі",
    50: "Генетикалық материалды сақтаушы және тасымалдаушы ДНҚ жайлы түсінік",
    51: "Белгілердің тұқым қуалауында гендердің рөлі",
    52: "Әртүрлі организмдердегі хромосомалар саны",
    53: "Соматикалық және жыныс жасушалары. Гаплоидті және диплоидті хромосомалар жиынтығы",
    54: "Өсімдіктердің жынысты және жыныссыз көбеюі",
    55: "Өсімдіктердің вегетативті жолмен көбеюі, оның түрлері және табиғаттағы биологиялық маңызы",
    56: "Гүлдің құрылысы. Тозаңдану түрлері",
    57: "Өсімдіктердің ұрықтануы және зиготаның түзілуі. Гүлді өсімдіктердегі қосарлы ұрықтану",
    58: "Организмдердің жеке дамуы түсінігі. Өсімдіктер мен жануарлардағы онтогенез кезеңдері",
    59: "Өсімдіктердің өсуі. Сабақтың ұзарып және жуандап өсуі",
    60: "Жануарлардағы тура және түрленіп даму онтогенез типтері",
    61: "Бактериялардың формаларының әртүрлілігі",
    62: "Бактерияларды пайдалану. Табиғаттағы және адам өміріндегі бактериялардың маңызы",
    63: "Патогендермен күресу тәсілдері",
    64: "Вирустар. Вирустардың құрылыс ерекшеліктері",
}

# OCR artifacts to fix
OCR_FIXES = {
    "<br>": " ",
    "<br/>": " ",
    "<br />": " ",
    "：": ":",
    "（": "(",
    "）": ")",
    "，": ",",
    "！": "!",
    "？": "?",
    "．": ".",
    "－": "-",
    "Herisri": "Негізгі",
    "Heriari": "Негізгі",
    "Heriʒri": "Негізгі",
    "Θсімдік": "Өсімдік",
}

# Lines/headings to skip entirely (watermarks, ads)
SKIP_PATTERNS = [
    "Все учебники Казахстана",
    "се учебники Казахстана",
    "OKULYK",
    "риказа Министра",
]

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

# "Бүгін сабақта:" in various OCR-damaged forms
RE_BUGIN_SABAKTA = re.compile(
    r"^#{1,2}\s+(?:\\section\*\{)?Б[уүұ]г[іiї]н\s+сабақта",
    re.IGNORECASE,
)

# Stop markers — everything after these is skipped
# NOTE: МАЗМУНЫ excluded — it appears at the beginning as TOC
RE_STOP = re.compile(
    r"^#{1,2}\s+(ГЛОССАРИЙ\b|Пайдаланылған әдебиеттер)",
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
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def get_chapter_for_para(para_number: int) -> dict | None:
    """Find which chapter a paragraph belongs to based on § number."""
    for ch in CHAPTERS:
        if ch["para_from"] <= para_number <= ch["para_to"]:
            return ch
    return None


# ── Parser ──────────────────────────────────────────────────────────────────


def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    """
    Parse the MMD file into chapters and paragraphs.

    Strategy: Use "Бугін сабақта:" as the definitive paragraph boundary.
    Each occurrence maps sequentially to §1 through §64.
    Content runs from each "Бугін сабақта:" line until the next one
    (or ГЛОССАРИЙ / end of file).
    """
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Phase 1: Find all "Бугін сабақта:" boundary lines
    boundary_lines = []  # (line_index, line_number)
    for idx, raw_line in enumerate(lines):
        line = raw_line.rstrip("\n")
        if RE_BUGIN_SABAKTA.match(line):
            boundary_lines.append(idx)

    print(f"  Found {len(boundary_lines)} 'Бугін сабақта' boundaries (expected 64)")

    if len(boundary_lines) != 64:
        print(f"  WARNING: Expected 64 boundaries, got {len(boundary_lines)}")
        print(f"  First 5 at lines: {[b+1 for b in boundary_lines[:5]]}")
        print(f"  Last 5 at lines: {[b+1 for b in boundary_lines[-5:]]}")

    # Phase 2: Find the stop line (ГЛОССАРИЙ)
    stop_idx = len(lines)
    for idx, raw_line in enumerate(lines):
        line = raw_line.rstrip("\n")
        if RE_STOP.match(line):
            stop_idx = idx
            print(f"  Stop marker at line {idx + 1}: {line.strip()[:60]}")
            break

    # Phase 3: For each boundary, look backward for a title heading
    # and collect content until the next boundary or stop
    paragraphs: list[ParsedParagraph] = []

    for i, boundary_idx in enumerate(boundary_lines):
        para_num = i + 1  # §1 through §64
        title = PARA_TITLES.get(para_num, f"§{para_num}")

        # Determine content start: look up to 10 lines backward for
        # a heading that is the paragraph title (## §N or ## Title)
        content_start = boundary_idx
        for back in range(1, 10):
            check_idx = boundary_idx - back
            if check_idx < 0:
                break
            check_line = lines[check_idx].rstrip("\n").strip()
            if not check_line:
                continue
            # Check if it's a § heading or a title heading
            if re.match(r"^#{1,2}\s+§\s*\d+", check_line):
                content_start = check_idx
                break
            # Check if the heading matches the TOC title (first 20 chars)
            heading_match = re.match(r"^#{1,2}\s+(.+)", check_line)
            if heading_match:
                heading_text = heading_match.group(1).strip()
                # Check if this looks like the paragraph title
                title_prefix = title[:20].lower()
                heading_prefix = fix_ocr(heading_text)[:20].lower()
                if title_prefix[:15] == heading_prefix[:15]:
                    content_start = check_idx
                    break
                # If it's an unrelated heading, stop looking back
                if not should_skip_line(check_line):
                    break

        # Determine content end: next boundary or stop
        if i + 1 < len(boundary_lines):
            next_boundary = boundary_lines[i + 1]
            # Also check backward from next boundary for title heading
            content_end = next_boundary
            for back in range(1, 10):
                check_idx = next_boundary - back
                if check_idx <= boundary_idx:
                    break
                check_line = lines[check_idx].rstrip("\n").strip()
                if not check_line:
                    continue
                if re.match(r"^#{1,2}\s+§\s*\d+", check_line):
                    content_end = check_idx
                    break
                heading_match = re.match(r"^#{1,2}\s+(.+)", check_line)
                if heading_match:
                    heading_text = heading_match.group(1).strip()
                    # Check if this looks like the NEXT paragraph's title
                    next_num = para_num + 1
                    next_title = PARA_TITLES.get(next_num, "")
                    if next_title:
                        next_prefix = next_title[:15].lower()
                        heading_prefix = fix_ocr(heading_text)[:15].lower()
                        if next_prefix == heading_prefix:
                            content_end = check_idx
                            break
                    if not should_skip_line(check_line):
                        break
        else:
            content_end = stop_idx

        # Collect content lines (skip watermarks)
        content_lines = []
        in_abstract = False
        for idx in range(content_start, content_end):
            line = lines[idx].rstrip("\n")

            if should_skip_line(line):
                continue

            if RE_ABSTRACT.match(line):
                in_abstract = True
                continue
            if in_abstract:
                if line.strip() == "" or line.startswith("#"):
                    in_abstract = False
                    if not line.startswith("#"):
                        continue
                else:
                    content_lines.append(line)
                    continue

            content_lines.append(line)

        para = ParsedParagraph(
            title=title,
            number=para_num,
            raw_number=str(para_num),
            content_lines=content_lines,
        )
        paragraphs.append(para)

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
    """Convert markdown content lines to HTML with embedded LaTeX."""
    if not lines:
        return ""

    content = "\n".join(lines)

    # Fix OCR artifacts in content
    content = fix_ocr(content)

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

    # Clean up \section*{} LaTeX artifacts
    content = re.sub(r"\\section\*\{[^}]*\}", "", content)

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

        # Subtask: "N) Text"
        subtask_match = re.match(r"^(\d+)\)\s+(.+)", line.strip())
        if subtask_match:
            flush_paragraph()
            st_num = subtask_match.group(1)
            st_text = subtask_match.group(2)
            html_parts.append(
                f'<div style="margin-left:1.5rem">{st_num}) {st_text}</div>'
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
                f"      §{p.raw_number:>3}. {p_title:<58} "
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
        f"-- Биология 7-сынып Textbook Import (Kazakh)",
        f"-- Generated by load_textbook_49.py",
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

            sql_lines.append(f"-- §{para.raw_number}: {para.title[:50]}")
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

    sql_lines = [
        "-- Биология 7-сынып Content UPDATE",
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

            sql_lines.append(f"-- Update §{para.raw_number}: {para.title[:50]}")
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
    print(
        f"    docker cp {output_path} ai_mentor_postgres_prod:/tmp/update.sql"
    )
    print(
        f"    docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/update.sql"
    )


# ── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Load Биология 7-сынып textbook into AI Mentor database"
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
    print("  Биология 7-сынып — Textbook Import")
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
