#!/usr/bin/env python3
"""
GOSO Data Import Script for Алгебра (7-9 classes), Kazakh language.
Parses the adilet-kaz.html file (53-қосымша) and imports GOSO learning objectives.
Generates SQL file, then loads via docker exec psql.
"""
import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HTML_FILE = PROJECT_ROOT / "book_parser" / "adilet-kaz.html"
SQL_FILE = Path("/tmp/goso_algebra_7_9_kz.sql")
EXTRACTED_HTML = Path("/tmp/goso_algebra_7_9_kz.html")

SUBJECT_ID = 24  # algebra
FRAMEWORK_CODE = "goso_algebra_7_9_2022_09_16"
FRAMEWORK_TITLE_KZ = 'Негізгі орта білім беру деңгейінің 7-9-сыныптарына арналған "Алгебра" оқу пәні бойынша үлгілік оқу бағдарламасы'
FRAMEWORK_TITLE_RU = FRAMEWORK_TITLE_KZ  # fallback, will be updated with RU import later
APPENDIX_NUMBER = 53

# --- SECTIONS (from lines 94-128 of extracted HTML) ---
SECTIONS = [
    {
        "code": "1",
        "name_kz": "Сандар",
        "name_ru": "Сандар",
        "subsections": [
            {"code": "1.1", "name_kz": "Сандар және шамалар туралы түсініктер", "name_ru": "Сандар және шамалар туралы түсініктер"},
            {"code": "1.2", "name_kz": "Сандарға амалдар қолдану", "name_ru": "Сандарға амалдар қолдану"},
        ]
    },
    {
        "code": "2",
        "name_kz": "Алгебра",
        "name_ru": "Алгебра",
        "subsections": [
            {"code": "2.1", "name_kz": "Алгебралық өрнектер және оларды түрлендіру", "name_ru": "Алгебралық өрнектер және оларды түрлендіру"},
            {"code": "2.2", "name_kz": "Теңдеулер және теңсіздіктер, олардың жүйелері және жиынтықтары", "name_ru": "Теңдеулер және теңсіздіктер, олардың жүйелері және жиынтықтары"},
            {"code": "2.3", "name_kz": "Тізбектер және олардың қосындысы", "name_ru": "Тізбектер және олардың қосындысы"},
            {"code": "2.4", "name_kz": "Тригонометрия", "name_ru": "Тригонометрия"},
        ]
    },
    {
        "code": "3",
        "name_kz": "Статистика және ықтималдықтар теориясы",
        "name_ru": "Статистика және ықтималдықтар теориясы",
        "subsections": [
            {"code": "3.1", "name_kz": "Комбинаторика негіздері", "name_ru": "Комбинаторика негіздері"},
            {"code": "3.2", "name_kz": "Ықтималдықтар теориясының негіздері", "name_ru": "Ықтималдықтар теориясының негіздері"},
            {"code": "3.3", "name_kz": "Статистика және деректерді талдау", "name_ru": "Статистика және деректерді талдау"},
        ]
    },
    {
        "code": "4",
        "name_kz": "Математикалық модельдеу және анализ",
        "name_ru": "Математикалық модельдеу және анализ",
        "subsections": [
            {"code": "4.1", "name_kz": "Математикалық анализ бастамалары", "name_ru": "Математикалық анализ бастамалары"},
            {"code": "4.2", "name_kz": "Математикалық модельдеудің көмегімен есептер шығару", "name_ru": "Математикалық модельдеудің көмегімен есептер шығару"},
            {"code": "4.3", "name_kz": "Математикалық тіл және математикалық модель", "name_ru": "Математикалық тіл және математикалық модель"},
        ]
    },
]

# Word-break fixes for narrow-column OCR artifacts
WORD_BREAKS = {
    "анықта масын": "анықтамасын",
    "қасиет терін": "қасиеттерін",
    "көрсет кішті": "көрсеткішті",
    "стандарт түрде": "стандарт түрде",
    "арифмети калық": "арифметикалық",
    "иррацио нал": "иррационал",
    "алгебра лық": "алгебралық",
    "квадрат тық": "квадраттық",
    "тригоно метриялық": "тригонометриялық",
    "прогрес сияларға": "прогрессияларға",
    "формула ларын": "формулаларын",
    "көбейткіш терге": "көбейткіштерге",
    "теңсіздік терді": "теңсіздіктерді",
    "функция сының": "функциясының",
    "өрнек терді": "өрнектерді",
    "бөлшек терді": "бөлшектерді",
    "түрлен діру": "түрлендіру",
    "ком бинаторика": "комбинаторика",
    "ықтимал дықтың": "ықтималдықтың",
    "статисти калық": "статистикалық",
    "модель деудің": "модельдеудің",
    "матема тикалық": "математикалық",
    "есептеу формула ларын": "есептеу формулаларын",
    "геометрия лық": "геометриялық",
    "прогрессия ның": "прогрессияның",
    "сипаттама лық": "сипаттамалық",
    "көрсету;<br>": "көрсету;",
}


def normalize_text(t: str) -> str:
    if not t:
        return t
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\s+([.,;:!?])', r'\1', t)
    return t.strip()


def clean_description(desc: str) -> str:
    # Remove trailing section headers (e.g., "2-бөлім. Алгебра")
    desc = re.sub(r'\s+\d+-бөлім\.?\s+.*$', '', desc)
    # Remove trailing subsection headers with numbering (e.g., "2. Сандарға амалдар қолдану 7.1.2. 8.")
    # This catches subsection names that leaked from adjacent table cells
    desc = re.sub(r'\s+\d+\.\s+[А-ЯӘӨҮҰҚҒІҢСс][а-яәөүұқғіңб].*$', '', desc)
    # Remove trailing grade code headers like "7.1.2. 8." or "7.3.1. 8.3.1."
    desc = re.sub(r'\s+\d\.\d\.\d\.?\s+\d\..*$', '', desc)
    # Remove trailing paragraph text like "16. Бөлімді және тақырыптарды..."
    desc = re.sub(r'\s+\d{2}\.\s+[А-ЯӘӨ].*$', '', desc)
    # Remove table headers
    desc = re.sub(r'\s+(Бөлімше|Білім алушылар|Подраздел|Обучающиеся)\b.*$', '', desc)
    # Strip trailing punctuation
    desc = desc.rstrip(';').rstrip('.').strip()
    return desc


def fix_word_breaks(text: str) -> str:
    for broken, fixed in sorted(WORD_BREAKS.items(), key=lambda x: -len(x[0])):
        text = text.replace(broken, fixed)
    return text


def parse_objectives_from_html(html_path: Path) -> dict:
    """Parse objectives from extracted HTML block."""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Find "2-параграф" section (objectives table starts there)
    idx_start = html_content.find('2-параграф')
    if idx_start == -1:
        print("ERROR: Could not find '2-параграф' in extracted HTML")
        return {}

    # End at "3-параграф" (long-term plan section — objectives listed again, avoid duplicates)
    idx_end = html_content.find('3-параграф')
    if idx_end == -1:
        idx_end = len(html_content)

    block = html_content[idx_start:idx_end]

    # Strip HTML tags, preserve line breaks
    text = block.replace('<br>', '\n').replace('<br/>', '\n')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('\u200B', '')
    text = re.sub(r'\s+', ' ', text)

    # Fix word breaks
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

        # Filter out the code example text (line 130: "7.2.1.4. кодында "7" сынып...")
        if 'кодында' in description or 'кодта' in description:
            print(f"  SKIP (code example): {code} → {description[:60]}...")
            continue

        if code not in objectives:
            objectives[code] = description

    return objectives


def generate_sql(objectives: dict) -> str:
    lines = []
    lines.append("-- GOSO Algebra 7-9 (Kazakh) Import")
    lines.append("-- Auto-generated by import_goso_algebra_7_9_kz.py")
    lines.append("BEGIN;")
    lines.append("")

    # 1. Create framework
    title_kz_escaped = FRAMEWORK_TITLE_KZ.replace("'", "''")
    lines.append(f"-- Create framework")
    lines.append(f"INSERT INTO frameworks (code, title_ru, title_kz, subject_id, appendix_number)")
    lines.append(f"VALUES ('{FRAMEWORK_CODE}', '{title_kz_escaped}', '{title_kz_escaped}', {SUBJECT_ID}, {APPENDIX_NUMBER})")
    lines.append(f"ON CONFLICT DO NOTHING;")
    lines.append("")

    # Get framework_id via subquery
    fw_subq = f"(SELECT id FROM frameworks WHERE code = '{FRAMEWORK_CODE}')"

    # 2. Create sections and subsections
    lines.append("-- Sections and subsections")
    for sec in SECTIONS:
        sec_name_kz = sec['name_kz'].replace("'", "''")
        sec_name_ru = sec['name_ru'].replace("'", "''")
        lines.append(f"INSERT INTO goso_sections (framework_id, code, name_ru, name_kz, display_order)")
        lines.append(f"VALUES ({fw_subq}, '{sec['code']}', '{sec_name_ru}', '{sec_name_kz}', {sec['code']})")
        lines.append(f"ON CONFLICT DO NOTHING;")

        for sub in sec['subsections']:
            sub_name_kz = sub['name_kz'].replace("'", "''")
            sub_name_ru = sub['name_ru'].replace("'", "''")
            sec_id_subq = f"(SELECT id FROM goso_sections WHERE framework_id = {fw_subq} AND code = '{sec['code']}')"
            parts = sub['code'].split('.')
            display_order = int(parts[1])
            lines.append(f"INSERT INTO goso_subsections (section_id, code, name_ru, name_kz, display_order)")
            lines.append(f"VALUES ({sec_id_subq}, '{sub['code']}', '{sub_name_ru}', '{sub_name_kz}', {display_order})")
            lines.append(f"ON CONFLICT DO NOTHING;")

    lines.append("")

    # 3. Create learning outcomes
    lines.append("-- Learning outcomes")
    for code in sorted(objectives.keys()):
        desc = objectives[code]
        desc_escaped = desc.replace("'", "''")
        parts = code.split('.')
        grade = int(parts[0])
        section = parts[1]
        subsection = f"{parts[1]}.{parts[2]}"

        sub_id_subq = (
            f"(SELECT gs.id FROM goso_subsections gs "
            f"JOIN goso_sections s ON gs.section_id = s.id "
            f"WHERE s.framework_id = {fw_subq} AND gs.code = '{subsection}')"
        )

        lines.append(f"INSERT INTO learning_outcomes (framework_id, subsection_id, code, grade, title_ru, title_kz)")
        lines.append(f"VALUES ({fw_subq}, {sub_id_subq}, '{code}', {grade}, '{desc_escaped}', '{desc_escaped}')")
        lines.append(f"ON CONFLICT DO NOTHING;")

    lines.append("")
    lines.append("COMMIT;")
    return "\n".join(lines)


def main():
    print(f"=== GOSO Algebra 7-9 (KZ) Import ===")
    print(f"Source: {EXTRACTED_HTML}")

    if not EXTRACTED_HTML.exists():
        print(f"ERROR: Extracted HTML not found at {EXTRACTED_HTML}")
        print(f"Run: sed -n '106724,107571p' {HTML_FILE} > {EXTRACTED_HTML}")
        return

    # Parse objectives
    print("\n1. Parsing objectives...")
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
    section_names = {"1": "Сандар", "2": "Алгебра", "3": "Статистика/Ықтималдықтар", "4": "Мат. модельдеу"}
    for sec in sorted(section_counts):
        print(f"     Section {sec} ({section_names.get(sec, '?')}): {section_counts[sec]}")

    # Generate SQL
    print("\n2. Generating SQL...")
    sql = generate_sql(objectives)
    SQL_FILE.write_text(sql, encoding='utf-8')
    print(f"   Written to {SQL_FILE} ({len(sql)} bytes)")

    # Load via docker
    print("\n3. Loading into database...")
    try:
        subprocess.run(
            ["docker", "cp", str(SQL_FILE), "ai_mentor_postgres_prod:/tmp/goso_algebra_7_9_kz.sql"],
            check=True
        )
        result = subprocess.run(
            ["docker", "exec", "ai_mentor_postgres_prod",
             "psql", "-U", "ai_mentor_user", "-d", "ai_mentor_db",
             "-f", "/tmp/goso_algebra_7_9_kz.sql"],
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
         "-c", f"SELECT grade, COUNT(*) FROM learning_outcomes lo "
               f"JOIN frameworks f ON lo.framework_id = f.id "
               f"WHERE f.code = '{FRAMEWORK_CODE}' "
               f"GROUP BY grade ORDER BY grade;"],
        capture_output=True, text=True
    )
    print(verify_result.stdout)

    print("\nDone!")


if __name__ == "__main__":
    main()
