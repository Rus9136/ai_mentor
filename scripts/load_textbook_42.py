#!/usr/bin/env python3
"""
Load 'Алгебра 8-сынып' into the AI Mentor database.

Textbook ID: 42 (already exists in DB)
Structure: 5 chapters, 20 paragraphs, exercises A/B/C, answers section.

Usage:
    python scripts/load_textbook_42.py --dry-run            # Parse only
    python scripts/load_textbook_42.py --generate-sql FILE   # Generate SQL
    python scripts/load_textbook_42.py --exercises FILE      # Exercises SQL
    python scripts/load_textbook_42.py --update-content FILE # Update existing content
"""
import re
import sys
import json
import hashlib
import argparse
from pathlib import Path
from dataclasses import dataclass, field

# ── Path setup ───────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# ── Constants ────────────────────────────────────────────────────────────────

TEXTBOOK_ID = 42
TEXTBOOK_TITLE = "Алгебра 8-сынып"
SUBJECT_CODE = "algebra"
GRADE_LEVEL = 8
AUTHORS = "Абылкасымова А.Е., Кучер Т., Корчевский В., Жумагулова З."
PUBLISHER = "Мектеп"
YEAR = 2018
ISBN = "978-601-07-0967-6"
LANGUAGE = "kk"

MD_FILE = PROJECT_ROOT / "uploads" / "textbook-mmd" / "42" / "textbook_42.mmd"
IMAGES_SRC_DIR = PROJECT_ROOT / "uploads" / "textbook-images" / "42"

# Chapter mapping: § number ranges → (chapter_number, chapter_title)
CHAPTER_MAP = {
    1: (1, "I тарау. Квадрат түбір және иррационал өрнектер"),
    2: (1, None), 3: (1, None), 4: (1, None), 5: (1, None),
    6: (2, "II тарау. Квадрат теңдеулер"),
    7: (2, None), 8: (2, None), 9: (2, None), 10: (2, None),
    11: (2, None), 12: (2, None),
    13: (3, "III тарау. Квадраттық функция"),
    14: (3, None),
    15: (4, "IV тарау. Статистика элементтері"),
    16: (4, None), 17: (4, None),
    18: (5, "V тарау. Теңсіздіктер"),
    19: (5, None), 20: (5, None),
}

# Clean titles for paragraphs (OCR is too garbled for some)
PARA_TITLE_OVERRIDES = {
    1: "Нақты сандар",
    2: "Квадрат түбір",
    3: "Арифметикалық квадрат түбірдің қасиеттері",
    4: "Құрамында квадрат түбірлері бар өрнектерді тепе-тең түрлендіру",
    5: "$y=\\sqrt{x}$ функциясы, оның қасиеттері және графигі",
    6: "Квадрат теңдеу. Квадрат теңдеулердің түрлері",
    7: "Квадрат теңдеуді шешу",
    8: "Виет теоремасы",
    9: "Квадрат үшмүше",
    10: "Бөлшек-рационал теңдеулер",
    11: "Квадрат теңдеуге келтірілетін теңдеулер",
    12: "Квадрат теңдеулер арқылы мәтінді есептерді шығару",
    13: "$y=a(x-m)^{2}$, $y=ax^{2}+n$, $y=(x-m)^{2}+n$ $(a \\neq 0)$ түріндегі квадраттық функциялар, олардың графиктері",
    14: "$y=ax^{2}+bx+c$ $(a \\neq 0)$ функциясы, оның қасиеттері және графигі",
    15: "Интервалдық кесте. Гистограмма",
    16: "Жиналталған жиілік",
    17: "Орта мән. Дисперсия. Стандартты ауытқу",
    18: "Квадрат теңсіздік. Квадрат теңсіздікті квадраттық функцияның графигі арқылы шығару",
    19: "Рационал теңсіздіктер. Интервалдар әдісі",
    20: "Бір айнымалысы бар сызықтық емес теңсіздіктер жүйесі",
}

# Headings that are internal content (NOT paragraph boundaries)
INTERNAL_HEADINGS = {
    "Түсіндіріңдер", "Тусіндіріңдер", "Түсіндіріцдер",
    "Түсіндіріндер", "Тусіндіріндер",
    "Жаттығулар", "Жаттыгулар", "Жаттынулар",
    "A", "B", "C",
    "Қайталау", "Кайталау", "Кайгалау",
    "Жана білімді менгеруге дайындаламыз",
    "Жана білімді менгеруге дайывдаламыз",
    "Жана білімді мецгеруте дайындаламыз",
    "Жана білімді ментеруге дайындаламыз",
    "Жана білімді менгеруге дайындадамыз",
    "Жана білімді менгеруте дайындаламыз",
    "Жаца білімді менгеруге дайындаламыз",
    "Жаца білімді мецгеруге дайындаламыз",
    "Жаца білімді менгеруге дайышдаламыз",
    "Жаца бблімді менгеруге дайындаламыз",
    "Жада білімді менгеруге дайындаламыз",
    "Жана білімді менчеруге дайындаламыз",
    "Математика тарихынан мағлуматтар",
    "Практикалык тапсырма",
    "Квадрат тендеулер",
    "Толымсыз квадрат тендеулер калай шығарылады?",
    "Сонымен:", "Сондыктан",
    "(2)",
    "AATEEPA",
    "АЛҒЫ СӨЗ",
    "Шартты белгілер:",
    "( 8",
}

# OCR fixes
OCR_FIXES = {
    "ТУБІР": "ТҮБІР",
    "ЖЭНЕ": "ЖӘНЕ",
    "ТЕНСЗДЕК": "ТЕҢСІЗДІК",
    "ТЕНСІЗДКТІ": "ТЕҢСІЗДІКТІ",
    "ТЕНСПДЮТЕР": "ТЕҢСІЗДІКТЕР",
    "ТЕНСІЗДКТЕР": "ТЕҢСІЗДІКТЕР",
    "ТЕПЕ-ТЕН": "ТЕПЕ-ТЕҢ",
    "ТУРЛЕНДРУ": "ТҮРЛЕНДІРУ",
    "ТУРДЕНДІРУ": "ТҮРЛЕНДІРУ",
    "КАСИЕТТЕРІ": "ҚАСИЕТТЕРІ",
    "ΘΡΗΕΚΤΕΡ": "ӨРНЕКТЕР",
    "АРНАЛЕАН": "АРНАЛҒАН",
}


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class ParsedSubExercise:
    number: str
    text: str
    answer: str = ""


@dataclass
class ParsedExercise:
    exercise_number: str       # "1.1", "2.15"
    difficulty: str = ""       # "A", "B", "C"
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

# Paragraph heading: "§ 1. TITLE", "## § 2. TITLE"
RE_PARAGRAPH = re.compile(
    r"^(?:#{1,2}\s+)?§\s*(\d+)[\.\s]+(.+)", re.IGNORECASE
)

# Stop markers — end of main content
RE_STOP = re.compile(
    r"^#{1,2}\s+(8-СЫНЫП\b|ПӘНД[ІК]|ЖАУАПТАР\b|ПРАКТИКАҒА\b)",
    re.IGNORECASE,
)

# Review sections to skip (both 7th and 8th grade review)
RE_REVIEW = re.compile(
    r"КАЙТАЛАУ[ҒГ]А\s+АРНА", re.IGNORECASE
)

# Image reference: ![...](images/file.jpg)
RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)")

# Exercise patterns
RE_EXERCISE_NUM = re.compile(r"^(\d+\.\d+)\.?\s*(.*)", re.DOTALL)
RE_SUB_EXERCISE = re.compile(r"^(\d+)\)\s+(.*)")
RE_DIFFICULTY_HEADER = re.compile(r"^(?:#{1,2}\s+)?([ABC])$")
RE_EXERCISES_START = re.compile(r"^(?:#{1,2}\s+)?Жатты[гғн]у[лд]ар", re.IGNORECASE)


# ── Parser ───────────────────────────────────────────────────────────────────


def fix_ocr(title: str) -> str:
    for wrong, correct in OCR_FIXES.items():
        title = title.replace(wrong, correct)
    return title


def is_internal_heading(heading: str) -> bool:
    clean = heading.strip()
    if clean in INTERNAL_HEADINGS:
        return True
    for prefix in INTERNAL_HEADINGS:
        if clean.startswith(prefix):
            return True
    if clean.startswith("![") or clean.startswith("$"):
        return True
    if clean and clean[0].isdigit():
        return True
    if len(clean) > 80:
        return True
    if "?" in clean:
        return True
    return False


def parse_textbook(md_path: Path) -> list[ParsedChapter]:
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    chapters: list[ParsedChapter] = []
    chapters_by_num: dict[int, ParsedChapter] = {}
    current_paragraph: ParsedParagraph | None = None
    in_preamble = True
    stopped = False

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")

        # Skip preamble lines (before first §)
        if in_preamble:
            m = RE_PARAGRAPH.match(line)
            if not m:
                continue
            # Found first §, fall through to paragraph detection below

        # Stop at answers/index/end-of-book review (only after preamble)
        if RE_STOP.search(line):
            stopped = True
            current_paragraph = None
            break

        # Detect § paragraph heading
        m = RE_PARAGRAPH.match(line)
        if m:
            # Filter out false positives: "§18 карастырылған..." (reference, not heading)
            rest_after = m.group(2).strip()
            if rest_after.startswith("карастырылған"):
                if current_paragraph is not None:
                    current_paragraph.content_lines.append(line)
                continue

            in_preamble = False
            para_num = int(m.group(1))
            para_title = PARA_TITLE_OVERRIDES.get(para_num, rest_after)
            para_title = re.sub(r"<br\s*/?>", " ", para_title).strip()
            para_title = fix_ocr(para_title)

            # Determine chapter
            ch_num, ch_title = CHAPTER_MAP.get(para_num, (0, None))
            if ch_num not in chapters_by_num:
                if ch_title is None:
                    ch_title = f"Тарау {ch_num}"
                chapter = ParsedChapter(title=ch_title, number=ch_num)
                chapters.append(chapter)
                chapters_by_num[ch_num] = chapter

            current_paragraph = ParsedParagraph(title=para_title, number=para_num)
            chapters_by_num[ch_num].paragraphs.append(current_paragraph)
            continue

        # Skip preamble lines
        if in_preamble:
            continue

        # Skip heading lines that are internal
        heading_match = re.match(r"^(#{1,2})\s+(.+)", line)
        if heading_match:
            heading_text = heading_match.group(2).strip()
            if is_internal_heading(heading_text):
                # Still add to content
                if current_paragraph is not None:
                    current_paragraph.content_lines.append(line)
                continue
            # Chapter title lines (КВАДРАТ ТЕҢДЕУЛЕР, etc.) — just add to content
            if current_paragraph is not None:
                current_paragraph.content_lines.append(line)
            continue

        # Accumulate content
        if current_paragraph is not None:
            current_paragraph.content_lines.append(line)

    return chapters


# ── Content conversion ───────────────────────────────────────────────────────


def md_lines_to_html(lines: list[str], textbook_id: int) -> str:
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

    # Protect LaTeX from processing
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

    for raw_line in content.split("\n"):
        line = raw_line.rstrip()

        if not line.strip():
            if in_table:
                flush_table()
            flush_paragraph()
            continue

        if line.strip().startswith("|"):
            if not in_table:
                flush_paragraph()
                in_table = True
            table_rows.append(line)
            continue
        elif in_table:
            flush_table()

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

        # List item
        list_match = re.match(r"^[-*]\s+(.+)", line.strip())
        if list_match:
            flush_paragraph()
            html_parts.append(
                f'<div style="margin-left:1rem;margin-top:0.25rem">- {list_match.group(1)}</div>'
            )
            continue

        # Task line: "N. Text"
        task_match = re.match(r"^(\d+)\.\s+(.+)", line.strip())
        if task_match:
            flush_paragraph()
            html_parts.append(
                f'<div style="margin-top:1.5rem;margin-bottom:0.5rem">'
                f'<strong>{task_match.group(1)}.</strong> {task_match.group(2)}</div>'
            )
            continue

        # Subtask: "N) text"
        subtask_match = re.match(r"^(\d+)\)\s+(.+)", line.strip())
        if subtask_match:
            flush_paragraph()
            html_parts.append(
                f'<div style="margin-left:1.5rem;margin-top:0.25rem;margin-bottom:0.25rem">'
                f'{subtask_match.group(1)}) {subtask_match.group(2)}</div>'
            )
            continue

        paragraph_lines.append(line)

    if in_table:
        flush_table()
    flush_paragraph()

    html = "\n".join(html_parts)

    # Inline formatting
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", html)

    # Restore LaTeX
    for idx, latex in enumerate(latex_blocks):
        html = html.replace(f"__LATEX_{idx}__", latex)

    return html.strip()


# ── SQL generation ───────────────────────────────────────────────────────────


def escape_sql(s: str) -> str:
    return s.replace("'", "''") if s else ""


def generate_sql(chapters: list[ParsedChapter], out_path: Path):
    lines: list[str] = []
    lines.append("-- Auto-generated import for Алгебра 8-сынып (textbook_id=42)")
    lines.append("BEGIN;")
    lines.append("")

    chapter_order = 0
    for ch in chapters:
        chapter_order += 1
        ch_title = escape_sql(ch.title)
        lines.append(f"-- Chapter {ch.number}: {ch.title}")
        lines.append(
            f"INSERT INTO chapters (textbook_id, title, number, \"order\", is_deleted)"
            f" SELECT {TEXTBOOK_ID}, '{ch_title}', {ch.number}, {chapter_order}, false"
            f" WHERE NOT EXISTS ("
            f"SELECT 1 FROM chapters WHERE textbook_id={TEXTBOOK_ID} AND number={ch.number} AND is_deleted=false);"
        )
        lines.append("")

        para_order = 0
        for p in ch.paragraphs:
            para_order += 1
            p_title = escape_sql(p.title)
            html_content = md_lines_to_html(p.content_lines, TEXTBOOK_ID)
            p_content = escape_sql(html_content)
            source_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]

            lines.append(f"-- § {p.number}. {p.title[:60]}")
            lines.append(
                f"INSERT INTO paragraphs (chapter_id, title, number, \"order\", content, is_deleted)"
                f" SELECT c.id, '{p_title}', {p.number}, {para_order}, '{p_content}', false"
                f" FROM chapters c"
                f" WHERE c.textbook_id={TEXTBOOK_ID} AND c.number={ch.number} AND c.is_deleted=false"
                f" AND NOT EXISTS ("
                f"SELECT 1 FROM paragraphs p2 JOIN chapters c2 ON p2.chapter_id=c2.id"
                f" WHERE c2.textbook_id={TEXTBOOK_ID} AND p2.number={p.number} AND p2.is_deleted=false);"
            )
            lines.append(
                f"INSERT INTO paragraph_contents (paragraph_id, language, explain_text, source_hash,"
                f" status_explain, status_audio, status_slides, status_video, status_cards)"
                f" SELECT p.id, 'kk', '{p_content}', '{source_hash}',"
                f" 'ready', 'empty', 'empty', 'empty', 'empty'"
                f" FROM paragraphs p JOIN chapters c ON p.chapter_id=c.id"
                f" WHERE c.textbook_id={TEXTBOOK_ID} AND p.number={p.number} AND p.is_deleted=false"
                f" AND NOT EXISTS ("
                f"SELECT 1 FROM paragraph_contents pc WHERE pc.paragraph_id=p.id AND pc.language='kk');"
            )
            lines.append("")

    lines.append("COMMIT;")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSQL written to {out_path}")


def generate_update_sql(chapters: list[ParsedChapter], out_path: Path):
    lines: list[str] = []
    lines.append("-- Update content for Алгебра 8-сынып (textbook_id=42)")
    lines.append("BEGIN;")
    lines.append("")

    for ch in chapters:
        for p in ch.paragraphs:
            html_content = md_lines_to_html(p.content_lines, TEXTBOOK_ID)
            p_content = escape_sql(html_content)
            source_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]

            lines.append(f"-- § {p.number}. {p.title[:60]}")
            lines.append(
                f"UPDATE paragraphs SET content='{p_content}'"
                f" WHERE id IN ("
                f"SELECT p.id FROM paragraphs p JOIN chapters c ON p.chapter_id=c.id"
                f" WHERE c.textbook_id={TEXTBOOK_ID} AND p.number={p.number} AND p.is_deleted=false);"
            )
            lines.append(
                f"UPDATE paragraph_contents SET explain_text='{p_content}',"
                f" source_hash='{source_hash}'"
                f" WHERE paragraph_id IN ("
                f"SELECT p.id FROM paragraphs p JOIN chapters c ON p.chapter_id=c.id"
                f" WHERE c.textbook_id={TEXTBOOK_ID} AND p.number={p.number} AND p.is_deleted=false)"
                f" AND language='kk';"
            )
            lines.append("")

    lines.append("COMMIT;")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nUpdate SQL written to {out_path}")


# ── Exercise extraction ──────────────────────────────────────────────────────


def extract_exercises_from_paragraph(para: ParsedParagraph) -> list[ParsedExercise]:
    exercises: list[ParsedExercise] = []
    in_exercises = False
    current_difficulty = ""
    current_exercise: ParsedExercise | None = None

    for line in para.content_lines:
        stripped = line.strip()

        if RE_EXERCISES_START.match(stripped):
            in_exercises = True
            continue

        if not in_exercises:
            continue

        m_diff = RE_DIFFICULTY_HEADER.match(stripped)
        if m_diff:
            current_difficulty = m_diff.group(1)
            continue

        if not stripped:
            continue

        m_ex = RE_EXERCISE_NUM.match(stripped)
        if m_ex:
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

            if rest:
                m_sub = RE_SUB_EXERCISE.match(rest)
                if m_sub:
                    current_exercise.content_lines = []
                    current_exercise.sub_exercises.append(
                        ParsedSubExercise(number=m_sub.group(1), text=m_sub.group(2).strip())
                    )
            continue

        if current_exercise:
            m_sub = RE_SUB_EXERCISE.match(stripped)
            if m_sub:
                current_exercise.sub_exercises.append(
                    ParsedSubExercise(number=m_sub.group(1), text=m_sub.group(2).strip())
                )
            else:
                current_exercise.content_lines.append(stripped)

    if current_exercise:
        exercises.append(current_exercise)

    return exercises


def generate_exercises_sql(chapters: list[ParsedChapter], out_path: Path):
    lines: list[str] = []
    lines.append("-- Exercises for Алгебра 8-сынып (textbook_id=42)")
    lines.append("BEGIN;")
    lines.append("")

    total = 0
    sort_order = 0
    for ch in chapters:
        for p in ch.paragraphs:
            exercises = extract_exercises_from_paragraph(p)
            if not exercises:
                continue
            lines.append(f"-- § {p.number}: {len(exercises)} exercises")
            for ex in exercises:
                sort_order += 1
                content_text = " ".join(ex.content_lines).strip()
                content_escaped = escape_sql(content_text)
                sub_json = "NULL"
                if ex.sub_exercises:
                    subs = [{"n": s.number, "t": s.text} for s in ex.sub_exercises]
                    sub_json = f"'{escape_sql(json.dumps(subs, ensure_ascii=False))}'::jsonb"

                diff = ex.difficulty if ex.difficulty else "A"

                lines.append(
                    f"INSERT INTO exercises (paragraph_id, exercise_number, sort_order,"
                    f" difficulty, content_text, sub_exercises, is_starred, language, is_deleted)"
                    f" SELECT p.id, '{escape_sql(ex.exercise_number)}', {sort_order},"
                    f" '{diff}', '{content_escaped}', {sub_json},"
                    f" {'true' if ex.is_starred else 'false'}, 'kk', false"
                    f" FROM paragraphs p JOIN chapters c ON p.chapter_id=c.id"
                    f" WHERE c.textbook_id={TEXTBOOK_ID} AND p.number={p.number} AND p.is_deleted=false"
                    f" AND NOT EXISTS ("
                    f"SELECT 1 FROM exercises e WHERE e.paragraph_id=p.id"
                    f" AND e.exercise_number='{escape_sql(ex.exercise_number)}');"
                )
                total += 1
            lines.append("")

    lines.append("COMMIT;")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nExercises SQL written to {out_path} ({total} exercises)")


# ── Statistics ───────────────────────────────────────────────────────────────


def print_parse_stats(chapters: list[ParsedChapter]):
    total_paragraphs = 0
    total_lines = 0
    total_exercises = 0
    print("\n--- Parsing Results ---")
    for ch in chapters:
        ch_lines = sum(len(p.content_lines) for p in ch.paragraphs)
        total_paragraphs += len(ch.paragraphs)
        total_lines += ch_lines
        ch_title = ch.title[:70] + ("..." if len(ch.title) > 70 else "")
        print(f"  Chapter {ch.number}: {ch_title}")
        print(f"    Paragraphs: {len(ch.paragraphs)}, Content lines: {ch_lines}")
        for p in ch.paragraphs:
            ex_count = len(extract_exercises_from_paragraph(p))
            total_exercises += ex_count
            p_title = p.title[:55] + ("..." if len(p.title) > 55 else "")
            print(
                f"      §{p.number:>2}. {p_title:<58} "
                f"({len(p.content_lines):>4} lines, {ex_count} ex)"
            )
    print(
        f"\n  Total: {len(chapters)} chapters, {total_paragraphs} paragraphs, "
        f"{total_lines} content lines, {total_exercises} exercises"
    )
    print("---")


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Load Алгебра 8-сынып textbook")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Parse only, no output")
    group.add_argument("--generate-sql", type=Path, help="Generate import SQL file")
    group.add_argument("--update-content", type=Path, help="Generate update SQL file")
    group.add_argument("--exercises", type=Path, help="Generate exercises SQL file")
    args = parser.parse_args()

    print(f"Parsing {MD_FILE}...")
    chapters = parse_textbook(MD_FILE)
    print_parse_stats(chapters)

    if args.generate_sql:
        generate_sql(chapters, args.generate_sql)
    elif args.update_content:
        generate_update_sql(chapters, args.update_content)
    elif args.exercises:
        generate_exercises_sql(chapters, args.exercises)


if __name__ == "__main__":
    main()
