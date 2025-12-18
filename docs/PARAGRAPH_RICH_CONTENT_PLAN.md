# План реализации: Обогащённый контент параграфов

**Дата:** 2025-12-18
**Статус:** Этапы 1-3 завершены, Этап 4 в ожидании
**Цель:** Добавить возможность прикреплять к параграфам "объясняющий" текст, аудио, слайды, видео и карточки для улучшения учебного опыта школьников.

---

## Общая концепция

Для каждого параграфа учебника создаётся "обогащённый" контент:

| Формат | Описание | Источник на MVP |
|--------|----------|-----------------|
| **Объяснение** | Переработанный текст простыми словами | Ручной ввод |
| **Аудио** | MP3 озвучка объяснения | Загрузка готового (Narakeet) |
| **Слайды** | PDF/PPTX презентация | Загрузка готового |
| **Видео** | MP4 (слайды + озвучка) | Загрузка готового (Narakeet) |
| **Карточки** | Флеш-карточки для повторения | Ручной ввод в админке |

**Языки:** Русский (ru) и Казахский (kk) — отдельные записи для каждого языка.

---

## Архитектура

### Схема данных

```
┌─────────────────┐
│   paragraphs    │ (существующая таблица)
│                 │
│ - content       │ ← "сырой" книжный текст
│ - summary       │
│ - key_terms     │
└────────┬────────┘
         │ 1:N (по языкам)
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   paragraph_contents                         │
│                                                              │
│ - paragraph_id (FK)                                          │
│ - language (ru/kk)                                           │
│ - explain_text (объяснение)                                  │
│ - audio_url, slides_url, video_url (ссылки на файлы)        │
│ - cards (JSONB)                                              │
│ - source_hash (для отслеживания изменений)                  │
│ - status_* (статусы по типам контента)                      │
└─────────────────────────────────────────────────────────────┘
```

### Хранение файлов

```
/uploads/paragraph-contents/
├── {paragraph_id}/
│   ├── ru/
│   │   ├── audio.mp3
│   │   ├── slides.pdf
│   │   └── video.mp4
│   └── kk/
│       ├── audio.mp3
│       ├── slides.pdf
│       └── video.mp4
```

**MVP:** Локальное хранилище (`/var/www/uploads/`)
**Продакшен:** MinIO/S3 (добавить позже)

---

## Этапы реализации

---

## Этап 1: База данных и модели

**Цель:** Создать таблицу `paragraph_contents` и SQLAlchemy модель.

### 1.1. Создание миграции

**Файл:** `backend/alembic/versions/xxx_add_paragraph_contents.py`

```sql
CREATE TABLE paragraph_contents (
    id SERIAL PRIMARY KEY,
    paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    language VARCHAR(2) NOT NULL DEFAULT 'ru',

    -- Основной контент
    explain_text TEXT,

    -- Медиа (ссылки на файлы)
    audio_url TEXT,
    slides_url TEXT,
    video_url TEXT,

    -- Карточки
    cards JSONB,

    -- Метаданные
    source_hash VARCHAR(64),
    status_explain VARCHAR(20) DEFAULT 'empty',
    status_audio VARCHAR(20) DEFAULT 'empty',
    status_slides VARCHAR(20) DEFAULT 'empty',
    status_video VARCHAR(20) DEFAULT 'empty',
    status_cards VARCHAR(20) DEFAULT 'empty',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_paragraph_content_language UNIQUE (paragraph_id, language),
    CONSTRAINT chk_language CHECK (language IN ('ru', 'kk'))
);

CREATE INDEX ix_paragraph_contents_paragraph_id ON paragraph_contents(paragraph_id);
```

### 1.2. SQLAlchemy модель

**Файл:** `backend/app/models/paragraph_content.py`

```python
class ContentStatus(str, Enum):
    EMPTY = "empty"
    DRAFT = "draft"
    READY = "ready"
    OUTDATED = "outdated"

class ParagraphContent(BaseModel):
    __tablename__ = "paragraph_contents"

    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(2), nullable=False, default="ru")

    explain_text = Column(Text, nullable=True)
    audio_url = Column(Text, nullable=True)
    slides_url = Column(Text, nullable=True)
    video_url = Column(Text, nullable=True)
    cards = Column(JSONB, nullable=True)

    source_hash = Column(String(64), nullable=True)
    status_explain = Column(String(20), default="empty")
    status_audio = Column(String(20), default="empty")
    status_slides = Column(String(20), default="empty")
    status_video = Column(String(20), default="empty")
    status_cards = Column(String(20), default="empty")

    # Relationships
    paragraph = relationship("Paragraph", back_populates="contents")

    __table_args__ = (
        UniqueConstraint('paragraph_id', 'language', name='uq_paragraph_content_language'),
    )
```

### 1.3. Pydantic схемы

**Файл:** `backend/app/schemas/paragraph_content.py`

```python
class CardItem(BaseModel):
    id: str  # UUID
    type: Literal["term", "fact", "check"]
    front: str
    back: str
    order: int

class ParagraphContentCreate(BaseModel):
    language: Literal["ru", "kk"] = "ru"
    explain_text: str | None = None

class ParagraphContentUpdate(BaseModel):
    explain_text: str | None = None
    cards: list[CardItem] | None = None

class ParagraphContentResponse(BaseModel):
    id: int
    paragraph_id: int
    language: str
    explain_text: str | None
    audio_url: str | None
    slides_url: str | None
    video_url: str | None
    cards: list[CardItem] | None
    source_hash: str | None
    status_explain: str
    status_audio: str
    status_slides: str
    status_video: str
    status_cards: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### Задачи этапа 1:

- [x] Создать файл модели `backend/app/models/paragraph_content.py`
- [x] Добавить import в `backend/app/models/__init__.py`
- [x] Добавить relationship в модель `Paragraph`
- [x] Создать миграцию: `backend/alembic/versions/014_add_paragraph_contents.py`
- [x] Проверить и отредактировать миграцию (добавлены RLS политики)
- [x] Применить миграцию на production БД
- [x] Создать Pydantic схемы `backend/app/schemas/paragraph_content.py`
- [x] Добавить export в `backend/app/schemas/__init__.py`

**Выполнено:** 2025-12-18

---

## Этап 2: Backend API

**Цель:** Создать CRUD endpoints и загрузку файлов.

### 2.1. Repository

**Файл:** `backend/app/repositories/paragraph_content_repo.py`

Методы:
- `get_by_paragraph_and_language(paragraph_id, language)` → ParagraphContent | None
- `get_or_create(paragraph_id, language)` → ParagraphContent
- `update(content_id, data)` → ParagraphContent
- `update_media_url(content_id, media_type, url)` → ParagraphContent
- `delete_media(content_id, media_type)` → bool

### 2.2. API Endpoints

**Файл:** `backend/app/api/v1/paragraph_contents.py`

```
# Получение контента
GET  /api/v1/paragraphs/{paragraph_id}/content?language=ru
     → ParagraphContentResponse (или 404 если нет)

# Создание/обновление объяснения
PUT  /api/v1/paragraphs/{paragraph_id}/content
     Body: { language: "ru", explain_text: "..." }
     → ParagraphContentResponse

# Загрузка медиа файлов
POST /api/v1/paragraphs/{paragraph_id}/content/audio?language=ru
     Body: multipart/form-data (file)
     → { audio_url: "/uploads/...", status_audio: "ready" }

POST /api/v1/paragraphs/{paragraph_id}/content/slides?language=ru
     Body: multipart/form-data (file)
     → { slides_url: "/uploads/...", status_slides: "ready" }

POST /api/v1/paragraphs/{paragraph_id}/content/video?language=ru
     Body: multipart/form-data (file)
     → { video_url: "/uploads/...", status_video: "ready" }

# Удаление медиа
DELETE /api/v1/paragraphs/{paragraph_id}/content/audio?language=ru
DELETE /api/v1/paragraphs/{paragraph_id}/content/slides?language=ru
DELETE /api/v1/paragraphs/{paragraph_id}/content/video?language=ru

# Карточки (CRUD внутри контента)
PUT  /api/v1/paragraphs/{paragraph_id}/content/cards?language=ru
     Body: { cards: [...] }
     → ParagraphContentResponse
```

### 2.3. Сервис загрузки файлов

**Файл:** `backend/app/services/paragraph_content_service.py`

```python
class ParagraphContentService:
    ALLOWED_AUDIO = {".mp3", ".ogg", ".wav"}
    ALLOWED_SLIDES = {".pdf", ".pptx"}
    ALLOWED_VIDEO = {".mp4", ".webm"}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    async def upload_media(
        self,
        paragraph_id: int,
        language: str,
        media_type: str,  # audio|slides|video
        file: UploadFile
    ) -> str:
        """Сохраняет файл и возвращает URL."""
        ...

    async def delete_media(
        self,
        paragraph_id: int,
        language: str,
        media_type: str
    ) -> bool:
        """Удаляет файл с диска."""
        ...

    def calculate_source_hash(self, paragraph: Paragraph) -> str:
        """SHA256 от content + summary + learning_objective."""
        ...

    def check_outdated(
        self,
        content: ParagraphContent,
        paragraph: Paragraph
    ) -> bool:
        """Проверяет, устарел ли контент."""
        ...
```

### 2.4. Настройка статики

**Файл:** `backend/app/main.py`

```python
from fastapi.staticfiles import StaticFiles

app.mount("/uploads", StaticFiles(directory="/var/www/uploads"), name="uploads")
```

### Задачи этапа 2:

- [x] Создать repository `backend/app/repositories/paragraph_content_repo.py`
- [x] Создать service `backend/app/services/paragraph_content_service.py`
- [x] Создать API router `backend/app/api/v1/paragraph_contents.py`
- [x] Подключить router в `backend/app/main.py`
- [x] Настроить директорию uploads и статику (уже было настроено)
- [x] Задеплоить backend на production
- [x] Протестировать CRUD операции (explain_text, cards)
- [x] Протестировать загрузку файлов (audio, slides)
- [x] Протестировать удаление медиа
- [x] Протестировать двуязычность (ru/kk)

**Выполнено:** 2025-12-18

### Реализованные API Endpoints:

**Global (SUPER_ADMIN):** `/api/v1/admin/global/paragraphs/{id}/content`
**School (ADMIN):** `/api/v1/admin/school/paragraphs/{id}/content`

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/content?language=ru` | Получить контент |
| PUT | `/content?language=ru` | Обновить explain_text/cards |
| PUT | `/content/cards?language=ru` | Обновить карточки |
| POST | `/content/audio?language=ru` | Загрузить аудио (MP3/OGG/WAV, 50MB) |
| POST | `/content/slides?language=ru` | Загрузить слайды (PDF/PPTX, 50MB) |
| POST | `/content/video?language=ru` | Загрузить видео (MP4/WEBM, 200MB) |
| DELETE | `/content/audio` | Удалить аудио |
| DELETE | `/content/slides` | Удалить слайды |
| DELETE | `/content/video` | Удалить видео |

---

## Этап 3: Frontend Admin Panel

**Цель:** Создать UI для управления контентом параграфа.

### 3.1. Структура файлов

```
admin-v2/src/
├── app/[locale]/(dashboard)/
│   └── textbooks/
│       └── [textbookId]/
│           └── chapters/
│               └── [chapterId]/
│                   └── paragraphs/
│                       └── [paragraphId]/
│                           └── content/
│                               └── page.tsx  ← Страница контента
│
├── lib/
│   ├── api/
│   │   └── paragraph-content.ts  ← API клиент
│   └── hooks/
│       └── use-paragraph-content.ts  ← React Query hooks
│
└── components/
    └── paragraph-content/
        ├── content-page.tsx        ← Основной компонент страницы
        ├── explain-section.tsx     ← Секция "Объяснение"
        ├── audio-section.tsx       ← Секция "Аудио"
        ├── slides-section.tsx      ← Секция "Слайды"
        ├── video-section.tsx       ← Секция "Видео"
        ├── cards-section.tsx       ← Секция "Карточки"
        ├── card-editor.tsx         ← Редактор одной карточки
        ├── media-uploader.tsx      ← Компонент загрузки файлов
        ├── status-badge.tsx        ← Бейдж статуса
        └── language-switcher.tsx   ← Переключатель RU/KK
```

### 3.2. API клиент

**Файл:** `admin-v2/src/lib/api/paragraph-content.ts`

```typescript
export interface ParagraphContent {
  id: number;
  paragraph_id: number;
  language: 'ru' | 'kk';
  explain_text: string | null;
  audio_url: string | null;
  slides_url: string | null;
  video_url: string | null;
  cards: CardItem[] | null;
  status_explain: ContentStatus;
  status_audio: ContentStatus;
  status_slides: ContentStatus;
  status_video: ContentStatus;
  status_cards: ContentStatus;
}

export type ContentStatus = 'empty' | 'draft' | 'ready' | 'outdated';

export interface CardItem {
  id: string;
  type: 'term' | 'fact' | 'check';
  front: string;
  back: string;
  order: number;
}

export const paragraphContentApi = {
  get: (paragraphId: number, language: string) =>
    api.get<ParagraphContent>(`/paragraphs/${paragraphId}/content?language=${language}`),

  updateExplain: (paragraphId: number, language: string, explain_text: string) =>
    api.put<ParagraphContent>(`/paragraphs/${paragraphId}/content`, { language, explain_text }),

  uploadAudio: (paragraphId: number, language: string, file: File) =>
    uploadFile(`/paragraphs/${paragraphId}/content/audio?language=${language}`, file),

  uploadSlides: (paragraphId: number, language: string, file: File) =>
    uploadFile(`/paragraphs/${paragraphId}/content/slides?language=${language}`, file),

  uploadVideo: (paragraphId: number, language: string, file: File) =>
    uploadFile(`/paragraphs/${paragraphId}/content/video?language=${language}`, file),

  deleteMedia: (paragraphId: number, language: string, type: 'audio' | 'slides' | 'video') =>
    api.delete(`/paragraphs/${paragraphId}/content/${type}?language=${language}`),

  updateCards: (paragraphId: number, language: string, cards: CardItem[]) =>
    api.put<ParagraphContent>(`/paragraphs/${paragraphId}/content/cards?language=${language}`, { cards }),
};
```

### 3.3. React Query Hooks

**Файл:** `admin-v2/src/lib/hooks/use-paragraph-content.ts`

```typescript
export const paragraphContentKeys = {
  all: ['paragraph-content'] as const,
  detail: (paragraphId: number, language: string) =>
    [...paragraphContentKeys.all, paragraphId, language] as const,
};

export function useParagraphContent(paragraphId: number, language: string) {
  return useQuery({
    queryKey: paragraphContentKeys.detail(paragraphId, language),
    queryFn: () => paragraphContentApi.get(paragraphId, language),
  });
}

export function useUpdateExplain() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ paragraphId, language, explain_text }) =>
      paragraphContentApi.updateExplain(paragraphId, language, explain_text),
    onSuccess: (_, { paragraphId, language }) => {
      queryClient.invalidateQueries({
        queryKey: paragraphContentKeys.detail(paragraphId, language)
      });
    },
  });
}

// ... аналогично для upload и delete
```

### 3.4. UI компоненты

#### Страница контента (page.tsx)

```tsx
export default function ParagraphContentPage({ params }) {
  const [language, setLanguage] = useState<'ru' | 'kk'>('ru');
  const { data: content, isLoading } = useParagraphContent(params.paragraphId, language);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Контент параграфа"
        breadcrumbs={[...]}
      >
        <LanguageSwitcher value={language} onChange={setLanguage} />
      </PageHeader>

      <ExplainSection content={content} language={language} />
      <AudioSection content={content} language={language} />
      <SlidesSection content={content} language={language} />
      <VideoSection content={content} language={language} />
      <CardsSection content={content} language={language} />
    </div>
  );
}
```

#### Секция с медиа (пример AudioSection)

```tsx
function AudioSection({ content, language, paragraphId }) {
  const uploadMutation = useUploadAudio();
  const deleteMutation = useDeleteMedia();

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <Headphones className="h-5 w-5" />
          <CardTitle>Аудио</CardTitle>
        </div>
        <StatusBadge status={content?.status_audio || 'empty'} />
      </CardHeader>
      <CardContent>
        {content?.audio_url ? (
          <div className="space-y-4">
            <audio controls className="w-full">
              <source src={content.audio_url} type="audio/mpeg" />
            </audio>
            <div className="flex gap-2">
              <MediaUploader
                accept=".mp3,.ogg,.wav"
                onUpload={(file) => uploadMutation.mutate({ paragraphId, language, file })}
                label="Заменить"
              />
              <Button
                variant="destructive"
                size="sm"
                onClick={() => deleteMutation.mutate({ paragraphId, language, type: 'audio' })}
              >
                Удалить
              </Button>
            </div>
          </div>
        ) : (
          <MediaUploader
            accept=".mp3,.ogg,.wav"
            onUpload={(file) => uploadMutation.mutate({ paragraphId, language, file })}
            label="Загрузить MP3"
            description="Поддерживаются форматы: MP3, OGG, WAV. Максимум 100MB."
          />
        )}
      </CardContent>
    </Card>
  );
}
```

### Задачи этапа 3:

- [x] Создать API клиент `admin-v2/src/lib/api/paragraph-content.ts`
- [x] Создать hooks `admin-v2/src/lib/hooks/use-paragraph-content.ts`
- [x] Создать компонент `StatusBadge`
- [x] Создать компонент `LanguageSwitcher`
- [x] Создать компонент `MediaUploader` (drag & drop)
- [x] Создать `ExplainSection` с Textarea редактором
- [x] Создать `AudioSection` с плеером
- [x] Создать `SlidesSection` с preview PDF
- [x] Создать `VideoSection` с видео плеером
- [x] Создать `CardsSection` с редактором карточек
- [x] Создать страницу `page.tsx`
- [x] Добавить навигацию на страницу контента из страницы параграфа
- [x] Протестировать весь flow

**Выполнено:** 2025-12-18

### Созданные файлы:

```
admin-v2/src/
├── types/index.ts                           # Добавлены типы ParagraphContent, CardItem, ContentStatus
├── lib/
│   ├── api/
│   │   ├── paragraph-content.ts             # API клиент для работы с контентом
│   │   └── index.ts                         # Экспорт
│   └── hooks/
│       ├── use-paragraph-content.ts         # React Query hooks
│       └── index.ts                         # Экспорт
├── components/
│   └── paragraph-content/
│       ├── index.ts                         # Экспорт компонентов
│       ├── status-badge.tsx                 # Бейдж статуса (empty/draft/ready/outdated)
│       ├── language-switcher.tsx            # Переключатель RU/KK
│       ├── media-uploader.tsx               # Drag & drop загрузка файлов
│       ├── explain-section.tsx              # Редактор объяснения
│       ├── audio-section.tsx                # Аудио плеер и загрузка
│       ├── slides-section.tsx               # PDF preview и загрузка
│       ├── video-section.tsx                # Видео плеер и загрузка
│       └── cards-section.tsx                # Редактор карточек
└── app/[locale]/(dashboard)/textbooks/[id]/paragraphs/[paragraphId]/content/
    └── page.tsx                             # Страница редактирования контента
```

### Добавленные зависимости:

- `react-dropzone` - для drag & drop загрузки файлов

---

## Этап 4: Интеграция и тестирование

**Цель:** Интеграция всех частей, тестирование, деплой.

### 4.1. Навигация

Добавить кнопку "Контент" на страницу просмотра параграфа:

```tsx
// На странице параграфа
<Button asChild>
  <Link href={`/textbooks/${textbookId}/chapters/${chapterId}/paragraphs/${paragraphId}/content`}>
    <FileText className="mr-2 h-4 w-4" />
    Управление контентом
  </Link>
</Button>
```

### 4.2. Обновление списка параграфов

Показывать иконки наличия контента в таблице параграфов:

```tsx
// В колонке таблицы
<div className="flex gap-1">
  {paragraph.has_audio_ru && <Headphones className="h-4 w-4 text-green-500" />}
  {paragraph.has_video_ru && <Video className="h-4 w-4 text-green-500" />}
  {paragraph.has_slides_ru && <Presentation className="h-4 w-4 text-green-500" />}
</div>
```

### 4.3. Nginx конфигурация

```nginx
# /etc/nginx/sites-available/api.ai-mentor.kz
location /uploads/ {
    alias /var/www/uploads/;
    expires 30d;
    add_header Cache-Control "public, immutable";

    # Ограничение по размеру для загрузки
    client_max_body_size 100M;
}
```

### Задачи этапа 4:

- [ ] Добавить кнопку навигации на страницу параграфа
- [ ] Добавить индикаторы контента в список параграфов
- [ ] Обновить nginx конфиг
- [ ] Создать директорию `/var/www/uploads/paragraph-contents/`
- [ ] Настроить права доступа к директории
- [ ] Провести end-to-end тестирование
- [ ] Задеплоить на production
- [ ] Проверить работу на production

---

## Этап 5 (будущее): Narakeet API интеграция

**Цель:** Автоматическая генерация аудио/видео через Narakeet API.

### 5.1. Что нужно реализовать

1. **Фоновые задачи** (Celery или asyncio background tasks)
2. **Интеграция с Narakeet API:**
   - Отправка текста на генерацию
   - Webhook для получения результата
   - Скачивание и сохранение файла
3. **UI для запуска генерации:**
   - Кнопка "Сгенерировать аудио"
   - Progress индикатор
   - Обработка ошибок

### 5.2. Примерный flow

```
1. Админ нажимает "Сгенерировать аудио"
2. Frontend → POST /api/v1/paragraphs/{id}/content/generate-audio
3. Backend создаёт задачу, статус = "generating"
4. Background task отправляет запрос в Narakeet API
5. Narakeet обрабатывает и возвращает URL файла (или webhook)
6. Backend скачивает файл, сохраняет, обновляет status = "ready"
7. Frontend получает обновление через polling или WebSocket
```

### Задачи этапа 5 (отложено):

- [ ] Изучить Narakeet API документацию
- [ ] Настроить Celery или background tasks
- [ ] Реализовать интеграцию с Narakeet
- [ ] Добавить кнопки генерации в UI
- [ ] Реализовать отображение прогресса

---

## Оценка трудозатрат

| Этап | Описание | Сложность |
|------|----------|-----------|
| 1 | База данных и модели | Низкая |
| 2 | Backend API | Средняя |
| 3 | Frontend Admin Panel | Высокая |
| 4 | Интеграция и деплой | Низкая |
| 5 | Narakeet API (будущее) | Средняя |

---

## Чеклист готовности к production

- [x] Миграция применена на production БД
- [x] Backend задеплоен с новыми endpoints
- [x] Frontend задеплоен с новыми страницами
- [x] Nginx настроен для /uploads/ (было настроено ранее)
- [x] Директория uploads создана с правильными правами
- [x] Протестирована загрузка файлов разных форматов (audio, slides)
- [x] Протестирован просмотр (аудио плеер, видео плеер, PDF)
- [x] Протестировано переключение языков (ru/kk)
- [x] Протестировано создание/редактирование карточек

**Production URLs:**
- API: https://api.ai-mentor.kz/api/v1/admin/global/paragraphs/{id}/content
- Admin Panel: https://admin.ai-mentor.kz/ru/textbooks/{textbookId}/paragraphs/{paragraphId}/content

---

## Открытые вопросы

1. **Лимиты файлов:** 100MB достаточно для видео?
2. **Формат слайдов:** Показывать PDF inline или только скачивание?
3. **Бэкапы:** Как бэкапить директорию uploads?
4. **CDN:** Нужен ли CDN для раздачи медиа в будущем?
