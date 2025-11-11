# Session Log: Add key_terms and questions Fields to Paragraphs

**Дата:** 2025-11-11
**Время:** 07:02
**Задача:** Добавить поля key_terms (массив строк) и questions (массив объектов) в таблицу paragraphs

---

## Требования

### 1. КЛЮЧЕВЫЕ СЛОВА - key_terms
- **Тип:** `string[]` (JSON array of strings)
- **Пример:**
  ```json
  ["Жоңғар хандығы", "Аңырақай шайқасы", "Батыр"]
  ```

### 2. ВОПРОСЫ - questions
- **Тип:** `Question[]` (JSON array of objects)
- **Структура объекта Question:**
  ```typescript
  {
    order: number
    text: string
  }
  ```
- **Пример:**
  ```json
  [
    { "order": 1, "text": "Ақтабан шұбырынды оқиғасы қай жылы болды?" },
    { "order": 2, "text": "Жоңғар шапқыншылығына қарсы күреске кімдер қатысты?" }
  ]
  ```

---

## Анализ существующей архитектуры

### Текущая структура Paragraph модели
- **Существующие поля:** chapter_id, title, number, order, content, summary, learning_objective, lesson_objective
- **Системные поля:** id, created_at, updated_at, deleted_at, is_deleted
- **Базовый класс:** SoftDeleteModel

### Паттерны использования JSON в проекте
В проекте уже используется JSON тип PostgreSQL:
- `test_attempt_answers.selected_option_ids` - JSON массив
- `learning_activities.activity_metadata` - JSON объект
- `sync_queue.data` - JSON объект
- `analytics_events.event_data` - JSON объект

**Паттерн:**
- SQLAlchemy: `Column(JSON, nullable=True)`
- Pydantic: `List[str]` или кастомная модель
- Миграция: импорт из `sqlalchemy.dialects.postgresql import JSON`

---

## Выполненные изменения

### 1. Pydantic схемы

**Файл:** `backend/app/schemas/paragraph.py`

**Добавлен новый класс:**
```python
class ParagraphQuestion(BaseModel):
    """Schema for paragraph question."""

    order: int = Field(..., ge=1, description="Question order/number")
    text: str = Field(..., min_length=1, description="Question text")
```

**Обновлены существующие схемы:**
- `ParagraphCreate` - добавлены поля для создания
- `ParagraphUpdate` - добавлены поля для обновления
- `ParagraphResponse` - добавлены поля для ответа
- `ParagraphListResponse` - добавлены поля для списка

**Новые поля:**
```python
key_terms: Optional[List[str]] = Field(None, description="Array of key terms")
questions: Optional[List[ParagraphQuestion]] = Field(None, description="Array of questions")
```

### 2. SQLAlchemy модель

**Файл:** `backend/app/models/paragraph.py`

**Изменения:**
```python
# Добавлен импорт
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON

# Добавлены столбцы
class Paragraph(SoftDeleteModel):
    # ... existing fields ...
    key_terms = Column(JSON, nullable=True)  # Array of key terms
    questions = Column(JSON, nullable=True)  # Array of questions {order, text}
```

### 3. Alembic миграция

**Файл:** `backend/alembic/versions/011_add_key_terms_and_questions_to_paragraphs.py`

**Создана новая миграция:**
- **Revision ID:** 011
- **Revises:** 010
- **Create Date:** 2025-11-11

**Upgrade:**
```python
def upgrade() -> None:
    op.add_column('paragraphs', sa.Column('key_terms', JSON, nullable=True))
    op.add_column('paragraphs', sa.Column('questions', JSON, nullable=True))
```

**Downgrade:**
```python
def downgrade() -> None:
    op.drop_column('paragraphs', 'questions')
    op.drop_column('paragraphs', 'key_terms')
```

### 4. Документация

**Файл:** `docs/database_schema.md`

**Обновлена таблица "10. paragraphs (Параграфы)":**

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| key_terms | JSON | Нет | Массив ключевых терминов (например: ["Жоңғар хандығы", "Батыр"]) |
| questions | JSON | Нет | Массив вопросов (например: [{"order": 1, "text": "..."}]) |

### 5. Применение миграции

**База данных:** Production PostgreSQL (ai_mentor_postgres_prod)

**Команды:**
```sql
ALTER TABLE paragraphs ADD COLUMN key_terms JSON;
ALTER TABLE paragraphs ADD COLUMN questions JSON;
UPDATE alembic_version SET version_num = '011';
```

**Результат:**
```
 key_terms | json |  |
 questions | json |  |
```

---

## Результаты

### Структура БД обновлена
Таблица `paragraphs` теперь содержит:
- ✅ `key_terms` (JSON, nullable)
- ✅ `questions` (JSON, nullable)
- ✅ Alembic версия: 011

### API endpoints автоматически поддерживают новые поля
Все существующие endpoints работают с новыми полями:
- ✅ `POST /api/v1/admin/global/paragraphs` - создание с key_terms и questions
- ✅ `PUT /api/v1/admin/global/paragraphs/{id}` - обновление
- ✅ `GET /api/v1/admin/global/paragraphs/{id}` - получение
- ✅ `GET /api/v1/admin/global/chapters/{id}/paragraphs` - список
- ✅ `POST /api/v1/admin/school/paragraphs` - создание школьного контента
- ✅ `PUT /api/v1/admin/school/paragraphs/{id}` - обновление школьного контента

### Пример использования API

**Request:**
```json
POST /api/v1/admin/global/paragraphs
{
  "chapter_id": 5,
  "title": "Жоңғар шапқыншылығы",
  "number": 1,
  "order": 1,
  "content": "XVIII ғасырдың басында...",
  "summary": "Жоңғар шапқыншылығы және қазақ халқының қарсылық көрсетуі",
  "key_terms": [
    "Жоңғар хандығы",
    "Аңырақай шайқасы",
    "Батыр"
  ],
  "questions": [
    {
      "order": 1,
      "text": "Ақтабан шұбырынды оқиғасы қай жылы болды?"
    },
    {
      "order": 2,
      "text": "Жоңғар шапқыншылығына қарсы күреске кімдер қатысты?"
    }
  ]
}
```

**Response:**
```json
{
  "id": 42,
  "chapter_id": 5,
  "title": "Жоңғар шапқыншылығы",
  "number": 1,
  "order": 1,
  "content": "XVIII ғасырдың басында...",
  "summary": "Жоңғар шапқыншылығы және қазақ халқының қарсылық көрсетуі",
  "learning_objective": null,
  "lesson_objective": null,
  "key_terms": ["Жоңғар хандығы", "Аңырақай шайқасы", "Батыр"],
  "questions": [
    {"order": 1, "text": "Ақтабан шұбырынды оқиғасы қай жылы болды?"},
    {"order": 2, "text": "Жоңғар шапқыншылығына қарсы күреске кімдер қатысты?"}
  ],
  "created_at": "2025-11-11T07:00:00Z",
  "updated_at": "2025-11-11T07:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

## Затронутые файлы

1. ✅ `backend/app/schemas/paragraph.py` - Pydantic схемы
2. ✅ `backend/app/models/paragraph.py` - SQLAlchemy модель
3. ✅ `backend/alembic/versions/011_add_key_terms_and_questions_to_paragraphs.py` - миграция
4. ✅ `docs/database_schema.md` - документация
5. ✅ Production БД - применена миграция

---

## Выводы

### Преимущества реализации
1. **Минимальные изменения:** API endpoints не требуют модификации - новые поля автоматически работают через Pydantic схемы
2. **Гибкость:** JSON формат позволяет легко добавлять новые ключевые термины и вопросы без изменения схемы БД
3. **Обратная совместимость:** Поля nullable, существующие параграфы не затронуты
4. **Следование паттернам:** Использован существующий паттерн JSON полей из проекта

### Готовность к использованию
- ✅ Backend модели обновлены
- ✅ Pydantic валидация настроена
- ✅ БД миграция применена
- ✅ Документация актуальна
- ✅ API endpoints готовы к приему данных

**Статус:** Реализация завершена успешно. Готово к тестированию и использованию.
