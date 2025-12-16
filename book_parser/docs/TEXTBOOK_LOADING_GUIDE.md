# Руководство по загрузке учебников в БД

## Обзор

Это руководство описывает процесс загрузки учебников в базу данных AI Mentor.

**Путь к файлам:** `/home/rus/projects/ai_mentor/book_parser/`

---

## 1. Формат JSON файла

### Структура файла

```json
{
  "textbook": {
    "title": "Название учебника",
    "subject": "Предмет",
    "grade_level": 7,
    "authors": "Автор 1, Автор 2",
    "publisher": "Издательство",
    "year": 2025,
    "isbn": "978-XXX-XX-XXXX-X",
    "description": "Описание учебника"
  },
  "chapters": [
    {
      "number": 1,
      "title": "Название раздела",
      "description": "Описание раздела",
      "paragraphs": [
        {
          "number": 1,
          "title": "Название параграфа",
          "learning_objective": "Цели обучения",
          "key_terms": ["термин1", "термин2", "термин3"],
          "content": "Полный текст параграфа...",
          "questions": ["Вопрос 1?", "Вопрос 2?"]
        }
      ]
    }
  ]
}
```

### Описание полей

#### Textbook (учебник)

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `title` | string | Да | Название учебника |
| `subject` | string | Да | Предмет (История Казахстана, Математика, и т.д.) |
| `grade_level` | int | Да | Класс (7, 8, 9...) |
| `authors` | string | Нет | Авторы через запятую |
| `publisher` | string | Нет | Издательство |
| `year` | int | Нет | Год издания |
| `isbn` | string | Нет | ISBN номер |
| `description` | string | Нет | Описание учебника |

#### Chapter (раздел/глава)

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `number` | int | Да | Номер раздела (1, 2, 3...) |
| `title` | string | Да | Название раздела |
| `description` | string | Нет | Описание раздела |
| `paragraphs` | array | Да | Массив параграфов |

#### Paragraph (параграф)

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `number` | int | Да | Номер параграфа |
| `title` | string | Да | Название параграфа |
| `content` | string | Да | Полный текст параграфа |
| `learning_objective` | string | Нет | Цели обучения |
| `key_terms` | array[string] | Нет | Ключевые термины |
| `questions` | array[string] | Нет | Вопросы для самопроверки |

---

## 2. Генерация SQL из JSON

### Скрипт генерации

Файл: `generate_textbook_sql.py`

```python
#!/usr/bin/env python3
"""
Генерация SQL для загрузки учебника из JSON.

Использование:
    python3 generate_textbook_sql.py input.json output.sql
    python3 generate_textbook_sql.py input.json output.sql --title-suffix " (версия 2)"
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
    sql.append("-- Сгенерировано автоматически")
    sql.append("BEGIN;")
    sql.append("")

    # Textbook
    sql.append("-- Учебник")
    sql.append(f"""INSERT INTO textbooks (school_id, title, subject, grade_level, author, publisher, year, isbn, description, is_active, is_deleted, is_customized, version)
VALUES (NULL,
    {escape_sql(new_title)},
    {escape_sql(tb.get('subject'))},
    {tb.get('grade_level', 7)},
    {escape_sql(tb.get('authors', tb.get('author')))},
    {escape_sql(tb.get('publisher'))},
    {tb.get('year') or 'NULL'},
    {escape_sql(tb.get('isbn'))},
    {escape_sql(tb.get('description'))},
    true, false, false, 1);""")
    sql.append("")

    # Chapters and paragraphs
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
    sql.append("-- Проверка")
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

    print(f"SQL файл создан: {output_path}")
    print(f"Учебник: {new_title}")
    print(f"Разделов: {total_chapters}")
    print(f"Параграфов: {total_paragraphs}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Генерация SQL из JSON')
    parser.add_argument('input', help='Путь к JSON файлу')
    parser.add_argument('output', help='Путь к выходному SQL файлу')
    parser.add_argument('--title-suffix', default='', help='Суффикс к названию учебника')

    args = parser.parse_args()
    generate_sql(args.input, args.output, args.title_suffix)
```

### Использование

```bash
cd /home/rus/projects/ai_mentor/book_parser

# Генерация SQL
python3 generate_textbook_sql.py books/output/my_textbook.json books/output/my_textbook.sql

# С суффиксом в названии
python3 generate_textbook_sql.py books/output/my_textbook.json books/output/my_textbook.sql --title-suffix " (полная версия)"
```

---

## 3. Загрузка SQL в БД

### Копирование и выполнение

```bash
# 1. Копируем SQL в контейнер
docker cp books/output/my_textbook.sql ai_mentor_postgres_prod:/tmp/my_textbook.sql

# 2. Выполняем SQL
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/my_textbook.sql
```

### Ожидаемый вывод

```
BEGIN
INSERT 0 1
INSERT 0 1
... (много INSERT 0 1)
COMMIT
 id |        title         | chapters | paragraphs
----+----------------------+----------+------------
 11 | Название учебника    |        6 |         47
(1 row)
```

---

## 4. Пост-обработка: формат questions

**ВАЖНО!** После загрузки нужно преобразовать формат `questions`.

В JSON вопросы хранятся как массив строк:
```json
["Вопрос 1?", "Вопрос 2?"]
```

API ожидает формат:
```json
[{"order": 1, "text": "Вопрос 1?"}, {"order": 2, "text": "Вопрос 2?"}]
```

### SQL для преобразования

```sql
-- Замените TEXTBOOK_ID на ID вашего учебника
UPDATE paragraphs p
SET questions = (
    SELECT json_agg(
        json_build_object(
            'order', ordinality::int,
            'text', elem
        )
        ORDER BY ordinality
    )
    FROM jsonb_array_elements_text(p.questions::jsonb) WITH ORDINALITY AS t(elem, ordinality)
)
WHERE p.chapter_id IN (SELECT id FROM chapters WHERE textbook_id = TEXTBOOK_ID)
  AND p.questions IS NOT NULL;
```

### Пример выполнения

```bash
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -c "
UPDATE paragraphs p
SET questions = (
    SELECT json_agg(
        json_build_object('order', ordinality::int, 'text', elem)
        ORDER BY ordinality
    )
    FROM jsonb_array_elements_text(p.questions::jsonb) WITH ORDINALITY AS t(elem, ordinality)
)
WHERE p.chapter_id IN (SELECT id FROM chapters WHERE textbook_id = 11)
  AND p.questions IS NOT NULL;
"
```

---

## 5. Проверка загруженных данных

### Список учебников

```bash
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -c "
SELECT id, title, subject, grade_level
FROM textbooks
WHERE school_id IS NULL AND is_deleted = false
ORDER BY id;
"
```

### Статистика учебника

```bash
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -c "
SELECT
    t.id,
    t.title,
    COUNT(DISTINCT c.id) as chapters,
    COUNT(DISTINCT p.id) as paragraphs
FROM textbooks t
LEFT JOIN chapters c ON c.textbook_id = t.id
LEFT JOIN paragraphs p ON p.chapter_id = c.id
WHERE t.id = 11  -- Замените на нужный ID
GROUP BY t.id, t.title;
"
```

### Проверка качества данных

```bash
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -c "
SELECT
    p.number,
    LEFT(p.title, 40) as title,
    LENGTH(p.content) as content_len,
    CASE WHEN p.learning_objective IS NOT NULL THEN 'YES' ELSE 'no' END as learn_obj,
    CASE WHEN p.key_terms IS NOT NULL THEN json_array_length(p.key_terms)::text ELSE '-' END as key_terms,
    CASE WHEN p.questions IS NOT NULL THEN json_array_length(p.questions)::text ELSE '-' END as questions
FROM paragraphs p
JOIN chapters c ON c.id = p.chapter_id
WHERE c.textbook_id = 11  -- Замените на нужный ID
ORDER BY c.number, p.order;
"
```

---

## 6. Удаление учебника

**ВНИМАНИЕ:** Это удалит учебник и все связанные данные (главы, параграфы).

```sql
-- Soft delete (рекомендуется)
UPDATE textbooks SET is_deleted = true, deleted_at = NOW() WHERE id = 11;

-- Hard delete (необратимо!)
DELETE FROM textbooks WHERE id = 11;
```

---

## 7. Полный пример: загрузка нового учебника

```bash
cd /home/rus/projects/ai_mentor/book_parser

# 1. Подготовить JSON файл (см. формат выше)
# books/output/algebra_7.json

# 2. Сгенерировать SQL
python3 generate_textbook_sql.py books/output/algebra_7.json books/output/algebra_7.sql

# 3. Загрузить в БД
docker cp books/output/algebra_7.sql ai_mentor_postgres_prod:/tmp/algebra_7.sql
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/algebra_7.sql

# 4. Получить ID нового учебника из вывода, например: 12

# 5. Преобразовать формат questions
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -c "
UPDATE paragraphs p
SET questions = (
    SELECT json_agg(json_build_object('order', ordinality::int, 'text', elem) ORDER BY ordinality)
    FROM jsonb_array_elements_text(p.questions::jsonb) WITH ORDINALITY AS t(elem, ordinality)
)
WHERE p.chapter_id IN (SELECT id FROM chapters WHERE textbook_id = 12)
  AND p.questions IS NOT NULL;
"

# 6. Проверить на сайте
# https://admin.ai-mentor.kz -> Учебники -> Выбрать новый учебник
```

---

## Примеры JSON файлов

- `books/output/history_kz_7_structured.json` - История Казахстана 7 класс (полная версия)

## Примеры SQL файлов

- `books/output/insert_history_kz_7.sql` - SQL для загрузки истории Казахстана 7 класс
