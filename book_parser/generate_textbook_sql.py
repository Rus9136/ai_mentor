#!/usr/bin/env python3
"""
Генерация SQL для загрузки учебника из JSON в БД AI Mentor.

Использование:
    python3 generate_textbook_sql.py input.json output.sql
    python3 generate_textbook_sql.py input.json output.sql --title-suffix " (версия 2)"

Пример:
    python3 generate_textbook_sql.py books/output/algebra_7.json books/output/algebra_7.sql
"""
import json
import argparse
from pathlib import Path


def escape_sql(s):
    """Экранирование для SQL с E'' синтаксисом."""
    if s is None:
        return 'NULL'
    escaped = str(s).replace("'", "''").replace("\\", "\\\\")
    return "E'" + escaped + "'"


def json_value(obj):
    """JSON значение для SQL."""
    if obj is None:
        return 'NULL'
    j = json.dumps(obj, ensure_ascii=False)
    return escape_sql(j)


def generate_sql(json_path: str, output_path: str, title_suffix: str = ""):
    """Генерирует SQL файл из JSON."""

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tb = data['textbook']
    new_title = tb['title'] + title_suffix

    sql = []
    sql.append(f"-- Загрузка учебника: {new_title}")
    sql.append(f"-- Источник: {json_path}")
    sql.append("-- Сгенерировано автоматически скриптом generate_textbook_sql.py")
    sql.append("")
    sql.append("BEGIN;")
    sql.append("")

    # Textbook
    sql.append("-- 1. Создание учебника")
    year_val = tb.get('year')
    year_sql = str(year_val) if year_val else 'NULL'

    sql.append(f"""INSERT INTO textbooks (school_id, title, subject, grade_level, author, publisher, year, isbn, description, is_active, is_deleted, is_customized, version)
VALUES (NULL,
    {escape_sql(new_title)},
    {escape_sql(tb.get('subject'))},
    {tb.get('grade_level', 7)},
    {escape_sql(tb.get('authors', tb.get('author')))},
    {escape_sql(tb.get('publisher'))},
    {year_sql},
    {escape_sql(tb.get('isbn'))},
    {escape_sql(tb.get('description'))},
    true, false, false, 1);""")
    sql.append("")

    # Chapters and paragraphs
    sql.append("-- 2. Создание разделов и параграфов")
    sql.append("")

    for ch in data['chapters']:
        sql.append(f"-- Раздел {ch['number']}: {ch['title']}")
        sql.append(f"""INSERT INTO chapters (textbook_id, title, number, "order", description, is_deleted)
SELECT id, {escape_sql(ch['title'])}, {ch['number']}, {ch['number']}, {escape_sql(ch.get('description'))}, false
FROM textbooks WHERE title = {escape_sql(new_title)} AND school_id IS NULL;""")
        sql.append("")

        for idx, p in enumerate(ch.get('paragraphs', [])):
            content = p.get('content', '')
            learning_obj = p.get('learning_objective')
            key_terms = p.get('key_terms')
            questions = p.get('questions')

            sql.append(f"""INSERT INTO paragraphs (chapter_id, title, number, "order", content, learning_objective, key_terms, questions, is_deleted)
SELECT c.id, {escape_sql(p['title'])}, {p['number']}, {idx + 1},
    {escape_sql(content)},
    {escape_sql(learning_obj)},
    {json_value(key_terms)},
    {json_value(questions)},
    false
FROM chapters c
JOIN textbooks t ON t.id = c.textbook_id
WHERE t.title = {escape_sql(new_title)} AND t.school_id IS NULL AND c.number = {ch['number']};""")
        sql.append("")

    sql.append("COMMIT;")
    sql.append("")

    # Verification query
    sql.append("-- 3. Проверка результата")
    sql.append(f"""SELECT t.id, t.title, COUNT(DISTINCT c.id) as chapters, COUNT(DISTINCT p.id) as paragraphs
FROM textbooks t
LEFT JOIN chapters c ON c.textbook_id = t.id
LEFT JOIN paragraphs p ON p.chapter_id = c.id
WHERE t.title = {escape_sql(new_title)}
GROUP BY t.id, t.title;""")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql))

    # Statistics
    total_chapters = len(data['chapters'])
    total_paragraphs = sum(len(ch.get('paragraphs', [])) for ch in data['chapters'])

    print(f"")
    print(f"SQL файл создан: {output_path}")
    print(f"")
    print(f"Учебник: {new_title}")
    print(f"Предмет: {tb.get('subject', 'Не указан')}")
    print(f"Класс: {tb.get('grade_level', 'Не указан')}")
    print(f"Разделов: {total_chapters}")
    print(f"Параграфов: {total_paragraphs}")
    print(f"")
    print(f"Для загрузки выполните:")
    print(f"  docker cp {output_path} ai_mentor_postgres_prod:/tmp/textbook.sql")
    print(f"  docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/textbook.sql")
    print(f"")
    print(f"ВАЖНО: После загрузки выполните преобразование формата questions!")
    print(f"См. документацию: docs/TEXTBOOK_LOADING_GUIDE.md")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Генерация SQL для загрузки учебника из JSON',
        epilog='Документация: docs/TEXTBOOK_LOADING_GUIDE.md'
    )
    parser.add_argument('input', help='Путь к JSON файлу с учебником')
    parser.add_argument('output', help='Путь к выходному SQL файлу')
    parser.add_argument(
        '--title-suffix',
        default='',
        help='Суффикс к названию учебника (например: " (полная версия)")'
    )

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Ошибка: файл не найден: {args.input}")
        exit(1)

    generate_sql(args.input, args.output, args.title_suffix)
