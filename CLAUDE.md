# CLAUDE.md

Инструкции для Claude Code при работе с этим репозиторием.

## Project Overview

**AI Mentor** — адаптивная образовательная платформа для школьников 7-11 классов.

**Приложения:**
| Приложение | Папка | Роли | URL |
|------------|-------|------|-----|
| Admin Panel | `admin-v2/` | SUPER_ADMIN, School ADMIN | admin.ai-mentor.kz |
| Student App | `student-app/` | STUDENT | ai-mentor.kz |
| Teacher App | `teacher-app/` | TEACHER | teacher.ai-mentor.kz |
| Backend API | `backend/` | Все | api.ai-mentor.kz |

**SUPER_ADMIN:** глобальный контент, школы, ГОСО
**School ADMIN:** ученики, учителя, классы, школьный контент

**Документация:**
| Документ | Назначение |
|----------|------------|
| `docs/ARCHITECTURE.md` | Техническая архитектура, RBAC, алгоритмы |
| `docs/IMPLEMENTATION_STATUS.md` | Прогресс итераций, статистика |
| `docs/TEACHER_APP.md` | Teacher Dashboard (API, Frontend, Deploy) |
| `docs/REFACTORING_SERVICES.md` | План рефакторинга Services |
| `docs/RAG_SERVICE.md` | RAG сервис (Jina + Cerebras) |
| `docs/CHAT_SERVICE.md` | Chat API |
| `docs/database_schema.md` | Схема БД |
| `docs/TASK_SELF_ASSESSMENT_BACKEND.md` | ТЗ самооценки ученика (этапы 1-2 готовы) |
| `docs/API_SELF_ASSESSMENT.md` | API документация самооценки для мобильных |
| `docs/AI_MEMORY.md` | 3-слойная память ИИ-репетитора (MVP) |

---

## Commands

### Database
```bash
docker compose up -d postgres                    # Запуск PostgreSQL
cd backend && alembic upgrade head               # Миграции
cd backend && alembic revision --autogenerate -m "desc"  # Новая миграция
docker exec -it ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db
```

### Testing
```bash
# Запуск всех тестов (из корня проекта, venv активирован)
source .venv/bin/activate
TEST_DB_HOST=localhost TEST_DB_PORT=5435 python -m pytest backend/tests/ -v --tb=short

# Запуск конкретного файла
TEST_DB_HOST=localhost TEST_DB_PORT=5435 python -m pytest backend/tests/test_quiz_api.py -v

# С покрытием
TEST_DB_HOST=localhost TEST_DB_PORT=5435 python -m pytest backend/tests/ --cov=backend/app --cov-report=html
```

### Deploy
```bash
./deploy.sh              # Умный деплой (анализ изменений)
./deploy.sh backend      # Только backend
./deploy.sh teacher-app  # Только teacher-app
./deploy-infra.sh status # Статус сервисов
./deploy-infra.sh logs backend
```

---

## CI/CD (GitHub Actions)

**Конфиг:** `.github/workflows/ci.yml`
**Репозиторий:** `Rus9136/ai_mentor` на GitHub

### ОБЯЗАТЕЛЬНО: Проверка CI после push

**После каждого `git push` в main (если затронут `backend/`) агент ОБЯЗАН:**
1. Подождать ~3 минуты
2. Выполнить `gh run list --limit 1` для проверки статуса
3. Если `failure` — выполнить `gh run view <id> --log-failed` и починить
4. Сообщить пользователю результат: CI зелёный ✓ или красный ✗

### Что запускается

CI автоматически запускается при **push в main** и **PR в main** (только при изменениях в `backend/`):

1. **test** — pytest регрессионные тесты против PostgreSQL (pgvector:pg16) service container

### Как это работает

- Service container поднимает PostgreSQL с базой `ai_mentor_test_db`
- Тесты используют `db_session` фикстуру (DROP/CREATE schema на каждый тест)
- Тестовая БД **отдельная** от продакшена — безопасно

### Регрессионные тесты

| Файл | Что покрывает | Тестов |
|------|---------------|--------|
| `test_onboarding_partial_state.py` | Partial onboarding (school_id без Student) | 4 |
| `test_join_request_approval.py` | Одобрение заявки (MissingGreenlet fix) | 6 |
| `test_route_conflicts.py` | Route ordering (/{id} vs /static-path) | 6 |

### ВАЖНО для агента

- **Перед деплоем** на прод: убедись что CI зелёный (или запусти тесты локально)
- **При добавлении нового endpoint:** написать хотя бы 1 интеграционный тест
- **При добавлении route с path parameter `/{id}`:** проверить, что статические routes (`/list`, `/stats`, etc.) объявлены **до** `/{id}` в роутере — иначе FastAPI поймает строку как id
- **При изменении async кода с relationships:** не обращаться к lazy-loaded relationships — использовать `selectinload()` или прямой SQL запрос
- **Тестовая БД:** `ai_mentor_test_db` на порту **5435** (тот же PostgreSQL контейнер что и прод, но отдельная БД)

---

## Production Deployment (ВАЖНО)

### Контейнеры и порты

| Сервис | Контейнер | Внутренний порт | Локальный порт |
|--------|-----------|-----------------|----------------|
| Backend API | `ai_mentor_backend_prod` | 8000 | **8020** |
| Teacher App | `ai_mentor_teacher_app_prod` | 3007 | 3007 |
| Student App | `ai_mentor_student_app_prod` | 3000 | 3000 |
| Admin Panel | `ai_mentor_admin_v2_prod` | 3000 | 3001 |
| PostgreSQL | `ai_mentor_postgres_prod` | 5432 | **5435** |

**ВАЖНО:** Backend слушает на порту **8020** локально, не 8000!

### Проверка статуса

```bash
# Статус всех контейнеров
docker ps --filter "name=ai_mentor" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Health check backend
curl -s http://localhost:8020/health

# Health check teacher-app
curl -s http://localhost:3007/
```

### Ручной деплой (если ./deploy.sh не работает)

```bash
# 1. Пересобрать образ
docker compose -f docker-compose.infra.yml build backend --no-cache
docker compose -f docker-compose.infra.yml build teacher-app --no-cache

# 2. Перезапустить контейнер
docker compose -f docker-compose.infra.yml up -d backend --force-recreate
docker compose -f docker-compose.infra.yml up -d teacher-app --force-recreate

# 3. Проверить логи
docker logs ai_mentor_backend_prod --tail 30
docker logs ai_mentor_teacher_app_prod --tail 20
```

### Troubleshooting

**Ошибка "container name already in use":**
```bash
docker rm -f ai_mentor_backend_prod
docker compose -f docker-compose.infra.yml up -d backend
```

**Ошибка "password authentication failed for user ai_mentor_app":**
```bash
# 1. Проверить какой пароль использует контейнер
docker exec ai_mentor_backend_prod env | grep POSTGRES_PASSWORD

# 2. Установить этот же пароль в PostgreSQL
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db \
  -c "ALTER USER ai_mentor_app WITH PASSWORD 'пароль_из_шага_1';"

# 3. Перезапустить backend
docker restart ai_mentor_backend_prod
```

**КРИТИЧНО: Пароль PostgreSQL**
- Пароль берётся из `.env` в корне проекта (переменная `POSTGRES_PASSWORD`)
- НЕ используй спецсимволы `@`, `!`, `#` в пароле — asyncpg может неправильно их обрабатывать
- НИКОГДА не хардкодить пароли в этом файле — используй только `.env`

### Nginx (внешний доступ)

Nginx проксирует запросы:
- `api.ai-mentor.kz` → `localhost:8020`
- `teacher.ai-mentor.kz` → `localhost:3007`
- `ai-mentor.kz` → `localhost:3000`
- `admin.ai-mentor.kz` → `localhost:3001`

### Code Quality
```bash
black backend/           # Форматирование
ruff check backend/      # Линтинг
```

---

## Database Credentials

**Две роли PostgreSQL:**
- `ai_mentor_user` (SUPERUSER) — миграции
- `ai_mentor_app` — runtime с RLS

**Пароли:** только в `backend/.env` (не в git!)

**ВАЖНО для AI-агентов:**
- НИКОГДА не хардкодить пароли
- `alembic/env.py` читает credentials из env vars

---

## Test Credentials

**Admin:**
- SUPER_ADMIN: `superadmin@aimentor.com` / `admin123`
- School ADMIN: `school.admin@test.com` / `admin123`

**Students (School 7):**
- `student1@school001.com` / `student123`

**Teachers (School 7):**
- `teacher.math@school001.com` / `teacher123`

---

## Code Architecture Standards (ОБЯЗАТЕЛЬНО)

### Лимиты размера файлов

| Тип файла | Максимум | Действие при превышении |
|-----------|----------|-------------------------|
| API endpoint | **400 строк** | Разбить на субмодули |
| Service | **300 строк** | Выделить отдельные services |
| Repository | **250 строк** | Следить за SRP |

### Layered Architecture

```
API Layer (thin)     → Валидация, авторизация, вызов Service
       ↓
Service Layer        → Бизнес-логика, транзакции, алгоритмы
       ↓
Repository Layer     → CRUD, SQL запросы
```

### Когда создавать Service

**Создавай если:**
- Логика в 2+ endpoints
- Алгоритм > 20 строк
- Операция с 2+ repositories
- Интеграция с внешним сервисом

### Reusable Dependencies

```python
# Используй готовые dependencies вместо дублирования:
async def get_student_from_user(...) -> Student
async def get_paragraph_with_access(...) -> Paragraph
async def get_current_user_school_id(...) -> int
```

### Anti-patterns (ЗАПРЕЩЕНО)

1. **God Files** — файлы > 500 строк с разными доменами
2. **Дублирование проверок** — копипаста access check в каждом endpoint
3. **Бизнес-логика в endpoints** — расчёты должны быть в Services
4. **N+1 запросы** — использовать batch queries

### Checklist перед PR

- [ ] Файл < 400 строк
- [ ] Нет дублирования (вынесено в dependency/service)
- [ ] Бизнес-логика в Service
- [ ] Нет N+1 запросов
- [ ] school_id изоляция проверена
- [ ] Response schemas указаны

---

## Development Rules

### КРИТИЧНО — Изоляция данных

```python
# ВСЕГДА используй school_id из токена:
@router.get("/students")
async def get_students(
    school_id: int = Depends(get_current_user_school_id),  # ИЗ ТОКЕНА!
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Student).where(Student.school_id == school_id)
    )
```

**Правила:**
- НИКОГДА не принимай `school_id` от клиента
- Для глобального контента: `.where(Model.school_id.is_(None))`

### Pydantic Schemas

```python
class StudentCreate(BaseModel):
    first_name: str

class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
```

### Async/Await

Весь проект async — все запросы к БД через `await`.

### КРИТИЧНО — RLS-политики при миграциях

При создании или изменении RLS-политик **обязательно проверяй консистентность** всех 4 операций (SELECT, INSERT, UPDATE, DELETE):

**Правило:** если SELECT-политика разрешает доступ по `user_id`, то UPDATE и DELETE тоже **обязаны** включать `user_id`. Иначе пользователь сможет прочитать запись, но не сможет её изменить → `StaleDataError`.

**Проверочный запрос после каждой RLS-миграции:**
```sql
-- Таблицы, где SELECT имеет user_id, а UPDATE — нет (баг!)
SELECT tablename FROM pg_policies WHERE schemaname='public' AND cmd='r'
  AND qual LIKE '%current_user_id%'
EXCEPT
SELECT tablename FROM pg_policies WHERE schemaname='public' AND cmd='w'
  AND qual LIKE '%current_user_id%';
-- Результат должен быть пустым (0 rows)
```

**Автотест:** `backend/tests/test_rls_policy_audit.py` — запускать перед деплоем.

---

## Git Conventions

```bash
feat: новая функциональность
fix: исправление бага
docs: документация
refactor: рефакторинг

# Всегда добавляй в конец:
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Quick Reference

```bash
# Статус миграций
cd backend && alembic current -v

# Поиск использования модели
grep -r "from app.models.textbook import" backend/

# Схема таблицы
docker exec -it ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\d textbooks"
```

---

## Key Concepts (краткий справочник)

**Подробности см. в `docs/ARCHITECTURE.md`**

### Гибридная модель контента
- `school_id = NULL` → глобальный контент (SUPER_ADMIN)
- `school_id = N` → школьный контент (School ADMIN)

### 5 ролей RBAC
SUPER_ADMIN → ADMIN → TEACHER → STUDENT → PARENT

### Два вида mastery (раздельные метрики)
- **Объективный** (`paragraph_mastery`) — от тестов, шкала 0.0–1.0, статусы struggling/progressing/mastered
- **Субъективный** (`paragraph_self_assessments`) — самооценка ученика, append-only, mastery_impact ±5.0

Они НЕ объединяются. Расхождение между ними — метакогнитивный сигнал для аналитики учителя.

### Самооценка ученика (Self-Assessment)
Ученик на шаге "Итоги" выбирает самооценку (`understood`/`questions`/`difficult`).
Сервер рассчитывает `mastery_impact` с корректировкой по `practice_score` и возвращает `next_recommendation`.
Поддержка идемпотентности для оффлайн-синхронизации.
- Сервис: `backend/app/services/self_assessment_service.py`
- API docs: `docs/API_SELF_ASSESSMENT.md`

### API префиксы
- `/api/v1/admin/global/*` — SUPER_ADMIN
- `/api/v1/admin/school/*` — School ADMIN
- `/api/v1/students/*` — STUDENT
- `/api/v1/teachers/*` — TEACHER
