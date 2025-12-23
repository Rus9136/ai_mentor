# Архитектура AI Mentor

> **Назначение документа:** Техническая архитектура системы — RBAC, структура данных, алгоритмы.
>
> **Связанные документы:**
> - `CLAUDE.md` — инструкции для AI-агентов, команды, credentials
> - `docs/IMPLEMENTATION_STATUS.md` — прогресс итераций, статистика
> - `docs/REFACTORING_SERVICES.md` — план рефакторинга Services Layer

## 1. Обзор

**AI Mentor** — адаптивная образовательная платформа для школьников 7-11 классов с автоматической группировкой по уровню мастерства (A/B/C).

**Ключевые особенности:**
- Multi-tenant SaaS с Row Level Security (RLS)
- Гибридная модель контента (глобальный + школьный)
- RAG-система для персонализированных пояснений
- Офлайн-режим с синхронизацией

**Технологический стек:**
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0+, Alembic
- Database: PostgreSQL 16+ с pgvector, RLS
- Frontend: Next.js 15 (Admin + Student App)
- AI: Jina (embeddings), Cerebras (LLM)

---

## 2. Роли и права доступа (RBAC)

### 2.1 SUPER_ADMIN
**Область:** Вся система, все школы

| Может | Не может |
|-------|----------|
| Управление школами (CRUD, блокировка) | Управлять пользователями школ |
| Глобальный контент (school_id=NULL) | Управлять классами |
| Статистика по всем школам | - |

**Особенность:** `users.school_id = NULL`

### 2.2 ADMIN (Школьный)
**Область:** Только своя школа

| Может | Не может |
|-------|----------|
| Управление пользователями школы | Видеть другие школы |
| Школьный контент (school_id=своя) | Редактировать глобальный контент |
| Кастомизация (fork) глобального контента | - |
| Настройки школы | - |

### 2.3 TEACHER
**Область:** Свои классы

| Может | Не может |
|-------|----------|
| Просмотр своих классов и учеников | Создавать контент |
| Аналитика по A/B/C группам | Видеть чужие классы |
| Создание заданий | Управлять пользователями |

### 2.4 STUDENT
**Область:** Только свои данные

| Может | Не может |
|-------|----------|
| Прохождение тестов | Видеть других учеников |
| Просмотр своего прогресса | Создавать тесты |
| Получение пояснений | - |

### 2.5 PARENT
**Область:** Только свои дети

| Может | Не может |
|-------|----------|
| Просмотр прогресса детей | Видеть других учеников |
| Результаты тестов детей | Проходить тесты |

---

## 3. Гибридная модель контента

### 3.1 Типы контента

| Тип | school_id | Кто создаёт | Кто видит |
|-----|-----------|-------------|-----------|
| **Глобальный** | NULL | SUPER_ADMIN | Все школы (read-only) |
| **Школьный** | конкретный ID | School ADMIN | Только эта школа |
| **Кастомизированный** | конкретный ID + `is_customized=true` | School ADMIN (fork) | Только эта школа |

### 3.2 Процесс кастомизации (Fork)

```
POST /api/v1/admin/school/textbooks/{global_id}/customize

Создаётся копия:
- school_id = current_school_id
- global_textbook_id = original_id
- is_customized = true
- Копируются все chapters и paragraphs
```

**Применяется к:** textbooks, chapters, paragraphs (tests НЕ форкаются)

---

## 4. Multi-tenancy и RLS

### 4.1 Изоляция данных

**Все таблицы с `school_id`** защищены RLS policies:
- 27 таблиц с FORCE ROW LEVEL SECURITY
- Контекст устанавливается через `app.current_school_id` и `app.current_user_id`

**TenancyMiddleware** автоматически:
1. Извлекает `school_id` из JWT токена
2. Устанавливает session variables перед каждым запросом
3. Сбрасывает после завершения

### 4.2 Роли PostgreSQL

| Роль | Назначение | RLS |
|------|------------|-----|
| `ai_mentor_user` | Миграции (SUPERUSER) | Bypass |
| `ai_mentor_app` | Runtime | Применяется |

---

## 5. Алгоритм группировки A/B/C

### 5.1 Критерии

| Группа | Условие |
|--------|---------|
| **A** | ≥85% + стабильность или улучшение |
| **B** | 60-84% |
| **C** | <60% или стабильное ухудшение |

### 5.2 Алгоритм расчёта

```python
# 1. Последние 5 попыток по главе
weights = [0.35, 0.25, 0.20, 0.12, 0.08]  # новые важнее

# 2. Взвешенное среднее
weighted_avg = sum(score * weight for score, weight in zip(scores, weights))

# 3. Тренд (сравнение первых 2 и последних 2)
trend = avg(recent_2) - avg(older_2)

# 4. Консистентность (std_dev)
std_dev = calculate_std_dev(scores)

# 5. Определение уровня
if weighted_avg >= 85 and (trend >= 0 or std_dev < 10):
    level = 'A'
elif weighted_avg < 60 or (weighted_avg < 70 and trend < -10):
    level = 'C'
else:
    level = 'B'
```

### 5.3 Когда обновляется

- Только после **FORMATIVE** или **SUMMATIVE** тестов
- **DIAGNOSTIC** и **PRACTICE** — не влияют на mastery
- Изменения записываются в `mastery_history`

---

## 6. GOSO — Государственный стандарт образования

### 6.1 Структура данных

```
subjects (предметы)
    └── frameworks (версии ГОСО)
            ├── goso_sections (разделы, 4 шт.)
            │       └── goso_subsections (подразделы, 9 шт.)
            │               └── learning_outcomes (цели, 164 шт.)
            │                       └── paragraph_outcomes (M:N → paragraphs)
```

### 6.2 Кодировка целей

Формат: `{класс}.{раздел}.{подраздел}.{номер}`

Пример: `7.2.1.2` = 7 класс, раздел 2, подраздел 1, цель 2

### 6.3 Права доступа

| Данные | SUPER_ADMIN | School ADMIN | Остальные |
|--------|-------------|--------------|-----------|
| subjects/frameworks/outcomes | Read | Read | Read |
| paragraph_outcomes (global) | Read/Write | Read | Read |
| paragraph_outcomes (school) | Read | Read/Write | Read |

---

## 7. Структура API

### 7.1 Префиксы

| Префикс | Роль | Описание |
|---------|------|----------|
| `/api/v1/auth/*` | Все | Аутентификация |
| `/api/v1/admin/global/*` | SUPER_ADMIN | Глобальный контент |
| `/api/v1/admin/school/*` | School ADMIN | Школьный контент + пользователи |
| `/api/v1/students/*` | STUDENT | Тесты, прогресс |
| `/api/v1/teachers/*` | TEACHER | Dashboard, аналитика |
| `/api/v1/parents/*` | PARENT | Прогресс детей |
| `/api/v1/goso/*` | Все auth | GOSO справочники |

### 7.2 Ключевые endpoints

**Auth:**
- `POST /auth/login` → `{access_token, refresh_token}`
- `POST /auth/refresh` → новые токены
- `GET /auth/me` → текущий пользователь

**Content (SUPER_ADMIN):**
- `CRUD /admin/global/textbooks`
- `CRUD /admin/global/chapters`
- `CRUD /admin/global/paragraphs`
- `CRUD /admin/global/tests`
- `CRUD /admin/global/questions`

**Content (School ADMIN):**
- То же с `/admin/school/*`
- `POST /admin/school/textbooks/{id}/customize` — fork

**Students:**
- `GET /students/tests` — доступные тесты
- `POST /students/tests/{id}/start` — начать
- `POST /students/attempts/{id}/submit` — завершить
- `GET /students/progress` — прогресс
- `GET /students/mastery/overview` — A/B/C статус

**GOSO:**
- `GET /goso/subjects`, `/goso/frameworks`, `/goso/outcomes`
- `GET /goso/frameworks/{id}/structure` — полная иерархия
- `CRUD /admin/*/paragraphs/{id}/outcomes` — маппинг

**Rich Content (SUPER_ADMIN / School ADMIN):**
- `GET/PUT /admin/*/paragraphs/{id}/content` — текст объяснения, карточки
- `POST /admin/*/paragraphs/{id}/content/{audio|slides|video}` — загрузка медиа
- `DELETE /admin/*/paragraphs/{id}/content/{audio|slides|video}` — удаление медиа

---

## 8. Структура БД

**Полная схема:** см. `docs/database_schema.md`

### 8.1 Основные таблицы

| Категория | Таблицы |
|-----------|---------|
| Core | schools, users |
| Content | textbooks, chapters, paragraphs, paragraph_contents, paragraph_embeddings |
| Tests | tests, questions, question_options |
| Progress | test_attempts, test_attempt_answers, paragraph_mastery, chapter_mastery, mastery_history |
| Users | students, teachers, parents, school_classes, class_students, class_teachers, parent_students |
| GOSO | subjects, frameworks, goso_sections, goso_subsections, learning_outcomes, paragraph_outcomes |
| Sync | sync_queue |

### 8.2 Ключевые поля

**Изоляция:**
- `school_id` — во всех таблицах (NULL для глобального контента)

**Soft delete:**
- `deleted_at`, `is_deleted` — в моделях с SoftDeleteMixin

**Timestamps:**
- `created_at`, `updated_at` — во всех таблицах

---

## 9. RAG Service (планируется)

### 9.1 Компоненты

```
ParagraphEmbedding (vector 1536) → pgvector index → LangChain → OpenAI
```

### 9.2 Логика

1. Генерация embeddings для параграфов (OpenAI text-embedding-3-small)
2. Векторный поиск релевантных параграфов
3. Генерация персонализированного пояснения с учётом:
   - Текста вопроса
   - Ответа ученика
   - Правильного ответа
   - Уровня mastery (A/B/C)

---

## 10. Offline Sync (планируется)

### 10.1 Принцип

```
Mobile App → Local DB → sync_queue → POST /sync/process → Server DB
```

### 10.2 Conflict Resolution

- Last-write-wins для простых полей
- Server-wins для критичных данных (scores)
- `client_timestamp` для ordering

---

## 11. Приложения проекта

### 11.1 Структура репозитория

```
ai_mentor/
├── backend/              # FastAPI API
├── admin-v2/             # Admin Panel (Next.js) — ACTIVE
├── student-app/          # Student App (Next.js) — ACTIVE
└── frontend/             # Старый React Admin — DEPRECATED
```

### 11.2 Приложения и роли

| Приложение | URL | Роли | Стек |
|------------|-----|------|------|
| **Admin Panel** | admin.ai-mentor.kz | SUPER_ADMIN, School ADMIN | Next.js 15, shadcn/ui |
| **Student App** | ai-mentor.kz | STUDENT | Next.js 15, shadcn/ui |
| **Backend API** | api.ai-mentor.kz | Все роли | FastAPI, PostgreSQL |

### 11.3 Admin Panel (`admin-v2/`)

**Назначение:** Управление контентом и пользователями

**Функции по ролям:**

| SUPER_ADMIN | School ADMIN |
|-------------|--------------|
| Управление школами | Ученики, учителя, классы |
| Глобальные учебники | Школьная библиотека |
| Глобальные тесты | Школьные тесты |
| ГОСО справочники | Кастомизация контента |
| Rich Content параграфов | Rich Content параграфов |

**Структура:**
```
admin-v2/src/
├── app/[locale]/(dashboard)/
│   ├── schools/           # SUPER_ADMIN
│   ├── textbooks/         # SUPER_ADMIN
│   ├── tests/             # SUPER_ADMIN
│   ├── goso/              # SUPER_ADMIN
│   ├── students/          # School ADMIN
│   ├── teachers/          # School ADMIN
│   └── classes/           # School ADMIN
├── lib/api/               # API clients
└── components/            # UI компоненты
```

### 11.4 Student App (`student-app/`)

**Назначение:** Обучение и прохождение тестов для учеников

**Функции:**
- Google OAuth авторизация
- Онбординг (код школы + профиль)
- Навигация: Предметы → Главы → Параграфы
- Изучение параграфов (текст, аудио, карточки)
- Встроенные вопросы (embedded questions)
- Самооценка (self-assessment)
- Прохождение тестов

**Learning Flow:**
```
intro → content → practice → summary → completed
```

**Структура:**
```
student-app/src/
├── app/[locale]/
│   ├── (auth)/login/      # Google OAuth
│   ├── onboarding/        # Регистрация
│   └── (app)/
│       ├── subjects/      # Предметы
│       ├── chapters/      # Главы
│       └── paragraphs/    # Параграфы
├── lib/api/               # API clients
└── components/learning/   # Learning компоненты
```

### 11.5 Backend (`backend/`)

**Структура:**
```
backend/app/
├── main.py                # FastAPI app
├── core/                  # Config, security, database
├── models/                # SQLAlchemy models
├── schemas/               # Pydantic schemas
├── repositories/          # Data access layer
├── services/              # Business logic
├── api/v1/                # Endpoints
│   ├── auth.py            # Все роли
│   ├── admin_global.py    # SUPER_ADMIN
│   ├── admin_school.py    # School ADMIN
│   ├── students.py        # STUDENT
│   ├── teachers.py        # TEACHER
│   ├── goso.py            # Read-only
│   ├── rag.py             # RAG endpoints
│   └── chat.py            # Chat endpoints
└── middleware/            # RLS, tenancy
```

---

## 12. Ссылки на документацию

| Документ | Описание |
|----------|----------|
| `CLAUDE.md` | Инструкции для AI, команды, credentials |
| `IMPLEMENTATION_STATUS.md` | Прогресс итераций |
| `database_schema.md` | Детальная схема БД |
| `GOSO_INTEGRATION_PLAN.md` | План интеграции ГОСО |
| `PARAGRAPH_RICH_CONTENT_PLAN.md` | План Rich Content параграфов |
| `ADMIN_PANEL.md` | Спецификация админ панели |
| `migrations_quick_guide.md` | Работа с миграциями |
