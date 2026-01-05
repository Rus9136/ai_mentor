# PROJECT ANALYSIS REPORT: AI MENTOR

**Дата анализа:** 2026-01-05
**Версия:** 1.0
**Статус проекта:** 77% (10/13 итераций завершено)

---

## РЕЗЮМЕ

| Критерий | Оценка | Статус |
|----------|--------|--------|
| **Готовность к Production** | **65%** | Требуется доработка |
| **Готовность к Mobile разработке** | **40%** | Критические пробелы |
| **API Quality** | **8.5/10** | Хорошо |
| **Code Quality** | **6/10** | Средне |
| **Security** | **5/10** | Критические проблемы |
| **Test Coverage** | **35%** | Недостаточно |
| **Documentation** | **46%** | Частично |
| **Database** | **75%** | Хорошо |

---

## 1. API ENDPOINTS (199 endpoints)

### Сильные стороны

- **99% endpoints имеют response_model** — отлично задокументировано
- **REST стандарты соблюдены** — правильные HTTP методы и статусы
- **RBAC авторизация** — get_current_user, require_admin, require_student
- **School isolation** — school_id из токена, не от клиента

### Проблемы

- **40% endpoints без пагинации** — риск OOM при больших данных
- **50% без фильтров** — неоптимально для мобильных
- **Deprecated endpoint** в students/tests.py (нужно удалить)
- **Несогласованность именования** path parameters

### Статистика по модулям

| Модуль | Endpoints | Статус |
|--------|-----------|--------|
| Authentication | 6 | OK |
| Admin Global | 18 | OK |
| Admin School | 58 | OK |
| Students | 56 | OK |
| Teachers | 22 | OK |
| AI/RAG Services | 39 | OK |

### Детальный каталог endpoints

#### A. Authentication (6 endpoints)

| Метод | Path | Назначение | Response Schema |
|-------|------|------------|-----------------|
| POST | `/auth/login` | Вход по email/password | `TokenResponse` |
| POST | `/auth/refresh` | Обновить токен | `TokenResponse` |
| GET | `/auth/me` | Текущий пользователь | `UserResponse` |
| POST | `/auth/google` | Google OAuth вход | `GoogleLoginResponse` |
| POST | `/auth/onboarding/validate-code` | Проверить код приглашения | `ValidateCodeResponse` |
| POST | `/auth/onboarding/complete` | Завершить онбординг | `OnboardingCompleteResponse` |

#### B. Admin Global (18 endpoints)

- CRUD для Textbooks, Chapters, Paragraphs
- CRUD для Tests, Questions, QuestionOptions
- Paragraph Outcomes management

#### C. Admin School (58 endpoints)

- Content Management (15 endpoints)
- User Management: Students, Teachers, Parents, Classes (28 endpoints)
- Test Management (10 endpoints)
- Settings (2 endpoints)
- Paragraph Outcomes (3 endpoints)

#### D. Students (56 endpoints)

- Content: textbooks, chapters, paragraphs, navigation
- Learning: progress, self-assessment
- Mastery: chapter mastery, overview
- Tests: start, submit, attempts
- Homework: list, tasks, answers, results

#### E. Teachers (22 endpoints)

- Dashboard: classes, overview, mastery distribution
- Analytics: mastery history, struggling topics, trends
- Homework: CRUD, tasks, publishing, submissions, review

#### F. AI & Support Services (39 endpoints)

- RAG: explain, embeddings
- Chat: sessions, messages, admin prompts
- Upload: images, PDFs
- GOSO: subjects, frameworks, sections, outcomes
- Invitation Codes, Schools

---

## 2. КАЧЕСТВО КОДА

### Критические нарушения размера файлов

**22 файла превышают лимит 400 строк (стандарт проекта):**

| Файл | Строк | Проблема |
|------|-------|----------|
| `services/teacher_analytics_service.py` | 883 | God class, нарушает SRP |
| `api/v1/teachers_homework.py` | 699 | Бизнес-логика в endpoint |
| `services/homework_ai_service.py` | 643 | Смешанные ответственности |
| `schemas/homework.py` | 630 | 8 моделей + 50+ вложенных классов |
| `api/v1/admin_school/_dependencies.py` | 628 | 17 дублирующих функций |
| `services/student_content_service.py` | 626 | Требует разбиения |
| `models/homework.py` | 623 | 15 классов в одном файле |
| `services/mastery_service.py` | 582 | Множество методов |
| `api/v1/paragraph_contents.py` | 577 | 15 инстанциаций Repository |

### N+1 запросы (КРИТИЧНО)

**Файл:** `backend/app/api/v1/students/homework.py` (строки 520-565)

```python
# ПРОБЛЕМА: 2N дополнительных запросов
for task in homework.tasks:  # N tasks
    await repo.get_attempts_count(...)  # +1 query per task
    await repo.get_latest_submission(...)  # +1 query per task
```

**Решение:** Использовать batch queries

### Дублирование кода

- **233+ инстанциирования Repository** inline вместо Depends()
- **12 функций** с идентичной логикой валидации в `_dependencies.py`
- **44 инстанциирования HTTPException** в одном файле

### Рекомендации по рефакторингу

1. **Разбить `teacher_analytics_service.py` на:**
   - `MasteryCalculationService`
   - `StudentProgressService`
   - `ClassAnalyticsService`

2. **Использовать generic dependency:**
   ```python
   async def get_entity_for_school(repo, entity_id, school_id):
       # Общая логика для всех 17 функций
   ```

3. **Заменить inline Repository на Depends()**

---

## 3. БЕЗОПАСНОСТЬ

### КРИТИЧЕСКИЕ УЯЗВИМОСТИ

| # | Уязвимость | Severity | Файл | Строка |
|---|-----------|----------|------|--------|
| 1 | Hardcoded SECRET_KEY | CRITICAL | `core/config.py` | 67 |
| 2 | Логирование JWT payload | HIGH | `middleware/tenancy.py` | 51-52 |
| 3 | CORS allow_methods=["*"] | MEDIUM | `main.py` | 52-58 |
| 4 | Отсутствие rate limiting | MEDIUM | auth endpoints | - |
| 5 | Слабые требования к паролю | MEDIUM | `schemas/auth.py` | 12 |

### Детали критических проблем

#### 1. Hardcoded SECRET_KEY (CRITICAL)
```python
# backend/app/core/config.py:67
SECRET_KEY: str = "your-secret-key-here-change-in-production"
```
**Риск:** Все JWT токены могут быть поддельными

**Решение:**
```python
if settings.SECRET_KEY == "your-secret-key-here-change-in-production":
    raise RuntimeError("SECRET_KEY must be changed in production!")
```

#### 2. Логирование JWT payload (HIGH)
```python
# backend/app/middleware/tenancy.py:51-52
logger.info(f"TenancyMiddleware: Decoded payload: {payload}")
```
**Риск:** User data в plain text логах

**Решение:**
```python
logger.info(f"User authenticated: user_id={payload.get('sub')}, role={payload.get('role')}")
```

#### 3. CORS конфигурация (MEDIUM)
```python
# backend/app/main.py:52-58
allow_methods=["*"],  # ПРОБЛЕМА
allow_headers=["*"],  # ПРОБЛЕМА
```

**Решение:**
```python
allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
allow_headers=["Accept", "Content-Type", "Authorization"],
```

### Что реализовано правильно

- JWT с HS256 + refresh tokens
- RBAC с 5 ролями (SUPER_ADMIN, ADMIN, TEACHER, STUDENT, PARENT)
- RLS на уровне PostgreSQL
- bcrypt для паролей
- School isolation через токен
- File upload validation (MIME type, size)

---

## 4. ТЕСТОВОЕ ПОКРЫТИЕ

### Общая статистика

```
Всего тестов:         187
Тестовых файлов:      10
Строк тестового кода: 6,393

API Layer:            44% (18/41 endpoints)
Service Layer:        27% (6/22 services)
Repository Layer:      0% (0/27 repos)
ОБЩЕЕ:               ~35%
```

### Хорошо протестированные модули

| Service | Тесты | Покрытие |
|---------|-------|----------|
| HomeworkAIService | 35 | 100% |
| HomeworkAIParsing | 35 | 100% |
| MasteryService | 12 | 100% |
| StudentContentService | 25 | 100% |
| GradingService | 8 | 100% |
| StudentStatsService | 10 | 100% |

### Критические модули БЕЗ ТЕСТОВ

| Модуль | Файл | Риск |
|--------|------|------|
| Authentication | `api/v1/auth.py` | КРИТИЧЕСКИЙ |
| OAuth Google | `api/v1/auth_oauth.py` | КРИТИЧЕСКИЙ |
| LLM Integration | `services/llm_service.py` | ВЫСОКИЙ |
| Chat Service | `services/chat_service.py` | ВЫСОКИЙ |
| Teachers | `api/v1/teachers*.py` | ВЫСОКИЙ |
| File Upload | `api/v1/upload.py` | ВЫСОКИЙ |
| Все Repositories | 27 файлов | СРЕДНИЙ |

### Рекомендации

**Фаза 1 (критическая):**
- Тесты для auth.py (JWT, refresh, OAuth)
- RBAC тесты для всех endpoints

**Фаза 2 (важная):**
- Увеличить покрытие endpoints до 70%+
- Repository CRUD tests
- Concurrent access tests

---

## 5. БАЗА ДАННЫХ

### Статистика

- **32 основные модели**
- **154 индекса** (простые + composite + vector)
- **31 миграция** Alembic
- **RLS политики** на 30+ таблицах
- **pgvector** для embeddings

### Архитектура multi-tenancy

```
School (tenant root)
├── Users, Students, Teachers, Parents (school_id NOT NULL)
├── School Classes (school_id NOT NULL)
├── Textbooks, Tests (school_id NULLABLE - гибридная модель)
│   ├── Chapters → Paragraphs → Embeddings
│   └── Questions → Options
├── Progress tables (денормализованный school_id для RLS)
└── Homework (7 связанных таблиц)
```

### Проблемы

| Проблема | Severity | Решение |
|----------|----------|---------|
| RLS отсутствует для chat_sessions, homework | КРИТИЧНА | Добавить политики |
| Session переменные не гарантированы | КРИТИЧНА | Верифицировать в middleware |
| Несогласованность типов в RLS | ВЫСОКАЯ | Унифицировать cast |
| Нет партиционирования больших таблиц | ВЫСОКАЯ | Добавить для test_attempts, learning_activities |
| Отсутствуют CHECK constraints | СРЕДНЯЯ | grade_level, passing_score |

### Индексы (хорошее покрытие)

- School_id фильтрация: все таблицы
- Composite индексы: student_id + created_at, school_id + status
- Vector index: IVFFlat для paragraph_embeddings

---

## 6. ДОКУМЕНТАЦИЯ

### Существующая документация (85% для web)

| Документ | Строк | Полнота |
|----------|-------|---------|
| ARCHITECTURE.md | 471 | 95% |
| IMPLEMENTATION_STATUS.md | 265 | 90% |
| TEACHER_APP.md | 634 | 98% |
| CHAT_SERVICE.md | 771 | 95% |
| RAG_SERVICE.md | 566 | 95% |
| DEPLOYMENT.md | 100+ | 80% |
| CLAUDE.md | 227 | 90% |

### Критически отсутствует

| Документ | Влияние |
|----------|---------|
| **MOBILE_API_GUIDE.md** | iOS/Android разработчики не смогут работать |
| **SECURITY.md** | Потенциальные уязвимости |
| **MONITORING.md** | Нет alerting при сбоях |
| **ERROR_CODES.md** | Нестандартизированные ошибки |
| **TESTING_STRATEGY.md** | Нет целей покрытия |
| **DISASTER_RECOVERY.md** | Нет плана восстановления |

---

## 7. ГОТОВНОСТЬ К MOBILE РАЗРАБОТКЕ

### Статус: НЕ ГОТОВО (40%)

| Требование | Статус |
|-----------|--------|
| API Response Formats | Не документированы |
| Offline Sync Guide | Только план (Итерация 12) |
| Error Codes & Handling | Нет стандарта |
| Pagination в всех lists | 40% endpoints |
| Rate Limiting docs | Отсутствует |
| WebSocket/Real-time | Нет |
| SDK/Client Library | Нет |
| TLS Pinning Guide | Нет |

---

## 8. ПЛАН ДЕЙСТВИЙ

### Фаза 1: КРИТИЧЕСКИЕ (1-2 недели)

#### Безопасность
- [ ] Исправить SECRET_KEY — использовать только env vars
- [ ] Убрать логирование JWT payload
- [ ] Исправить CORS — явный список методов/headers
- [ ] Добавить rate limiting (slowapi)

#### Код
- [ ] Исправить N+1 в students/homework.py — batch queries
- [ ] Разбить файлы > 400 строк

### Фаза 2: ВЫСОКИЙ ПРИОРИТЕТ (2-4 недели)

- [ ] Тесты для auth.py (JWT, refresh, OAuth)
- [ ] RLS политики для chat_sessions, homework
- [ ] Пагинация для всех list endpoints
- [ ] Документация: SECURITY.md, MOBILE_API_GUIDE.md

### Фаза 3: ДЛЯ MOBILE (4-6 недель)

- [ ] Стандартизировать error responses
- [ ] Offline sync API (Итерация 12)
- [ ] WebSocket для real-time (опционально)
- [ ] SDK для React Native / Flutter
- [ ] TLS pinning guide

---

## 9. ИТОГОВАЯ РЕКОМЕНДАЦИЯ

### Для Production Web

**МОЖНО запускать** с условием исправления:
- 3 критических уязвимостей безопасности
- N+1 запросов в homework
- Добавления rate limiting

**Оценка работы:** 1-2 недели

### Для Mobile разработки

**НЕ ГОТОВО** — требуется:
- MOBILE_API_GUIDE.md
- Стандартизация error codes
- Пагинация на всех endpoints
- Offline sync API
- SDK или примеры интеграции

**Оценка работы:** 4-6 недель

---

## Приложения

### A. Файлы для исправления (критические)

```
backend/app/core/config.py:67              — SECRET_KEY
backend/app/middleware/tenancy.py:51-52    — JWT logging
backend/app/main.py:52-58                  — CORS
backend/app/api/v1/students/homework.py:520-565 — N+1
```

### B. Файлы для рефакторинга

```
backend/app/services/teacher_analytics_service.py (883 строк)
backend/app/api/v1/teachers_homework.py (699 строк)
backend/app/services/homework_ai_service.py (643 строк)
backend/app/api/v1/admin_school/_dependencies.py (628 строк)
```

### C. Тестовые файлы

```
backend/tests/test_homework_ai_service.py (35 тестов)
backend/tests/test_homework_ai_parsing.py (35 тестов)
backend/tests/test_mastery_service.py (12 тестов)
backend/tests/test_student_content_service.py (25 тестов)
backend/tests/conftest.py (fixtures)
```

---

**Отчет сгенерирован:** 2026-01-05
**Инструмент:** Claude Code Analysis
