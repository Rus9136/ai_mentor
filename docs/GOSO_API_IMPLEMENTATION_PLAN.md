# План реализации ГОСО API Endpoints

**Дата создания:** 2025-12-16
**Статус:** Готов к реализации
**Автор:** Claude Code

---

## Обзор

Данный документ описывает пошаговый план реализации API endpoints для работы с ГОСО (Государственный общеобязательный стандарт образования).

### Текущее состояние

| Компонент | Статус | Файл/Расположение |
|-----------|--------|-------------------|
| Миграции БД | ✅ Готово | `012_add_goso_core_tables.py`, `013_add_paragraph_outcomes.py` |
| SQLAlchemy модели | ✅ Готово | `models/subject.py`, `models/goso.py` |
| Pydantic схемы | ✅ Готово | `schemas/goso.py` (425 строк) |
| Импорт данных | ✅ Готово | 164 learning outcomes (История Казахстана 5-9) |
| API endpoints | ❌ Не реализовано | Требуется создать |

### Данные в БД

```
subjects:           1 (История Казахстана)
frameworks:         1 (ГОСО 2022-09-16)
goso_sections:      4 (разделы ГОСО)
goso_subsections:   9 (подразделы)
learning_outcomes:  164 (цели обучения: 5кл-27, 6кл-43, 7кл-32, 8кл-26, 9кл-36)
paragraph_outcomes: 0 (маппинг ещё не создан)
```

---

## Этап 1: Создание GosoRepository

**Цель:** Создать репозиторий для доступа к данным ГОСО

**Файл:** `backend/app/repositories/goso_repo.py`

### 1.1 Класс GosoRepository

```python
class GosoRepository:
    """Repository for GOSO data access (read-only operations)."""

    def __init__(self, db: AsyncSession):
        self.db = db
```

**Методы:**

| Метод | Описание | Параметры |
|-------|----------|-----------|
| `get_all_subjects()` | Все предметы | `is_active: bool = True` |
| `get_subject_by_id()` | Предмет по ID | `subject_id: int` |
| `get_subject_by_code()` | Предмет по коду | `code: str` |
| `get_all_frameworks()` | Все версии ГОСО | `subject_id: int = None, is_active: bool = True` |
| `get_framework_by_id()` | Версия ГОСО по ID | `framework_id: int, load_structure: bool = False` |
| `get_sections_by_framework()` | Разделы ГОСО | `framework_id: int` |
| `get_section_by_id()` | Раздел по ID | `section_id: int, load_subsections: bool = False` |
| `get_subsections_by_section()` | Подразделы | `section_id: int` |
| `get_subsection_by_id()` | Подраздел по ID | `subsection_id: int, load_outcomes: bool = False` |
| `get_outcomes()` | Цели обучения | `framework_id, grade, subsection_id, is_active` |
| `get_outcome_by_id()` | Цель по ID | `outcome_id: int` |
| `get_outcome_with_context()` | Цель с контекстом | `outcome_id: int` (+ section/subsection names) |

### 1.2 Класс ParagraphOutcomeRepository

```python
class ParagraphOutcomeRepository:
    """Repository for paragraph-outcome mapping CRUD."""

    def __init__(self, db: AsyncSession):
        self.db = db
```

**Методы:**

| Метод | Описание | Параметры |
|-------|----------|-----------|
| `create()` | Создать связь | `paragraph_outcome: ParagraphOutcome` |
| `get_by_id()` | Получить по ID | `id: int` |
| `get_by_paragraph()` | Все outcomes для параграфа | `paragraph_id: int` |
| `get_by_outcome()` | Все параграфы для outcome | `outcome_id: int` |
| `update()` | Обновить связь | `paragraph_outcome: ParagraphOutcome` |
| `delete()` | Удалить связь | `id: int` (hard delete) |

### 1.3 Критерии завершения

- [ ] Файл `goso_repo.py` создан
- [ ] GosoRepository реализован (12 методов)
- [ ] ParagraphOutcomeRepository реализован (6 методов)
- [ ] Добавлен в `repositories/__init__.py`
- [ ] Базовые тесты проходят

**Оценка:** ~200 строк кода

---

## Этап 2: Read-only ГОСО endpoints

**Цель:** Создать публичные (для авторизованных) endpoints для чтения ГОСО

**Файл:** `backend/app/api/v1/goso.py`

### 2.1 Endpoints

| Endpoint | Метод | Описание | Response |
|----------|-------|----------|----------|
| `/goso/subjects` | GET | Список предметов | `List[SubjectListResponse]` |
| `/goso/subjects/{id}` | GET | Предмет по ID | `SubjectResponse` |
| `/goso/frameworks` | GET | Версии ГОСО | `List[FrameworkListResponse]` |
| `/goso/frameworks/{id}` | GET | Версия ГОСО | `FrameworkResponse` |
| `/goso/frameworks/{id}/structure` | GET | Полная структура | `FrameworkWithSections` (nested) |
| `/goso/outcomes` | GET | Цели обучения | `List[LearningOutcomeListResponse]` |
| `/goso/outcomes/{id}` | GET | Цель с контекстом | `LearningOutcomeWithContext` |
| `/goso/paragraphs/{id}/outcomes` | GET | Outcomes для параграфа | `List[ParagraphOutcomeWithDetails]` |

### 2.2 Query параметры

**GET /goso/frameworks:**
- `subject_id: int` — фильтр по предмету
- `is_active: bool = True` — только активные

**GET /goso/outcomes:**
- `framework_id: int` — фильтр по версии ГОСО
- `grade: int` — фильтр по классу (5-11)
- `subsection_id: int` — фильтр по подразделу
- `section_id: int` — фильтр по разделу
- `is_active: bool = True` — только активные
- `limit: int = 100` — лимит результатов
- `offset: int = 0` — смещение

### 2.3 Доступ

```python
from app.api.dependencies import get_current_user

# Все endpoints требуют аутентификации, но не требуют конкретной роли
@router.get("/subjects")
async def list_subjects(
    current_user: User = Depends(get_current_user),  # Любая роль
    db: AsyncSession = Depends(get_db)
):
    ...
```

### 2.4 Критерии завершения

- [ ] Файл `goso.py` создан
- [ ] 8 endpoints реализованы
- [ ] Фильтрация работает корректно
- [ ] Nested responses загружаются правильно
- [ ] Роутер зарегистрирован в `main.py`

**Оценка:** ~250 строк кода

---

## Этап 3: SUPER_ADMIN endpoints для paragraph_outcomes

**Цель:** Добавить CRUD для маппинга глобальных параграфов к целям ГОСО

**Файл:** `backend/app/api/v1/admin_global.py` (добавить секцию)

### 3.1 Endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/admin/global/paragraph-outcomes` | POST | Создать связь |
| `/admin/global/paragraphs/{id}/outcomes` | GET | Outcomes для глобального параграфа |
| `/admin/global/paragraph-outcomes/{id}` | PUT | Обновить связь |
| `/admin/global/paragraph-outcomes/{id}` | DELETE | Удалить связь |

### 3.2 Логика проверок

```python
@router.post("/paragraph-outcomes")
async def create_global_paragraph_outcome(
    data: ParagraphOutcomeCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    # 1. Проверить что paragraph существует
    # 2. Проверить что paragraph глобальный (school_id = NULL)
    # 3. Проверить что outcome существует и активен
    # 4. Проверить что связь не дублируется (UNIQUE constraint)
    # 5. Создать связь с created_by = current_user.id
    ...
```

### 3.3 Критерии завершения

- [ ] 4 endpoints добавлены в `admin_global.py`
- [ ] Проверка глобальности параграфа работает
- [ ] `created_by` автоматически заполняется
- [ ] UNIQUE constraint обрабатывается (409 Conflict)

**Оценка:** ~100 строк кода

---

## Этап 4: School ADMIN endpoints для paragraph_outcomes

**Цель:** Добавить CRUD для маппинга школьных параграфов к целям ГОСО

**Файл:** `backend/app/api/v1/admin_school.py` (добавить секцию)

### 4.1 Endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/admin/school/paragraph-outcomes` | POST | Создать связь |
| `/admin/school/paragraphs/{id}/outcomes` | GET | Outcomes для параграфа |
| `/admin/school/paragraph-outcomes/{id}` | PUT | Обновить связь |
| `/admin/school/paragraph-outcomes/{id}` | DELETE | Удалить связь |

### 4.2 Логика доступа

```python
@router.post("/paragraph-outcomes")
async def create_school_paragraph_outcome(
    data: ParagraphOutcomeCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    # 1. Получить paragraph
    # 2. Проверить доступ:
    #    - Если paragraph.school_id == school_id → OK (свой параграф)
    #    - Если paragraph.school_id IS NULL → OK (глобальный, можно маппить)
    #    - Иначе → 403 Forbidden
    # 3. Проверить что outcome существует
    # 4. Создать связь
    ...
```

### 4.3 RLS политики (уже настроены в миграции 013)

```sql
-- School ADMIN может:
-- 1. Читать все paragraph_outcomes (для чтения целей параграфов)
-- 2. Создавать для своих параграфов
-- 3. Создавать для глобальных параграфов (своё мнение о маппинге)
```

### 4.4 Критерии завершения

- [ ] 4 endpoints добавлены в `admin_school.py`
- [ ] Проверка school_id работает корректно
- [ ] Можно маппить и свои, и глобальные параграфы
- [ ] `created_by` заполняется автоматически

**Оценка:** ~120 строк кода

---

## Этап 5: Регистрация и тестирование

**Цель:** Интеграция всех компонентов и тестирование

### 5.1 Обновление main.py

```python
# backend/app/main.py

from app.api.v1 import auth, admin_global, admin_school, schools, upload, students, goso

# ... существующие роутеры ...

app.include_router(
    goso.router,
    prefix=f"{settings.API_V1_PREFIX}/goso",
    tags=["GOSO - Learning Standards"],
)
```

### 5.2 Обновление repositories/__init__.py

```python
from app.repositories.goso_repo import GosoRepository, ParagraphOutcomeRepository

__all__ = [
    # ... existing ...
    "GosoRepository",
    "ParagraphOutcomeRepository",
]
```

### 5.3 Тестирование

**Ручное тестирование через Swagger UI:**

1. **Авторизация:**
   ```bash
   POST /api/v1/auth/login
   # superadmin@aimentor.com / admin123
   ```

2. **Чтение ГОСО:**
   ```bash
   GET /api/v1/goso/subjects
   GET /api/v1/goso/frameworks
   GET /api/v1/goso/frameworks/1/structure
   GET /api/v1/goso/outcomes?grade=5
   ```

3. **Создание маппинга (SUPER_ADMIN):**
   ```bash
   POST /api/v1/admin/global/paragraph-outcomes
   {
     "paragraph_id": 1,
     "outcome_id": 1,
     "confidence": 0.95,
     "notes": "Прямое соответствие"
   }
   ```

4. **Получение маппинга:**
   ```bash
   GET /api/v1/goso/paragraphs/1/outcomes
   ```

### 5.4 Критерии завершения

- [ ] Все роутеры зарегистрированы
- [ ] Swagger UI показывает новые endpoints
- [ ] Read endpoints работают для всех ролей
- [ ] CRUD endpoints работают для SUPER_ADMIN
- [ ] CRUD endpoints работают для School ADMIN
- [ ] Деплой на production успешен

---

## Сводка

### Файлы для создания

| Файл | Действие | Строк кода |
|------|----------|------------|
| `repositories/goso_repo.py` | Создать | ~200 |
| `api/v1/goso.py` | Создать | ~250 |

### Файлы для изменения

| Файл | Действие | Строк кода |
|------|----------|------------|
| `api/v1/admin_global.py` | Добавить секцию | ~100 |
| `api/v1/admin_school.py` | Добавить секцию | ~120 |
| `repositories/__init__.py` | Добавить экспорт | ~5 |
| `main.py` | Зарегистрировать роутер | ~10 |

### Общий объём

- **Новый код:** ~450 строк
- **Изменения:** ~235 строк
- **Итого:** ~685 строк

---

## API Reference (после реализации)

### Read-only endpoints (все роли)

```
GET /api/v1/goso/subjects
GET /api/v1/goso/subjects/{id}
GET /api/v1/goso/frameworks
GET /api/v1/goso/frameworks/{id}
GET /api/v1/goso/frameworks/{id}/structure
GET /api/v1/goso/outcomes
GET /api/v1/goso/outcomes/{id}
GET /api/v1/goso/paragraphs/{id}/outcomes
```

### SUPER_ADMIN endpoints

```
POST   /api/v1/admin/global/paragraph-outcomes
GET    /api/v1/admin/global/paragraphs/{id}/outcomes
PUT    /api/v1/admin/global/paragraph-outcomes/{id}
DELETE /api/v1/admin/global/paragraph-outcomes/{id}
```

### School ADMIN endpoints

```
POST   /api/v1/admin/school/paragraph-outcomes
GET    /api/v1/admin/school/paragraphs/{id}/outcomes
PUT    /api/v1/admin/school/paragraph-outcomes/{id}
DELETE /api/v1/admin/school/paragraph-outcomes/{id}
```

---

## Зависимости между этапами

```
Этап 1 (Repository) ────┬──> Этап 2 (Read-only API)
                        │
                        ├──> Этап 3 (SUPER_ADMIN CRUD)
                        │
                        └──> Этап 4 (School ADMIN CRUD)
                                      │
                                      v
                              Этап 5 (Интеграция)
```

**Этап 1 является блокирующим** — без него нельзя начать другие этапы.

Этапы 2, 3, 4 могут выполняться параллельно после завершения Этапа 1.

---

**Автор:** Claude Code
**Дата:** 2025-12-16
