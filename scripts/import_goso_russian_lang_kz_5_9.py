#!/usr/bin/env python3
"""
GOSO Data Import Script for Русский язык и литература (5-9 кл, нерус/KZ schools).
Parses Appendix 48 from book_parser/adilet-kaz.html and imports learning objectives.

Source: 48-қосымша, lines 94647-97858
Subject: russian_lang (id=33)
This is a SEPARATE framework from Appendix 39 (Russian-medium schools).
"""
import re
import sys
from pathlib import Path
from datetime import date

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# --- SECTIONS (from Appendix 48, KZ-medium curriculum) ---
SECTIONS = [
    {
        "code": "1",
        "name_ru": "Аудирование (Тыңдалым)",
        "name_kz": "Тыңдалым",
        "subsections": [
            {"code": "1.1", "name_ru": "Понимание устного сообщения/аудио/видеоматериала", "name_kz": "Ауызша хабарламаны/аудио/бейнематериалды түсіну"},
            {"code": "1.2", "name_ru": "Понимание лексического значения слов", "name_kz": "Сөздердің лексикалық мағынасын түсіну"},
            {"code": "1.3", "name_ru": "Понимание содержания художественных произведений", "name_kz": "Көркем туындылардың мазмұнын түсіну"},
            {"code": "1.4", "name_ru": "Определение основной мысли", "name_kz": "Негізгі ойды анықтау"},
            {"code": "1.5", "name_ru": "Прогнозирование содержания текста", "name_kz": "Мәтін мазмұнын болжау"},
        ]
    },
    {
        "code": "2",
        "name_ru": "Говорение (Айтылым)",
        "name_kz": "Айтылым",
        "subsections": [
            {"code": "2.1", "name_ru": "Разнообразие словарного запаса", "name_kz": "Сөздік қордың алуан түрлілігі"},
            {"code": "2.2", "name_ru": "Пересказ прослушанного/прочитанного текста", "name_kz": "Тыңдалған/оқылған мәтінді қайта айту"},
            {"code": "2.3", "name_ru": "Соблюдение речевых норм", "name_kz": "Сөйлеу нормаларын сақтау"},
            {"code": "2.4", "name_ru": "Построение монологической речи", "name_kz": "Монологтік сөз құру"},
            {"code": "2.5", "name_ru": "Участие в диалоге", "name_kz": "Диалогке қатысу"},
            {"code": "2.6", "name_ru": "Оценивание устного высказывания", "name_kz": "Ауызша пікірді бағалау"},
        ]
    },
    {
        "code": "3",
        "name_ru": "Чтение (Оқылым)",
        "name_kz": "Оқылым",
        "subsections": [
            {"code": "3.1", "name_ru": "Понимание содержания текста", "name_kz": "Мәтін мазмұнын түсіну"},
            {"code": "3.2", "name_ru": "Определение стилей и типов речи", "name_kz": "Сөйлеу стильдері мен түрлерін анықтау"},
            {"code": "3.3", "name_ru": "Составление вопросов и ответов", "name_kz": "Сұрақ-жауап құрастыру"},
            {"code": "3.4", "name_ru": "Владение различными видами чтения", "name_kz": "Әртүрлі оқу түрлерін меңгеру"},
            {"code": "3.5", "name_ru": "Составление плана", "name_kz": "Жоспар құру"},
            {"code": "3.6", "name_ru": "Анализ художественных произведений", "name_kz": "Көркем туындыларды талдау"},
            {"code": "3.7", "name_ru": "Извлечение информации из различных источников", "name_kz": "Әртүрлі ресурстардан ақпарат алу"},
            {"code": "3.8", "name_ru": "Сравнительный анализ", "name_kz": "Салыстыру"},
        ]
    },
    {
        "code": "4",
        "name_ru": "Письмо (Жазылым)",
        "name_kz": "Жазылым",
        "subsections": [
            {"code": "4.1", "name_ru": "Создание текстов различных жанров и стилей", "name_kz": "Әртүрлі жанрлардағы және сөйлеу стильдеріндегі мәтіндер құру"},
            {"code": "4.2", "name_ru": "Обобщение прослушанного, прочитанного и аудиовизуального материала", "name_kz": "Тыңдалған, оқылған және аудиовизуалды материалды жалпылау"},
            {"code": "4.3", "name_ru": "Представление информации в различных формах", "name_kz": "Ақпаратты әртүрлі формаларда беру"},
            {"code": "4.4", "name_ru": "Творческое письмо", "name_kz": "Шығармашылық хат"},
            {"code": "4.5", "name_ru": "Написание эссе", "name_kz": "Эссе жазу"},
            {"code": "4.6", "name_ru": "Соблюдение орфографических норм", "name_kz": "Орфографиялық нормаларды сақтау"},
            {"code": "4.7", "name_ru": "Соблюдение пунктуационных норм", "name_kz": "Пунктуациялық нормаларды сақтау"},
        ]
    },
    {
        "code": "5",
        "name_ru": "Использование языковых единиц (Тілдік бірліктерді пайдалану)",
        "name_kz": "Тілдік бірліктерді пайдалану",
        "subsections": [
            {"code": "5.1", "name_ru": "Использование грамматических форм слов", "name_kz": "Сөздердің грамматикалық формаларын қолдану"},
            {"code": "5.2", "name_ru": "Использование синтаксических конструкций", "name_kz": "Синтаксистік құрылымдарды қолдану"},
        ]
    },
]

# Word-break fixes from OCR narrow 5-column KZ tables
WORD_BREAKS = {
    "кейіп-керлерге": "кейіпкерлерге",
    "кейіп- керлерге": "кейіпкерлерге",
    "тақырыпта-ғы": "тақырыптағы",
    "тақырыпта- ғы": "тақырыптағы",
    "грам-матикалық": "грамматикалық",
    "грам- матикалық": "грамматикалық",
    "қаһарман-ның": "қаһарманның",
    "әрекет-терін": "әрекеттерін",
    "сипат-тау": "сипаттау",
    "стилистика-лық": "стилистикалық",
    "хабарлан-дыру": "хабарландыру",
    "сәйкестенді-ріп": "сәйкестендіріп",
    "баяндау/си-паттау": "баяндау/сипаттау",
    "эле-менттерімен": "элементтерімен",
    "ерекшелікте-рін": "ерекшеліктерін",
    "келіспе-уін": "келіспеуін",
    "келісі-мін": "келісімін",
    "негіз-деп": "негіздеп",
    "жол-дарын": "жолдарын",
    "ұсы-нып": "ұсынып",
    "ұсы-нылған": "ұсынылған",
    "тақырыптар-ға": "тақырыптарға",
    "салыстырма лы": "салыстырмалы",
    "шығармашы-лық": "шығармашылық",
    "аудиовизу-алды": "аудиовизуалды",
    "қатарыменауыстыру": "қатарымен ауыстыру",
    "жарнама)мәтіндерді": "жарнама) мәтіндерді",
    "мінездеме,өмірбаян": "мінездеме, өмірбаян",
    "әң-гімелердің": "әңгімелердің",
    "бағалау негізінде ұсынылған тақырыпқа/жағдайға қатысты тұрғыда орфоэпиялық": "бағалау негізінде, ұсынылған тақырыпқа/жағдайға қатысты тұрғыда, орфоэпиялық",
    "сөйлем-дерде": "сөйлемдерде",
    "тіркес-терінің": "тіркестерінің",
}


def normalize_text(t):
    if not t:
        return t
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\s+([.,;:!?])', r'\1', t)
    return t.strip()


def clean_description(desc):
    """Clean up description text."""
    # Remove trailing section/paragraph markers
    desc = re.sub(r'\s+\d{2}\.\s+[А-ЯӘӨҮҰҚҒІҢа-яәөүұқғіңбA-Z].*$', '', desc)
    # Remove trailing table headers
    desc = re.sub(r'\s+(Бөлімше|Білім алушылар|Дағдылар|Оқу мақсаттары)\b.*$', '', desc)
    # Remove trailing subsection headers like "2. Сөздердің лексикалық"
    desc = re.sub(r'\s+\d+\.\s+[А-ЯӘӨҮҰҚҒІҢа-яA-Z][а-яәөүұқғіңбa-z].*$', '', desc)
    # Remove noise reference codes like "7.Ж2." or "10.Ж2."
    desc = re.sub(r'\s*\d+\.Ж\d+\.?\s+.*$', '', desc)
    # Remove trailing section label like "5) тілдік бірліктерді пайдалану"
    desc = re.sub(r'\s+\d+\)\s+[а-яәөүұқғіңб].*$', '', desc)
    # Strip trailing punctuation
    desc = desc.rstrip(';').rstrip('.').rstrip(',').strip()
    return desc


def parse_objectives(html_path):
    """Parse learning objectives from extracted HTML block."""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Find 2-параграф (objectives) and stop at 3-параграф
    idx_start = html_content.find('2-параграф. Оқу мақсаттарының жүйесі')
    idx_end = html_content.find('3-параграф.')
    if idx_start == -1:
        print("ERROR: Could not find '2-параграф'")
        sys.exit(1)
    if idx_end == -1:
        idx_end = len(html_content)

    block = html_content[idx_start:idx_end]

    # Strip HTML
    text = block.replace('<br>', '\n').replace('<br/>', '\n')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = text.replace('\u200B', '')
    text = re.sub(r'\s+', ' ', text)

    # Fix word breaks (longest first)
    for old, new in sorted(WORD_BREAKS.items(), key=lambda x: -len(x[0])):
        text = text.replace(old, new)

    # Parse objective codes — allow spaces between digits (KZ format: "5. 1. 1. 1")
    code_pattern = re.compile(
        r'(\d{1,2})\s*\.\s*(\d)\s*\.\s*(\d)\s*\.\s*(\d+)'
        r'\.?\s*'
        r'(.+?)(?=(?:\d{1,2}\s*\.\s*\d\s*\.\s*\d\s*\.\s*\d+)|$)',
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

        # Skip false match on code example
        if 'кодында' in description or 'кодтық белгі' in description:
            continue
        if description.startswith('"') and ('сынып' in description[:20] or 'класс' in description[:20]):
            continue

        description = clean_description(description)
        description = description.rstrip(';').rstrip('.').strip()

        if code not in objectives and description:
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
    return s.replace("'", "''")


def generate_sql(objectives, subject_id=33):
    lines = []
    lines.append("-- GOSO Import: Орыс тілі мен әдебиеті 5-9 сыныптар (KZ-medium schools)")
    lines.append("-- Source: 48-қосымша, book_parser/adilet-kaz.html")
    lines.append(f"-- Generated: {date.today()}")
    lines.append("BEGIN;")
    lines.append("")

    fw_code = "goso_russian_lang_kz_5_9_2022_09_16"
    fw_title_kz = 'Негізгі орта білім беру деңгейінің 5-9-сыныптарына арналған "Орыс тілі мен әдебиеті" оқу пәні бойынша үлгілік оқу бағдарламасы'
    fw_title_ru = 'Типовая учебная программа по учебному предмету "Русский язык и литература" для 5-9 классов (нерусские школы)'
    lines.append(f"INSERT INTO frameworks (subject_id, code, title_ru, title_kz, appendix_number)")
    lines.append(f"VALUES ({subject_id}, '{fw_code}', '{escape_sql(fw_title_ru)}', '{escape_sql(fw_title_kz)}', 48)")
    lines.append(f"ON CONFLICT (code) DO NOTHING;")
    lines.append("")

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
    html_path = Path("/tmp/goso_russian_lang_kz_5_9.html")
    if not html_path.exists():
        print("ERROR: Extract the block first:")
        print("  sed -n '94647,97858p' book_parser/adilet-kaz.html > /tmp/goso_russian_lang_kz_5_9.html")
        sys.exit(1)

    print(f"Parsing objectives from: {html_path}")
    objectives = parse_objectives(html_path)

    print(f"\nTotal objectives parsed: {len(objectives)}")
    by_grade = {}
    for obj in objectives:
        by_grade.setdefault(obj["grade"], []).append(obj)
    for grade in sorted(by_grade.keys()):
        print(f"  Grade {grade}: {len(by_grade[grade])} objectives")

    by_section = {}
    for obj in objectives:
        by_section.setdefault(obj["section"], []).append(obj)
    sec_names = {1: "Тыңдалым", 2: "Айтылым", 3: "Оқылым", 4: "Жазылым", 5: "Тілдік бірліктерді пайдалану"}
    print("\nBy section:")
    for sec in sorted(by_section.keys()):
        print(f"  {sec}. {sec_names.get(sec, '?')}: {len(by_section[sec])} objectives")

    print("\nFirst 5 objectives:")
    for obj in objectives[:5]:
        print(f"  {obj['code']}: {obj['description'][:80]}...")

    print("\nLast 5 objectives:")
    for obj in objectives[-5:]:
        print(f"  {obj['code']}: {obj['description'][:80]}...")

    # Show section 5 objectives (complex structure)
    sec5 = [o for o in objectives if o["section"] == 5]
    print(f"\nSection 5 objectives ({len(sec5)}):")
    for obj in sec5:
        print(f"  {obj['code']}: {obj['description'][:80]}...")

    sql = generate_sql(objectives)
    sql_path = Path("/tmp/goso_russian_lang_kz_5_9.sql")
    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write(sql)
    print(f"\nSQL written to: {sql_path}")
    print(f"SQL size: {len(sql)} bytes, {sql.count(chr(10))} lines")

    return objectives


if __name__ == "__main__":
    main()
