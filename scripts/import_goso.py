#!/usr/bin/env python3
"""
GOSO Data Import Script.

Imports GOSO (State Educational Standard) data from adilet_merged.json
into the database tables: subjects, frameworks, goso_sections,
goso_subsections, learning_outcomes.

Usage:
    cd backend
    python -m scripts.import_goso

Or from project root:
    cd scripts && python import_goso.py
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

# Add backend to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

# Load environment
from dotenv import load_dotenv
import os

env_path = BACKEND_DIR / ".env"
if env_path.exists():
    # Don't override existing env vars - allow command line overrides
    load_dotenv(env_path, override=False)


def get_database_url() -> str:
    """Build database URL from environment variables."""
    user = os.getenv("POSTGRES_USER", "ai_mentor_user")
    password = os.getenv("POSTGRES_PASSWORD", "ai_mentor_pass")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ai_mentor_db")

    # URL-encode password for special characters
    encoded_password = quote_plus(password)
    return f"postgresql://{user}:{encoded_password}@{host}:{port}/{db}"


def normalize_kz_text(text: str) -> str:
    """
    Normalize Kazakh text by removing extra spaces.

    Example: "алғашқы адамдар дың" -> "алғашқы адамдардың"
    """
    if not text:
        return text
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    # Remove spaces before punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    return text.strip()


def clean_text(text: str | None) -> str | None:
    """Clean text: return None if empty, otherwise strip whitespace."""
    if not text:
        return None
    text = text.strip()
    return text if text else None


def load_json_data(json_path: Path) -> dict:
    """Load and parse JSON file."""
    print(f"📖 Loading JSON from: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def import_subject(session, data: dict) -> int:
    """Import subject (предмет) and return its ID."""
    metadata = data['metadata']
    code = "history_kz"

    # Check if exists
    result = session.execute(
        text("SELECT id FROM subjects WHERE code = :code"),
        {"code": code}
    )
    existing = result.fetchone()

    if existing:
        print(f"  ✓ Subject '{code}' already exists (id={existing[0]})")
        return existing[0]

    # Insert new subject
    result = session.execute(
        text("""
            INSERT INTO subjects (code, name_ru, name_kz, description_ru, description_kz, grade_from, grade_to, is_active)
            VALUES (:code, :name_ru, :name_kz, :description_ru, :description_kz, :grade_from, :grade_to, true)
            RETURNING id
        """),
        {
            "code": code,
            "name_ru": metadata.get('subject_ru', 'История Казахстана'),
            "name_kz": metadata.get('subject_kz', 'Қазақстан тарихы'),
            "description_ru": metadata.get('level_ru'),
            "description_kz": metadata.get('level_kz'),
            "grade_from": min(metadata.get('grades', [5])),
            "grade_to": max(metadata.get('grades', [9])),
        }
    )
    subject_id = result.fetchone()[0]
    print(f"  ✓ Created subject '{code}' (id={subject_id})")
    return subject_id


def import_framework(session, data: dict, subject_id: int) -> int:
    """Import framework (версия ГОСО) and return its ID."""
    metadata = data['metadata']
    order = metadata.get('order', {})

    # Generate unique code
    code = f"goso_hist_kz_{order.get('date', '2022-09-16').replace('-', '_')}"

    # Check if exists
    result = session.execute(
        text("SELECT id FROM frameworks WHERE code = :code"),
        {"code": code}
    )
    existing = result.fetchone()

    if existing:
        print(f"  ✓ Framework '{code}' already exists (id={existing[0]})")
        return existing[0]

    # Parse order date
    order_date = None
    if order.get('date'):
        try:
            parts = order['date'].split('-')
            order_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            pass

    # Insert new framework
    result = session.execute(
        text("""
            INSERT INTO frameworks (
                code, subject_id, title_ru, title_kz,
                description_ru, description_kz,
                document_type, order_number, order_date, ministry, appendix_number,
                amendments, valid_from, is_active
            )
            VALUES (
                :code, :subject_id, :title_ru, :title_kz,
                :description_ru, :description_kz,
                :document_type, :order_number, :order_date, :ministry, :appendix_number,
                :amendments::json, :valid_from, true
            )
            RETURNING id
        """),
        {
            "code": code,
            "subject_id": subject_id,
            "title_ru": f"ГОСО {metadata.get('subject_ru', 'История Казахстана')} (5-9 классы)",
            "title_kz": f"МЖМБС {metadata.get('subject_kz', 'Қазақстан тарихы')} (5-9 сыныптар)",
            "description_ru": metadata.get('document_type_ru'),
            "description_kz": metadata.get('document_type_kz'),
            "document_type": metadata.get('document_type_ru', 'Типовая учебная программа'),
            "order_number": order.get('number'),
            "order_date": order_date,
            "ministry": order.get('ministry_ru') or order.get('ministry_kz'),
            "appendix_number": metadata.get('appendix_number'),
            "amendments": json.dumps(metadata.get('amendments', [])),
            "valid_from": order_date,
        }
    )
    framework_id = result.fetchone()[0]
    print(f"  ✓ Created framework '{code}' (id={framework_id})")
    return framework_id


def import_sections_and_subsections(session, data: dict, framework_id: int) -> dict:
    """
    Import goso_sections and goso_subsections.
    Returns mapping: subsection_code -> subsection_id
    """
    sections = data['content_organization']['sections']
    subsection_map = {}

    for idx, section in enumerate(sections):
        section_code = str(section['id'])

        # Check if section exists
        result = session.execute(
            text("SELECT id FROM goso_sections WHERE framework_id = :fid AND code = :code"),
            {"fid": framework_id, "code": section_code}
        )
        existing = result.fetchone()

        if existing:
            section_id = existing[0]
            print(f"  ✓ Section '{section_code}' already exists (id={section_id})")
        else:
            # Insert section
            result = session.execute(
                text("""
                    INSERT INTO goso_sections (framework_id, code, name_ru, name_kz, display_order, is_active)
                    VALUES (:framework_id, :code, :name_ru, :name_kz, :display_order, true)
                    RETURNING id
                """),
                {
                    "framework_id": framework_id,
                    "code": section_code,
                    "name_ru": section.get('name_ru', ''),
                    "name_kz": section.get('name_kz', ''),
                    "display_order": idx + 1,
                }
            )
            section_id = result.fetchone()[0]
            print(f"  ✓ Created section '{section_code}': {section.get('name_ru', '')[:40]}... (id={section_id})")

        # Import subsections
        for sub_idx, subsection in enumerate(section.get('subsections', [])):
            sub_code = str(subsection['id'])  # e.g., "1.1", "2.1"

            # Check if subsection exists
            result = session.execute(
                text("SELECT id FROM goso_subsections WHERE section_id = :sid AND code = :code"),
                {"sid": section_id, "code": sub_code}
            )
            existing_sub = result.fetchone()

            if existing_sub:
                subsection_id = existing_sub[0]
                print(f"    ✓ Subsection '{sub_code}' already exists (id={subsection_id})")
            else:
                # Insert subsection
                result = session.execute(
                    text("""
                        INSERT INTO goso_subsections (section_id, code, name_ru, name_kz, display_order, is_active)
                        VALUES (:section_id, :code, :name_ru, :name_kz, :display_order, true)
                        RETURNING id
                    """),
                    {
                        "section_id": section_id,
                        "code": sub_code,
                        "name_ru": subsection.get('name_ru', ''),
                        "name_kz": subsection.get('name_kz', ''),
                        "display_order": sub_idx + 1,
                    }
                )
                subsection_id = result.fetchone()[0]
                print(f"    ✓ Created subsection '{sub_code}': {subsection.get('name_ru', '')[:30]}... (id={subsection_id})")

            # Store mapping using section.subsection format
            # e.g., section=1, subsection=1 -> "1.1"
            subsection_map[sub_code] = subsection_id

    return subsection_map


def import_learning_outcomes(session, data: dict, framework_id: int, subsection_map: dict) -> int:
    """Import learning_outcomes (цели обучения). Returns count of imported."""
    objectives = data['learning_objectives']['all_objectives']
    imported = 0
    skipped = 0

    for idx, obj in enumerate(objectives):
        code = obj['code']  # e.g., "5.1.1.1"

        # Check if exists
        result = session.execute(
            text("SELECT id FROM learning_outcomes WHERE framework_id = :fid AND code = :code"),
            {"fid": framework_id, "code": code}
        )
        if result.fetchone():
            skipped += 1
            continue

        # Build subsection code from section.subsection
        # code "5.1.1.1" -> section=1, subsection=1 -> "1.1"
        section_num = obj.get('section')
        subsection_num = obj.get('subsection')
        subsection_code = f"{section_num}.{subsection_num}"

        subsection_id = subsection_map.get(subsection_code)
        if not subsection_id:
            print(f"    ⚠ Warning: Subsection '{subsection_code}' not found for outcome '{code}'")
            continue

        # Normalize KZ text, clean RU text
        title_kz = normalize_kz_text(obj.get('description_kz', ''))
        title_ru = clean_text(obj.get('description_ru', ''))

        # If RU is empty, use KZ as fallback for title_ru (it's required field)
        if not title_ru:
            title_ru = title_kz

        # Insert outcome
        session.execute(
            text("""
                INSERT INTO learning_outcomes (
                    framework_id, subsection_id, grade, code,
                    title_ru, title_kz, display_order, is_active
                )
                VALUES (
                    :framework_id, :subsection_id, :grade, :code,
                    :title_ru, :title_kz, :display_order, true
                )
            """),
            {
                "framework_id": framework_id,
                "subsection_id": subsection_id,
                "grade": obj.get('grade'),
                "code": code,
                "title_ru": title_ru,
                "title_kz": title_kz,
                "display_order": idx + 1,
            }
        )
        imported += 1

    return imported, skipped


def main():
    """Main import function."""
    print("=" * 60)
    print("GOSO Data Import Script")
    print("=" * 60)

    # Paths
    json_path = PROJECT_ROOT / "docs" / "adilet_merged.json"

    if not json_path.exists():
        print(f"❌ Error: JSON file not found: {json_path}")
        sys.exit(1)

    # Load data
    data = load_json_data(json_path)

    # Connect to database
    db_url = get_database_url()
    print(f"\n🔌 Connecting to database...")
    # Mask password in output
    safe_url = re.sub(r':([^:@]+)@', ':***@', db_url)
    print(f"   URL: {safe_url}")

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("\n" + "=" * 60)
        print("Step 1: Import Subject")
        print("=" * 60)
        subject_id = import_subject(session, data)

        print("\n" + "=" * 60)
        print("Step 2: Import Framework")
        print("=" * 60)
        framework_id = import_framework(session, data, subject_id)

        print("\n" + "=" * 60)
        print("Step 3: Import Sections & Subsections")
        print("=" * 60)
        subsection_map = import_sections_and_subsections(session, data, framework_id)
        print(f"\n  📊 Subsection mapping: {len(subsection_map)} subsections")

        print("\n" + "=" * 60)
        print("Step 4: Import Learning Outcomes")
        print("=" * 60)
        imported, skipped = import_learning_outcomes(session, data, framework_id, subsection_map)
        print(f"\n  📊 Outcomes: {imported} imported, {skipped} skipped (already exist)")

        # Commit all changes
        session.commit()

        print("\n" + "=" * 60)
        print("✅ Import completed successfully!")
        print("=" * 60)

        # Summary
        print("\n📊 Summary:")
        result = session.execute(text("SELECT COUNT(*) FROM subjects"))
        print(f"   Subjects: {result.scalar()}")

        result = session.execute(text("SELECT COUNT(*) FROM frameworks"))
        print(f"   Frameworks: {result.scalar()}")

        result = session.execute(text("SELECT COUNT(*) FROM goso_sections"))
        print(f"   Sections: {result.scalar()}")

        result = session.execute(text("SELECT COUNT(*) FROM goso_subsections"))
        print(f"   Subsections: {result.scalar()}")

        result = session.execute(text("SELECT COUNT(*) FROM learning_outcomes"))
        print(f"   Learning Outcomes: {result.scalar()}")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error during import: {e}")
        raise
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
