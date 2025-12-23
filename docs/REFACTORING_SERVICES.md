# Refactoring Plan: Services Layer

> **Назначение документа:** План рефакторинга — вынесение бизнес-логики в Services.
>
> **Связанные документы:**
> - `CLAUDE.md` — стандарты кода, лимиты файлов
> - `docs/ARCHITECTURE.md` — layered architecture

**Статус:** Планирование | **Приоритет:** Средний | **Effort:** 3-4 дня

---

## Архитектурные принципы

### 1. Transaction Boundary (Unit of Work)

**Правило:** Services НЕ делают `commit()`. Транзакции контролирует вызывающий код.

```python
# ❌ НЕПРАВИЛЬНО — commit внутри service
class MyService:
    async def create_something(self):
        self.db.add(entity)
        await self.db.commit()  # НЕТ!

# ✅ ПРАВИЛЬНО — commit в endpoint или UoW
@router.post("/something")
async def create(service: MyService = Depends(get_service), db: AsyncSession = Depends(get_db)):
    result = await service.create_something()
    await db.commit()
    return result
```

**Исключения:** Только для изолированных операций (логирование, аудит).

### 2. Dependency Injection для Services

**Правило:** Services создаются через FastAPI Depends, не внутри endpoints.

```python
# ❌ НЕПРАВИЛЬНО
@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    service = StudentStatsService(db)  # Каждый раз новый инстанс
    return await service.get_stats()

# ✅ ПРАВИЛЬНО
async def get_stats_service(
    db: AsyncSession = Depends(get_db)
) -> StudentStatsService:
    return StudentStatsService(db)

@router.get("/stats")
async def get_stats(
    service: StudentStatsService = Depends(get_stats_service)
):
    return await service.get_stats()
```

**Преимущества:**
- Легко мокать в тестах
- Единая точка создания
- Возможность добавить caching/pooling

### 3. Protocols для тестирования

```python
# backend/app/services/protocols.py

from typing import Protocol

class IStudentStatsService(Protocol):
    async def calculate_streak(self, student_id: int, school_id: int) -> int: ...
    async def get_dashboard_stats(self, student_id: int, school_id: int) -> StudentDashboardStats: ...
```

### 4. Конфигурируемые значения

```python
# backend/app/core/config.py

class Settings(BaseSettings):
    # Learning settings
    MIN_DAILY_ACTIVITY_SECONDS: int = 600  # 10 minutes for streak
    MASTERY_LEVEL_A_THRESHOLD: int = 85
    MASTERY_LEVEL_B_THRESHOLD: int = 60
```

## Текущее состояние

### Проблемный файл: `backend/app/api/v1/students.py` → ✅ REFACTORED

| Метрика | До | После | Норма |
|---------|-----|-------|-------|
| Строк кода | 2661 | 0 (deleted) | < 400 |
| Файлов | 1 | 7 | - |
| Max строк/файл | 2661 | 891 | < 400 |
| Endpoints | 21 | 20 (across 6 files) | 5-6 на файл |
| Доменов | 6 | 1 per file | 1 на файл |
| Дублирование | ~200 строк | ~200 | 0 |

**Статус:** Phase 2 завершён. tests.py и content.py требуют дополнительной оптимизации.

### Выявленные проблемы

1. **God File** — один файл содержит 6 разных доменов
2. **Дублирование** — проверка доступа к параграфу копируется 10+ раз
3. **Бизнес-логика в endpoints** — расчёт streak, progress, mastery
4. **N+1 запросы** — в `get_student_textbooks()` и `get_textbook_chapters()`

---

## Целевая архитектура

### Структура файлов после рефакторинга

```
backend/app/
├── api/v1/
│   └── students/
│       ├── __init__.py           # Router aggregation
│       ├── tests.py              # Test-taking workflow
│       ├── content.py            # Textbooks, chapters, paragraphs
│       ├── learning.py           # Progress, steps, self-assessment
│       ├── mastery.py            # Mastery endpoints
│       ├── embedded.py           # Embedded questions
│       └── stats.py              # Dashboard stats
│
├── services/
│   ├── student_content_service.py    # NEW
│   ├── student_progress_service.py   # NEW
│   ├── student_stats_service.py      # NEW
│   ├── test_taking_service.py        # NEW
│   ├── grading_service.py            # EXISTS
│   └── mastery_service.py            # EXISTS
│
└── api/dependencies.py               # + new dependencies
```

---

## Phase 1: Reusable Dependencies (2h)

> **Риск:** Низкий | **Можно деплоить:** Отдельно

### Задача

Вынести повторяющиеся проверки в `dependencies.py`.

### Новые dependencies

```python
# backend/app/api/dependencies.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import Depends, HTTPException, status

from app.models.student import Student
from app.models.paragraph import Paragraph
from app.models.chapter import Chapter
from app.models.textbook import Textbook
from app.models.user import User
from app.core.database import get_db


async def get_student_from_user(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db)
) -> Student:
    """
    Получить Student record из User.

    Используется вместо lazy loading current_user.student,
    который не работает в async контексте.
    """
    result = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student record not found for this user"
        )
    return student


async def get_paragraph_with_access(
    paragraph_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Paragraph:
    """
    Получить параграф с проверкой доступа через textbook.school_id.

    Загружает: paragraph -> chapter -> textbook (eager loading).
    Проверяет: textbook.school_id in (None, current_school_id).
    """
    result = await db.execute(
        select(Paragraph)
        .options(
            selectinload(Paragraph.chapter)
            .selectinload(Chapter.textbook)
        )
        .where(
            Paragraph.id == paragraph_id,
            Paragraph.is_deleted == False
        )
    )
    paragraph = result.scalar_one_or_none()

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    textbook = paragraph.chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this paragraph"
        )

    return paragraph


async def get_chapter_with_access(
    chapter_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Chapter:
    """
    Получить главу с проверкой доступа через textbook.school_id.
    """
    result = await db.execute(
        select(Chapter)
        .options(selectinload(Chapter.textbook))
        .where(
            Chapter.id == chapter_id,
            Chapter.is_deleted == False
        )
    )
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    textbook = chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chapter"
        )

    return chapter


async def get_textbook_with_access(
    textbook_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Textbook:
    """
    Получить учебник с проверкой доступа.
    """
    from app.repositories.textbook_repo import TextbookRepository

    repo = TextbookRepository(db)
    textbook = await repo.get_by_id(textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this textbook"
        )

    return textbook
```

### Результат Phase 1

- Убрано ~200 строк дублирования
- Endpoints становятся чище
- Единая точка проверки доступа

---

## Phase 2: Split Students Router (3h)

> **Риск:** Средний | **Можно деплоить:** Отдельно
>
> ⚠️ **ВАЖНО:** Выполнять ДО создания services, чтобы не переносить endpoints дважды.

### Задача

Разбить `students.py` на субмодули по доменам. Это упростит последующий рефакторинг.

### Новая структура

```
backend/app/api/v1/students/
├── __init__.py       # Router aggregation
├── tests.py          # 6 endpoints (~400 строк)
├── content.py        # 6 endpoints (~350 строк)
├── learning.py       # 4 endpoints (~300 строк)
├── mastery.py        # 2 endpoints (~150 строк)
├── embedded.py       # 2 endpoints (~150 строк)
└── stats.py          # 1 endpoint (~50 строк)
```

### Router aggregation

```python
# backend/app/api/v1/students/__init__.py

from fastapi import APIRouter

from .tests import router as tests_router
from .content import router as content_router
from .learning import router as learning_router
from .mastery import router as mastery_router
from .embedded import router as embedded_router
from .stats import router as stats_router

router = APIRouter()

# Test-taking workflow
router.include_router(tests_router, tags=["Student Tests"])

# Content browsing
router.include_router(content_router, tags=["Student Content"])

# Learning progress
router.include_router(learning_router, tags=["Student Learning"])

# Mastery
router.include_router(mastery_router, tags=["Student Mastery"])

# Embedded questions
router.include_router(embedded_router, tags=["Embedded Questions"])

# Stats
router.include_router(stats_router, tags=["Student Stats"])
```

### Стратегия миграции (zero-downtime)

1. Создать `students/` package с пустыми файлами
2. Переносить endpoints по одному домену
3. После каждого переноса — тест на staging
4. Удалить старый `students.py` только после полного переноса

### Обновление main.py

```python
# Импорт не меняется благодаря __init__.py:
from app.api.v1.students import router as students_router
```

### Результат Phase 2

- Каждый файл < 400 строк
- Чёткое разделение ответственности
- Готово для внедрения services

---

## Phase 3: Student Stats Service (3h)

> **Риск:** Низкий | **Можно деплоить:** Отдельно

### Задача

Вынести расчёт streak и dashboard stats в отдельный service.

### Требуемый индекс для производительности

```sql
-- Добавить в миграцию!
CREATE INDEX CONCURRENTLY idx_student_paragraph_streak
ON student_paragraphs (student_id, school_id, last_accessed_at DESC)
WHERE last_accessed_at IS NOT NULL;
```

### Новый service

```python
# backend/app/services/student_stats_service.py

import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date

from app.models.learning import StudentParagraph
from app.models.embedded_question import StudentEmbeddedAnswer
from app.schemas.student_content import StudentDashboardStats
from app.core.config import settings

logger = logging.getLogger(__name__)


class StudentStatsService:
    """
    Service для расчёта статистики студента.

    Responsibilities:
    - Расчёт streak (consecutive active days)
    - Агрегация time spent
    - Подсчёт completed paragraphs и tasks

    Note: Этот service только читает данные, commit не требуется.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_streak(
        self,
        student_id: int,
        school_id: int
    ) -> int:
        """
        Рассчитать streak — количество последовательных активных дней.

        Активный день = день с >= MIN_DAILY_ACTIVITY_SECONDS секунд активности.
        Streak считается от сегодня/вчера назад.

        Returns:
            Количество последовательных активных дней
        """
        min_seconds = settings.MIN_DAILY_ACTIVITY_SECONDS

        # Получить дни с достаточной активностью
        # Использует индекс idx_student_paragraph_streak
        daily_time_query = (
            select(
                cast(StudentParagraph.last_accessed_at, Date).label('activity_date'),
                func.sum(StudentParagraph.time_spent).label('total_time')
            )
            .where(
                StudentParagraph.student_id == student_id,
                StudentParagraph.school_id == school_id,
                StudentParagraph.last_accessed_at.isnot(None)
            )
            .group_by(cast(StudentParagraph.last_accessed_at, Date))
            .having(func.sum(StudentParagraph.time_spent) >= min_seconds)
            .order_by(cast(StudentParagraph.last_accessed_at, Date).desc())
        )

        result = await self.db.execute(daily_time_query)
        rows = result.fetchall()
        active_days = [row.activity_date for row in rows]

        if not active_days:
            return 0

        # Проверить, что streak не прерван
        today = date.today()
        yesterday = today - timedelta(days=1)

        if active_days[0] not in (today, yesterday):
            return 0  # Streak прерван

        # Считаем последовательные дни
        streak = 0
        expected_date = active_days[0]

        for active_date in active_days:
            if active_date == expected_date:
                streak += 1
                expected_date = expected_date - timedelta(days=1)
            else:
                break

        return streak

    async def get_dashboard_stats(
        self,
        student_id: int,
        school_id: int
    ) -> StudentDashboardStats:
        """
        Получить полную статистику для dashboard.

        Returns:
            StudentDashboardStats с streak, paragraphs, tasks, time
        """
        # 1. Completed paragraphs
        completed_result = await self.db.execute(
            select(func.count(StudentParagraph.id)).where(
                StudentParagraph.student_id == student_id,
                StudentParagraph.school_id == school_id,
                StudentParagraph.is_completed == True
            )
        )
        total_paragraphs_completed = completed_result.scalar() or 0

        # 2. Answered embedded questions
        tasks_result = await self.db.execute(
            select(func.count(StudentEmbeddedAnswer.id)).where(
                StudentEmbeddedAnswer.student_id == student_id,
                StudentEmbeddedAnswer.school_id == school_id
            )
        )
        total_tasks_completed = tasks_result.scalar() or 0

        # 3. Total time spent
        time_result = await self.db.execute(
            select(func.sum(StudentParagraph.time_spent)).where(
                StudentParagraph.student_id == student_id,
                StudentParagraph.school_id == school_id
            )
        )
        total_time_seconds = time_result.scalar() or 0
        total_time_minutes = total_time_seconds // 60

        # 4. Streak
        streak_days = await self.calculate_streak(student_id, school_id)

        logger.info(
            f"Student {student_id} stats: streak={streak_days}, "
            f"paragraphs={total_paragraphs_completed}, tasks={total_tasks_completed}"
        )

        return StudentDashboardStats(
            streak_days=streak_days,
            total_paragraphs_completed=total_paragraphs_completed,
            total_tasks_completed=total_tasks_completed,
            total_time_spent_minutes=total_time_minutes
        )
```

### Dependency Injection для service

```python
# backend/app/api/dependencies.py (добавить)

from app.services.student_stats_service import StudentStatsService

async def get_student_stats_service(
    db: AsyncSession = Depends(get_db)
) -> StudentStatsService:
    """DI factory для StudentStatsService."""
    return StudentStatsService(db)
```

### Использование в endpoint

```python
# backend/app/api/v1/students/stats.py

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_student_from_user,
    get_current_user_school_id,
    get_student_stats_service
)
from app.services.student_stats_service import StudentStatsService
from app.schemas.student_content import StudentDashboardStats

router = APIRouter()


@router.get("/stats", response_model=StudentDashboardStats)
async def get_student_stats(
    student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    service: StudentStatsService = Depends(get_student_stats_service)  # DI!
):
    """Get student's dashboard statistics including streak."""
    return await service.get_dashboard_stats(student.id, school_id)
```

### Результат Phase 3

- Streak логика вынесена и тестируема отдельно
- Endpoint сократился с 60 до 5 строк
- DI позволяет легко мокать service в тестах
- Индекс обеспечивает производительность

---

## Phase 4: Student Content Service (4h)

> **Риск:** Средний | **Можно деплоить:** Отдельно

### Задача

Оптимизировать N+1 запросы и вынести логику прогресса по контенту.

### Новый service

```python
# backend/app/services/student_content_service.py

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.mastery import ParagraphMastery, ChapterMastery

logger = logging.getLogger(__name__)


@dataclass
class TextbookProgress:
    """Progress data for a textbook."""
    textbook_id: int
    chapters_total: int
    chapters_completed: int
    paragraphs_total: int
    paragraphs_completed: int
    percentage: int
    mastery_level: Optional[str]


@dataclass
class ChapterProgress:
    """Progress data for a chapter."""
    chapter_id: int
    paragraphs_total: int
    paragraphs_completed: int
    percentage: int
    mastery_level: Optional[str]
    mastery_score: Optional[float]
    status: str  # completed, in_progress, not_started, locked


class StudentContentService:
    """
    Service для работы с контентом студента.

    Responsibilities:
    - Получение учебников с прогрессом (batch queries)
    - Получение глав с прогрессом
    - Расчёт mastery level по textbook
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_textbooks_with_progress(
        self,
        student_id: int,
        school_id: int
    ) -> List[Dict[str, Any]]:
        """
        Получить учебники с прогрессом студента.

        Использует batch queries вместо N+1.
        """
        # 1. Получить доступные учебники (global + school)
        textbooks_result = await self.db.execute(
            select(Textbook).where(
                Textbook.is_deleted == False,
                Textbook.is_active == True,
                (Textbook.school_id.is_(None)) | (Textbook.school_id == school_id)
            )
        )
        textbooks = textbooks_result.scalars().all()
        textbook_ids = [t.id for t in textbooks]

        if not textbook_ids:
            return []

        # 2. Batch: chapters count per textbook
        chapters_count = await self._get_chapters_count_batch(textbook_ids)

        # 3. Batch: paragraphs count per textbook
        paragraphs_total = await self._get_paragraphs_count_batch(textbook_ids)

        # 4. Batch: completed paragraphs per textbook
        paragraphs_completed = await self._get_completed_paragraphs_batch(
            student_id, textbook_ids
        )

        # 5. Batch: average mastery score per textbook
        mastery_scores = await self._get_mastery_scores_batch(
            student_id, textbook_ids
        )

        # 6. Build response
        result = []
        for textbook in textbooks:
            tid = textbook.id
            total = paragraphs_total.get(tid, 0)
            completed = paragraphs_completed.get(tid, 0)
            percentage = int((completed / total * 100)) if total > 0 else 0

            avg_score = mastery_scores.get(tid)
            mastery_level = None
            if avg_score is not None:
                # Используем настройки из config
                if avg_score >= settings.MASTERY_LEVEL_A_THRESHOLD:
                    mastery_level = "A"
                elif avg_score >= settings.MASTERY_LEVEL_B_THRESHOLD:
                    mastery_level = "B"
                else:
                    mastery_level = "C"

            result.append({
                "textbook": textbook,
                "progress": TextbookProgress(
                    textbook_id=tid,
                    chapters_total=chapters_count.get(tid, 0),
                    chapters_completed=0,  # TODO: calculate
                    paragraphs_total=total,
                    paragraphs_completed=completed,
                    percentage=percentage,
                    mastery_level=mastery_level
                )
            })

        return result

    async def _get_chapters_count_batch(
        self,
        textbook_ids: List[int]
    ) -> Dict[int, int]:
        """Batch query: count chapters per textbook."""
        result = await self.db.execute(
            select(
                Chapter.textbook_id,
                func.count(Chapter.id).label('count')
            )
            .where(
                Chapter.textbook_id.in_(textbook_ids),
                Chapter.is_deleted == False
            )
            .group_by(Chapter.textbook_id)
        )
        return {row.textbook_id: row.count for row in result.fetchall()}

    async def _get_paragraphs_count_batch(
        self,
        textbook_ids: List[int]
    ) -> Dict[int, int]:
        """Batch query: count paragraphs per textbook."""
        result = await self.db.execute(
            select(
                Chapter.textbook_id,
                func.count(Paragraph.id).label('count')
            )
            .join(Paragraph, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id.in_(textbook_ids),
                Chapter.is_deleted == False,
                Paragraph.is_deleted == False
            )
            .group_by(Chapter.textbook_id)
        )
        return {row.textbook_id: row.count for row in result.fetchall()}

    async def _get_completed_paragraphs_batch(
        self,
        student_id: int,
        textbook_ids: List[int]
    ) -> Dict[int, int]:
        """Batch query: count completed paragraphs per textbook."""
        result = await self.db.execute(
            select(
                Chapter.textbook_id,
                func.count(ParagraphMastery.id).label('count')
            )
            .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id.in_(textbook_ids),
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.is_completed == True
            )
            .group_by(Chapter.textbook_id)
        )
        return {row.textbook_id: row.count for row in result.fetchall()}

    async def _get_mastery_scores_batch(
        self,
        student_id: int,
        textbook_ids: List[int]
    ) -> Dict[int, Optional[float]]:
        """Batch query: average mastery score per textbook."""
        result = await self.db.execute(
            select(
                Chapter.textbook_id,
                func.avg(ChapterMastery.mastery_score).label('avg_score')
            )
            .join(Chapter, ChapterMastery.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id.in_(textbook_ids),
                ChapterMastery.student_id == student_id
            )
            .group_by(Chapter.textbook_id)
        )
        return {row.textbook_id: row.avg_score for row in result.fetchall()}
```

### Результат Phase 4

- N+1 проблема решена через batch queries
- Запросы к БД: O(1) вместо O(N)
- Код изолирован и тестируем
- Thresholds вынесены в config

---

## Phase 5: Test Taking Service (4h)

> **Риск:** Средний | **Можно деплоить:** Отдельно

### Задача

Вынести логику прохождения тестов в отдельный service.

### Новый service

```python
# backend/app/services/test_taking_service.py

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.test import Test, Question
from app.models.test_attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.repositories.test_repo import TestRepository
from app.repositories.question_repo import QuestionRepository, QuestionOptionRepository
from app.repositories.test_attempt_repo import TestAttemptRepository
from app.services.grading_service import GradingService

logger = logging.getLogger(__name__)


class TestTakingService:
    """
    Service для workflow прохождения тестов.

    Responsibilities:
    - Старт теста (создание attempt)
    - Сохранение ответов
    - Проверка ответа (is_correct)
    - Завершение теста

    Transaction Policy:
    - Service добавляет объекты в session (db.add)
    - НЕ вызывает commit() — это делает endpoint
    - Позволяет откатить всю операцию при ошибке
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.test_repo = TestRepository(db)
        self.question_repo = QuestionRepository(db)
        self.option_repo = QuestionOptionRepository(db)
        self.attempt_repo = TestAttemptRepository(db)
        self.grading_service = GradingService(db)

    async def start_test(
        self,
        student_id: int,
        test_id: int,
        school_id: int
    ) -> TestAttempt:
        """
        Начать новую попытку теста.

        Args:
            student_id: ID студента
            test_id: ID теста
            school_id: ID школы

        Returns:
            Созданный TestAttempt

        Raises:
            ValueError: Test not found or not accessible
        """
        # Verify test exists and is accessible
        test = await self.test_repo.get_by_id(test_id, load_questions=False)

        if not test:
            raise ValueError(f"Test {test_id} not found")

        if test.school_id is not None and test.school_id != school_id:
            raise ValueError("Test not available for your school")

        if not test.is_active:
            raise ValueError("Test is not active")

        # Calculate attempt number
        attempt_count = await self.attempt_repo.count_attempts(
            student_id=student_id,
            test_id=test_id
        )

        # Create attempt
        attempt = TestAttempt(
            student_id=student_id,
            test_id=test_id,
            school_id=school_id,
            attempt_number=attempt_count + 1,
            status=AttemptStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc)
        )

        attempt = await self.attempt_repo.create(attempt)

        logger.info(
            f"Student {student_id} started test {test_id}, "
            f"attempt #{attempt.attempt_number}"
        )

        return attempt

    async def answer_question(
        self,
        attempt_id: int,
        question_id: int,
        selected_option_ids: List[int],
        student_id: int,
        school_id: int
    ) -> dict:
        """
        Ответить на вопрос теста.

        Returns:
            {
                "is_correct": bool,
                "correct_option_ids": List[int],
                "explanation": Optional[str],
                "points_earned": float
            }
        """
        # Verify attempt
        attempt = await self.attempt_repo.get_by_id(
            attempt_id=attempt_id,
            student_id=student_id,
            school_id=school_id
        )

        if not attempt:
            raise ValueError("Attempt not found or access denied")

        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise ValueError(f"Cannot answer: attempt status is {attempt.status}")

        # Get question and options
        question = await self.question_repo.get_by_id(question_id)

        if not question or question.test_id != attempt.test_id:
            raise ValueError(f"Question {question_id} not in this test")

        # Check if already answered
        existing = await self.db.execute(
            select(TestAttemptAnswer).where(
                TestAttemptAnswer.attempt_id == attempt_id,
                TestAttemptAnswer.question_id == question_id
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Question {question_id} already answered")

        # Load options and check correctness
        options = await self.option_repo.get_by_question(question_id)
        correct_option_ids = [opt.id for opt in options if opt.is_correct]

        is_correct = set(selected_option_ids) == set(correct_option_ids)
        points_earned = question.points if is_correct else 0.0

        # Save answer (commit делает endpoint!)
        answer = TestAttemptAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_ids=selected_option_ids,
            is_correct=is_correct,
            points_earned=points_earned,
            answered_at=datetime.now(timezone.utc)
        )
        self.db.add(answer)
        # НЕ делаем commit — это ответственность endpoint

        logger.info(
            f"Student {student_id} answered Q{question_id}: "
            f"correct={is_correct}, points={points_earned}"
        )

        return {
            "is_correct": is_correct,
            "correct_option_ids": correct_option_ids,
            "explanation": question.explanation,
            "points_earned": points_earned
        }

    async def complete_attempt(
        self,
        attempt_id: int,
        student_id: int,
        school_id: int
    ) -> TestAttempt:
        """
        Завершить попытку теста.

        Проверяет, что все вопросы отвечены, запускает grading.
        """
        attempt = await self.attempt_repo.get_by_id(
            attempt_id=attempt_id,
            student_id=student_id,
            school_id=school_id
        )

        if not attempt:
            raise ValueError("Attempt not found")

        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete: status is {attempt.status}")

        # Check all questions answered
        questions = await self.question_repo.get_by_test(
            attempt.test_id,
            load_options=False
        )
        total_questions = len(questions)

        answered_count = await self.db.execute(
            select(func.count(TestAttemptAnswer.id)).where(
                TestAttemptAnswer.attempt_id == attempt_id
            )
        )
        answered = answered_count.scalar() or 0

        if answered < total_questions:
            raise ValueError(
                f"Not all questions answered: {answered}/{total_questions}"
            )

        # Run grading
        graded = await self.grading_service.grade_attempt(
            attempt_id=attempt_id,
            student_id=student_id,
            school_id=school_id
        )

        logger.info(
            f"Attempt {attempt_id} completed: "
            f"score={graded.score}, passed={graded.passed}"
        )

        return graded
```

### Пример использования в endpoint

```python
# backend/app/api/v1/students/tests.py

@router.post("/tests/{test_id}/answer")
async def answer_question(
    test_id: int,
    answer_data: AnswerRequest,
    service: TestTakingService = Depends(get_test_taking_service),
    db: AsyncSession = Depends(get_db)
):
    result = await service.answer_question(...)
    await db.commit()  # Commit здесь!
    return result
```

### Результат Phase 5

- Test-taking логика изолирована
- Легко тестировать без HTTP (mock db, без commit)
- Готово для расширения (таймеры, retries)
- Transaction boundary в endpoint

---

## Phase 6: Learning Progress Service (3h)

> **Риск:** Низкий | **Можно деплоить:** Отдельно

### Задача

Вынести логику обновления прогресса обучения.

### Новый service

```python
# backend/app/services/student_progress_service.py

import logging
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.learning import StudentParagraph
from app.models.embedded_question import EmbeddedQuestion, StudentEmbeddedAnswer
from app.models.paragraph import Paragraph

logger = logging.getLogger(__name__)


class StudentProgressService:
    """
    Service для управления прогрессом обучения студента.

    Responsibilities:
    - Обновление текущего шага (step)
    - Сохранение self-assessment
    - Расчёт доступных шагов
    - Трекинг времени

    Transaction Policy:
    - Добавляет/изменяет объекты в session
    - НЕ вызывает commit() — это делает endpoint
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_steps(
        self,
        paragraph_id: int
    ) -> List[str]:
        """Определить доступные шаги для параграфа."""
        steps = ["intro", "content"]

        # Check for embedded questions
        eq_count = await self.db.execute(
            select(func.count(EmbeddedQuestion.id)).where(
                EmbeddedQuestion.paragraph_id == paragraph_id,
                EmbeddedQuestion.is_active == True
            )
        )
        if (eq_count.scalar() or 0) > 0:
            steps.append("practice")

        # Check for summary
        para = await self.db.execute(
            select(Paragraph.summary).where(Paragraph.id == paragraph_id)
        )
        if para.scalar():
            steps.append("summary")

        return steps

    async def update_step(
        self,
        student_id: int,
        paragraph_id: int,
        school_id: int,
        step: str,
        time_spent: Optional[int] = None
    ) -> StudentParagraph:
        """
        Обновить текущий шаг студента в параграфе.

        Args:
            student_id: ID студента
            paragraph_id: ID параграфа
            school_id: ID школы
            step: Новый шаг (intro, content, practice, summary, completed)
            time_spent: Дополнительное время (секунды)

        Returns:
            Обновлённый StudentParagraph
        """
        result = await self.db.execute(
            select(StudentParagraph).where(
                StudentParagraph.paragraph_id == paragraph_id,
                StudentParagraph.student_id == student_id
            )
        )
        student_para = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if not student_para:
            student_para = StudentParagraph(
                student_id=student_id,
                paragraph_id=paragraph_id,
                school_id=school_id,
                current_step=step,
                time_spent=time_spent or 0,
                last_accessed_at=now
            )
            self.db.add(student_para)
        else:
            student_para.current_step = step
            student_para.last_accessed_at = now
            if time_spent:
                student_para.time_spent += time_spent

        # Mark completed
        if step == "completed":
            student_para.is_completed = True
            student_para.completed_at = now

        # НЕ делаем commit — это ответственность endpoint
        await self.db.flush()  # Получаем ID для нового объекта

        logger.info(
            f"Student {student_id} updated paragraph {paragraph_id} "
            f"to step '{step}'"
        )

        return student_para

    async def submit_self_assessment(
        self,
        student_id: int,
        paragraph_id: int,
        school_id: int,
        rating: str  # understood, questions, difficult
    ) -> dict:
        """
        Сохранить self-assessment для параграфа.

        Returns:
            {"recorded_at": datetime, "message": str}
        """
        result = await self.db.execute(
            select(StudentParagraph).where(
                StudentParagraph.paragraph_id == paragraph_id,
                StudentParagraph.student_id == student_id
            )
        )
        student_para = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if not student_para:
            student_para = StudentParagraph(
                student_id=student_id,
                paragraph_id=paragraph_id,
                school_id=school_id,
                self_assessment=rating,
                self_assessment_at=now,
                last_accessed_at=now
            )
            self.db.add(student_para)
        else:
            student_para.self_assessment = rating
            student_para.self_assessment_at = now
            student_para.last_accessed_at = now

        await self.db.flush()  # НЕ commit!

        messages = {
            "understood": "Отлично! Продолжай в том же духе!",
            "questions": "Хорошо, попробуй повторить материал или задай вопрос.",
            "difficult": "Не переживай! Попробуй посмотреть материал в другом формате."
        }

        logger.info(
            f"Student {student_id} self-assessment '{rating}' "
            f"for paragraph {paragraph_id}"
        )

        return {
            "recorded_at": now,
            "message": messages.get(rating, "Оценка сохранена")
        }

    async def get_embedded_questions_stats(
        self,
        student_id: int,
        paragraph_id: int
    ) -> dict:
        """
        Получить статистику по embedded questions.

        Returns:
            {"total": int, "answered": int, "correct": int}
        """
        # Total questions
        total_result = await self.db.execute(
            select(func.count(EmbeddedQuestion.id)).where(
                EmbeddedQuestion.paragraph_id == paragraph_id,
                EmbeddedQuestion.is_active == True
            )
        )
        total = total_result.scalar() or 0

        # Answered
        answered_result = await self.db.execute(
            select(func.count(StudentEmbeddedAnswer.id))
            .join(EmbeddedQuestion, StudentEmbeddedAnswer.question_id == EmbeddedQuestion.id)
            .where(
                EmbeddedQuestion.paragraph_id == paragraph_id,
                StudentEmbeddedAnswer.student_id == student_id
            )
        )
        answered = answered_result.scalar() or 0

        # Correct
        correct_result = await self.db.execute(
            select(func.count(StudentEmbeddedAnswer.id))
            .join(EmbeddedQuestion, StudentEmbeddedAnswer.question_id == EmbeddedQuestion.id)
            .where(
                EmbeddedQuestion.paragraph_id == paragraph_id,
                StudentEmbeddedAnswer.student_id == student_id,
                StudentEmbeddedAnswer.is_correct == True
            )
        )
        correct = correct_result.scalar() or 0

        return {"total": total, "answered": answered, "correct": correct}
```

---

## Summary

### Итоговая структура

```
backend/app/
├── api/
│   ├── dependencies.py              # + get_*_service factories
│   └── v1/students/
│       ├── __init__.py              # Router aggregation
│       ├── tests.py                 # Test-taking
│       ├── content.py               # Textbooks, chapters
│       ├── learning.py              # Progress, steps
│       ├── mastery.py               # Mastery endpoints
│       ├── embedded.py              # Embedded questions
│       └── stats.py                 # Dashboard stats
│
├── services/
│   ├── protocols.py                 # NEW - interfaces для тестирования
│   ├── grading_service.py           # EXISTS
│   ├── mastery_service.py           # EXISTS
│   ├── upload_service.py            # EXISTS
│   ├── chat_service.py              # EXISTS
│   ├── rag_service.py               # EXISTS
│   ├── embedding_service.py         # EXISTS
│   ├── student_stats_service.py     # NEW - streak, dashboard
│   ├── student_content_service.py   # NEW - textbooks progress
│   ├── student_progress_service.py  # NEW - learning steps
│   └── test_taking_service.py       # NEW - test workflow
│
└── core/
    └── config.py                    # + learning settings
```

### Метрики после рефакторинга

| Метрика | До | После |
|---------|-----|-------|
| students.py строк | 2661 | 0 (deleted) |
| Файлов в students/ | 1 | 7 |
| Max строк/файл | 2661 | 400 |
| Дублирование | ~200 строк | 0 |
| N+1 запросов | 3 места | 0 |
| Покрытие тестами | Сложно | Легко |
| Hardcoded values | 5+ мест | 0 (в config) |

### Порядок выполнения (ОБНОВЛЁННЫЙ)

| Phase | Задача | Effort | Риск | Зависимости |
|-------|--------|--------|------|-------------|
| 1 | Reusable Dependencies | 2h | Низкий | — |
| 2 | **Split Router** | 3h | Средний | — |
| 3 | Student Stats Service | 3h | Низкий | Phase 1, 2 |
| 4 | Student Content Service | 4h | Средний | Phase 1, 2 |
| 5 | Test Taking Service | 4h | Средний | Phase 1, 2 |
| 6 | Learning Progress Service | 3h | Низкий | Phase 1, 2 |

**Total:** ~19 часов (3 рабочих дня)

> **Изменение:** Split Router перенесён на Phase 2, чтобы упростить внедрение services в уже разделённые файлы.

---

## Ключевые правила (напоминание)

1. **Transaction Boundary** — services НЕ делают commit()
2. **Dependency Injection** — services создаются через Depends()
3. **Configurable Values** — все thresholds в settings
4. **Protocols** — для unit-тестов используем интерфейсы

---

## Checklist для выполнения

### Phase 1: Dependencies ✅ DONE (2025-12-23)
- [x] Добавить `get_student_from_user` в `dependencies.py`
- [x] Добавить `get_paragraph_with_access`
- [x] Добавить `get_chapter_with_access`
- [x] Добавить `get_textbook_with_access`

### Phase 2: Split Router ✅ DONE (2025-12-23)
- [x] Создать `api/v1/students/` package
- [x] Перенести test endpoints в `tests.py` (891 строк)
- [x] Перенести content endpoints в `content.py` (741 строк)
- [x] Перенести learning endpoints в `learning.py` (340 строк)
- [x] Перенести mastery endpoints в `mastery.py` (161 строк)
- [x] Перенести embedded endpoints в `embedded.py` (215 строк)
- [x] Перенести stats endpoints в `stats.py` (156 строк)
- [x] Создать `__init__.py` с router aggregation (46 строк)
- [x] Удалить старый `students.py`
- [x] Проверить OpenAPI docs (20 endpoints working)

**Примечание:** tests.py и content.py превышают лимит 400 строк.
Требуется дальнейшая оптимизация через reusable dependencies (Phase 1).

### Phase 3: Stats Service ✅ DONE (2025-12-23)
- [x] Добавить индекс `idx_student_paragraph_streak`
- [x] Добавить settings в `config.py` (MIN_DAILY_ACTIVITY_SECONDS, MASTERY_LEVEL_*_THRESHOLD)
- [x] Создать `student_stats_service.py` (160 строк)
- [x] Добавить DI factory `get_student_stats_service` в `dependencies.py`
- [x] Обновить endpoint в `stats.py` (43 строки, было 156)
- [x] Написать unit tests (`test_student_stats_service.py`)

### Phase 4: Content Service ✅ DONE (2025-12-23)
- [x] Создать `student_content_service.py` (426 строк, batch queries)
- [x] Добавить DI factory `get_student_content_service` в `dependencies.py`
- [x] Обновить endpoints в `content.py` (456 строк, было 741)
- [x] Написать unit tests (`test_student_content_service.py`)

### Phase 5: Test Taking Service
- [ ] Создать `test_taking_service.py`
- [ ] Добавить DI factory
- [ ] Обновить endpoints в `tests.py`
- [ ] Написать unit tests

### Phase 6: Progress Service
- [ ] Создать `student_progress_service.py`
- [ ] Добавить DI factory
- [ ] Обновить endpoints в `learning.py`
- [ ] Написать unit tests

### Финализация
- [ ] Создать `services/protocols.py` с интерфейсами
- [ ] Проверить все endpoints на staging
- [ ] Обновить документацию
