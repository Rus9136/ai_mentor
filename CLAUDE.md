# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Mentor - адаптивная образовательная платформа для школьников (7-11 классы) с автоматической группировкой учеников по уровню мастерства (A/B/C). Multi-tenant SaaS решение с гибридной моделью контента.

**Текущий статус:** Итерация 3 завершена (25% проекта). Backend основа + JWT аутентификация работают. Следующая итерация: Content Management API.

**Важные документы:**
- `docs/IMPLEMENTATION_STATUS.md` - план из 12 итераций с текущим прогрессом
- `docs/ARCHITECTURE.md` - полное техническое задание
- `docs/ADMIN_PANEL.md` - детальная спецификация админ панели
- `docs/database_schema.md` - документация схемы БД
- `docs/migrations_quick_guide.md` - инструкции по работе с миграциями

## Common Commands

### Database Operations
```bash
# Запустить PostgreSQL
docker compose up -d postgres

# Применить миграции
cd backend && alembic upgrade head

# Создать новую миграцию
cd backend && alembic revision --autogenerate -m "описание"

# Откатить последнюю миграцию
cd backend && alembic downgrade -1

# Посмотреть текущую версию БД
cd backend && alembic current

# Подключиться к БД напрямую
docker exec -it ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db
```

**Database Credentials:**

Проект использует **две роли** PostgreSQL для разных целей:

1. **ai_mentor_user** (SUPERUSER) - для миграций
   - User: `ai_mentor_user`
   - Права: SUPERUSER (bypass RLS policies)
   - Почему нужен: RLS политики применяются даже к владельцу таблицы, но SUPERUSER может их обойти для создания/изменения схемы

2. **ai_mentor_app** (обычный пользователь) - для runtime
   - User: `ai_mentor_app`
   - Права: Обычный пользователь, RLS политики активны
   - Почему нужен: Обеспечивает multi-tenant изоляцию на уровне БД через RLS

**Где хранятся пароли (НЕ хардкодить в коде!):**

| Окружение | Файл | Переменная | Описание |
|-----------|------|------------|----------|
| Production & Local | `backend/.env` | `POSTGRES_PASSWORD` | Единый пароль для обеих ролей |
| Docker default | `docker-compose.infra.yml` | `${POSTGRES_PASSWORD:-ai_mentor_pass}` | Fallback если .env не задан |

**Файл `backend/.env` содержит все секреты и НЕ коммитится в git (в .gitignore).**

**Как работает подключение к БД:**

1. **Runtime (FastAPI приложение):**
   - Читает `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_DB` из environment
   - Использует роль `ai_mentor_app` (задаётся в `docker-compose.infra.yml`)

2. **Миграции (Alembic):**
   - `alembic/env.py` автоматически собирает URL из environment variables
   - Использует `quote_plus()` для URL-кодирования спецсимволов в пароле (`@`, `!`, и т.д.)
   - Всегда использует роль `ai_mentor_user` (SUPERUSER)
   - Fallback на `alembic.ini` если env vars не заданы (для локальной разработки)

**Важно для AI-агентов:**
- НИКОГДА не хардкодить пароли в коде, конфигах или документации
- Production пароль хранится ТОЛЬКО в `backend/.env` (файл не в git)
- `alembic.ini` содержит только fallback URL для локальной разработки (`ai_mentor_pass`)
- `alembic/env.py` автоматически собирает URL из env vars с URL-кодированием спецсимволов
- При деплое docker-compose читает `backend/.env` через `env_file` директиву

### Production Deployment

**Быстрый деплой (автоматический):**
```bash
# Умный деплой - автоматически определяет изменения и деплоит только нужное
./deploy.sh

# Принудительный деплой конкретного компонента
./deploy.sh backend      # Только backend
./deploy.sh frontend     # Только frontend
./deploy.sh full         # Полный деплой всего
```

**Что происходит автоматически:**
- Анализ git diff для определения изменений
- Сборка Docker образов только для измененных компонентов
- Применение миграций (если обнаружены новые)
- Healthcheck после деплоя
- Детальный вывод с прогрессом и ошибками

**Ручное управление инфраструктурой:**
```bash
# Запуск сервисов
./deploy-infra.sh start

# Остановка
./deploy-infra.sh stop

# Перезапуск
./deploy-infra.sh restart

# Статус
./deploy-infra.sh status

# Логи
./deploy-infra.sh logs backend
./deploy-infra.sh logs postgres

# Миграции
./deploy-infra.sh migrate

# Заполнить БД тестовыми данными (SUPER_ADMIN, School, Teachers, Students)
./deploy-infra.sh seed

# Backup БД
./deploy-infra.sh backup
```

**Production URLs:**
- Frontend: https://ai-mentor.kz
- Admin Panel: https://admin.ai-mentor.kz
- API: https://api.ai-mentor.kz
- API Docs: https://api.ai-mentor.kz/docs

### Testing
```bash
# Все тесты с покрытием
pytest

# Конкретный тест
pytest backend/tests/test_auth.py::test_login

# Запустить тестовую БД
docker compose --profile test up postgres_test
```

### Code Quality
```bash
# Форматирование (Black)
black backend/

# Линтинг (Ruff)
ruff check backend/

# Проверка типов (MyPy) - когда будет настроено
mypy backend/
```

### Test Credentials

**Administrators:**
- **SUPER_ADMIN:** superadmin@aimentor.com / admin123
- **School ADMIN:** school.admin@test.com / admin123

**Teachers (School 7 - "Тестовая школа №1"):**
- teacher.math@school001.com / teacher123 (Айгерим Нурсултанова - Математика)
- teacher.physics@school001.com / teacher123 (Асхат Жумабаев - Физика)
- teacher.chemistry@school001.com / teacher123 (Динара Сатыбалдиева - Химия)
- teacher.biology@school001.com / teacher123 (Нургуль Абишева - Биология)
- teacher.history@school001.com / teacher123 (Ержан Кенжебаев - История)

**Students (School 7 - "Тестовая школа №1"):**
- student1@school001.com / student123 (Алихан Султанов - 7-А класс)
- student2@school001.com / student123 (Аружан Есимова - 7-А класс)
- student3@school001.com / student123 (Нурислам Бекжанов - 8-Б класс)
- student4@school001.com / student123 (Жанель Кабдулова - 8-Б класс)
- student5@school001.com / student123 (Данияр Мухамедов - 9-В класс)
- student6@school001.com / student123 (Айым Сейдахметова - 9-В класс)
- student7@school001.com / student123 (Ернар Токаев - 10-А класс)
- student8@school001.com / student123 (Камила Нурланова - 10-А класс)

**Frontend:** http://localhost:5173

## Architecture & Key Concepts

### Двухуровневая система администрирования (Гибридная модель контента)

**Критически важная концепция:** Платформа имеет ДВА уровня контента:

1. **Глобальный контент** (`school_id = NULL`)
   - Создается SUPER_ADMIN
   - Доступен всем школам в режиме read-only
   - Учебники, тесты, главы, параграфы
   - Примеры: стандартные учебники "Алгебра 7 класс", "Физика 8 класс"

2. **Школьный контент** (`school_id = конкретная школа`)
   - Создается школьным ADMIN
   - Доступен только одной школе
   - Два типа:
     - **Собственный контент** - уникальные материалы школы
     - **Кастомизированный контент** - форк глобального учебника с флагом `is_customized=true` и ссылкой `global_textbook_id`

**Процесс кастомизации (fork):**
```python
# Школа хочет адаптировать глобальный учебник
POST /api/v1/admin/school/textbooks/{global_id}/customize

# Backend создает копию:
Textbook(
    school_id=current_school_id,      # привязка к школе
    global_textbook_id=global_id,     # ссылка на оригинал
    is_customized=True,                # флаг кастомизации
    title="Алгебра 7 класс (Школа №1)"
)
# + копируются все главы и параграфы
```

### Multi-tenancy & Data Isolation

**Изоляция на уровне БД через `school_id`:**
- Каждая модель прогресса имеет denormalized `school_id` (добавлено в миграции 008)
- Модели: `test_attempts`, `mastery_history`, `adaptive_groups`, `student_paragraphs`, `learning_sessions`, `learning_activities`, `sync_queue`
- Это позволяет:
  - Фильтровать без JOIN через students
  - Партицировать по школам в будущем
  - Применять Row Level Security (RLS) - планируется в Итерации 6

**Гибридная модель для контента:**
- `textbooks.school_id` - nullable (NULL = глобальный)
- `tests.school_id` - nullable (NULL = глобальный)
- `chapters`, `paragraphs`, `questions` - наследуют school_id от родителя

### User Roles (RBAC)

**5 ролей в системе:**
1. **SUPER_ADMIN** - управление глобальным контентом и школами (НЕ привязан к school_id)
2. **ADMIN** - управление школой, пользователями, классами, школьным контентом
3. **TEACHER** - просмотр своих классов, создание заданий, аналитика учеников
4. **STUDENT** - прохождение тестов, просмотр прогресса
5. **PARENT** - просмотр прогресса детей (read-only)

**Важно:** SUPER_ADMIN и ADMIN - это разные роли с разными правами. SUPER_ADMIN НЕ управляет конкретными школами, а ADMIN НЕ создает глобальный контент.

### Database Models Patterns

**Все модели наследуются от базовых классов:**

```python
# backend/app/models/base.py
class TimestampMixin:
    created_at  # автоматически при создании
    updated_at  # автоматически при обновлении

class SoftDeleteMixin:
    deleted_at  # дата удаления (NULL если не удалено)
    is_deleted  # булевый флаг

class BaseModel(Base, TimestampMixin):
    id  # Integer primary key, autoincrement

class SoftDeleteModel(Base, TimestampMixin, SoftDeleteMixin):
    id
```

**Используй:**
- `BaseModel` для сущностей без soft delete (School, User, SystemSetting)
- `SoftDeleteModel` для остального (Textbook, Test, Student, и т.д.)

**Важные модели:**
- `Textbook` - имеет `school_id` (nullable), `global_textbook_id`, `is_customized`
- `Test` - имеет `school_id` (nullable) для глобальных тестов
- `ParagraphEmbedding` - векторные embeddings (vector(1536)) для RAG с pgvector
- `TestAttempt` - имеет denormalized `school_id` для быстрой фильтрации
- `MasteryHistory` - история изменений уровня мастерства ученика

### Naming Conventions

**Database:**
- Таблицы: lowercase, snake_case, множественное число (`users`, `test_attempts`)
- Колонки: snake_case (`first_name`, `created_at`)
- Индексы: `ix_{table}_{column}` или `ix_{table}_{col1}_{col2}` для составных
- Foreign keys: автоматически с CASCADE DELETE

**Python:**
- Models: PascalCase (`User`, `TestAttempt`)
- Enums: PascalCase для класса, UPPER_CASE для значений (`UserRole.SUPER_ADMIN`)
- Services: snake_case файлы, PascalCase классы (`auth_service.py` -> `AuthService`)
- Repositories: то же (`user_repo.py` -> `UserRepository`)

**API Endpoints:**
- SUPER_ADMIN: `/api/v1/admin/global/*` и `/api/v1/admin/schools`
- School ADMIN: `/api/v1/admin/school/*`
- Teacher: `/api/v1/teachers/*`
- Student: `/api/v1/students/*`
- Parent: `/api/v1/parents/*`

## Development Principles (MVP Approach)

**Философия:** Это MVP - пиши качественный код, но избегай преждевременной оптимизации и сложности.

### КРИТИЧНО - Всегда обязательно

**1. Изоляция данных по school_id - НЕ ПРОПУСКАЙ НИКОГДА**

```python
# backend/app/api/dependencies.py
async def get_current_user_school_id(
    current_user: User = Depends(get_current_user)
) -> int:
    """Извлекает school_id из текущего пользователя"""
    if current_user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(400, "SUPER_ADMIN has no school_id")
    return current_user.school_id

# ВСЕГДА используй в endpoint'ах для фильтрации:
@router.get("/students")
async def get_students(
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    # Фильтр school_id обязателен!
    result = await db.execute(
        select(Student).where(Student.school_id == school_id)
    )
    return result.scalars().all()
```

**Правила изоляции:**
- ВСЕГДА добавляй `school_id = Depends(get_current_user_school_id)` в endpoints
- НИКОГДА не принимай `school_id` от клиента - только из `current_user`
- Для SUPER_ADMIN endpoints (глобальный контент) фильтруй `.where(Model.school_id.is_(None))`

**2. Pydantic схемы для Request/Response - обязательно**

```python
# Минимум: Request и Response схемы
class StudentCreate(BaseModel):
    first_name: str
    last_name: str

class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
    last_name: str
```

**3. Обработка ошибок - базовая**

```python
# Используй стандартные HTTPException
from fastapi import HTTPException

# Не найдено
if not student:
    raise HTTPException(404, f"Student {student_id} not found")

# Нет прав
if student.school_id != current_user.school_id:
    raise HTTPException(403, "Access denied")
```

### Упрощенная архитектура для MVP

**Структура кода:**

```
backend/app/
├── main.py                 # FastAPI app, CORS, middleware
├── core/
│   ├── config.py          # Settings (Pydantic Settings)
│   ├── security.py        # JWT функции
│   └── dependencies.py    # get_db, get_current_user, get_current_user_school_id
├── models/                # SQLAlchemy (готово)
├── schemas/               # Pydantic Request/Response
└── api/v1/
    ├── auth.py           # Login, register
    ├── students.py       # CRUD endpoints
    └── textbooks.py      # CRUD endpoints
```

**Двухслойная архитектура на старте:**
```
API Routes → Database (SQLAlchemy напрямую)
```

**Когда добавлять Service/Repository слои:**
- Если логика в endpoint > 50 строк → вынеси в Service
- Если один запрос повторяется в 3+ местах → создай Repository метод

**Пример простого endpoint (достаточно для MVP):**

```python
@router.post("/students")
async def create_student(
    data: StudentCreate,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    student = Student(**data.dict(), school_id=school_id)
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student
```

### Что НЕ делать в MVP

- ❌ Сложные базовые классы (BaseRepository, BaseService) - добавишь при рефакторинге
- ❌ Декораторы для permissions - используй `if current_user.role not in [...]`
- ❌ MyPy проверки типов - потом
- ❌ Structlog - обычный logging хватит
- ❌ Pagination везде - добавь когда понадобится
- ❌ Множественные Pydantic схемы (Base, Create, Update, InDB) - только Create и Response

### Code Quality минимум

```bash
# Перед коммитом:
black backend/                    # Форматирование (обязательно)
ruff check backend/ --fix         # Линтинг (желательно)
```

### Тестирование - фокус на критичное

**Тестируй в первую очередь:**
1. Изоляцию данных (админ школы 1 не видит данные школы 2)
2. Аутентификацию (login, JWT токены)
3. RBAC permissions (роли и доступы)

**Остальное - по необходимости.**

### Конфигурация - только нужное

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = ConfigDict(env_file=".env")

settings = Settings()
```

Добавляй настройки по мере необходимости.

### Когда рефакторить

Добавляй сложность **только когда почувствуешь боль**:
- Код дублируется в 3+ местах → создай функцию/класс
- Endpoint > 100 строк → вынеси логику в Service
- Тесты дублируют setup → создай fixtures в conftest.py

**Принцип:** Start simple, refactor when needed.

## Migration Strategy

**Текущие миграции (8 штук):**
- 001: Initial schema (28 таблиц)
- 002-007: Различные улучшения (learning objectives, JSON типы, индексы)
- 008: **Критическая** - добавление school_id для изоляции данных + гибридная модель

**При создании новых миграций:**
1. Всегда проверяй, что модель обновлена ПЕРЕД созданием миграции
2. Используй `--autogenerate`, но всегда проверяй результат вручную
3. Для complex миграций создавай `.sql` файл рядом с `.py` файлом
4. Указывай `server_default` для NOT NULL колонок при добавлении в существующие таблицы
5. Тестируй и upgrade, и downgrade

**Пример создания миграции:**
```bash
cd backend
alembic revision --autogenerate -m "add super_admin role"
# Отредактируй файл миграции, проверь downgrade()
alembic upgrade head
# Проверь БД
alembic downgrade -1  # тестируй откат
alembic upgrade head  # вернись обратно
```

## Development Workflow

### Текущий этап: GOSO API Implementation (2025-12-16)

**Завершено ранее:**
- ✅ Итерации 1-4: Auth, RBAC, Content Management API
- ✅ Миграции 001-011: базовая схема, school_id изоляция, SUPER_ADMIN роль
- ✅ Admin Panel (React-Admin): CRUD для учебников, тестов, вопросов
- ✅ Production deploy: api.ai-mentor.kz, admin.ai-mentor.kz

**Текущая работа - ГОСО интеграция:**

| Компонент | Статус | Файл |
|-----------|--------|------|
| Миграция 012: GOSO таблицы | ✅ Готово | `012_add_goso_core_tables.py` |
| Миграция 013: paragraph_outcomes | ✅ Готово | `013_add_paragraph_outcomes.py` |
| SQLAlchemy модели | ✅ Готово | `models/subject.py`, `models/goso.py` |
| Pydantic схемы | ✅ Готово | `schemas/goso.py` (425 строк) |
| Импорт данных | ✅ Готово | 164 learning outcomes (История КЗ 5-9) |
| GosoRepository | ⏳ В работе | `repositories/goso_repo.py` |
| GOSO API endpoints | ⏳ В работе | `api/v1/goso.py` |

**План реализации GOSO API (см. `docs/GOSO_API_IMPLEMENTATION_PLAN.md`):**
1. Этап 1: GosoRepository (~200 строк) - read-only доступ к ГОСО данным
2. Этап 2: Read-only endpoints в `/goso/*` (8 endpoints)
3. Этап 3: SUPER_ADMIN endpoints для paragraph_outcomes
4. Этап 4: School ADMIN endpoints для paragraph_outcomes
5. Этап 5: Интеграция и тестирование

**Данные в БД:**
```
subjects:           1 (История Казахстана)
frameworks:         1 (ГОСО 2022-09-16)
goso_sections:      4 (разделы)
goso_subsections:   9 (подразделы)
learning_outcomes:  164 (цели обучения: 5кл-27, 6кл-43, 7кл-32, 8кл-26, 9кл-36)
```

### Git Commit Conventions

**Следуй conventional commits:**
- `feat:` - новая функциональность
- `fix:` - исправление бага
- `docs:` - обновление документации
- `refactor:` - рефакторинг без изменения функциональности
- `test:` - добавление тестов
- `chore:` - обновление зависимостей, настроек

**Всегда добавляй в конец коммита:**
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Important Technical Details

### pgvector для RAG

**Embeddings модель:**
- Используется OpenAI `text-embedding-3-small`
- Размерность: 1536
- Тип в PostgreSQL: `vector(1536)`
- Индекс: `USING ivfflat (embedding vector_cosine_ops)`

**Модель ParagraphEmbedding:**
```python
class ParagraphEmbedding:
    id
    school_id          # для изоляции
    paragraph_id       # FK к paragraphs
    embedding          # vector(1536)
    chunk_text         # текст чанка
    chunk_index        # номер чанка (один параграф = N чанков)
    token_count
```

### Алгоритм группировки A/B/C (Mastery Service)

**Критерии (из ARCHITECTURE.md):**
- **Группа A**: ≥ 85% правильных ответов, стабильные результаты
- **Группа B**: 60-84% правильных ответов
- **Группа C**: < 60% правильных ответов или нестабильные результаты

**Алгоритм:**
- Берет последние 5 попыток по главе
- Считает взвешенный средний (новые попытки важнее: weights = [0.35, 0.25, 0.20, 0.12, 0.08])
- Анализирует тренд (улучшение/стабильно/ухудшение)
- Считает консистентность (стандартное отклонение)
- Сохраняет в `mastery_history` при изменении уровня

**Модели:**
- `MasteryHistory` - история изменений уровня
- `AdaptiveGroup` - текущая группа ученика по главе (расчет каждый раз при новой попытке)

### Async/Await Pattern

**Весь проект использует async:**
```python
# Database connection
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Dependencies
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Endpoints
@router.post("/tests")
async def create_test(
    data: TestCreate,
    db: AsyncSession = Depends(get_db)
):
    ...
```

**Важно:** Все запросы к БД должны быть через `await`.

## Quick Reference

**Check implementation status:**
```bash
cat docs/IMPLEMENTATION_STATUS.md | grep "ИТЕРАЦИЯ" | head -15
```

**Find where a model is used:**
```bash
grep -r "from app.models.textbook import" backend/
```

**Check database schema:**
```bash
docker exec -it ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\dt"
docker exec -it ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\d textbooks"
```

**View current migration:**
```bash
cd backend && alembic current -v
```

**Count migrations:**
```bash
ls backend/alembic/versions/*.py | wc -l
```
