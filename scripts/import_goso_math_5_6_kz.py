#!/usr/bin/env python3
"""
GOSO Data Import Script for Математика (5-6 classes), Kazakh language.
Source: book_parser/adilet-kaz.html, 52-қосымша (lines 105684-106723)
Subject: math (id=23)
"""
import re
import sys
import os
from pathlib import Path
from datetime import date

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# --- SECTIONS (extracted from 52-қосымша) ---
SECTIONS = [
    {
        "code": "1",
        "name_kz": "Сандар",
        "subsections": [
            {"code": "1.1", "name_kz": "Сандар және шамалар туралы түсініктер"},
            {"code": "1.2", "name_kz": "Сандарға амалдар қолдану"},
        ]
    },
    {
        "code": "2",
        "name_kz": "Алгебра",
        "subsections": [
            {"code": "2.1", "name_kz": "Алгебралық өрнектер және түрлендірулер"},
            {"code": "2.2", "name_kz": "Теңдеулер және теңсіздіктер, олардың жүйелері және жиынтықтары"},
            {"code": "2.3", "name_kz": "Тізбектер және қосындылау"},
        ]
    },
    {
        "code": "3",
        "name_kz": "Геометрия",
        "subsections": [
            {"code": "3.1", "name_kz": "Геометриялық фигуралар туралы түсінік"},
            {"code": "3.2", "name_kz": "Геометриялық фигуралардың өзара орналасуы"},
            {"code": "3.3", "name_kz": "Метрикалық қатыстар"},
            {"code": "3.4", "name_kz": "Векторлар және түрлендірулер"},
        ]
    },
    {
        "code": "4",
        "name_kz": "Статистика және ықтималдықтар теориясы",
        "subsections": [
            {"code": "4.1", "name_kz": "Жиындар теориясы және логика элементтері"},
            {"code": "4.2", "name_kz": "Комбинаторика негіздері"},
            {"code": "4.3", "name_kz": "Статистика және деректерді талдау"},
        ]
    },
    {
        "code": "5",
        "name_kz": "Математикалық модельдеу мен талдау",
        "subsections": [
            {"code": "5.1", "name_kz": "Математикалық модельдеудің көмегімен есептер шығару"},
            {"code": "5.2", "name_kz": "Математикалық тіл және математикалық модель"},
        ]
    },
]

FRAMEWORK_CODE = "goso_math_5_6_2022_09_16"
FRAMEWORK_TITLE_KZ = '5-6-сыныптарына арналған "Математика" оқу пәнінен үлгілік оқу бағдарламасы'
FRAMEWORK_TITLE_RU = FRAMEWORK_TITLE_KZ  # fallback — same as KZ
SUBJECT_ID = 23  # math
APPENDIX_NUMBER = "52"


def extract_html_block():
    """Extract the objectives table block from 52-қосымша."""
    html_path = PROJECT_ROOT / "book_parser" / "adilet-kaz.html"
    with open(html_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Block: lines 105684-106723 (1-indexed)
    start = 105684 - 1
    end = 106723
    block = "".join(lines[start:end])
    return block


def parse_objectives(html_block: str) -> list[dict]:
    """Parse learning objectives from the HTML block."""
    # Find the objectives table section (2-параграф to 3-параграф)
    idx_start = html_block.find("2-параграф")
    idx_end = html_block.find("3-параграф")
    if idx_start == -1:
        print("ERROR: Could not find '2-параграф' in block")
        sys.exit(1)
    if idx_end == -1:
        idx_end = len(html_block)

    table_html = html_block[idx_start:idx_end]

    # Strip HTML, preserve line breaks
    text = table_html.replace("<br>", "\n").replace("<br/>", "\n")
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("\u200B", "")
    text = re.sub(r"\s+", " ", text)

    # Pattern for codes like "5. 1. 1. 1" or "6.1.2.3" (with or without spaces)
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

        # Filter: only grades 5 and 6
        if grade not in ("5", "6"):
            continue

        # Clean description
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
    # Remove trailing paragraph numbers like "16. Тоқсандағы..." or "17. Осы оқу..."
    desc = re.sub(r"\s+\d{2}\.\s+[А-ЯӘӨҮҰҚҒІҢБТОа-яәөүұқғіңб].*$", "", desc)
    # Remove trailing section headers (бөлім markers)
    desc = re.sub(r"\s+\d+-бөлім\.?\s+.*$", "", desc)
    # Remove trailing subsection names starting with number
    desc = re.sub(r"\s+\d+\.\s+[А-ЯӘӨҮҰҚҒІҢа-яәөүұқғіңб][А-Яа-яӘӨҮҰҚҒІҢәөүұқғіңб\s,]+$", "", desc)
    # Remove trailing "Білім алушылар..." or "Бөлімше" headers
    desc = re.sub(r"\s+(Бөлімше|Білім алушылар)\b.*$", "", desc)
    # Remove code explanation text like 'кодында "6" сынып'
    desc = re.sub(r'\s*кодында\s+"?\d+"?\s+сынып.*$', "", desc)
    # Remove trailing section markers like "15. Білім алушыларға..."
    desc = re.sub(r"\s+\d+\.\s+Білім алушыларға.*$", "", desc)
    # Remove table header remnants
    desc = re.sub(r"\s+\d+\.\d+\.\s*$", "", desc)
    # Strip trailing punctuation
    desc = desc.rstrip(";").rstrip(".").strip()
    # Collapse whitespace
    desc = re.sub(r"\s+", " ", desc)
    return desc.strip()


def escape_sql(s: str) -> str:
    """Escape single quotes for SQL."""
    return s.replace("'", "''")


def generate_sql(objectives: list[dict]) -> str:
    """Generate SQL for importing framework, sections, subsections, and objectives."""
    sql_lines = []
    sql_lines.append("-- GOSO Import: Математика 5-6 (Kazakh)")
    sql_lines.append(f"-- Generated: {date.today()}")
    sql_lines.append(f"-- Objectives count: {len(objectives)}")
    sql_lines.append("")

    # 1. Create framework
    sql_lines.append("-- === Framework ===")
    sql_lines.append(f"""
INSERT INTO frameworks (subject_id, code, title_ru, title_kz, appendix_number)
VALUES ({SUBJECT_ID}, '{FRAMEWORK_CODE}', '{escape_sql(FRAMEWORK_TITLE_RU)}', '{escape_sql(FRAMEWORK_TITLE_KZ)}', {APPENDIX_NUMBER})
ON CONFLICT (code) DO NOTHING;
""")

    # 2. Create sections and subsections
    sql_lines.append("-- === Sections & Subsections ===")
    for sec in SECTIONS:
        sec_code = sec["code"]
        sec_name = escape_sql(sec["name_kz"])
        sql_lines.append(f"""
INSERT INTO goso_sections (framework_id, code, name_ru, name_kz, display_order)
SELECT f.id, '{sec_code}', '{sec_name}', '{sec_name}', {int(sec_code)}
FROM frameworks f WHERE f.code = '{FRAMEWORK_CODE}'
ON CONFLICT (framework_id, code) DO NOTHING;
""")
        for sub in sec["subsections"]:
            sub_code = sub["code"]
            sub_name = escape_sql(sub["name_kz"])
            sub_order = int(sub_code.split(".")[1])
            sql_lines.append(f"""
INSERT INTO goso_subsections (section_id, code, name_ru, name_kz, display_order)
SELECT gs.id, '{sub_code}', '{sub_name}', '{sub_name}', {sub_order}
FROM goso_sections gs
JOIN frameworks f ON gs.framework_id = f.id
WHERE f.code = '{FRAMEWORK_CODE}' AND gs.code = '{sec_code}'
ON CONFLICT (section_id, code) DO NOTHING;
""")

    # 3. Create learning outcomes
    sql_lines.append("-- === Learning Outcomes ===")
    for obj in objectives:
        code = obj["code"]
        desc = escape_sql(obj["description"])
        grade = obj["grade"]
        sub_code = f"{obj['section']}.{obj['subsection']}"
        sec_code = str(obj["section"])

        sql_lines.append(f"""
INSERT INTO learning_outcomes (framework_id, subsection_id, code, title_ru, title_kz, grade, display_order)
SELECT f.id, gsub.id, '{code}', '{desc}', '{desc}', {grade}, {obj['order']}
FROM frameworks f
JOIN goso_sections gs ON gs.framework_id = f.id AND gs.code = '{sec_code}'
JOIN goso_subsections gsub ON gsub.section_id = gs.id AND gsub.code = '{sub_code}'
WHERE f.code = '{FRAMEWORK_CODE}'
ON CONFLICT (framework_id, code) DO NOTHING;
""")

    return "\n".join(sql_lines)


def main():
    print("=== GOSO Import: Математика 5-6 (Kazakh) ===")
    print()

    # 1. Extract HTML block
    print("1. Extracting HTML block (52-қосымша)...")
    html_block = extract_html_block()
    print(f"   Block size: {len(html_block)} chars")

    # 2. Parse objectives
    print("2. Parsing learning objectives...")
    objectives = parse_objectives(html_block)
    print(f"   Found {len(objectives)} objectives")

    # Count by grade
    grade_counts = {}
    for obj in objectives:
        g = obj["grade"]
        grade_counts[g] = grade_counts.get(g, 0) + 1
    for g in sorted(grade_counts):
        print(f"   Grade {g}: {grade_counts[g]} objectives")

    # Count by section
    section_counts = {}
    for obj in objectives:
        s = obj["section"]
        section_counts[s] = section_counts.get(s, 0) + 1
    print("   By section:")
    for s in sorted(section_counts):
        sec_name = next((sec["name_kz"] for sec in SECTIONS if sec["code"] == str(s)), "?")
        print(f"     Section {s} ({sec_name}): {section_counts[s]}")

    if not objectives:
        print("ERROR: No objectives found!")
        sys.exit(1)

    # 3. Print sample
    print()
    print("3. Sample objectives:")
    for obj in objectives[:5]:
        print(f"   {obj['code']}: {obj['description'][:80]}...")
    print(f"   ... and {len(objectives) - 5} more")

    # 4. Generate SQL
    print()
    print("4. Generating SQL...")
    sql = generate_sql(objectives)
    sql_path = PROJECT_ROOT / "scripts" / "import_goso_math_5_6_kz.sql"
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write(sql)
    print(f"   SQL written to: {sql_path}")
    print(f"   SQL size: {len(sql)} chars")

    # 5. Execute SQL
    print()
    print("5. To execute, run:")
    print(f"   docker cp {sql_path} ai_mentor_postgres_prod:/tmp/import.sql")
    print("   docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/import.sql")


if __name__ == "__main__":
    main()
