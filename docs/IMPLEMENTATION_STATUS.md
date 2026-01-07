# Статус реализации AI Mentor

> **Назначение документа:** Прогресс итераций, что завершено, что в работе.
>
> **Связанные документы:**
> - `CLAUDE.md` — инструкции для AI-агентов, команды, credentials
> - `docs/ARCHITECTURE.md` — техническая архитектура, RBAC, алгоритмы

**Прогресс:** 85% (11/13 итераций) | **Последнее обновление:** 2025-12-23

**Production URLs:**
- Student App: https://ai-mentor.kz
- Admin Panel: https://admin.ai-mentor.kz
- Teacher App: https://teacher.ai-mentor.kz (pending deploy)
- API Docs: https://api.ai-mentor.kz/docs

---

## Завершённые итерации

### Итерации 1-3: Инфраструктура (2025-10-28 — 2025-10-29)
- PostgreSQL 16 + pgvector 0.8.1
- 28 таблиц, миграции 001-009
- JWT аутентификация, RBAC (5 ролей: SUPER_ADMIN, ADMIN, TEACHER, STUDENT, PARENT)
- FastAPI + async SQLAlchemy

### Итерация 4A-4B: Content Management API (2025-10-30)
**51 endpoint** для управления контентом:
- SUPER_ADMIN (`/admin/global/*`): CRUD textbooks, chapters, paragraphs, tests, questions, options
- School ADMIN (`/admin/school/*`): то же + fork/customize глобального контента
- Гибридная модель: `school_id = NULL` для глобального контента

### Итерация 5A-5F: Admin Panel (2025-10-30 — 2025-11-06)
**React Admin v5 + Material-UI v5:**
- SUPER_ADMIN: управление школами (7 endpoints), глобальные учебники/тесты
- School ADMIN: пользователи (35 endpoints), классы, библиотека контента
- Rich Text Editor: TinyMCE + KaTeX (LaTeX формулы)
- E2E тесты: Playwright (75+ тестов), Unit: Vitest (42 теста)
- Bundle: 373 KB gzipped

### Итерация 6: RLS & Multi-tenancy (2025-11-06)
- 27 таблиц с RLS policies (FORCE ROW LEVEL SECURITY)
- TenancyMiddleware: автоматическая установка tenant context из JWT
- Роль `ai_mentor_app` (non-superuser) для runtime
- Perfect isolation: школы не видят данные друг друга

### Итерация 7: Student API (2025-01-07)
**5 endpoints** для прохождения тестов:
- `GET /students/tests` — доступные тесты
- `POST /students/tests/{id}/start` — начать тест
- `GET /students/attempts/{id}` — детали попытки
- `POST /students/attempts/{id}/submit` — завершить тест
- `GET /students/progress` — прогресс по параграфам

**Services:**
- GradingService: автопроверка 4 типов вопросов (SINGLE/MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER)
- MasteryService: обновление ParagraphMastery после FORMATIVE/SUMMATIVE тестов

### Итерация 8: Mastery Service — алгоритм A/B/C (2025-01-07)
Группировка студентов по уровню мастерства:
- **Группа A:** ≥85% правильных, стабильные результаты
- **Группа B:** 60-84% правильных
- **Группа C:** <60% или нестабильные результаты

**Алгоритм:**
- Weighted average последних 5 попыток: `[0.35, 0.25, 0.20, 0.12, 0.08]`
- Анализ тренда (улучшение/ухудшение)
- Консистентность (std_dev)
- MasteryHistory при изменении уровня

**Endpoints:**
- `GET /students/mastery/chapter/{id}` — mastery по главе
- `GET /students/mastery/overview` — общий обзор

### Итерация 8B: GOSO Integration (2025-12-09 — 2025-12-16)
Интеграция государственного стандарта образования РК:

**Структура данных:**
```
subjects → frameworks → goso_sections → goso_subsections → learning_outcomes
                                                                  ↓
                                                         paragraph_outcomes (M:N)
```

**16 API endpoints:**
- Read-only (`/goso/*`): subjects, frameworks, outcomes, structure
- Admin (`/admin/*/paragraphs/{id}/outcomes`): маппинг параграф↔цели

**Импортированные данные (пилот):**
| Сущность | Кол-во |
|----------|--------|
| subjects | 1 (История КЗ) |
| frameworks | 1 (ГОСО 2023) |
| goso_sections | 4 |
| goso_subsections | 9 |
| learning_outcomes | 164 (5-9 кл.) |

### Итерация 8C: Paragraph Rich Content (2025-12-18)
Обогащённый контент параграфов (объяснения, аудио, слайды, видео, карточки):

**Backend:**
- Таблица `paragraph_contents` с RLS политиками
- 10 API endpoints для SUPER_ADMIN и School ADMIN
- `ParagraphContentService` для загрузки медиа файлов

**Frontend (Admin Panel v2):**
- Страница редактирования контента параграфа
- Компоненты: MediaUploader (drag & drop), CardsEditor, LanguageSwitcher
- Поддержка двух языков: RU/KK

**Лимиты файлов:** Audio 50MB, Slides 50MB, Video 200MB

**Детальный план:** `docs/PARAGRAPH_RICH_CONTENT_PLAN.md`

### Итерация 9: Student Interface MVP (2025-12-18)
**Студенческое веб-приложение для обучения (Next.js 15)**

**Технологии:**
- Next.js 15 (App Router) + TypeScript
- TanStack Query для data fetching
- next-intl (ru/kk локализация)
- Tailwind CSS + shadcn/ui
- Google OAuth авторизация

**Реализованные страницы:**
- `/login` — авторизация через Google
- `/onboarding` — ввод кода школы + профиль
- `/` — главная с приветствием и списком предметов
- `/subjects/[id]` — учебник с главами
- `/chapters/[id]` — глава с параграфами
- `/paragraphs/[id]` — изучение параграфа

**Learning Flow (страница параграфа):**
- StepIndicator: intro → content → practice → summary → completed
- Табы контента: Текст / Аудио / Карточки
- EmbeddedQuestion: встроенные вопросы (single/multiple choice, true/false)
- SelfAssessment: самооценка после изучения (understood/questions/difficult)
- Прогресс сохраняется в БД

**Backend дополнения:**
- Миграция: `embedded_questions`, `student_embedded_answers`
- Колонки в `student_paragraphs`: `current_step`, `self_assessment`
- 5 новых endpoints в `/students/*`

**Этапы:**
- [x] Этап 1: Инфраструктура (auth, layout, deploy)
- [x] Этап 2: Навигация (главная → предмет → глава → параграф)
- [x] Этап 3: Изучение параграфа (learning flow + Rich Content)
- [x] Этап 4: Практика (embedded questions + self-assessment)
- [ ] Этап 5: Профиль пользователя
- [ ] Этап 6: E2E тесты

**Production:** https://ai-mentor.kz (контейнер `ai_mentor_student_app_prod:3006`)

**План:** `docs/STUDENT_INTERFACE_PLAN.md`

### Итерация 10: RAG Service — персонализированные пояснения (2025-12-19)
**Retrieval-Augmented Generation для объяснения учебного материала**

**Архитектура:**
- **Embeddings:** Jina AI (jina-embeddings-v3, 1024 dims) — бесплатно 1M токенов/мес
- **Vector DB:** pgvector с IVFFlat индексом
- **LLM:** Cerebras (llama-3.3-70b) — direct API, fastest inference

**Персонализация A/B/C:**
- **Level A:** Краткий, продвинутый стиль для сильных учеников (≥85%)
- **Level B:** Сбалансированный с примерами (60-84%)
- **Level C:** Простой, пошаговый для учеников, требующих поддержки (<60%)

**API Endpoints (5):**
| Endpoint | Роль | Описание |
|----------|------|----------|
| `POST /rag/explain` | STUDENT | Объяснить вопрос/концепцию |
| `POST /rag/paragraphs/{id}/explain` | STUDENT | Объяснить параграф |
| `POST /rag/admin/global/paragraphs/{id}/embeddings` | SUPER_ADMIN | Генерация embeddings |
| `GET /rag/admin/global/paragraphs/{id}/embeddings` | SUPER_ADMIN | Статус embeddings |
| `POST /rag/admin/global/textbooks/{id}/embeddings` | SUPER_ADMIN | Batch для учебника |

**Файловая структура:**
```
backend/app/
├── api/v1/rag.py              # API endpoints
├── services/
│   ├── rag_service.py         # RAG orchestration
│   ├── embedding_service.py   # Jina/OpenAI embeddings
│   └── llm_service.py         # Cerebras/OpenRouter LLM
├── repositories/
│   └── embedding_repo.py      # Vector search
└── schemas/rag.py             # Pydantic models
```

**Стоимость:** $0 (бесплатные тиры Jina + Cerebras)

**Документация:** `docs/RAG_SERVICE.md`

---

## Следующие итерации

---

### ✅ Итерация 11: Teacher Dashboard (ВЫПОЛНЕНО — 2025-12-23)

**Backend API — ВЫПОЛНЕНО:**
- [x] `GET /teachers/dashboard` — обзор dashboard
- [x] `GET /teachers/classes` — список классов учителя
- [x] `GET /teachers/classes/{id}` — детали класса со студентами
- [x] `GET /teachers/classes/{id}/overview` — аналитика класса
- [x] `GET /teachers/classes/{id}/mastery-distribution` — распределение A/B/C
- [x] `GET /teachers/classes/{id}/students/{sid}/progress` — прогресс студента
- [x] `GET /teachers/students/{id}/mastery-history` — история mastery
- [x] `GET /teachers/analytics/struggling-topics` — проблемные темы
- [x] `GET /teachers/analytics/mastery-trends` — тренды
- [x] CRUD `/teachers/assignments` — управление заданиями (stubs)
- [x] `TeacherAnalyticsService` — бизнес-логика аналитики

**Backend файлы:**
- `backend/app/api/v1/teachers.py` (320 строк)
- `backend/app/services/teacher_analytics_service.py` (480 строк)
- `backend/app/schemas/teacher_dashboard.py` (280 строк)

**Frontend — ВЫПОЛНЕНО:**
- [x] Создать teacher-app (Next.js 15)
- [x] Dashboard страница (stats, classes list, mastery distribution)
- [x] Classes list и detail с таблицей учеников
- [x] Student progress view (chapters, tests, mastery history tabs)
- [x] Analytics pages (struggling topics, mastery trends)
- [x] Google OAuth авторизация (teacher role only)
- [x] RU/KZ локализация

**Frontend файлы (38 файлов, 11660 строк):**
- `teacher-app/src/app/[locale]/(dashboard)/page.tsx` — Dashboard
- `teacher-app/src/app/[locale]/(dashboard)/classes/` — Classes pages
- `teacher-app/src/app/[locale]/(dashboard)/analytics/page.tsx` — Analytics
- `teacher-app/src/components/dashboard/` — StatCard, MasteryBadge, MasteryDistributionChart
- `teacher-app/Dockerfile` — Production build

**Build:** 102 KB first load JS, все страницы компилируются успешно

**Pending:** Деплой на teacher.ai-mentor.kz

### ⏳ Итерация 12: Offline Sync Service
**Задачи:**
- [ ] SyncQueue management
- [ ] `POST /sync/queue` — добавление операций
- [ ] `POST /sync/process` — обработка очереди
- [ ] Conflict resolution
- [ ] `GET /sync/status`

### ⏳ Итерация 13: Тестирование и документация
**Задачи:**
- [ ] Unit тесты для всех сервисов (coverage >80%)
- [ ] Integration тесты для API
- [ ] RBAC тесты для всех ролей
- [ ] seed_data.py с тестовыми данными
- [ ] Полная API документация

---

## Статистика

| Метрика | Значение |
|---------|----------|
| Завершено итераций | 11/13 (85%) |
| Таблиц в БД | 37+ |
| Миграций | 19+ |
| API endpoints | 145+ |
| Backend тестов | 51+ |
| Frontend тестов | 117 (42 unit + 75 E2E) |
| Student App компонентов | 15+ |
| Teacher App компонентов | 12+ |

---

## Ключевые файлы

| Категория | Путь |
|-----------|------|
| Архитектура | `docs/ARCHITECTURE.md` |
| Схема БД | `docs/database_schema.md` |
| Миграции | `docs/migrations_quick_guide.md` |
| GOSO план | `docs/GOSO_INTEGRATION_PLAN.md` |
| Rich Content план | `docs/PARAGRAPH_RICH_CONTENT_PLAN.md` |
| Student Interface план | `docs/STUDENT_INTERFACE_PLAN.md` |
| Admin Panel | `docs/ADMIN_PANEL.md` |
| Деплой | `deploy.sh`, `deploy-infra.sh` |

---

## Session Logs (детальные логи итераций)

Для детальной информации о конкретной итерации см. файлы `SESSION_LOG_*.md` в корне проекта:
- `SESSION_LOG_Iteration5A_*.md` — Admin Panel setup
- `SESSION_LOG_Iteration5B_*.md` — Rich Text Editor
- `SESSION_LOG_Iteration5C_*.md` — Tests CRUD
- `SESSION_LOG_Iteration5D_*.md` — Users & Classes
- `SESSION_LOG_Iteration7_*.md` — Student API
- `SESSION_LOG_Iteration_8_*.md` — Mastery A/B/C
- `SESSION_LOG_GOSO_*.md` — GOSO Integration
