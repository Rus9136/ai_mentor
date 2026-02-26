# Инструкция по загрузке учебников

Пошаговое руководство по загрузке учебника из MD файла в базу данных AI Mentor.

---

## Требования

- MD файл учебника (формат: markdown с LaTeX формулами `$...$`, `$$...$$`)
- Папка `images/` с изображениями (если есть в учебнике)
- Доступ к серверу с запущенными Docker контейнерами

## Структура MD файла

Скрипт ожидает следующую структуру:

```
# Преамбула (пропускается до маркера "КАЙТАЛАУҒА АРНАЛҒАН ЖАТТЫҒУЛАР")

## 7-8-СЫНЫПТАРДАҒЫ ... КАЙТАЛАУҒА АРНАЛҒАН ЖАТТЫҒУЛАР   ← Раздел повторения (Chapter 0)
## Подраздел 1                                           ← Параграф внутри повторения
1. Задача...
1) Подзадача...

# І тарау. НАЗВАНИЕ ГЛАВЫ                               ← Chapter 1
## §1. Название параграфа                                ← Paragraph 1
Текст теории...
1. Задача с $формулами$...

## §2. Название параграфа                                ← Paragraph 2
...

## ӨЗІҢДІ ТЕКСЕР!                                        ← Самопроверка (в конце каждой главы)

# ІІ тарау. НАЗВАНИЕ ГЛАВЫ                              ← Chapter 2
## §7. ...

## ЖАУАПТАРЫ                                             ← Ответы (пропускаются)
## МАЗМУНЫ                                               ← Содержание (пропускается)
```

---

## Пошаговый процесс

### Шаг 1. Подготовка файлов

1. Положите MD файл и папку `images/` в любую директорию проекта, например:

```
docs/textbooks/algebra10/
├── textbook.md
└── images/
    ├── img_001.jpg
    ├── img_002.jpg
    └── ...
```

2. В MD файле изображения должны быть в формате:
```markdown
![описание](./images/img_001.jpg)
```

### Шаг 2. Настройка скрипта

Откройте `scripts/load_algebra9_textbook.py` и измените константы в блоке `Constants` (строки 36-47):

```python
TEXTBOOK_TITLE = "Алгебра 10 сынып, 1-бөлім"    # Название учебника
SUBJECT_CODE = "algebra"                          # Предмет (algebra, geometry, physics...)
GRADE_LEVEL = 10                                  # Класс
AUTHORS = "Фамилия И.О., ..."                     # Авторы
PUBLISHER = "Мектеп"                              # Издательство
YEAR = 2020                                       # Год издания
ISBN = "978-..."                                  # ISBN
LANGUAGE = "kk"                                   # Язык: "kk" (казахский), "ru" (русский)

MD_FILE = PROJECT_ROOT / "docs" / "textbooks" / "algebra10" / "textbook.md"
IMAGES_SRC_DIR = PROJECT_ROOT / "docs" / "textbooks" / "algebra10" / "images"
```

Если в учебнике другая структура заголовков или OCR-артефакты, может потребоваться настроить:

- `INTERNAL_HEADINGS` — заголовки, которые НЕ являются границами параграфов (например, "Мысал", "Жаттығулар", "A", "B", "C")
- `OCR_FIXES` — замены OCR-ошибок в заголовках
- `RE_REVIEW_START` — маркер начала раздела повторения

### Шаг 3. Тестовый запуск (dry-run)

```bash
python3 scripts/load_algebra9_textbook.py --dry-run
```

Проверьте вывод:
- Количество глав (chapters) — соответствует учебнику?
- Количество параграфов в каждой главе — правильное?
- Заголовки параграфов — корректные?
- Количество строк контента — не пустые?

```
--- Parsing Results ---
  Chapter 0: Повторение...
    Paragraphs: 6, Content lines: 483
  Chapter 1: І тарау. ...
    Paragraphs: 7, Content lines: 1436
  ...
  Total: 4 chapters, 27 paragraphs, 4834 content lines
```

Если что-то не так — вернитесь к Шагу 2 и настройте регулярные выражения/заголовки.

### Шаг 4. Генерация SQL

```bash
# Генерация SQL для учебника (главы, параграфы, контент)
python3 scripts/load_algebra9_textbook.py --generate-sql /tmp/textbook_import.sql

# Генерация SQL для упражнений (задачи с уровнями A/B/C и ответами)
python3 scripts/load_algebra9_textbook.py --exercises /tmp/textbook_exercises.sql
```

### Шаг 5. Импорт в базу данных

```bash
# Копируем SQL в контейнер PostgreSQL
docker cp /tmp/textbook_import.sql ai_mentor_postgres_prod:/tmp/import.sql

# Выполняем импорт
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/import.sql

# Импорт упражнений (после основного импорта)
docker cp /tmp/textbook_exercises.sql ai_mentor_postgres_prod:/tmp/exercises.sql
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/exercises.sql
```

Ожидаемый вывод — серия `INSERT 0 1` и `UPDATE N` в конце. Если ошибки — см. раздел "Troubleshooting".

### Шаг 6. Копирование изображений

Узнайте ID учебника:
```bash
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -t -A \
  -c "SELECT id FROM textbooks WHERE title = 'Алгебра 10 сынып, 1-бөлім' AND is_deleted = false;"
```

Скопируйте изображения (замените `<ID>` на полученный ID и путь к images):
```bash
mkdir -p uploads/textbook-images/<ID>/
cp docs/textbooks/algebra10/images/* uploads/textbook-images/<ID>/
```

Проверьте доступность через API:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8020/uploads/textbook-images/<ID>/img_001.jpg
# Ожидаем: 200
```

### Шаг 7. Проверка

```bash
# Количество глав
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db \
  -c "SELECT count(*) FROM chapters WHERE textbook_id = <ID> AND is_deleted = false;"

# Количество параграфов
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db \
  -c "SELECT count(*) FROM paragraphs p JOIN chapters c ON p.chapter_id = c.id
      WHERE c.textbook_id = <ID> AND p.is_deleted = false;"

# Проверка контента (не пустой)
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db \
  -c "SELECT p.number, LEFT(p.title, 50), LENGTH(p.content) as content_len
      FROM paragraphs p JOIN chapters c ON p.chapter_id = c.id
      WHERE c.textbook_id = <ID> AND p.is_deleted = false
      ORDER BY c.number, p.number;"
```

### Шаг 8. Визуальная проверка

1. Откройте Student App (`ai-mentor.kz`)
2. Войдите под тестовым учеником
3. Перейдите к новому учебнику
4. Откройте любой параграф
5. Проверьте:
   - Формулы отображаются (KaTeX рендеринг)
   - Изображения загружаются
   - Задачи разделены отступами
   - Подзадачи с отступом слева

---

## Обновление контента

Если нужно перегенерировать HTML (например, после исправления конвертера):

```bash
# Генерация UPDATE SQL
python3 scripts/load_algebra9_textbook.py --update-content /tmp/textbook_update.sql

# Применение
docker cp /tmp/textbook_update.sql ai_mentor_postgres_prod:/tmp/update.sql
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f /tmp/update.sql
```

---

## Удаление учебника

Если нужно удалить загруженный учебник и начать заново:

```bash
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -c "
  DELETE FROM exercises WHERE paragraph_id IN (
    SELECT p.id FROM paragraphs p JOIN chapters c ON p.chapter_id = c.id WHERE c.textbook_id = <ID>
  );
  DELETE FROM paragraph_contents WHERE paragraph_id IN (
    SELECT p.id FROM paragraphs p JOIN chapters c ON p.chapter_id = c.id WHERE c.textbook_id = <ID>
  );
  DELETE FROM paragraphs WHERE chapter_id IN (SELECT id FROM chapters WHERE textbook_id = <ID>);
  DELETE FROM chapters WHERE textbook_id = <ID>;
  DELETE FROM textbooks WHERE id = <ID>;
"
rm -rf uploads/textbook-images/<ID>/
```

---

## Troubleshooting

### Ошибка `is_deleted violates not-null constraint`
Все INSERT должны включать `is_deleted = false`. Скрипт уже это делает.

### Ошибка `duplicate key` или `already exists`
Скрипт идемпотентный (`WHERE NOT EXISTS`). Повторный запуск безопасен. Если нужно перезаписать — сначала удалите (см. выше).

### Формулы не рендерятся
- В контенте должен быть raw LaTeX: `$x^2$`, `$$\int_0^1 x dx$$`
- Student App рендерит через KaTeX на клиенте
- Убедитесь, что URL содержит правильную локаль (`/kz/` для казахского контента)

### Изображения не отображаются
- Проверьте, что файлы скопированы в `uploads/textbook-images/<ID>/`
- Проверьте, что Docker volume `./uploads:/app/uploads` прописан в `docker-compose.infra.yml`
- Пути в контенте должны быть `/uploads/textbook-images/<ID>/img_001.jpg`
- Student App конвертирует относительные URL (`/uploads/...`) в абсолютные (`https://api.ai-mentor.kz/uploads/...`) через `renderMathInHtml()` в `MathText.tsx`
- Проверьте доступность: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8020/uploads/textbook-images/<ID>/img_001.jpg` (ожидаем 200)

### Параграфы определяются неправильно
- Проверьте `--dry-run` вывод
- Настройте `INTERNAL_HEADINGS` если внутренние заголовки (Мысал, A, B, C) определяются как границы параграфов
- Настройте `RE_PARAGRAPH`, `RE_CHAPTER` если формат заголовков отличается

---

## Режимы скрипта

| Флаг | Назначение |
|------|-----------|
| `--dry-run` | Только парсинг, показывает статистику (без записи в БД) |
| `--generate-sql FILE` | Генерация SQL для импорта учебника (главы, параграфы, контент) |
| `--exercises FILE` | Генерация SQL для импорта упражнений (задачи A/B/C с ответами) |
| `--update-content FILE` | Генерация SQL UPDATE для перегенерации HTML в существующих записях |
| без флагов | Прямой импорт через SQLAlchemy (требует доступ к БД) |

---

## Файлы

| Файл | Назначение |
|------|-----------|
| `scripts/load_algebra9_textbook.py` | Скрипт загрузки |
| `uploads/textbook-images/<ID>/` | Изображения учебника |
| `student-app/src/components/common/MathText.tsx` | KaTeX рендеринг + конвертация URL картинок (`renderMathInHtml`) |
