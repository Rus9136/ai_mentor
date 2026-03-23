#!/usr/bin/env python3
"""
Update title_ru for GOSO Informatics (5-9) learning outcomes.
The KZ text was imported first; this script fills in the Russian translations
from Приложение 55 of adilet01.html.
"""
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
HTML_FILE = PROJECT_ROOT / "book_parser" / "adilet01.html"

FRAMEWORK_ID = 2  # goso_informatics_2022_09_16


def parse_russian_objectives(html_path: Path) -> dict[str, str]:
    """Parse Russian objective descriptions from Приложение 55."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # First, isolate Приложение 55 block (Информатика 5-9)
    app55_start = content.find("Приложение 55")
    if app55_start == -1:
        raise ValueError("Cannot find 'Приложение 55' in HTML")

    app56_start = content.find("Приложение 56", app55_start + 100)
    if app56_start == -1:
        app56_start = len(content)

    app_block = content[app55_start:app56_start]

    # Within Приложение 55, find Параграф 2 (objectives tables)
    idx_start = app_block.find("Параграф 2. Система целей обучения")
    if idx_start == -1:
        raise ValueError("Cannot find 'Параграф 2' in Приложение 55")

    # End at Параграф 3 (long-term plan - has duplicate codes)
    idx_end = app_block.find("Параграф 3.", idx_start)
    if idx_end == -1:
        idx_end = len(app_block)

    block = app_block[idx_start:idx_end]

    # Strip HTML tags, preserve line breaks
    text = block.replace("<br>", "\n").replace("<br/>", "\n")
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("\u200B", "")  # zero-width space
    text = re.sub(r"\s+", " ", text)

    objectives = {}

    # Pattern: grade.section.subsection.order + description
    code_pattern = re.compile(
        r"(\d{1,2})\s*\.\s*(\d)\s*\.\s*(\d)\s*\.\s*(\d+)"
        r"\s*"
        r'([а-яА-Яa-zA-ZёЁ].+?)(?=(?:\d{1,2}\s*\.\s*\d\s*\.\s*\d\s*\.\s*\d+\s*[а-яА-Яa-zA-ZёЁ"])|$)',
        re.DOTALL,
    )

    for m in code_pattern.finditer(text):
        grade, section, subsection, order = (
            m.group(1),
            m.group(2),
            m.group(3),
            m.group(4),
        )
        desc = m.group(5).strip()
        code = f"{grade}.{section}.{subsection}.{order}"

        # Skip the code explanation example
        if desc.startswith('"') and "класс" in desc[:30]:
            continue

        # Clean description
        desc = clean_description(desc)

        if code not in objectives and desc:
            objectives[code] = desc

    return objectives


def clean_description(desc: str) -> str:
    """Clean extracted description text."""
    # Remove trailing paragraph numbers (18. Настоящая..., 19. Распределение...)
    desc = re.sub(r"\s+\d{2}\.\s+[А-Я].*$", "", desc)
    # Remove trailing section headers
    desc = re.sub(
        r"\s+(Компьютерные системы|Информационные процессы|Компьютерное мышление|Здоровье и безопасность)\s*$",
        "",
        desc,
    )
    # Remove table headers
    desc = re.sub(r"\s+(Подраздел|Обучающиеся должны:?)\s*$", "", desc)
    # Remove grade column headers
    desc = re.sub(r"\s+\d\s+класс\s*$", "", desc)
    # Remove trailing subsection names like "2. Программное обеспечение"
    desc = re.sub(
        r"\s+\d+\.\s*[А-ЯA-Z][а-яa-zА-ЯA-Z\s]+$", "", desc
    )
    # Fix specific OCR word-breaks
    OCR_FIXES = {
        "предвари-тельный": "предварительный",
    }
    for wrong, right in OCR_FIXES.items():
        desc = desc.replace(wrong, right)
    # Strip trailing punctuation
    desc = desc.rstrip(";").rstrip(".").strip()
    # Remove trailing whitespace artifacts
    desc = re.sub(r"\s+", " ", desc).strip()
    return desc


def generate_sql(objectives: dict[str, str]) -> str:
    """Generate UPDATE SQL statements."""
    lines = [
        "-- Update title_ru for GOSO Informatics (5-9) framework_id=2",
        "-- Source: Приложение 55, book_parser/adilet01.html",
        "BEGIN;",
        "",
    ]

    for code in sorted(objectives.keys(), key=lambda c: [int(x) for x in c.split(".")]):
        desc = objectives[code]
        # Escape single quotes for SQL
        desc_escaped = desc.replace("'", "''")
        lines.append(
            f"UPDATE learning_outcomes SET title_ru = '{desc_escaped}' "
            f"WHERE framework_id = {FRAMEWORK_ID} AND code = '{code}';"
        )

    lines.append("")
    lines.append("COMMIT;")
    lines.append("")

    # Summary
    lines.append(f"-- Total: {len(objectives)} objectives updated")
    return "\n".join(lines)


def main():
    print(f"Parsing Russian objectives from {HTML_FILE}...")
    objectives = parse_russian_objectives(HTML_FILE)
    print(f"Found {len(objectives)} objectives")

    # Show per-grade counts
    grade_counts = {}
    for code in objectives:
        grade = int(code.split(".")[0])
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
    for grade in sorted(grade_counts):
        print(f"  Grade {grade}: {grade_counts[grade]} objectives")

    # Generate SQL
    sql = generate_sql(objectives)
    sql_path = Path("/tmp/update_informatics_title_ru.sql")
    sql_path.write_text(sql, encoding="utf-8")
    print(f"\nSQL written to {sql_path}")

    # Show first few for verification
    print("\nFirst 5 objectives:")
    for i, (code, desc) in enumerate(sorted(objectives.items(), key=lambda c: [int(x) for x in c[0].split(".")])):
        if i >= 5:
            break
        print(f"  {code}: {desc}")


if __name__ == "__main__":
    main()
