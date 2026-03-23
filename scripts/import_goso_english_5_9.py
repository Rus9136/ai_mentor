#!/usr/bin/env python3
"""
GOSO Data Import Script for English Language (5-9 classes).
Parses Приложение 49 from adilet01.html and imports GOSO learning objectives.

Usage:
    cd /home/rus/projects/ai_mentor
    source .venv/bin/activate
    python scripts/import_goso_english_5_9.py
"""
import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HTML_FILE = PROJECT_ROOT / "book_parser" / "adilet01.html"

# --- Constants ---
SUBJECT_ID = 34  # english_lang
FRAMEWORK_CODE = "goso_english_5_9_2022_09_16"
APPENDIX_NUMBER = 49
FRAMEWORK_TITLE_RU = 'ГОСО Английский язык (5-9 классы)'
FRAMEWORK_TITLE_KZ = 'МЖБС Ағылшын тілі (5-9 сыныптар)'

# Block boundaries in adilet01.html
BLOCK_START = 39635
BLOCK_END = 42955

# --- Sections and Subsections ---
SECTIONS = [
    {
        "code": "1",
        "name_ru": "Содержание (Content)",
        "name_kz": "Мазмұн (Content)",
        "subsections": [
            {"code": "1.1", "name_ru": "Совместное решение проблем", "name_kz": "Мәселелерді бірлесіп шешу"},
            {"code": "1.2", "name_ru": "Обеспечение обратной связи", "name_kz": "Кері байланыс беру"},
            {"code": "1.3", "name_ru": "Уважение различных точек зрения", "name_kz": "Түрлі көзқарастарды құрметтеу"},
            {"code": "1.4", "name_ru": "Реагирование на обратную связь", "name_kz": "Кері байланысқа жауап беру"},
            {"code": "1.5", "name_ru": "Постановка целей обучения", "name_kz": "Оқу мақсаттарын қою"},
            {"code": "1.6", "name_ru": "Организация и представление информации", "name_kz": "Ақпаратты ұйымдастыру және ұсыну"},
            {"code": "1.7", "name_ru": "Аргументация в устной и письменной речи", "name_kz": "Ауызша және жазбаша дәлелдеу"},
            {"code": "1.8", "name_ru": "Межкультурное понимание", "name_kz": "Мәдениетаралық түсінік"},
            {"code": "1.9", "name_ru": "Выражение мыслей и чувств", "name_kz": "Ойлар мен сезімдерді білдіру"},
            {"code": "1.10", "name_ru": "Анализ мнений и взглядов", "name_kz": "Пікірлер мен көзқарастарды талдау"},
        ]
    },
    {
        "code": "2",
        "name_ru": "Аудирование (Listening)",
        "name_kz": "Тыңдалым (Listening)",
        "subsections": [
            {"code": "2.1", "name_ru": "Понимание основных моментов беседы", "name_kz": "Әңгіменің негізгі тұстарын түсіну"},
            {"code": "2.2", "name_ru": "Понимание специфичной информации", "name_kz": "Нақты ақпаратты түсіну"},
            {"code": "2.3", "name_ru": "Понимание деталей аргументов", "name_kz": "Дәлелдер бөлшектерін түсіну"},
            {"code": "2.4", "name_ru": "Понимание подразумеваемого смысла", "name_kz": "Тұспалды мағынаны түсіну"},
            {"code": "2.5", "name_ru": "Определение мнения говорящего", "name_kz": "Сөйлеушінің пікірін анықтау"},
            {"code": "2.6", "name_ru": "Определение смысла из контекста", "name_kz": "Контекстен мағынаны анықтау"},
            {"code": "2.7", "name_ru": "Характерные черты устных жанров", "name_kz": "Ауызша жанрлардың сипаттамалары"},
            {"code": "2.8", "name_ru": "Понимание рассказов и повествований", "name_kz": "Әңгімелер мен баяндауларды түсіну"},
        ]
    },
    {
        "code": "3",
        "name_ru": "Говорение (Speaking)",
        "name_kz": "Айтылым (Speaking)",
        "subsections": [
            {"code": "3.1", "name_ru": "Использование регистров речи", "name_kz": "Сөйлеу регистрлерін қолдану"},
            {"code": "3.2", "name_ru": "Формулирование вопросов", "name_kz": "Сұрақтар құрастыру"},
            {"code": "3.3", "name_ru": "Выражение мнения", "name_kz": "Пікір білдіру"},
            {"code": "3.4", "name_ru": "Реагирование на неожиданные комментарии", "name_kz": "Күтпеген пікірлерге жауап беру"},
            {"code": "3.5", "name_ru": "Взаимодействие с одноклассниками", "name_kz": "Сыныптастармен өзара әрекеттесу"},
            {"code": "3.6", "name_ru": "Изложение мыслей при групповой работе", "name_kz": "Топтық жұмыс кезінде ойларды баяндау"},
            {"code": "3.7", "name_ru": "Специфичная лексика и синтаксис", "name_kz": "Арнайы лексика мен синтаксис"},
            {"code": "3.8", "name_ru": "Пересказ историй и событий", "name_kz": "Оқиғалар мен әңгімелерді қайта баяндау"},
        ]
    },
    {
        "code": "4",
        "name_ru": "Чтение (Reading)",
        "name_kz": "Оқылым (Reading)",
        "subsections": [
            {"code": "4.1", "name_ru": "Понимание основных моментов текста", "name_kz": "Мәтіннің негізгі тұстарын түсіну"},
            {"code": "4.2", "name_ru": "Понимание специфичной информации", "name_kz": "Нақты ақпаратты түсіну"},
            {"code": "4.3", "name_ru": "Понимание деталей аргументов", "name_kz": "Дәлелдер бөлшектерін түсіну"},
            {"code": "4.4", "name_ru": "Чтение художественной и нехудожественной литературы", "name_kz": "Көркем және көркем емес әдебиетті оқу"},
            {"code": "4.5", "name_ru": "Определение смысла из контекста", "name_kz": "Контекстен мағынаны анықтау"},
            {"code": "4.6", "name_ru": "Определение отношения/мнения автора", "name_kz": "Автордың көзқарасын/пікірін анықтау"},
            {"code": "4.7", "name_ru": "Характерные свойства написанных жанров", "name_kz": "Жазбаша жанрлардың сипаттамалары"},
            {"code": "4.8", "name_ru": "Использование бумажных и цифровых ресурсов", "name_kz": "Қағаз және цифрлық ресурстарды пайдалану"},
            {"code": "4.9", "name_ru": "Различение фактов и мнений", "name_kz": "Фактілер мен пікірлерді ажырату"},
        ]
    },
    {
        "code": "5",
        "name_ru": "Письмо (Writing)",
        "name_kz": "Жазылым (Writing)",
        "subsections": [
            {"code": "5.1", "name_ru": "Планирование, написание и редактирование текстов", "name_kz": "Мәтіндерді жоспарлау, жазу және өңдеу"},
            {"code": "5.2", "name_ru": "Описание событий из прошлого", "name_kz": "Өткен оқиғаларды сипаттау"},
            {"code": "5.3", "name_ru": "Грамматическая грамотность", "name_kz": "Грамматикалық сауаттылық"},
            {"code": "5.4", "name_ru": "Стиль и регистр", "name_kz": "Стиль мен регистр"},
            {"code": "5.5", "name_ru": "Аргументация с примерами", "name_kz": "Мысалдармен дәлелдеу"},
            {"code": "5.6", "name_ru": "Логическое объединение предложений", "name_kz": "Сөйлемдерді логикалық біріктіру"},
            {"code": "5.7", "name_ru": "Формат письменных жанров", "name_kz": "Жазбаша жанрлардың форматы"},
            {"code": "5.8", "name_ru": "Правописание", "name_kz": "Емле"},
            {"code": "5.9", "name_ru": "Пунктуация", "name_kz": "Тыныс белгілері"},
        ]
    },
    {
        "code": "6",
        "name_ru": "Использование английского языка (Use of English)",
        "name_kz": "Ағылшын тілін қолдану (Use of English)",
        "subsections": [
            {"code": "6.1", "name_ru": "Существительные и именные фразы", "name_kz": "Зат есімдер мен есімді тіркестер"},
            {"code": "6.2", "name_ru": "Количественные определители", "name_kz": "Сандық анықтауыштар"},
            {"code": "6.3", "name_ru": "Прилагательные и степени сравнения", "name_kz": "Сын есімдер мен шырайлар"},
            {"code": "6.4", "name_ru": "Указательные и определяющие слова", "name_kz": "Сілтеу және анықтау сөздері"},
            {"code": "6.5", "name_ru": "Вопросительные формы", "name_kz": "Сұраулық формалар"},
            {"code": "6.6", "name_ru": "Местоимения", "name_kz": "Есімдіктер"},
            {"code": "6.7", "name_ru": "Совершенные формы глаголов", "name_kz": "Етістіктің Perfect формалары"},
            {"code": "6.8", "name_ru": "Формы будущего времени", "name_kz": "Келер шақ формалары"},
            {"code": "6.9", "name_ru": "Настоящее и прошедшее время", "name_kz": "Осы және өткен шақ"},
            {"code": "6.10", "name_ru": "Продолжительные формы времени", "name_kz": "Continuous шақ формалары"},
            {"code": "6.11", "name_ru": "Безличные структуры и косвенная речь", "name_kz": "Жеке емес құрылымдар мен төлеу сөз"},
            {"code": "6.12", "name_ru": "Наречия", "name_kz": "Үстеулер"},
            {"code": "6.13", "name_ru": "Модальные глаголы", "name_kz": "Модальді етістіктер"},
            {"code": "6.14", "name_ru": "Предлоги", "name_kz": "Предлогтар"},
            {"code": "6.15", "name_ru": "Инфинитив, герундий и фразовые глаголы", "name_kz": "Инфинитив, герундий және фразалық етістіктер"},
            {"code": "6.16", "name_ru": "Союзы", "name_kz": "Жалғаулықтар"},
            {"code": "6.17", "name_ru": "Придаточные предложения", "name_kz": "Бағыныңқы сөйлемдер"},
        ]
    },
]


def normalize_text(t: str) -> str:
    """Clean up OCR word-break artifacts and extra whitespace."""
    if not t:
        return t
    # Fix OCR word breaks (space in the middle of words from narrow columns)
    # e.g., "говоре ния" -> "говорения", "проб лем" -> "проблем"
    # But we need to be careful not to merge separate words
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\s+([.,;:!?])', r'\1', t)
    return t.strip()


def clean_description(desc: str) -> str:
    """Clean objective description text."""
    if not desc:
        return desc
    # Remove section headers that leaked in
    desc = re.sub(r'\s+\d+\)\s+(базовое содержание|аудирование|говорение|чтение|письмо|использование английского).*$', '', desc, flags=re.IGNORECASE)
    # Remove table column headers
    desc = re.sub(r'\s+(Обучающиеся должны|5 класс|6 класс|7 класс|8 класс|9 класс|ниже среднего|выше среднего|низкий В1|средний В1|высокий В1).*$', '', desc, flags=re.IGNORECASE)
    # Remove trailing punctuation
    desc = desc.rstrip(';').rstrip('.').strip()
    return desc


def parse_objectives_from_html() -> dict:
    """Parse learning objectives from the HTML block."""
    # Read HTML block
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    html_content = ''.join(lines[BLOCK_START-1:BLOCK_END])

    # Only take the "Параграф 2" section (objectives tables), not "Параграф 3" (долгосрочный план)
    para2_marker = 'Параграф 2. Система целей обучения'
    para3_marker = 'Параграф 3.'

    idx_start = html_content.find(para2_marker)
    idx_end = html_content.find(para3_marker)

    if idx_start == -1:
        raise ValueError("Could not find 'Параграф 2. Система целей обучения'")
    if idx_end == -1:
        idx_end = len(html_content)

    objectives_html = html_content[idx_start:idx_end]

    # Strip HTML, preserve some structure
    text = objectives_html.replace('<br>', '\n').replace('<br/>', '\n')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = text.replace('\u200B', '')  # Zero-width spaces
    text = re.sub(r'\s+', ' ', text)

    # Find all objective codes with descriptions
    code_pattern = re.compile(
        r'(\d{1,2})\s*\.\s*(\d)\s*\.\s*(\d{1,2})\s*\.\s*(\d+)'
        r'\s+'
        r'(.+?)(?=(?:\d{1,2}\s*\.\s*\d\s*\.\s*\d{1,2}\s*\.\s*\d+\s)|$)',
        re.DOTALL
    )

    objectives = {}
    for m in code_pattern.finditer(text):
        grade = int(m.group(1))
        section = int(m.group(2))
        subsection = int(m.group(3))
        order = int(m.group(4))
        description = normalize_text(m.group(5).strip())
        description = clean_description(description)

        code = f"{grade}.{section}.{subsection}.{order}"

        # Skip false matches (code examples in text)
        if description.startswith('"') and description[1:2].isdigit():
            continue

        # Only keep first occurrence (avoid duplicates)
        if code not in objectives:
            objectives[code] = {
                "code": code,
                "grade": grade,
                "section": section,
                "subsection": subsection,
                "order": order,
                "description": description,
            }

    return objectives


def fix_known_issues(objectives: dict) -> dict:
    """Fix known data issues in the parsed objectives."""
    # Known issue: 9.3.5.1 is printed as 8.3.5.1 in the source
    # Check if 9.3.5.1 is missing
    if "9.3.5.1" not in objectives and "8.3.5.1" in objectives:
        desc_8 = objectives["8.3.5.1"]["description"]
        # Create 9.3.5.1 with similar text
        objectives["9.3.5.1"] = {
            "code": "9.3.5.1",
            "grade": 9,
            "section": 3,
            "subsection": 5,
            "order": 1,
            "description": "взаимодействовать с одноклассниками для сотрудничества, обсуждения, согласования, планирования и расставления приоритетов с целью выполнения учебных задач",
        }
        print(f"  [FIX] Added missing 9.3.5.1 (was printed as 8.3.5.1 in source)")

    return objectives


def generate_sql(objectives: dict) -> str:
    """Generate SQL statements for import."""
    sql_lines = []
    sql_lines.append("-- GOSO English Language 5-9 Import")
    sql_lines.append("-- Generated by import_goso_english_5_9.py")
    sql_lines.append("BEGIN;")
    sql_lines.append("")

    # Set session vars for RLS bypass
    sql_lines.append("SET app.is_super_admin = 'true';")
    sql_lines.append("")

    # 1. Create framework
    sql_lines.append("-- Framework")
    sql_lines.append(f"""INSERT INTO frameworks (code, subject_id, title_ru, title_kz, document_type, order_number, order_date, ministry, appendix_number, is_active)
VALUES ('{FRAMEWORK_CODE}', {SUBJECT_ID}, '{FRAMEWORK_TITLE_RU}', '{FRAMEWORK_TITLE_KZ}',
        'Типовая учебная программа', '399', '2022-09-16',
        'Министерство просвещения Республики Казахстан', {APPENDIX_NUMBER}, true)
ON CONFLICT (code) DO NOTHING;""")
    sql_lines.append("")

    # 2. Create sections and subsections
    sql_lines.append("-- Sections and Subsections")
    for si, section in enumerate(SECTIONS):
        esc_name_ru = section["name_ru"].replace("'", "''")
        esc_name_kz = section["name_kz"].replace("'", "''")
        sql_lines.append(f"""INSERT INTO goso_sections (framework_id, code, name_ru, name_kz, display_order)
VALUES ((SELECT id FROM frameworks WHERE code = '{FRAMEWORK_CODE}'), '{section["code"]}', '{esc_name_ru}', '{esc_name_kz}', {si + 1})
ON CONFLICT (framework_id, code) DO NOTHING;""")

        for ssi, sub in enumerate(section["subsections"]):
            esc_sub_ru = sub["name_ru"].replace("'", "''")
            esc_sub_kz = sub["name_kz"].replace("'", "''")
            sql_lines.append(f"""INSERT INTO goso_subsections (section_id, code, name_ru, name_kz, display_order)
VALUES (
    (SELECT gs.id FROM goso_sections gs JOIN frameworks f ON gs.framework_id = f.id WHERE f.code = '{FRAMEWORK_CODE}' AND gs.code = '{section["code"]}'),
    '{sub["code"]}', '{esc_sub_ru}', '{esc_sub_kz}', {ssi + 1}
) ON CONFLICT (section_id, code) DO NOTHING;""")

    sql_lines.append("")

    # 3. Create learning outcomes
    sql_lines.append("-- Learning Outcomes")
    sorted_codes = sorted(objectives.keys(), key=lambda c: [int(x) for x in c.split('.')])

    for code in sorted_codes:
        obj = objectives[code]
        grade = obj["grade"]
        section_code = str(obj["section"])
        subsection_code = f"{obj['section']}.{obj['subsection']}"

        # Escape single quotes in description
        desc = obj["description"].replace("'", "''")

        sql_lines.append(f"""INSERT INTO learning_outcomes (framework_id, subsection_id, grade, code, title_ru, title_kz, display_order, is_active)
VALUES (
    (SELECT id FROM frameworks WHERE code = '{FRAMEWORK_CODE}'),
    (SELECT gss.id FROM goso_subsections gss
     JOIN goso_sections gs ON gss.section_id = gs.id
     JOIN frameworks f ON gs.framework_id = f.id
     WHERE f.code = '{FRAMEWORK_CODE}' AND gs.code = '{section_code}' AND gss.code = '{subsection_code}'),
    {grade}, '{code}', '{desc}', '{desc}', {obj["order"]}, true
) ON CONFLICT (framework_id, code) DO NOTHING;""")

    sql_lines.append("")
    sql_lines.append("COMMIT;")

    return '\n'.join(sql_lines)


def main():
    print("=" * 60)
    print("GOSO English Language (5-9) Import")
    print("=" * 60)

    # Step 1: Parse objectives
    print("\n1. Parsing objectives from HTML...")
    objectives = parse_objectives_from_html()
    print(f"   Found {len(objectives)} raw objectives")

    # Step 2: Fix known issues
    objectives = fix_known_issues(objectives)

    # Step 3: Validate
    print("\n2. Validation:")
    expected_subsections = {
        1: 10, 2: 8, 3: 8, 4: 9, 5: 9, 6: 17
    }

    by_grade = {}
    by_section = {}
    for code, obj in objectives.items():
        g = obj["grade"]
        s = obj["section"]
        by_grade[g] = by_grade.get(g, 0) + 1
        by_section[s] = by_section.get(s, 0) + 1

    print(f"   By grade: {dict(sorted(by_grade.items()))}")
    print(f"   By section: {dict(sorted(by_section.items()))}")

    # Check for missing objectives
    missing = []
    for section_code, subsection_count in expected_subsections.items():
        for sub_num in range(1, subsection_count + 1):
            for grade in range(5, 10):
                code = f"{grade}.{section_code}.{sub_num}.1"
                if code not in objectives:
                    missing.append(code)

    if missing:
        print(f"\n   WARNING: Missing {len(missing)} expected codes:")
        for m in missing[:20]:
            print(f"     - {m}")
        if len(missing) > 20:
            print(f"     ... and {len(missing) - 20} more")
    else:
        print("   All expected codes present!")

    total_expected = sum(v * 5 for v in expected_subsections.values())
    print(f"\n   Total: {len(objectives)} objectives (expected {total_expected})")

    # Step 4: Generate SQL
    print("\n3. Generating SQL...")
    sql = generate_sql(objectives)
    sql_path = Path("/tmp/goso_english_5_9.sql")
    sql_path.write_text(sql, encoding='utf-8')
    print(f"   Written to {sql_path} ({len(sql)} bytes)")

    # Step 5: Load into DB via docker
    print("\n4. Loading into database...")

    # Copy SQL file into container
    subprocess.run(
        ["docker", "cp", str(sql_path), "ai_mentor_postgres_prod:/tmp/goso_english_5_9.sql"],
        check=True
    )

    # Execute SQL
    result = subprocess.run(
        ["docker", "exec", "ai_mentor_postgres_prod", "psql", "-U", "ai_mentor_user", "-d", "ai_mentor_db",
         "-f", "/tmp/goso_english_5_9.sql"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"   ERROR: {result.stderr}")
        return

    print(f"   SQL output: {result.stdout[-500:] if len(result.stdout) > 500 else result.stdout}")

    # Step 6: Verify
    print("\n5. Verification:")
    verify = subprocess.run(
        ["docker", "exec", "ai_mentor_postgres_prod", "psql", "-U", "ai_mentor_user", "-d", "ai_mentor_db",
         "-c", f"""
SELECT grade, COUNT(*) as cnt FROM learning_outcomes lo
JOIN frameworks f ON lo.framework_id = f.id
WHERE f.code = '{FRAMEWORK_CODE}'
GROUP BY grade ORDER BY grade;
"""],
        capture_output=True, text=True
    )
    print(verify.stdout)

    # Spot-check
    spot = subprocess.run(
        ["docker", "exec", "ai_mentor_postgres_prod", "psql", "-U", "ai_mentor_user", "-d", "ai_mentor_db",
         "-c", f"""
SELECT code, LEFT(title_ru, 80) as title FROM learning_outcomes
WHERE framework_id = (SELECT id FROM frameworks WHERE code = '{FRAMEWORK_CODE}')
ORDER BY code LIMIT 15;
"""],
        capture_output=True, text=True
    )
    print(spot.stdout)

    print("Done!")


if __name__ == "__main__":
    main()
