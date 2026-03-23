#!/usr/bin/env python3
"""
GOSO Data Import Script for Русский язык (5-9 classes).
Parses Appendix 39 from book_parser/adilet01.html and imports learning objectives.

Source: Приложение 39, lines 10054-14502
Subject: russian_lang (id=33)
"""
import re
import sys
import os
from pathlib import Path
from datetime import date

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# --- SECTIONS ---
SECTIONS = [
    {
        "code": "1",
        "name_ru": "Слушание и говорение",
        "name_kz": "Слушание и говорение",
        "subsections": [
            {"code": "1.1", "name_ru": "Понимание содержания текста", "name_kz": "Понимание содержания текста"},
            {"code": "1.2", "name_ru": "Определение основной мысли", "name_kz": "Определение основной мысли"},
            {"code": "1.3", "name_ru": "Пересказывание прослушанного материала", "name_kz": "Пересказывание прослушанного материала"},
            {"code": "1.4", "name_ru": "Прогнозирование событий", "name_kz": "Прогнозирование событий"},
            {"code": "1.5", "name_ru": "Участие в диалоге", "name_kz": "Участие в диалоге"},
            {"code": "1.6", "name_ru": "Оценивание прослушанного материала", "name_kz": "Оценивание прослушанного материала"},
            {"code": "1.7", "name_ru": "Построение монологического высказывания", "name_kz": "Построение монологического высказывания"},
        ]
    },
    {
        "code": "2",
        "name_ru": "Чтение",
        "name_kz": "Чтение",
        "subsections": [
            {"code": "2.1", "name_ru": "Понимание информации", "name_kz": "Понимание информации"},
            {"code": "2.2", "name_ru": "Выявление структурных частей текста и определение основной мысли", "name_kz": "Выявление структурных частей текста и определение основной мысли"},
            {"code": "2.3", "name_ru": "Понимание применения лексических и синтаксических единиц в прочитанном тексте", "name_kz": "Понимание применения лексических и синтаксических единиц в прочитанном тексте"},
            {"code": "2.4", "name_ru": "Определение типов и стилей текстов", "name_kz": "Определение типов и стилей текстов"},
            {"code": "2.5", "name_ru": "Формулирование вопросов и оценивание", "name_kz": "Формулирование вопросов и оценивание"},
            {"code": "2.6", "name_ru": "Использование разных видов чтения", "name_kz": "Использование разных видов чтения"},
            {"code": "2.7", "name_ru": "Извлечение информации из различных источников", "name_kz": "Извлечение информации из различных источников"},
            {"code": "2.8", "name_ru": "Сравнительный анализ текстов", "name_kz": "Сравнительный анализ текстов"},
        ]
    },
    {
        "code": "3",
        "name_ru": "Письмо",
        "name_kz": "Письмо",
        "subsections": [
            {"code": "3.1", "name_ru": "Составление плана", "name_kz": "Составление плана"},
            {"code": "3.2", "name_ru": "Изложение содержания прослушанного, прочитанного и аудиовизуального материала", "name_kz": "Изложение содержания прослушанного, прочитанного и аудиовизуального материала"},
            {"code": "3.3", "name_ru": "Написание текстов с использованием различных форм представления", "name_kz": "Написание текстов с использованием различных форм представления"},
            {"code": "3.4", "name_ru": "Создание текстов различных типов и стилей", "name_kz": "Создание текстов различных типов и стилей"},
            {"code": "3.5", "name_ru": "Написание эссе", "name_kz": "Написание эссе"},
            {"code": "3.6", "name_ru": "Творческое письмо", "name_kz": "Творческое письмо"},
            {"code": "3.7", "name_ru": "Корректирование и редактирование текстов", "name_kz": "Корректирование и редактирование текстов"},
        ]
    },
    {
        "code": "4",
        "name_ru": "Соблюдение речевых норм",
        "name_kz": "Соблюдение речевых норм",
        "subsections": [
            {"code": "4.1", "name_ru": "Соблюдение орфографических норм", "name_kz": "Соблюдение орфографических норм"},
            {"code": "4.2", "name_ru": "Соблюдение лексических норм", "name_kz": "Соблюдение лексических норм"},
            {"code": "4.3", "name_ru": "Соблюдение грамматических норм", "name_kz": "Соблюдение грамматических норм"},
            {"code": "4.4", "name_ru": "Соблюдение пунктуационных норм", "name_kz": "Соблюдение пунктуационных норм"},
        ]
    },
]

# Word-break fixes from OCR narrow columns
WORD_BREAKS = {
    "интерпрети- руя": "интерпретируя",
    "несплош- ных": "несплошных",
    "содержа- ния": "содержания",
    "художествен- ного": "художественного",
    "рассужде- ние": "рассуждение",
    "эмоциональ- но": "эмоционально",
    "прочитан- ного": "прочитанного",
    "обособленнымопределени- ем": "обособленным определением",
    "пунктуационныхнорм": "пунктуационных норм",
    "орфографиические": "орфографические",
    "особенностиисполняемой": "особенности исполняемой",
    "зренияактуальности": "зрения актуальности",
    "противоречиивость": "противоречивость",
}

# Manual overrides for specific codes
MANUAL_OVERRIDES = {
    "6.3.3.13": None,  # This is actually 6.3.3.1 — OCR error, code has trailing "3"
}

# Kazakh ё fix
def fix_kazakh_yo(text):
    """Fix Ұ used instead of ё in Russian text."""
    replacements = {
        "развҰрнутый": "развёрнутый",
        "развҰрнутого": "развёрнутого",
        "развҰрнутую": "развёрнутую",
        "развҰрнутом": "развёрнутом",
        "развҰрнутым": "развёрнутым",
        "развҰрнутые": "развёрнутые",
        "развҰрнутых": "развёрнутых",
        "развҰрнут": "развёрнут",
        "четвҰртое": "четвёртое",
        "заключҰнную": "заключённую",
        "намҰк": "намёк",
        "намҰков": "намёков",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def normalize_text(t):
    if not t:
        return t
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\s+([.,;:!?])', r'\1', t)
    return t.strip()


def clean_description(desc):
    """Clean up description text."""
    # Remove trailing section headers
    desc = re.sub(r'\s+\d+\)\s+[а-яА-Я].*$', '', desc)
    # Remove trailing paragraph numbers like "23. Распределение часов..."
    desc = re.sub(r'\s+\d{2}\.\s+[А-Я].*$', '', desc)
    # Remove "Обучающиеся должны:" and similar table headers
    desc = re.sub(r'\s+(Подраздел|Обучающиеся|Обучающийся)\b.*$', '', desc)
    # Remove trailing subsection headers like "2. Определение основной мысли"
    desc = re.sub(r'\s+\d+\.\s+[А-Я][а-я].*$', '', desc)
    # Strip trailing punctuation
    desc = desc.rstrip(';').rstrip('.').strip()
    return desc


def parse_objectives(html_path):
    """Parse learning objectives from extracted HTML block."""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Find Параграф 2 (objectives) and stop at Параграф 3 (long-term plan)
    idx_start = html_content.find('Параграф 2. Система целей обучения')
    idx_end = html_content.find('Параграф 3.')
    if idx_start == -1:
        print("ERROR: Could not find 'Параграф 2'")
        sys.exit(1)
    if idx_end == -1:
        idx_end = len(html_content)

    block = html_content[idx_start:idx_end]

    # Strip HTML tags, preserve line breaks
    text = block.replace('<br>', '\n').replace('<br/>', '\n')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = text.replace('\u200B', '')  # zero-width space
    text = re.sub(r'\s+', ' ', text)

    # Fix Kazakh ё
    text = fix_kazakh_yo(text)

    # Fix word breaks
    for old, new in sorted(WORD_BREAKS.items(), key=lambda x: -len(x[0])):
        text = text.replace(old, new)

    # Parse objective codes
    code_pattern = re.compile(
        r'(\d{1,2})\s*\.\s*(\d)\s*\.\s*(\d)\s*\.\s*(\d+)'
        r'\s*'
        r'(.+?)(?=(?:\d{1,2}\s*\.\s*\d\s*\.\s*\d\s*\.\s*\d+\s)|$)',
        re.DOTALL
    )

    objectives = {}
    for m in code_pattern.finditer(text):
        grade = m.group(1)
        section = m.group(2)
        subsection = m.group(3)
        order = m.group(4)
        description = normalize_text(m.group(5).strip())

        code = f"{grade}.{section}.{subsection}.{order}"

        # Skip false matches (code examples in text)
        if 'кодировке' in description or 'нумерация учебной цели' in description:
            continue
        if description.startswith('"') and 'класс' in description[:20]:
            continue

        # Handle 6.3.3.13 OCR error → 6.3.3.1
        if code == "6.3.3.13":
            # The "3" at position 4 is actually start of "Представлять"
            code = "6.3.3.1"
            description = description.lstrip('3').strip()

        description = clean_description(description)
        description = fix_kazakh_yo(description)
        description = description.rstrip(';').rstrip('.').strip()

        # Lowercase first letter (consistency)
        if description and description[0].isupper():
            # Keep uppercase for proper starts like "Формулировать", "Корректировать", etc.
            pass

        if code not in objectives:
            objectives[code] = description

    # Build sorted result
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


def escape_sql(s):
    """Escape single quotes for SQL."""
    return s.replace("'", "''")


def generate_sql(objectives, subject_id=33):
    """Generate SQL for inserting framework, sections, subsections, and objectives."""
    lines = []
    lines.append("-- GOSO Import: Русский язык 5-9 классы")
    lines.append("-- Source: Приложение 39, book_parser/adilet01.html")
    lines.append(f"-- Generated: {date.today()}")
    lines.append("BEGIN;")
    lines.append("")

    # 1. Create framework
    fw_code = "goso_russian_lang_5_9_2022_09_16"
    fw_title = "Типовая учебная программа по учебному предмету \"Русский язык\" для 5-9 классов"
    lines.append(f"-- Framework")
    lines.append(f"INSERT INTO frameworks (subject_id, code, title_ru, title_kz, appendix_number)")
    lines.append(f"VALUES ({subject_id}, '{fw_code}', '{escape_sql(fw_title)}', '{escape_sql(fw_title)}', 39)")
    lines.append(f"ON CONFLICT (code) DO NOTHING;")
    lines.append("")

    # 2. Sections and subsections
    lines.append("-- Sections and subsections")
    for sec in SECTIONS:
        sec_code = sec["code"]
        lines.append(f"INSERT INTO goso_sections (framework_id, code, name_ru, name_kz, display_order)")
        lines.append(f"SELECT id, '{sec_code}', '{escape_sql(sec['name_ru'])}', '{escape_sql(sec['name_kz'])}', {sec_code}")
        lines.append(f"FROM frameworks WHERE code = '{fw_code}'")
        lines.append(f"ON CONFLICT DO NOTHING;")
        lines.append("")

        for sub in sec["subsections"]:
            sub_code = sub["code"]
            sub_order = int(sub_code.split('.')[1])
            lines.append(f"INSERT INTO goso_subsections (section_id, code, name_ru, name_kz, display_order)")
            lines.append(f"SELECT gs.id, '{sub_code}', '{escape_sql(sub['name_ru'])}', '{escape_sql(sub['name_kz'])}', {sub_order}")
            lines.append(f"FROM goso_sections gs")
            lines.append(f"JOIN frameworks f ON gs.framework_id = f.id")
            lines.append(f"WHERE f.code = '{fw_code}' AND gs.code = '{sec_code}'")
            lines.append(f"ON CONFLICT DO NOTHING;")
            lines.append("")

    # 3. Learning outcomes
    lines.append("-- Learning outcomes")
    for obj in objectives:
        code = obj["code"]
        grade = obj["grade"]
        desc = escape_sql(obj["description"])
        sub_code = f"{obj['section']}.{obj['subsection']}"

        lines.append(f"INSERT INTO learning_outcomes (framework_id, subsection_id, code, grade, title_ru, title_kz)")
        lines.append(f"SELECT f.id, gsub.id, '{code}', {grade}, '{desc}', '{desc}'")
        lines.append(f"FROM frameworks f")
        lines.append(f"JOIN goso_sections gs ON gs.framework_id = f.id AND gs.code = '{obj['section']}'")
        lines.append(f"JOIN goso_subsections gsub ON gsub.section_id = gs.id AND gsub.code = '{sub_code}'")
        lines.append(f"WHERE f.code = '{fw_code}'")
        lines.append(f"ON CONFLICT DO NOTHING;")
        lines.append("")

    lines.append("COMMIT;")
    return "\n".join(lines)


def main():
    html_path = PROJECT_ROOT / "book_parser" / "adilet01.html"
    if not html_path.exists():
        # Use the temp extracted file
        html_path = Path("/tmp/goso_russian_lang_5_9.html")

    print(f"Parsing objectives from: {html_path}")

    # Parse from full file - extract block first
    if "adilet01" in str(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Find Appendix 39 block
        start_marker = "Приложение 39"
        end_marker = "Приложение 40"
        idx_start = content.find(start_marker)
        idx_end = content.find(end_marker, idx_start + 1)
        if idx_start == -1 or idx_end == -1:
            print("ERROR: Could not find Appendix 39 boundaries")
            sys.exit(1)
        block = content[idx_start:idx_end]
        tmp_path = Path("/tmp/goso_russian_lang_5_9.html")
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(block)
        html_path = tmp_path

    objectives = parse_objectives(html_path)

    # Stats
    print(f"\nTotal objectives parsed: {len(objectives)}")
    by_grade = {}
    for obj in objectives:
        by_grade.setdefault(obj["grade"], []).append(obj)
    for grade in sorted(by_grade.keys()):
        print(f"  Grade {grade}: {len(by_grade[grade])} objectives")

    by_section = {}
    for obj in objectives:
        by_section.setdefault(obj["section"], []).append(obj)
    print("\nBy section:")
    sec_names = {1: "Слушание и говорение", 2: "Чтение", 3: "Письмо", 4: "Соблюдение речевых норм"}
    for sec in sorted(by_section.keys()):
        print(f"  {sec}. {sec_names.get(sec, '?')}: {len(by_section[sec])} objectives")

    # Show sample
    print("\nFirst 5 objectives:")
    for obj in objectives[:5]:
        print(f"  {obj['code']}: {obj['description'][:80]}...")

    print("\nLast 5 objectives:")
    for obj in objectives[-5:]:
        print(f"  {obj['code']}: {obj['description'][:80]}...")

    # Generate SQL
    sql = generate_sql(objectives)
    sql_path = Path("/tmp/goso_russian_lang_5_9.sql")
    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write(sql)
    print(f"\nSQL written to: {sql_path}")
    print(f"SQL size: {len(sql)} bytes, {sql.count(chr(10))} lines")

    return objectives


if __name__ == "__main__":
    main()
