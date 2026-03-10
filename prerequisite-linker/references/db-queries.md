# SQL-запросы для работы с prerequisites

## Все учебники предмета

```sql
SELECT t.id, t.title, t.grade_level, t.subject_id,
       COUNT(p.id) as para_count
FROM textbooks t
JOIN chapters c ON c.textbook_id = t.id
JOIN paragraphs p ON p.chapter_id = c.id
WHERE t.subject_id = {SUBJECT_ID}
  AND t.school_id IS NULL
GROUP BY t.id
ORDER BY t.grade_level, t.id;
```

## Все параграфы предмета (компактный формат)

```sql
SELECT t.grade_level, t.id as tid, p.number, p.id as pid, p.title
FROM paragraphs p
JOIN chapters c ON c.id = p.chapter_id
JOIN textbooks t ON t.id = c.textbook_id
WHERE t.id IN ({TEXTBOOK_IDS})
ORDER BY t.grade_level, t.id, p.number;
```

## Текущие связи предмета

```sql
SELECT
  pp.id,
  t2.grade_level as from_grade,
  '§' || p2.number as from_para,
  LEFT(p2.title, 50) as prerequisite,
  '→' as dir,
  t1.grade_level as to_grade,
  '§' || p1.number as to_para,
  LEFT(p1.title, 50) as paragraph,
  pp.strength
FROM paragraph_prerequisites pp
JOIN paragraphs p1 ON p1.id = pp.paragraph_id
JOIN chapters c1 ON c1.id = p1.chapter_id
JOIN textbooks t1 ON t1.id = c1.textbook_id
JOIN paragraphs p2 ON p2.id = pp.prerequisite_paragraph_id
JOIN chapters c2 ON c2.id = p2.chapter_id
JOIN textbooks t2 ON t2.id = c2.textbook_id
WHERE t1.subject_id = {SUBJECT_ID}
ORDER BY t2.grade_level, t1.grade_level, pp.id;
```

## Подсчёт связей по предмету

```sql
SELECT COUNT(*) as total_links,
       COUNT(CASE WHEN pp.strength = 'required' THEN 1 END) as required_count,
       COUNT(CASE WHEN pp.strength = 'recommended' THEN 1 END) as recommended_count
FROM paragraph_prerequisites pp
JOIN paragraphs p1 ON p1.id = pp.paragraph_id
JOIN chapters c1 ON c1.id = p1.chapter_id
JOIN textbooks t1 ON t1.id = c1.textbook_id
WHERE t1.subject_id = {SUBJECT_ID};
```

## Создание связи

```sql
INSERT INTO paragraph_prerequisites (paragraph_id, prerequisite_paragraph_id, strength)
VALUES ({PARAGRAPH_ID}, {PREREQUISITE_PARAGRAPH_ID}, '{STRENGTH}')
ON CONFLICT (paragraph_id, prerequisite_paragraph_id) DO NOTHING;
```

## Создание связей пакетом

```sql
INSERT INTO paragraph_prerequisites (paragraph_id, prerequisite_paragraph_id, strength) VALUES
(para_id_1, prereq_id_1, 'required'),
(para_id_2, prereq_id_2, 'recommended')
ON CONFLICT (paragraph_id, prerequisite_paragraph_id) DO NOTHING;
```

## Удаление связи

```sql
DELETE FROM paragraph_prerequisites WHERE id = {PREREQ_LINK_ID};
```

## Чтение содержимого параграфа (при необходимости уточнить тему)

```sql
SELECT p.id, p.number, p.title, LEFT(p.content, 500) as content_preview,
       c.title as chapter, t.title as textbook, t.grade_level
FROM paragraphs p
JOIN chapters c ON c.id = p.chapter_id
JOIN textbooks t ON t.id = c.textbook_id
WHERE p.id = {PARAGRAPH_ID};
```

## Поиск subject_id по названию

```sql
SELECT id, title FROM subjects WHERE title ILIKE '%{SUBJECT_NAME}%';
```

Если subjects таблицы нет или предмет не найден — искать через textbooks:

```sql
SELECT DISTINCT t.subject_id, t.title
FROM textbooks t
WHERE t.title ILIKE '%{SUBJECT_NAME}%'
  AND t.school_id IS NULL
ORDER BY t.subject_id;
```

## Подключение к БД

```bash
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -c "SQL"
```

Для длинных запросов с кавычками использовать `--no-align -t` флаги для компактного вывода.
