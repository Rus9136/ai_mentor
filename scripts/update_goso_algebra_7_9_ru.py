#!/usr/bin/env python3
"""
GOSO Algebra 7-9 — Update title_ru from Russian source (Приложение 53).
The KZ import already created the framework (id=8) with Kazakh text in both fields.
This script parses Russian objectives and generates UPDATE SQL for title_ru/name_ru.
"""
import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HTML_FILE = PROJECT_ROOT / "book_parser" / "adilet01.html"
SQL_FILE = Path("/tmp/goso_algebra_7_9_ru_update.sql")
EXTRACTED_HTML = Path("/tmp/goso_algebra_7_9_ru.html")

FRAMEWORK_CODE = "goso_algebra_7_9_2022_09_16"
FRAMEWORK_TITLE_RU = 'Типовая учебная программа по учебному предмету "Алгебра" для 7-9 классов уровня основного среднего образования'

# Russian section names
SECTIONS_RU = {
    "1": "Числа",
    "2": "Алгебра",
    "3": "Статистика и теория вероятностей",
    "4": "Математическое моделирование и анализ",
}

# Russian subsection names
SUBSECTIONS_RU = {
    "1.1": "Понятие о числах и величинах",
    "1.2": "Операции над числами",
    "2.1": "Алгебраические выражения и их преобразования",
    "2.2": "Уравнения и неравенства, их системы и совокупности",
    "2.3": "Последовательности и их суммирование",
    "2.4": "Тригонометрия",
    "3.1": "Основы комбинаторики",
    "3.2": "Основы теории вероятностей",
    "3.3": "Статистика и анализ данных",
    "4.1": "Начала математического анализа",
    "4.2": "Решение задач с помощью математического моделирования",
    "4.3": "Математический язык и математическая модель",
}

# OCR word-break fixes for narrow-column artifacts
WORD_BREAKS = {
    "сокращҰнного": "сокращённого",
    "приближҰнные": "приближённые",
    "приближҰнных": "приближённых",
    "объҰм": "объём",
    "чҰтность": "чётность",
    "нечҰтность": "нечётность",
    "четвҰртое": "четвёртое",
    "арифмети ческий": "арифметический",
    "арифмети ческого": "арифметического",
    "алгебраи ческие": "алгебраические",
    "алгебраи ческих": "алгебраических",
    "тригоно метрических": "тригонометрических",
    "тригоно метрические": "тригонометрические",
    "комбина торики": "комбинаторики",
    "комбинато рики": "комбинаторики",
    "последо вательности": "последовательности",
    "последова тельности": "последовательности",
    "квадратич ную": "квадратичную",
    "квадратич ной": "квадратичной",
    "квадрат ного": "квадратного",
    "дробно- рациональные": "дробно-рациональные",
    "дробно-рацио нальных": "дробно-рациональных",
    "знакопо стоянства": "знакопостоянства",
    "рацио нальные": "рациональные",
    "рацио нальное": "рациональное",
    "пересе чения": "пересечения",
    "прогрес сии": "прогрессии",
    "прогрес сиями": "прогрессиями",
    "геометри ческая": "геометрическая",
    "геометри ческую": "геометрическую",
}


def normalize_text(t: str) -> str:
    if not t:
        return t
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\s+([.,;:!?])', r'\1', t)
    return t.strip()


def fix_kazakh_yo(text: str) -> str:
    """Replace Kazakh Ұ used in place of Russian ё."""
    text = text.replace("еҰ", "её")
    text = text.replace("ЕҰ", "Её")
    return text


def fix_word_breaks(text: str) -> str:
    for broken, fixed in sorted(WORD_BREAKS.items(), key=lambda x: -len(x[0])):
        text = text.replace(broken, fixed)
    return text


def clean_description(desc: str) -> str:
    # Remove trailing section headers (e.g., "Раздел 2. Алгебра")
    desc = re.sub(r'\s+Раздел\s+\d+\.?\s+.*$', '', desc)
    # Remove trailing subsection headers (e.g., "2. Уравнения и неравенства...")
    desc = re.sub(r'\s+\d+\.\s+[А-ЯЁ][а-яё].*$', '', desc)
    # Remove trailing grade code prefixes (e.g., "7.1.2. 8." or "7.3.1. 8.3.1.")
    desc = re.sub(r'\s+\d\.\d\.\d\.?\s+\d\..*$', '', desc)
    # Remove trailing paragraph text (e.g., "16. Количество часов...")
    desc = re.sub(r'\s+\d{2}\.\s+[А-ЯЁ].*$', '', desc)
    # Remove table headers
    desc = re.sub(r'\s+(Подраздел|Обучающиеся|Обучающийся)\b.*$', '', desc)
    # Strip trailing punctuation
    desc = desc.rstrip(';').rstrip('.').strip()
    return desc


def parse_objectives_from_html(html_path: Path) -> dict:
    """Parse Russian objectives from extracted HTML block."""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Find "Параграф 2" section (objectives table)
    idx_start = html_content.find('Параграф 2')
    if idx_start == -1:
        print("ERROR: Could not find 'Параграф 2' in extracted HTML")
        return {}

    # End at "Параграф 3" (long-term plan — avoid duplicates)
    idx_end = html_content.find('Параграф 3')
    if idx_end == -1:
        idx_end = len(html_content)

    block = html_content[idx_start:idx_end]

    # Strip HTML tags, preserve line breaks
    text = block.replace('<br>', '\n').replace('<br/>', '\n')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('\u200B', '')
    text = re.sub(r'\s+', ' ', text)

    # Fix Ұ→ё and word breaks
    text = fix_kazakh_yo(text)
    text = fix_word_breaks(text)

    objectives = {}

    # Pattern: grade.section.subsection.order + description
    code_pattern = re.compile(
        r'(\d{1,2})\s*\.\s*(\d)\s*\.\s*(\d)\s*\.\s*(\d+)'
        r'\s*'
        r'(.+?)(?=(?:\d{1,2}\s*\.\s*\d\s*\.\s*\d\s*\.\s*\d+\s)|$)',
        re.DOTALL
    )

    for m in code_pattern.finditer(text):
        grade, section, subsection, order = m.group(1), m.group(2), m.group(3), m.group(4)
        description = normalize_text(m.group(5).strip())
        description = clean_description(description)
        code = f"{grade}.{section}.{subsection}.{order}"

        # Filter code example text
        if 'кодировке' in description or 'кодировка' in description:
            print(f"  SKIP (code example): {code} → {description[:60]}...")
            continue

        if code not in objectives:
            objectives[code] = description

    return objectives


def generate_update_sql(objectives: dict) -> str:
    lines = []
    lines.append("-- GOSO Algebra 7-9 — UPDATE title_ru from Russian source")
    lines.append("-- Auto-generated by update_goso_algebra_7_9_ru.py")
    lines.append("BEGIN;")
    lines.append("")

    fw_subq = f"(SELECT id FROM frameworks WHERE code = '{FRAMEWORK_CODE}')"

    # 1. Update framework title_ru
    title_escaped = FRAMEWORK_TITLE_RU.replace("'", "''")
    lines.append("-- Update framework title_ru")
    lines.append(f"UPDATE frameworks SET title_ru = '{title_escaped}' WHERE code = '{FRAMEWORK_CODE}';")
    lines.append("")

    # 2. Update section name_ru
    lines.append("-- Update section name_ru")
    for code, name_ru in SECTIONS_RU.items():
        name_escaped = name_ru.replace("'", "''")
        lines.append(f"UPDATE goso_sections SET name_ru = '{name_escaped}' WHERE framework_id = {fw_subq} AND code = '{code}';")
    lines.append("")

    # 3. Update subsection name_ru
    lines.append("-- Update subsection name_ru")
    for code, name_ru in SUBSECTIONS_RU.items():
        name_escaped = name_ru.replace("'", "''")
        sec_code = code.split('.')[0]
        sec_id_subq = f"(SELECT id FROM goso_sections WHERE framework_id = {fw_subq} AND code = '{sec_code}')"
        lines.append(f"UPDATE goso_subsections SET name_ru = '{name_escaped}' WHERE section_id = {sec_id_subq} AND code = '{code}';")
    lines.append("")

    # 4. Update learning outcomes title_ru
    lines.append("-- Update learning outcomes title_ru")
    for code in sorted(objectives.keys()):
        desc = objectives[code]
        desc_escaped = desc.replace("'", "''")
        lines.append(f"UPDATE learning_outcomes SET title_ru = '{desc_escaped}' WHERE framework_id = {fw_subq} AND code = '{code}';")

    lines.append("")
    lines.append("COMMIT;")
    return "\n".join(lines)


def main():
    print("=== GOSO Algebra 7-9 — UPDATE title_ru ===")
    print(f"Source: {EXTRACTED_HTML}")

    if not EXTRACTED_HTML.exists():
        print(f"ERROR: Extracted HTML not found at {EXTRACTED_HTML}")
        print(f"Run: sed -n '44004,44851p' {HTML_FILE} > {EXTRACTED_HTML}")
        return

    # Parse objectives
    print("\n1. Parsing Russian objectives...")
    objectives = parse_objectives_from_html(EXTRACTED_HTML)
    print(f"   Found {len(objectives)} objectives")

    # Count by grade
    grade_counts = {}
    for code in objectives:
        grade = int(code.split('.')[0])
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
    for grade in sorted(grade_counts):
        print(f"   Grade {grade}: {grade_counts[grade]} objectives")

    # Count by section
    section_counts = {}
    for code in objectives:
        parts = code.split('.')
        sec = parts[1]
        section_counts[sec] = section_counts.get(sec, 0) + 1
    print(f"\n   By section:")
    section_names = {"1": "Числа", "2": "Алгебра", "3": "Стат./Вероятности", "4": "Мат. моделирование"}
    for sec in sorted(section_counts):
        print(f"     Section {sec} ({section_names.get(sec, '?')}): {section_counts[sec]}")

    # Generate SQL
    print("\n2. Generating UPDATE SQL...")
    sql = generate_update_sql(objectives)
    SQL_FILE.write_text(sql, encoding='utf-8')
    print(f"   Written to {SQL_FILE} ({len(sql)} bytes)")

    # Load via docker
    print("\n3. Loading into database...")
    try:
        subprocess.run(
            ["docker", "cp", str(SQL_FILE), "ai_mentor_postgres_prod:/tmp/goso_algebra_7_9_ru_update.sql"],
            check=True
        )
        result = subprocess.run(
            ["docker", "exec", "ai_mentor_postgres_prod",
             "psql", "-U", "ai_mentor_user", "-d", "ai_mentor_db",
             "-f", "/tmp/goso_algebra_7_9_ru_update.sql"],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        if result.returncode != 0:
            print(f"ERROR: psql returned {result.returncode}")
            return
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}")
        return

    # Verify
    print("\n4. Verifying...")
    verify_result = subprocess.run(
        ["docker", "exec", "ai_mentor_postgres_prod",
         "psql", "-U", "ai_mentor_user", "-d", "ai_mentor_db",
         "-c", f"SELECT code, LEFT(title_ru, 60) as title_ru_preview FROM learning_outcomes "
               f"WHERE framework_id = (SELECT id FROM frameworks WHERE code = '{FRAMEWORK_CODE}') "
               f"ORDER BY code LIMIT 15;"],
        capture_output=True, text=True
    )
    print(verify_result.stdout)

    print("\nDone!")


if __name__ == "__main__":
    main()
