#!/usr/bin/env python3
"""
GOSO Data Import Script for Биология (7-9 classes).

Parses the adilet HTML file (Приложение 59) and imports GOSO learning objectives
into the database tables: frameworks, goso_sections, goso_subsections, learning_outcomes.

Subject 'biology' (id=28) already exists in the database.

Usage:
    cd /home/rus/projects/ai_mentor
    POSTGRES_PORT=5435 python scripts/import_goso_biology_7_9.py
"""
import re
import sys
import os
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

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


# ─── Structure: Sections → Subsections ───
# Extracted from Приложение 59, Глава 2, пункты 7-11

SECTIONS = [
    {
        "code": "1",
        "name_ru": "Многообразие, структура и функции живых организмов",
        "name_kz": "Тірі организмдердің алуан түрлілігі, құрылысы және функциялары",
        "subsections": [
            {"code": "1.1", "name_ru": "Разнообразие живых организмов", "name_kz": "Тірі организмдердің алуан түрлілігі"},
            {"code": "1.2", "name_ru": "Питание", "name_kz": "Қоректену"},
            {"code": "1.3", "name_ru": "Транспорт веществ", "name_kz": "Заттар тасымалдау"},
            {"code": "1.4", "name_ru": "Дыхание", "name_kz": "Тыныс алу"},
            {"code": "1.5", "name_ru": "Выделение", "name_kz": "Бөліп шығару"},
            {"code": "1.6", "name_ru": "Движение", "name_kz": "Қозғалыс"},
            {"code": "1.7", "name_ru": "Координация и регуляция", "name_kz": "Координация және реттелу"},
        ],
    },
    {
        "code": "2",
        "name_ru": "Размножение, наследственность, изменчивость, эволюционное развитие",
        "name_kz": "Көбею, тұқым қуалаушылық, өзгергіштік, эволюциялық даму",
        "subsections": [
            {"code": "2.1", "name_ru": "Размножение", "name_kz": "Көбею"},
            {"code": "2.2", "name_ru": "Клеточный цикл", "name_kz": "Жасуша циклі"},
            {"code": "2.3", "name_ru": "Рост и развитие", "name_kz": "Өсу және даму"},
            {"code": "2.4", "name_ru": "Закономерности наследственности и изменчивости", "name_kz": "Тұқым қуалаушылық және өзгергіштік заңдылықтары"},
            {"code": "2.5", "name_ru": "Основы селекции и эволюционное развитие", "name_kz": "Селекция негіздері және эволюциялық даму"},
        ],
    },
    {
        "code": "3",
        "name_ru": "Организмы и окружающая среда",
        "name_kz": "Организмдер және қоршаған орта",
        "subsections": [
            {"code": "3.1", "name_ru": "Биосфера, экосистема, популяция", "name_kz": "Биосфера, экожүйе, популяция"},
            {"code": "3.2", "name_ru": "Влияние человеческой деятельности на окружающую среду", "name_kz": "Адам қызметінің қоршаған ортаға әсері"},
        ],
    },
    {
        "code": "4",
        "name_ru": "Прикладные интегрированные науки",
        "name_kz": "Қолданбалы кіріктірілген ғылымдар",
        "subsections": [
            {"code": "4.1", "name_ru": "Молекулярная биология и биохимия", "name_kz": "Молекулалық биология және биохимия"},
            {"code": "4.2", "name_ru": "Клеточная биология", "name_kz": "Жасуша биологиясы"},
            {"code": "4.3", "name_ru": "Микробиология и биотехнология", "name_kz": "Микробиология және биотехнология"},
            {"code": "4.4", "name_ru": "Биофизика", "name_kz": "Биофизика"},
        ],
    },
]


def normalize_text(t: str) -> str:
    """Normalize text: collapse whitespace, remove spaces before punctuation."""
    if not t:
        return t
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\s+([.,;:!?])', r'\1', t)
    return t.strip()


def clean_description(desc: str) -> str:
    """Clean parsed description by removing trailing garbage."""
    # Remove trailing section headers
    desc = re.sub(r'\s+\d+\)\s+[А-ЯA-Z].*$', '', desc)
    # Remove trailing subsection names
    desc = re.sub(r'\s+\d+\.\s+[А-ЯA-Z].*$', '', desc)
    # Remove table headers
    desc = re.sub(r'\s+(Подраздел|Бөлімше|Обучающиеся|Обучающийся|Білім алушылар)\b.*$', '', desc)
    # Remove trailing "Размножение, наследственность..." (section name leak)
    desc = re.sub(r'\s+Размножение, наследственность.*$', '', desc)
    desc = re.sub(r'\s+Организмы и окружающая среда.*$', '', desc)
    desc = re.sub(r'\s+Прикладные интегрированные.*$', '', desc)
    desc = re.sub(r'\s+Многообразие, структура.*$', '', desc)
    # Strip trailing punctuation
    desc = desc.rstrip(';').rstrip('.').strip()
    # Remove leading dash/hyphen artifacts
    desc = re.sub(r'^[-–—]\s*', '', desc)
    return desc.strip()


def parse_learning_objectives_from_html(html_path: Path) -> list[dict]:
    """Parse learning objectives from the extracted HTML block."""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    objectives = {}

    # Strip HTML tags, preserve line breaks from <br>
    txt = html_content.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
    txt = re.sub(r'<[^>]+>', ' ', txt)
    txt = txt.replace('&nbsp;', ' ').replace('&amp;', '&')
    # Remove zero-width spaces
    txt = txt.replace('\u200B', '')
    txt = re.sub(r'\s+', ' ', txt)

    # Pattern: grade.section.subsection.order + description
    code_pattern = re.compile(
        r'(\d{1,2})\s*\.\s*(\d)\s*\.\s*(\d)\s*\.\s*(\d+)'
        r'\s+'
        r'(.+?)(?=(?:\d{1,2}\s*\.\s*\d\s*\.\s*\d\s*\.\s*\d+\s)|$)',
        re.DOTALL
    )

    for m in code_pattern.finditer(txt):
        grade = m.group(1)
        section = m.group(2)
        subsection = m.group(3)
        order = m.group(4)
        description = m.group(5).strip()

        code = f"{grade}.{section}.{subsection}.{order}"
        grade_int = int(grade)

        # Only grades 7-9
        if grade_int < 7 or grade_int > 9:
            continue

        description = normalize_text(description)
        description = clean_description(description)
        description = description.rstrip(';').rstrip('.').strip()

        if code not in objectives and description:
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
            "description_ru": desc,
        })

    return result


def import_framework(session, subject_id: int) -> int:
    """Create framework for Biology ГОСО 7-9."""
    code = "goso_biology_7_9_2022_09_16"

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
            "title_ru": "ГОСО Биология (7-9 классы)",
            "title_kz": "МЖМБС Биология (7-9 сыныптар)",
            "description_ru": 'Типовая учебная программа по учебному предмету "Биология" для 7-9 классов уровня основного среднего образования',
            "description_kz": 'Негізгі орта білім беру деңгейінің 7-9-сыныптарына арналған "Биология" оқу пәні бойынша үлгілік оқу бағдарламасы',
            "document_type": "Типовая учебная программа",
            "order_number": "399",
            "order_date": order_date,
            "ministry": "Министерство просвещения Республики Казахстан",
            "appendix_number": "59",
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
            print(f"  Created section '{section_code}': {section['name_ru'][:50]}... (id={section_id})")

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
                print(f"    Created subsection '{sub_code}': {sub['name_ru']} (id={subsection_id})")

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

        result = session.execute(
            text("SELECT id FROM learning_outcomes WHERE framework_id = :fid AND code = :code"),
            {"fid": framework_id, "code": code}
        )
        if result.fetchone():
            skipped += 1
            continue

        subsection_code = f"{obj['section']}.{obj['subsection']}"
        subsection_id = subsection_map.get(subsection_code)

        if not subsection_id:
            print(f"    WARNING: Subsection '{subsection_code}' not found for outcome '{code}'")
            continue

        title_ru = obj["description_ru"]

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
                "title_kz": title_ru,  # Russian text as fallback for KZ
                "display_order": idx + 1,
            }
        )
        imported += 1

    return imported, skipped


def main():
    print("=" * 60)
    print("GOSO Import: Биология (7-9 classes)")
    print("=" * 60)

    html_path = Path("/tmp/goso_block_biology_7_9.html")
    if not html_path.exists():
        print(f"ERROR: HTML file not found: {html_path}")
        sys.exit(1)

    # Step 1: Parse objectives from HTML
    print("\n--- Step 1: Parse HTML ---")
    objectives = parse_learning_objectives_from_html(html_path)
    print(f"  Parsed {len(objectives)} unique learning objectives")

    by_grade = {}
    for obj in objectives:
        g = obj["grade"]
        by_grade[g] = by_grade.get(g, 0) + 1
    for g in sorted(by_grade):
        print(f"    Grade {g}: {by_grade[g]} objectives")

    # Print all parsed objectives for verification
    print("\n  All parsed objectives:")
    for obj in objectives:
        desc_preview = obj['description_ru'][:80]
        print(f"    {obj['code']}: {desc_preview}...")

    # Connect to database
    db_url = get_database_url()
    safe_url = re.sub(r':([^:@]+)@', ':***@', db_url)
    print(f"\n--- Step 2: Connect to DB ---")
    print(f"  URL: {safe_url}")

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Step 3: Get subject_id for biology
        print("\n--- Step 3: Check Subject ---")
        result = session.execute(
            text("SELECT id FROM subjects WHERE code = 'biology'")
        )
        row = result.fetchone()
        if not row:
            print("  ERROR: Subject 'biology' not found!")
            sys.exit(1)
        subject_id = row[0]
        print(f"  Subject 'biology' found (id={subject_id})")

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
        print(f"\n  Total learning outcomes for Биология 7-9: {result.scalar()}")

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
