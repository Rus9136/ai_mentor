#!/usr/bin/env python3
"""
GOSO Data Import Script for Информатика (5-9 classes).

Parses the adilet HTML file and imports GOSO learning objectives
into the database tables: frameworks, goso_sections,
goso_subsections, learning_outcomes.

Subject 'informatics' (id=31) already exists in the database.

Usage:
    cd scripts && python import_goso_informatics.py
"""
import re
import sys
from datetime import date
from pathlib import Path
from html.parser import HTMLParser

# Add backend to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

env_path = BACKEND_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path, override=False)


def get_database_url() -> str:
    user = os.getenv("POSTGRES_USER", "ai_mentor_user")
    password = os.getenv("POSTGRES_PASSWORD", "ai_mentor_pass")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ai_mentor_db")
    encoded_password = quote_plus(password)
    return f"postgresql://{user}:{encoded_password}@{host}:{port}/{db}"


def normalize_text(t: str) -> str:
    """Normalize text: collapse whitespace, remove spaces before punctuation."""
    if not t:
        return t
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\s+([.,;:!?])', r'\1', t)
    return t.strip()


# ─── Structure: Sections → Subsections ───
# Extracted manually from the HTML document structure (paragraphs 6-10)

SECTIONS = [
    {
        "code": "1",
        "name_kz": "Компьютерлік жүйелер",
        "name_ru": "Компьютерные системы",
        "subsections": [
            {"code": "1.1", "name_kz": "Компьютердің құрылғылары", "name_ru": "Устройства компьютера"},
            {"code": "1.2", "name_kz": "Программалық қамтамасыз ету", "name_ru": "Программное обеспечение"},
            {"code": "1.3", "name_kz": "Компьютерлік желілер", "name_ru": "Компьютерные сети"},
        ],
    },
    {
        "code": "2",
        "name_kz": "Ақпараттық процестер",
        "name_ru": "Информационные процессы",
        "subsections": [
            {"code": "2.1", "name_kz": "Ақпаратты ұсыну және өлшеу", "name_ru": "Представление и измерение информации"},
            {"code": "2.2", "name_kz": "Ақпараттық объектілерді құру және түрлендіру", "name_ru": "Создание и преобразование информационных объектов"},
        ],
    },
    {
        "code": "3",
        "name_kz": "Компьютерлік ойлау",
        "name_ru": "Компьютерное мышление",
        "subsections": [
            {"code": "3.1", "name_kz": "Модельдеу", "name_ru": "Моделирование"},
            {"code": "3.2", "name_kz": "Алгоритмдер", "name_ru": "Алгоритмы"},
            {"code": "3.3", "name_kz": "Программалау", "name_ru": "Программирование"},
            {"code": "3.4", "name_kz": "Робототехника", "name_ru": "Робототехника"},
        ],
    },
    {
        "code": "4",
        "name_kz": "Денсаулық және қауіпсіздік",
        "name_ru": "Здоровье и безопасность",
        "subsections": [
            {"code": "4.1", "name_kz": "Эргономика", "name_ru": "Эргономика"},
            {"code": "4.2", "name_kz": "Ақпараттық қауіпсіздік", "name_ru": "Информационная безопасность"},
        ],
    },
]


def clean_description(desc: str) -> str:
    """
    Clean parsed description by removing trailing garbage from adjacent HTML cells.

    After HTML tags are stripped, text from neighboring table cells merges together.
    Trailing patterns to remove:
    - Section headers: "2) Ақпараттық процестер", "3) Компьютерлік ойлау"
    - Subsection names: "2. Программалау", "3. Компьютерлік желілер"
    - Table headers: "Бөлімше 5-сынып 6-сынып..."
    - Paragraph numbers: "18. Тоқсандағы бөлімдер..."
    """
    # Remove trailing content starting from common boundary patterns:
    # 1. "N) Section_name" (section headers like "2) Ақпараттық процестер")
    desc = re.sub(r'\s+\d+\)\s+[А-ЯӘӨҮҰҚҒІҢБа-яәөүұқғіңб].*$', '', desc)
    # 2. "N. Subsection_name" where N is a single digit (subsection headers)
    desc = re.sub(r'\s+\d+\.\s+[А-ЯӘӨҮҰҚҒІҢБа-яәөүұқғіңб].*$', '', desc)
    # 3. "Бөлімше" (subsection table header)
    desc = re.sub(r'\s+Бөлімше\b.*$', '', desc)
    # 4. "Білім алушылар" (table header)
    desc = re.sub(r'\s+Білім алушылар\b.*$', '', desc)
    # 5. Trailing HTML artifact "һ" (found in some entries)
    desc = desc.rstrip('һ')

    # Fix OCR word-break artifacts from narrow HTML table columns
    # Words broken by <br> tags across lines
    ocr_fixes = {
        "операция лық": "операциялық",
        "интерфейсі нің": "интерфейсінің",
        "байланыс тың артықшы лықтарын": "байланыстың артықшылықтарын",
        "компьютер лік": "компьютерлік",
        "қолдана тын құжаттар мен": "қолданатын құжаттармен",
    }
    for broken, fixed in ocr_fixes.items():
        desc = desc.replace(broken, fixed)

    return desc.strip()


def parse_learning_objectives_from_html(html_path: Path) -> list[dict]:
    """
    Parse learning objectives from the HTML tables.

    The tables in section "2-параграф. Оқыту мақсаттарының жүйесі" contain
    objectives organized by section/subsection (rows) and grades (columns 5-9).

    Objectives have codes like "5.1.1.1", "6.3.2.1", etc.
    Format: grade.section.subsection.order
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    objectives = {}  # code -> description_kz (deduplicated)

    # Pattern to match objective codes with optional spaces around dots
    # Match codes like "5. 1. 1. 1", "5.1.1.1", "9. 3. 3. 10"
    code_pattern = re.compile(
        r'(\d)\s*\.\s*(\d)\s*\.\s*(\d)\s*\.\s*(\d+)'
        r'\s+'
        r'(.+?)(?=(?:\d\s*\.\s*\d\s*\.\s*\d\s*\.\s*\d+\s)|<|$)',
        re.DOTALL
    )

    # Remove HTML tags for easier parsing, but preserve line breaks from <br>
    text = html_content.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode HTML entities
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = re.sub(r'\s+', ' ', text)

    # Find all objective entries
    for m in code_pattern.finditer(text):
        grade = m.group(1)
        section = m.group(2)
        subsection = m.group(3)
        order = m.group(4)
        description = m.group(5).strip()

        code = f"{grade}.{section}.{subsection}.{order}"

        # Clean description
        description = normalize_text(description)
        description = clean_description(description)
        # Remove trailing semicolons/periods
        description = description.rstrip(';').rstrip('.').strip()

        if code not in objectives:
            objectives[code] = description

    # Convert to list of dicts
    result = []
    for code, desc in sorted(objectives.items()):
        parts = code.split('.')
        result.append({
            "code": code,
            "grade": int(parts[0]),
            "section": int(parts[1]),
            "subsection": int(parts[2]),
            "order": int(parts[3]),
            "description_kz": desc,
        })

    return result


def import_framework(session, subject_id: int) -> int:
    """Create framework for Информатика ГОСО."""
    code = "goso_informatics_2022_09_16"

    result = session.execute(
        text("SELECT id FROM frameworks WHERE code = :code"),
        {"code": code}
    )
    existing = result.fetchone()
    if existing:
        print(f"  Framework '{code}' already exists (id={existing[0]})")
        return existing[0]

    order_date = date(2022, 9, 16)

    result = session.execute(
        text("""
            INSERT INTO frameworks (
                code, subject_id, title_ru, title_kz,
                description_ru, description_kz,
                document_type, order_number, order_date, ministry,
                appendix_number, amendments, valid_from, is_active
            ) VALUES (
                :code, :subject_id, :title_ru, :title_kz,
                :description_ru, :description_kz,
                :document_type, :order_number, :order_date, :ministry,
                :appendix_number, :amendments::json, :valid_from, true
            )
            RETURNING id
        """),
        {
            "code": code,
            "subject_id": subject_id,
            "title_ru": "ГОСО Информатика (5-9 классы)",
            "title_kz": "МЖМБС Информатика (5-9 сыныптар)",
            "description_ru": "Типовая учебная программа по учебному предмету \"Информатика\" для 5-9 классов уровня основного среднего образования",
            "description_kz": "Негізгі орта білім беру деңгейінің 5-9-сыныптарына арналған \"Информатика\" оқу пәні бойынша үлгілік оқу бағдарламасы",
            "document_type": "Типовая учебная программа",
            "order_number": "399",
            "order_date": order_date,
            "ministry": "Қазақстан Республикасы Оқу-ағарту министрлігі",
            "appendix_number": "55",
            "amendments": "[]",
            "valid_from": order_date,
        }
    )
    framework_id = result.fetchone()[0]
    print(f"  Created framework '{code}' (id={framework_id})")
    return framework_id


def import_sections_and_subsections(session, framework_id: int) -> dict:
    """Import sections and subsections. Returns mapping subsection_code -> subsection_id."""
    subsection_map = {}

    for idx, section in enumerate(SECTIONS):
        section_code = section["code"]

        result = session.execute(
            text("SELECT id FROM goso_sections WHERE framework_id = :fid AND code = :code"),
            {"fid": framework_id, "code": section_code}
        )
        existing = result.fetchone()

        if existing:
            section_id = existing[0]
            print(f"  Section '{section_code}' already exists (id={section_id})")
        else:
            result = session.execute(
                text("""
                    INSERT INTO goso_sections (framework_id, code, name_ru, name_kz, display_order, is_active)
                    VALUES (:framework_id, :code, :name_ru, :name_kz, :display_order, true)
                    RETURNING id
                """),
                {
                    "framework_id": framework_id,
                    "code": section_code,
                    "name_ru": section["name_ru"],
                    "name_kz": section["name_kz"],
                    "display_order": idx + 1,
                }
            )
            section_id = result.fetchone()[0]
            print(f"  Created section '{section_code}': {section['name_kz']} (id={section_id})")

        for sub_idx, sub in enumerate(section["subsections"]):
            sub_code = sub["code"]

            result = session.execute(
                text("SELECT id FROM goso_subsections WHERE section_id = :sid AND code = :code"),
                {"sid": section_id, "code": sub_code}
            )
            existing_sub = result.fetchone()

            if existing_sub:
                subsection_id = existing_sub[0]
                print(f"    Subsection '{sub_code}' already exists (id={subsection_id})")
            else:
                result = session.execute(
                    text("""
                        INSERT INTO goso_subsections (section_id, code, name_ru, name_kz, display_order, is_active)
                        VALUES (:section_id, :code, :name_ru, :name_kz, :display_order, true)
                        RETURNING id
                    """),
                    {
                        "section_id": section_id,
                        "code": sub_code,
                        "name_ru": sub["name_ru"],
                        "name_kz": sub["name_kz"],
                        "display_order": sub_idx + 1,
                    }
                )
                subsection_id = result.fetchone()[0]
                print(f"    Created subsection '{sub_code}': {sub['name_kz']} (id={subsection_id})")

            subsection_map[sub_code] = subsection_id

    return subsection_map


def import_learning_outcomes(
    session, objectives: list[dict], framework_id: int, subsection_map: dict
) -> tuple[int, int]:
    """Import learning outcomes. Returns (imported, skipped) counts."""
    imported = 0
    skipped = 0

    for idx, obj in enumerate(objectives):
        code = obj["code"]

        # Check if already exists
        result = session.execute(
            text("SELECT id FROM learning_outcomes WHERE framework_id = :fid AND code = :code"),
            {"fid": framework_id, "code": code}
        )
        if result.fetchone():
            skipped += 1
            continue

        # Map to subsection: code "5.1.1.1" -> section=1, subsection=1 -> "1.1"
        subsection_code = f"{obj['section']}.{obj['subsection']}"
        subsection_id = subsection_map.get(subsection_code)

        if not subsection_id:
            print(f"    WARNING: Subsection '{subsection_code}' not found for outcome '{code}'")
            continue

        title_kz = obj["description_kz"]
        # Use KZ text as RU fallback (KZ-only document)
        title_ru = title_kz

        session.execute(
            text("""
                INSERT INTO learning_outcomes (
                    framework_id, subsection_id, grade, code,
                    title_ru, title_kz, display_order, is_active
                ) VALUES (
                    :framework_id, :subsection_id, :grade, :code,
                    :title_ru, :title_kz, :display_order, true
                )
            """),
            {
                "framework_id": framework_id,
                "subsection_id": subsection_id,
                "grade": obj["grade"],
                "code": code,
                "title_ru": title_ru,
                "title_kz": title_kz,
                "display_order": idx + 1,
            }
        )
        imported += 1

    return imported, skipped


def main():
    print("=" * 60)
    print("GOSO Import: Информатика (5-9 classes)")
    print("=" * 60)

    html_path = PROJECT_ROOT / "adilet (1).html"
    if not html_path.exists():
        print(f"ERROR: HTML file not found: {html_path}")
        sys.exit(1)

    # Step 1: Parse objectives from HTML
    print("\n--- Step 1: Parse HTML ---")
    objectives = parse_learning_objectives_from_html(html_path)
    print(f"  Parsed {len(objectives)} unique learning objectives")

    # Print summary by grade
    by_grade = {}
    for obj in objectives:
        g = obj["grade"]
        by_grade[g] = by_grade.get(g, 0) + 1
    for g in sorted(by_grade):
        print(f"    Grade {g}: {by_grade[g]} objectives")

    # Print all parsed objectives for verification
    print("\n  All parsed objectives:")
    for obj in objectives:
        print(f"    {obj['code']}: {obj['description_kz'][:80]}...")

    # Connect to database
    db_url = get_database_url()
    safe_url = re.sub(r':([^:@]+)@', ':***@', db_url)
    print(f"\n--- Step 2: Connect to DB ---")
    print(f"  URL: {safe_url}")

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Step 3: Get subject_id for informatics
        print("\n--- Step 3: Check Subject ---")
        result = session.execute(
            text("SELECT id FROM subjects WHERE code = 'informatics'")
        )
        row = result.fetchone()
        if not row:
            print("  ERROR: Subject 'informatics' not found!")
            sys.exit(1)
        subject_id = row[0]
        print(f"  Subject 'informatics' found (id={subject_id})")

        # Step 4: Create framework
        print("\n--- Step 4: Import Framework ---")
        framework_id = import_framework(session, subject_id)

        # Step 5: Create sections & subsections
        print("\n--- Step 5: Import Sections & Subsections ---")
        subsection_map = import_sections_and_subsections(session, framework_id)
        print(f"\n  Subsection mapping: {len(subsection_map)} subsections")

        # Step 6: Import learning outcomes
        print("\n--- Step 6: Import Learning Outcomes ---")
        imported, skipped = import_learning_outcomes(session, objectives, framework_id, subsection_map)
        print(f"\n  Outcomes: {imported} imported, {skipped} skipped (already exist)")

        # Commit
        session.commit()

        # Summary
        print("\n" + "=" * 60)
        print("Import completed!")
        print("=" * 60)

        result = session.execute(
            text("SELECT COUNT(*) FROM learning_outcomes WHERE framework_id = :fid"),
            {"fid": framework_id}
        )
        print(f"\n  Total learning outcomes for Информатика: {result.scalar()}")

        # Show by grade
        result = session.execute(
            text("""
                SELECT grade, COUNT(*)
                FROM learning_outcomes
                WHERE framework_id = :fid
                GROUP BY grade
                ORDER BY grade
            """),
            {"fid": framework_id}
        )
        for row in result:
            print(f"    Grade {row[0]}: {row[1]} outcomes")

    except Exception as e:
        session.rollback()
        print(f"\nERROR during import: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
