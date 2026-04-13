# SESSION LOG: Presentation Export v2 (Gamma-style)

**Дата:** 2026-04-13 16:02  
**Задача:** Переработка системы генерации PPTX-презентаций — визуальное качество уровня Gamma.app  
**Статус:** Этапы 2–10 завершены. v2 готов к включению через feature flag. Code review пройден, все замечания исправлены.

---

## Исходная проблема

Текущая реализация генерации презентаций (v1) работает, но визуально слабая:
- Все слайды выглядят одинаково — белый фон, чёрный текст, header bar сверху
- Нет разнообразия layout-ов (все content-слайды идентичны)
- Нет stock-фотографий (только картинки из учебника, которых часто нет)
- Темы — просто смена accent color, не полноценные палитры
- Key terms — плоский список, Quiz — вертикальный список с подсветкой ответа

**Цель:** приблизить визуальное качество к Gamma.app. Архитектурный сдвиг: LLM выдаёт семантику + метаданные (`layout_hint`, `image_query`, `stat_value`), а layout-движок детерминированно выбирает визуальную форму.

---

## Архитектурное решение

```
LLM генерирует JSON с семантикой          Layout-движок рендерит PPTX
─────────────────────────────────          ───────────────────────────
{                                          ┌─────────────────────────┐
  "type": "content",                       │ layout_hint = image_left│
  "title": "Қасым хан",                   │ → текст справа,         │
  "body": "...",                           │   фото слева            │
  "layout_hint": "stat_callout",     →     │ layout_hint = stat_call │
  "stat_value": "1511",                    │ → большая цифра в карт. │
  "image_query": "kazakh steppe"           │ layout_hint = image_righ│
}                                          │ → текст слева, фото спра│
                                           └─────────────────────────┘
```

**Ключевой принцип:** LLM НЕ занимается дизайном. Она выбирает что показать (факт, картинку, термины), а экспортёр решает как это выглядит.

---

## Что было сделано (по этапам)

### Этап 1: Разведка и план

Изучены файлы:
- `backend/app/services/presentation_export.py` (v1 экспортёр, 515 строк)
- `backend/app/services/presentation_service.py` (сервис генерации)
- `backend/app/schemas/presentation.py` (pydantic схемы)
- `backend/app/api/v1/teachers_presentations.py` (API роуты)
- `backend/app/models/presentation.py` (DB модель)
- `teacher-app/src/components/presentation/slides/*.tsx` (6 React компонентов)
- `teacher-app/src/components/presentation/slide-themes.ts` (2 темы)
- Три референсных файла: `presentation_export_v2.py`, `llm_prompt_v2.md`, `sample_slides.json`

**Обнаружено:**
- Redis не используется в проекте → решено использовать in-memory кэш
- HTTP-клиент проекта — `httpx`, не `requests`
- `slides_data` хранится как JSONB dict → миграция БД не нужна
- Публичная API сигнатура: `export_to_pptx(slides_data, context_data, template) -> BytesIO`

---

### Этап 2: Pydantic схемы

**Файл:** `backend/app/schemas/presentation.py`

Добавлены модели валидации для LLM-ответов:

```python
class SlideV2(BaseModel):
    # Все существующие поля (type, title, body, items, terms, etc.)
    # + новые v2 поля:
    layout_hint: Optional[Literal["image_left", "image_right", "stat_callout"]] = None
    image_query: Optional[str] = None
    stat_value: Optional[str] = None
    stat_label: Optional[str] = None
```

**Принципы:**
- Все новые поля `Optional` с дефолтами → старый JSON парсится без ошибок
- `extra="ignore"` → неизвестные поля (например `emphasis_word`) не ломают парсинг
- **Soft validation:** при превышении лимитов — truncate + warning в лог, не exception
- `image_query` очищается от нелатинских символов (Unsplash требует English)
- `stat_value` ≤ 7 символов
- Если `stat_value` есть, но `layout_hint` не указан → автоматически `stat_callout`

Лимиты символов:
| Поле | Лимит |
|------|-------|
| title | 60 |
| subtitle | 90 |
| body | 300 |
| item | 80 |
| term | 25 |
| definition | 90 |
| question | 120 |
| option | 50 |
| stat_value | 7 |
| stat_label | 35 |
| image_query | 60 |

**Функция-валидатор:** `validate_slides_data(raw: dict) -> dict` — вызывается в сервисе после парсинга LLM-ответа. Никогда не raise — при ошибке возвращает raw data с warning.

**Тесты:** `backend/tests/test_presentation_schemas.py` — 26 тестов (backward compat, v2 fields, soft validation).

---

### Этап 3: Новый экспортёр PPTX

**Файл:** `backend/app/services/presentation_export_v2.py` (~660 строк)

**Адаптации от референса:**
- `requests` → `httpx.Client` (единый HTTP-клиент проекта)
- Шрифт `Nunito` → `Calibri` (гарантированно есть на всех машинах с Office)
- Сигнатура: `export_to_pptx(slides_data, context_data, template) -> BytesIO` (совпадает с v1)
- Логирование через `logging`, не `print`

**3 полноценные темы:**

| Тема | Предмет | Палитра | Motif |
|------|---------|---------|-------|
| `warm` | История | Кремовый фон, оранжевый primary | `rounded_card` |
| `forest` | Биология | Светло-зелёный фон, тёмно-зелёный primary | `side_bar` |
| `midnight` | Математика/Информатика | Тёмно-синий фон, фиолетовый primary | `circle_badge` |

**Aliases для обратной совместимости:** `green` → `forest`, `blue` → `warm`

**6 типов слайдов с уникальным дизайном:**

| Тип | Layout |
|-----|--------|
| `title` | Half-bleed image справа, typography слева, eyebrow "САБАҚ" |
| `objectives` | Numbered circles + text rows, eyebrow "01" |
| `content` (image_left) | Фото слева, текст справа |
| `content` (image_right) | Текст слева, фото справа |
| `content` (stat_callout) | Большая цифра в цветной карточке + body справа |
| `key_terms` | 3×2 grid карточек с accent strip |
| `quiz` | 2×2 grid, letter badges A/B/C/D, ответ только в speaker notes |
| `summary` | Dark sandwich (primary фон, белые карточки с checkmarks) |

**Speaker notes** на каждом слайде (для учителя).

**ImageProvider:**
- Unsplash API через `httpx.Client`
- In-memory кэш с TTL 30 дней
- Graceful fallback: без ключа → цветные placeholder-блоки с декоративными кругами
- Rate limit (429) и auth errors (401/403) → кэшируются как None, не повторяются

**Тесты:** `backend/tests/test_presentation_export_v2.py` — 32 теста (smoke per type, all themes, backward compat, edge cases, ImageProvider).

---

### Этап 4: Unsplash + config

**Файлы:** `backend/app/core/config.py`, `.env.example`

Добавлены settings:
```python
UNSPLASH_ACCESS_KEY: Optional[str] = None
PRESENTATION_EXPORTER_VERSION: str = "v1"
```

`.env.example` обновлён с комментариями:
```
# Get your key at https://unsplash.com/developers → New Application → Access Key
UNSPLASH_ACCESS_KEY=
PRESENTATION_EXPORTER_VERSION=v1
```

`ImageProvider` берёт ключ из `settings.UNSPLASH_ACCESS_KEY` (не `os.getenv`).

---

### Этап 5: Новый LLM промпт

**Файл:** `backend/app/services/presentation_service.py`

**Изменения в system prompt:**
- Полностью переписан на английском (LLM лучше следует инструкциям)
- Описаны 6 slide types с полной JSON-схемой включая v2 поля
- Layout rules: чередовать image_left/image_right, stat_callout для дат/цифр
- image_query rules: только English, конкретные существительные
- Character limits из llm_prompt_v2.md

**3 варианта структуры слайдов:**

| Кол-во | Структура |
|--------|-----------|
| 5 | title → objectives → 2 content → summary |
| 10 | title → objectives → 4 content → key_terms → content → quiz → summary |
| 15 | title → objectives → 6 content → key_terms → 2 content → 2 quiz → content → summary |

**Другие изменения:**
- `temperature`: 0.7 → 0.8
- **DEBUG-лог** сырого ответа LLM (первые 500 символов)
- **Retry при битом JSON:** один повтор с сообщением об ошибке, temperature 0.3
- **validate_slides_data()** вызывается после парсинга (soft-санитизация)

---

### Этап 6: Feature flag

**Файл:** `backend/app/api/v1/teachers_presentations.py`

```python
def _get_exporter():
    if settings.PRESENTATION_EXPORTER_VERSION == "v2":
        return export_to_pptx_v2, get_available_templates_v2
    return export_to_pptx_v1, get_available_templates_v1
```

Используется в двух местах:
- `GET /teachers/presentations/templates` — список тем
- `GET /teachers/presentations/{id}/export/pptx` — экспорт PPTX

**Переключение:** одна env-переменная `PRESENTATION_EXPORTER_VERSION=v2`, откат = `v1`.

---

### Этап 7: Маппинг темы к предмету

**Файлы:** `presentation_service.py`, `paragraph_repo.py`, фронтенд

```python
SUBJECT_THEME_MAP = {
    "history_kz": "warm",    "world_history": "warm",
    "biology": "forest",     "natural_science": "forest",
    "chemistry": "forest",   "geography": "forest",
    "algebra": "midnight",   "geometry": "midnight",
    "math": "midnight",      "informatics": "midnight",
    "physics": "midnight",
}
DEFAULT_THEME = "warm"
```

- `subject_code` добавлен в `ContentMetadata` (из `textbook.subject_rel.code`)
- `theme` автоматически определяется и включается в `PresentationContext`
- **Фронтенд:** убран дропдаун "Стиль оформления" из формы создания
- Grid сменился с 3 на 2 колонки (Язык + Слайдов)

---

### Этап 8: React-компоненты preview

**Файлы в `teacher-app/src/components/presentation/`:**

| Файл | Изменения |
|------|-----------|
| `types/presentation.ts` | `SlideThemeName` += `'forest' \| 'midnight'`; `SlideData` += `layout_hint`, `image_query`, `stat_value`, `stat_label` |
| `slide-themes.ts` | Добавлены `forest`, `midnight`; новые поля `bgColor` (CSS fallback), `statBg/statText/statLabel`; функция `getSlideBg()` |
| `ContentSlide.tsx` | 3 layout: `ImageLayout(left/right)` + `StatCalloutLayout` |
| `KeyTermsSlide.tsx` | Grid 3×N карточек с accent strip вместо flat list |
| `QuizSlide.tsx` | 2×2 grid, letter badges, ответ НЕ показан |
| `TitleSlide.tsx` | Eyebrow "САБАҚ", accent bar, `getSlideBg` |
| `ObjectivesSlide.tsx` | Eyebrow "01", numbered circles |
| `SummarySlide.tsx` | Dark sandwich (цветной фон + белые карточки) |
| `SpectacleViewer.tsx` | `slideBgProps()` — backgroundColor fallback для midnight |

**TypeScript:** 0 ошибок после всех изменений.

---

### Этап 9: Тестирование

**Результаты:**

| Тест | Кол-во | Статус |
|------|--------|--------|
| `test_presentation_schemas.py` | 26 | 26 passed |
| `test_presentation_export_v2.py` | 32 | 32 passed |
| Реальные презентации из БД | 9 | 9 rendered OK |
| TypeScript (teacher-app) | — | 0 errors |
| Визуальная проверка PPTX (LibreOffice) | warm/forest/midnight + backward | 0 overflow, 0 overlap |

---

## Файлы изменённые/созданные

### Backend — изменённые:
```
backend/app/schemas/presentation.py          — v2 slide models + validate_slides_data()
backend/app/services/presentation_service.py — v2 prompt, retry, theme mapping
backend/app/api/v1/teachers_presentations.py — feature flag switching
backend/app/core/config.py                   — UNSPLASH_ACCESS_KEY, PRESENTATION_EXPORTER_VERSION
backend/app/repositories/paragraph_repo.py   — subject_code в ContentMetadata
.env.example                                 — новые переменные
```

### Backend — созданные:
```
backend/app/services/presentation_export_v2.py  — новый Gamma-style экспортёр
backend/tests/test_presentation_schemas.py      — 26 тестов v2 схем
backend/tests/test_presentation_export_v2.py    — 32 теста v2 экспортёра
```

### Frontend — изменённые:
```
teacher-app/src/types/presentation.ts
teacher-app/src/components/presentation/slide-themes.ts
teacher-app/src/components/presentation/slides/ContentSlide.tsx
teacher-app/src/components/presentation/slides/KeyTermsSlide.tsx
teacher-app/src/components/presentation/slides/QuizSlide.tsx
teacher-app/src/components/presentation/slides/TitleSlide.tsx
teacher-app/src/components/presentation/slides/ObjectivesSlide.tsx
teacher-app/src/components/presentation/slides/SummarySlide.tsx
teacher-app/src/components/presentation/SpectacleViewer.tsx
teacher-app/src/app/[locale]/(dashboard)/presentations/create/page.tsx
```

### НЕ изменённые (специально):
```
backend/app/services/presentation_export.py  — старый v1 экспортёр (сосуществует)
backend/app/models/presentation.py           — JSONB, миграция не нужна
```

---

## Как включить v2

### На staging (для тестирования):
```bash
# В .env добавить:
PRESENTATION_EXPORTER_VERSION=v2

# Опционально (для реальных фото):
UNSPLASH_ACCESS_KEY=your_key_here

# Пересобрать и перезапустить:
docker compose -f docker-compose.infra.yml build backend --no-cache
docker compose -f docker-compose.infra.yml up -d backend --force-recreate
docker compose -f docker-compose.infra.yml build teacher-app --no-cache
docker compose -f docker-compose.infra.yml up -d teacher-app --force-recreate
```

### Проверка на staging:
1. Создать презентацию по параграфу истории → должна быть warm тема
2. Создать по биологии → forest тема
3. Создать по информатике → midnight тема (тёмный фон)
4. Экспортировать в PPTX → открыть в PowerPoint/LibreOffice, проверить все слайды
5. Открыть старую сохранённую презентацию → должна рендериться через v2 без ошибок

### Откат:
```bash
PRESENTATION_EXPORTER_VERSION=v1
# Перезапустить backend
```

---

## Что НЕ вошло в этот sprint

1. **Полная генерация через реальную LLM** — промпт написан и интегрирован, но тестовая генерация через DashScope не проводилась (это первое что нужно проверить на staging)
2. **Unsplash с реальным ключом** — протестирован fallback без ключа, с реальным ключом нужно проверить rate limit и качество фотографий
3. **SpectacleViewer полный рефакторинг** — добавлен только backgroundColor fallback для midnight; полная переделка Spectacle-компонентов под v2 layouts — отдельная задача
4. **Фоновые картинки для midnight** — нет PNG-файлов в `/slide-bg/`, используется CSS bgColor
5. **Этап 10 (документация + prod deploy)** — ожидает ручной проверки на staging

---

## Этап 10: Code Review и исправления (2026-04-13)

По результатам ревью были найдены и исправлены следующие проблемы:

### 10.1 ImageProvider: singleton-кэш + reuse httpx.Client (CRITICAL)

**Проблема:** `_cache` был instance variable, а `ImageProvider()` создавался заново при каждом вызове `export_to_pptx()`. Кэш умирал вместе с экземпляром. Также каждый `fetch()` создавал новый `httpx.Client` — 10 слайдов = 10 TCP handshakes.

**Исправление:**
- `_cache` → class variable (переживает вызовы)
- `httpx.Client` создаётся один раз через `_get_client()` (lazy init)
- Тест `test_cache_stores_results` обновлён для class-level кэша

**Файлы:** `presentation_export_v2.py`, `test_presentation_export_v2.py`

### 10.2 run_in_executor для sync PPTX export (HIGH)

**Проблема:** `export_to_pptx()` — синхронная функция с HTTP-вызовами к Unsplash. Вызывалась напрямую из async FastAPI handler, блокируя event loop для всех запросов.

**Исправление:**
```python
loop = asyncio.get_event_loop()
buf = await loop.run_in_executor(
    None, lambda: export_fn(pres.slides_data, export_context, template=template)
)
```

**Файл:** `teachers_presentations.py`

### 10.3 Локализация prompt + eyebrow текстов для ru/kk (MEDIUM)

**Проблема:** System prompt хардкодил казахские заголовки ("Сабақтың мақсаты", "Негізгі ұғымдар") для всех языков. PPTX экспортёр хардкодил казахские eyebrow-тексты ("САБАҚ", "ТАҚЫРЫП", "ТЕРМИНДЕР", "БІЛІМДІ ТЕКСЕР", "ҚОРЫТЫНДЫ", "НЕГІЗГІ ФАКТ") и speaker notes.

**Исправление:**
- `_build_system_prompt()` — условные `obj_title`, `terms_title`, `summary_title` по `language`
- `presentation_export_v2.py` — добавлен `_L10N` dict с полным набором строк для kk/ru
- `_get_l10n(context_data)` извлекает язык из `context_data["language"]`
- `SlideBuilder.__init__` принимает `l10n` параметр, все методы используют `self.l[key]`
- В endpoint `export_presentation_pptx` — inject `language` в `export_context`

**Файлы:** `presentation_service.py`, `presentation_export_v2.py`, `teachers_presentations.py`

### 10.4 SummarySlide theme adaptation для midnight (MEDIUM)

**Проблема:** `SummarySlide.tsx` хардкодил `bg-white/90` и `text-slate-800`. На midnight теме карточки выглядели ослепительно белыми.

**Исправление:** `bg-white/90` → `theme.cardBg`, `text-slate-800` → `theme.cardText`

**Файл:** `SummarySlide.tsx`

### 10.5 Redundant exception catch (LOW)

**Проблема:** `except (ValueError, Exception)` — ValueError подкласс Exception, дублирование.

**Исправление:** → `except Exception`

**Файл:** `presentation_service.py`

### 10.6 Дифференциация green/forest labels (LOW)

**Проблема:** Оба theme имели идентичный label `"Биология (зелёный)"`.

**Исправление:** `forest.label` → `"Естественные науки (изумрудный)"` (frontend + backend)

**Файлы:** `slide-themes.ts`, `presentation_export_v2.py`

### Результаты тестов после исправлений

| Тест | Кол-во | Статус |
|------|--------|--------|
| `test_presentation_schemas.py` | 26 | 26 passed |
| `test_presentation_export_v2.py` | 32 | 32 passed |
| TypeScript (teacher-app) | — | 0 errors |

---

## Оставшиеся known issues (tech debt)

1. **SpectacleViewer (fullscreen)** не обновлён для v2 — хардкоженные amber цвета, нет stat_callout layout, quiz показывает ответ. Grid preview и fullscreen визуально различаются.
2. **Фронтенд eyebrow-тексты** в React-компонентах (`ContentSlide`, `QuizSlide`, `KeyTermsSlide` и др.) хардкодят казахские строки. Для полной локализации нужно передавать `language` через props и выбирать текст условно.
3. **Фоновые PNG для midnight** — нет файлов, используется CSS bgColor fallback.
