#!/usr/bin/env python3
"""
GOSO RU Update Script for Математика (5-6 classes).
Updates title_ru on existing framework id=5 (goso_math_5_6_2022_09_16).
Source: book_parser/adilet01.html, Приложение 52 (lines 42956-44003)
"""
import re
import sys
from pathlib import Path
from datetime import date

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

FRAMEWORK_ID = 5
FRAMEWORK_CODE = "goso_math_5_6_2022_09_16"
FRAMEWORK_TITLE_RU = 'Типовая учебная программа по учебному предмету "Математика" для 5-6 классов'

# Section name_ru mappings (code -> Russian name)
SECTION_NAMES_RU = {
    "1": "Числа",
    "2": "Алгебра",
    "3": "Геометрия",
    "4": "Статистика и теория вероятностей",
    "5": "Математическое моделирование и анализ",
}

SUBSECTION_NAMES_RU = {
    "1.1": "Понятие о числах и величинах",
    "1.2": "Операции над числами",
    "2.1": "Алгебраические выражения и преобразования",
    "2.2": "Уравнения и неравенства, их системы и совокупности",
    "2.3": "Последовательности и суммирование",
    "3.1": "Понятие о геометрических фигурах",
    "3.2": "Взаимное расположение геометрических фигур",
    "3.3": "Метрические соотношения",
    "3.4": "Векторы и преобразования",
    "4.1": "Элементы теории множеств и логики",
    "4.2": "Основы комбинаторики",
    "4.3": "Статистика и анализ данных",
    "5.1": "Решение задач с помощью математического моделирования",
    "5.2": "Математический язык и математическая модель",
}


def extract_html_block():
    """Extract the objectives table block from Приложение 52."""
    html_path = PROJECT_ROOT / "book_parser" / "adilet01.html"
    with open(html_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    start = 42956 - 1
    end = 44003
    return "".join(lines[start:end])


def parse_objectives(html_block: str) -> list[dict]:
    """Parse RU learning objectives from the HTML block."""
    idx_start = html_block.find("Параграф 2")
    idx_end = html_block.find("Параграф 3")
    if idx_start == -1:
        print("ERROR: Could not find 'Параграф 2'")
        sys.exit(1)
    if idx_end == -1:
        idx_end = len(html_block)

    table_html = html_block[idx_start:idx_end]

    # Strip HTML
    text = table_html.replace("<br>", "\n").replace("<br/>", "\n")
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("\u200B", "")
    text = re.sub(r"\s+", " ", text)

    code_pattern = re.compile(
        r"(\d{1,2})\s*\.\s*(\d)\s*\.\s*(\d)\s*\.\s*(\d+)"
        r"\s*"
        r"(.+?)(?=(?:\d{1,2}\s*\.\s*\d\s*\.\s*\d\s*\.\s*\d+\s)|$)",
        re.DOTALL,
    )

    objectives = {}
    for m in code_pattern.finditer(text):
        grade = m.group(1).strip()
        section = m.group(2).strip()
        subsection = m.group(3).strip()
        order = m.group(4).strip()
        description = m.group(5).strip()

        code = f"{grade}.{section}.{subsection}.{order}"

        if grade not in ("5", "6"):
            continue

        description = clean_description(description)

        if code not in objectives and description:
            objectives[code] = description

    result = []
    for code, desc in sorted(objectives.items()):
        parts = code.split(".")
        result.append({
            "code": code,
            "grade": int(parts[0]),
            "section": int(parts[1]),
            "subsection": int(parts[2]),
            "order": int(parts[3]),
            "description": desc,
        })
    return result


def clean_description(desc: str) -> str:
    """Clean objective description."""
    # Remove trailing paragraph numbers
    desc = re.sub(r"\s+\d{2}\.\s+[А-ЯA-Z].*$", "", desc)
    # Remove trailing section headers
    desc = re.sub(r"\s+Раздел\s+\d+\.?\s+.*$", "", desc)
    # Remove trailing subsection names
    desc = re.sub(r"\s+\d+\.\s+[А-Я][а-яА-Я\s,]+$", "", desc)
    # Remove "Подраздел" or "Обучающийся" headers
    desc = re.sub(r"\s+(Подраздел|Обучающийся|Обучающиеся)\b.*$", "", desc)
    # Remove code explanation text
    desc = re.sub(r'\s*кодировке\s+\d+\.\d+.*$', "", desc)
    # Fix common OCR word-breaks
    desc = fix_word_breaks(desc)
    # Strip trailing punctuation
    desc = desc.rstrip(";").rstrip(".").strip()
    desc = re.sub(r"\s+", " ", desc)
    return desc.strip()


# OCR word-break fixes (sorted longest first)
WORD_BREAKS = {
    "обыкновен ной": "обыкновенной",
    "десятич ной": "десятичной",
    "произве дение": "произведение",
    "координат ной": "координатной",
    "пропорцио нальными": "пропорциональными",
    "прямо- пропорциональными": "прямо пропорциональными",
    "обратно пропорцио нальными": "обратно пропорциональными",
    "рацио нального": "рационального",
    "рацио нальных": "рациональных",
    "рацио нальные": "рациональные",
    "рацио нальное": "рациональное",
    "сравни вать": "сравнивать",
    "выраже ний": "выражений",
    "выраже ния": "выражения",
    "умноже ния": "умножения",
    "много угольника": "многоугольника",
    "много угольник": "многоугольник",
    "парал лельных": "параллельных",
    "парал лелепипед": "параллелепипед",
    "параллеле пипед": "параллелепипед",
    "коорди натной": "координатной",
    "коорди натную": "координатную",
    "алгебраи ческих": "алгебраических",
    "алгебраи ческие": "алгебраические",
    "алгебраи ческое": "алгебраическое",
    "перпенди кулярных": "перпендикулярных",
    "перпенди куляр": "перпендикуляр",
    "неравен ства": "неравенства",
    "неравен ство": "неравенство",
    "неравен ствами": "неравенствами",
    "пропор ции": "пропорции",
    "пропор цию": "пропорцию",
    "пропор циональности": "пропорциональности",
    "про центов": "процентов",
    "зависи мость": "зависимость",
    "зависи мости": "зависимости",
    "транс портира": "транспортира",
    "транс портир": "транспортир",
    "стати стической": "статистической",
    "стати стические": "статистические",
    "диа граммы": "диаграммы",
    "урав нения": "уравнения",
    "урав нение": "уравнение",
    "при ближённого": "приближённого",
    "приближ Ұнного": "приближённого",
    "четыр Ұх": "четырёх",
    "четырҰх": "четырёх",
    "приближ Ұнному": "приближённому",
    "четв Ұртое": "четвёртое",
    "ЧетвҰртое": "Четвёртое",
}


def fix_word_breaks(text: str) -> str:
    """Fix OCR word-break artifacts."""
    # Fix Ұ (Kazakh letter) used instead of ё in Russian text
    text = text.replace("Ұ", "ё")
    for broken, fixed in sorted(WORD_BREAKS.items(), key=lambda x: -len(x[0])):
        text = text.replace(broken, fixed)
    return text


def escape_sql(s: str) -> str:
    return s.replace("'", "''")


def generate_update_sql(objectives: list[dict]) -> str:
    """Generate UPDATE SQL for title_ru."""
    sql_lines = []
    sql_lines.append("-- GOSO Update: Математика 5-6 title_ru (Russian)")
    sql_lines.append(f"-- Generated: {date.today()}")
    sql_lines.append(f"-- Objectives count: {len(objectives)}")
    sql_lines.append("")

    # Update framework title_ru
    sql_lines.append(f"UPDATE frameworks SET title_ru = '{escape_sql(FRAMEWORK_TITLE_RU)}' WHERE code = '{FRAMEWORK_CODE}';")
    sql_lines.append("")

    # Update section name_ru
    for sec_code, name_ru in SECTION_NAMES_RU.items():
        sql_lines.append(
            f"UPDATE goso_sections SET name_ru = '{escape_sql(name_ru)}' "
            f"WHERE framework_id = {FRAMEWORK_ID} AND code = '{sec_code}';"
        )
    sql_lines.append("")

    # Update subsection name_ru
    for sub_code, name_ru in SUBSECTION_NAMES_RU.items():
        sec_code = sub_code.split(".")[0]
        sql_lines.append(
            f"UPDATE goso_subsections SET name_ru = '{escape_sql(name_ru)}' "
            f"WHERE section_id = (SELECT id FROM goso_sections WHERE framework_id = {FRAMEWORK_ID} AND code = '{sec_code}') "
            f"AND code = '{sub_code}';"
        )
    sql_lines.append("")

    # Update learning_outcomes title_ru
    for obj in objectives:
        code = obj["code"]
        desc = escape_sql(obj["description"])
        sql_lines.append(
            f"UPDATE learning_outcomes SET title_ru = '{desc}' "
            f"WHERE framework_id = {FRAMEWORK_ID} AND code = '{code}';"
        )

    return "\n".join(sql_lines)


def main():
    print("=== GOSO Update: Математика 5-6 title_ru ===")
    print()

    print("1. Extracting HTML block (Приложение 52)...")
    html_block = extract_html_block()
    print(f"   Block size: {len(html_block)} chars")

    print("2. Parsing RU learning objectives...")
    objectives = parse_objectives(html_block)
    print(f"   Found {len(objectives)} objectives")

    grade_counts = {}
    for obj in objectives:
        g = obj["grade"]
        grade_counts[g] = grade_counts.get(g, 0) + 1
    for g in sorted(grade_counts):
        print(f"   Grade {g}: {grade_counts[g]} objectives")

    if not objectives:
        print("ERROR: No objectives found!")
        sys.exit(1)

    # Check against existing KZ codes
    print()
    print("3. Sample objectives:")
    for obj in objectives[:5]:
        print(f"   {obj['code']}: {obj['description'][:80]}...")
    print(f"   ... and {len(objectives) - 5} more")

    # Check last objectives for garbage
    print()
    print("   Last 3:")
    for obj in objectives[-3:]:
        print(f"   {obj['code']}: {obj['description'][:100]}")

    print()
    print("4. Generating UPDATE SQL...")
    sql = generate_update_sql(objectives)
    sql_path = PROJECT_ROOT / "scripts" / "update_goso_math_5_6_ru.sql"
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write(sql)
    print(f"   SQL written to: {sql_path}")

    print()
    print("5. To execute:")
    print(f"   docker cp {sql_path} ai_mentor_postgres_prod:/tmp/update_ru.sql")
    print("   docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/update_ru.sql")


if __name__ == "__main__":
    main()
