# Медиа-слой для тестов, вопросов и учебного контента

**Статус:** 🔮 PLANNED (после Итерации 12)

**Дата проектирования:** 2025-10-30

**Оценка сложности внедрения:** 1 рабочий день (миграция + модели + API)

**Риски:** Низкие (только additive changes, zero breaking changes)

---

## Цель

Добавить поддержку изображений и анимаций к тестам, вопросам и параграфам учебников с обеспечением:
- Масштабируемости (много медиа на одну сущность)
- Упорядочивания медиа
- Типизации (изображения, видео, анимации)
- Возможности генерации изображений по текстовым промптам

---

## Где прикрепляются медиа

### Простые медиа-поля (одно медиа на сущность)

**Для верхнеуровневых сущностей** - простые nullable поля:

- **`textbooks`**: обложка
  - `cover_image_url` (String 1000)
  - `cover_image_alt` (String 255)
  - `cover_image_attribution` (String 255)

- **`chapters`**: герой-картинка для шапки
  - `hero_image_url` (String 1000)
  - `hero_image_alt` (String 255)
  - `hero_image_attribution` (String 255)

- **`tests`**: вступительная картинка
  - `intro_image_url` (String 1000)
  - `intro_image_alt` (String 255)

- **`question_options`**: картинка в варианте ответа
  - `image_url` (String 1000)
  - `image_alt` (String 255)

### Множественные медиа (N:1 relationship)

**Для детального контента** - отдельные таблицы:

- **`question_media`** (N:1 к `questions`)
  - Иллюстрации стема вопроса
  - Визуальные подсказки
  - Анимации/диаграммы

- **`paragraph_media`** (N:1 к `paragraphs`)
  - Объясняющие иллюстрации
  - Схемы и диаграммы
  - Обучающие анимации

---

## Дизайн таблиц *_media

### Структура (общая для question_media и paragraph_media)

```sql
CREATE TYPE mediatype AS ENUM ('image', 'animation', 'video', 'lottie');

CREATE TABLE question_media (
  -- Primary key
  id SERIAL PRIMARY KEY,

  -- Relationships (CASCADE DELETE)
  question_id INT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,

  -- Ordering
  "order" INT NOT NULL DEFAULT 0,

  -- Media type and URL
  media_type mediatype NOT NULL,
  url VARCHAR(1000) NOT NULL,

  -- Accessibility and metadata
  alt_text VARCHAR(255),
  caption TEXT,
  attribution VARCHAR(255),

  -- Video-specific
  poster_url VARCHAR(1000),

  -- Dimensions (optional)
  width INT,
  height INT,

  -- Flexible metadata (JSONB for performance)
  metadata JSONB,

  -- AI Generation tracking
  generation_prompt TEXT,
  generation_metadata JSONB,

  -- Standard soft-delete fields
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ
);

-- Composite index for efficient queries
CREATE INDEX ix_question_media_question_id_order
  ON question_media (question_id, "order");

CREATE TABLE paragraph_media (
  id SERIAL PRIMARY KEY,
  paragraph_id INT NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
  "order" INT NOT NULL DEFAULT 0,
  media_type mediatype NOT NULL,
  url VARCHAR(1000) NOT NULL,
  alt_text VARCHAR(255),
  caption TEXT,
  attribution VARCHAR(255),
  poster_url VARCHAR(1000),
  width INT,
  height INT,
  metadata JSONB,
  generation_prompt TEXT,
  generation_metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ
);

CREATE INDEX ix_paragraph_media_paragraph_id_order
  ON paragraph_media (paragraph_id, "order");
```

### Поля - подробное описание

| Поле | Тип | Назначение |
|------|-----|------------|
| `order` | Integer | Порядок отображения медиа (0, 1, 2...) |
| `media_type` | Enum | Тип: image, animation, video, lottie |
| `url` | String(1000) | Ссылка на S3/CDN/объектное хранилище |
| `alt_text` | String(255) | Accessibility (screen readers) + SEO |
| `caption` | Text | Подпись под медиа для пользователей |
| `attribution` | String(255) | Автор/источник/лицензия (copyright) |
| `poster_url` | String(1000) | Poster frame для видео/анимаций |
| `width`, `height` | Integer | Размеры для aspect ratio preservation |
| `metadata` | JSONB | Произвольные метаданные: цветовой профиль, трансформации, EXIF, лицензия |
| `generation_prompt` | Text | Промпт, использованный для AI-генерации |
| `generation_metadata` | JSONB | Модель, параметры, сид, версия, timestamp генерации |

### Почему JSONB, а не JSON?

**PostgreSQL JSONB:**
- Индексирование по вложенным полям
- GIN индексы для быстрого поиска
- Бинарный формат = меньше памяти
- Поддержка операторов `@>`, `?`, `?&`, `?|`

```sql
-- Пример: найти все медиа, сгенерированные DALL-E 3
SELECT * FROM question_media
WHERE generation_metadata @> '{"model": "dall-e-3"}';
```

---

## SQLAlchemy модели

```python
# backend/app/models/media.py
import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import SoftDeleteModel


class MediaType(str, enum.Enum):
    """Media type enumeration."""
    IMAGE = "image"
    ANIMATION = "animation"
    VIDEO = "video"
    LOTTIE = "lottie"


class QuestionMedia(SoftDeleteModel):
    """Media attached to questions (multiple per question)."""

    __tablename__ = "question_media"

    # Relationships
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Ordering
    order = Column(Integer, nullable=False, default=0)

    # Media info
    media_type = Column(SQLEnum(MediaType), nullable=False)
    url = Column(String(1000), nullable=False)

    # Accessibility
    alt_text = Column(String(255), nullable=True)
    caption = Column(Text, nullable=True)
    attribution = Column(String(255), nullable=True)

    # Video-specific
    poster_url = Column(String(1000), nullable=True)

    # Dimensions
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    # Flexible metadata
    metadata = Column(JSONB, nullable=True)

    # AI generation tracking
    generation_prompt = Column(Text, nullable=True)
    generation_metadata = Column(JSONB, nullable=True)

    # Relationships
    question = relationship("Question", back_populates="media")

    def __repr__(self) -> str:
        return f"<QuestionMedia(id={self.id}, question_id={self.question_id}, type={self.media_type})>"


class ParagraphMedia(SoftDeleteModel):
    """Media attached to paragraphs (multiple per paragraph)."""

    __tablename__ = "paragraph_media"

    # Relationships
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)

    # Ordering
    order = Column(Integer, nullable=False, default=0)

    # Media info
    media_type = Column(SQLEnum(MediaType), nullable=False)
    url = Column(String(1000), nullable=False)

    # Accessibility
    alt_text = Column(String(255), nullable=True)
    caption = Column(Text, nullable=True)
    attribution = Column(String(255), nullable=True)

    # Video-specific
    poster_url = Column(String(1000), nullable=True)

    # Dimensions
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    # Flexible metadata
    metadata = Column(JSONB, nullable=True)

    # AI generation tracking
    generation_prompt = Column(Text, nullable=True)
    generation_metadata = Column(JSONB, nullable=True)

    # Relationships
    paragraph = relationship("Paragraph", back_populates="media")

    def __repr__(self) -> str:
        return f"<ParagraphMedia(id={self.id}, paragraph_id={self.paragraph_id}, type={self.media_type})>"
```

### Обновление существующих моделей

```python
# backend/app/models/textbook.py
class Textbook(SoftDeleteModel):
    # ... existing fields ...

    # 🆕 Cover image
    cover_image_url = Column(String(1000), nullable=True)
    cover_image_alt = Column(String(255), nullable=True)
    cover_image_attribution = Column(String(255), nullable=True)


# backend/app/models/chapter.py
class Chapter(SoftDeleteModel):
    # ... existing fields ...

    # 🆕 Hero image
    hero_image_url = Column(String(1000), nullable=True)
    hero_image_alt = Column(String(255), nullable=True)
    hero_image_attribution = Column(String(255), nullable=True)


# backend/app/models/test.py
class Test(SoftDeleteModel):
    # ... existing fields ...

    # 🆕 Intro image
    intro_image_url = Column(String(1000), nullable=True)
    intro_image_alt = Column(String(255), nullable=True)


class Question(SoftDeleteModel):
    # ... existing fields ...

    # 🆕 Relationship to media
    media = relationship("QuestionMedia", back_populates="question",
                        cascade="all, delete-orphan", order_by="QuestionMedia.order")


class QuestionOption(SoftDeleteModel):
    # ... existing fields ...

    # 🆕 Image in answer option
    image_url = Column(String(1000), nullable=True)
    image_alt = Column(String(255), nullable=True)


# backend/app/models/paragraph.py
class Paragraph(SoftDeleteModel):
    # ... existing fields ...

    # 🆕 Relationship to media
    media = relationship("ParagraphMedia", back_populates="paragraph",
                        cascade="all, delete-orphan", order_by="ParagraphMedia.order")
```

---

## Хранение и форматы файлов

### Принцип: БД хранит только метаданные, файлы - в объектном хранилище

**Архитектура:**
```
User Upload → FastAPI → S3/MinIO → CDN → Frontend
                ↓
            PostgreSQL (metadata only)
```

### Рекомендуемые форматы

| Тип | Формат | Комментарий |
|-----|--------|-------------|
| Изображения | WebP (default) | Лучшая компрессия, широкая поддержка |
| Изображения | PNG | Для графики с прозрачностью |
| Изображения | JPEG | Для фотографий |
| Анимации | MP4/WebM | Предпочтительнее GIF (меньше размер) |
| Анимации | GIF | В крайних случаях (legacy support) |
| Векторная анимация | Lottie JSON | Легкие анимации (JSON-файл по URL) |
| Видео | MP4 (H.264) | Максимальная совместимость |

### Оптимизация изображений

**При загрузке автоматически создавать варианты:**
```python
# Пример metadata в JSONB
{
  "original": {
    "width": 2048,
    "height": 1536,
    "size_bytes": 856432,
    "format": "png"
  },
  "variants": {
    "thumbnail": "https://cdn.example.com/img_thumb.webp",
    "medium": "https://cdn.example.com/img_medium.webp",
    "large": "https://cdn.example.com/img_large.webp"
  },
  "color_profile": "sRGB",
  "exif": { ... }
}
```

---

## AI-генерация изображений

### Поддержка через поля generation_*

**Процесс генерации:**
```
1. Текст/промпт → AI модель (OpenAI DALL-E / Stability AI / Midjourney)
2. Сгенерированное изображение → загрузка в S3
3. Метаданные → запись в *_media таблицу
```

### Пример generation_metadata

```json
{
  "model": "dall-e-3",
  "parameters": {
    "size": "1024x1024",
    "quality": "standard",
    "style": "natural"
  },
  "seed": 42,
  "timestamp": "2025-10-30T12:34:56Z",
  "version": "1.0",
  "cost_usd": 0.04
}
```

### API endpoint (пример)

```python
@router.post("/questions/{question_id}/media/generate")
async def generate_question_media(
    question_id: int,
    prompt: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    # 1. Генерация через OpenAI
    response = await openai_client.images.generate(
        prompt=prompt,
        model="dall-e-3",
        size="1024x1024"
    )

    # 2. Загрузка в S3
    image_url = response.data[0].url
    s3_url = await upload_generated_image_to_s3(image_url, question_id)

    # 3. Сохранение в БД
    media = QuestionMedia(
        question_id=question_id,
        media_type=MediaType.IMAGE,
        url=s3_url,
        generation_prompt=prompt,
        generation_metadata={
            "model": "dall-e-3",
            "timestamp": datetime.utcnow().isoformat(),
            "revised_prompt": response.data[0].revised_prompt
        }
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)

    return media
```

### Кеширование по хешу промпта

**Избегать повторной генерации:**
```python
import hashlib

def get_prompt_hash(prompt: str, model: str, params: dict) -> str:
    data = f"{prompt}|{model}|{json.dumps(params, sort_keys=True)}"
    return hashlib.sha256(data.encode()).hexdigest()

# Проверка кеша перед генерацией
prompt_hash = get_prompt_hash(prompt, "dall-e-3", {"size": "1024x1024"})
existing = await db.execute(
    select(QuestionMedia)
    .where(QuestionMedia.generation_metadata["prompt_hash"].astext == prompt_hash)
)
if existing.scalar_one_or_none():
    return existing  # Переиспользуем
```

### Модерация контента

**OpenAI Content Policy:**
- Автоматическая модерация через OpenAI Moderation API
- Хранить результаты в `metadata.moderation`
- Блокировать unsafe контент

```python
# Перед генерацией
moderation = await openai_client.moderations.create(input=prompt)
if moderation.results[0].flagged:
    raise HTTPException(400, "Prompt violates content policy")
```

---

## Причины такого дизайна

### ✅ Преимущества

1. **Масштабируемость и гибкость**
   - Любое количество медиа на сущность
   - Упорядочивание через `order`
   - Типизация через enum `MediaType`

2. **Производительность**
   - Индексы по (owner_id, order)
   - JSONB для гибких метаданных + ин��ексирование
   - Файлы вне БД (только URL)
   - CDN для быстрой доставки

3. **Простота интеграции на фронтенде**
   - Предсказуемый контракт API
   - Сортировка по `order` из коробки
   - Опциональные поля = обратная совместимость

4. **Accessibility & SEO**
   - `alt_text` для screen readers
   - `caption` для контекста
   - Structured data для поисковиков

5. **Audit trail для AI-генерации**
   - Промпт сохранен → воспроизводимость
   - Метаданные модели → версионирование
   - Кеширование по хешу → экономия

6. **Будущая расширяемость**
   - Легко добавить новые `media_type`
   - Можно вынести в общую таблицу `assets` при росте
   - Миграция к единой "медиатеке" тривиальна

---

## Поэтапный план внедрения

### Фаза 1: Минимальные медиа (1 день)

**Что:** Простые URL-поля для "одно медиа на сущность"

**Миграция:**
```sql
-- Textbooks
ALTER TABLE textbooks ADD COLUMN cover_image_url VARCHAR(1000);
ALTER TABLE textbooks ADD COLUMN cover_image_alt VARCHAR(255);
ALTER TABLE textbooks ADD COLUMN cover_image_attribution VARCHAR(255);

-- Chapters
ALTER TABLE chapters ADD COLUMN hero_image_url VARCHAR(1000);
ALTER TABLE chapters ADD COLUMN hero_image_alt VARCHAR(255);
ALTER TABLE chapters ADD COLUMN hero_image_attribution VARCHAR(255);

-- Tests
ALTER TABLE tests ADD COLUMN intro_image_url VARCHAR(1000);
ALTER TABLE tests ADD COLUMN intro_image_alt VARCHAR(255);

-- Question Options
ALTER TABLE question_options ADD COLUMN image_url VARCHAR(1000);
ALTER TABLE question_options ADD COLUMN image_alt VARCHAR(255);
```

**Use case:** Админ вводит URL вручную (Unsplash, собственный сервер)

**Преимущества:**
- ✅ Zero dependencies
- ✅ Zero инфраструктуры
- ✅ Работает сразу

### Фаза 2: Локальное хранилище (3-5 дней)

**Что:** Upload endpoint + локальное хранение или MinIO

**Зависимости:**
- `python-multipart` для file uploads
- `Pillow` для обработки изображений
- MinIO (опционально)

**Endpoints:**
```python
POST /api/v1/media/upload
GET  /api/v1/media/{filename}
```

**Use case:** Админ загружает файлы через UI

### Фаза 3: Множественные медиа (1 неделя)

**Что:** Создание таблиц `question_media` и `paragraph_media`

**Миграция:** Создание таблиц (см. SQL выше)

**Endpoints:**
```python
POST   /api/v1/questions/{id}/media
GET    /api/v1/questions/{id}/media
PATCH  /api/v1/questions/{id}/media/{media_id}
DELETE /api/v1/questions/{id}/media/{media_id}
PUT    /api/v1/questions/{id}/media/reorder  # Изменить order
```

**Use case:** К одному вопросу прикрепить схему + анимацию + подсказку

### Фаза 4: AI-генерация (2 недели)

**Что:** Интеграция с OpenAI DALL-E / Stability AI

**Зависимости:**
- `openai` SDK
- Celery/Dramatiq для async processing
- Redis для queue

**Endpoints:**
```python
POST /api/v1/questions/{id}/media/generate
GET  /api/v1/media/generations/{job_id}/status
```

**Features:**
- Генерация по промпту
- Кеширование по хешу
- Модерация контента
- Retry механизм

---

## Оценка сложности внедрения

### Фаза 1 (рекомендуемая для старта):

| Задача | Время |
|--------|-------|
| Миграция БД (простые поля) | 30 мин |
| Обновление моделей | 30 мин |
| Обновление Pydantic схем | 1 час |
| Обновление endpoints (CRUD) | 2 часа |
| Тесты | 2 часа |
| Документация | 1 час |
| **ИТОГО** | **~1 день** |

### Полная реализация (все 4 фазы):

| Фаза | Время |
|------|-------|
| Фаза 1: Простые поля | 1 день |
| Фаза 2: Локальное хранилище | 3-5 дней |
| Фаза 3: Множественные медиа | 1 неделя |
| Фаза 4: AI-генерация | 2 недели |
| **ИТОГО** | **~4 недели** |

---

## Риски и миграция

### ✅ Почему это безопасно внедрять ПОСЛЕ MVP:

1. **Additive changes only:**
   - Все новые поля - nullable
   - Новые таблицы не затрагивают существующие
   - Zero breaking changes для API

2. **Тривиальная миграция БД:**
   ```sql
   ALTER TABLE textbooks ADD COLUMN cover_image_url VARCHAR(1000);
   ```
   - Мгновенная операция в PostgreSQL
   - Не требует rewrite таблицы
   - Rollback через transactional DDL

3. **Обратная совместимость API:**
   ```python
   # Старые клиенты игнорируют новые поля
   class TextbookResponse(BaseModel):
       id: int
       title: str
       cover_image_url: str | None = None  # Опционально!
   ```

4. **Frontend изменения incremental:**
   - Старый код продолжает работать
   - Новые фичи добавляются условно

### ❌ Что НЕ является нашим случаем (сложные миграции):

- Изменение PRIMARY KEY
- Разбиение таблицы (vertical partitioning)
- Изменение типа relationship (one-to-many → many-to-many)
- Data migration с трансформацией

---

## Зависимости для полной реализации

### Python packages:

```toml
# pyproject.toml
[tool.poetry.dependencies]
# Фаза 2
python-multipart = "^0.0.6"  # File uploads
Pillow = "^10.0.0"            # Image processing

# Фаза 2 (если MinIO)
boto3 = "^1.28.0"             # S3-compatible client
minio = "^7.1.0"              # MinIO client

# Фаза 4
openai = "^1.3.0"             # AI generation
celery = "^5.3.0"             # Async tasks
redis = "^5.0.0"              # Queue backend
```

### Infrastructure:

- **Storage:** S3 / MinIO / Local filesystem
- **CDN:** CloudFront / Cloudflare (опционально)
- **Queue:** Redis + Celery (для AI генерации)
- **Модерация:** OpenAI Moderation API

---

## Рекомендации

### ✅ Делать:

1. **Начинать с Фазы 1** после завершения всех 12 итераций
2. **Внедрять поэтапно** по мере появления реальных потребностей
3. **Валидировать на реальных данных** перед инвестициями в инфраструктуру
4. **Использовать JSONB** вместо JSON для метаданных
5. **Всегда добавлять alt_text** для accessibility

### ❌ Не делать:

1. **Не внедрять до завершения MVP** (core features важнее)
2. **Не хранить бинарные данные в PostgreSQL**
3. **Не делать over-engineering** (единая таблица `assets` на старте не нужна)
4. **Не пропускать модерацию** для AI-генерации

---

## Альтернативы и trade-offs

### Вариант А: Единая таблица `assets` (отклонен)

**Плюсы:**
- Централизованное управление медиа
- Легче добавлять новые типы владельцев

**Минусы:**
- Over-engineering для MVP
- Сложнее делать CASCADE DELETE
- Нужен polymorphic pattern (owner_type, owner_id)

**Вердикт:** Отложить до масштабирования (если > 5 типов владельцев)

### Вариант Б: NoSQL для медиа (отклонен)

**Плюсы:**
- Гибкость схемы
- Горизонтальное масштабирование

**Минусы:**
- Дополнительная БД в стеке
- Потеря транзакционности
- Сложнее делать JOIN с основными данными

**Вердикт:** PostgreSQL JSONB покрывает все потребности

---

## Примеры использования

### Frontend (React/Vue)

```typescript
// Отображение обложки учебника
<img
  src={textbook.cover_image_url}
  alt={textbook.cover_image_alt}
  loading="lazy"
/>

// Отображение множественных медиа в вопросе
{question.media?.sort((a, b) => a.order - b.order).map(media => (
  <MediaViewer
    key={media.id}
    type={media.media_type}
    url={media.url}
    alt={media.alt_text}
    caption={media.caption}
  />
))}
```

### API Response

```json
{
  "id": 123,
  "question_text": "Найдите площадь фигуры:",
  "media": [
    {
      "id": 1,
      "order": 0,
      "media_type": "image",
      "url": "https://cdn.example.com/figures/triangle.webp",
      "alt_text": "Прямоугольный треугольник с катетами 3 и 4",
      "caption": "Рис. 1: Исходная фигура",
      "width": 800,
      "height": 600
    },
    {
      "id": 2,
      "order": 1,
      "media_type": "animation",
      "url": "https://cdn.example.com/animations/solution.mp4",
      "poster_url": "https://cdn.example.com/animations/solution_poster.jpg",
      "alt_text": "Анимация решения задачи",
      "caption": "Подсказка: смотри анимацию"
    }
  ]
}
```

---

## Контрольный чеклист перед внедрением

- [ ] Все 12 итераций MVP завершены
- [ ] Core features протестированы в продакшене
- [ ] Появился реальный запрос от пользователей на медиа
- [ ] Определено объектное хранилище (S3/MinIO/Local)
- [ ] Настроен CDN (опционально, но желательно)
- [ ] Выделен бюджет на AI-генерацию (если нужна Фаза 4)
- [ ] Подготовлены guidelines для accessibility (alt-тексты)
- [ ] Настроена модерация контента

---

## Связанные документы

- [ARCHITECTURE.md](./ARCHITECTURE.md) - общая архитектура проекта
- [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) - план итераций
- [database_schema.md](./database_schema.md) - текущая схема БД

---

**Последнее обновление:** 2025-10-30

**Автор:** AI Mentor Team + Claude Code

**Статус:** PLANNED (ожидает завершения Итерации 12)
