#!/usr/bin/env python3
"""
GOSO Data Import Script for Русская литература (5-9 classes).
Parses Приложение 40 from adilet01.html and imports GOSO learning objectives.
"""
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# --- Configuration ---
SUBJECT_ID = 36  # russian_lit
FRAMEWORK_CODE = "goso_russian_lit_5_9_2022_09_16"
FRAMEWORK_TITLE_RU = 'Типовая учебная программа по учебному предмету "Русская литература" для 5-9 классов'
APPENDIX_NUMBER = 40

# --- Section/Subsection structure (from the document) ---
SECTIONS = [
    {
        "code": "1",
        "name_ru": "Понимание и ответы по тексту",
        "subsections": [
            {"code": "1.1", "name_ru": "Понимание терминов"},
            {"code": "1.2", "name_ru": "Понимание художественного произведения"},
            {"code": "1.3", "name_ru": "Чтение наизусть и цитирование"},
            {"code": "1.4", "name_ru": "Составление плана"},
            {"code": "1.5", "name_ru": "Пересказ"},
            {"code": "1.6", "name_ru": "Ответы на вопросы"},
        ]
    },
    {
        "code": "2",
        "name_ru": "Анализ и интерпретация текста",
        "subsections": [
            {"code": "2.1", "name_ru": "Жанр"},
            {"code": "2.2", "name_ru": "Тема и идея"},
            {"code": "2.3", "name_ru": "Композиция"},
            {"code": "2.4", "name_ru": "Анализ эпизодов"},
            {"code": "2.5", "name_ru": "Характеристика героев"},
            {"code": "2.6", "name_ru": "Художественный мир произведения в разных формах представления"},
            {"code": "2.7", "name_ru": "Отношение автора"},
            {"code": "2.8", "name_ru": "Литературные приемы и изобразительные средства"},
            {"code": "2.9", "name_ru": "Творческое письмо"},
        ]
    },
    {
        "code": "3",
        "name_ru": "Оценка и сравнительный анализ",
        "subsections": [
            {"code": "3.1", "name_ru": "Оценивание художественного произведения"},
            {"code": "3.2", "name_ru": "Сравнение художественного произведения с произведениями других видов искусства"},
            {"code": "3.3", "name_ru": "Сопоставление произведений литературы"},
            {"code": "3.4", "name_ru": "Оценивание высказываний"},
        ]
    },
]

# --- Word-break fixes for OCR artifacts ---
WORD_BREAKS = {
    "паралле лизм": "параллелизм",
    "распи сана": "расписана",
    "выразительнофрагменты": "выразительно фрагменты",
    "произведенияили": "произведения или",
    "композициипри": "композиции при",
    "развернутый ответна": "развернутый ответ на",
    "произведе-ния": "произведения",
    "драматичеком": "драматическом",
    "автобиографизми": "автобиографизм",
    "парцелляция,афоризм": "парцелляция, афоризм",
    "одноклас сников": "одноклассников",
    "тематике/ проблематике/ жанру": "тематике/проблематике/жанру",
    "тематике/ проблематике/жанру": "тематике/проблематике/жанру",
}


def fix_kazakh_yo(text: str) -> str:
    """Fix Ұ (Kazakh letter) used instead of ё in Russian text."""
    text = text.replace("своҰ", "своё")
    text = text.replace("свҰртывания", "свёртывания")
    return text


def fix_word_breaks(text: str) -> str:
    for broken, fixed in sorted(WORD_BREAKS.items(), key=lambda x: -len(x[0])):
        text = text.replace(broken, fixed)
    return text


def normalize_text(t: str) -> str:
    if not t:
        return t
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\s+([.,;:!?])', r'\1', t)
    return t.strip()


def clean_description(desc: str) -> str:
    # Remove trailing section headers
    desc = re.sub(r'\s+\d+\)\s+[а-яА-Я].*$', '', desc)
    desc = re.sub(r'\s+\d+\.\s+[А-Я][а-я].*$', '', desc)
    # Remove table headers
    desc = re.sub(r'\s+(Подраздел|Обучающиеся|Обучающийся)\b.*$', '', desc)
    # Remove trailing paragraph numbers
    desc = re.sub(r'\s+\d{2}\.\s+[А-Я].*$', '', desc)
    # Strip trailing punctuation
    desc = desc.rstrip(';').rstrip('.').strip()
    return desc


def parse_objectives_from_html(html_path: Path, start_line: int, end_line: int) -> list[dict]:
    """Parse learning objectives from the extracted HTML block."""
    with open(html_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Extract the Параграф 2 block (between start_line and end_line, 1-indexed)
    block = ''.join(lines[start_line - 1:end_line - 1])

    # Strip HTML tags, preserve line breaks
    text = block.replace('<br>', ' ').replace('<br/>', ' ')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = text.replace('\u200B', '')  # Remove zero-width spaces
    text = re.sub(r'\s+', ' ', text)

    # Fix Kazakh Ұ → ё
    text = fix_kazakh_yo(text)

    # Find all objective codes with descriptions
    # Use [\s.]+ to handle OCR artifacts like "6.1 2.1" (missing dot between section/subsection)
    code_pattern = re.compile(
        r'(\d{1,2})[\s.]+(\d)[\s.]+(\d)[\s.]+(\d+)'
        r'\s*'
        r'(.+?)(?=(?:\d{1,2}[\s.]+\d[\s.]+\d[\s.]+\d+\s)|$)',
        re.DOTALL
    )

    objectives = {}
    for m in code_pattern.finditer(text):
        grade = m.group(1).strip()
        section = m.group(2).strip()
        subsection = m.group(3).strip()
        order = m.group(4).strip()
        description = m.group(5).strip()

        code = f"{grade}.{section}.{subsection}.{order}"

        # Filter false matches (code example text)
        if 'кодировке' in description or 'нумерация' in description:
            continue
        if description.startswith('"') and 'класс' in description[:30]:
            continue

        description = normalize_text(description)
        description = fix_word_breaks(description)
        description = clean_description(description)

        if code not in objectives:
            objectives[code] = description

    result = []
    for code, desc in sorted(objectives.items()):
        parts = code.split('.')
        result.append({
            "code": code,
            "grade": int(parts[0]),
            "section": int(parts[1]),
            "subsection": int(parts[2]),
            "order": int(parts[3]),
            "description": desc,
        })
    return result


def escape_sql(text: str) -> str:
    return text.replace("'", "''")


def generate_sql(objectives: list[dict]) -> str:
    lines = []
    lines.append("BEGIN;")
    lines.append("")

    # 1. Create framework
    lines.append("-- 1. Create framework")
    lines.append(f"""INSERT INTO frameworks (subject_id, code, title_ru, title_kz, appendix_number)
VALUES ({SUBJECT_ID}, '{FRAMEWORK_CODE}', '{escape_sql(FRAMEWORK_TITLE_RU)}', '{escape_sql(FRAMEWORK_TITLE_RU)}', {APPENDIX_NUMBER})
ON CONFLICT DO NOTHING;""")
    lines.append("")

    # 2. Create sections
    lines.append("-- 2. Create sections")
    for i, section in enumerate(SECTIONS):
        lines.append(f"""INSERT INTO goso_sections (framework_id, code, name_ru, name_kz, display_order)
SELECT id, '{section['code']}', '{escape_sql(section['name_ru'])}', '{escape_sql(section['name_ru'])}', {i + 1}
FROM frameworks WHERE code = '{FRAMEWORK_CODE}'
ON CONFLICT DO NOTHING;""")
    lines.append("")

    # 3. Create subsections
    lines.append("-- 3. Create subsections")
    for section in SECTIONS:
        for j, sub in enumerate(section['subsections']):
            lines.append(f"""INSERT INTO goso_subsections (section_id, code, name_ru, name_kz, display_order)
SELECT gs.id, '{sub['code']}', '{escape_sql(sub['name_ru'])}', '{escape_sql(sub['name_ru'])}', {j + 1}
FROM goso_sections gs
JOIN frameworks f ON gs.framework_id = f.id
WHERE f.code = '{FRAMEWORK_CODE}' AND gs.code = '{section['code']}'
ON CONFLICT DO NOTHING;""")
    lines.append("")

    # 4. Create learning outcomes
    lines.append("-- 4. Create learning outcomes")
    for obj in objectives:
        sub_code = f"{obj['section']}.{obj['subsection']}"
        lines.append(f"""INSERT INTO learning_outcomes (framework_id, subsection_id, grade, code, title_ru, title_kz)
SELECT f.id, gsub.id, {obj['grade']}, '{obj['code']}',
    '{escape_sql(obj['description'])}',
    '{escape_sql(obj['description'])}'
FROM frameworks f
JOIN goso_sections gs ON gs.framework_id = f.id AND gs.code = '{obj['section']}'
JOIN goso_subsections gsub ON gsub.section_id = gs.id AND gsub.code = '{sub_code}'
WHERE f.code = '{FRAMEWORK_CODE}'
ON CONFLICT DO NOTHING;""")
    lines.append("")
    lines.append("COMMIT;")

    return '\n'.join(lines)


def main():
    html_path = PROJECT_ROOT / "book_parser" / "adilet01.html"
    if not html_path.exists():
        print(f"ERROR: HTML file not found: {html_path}")
        sys.exit(1)

    # Параграф 2 starts at line 14503+281-1=14783, ends at 14503+685-1=15187
    # But we use the extracted block directly
    print("Parsing objectives from Приложение 40...")
    objectives = parse_objectives_from_html(html_path, 14503 + 281 - 1, 14503 + 685 - 1)

    # Print summary
    grades = {}
    for obj in objectives:
        grades.setdefault(obj['grade'], []).append(obj)

    print(f"\nParsed {len(objectives)} objectives:")
    for grade in sorted(grades):
        print(f"  Grade {grade}: {len(grades[grade])} objectives")

    # Generate SQL
    sql = generate_sql(objectives)
    sql_path = PROJECT_ROOT / "scripts" / "import_goso_russian_lit_5_9.sql"
    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write(sql)
    print(f"\nSQL written to: {sql_path}")

    return sql_path


if __name__ == "__main__":
    main()
