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

---

## Commands

### Database
```bash
docker compose up -d postgres                    # Запуск PostgreSQL
cd backend && alembic upgrade head               # Миграции
cd backend && alembic revision --autogenerate -m "desc"  # Новая миграция
docker exec -it ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db
```

### Deploy
```bash
./deploy.sh              # Умный деплой (анализ изменений)
./deploy.sh backend      # Только backend
./deploy-infra.sh status # Статус сервисов
./deploy-infra.sh logs backend
```

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

### API префиксы
- `/api/v1/admin/global/*` — SUPER_ADMIN
- `/api/v1/admin/school/*` — School ADMIN
- `/api/v1/students/*` — STUDENT
- `/api/v1/teachers/*` — TEACHER
