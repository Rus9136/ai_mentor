# SESSION LOG: Итерация 8 - Mastery Service (A/B/C алгоритм группировки)

**Дата начала:** 2025-01-07
**Дата обновления:** 2025-01-07
**Статус:** ✅ ЗАВЕРШЕНА
**Итерация:** 8 из 12
**Цель:** Реализовать полный алгоритм A/B/C группировки студентов по уровню мастерства

**Прогресс:** 7 из 7 фаз завершены (100%)

---

## 📋 ПЛАН РАБОТЫ

### ОБЗОР ИТЕРАЦИЙ (по фазам)

| Фаза | Задача | Время | Статус |
|------|--------|-------|--------|
| 1 | Repository слой (2 метода) | 30 мин | ✅ **ЗАВЕРШЕНА** |
| 2 | Алгоритм A/B/C (6 методов) | 2 часа | ✅ **ЗАВЕРШЕНА** |
| 3 | Trigger placeholder | 15 мин | ✅ **ЗАВЕРШЕНА** |
| 4 | Интеграция с GradingService | 15 мин | ✅ **ЗАВЕРШЕНА** |
| 5 | Pydantic схемы (4 шт) | 30 мин | ✅ **ЗАВЕРШЕНА** |
| 6 | API endpoints (2 шт) | 30 мин | ✅ **ЗАВЕРШЕНА** |
| 7 | Тесты (12 шт) | 2.5 часа | ✅ **ЗАВЕРШЕНА** |

**Общее время:** 5-7 часов
**Формат работы:** Итеративно с одобрением после каждой фазы

---

## 🎯 ДЕТАЛЬНЫЙ ПЛАН

### **ФАЗА 1: Repository слой** (30 мин)

#### 1.1 TestAttemptRepository.get_chapter_attempts()

**Файл:** `backend/app/repositories/test_attempt_repo.py`

**Сигнатура:**
```python
async def get_chapter_attempts(
    self,
    student_id: int,
    chapter_id: int,
    school_id: int,
    limit: int = 5,
    status: AttemptStatus = AttemptStatus.COMPLETED
) -> List[TestAttempt]:
```

**Требования:**
- JOIN с таблицей tests через test_id
- Фильтр: test.chapter_id = chapter_id
- Фильтр: student_id, school_id, status
- Сортировка: completed_at DESC
- Limit: 5 (по умолчанию)

**SQL логика:**
```sql
SELECT test_attempts.*
FROM test_attempts
JOIN tests ON tests.id = test_attempts.test_id
WHERE test_attempts.student_id = :student_id
  AND test_attempts.school_id = :school_id
  AND test_attempts.status = :status
  AND tests.chapter_id = :chapter_id
ORDER BY test_attempts.completed_at DESC
LIMIT :limit;
```

#### 1.2 ParagraphMasteryRepository.get_chapter_stats()

**Файл:** `backend/app/repositories/paragraph_mastery_repo.py`

**Сигнатура:**
```python
async def get_chapter_stats(
    self,
    student_id: int,
    chapter_id: int
) -> dict:
```

**Требования:**
- JOIN с таблицей paragraphs через paragraph_id
- Фильтр: paragraphs.chapter_id = chapter_id
- Агрегация:
  - `total`: COUNT(*)
  - `completed`: COUNT(WHERE is_completed = True)
  - `mastered`: COUNT(WHERE status = 'mastered')
  - `struggling`: COUNT(WHERE status = 'struggling')

**Возврат:**
```python
{
    'total': int,
    'completed': int,
    'mastered': int,
    'struggling': int
}
```

**SQL логика:**
```sql
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN pm.is_completed = true THEN 1 END) as completed,
    COUNT(CASE WHEN pm.status = 'mastered' THEN 1 END) as mastered,
    COUNT(CASE WHEN pm.status = 'struggling' THEN 1 END) as struggling
FROM paragraph_mastery pm
JOIN paragraphs p ON p.id = pm.paragraph_id
WHERE pm.student_id = :student_id
  AND p.chapter_id = :chapter_id;
```

**✅ Критерии завершения ФАЗЫ 1:**
- [ ] Оба метода реализованы
- [ ] Code quality: black + ruff проходят
- [ ] Manual test: методы возвращают корректные данные
- [ ] **ОСТАНОВИТЬСЯ И ЖДАТЬ ОДОБРЕНИЯ**

---

### **ФАЗА 2: Алгоритм A/B/C** (2 часа)

#### 2.1 Приватные вспомогательные методы

**Файл:** `backend/app/services/mastery_service.py`

**Методы (4 шт):**

1. **_calculate_weighted_average()**
```python
def _calculate_weighted_average(self, attempts: List[TestAttempt]) -> float:
    """
    Взвешенный средний балл (новые попытки важнее).

    Weights: [0.35, 0.25, 0.20, 0.12, 0.08]

    Returns:
        float (0.0 to 100.0)
    """
    weights = [0.35, 0.25, 0.20, 0.12, 0.08]
    scores = [a.score * 100 for a in attempts]  # 🔴 КРИТИЧНО: 0-1 → 0-100
    total_weight = sum(weights[:len(scores)])
    weighted_sum = sum(s * w for s, w in zip(scores, weights[:len(scores)]))
    return weighted_sum / total_weight
```

2. **_calculate_trend()**
```python
def _calculate_trend(self, attempts: List[TestAttempt]) -> float:
    """
    Тренд: улучшение (+) или ухудшение (-).

    Сравниваем первые 2 и последние 2 попытки.

    Returns:
        float (разница в процентах)
    """
    if len(attempts) < 3:
        return 0.0

    # Новые попытки (первые 2 в DESC сортировке)
    recent_avg = sum(a.score * 100 for a in attempts[:2]) / 2

    # Старые попытки (последние 2)
    older_avg = sum(a.score * 100 for a in attempts[-2:]) / 2

    return recent_avg - older_avg
```

3. **_calculate_consistency()**
```python
def _calculate_consistency(self, attempts: List[TestAttempt], avg: float) -> float:
    """
    Консистентность результатов (стандартное отклонение).

    Args:
        avg: Средний балл (для расчета variance)

    Returns:
        float (std_dev)
    """
    scores = [a.score * 100 for a in attempts]
    variance = sum((s - avg) ** 2 for s in scores) / len(scores)
    return variance ** 0.5
```

4. **_determine_mastery_level()**
```python
def _determine_mastery_level(
    self,
    weighted_avg: float,
    trend: float,
    std_dev: float
) -> Tuple[str, float]:
    """
    Определить A/B/C уровень мастерства.

    Критерии:
    - A: weighted_avg >= 85 AND (trend >= 0 OR std_dev < 10)
    - C: weighted_avg < 60 OR (weighted_avg < 70 AND trend < -10)
    - B: все остальные

    Returns:
        (mastery_level, mastery_score)
    """
    if weighted_avg >= 85 and (trend >= 0 or std_dev < 10):
        level = 'A'
        score = min(100.0, weighted_avg + (trend * 0.2))
    elif weighted_avg < 60 or (weighted_avg < 70 and trend < -10):
        level = 'C'
        score = max(0.0, weighted_avg + (trend * 0.2))
    else:
        level = 'B'
        score = weighted_avg

    return (level, round(score, 2))
```

#### 2.2 Основной метод calculate_chapter_mastery()

```python
async def calculate_chapter_mastery(
    self,
    student_id: int,
    chapter_id: int,
    school_id: int,
    test_attempt: Optional[TestAttempt] = None
) -> Tuple[str, float]:
    """
    Вычислить A/B/C уровень мастерства по главе.

    Алгоритм:
    1. Получить последние 5 попыток по главе
    2. Если < 3 попыток → C, 0.0
    3. Рассчитать weighted_avg, trend, std_dev
    4. Определить mastery_level (A/B/C)
    5. Обновить ChapterMastery (+ summative, paragraph stats)
    6. Создать MasteryHistory если level изменился

    Args:
        test_attempt: Передать если вызов после summative теста

    Returns:
        (mastery_level, mastery_score)
    """
    logger.info(
        f"Calculating chapter mastery: student={student_id}, chapter={chapter_id}"
    )

    # 1. Get recent test attempts
    attempts = await self.test_attempt_repo.get_chapter_attempts(
        student_id=student_id,
        chapter_id=chapter_id,
        school_id=school_id,
        limit=5
    )

    # 2. Insufficient data → default to C
    if len(attempts) < 3:
        logger.info(
            f"Insufficient data ({len(attempts)} attempts), defaulting to C"
        )
        await self._update_chapter_mastery_record(
            student_id=student_id,
            chapter_id=chapter_id,
            school_id=school_id,
            mastery_level='C',
            mastery_score=0.0,
            test_attempt=test_attempt
        )
        return ('C', 0.0)

    # 3. Calculate metrics
    weighted_avg = self._calculate_weighted_average(attempts)
    trend = self._calculate_trend(attempts)
    std_dev = self._calculate_consistency(attempts, weighted_avg)

    logger.info(
        f"Metrics: weighted_avg={weighted_avg:.2f}, "
        f"trend={trend:.2f}, std_dev={std_dev:.2f}"
    )

    # 4. Determine mastery level
    level, score = self._determine_mastery_level(weighted_avg, trend, std_dev)

    logger.info(f"Determined level: {level}, score: {score}")

    # 5. Update ChapterMastery record
    mastery = await self._update_chapter_mastery_record(
        student_id=student_id,
        chapter_id=chapter_id,
        school_id=school_id,
        mastery_level=level,
        mastery_score=score,
        test_attempt=test_attempt
    )

    # 6. Create MasteryHistory if level changed
    await self._create_mastery_history_if_changed(
        mastery=mastery,
        new_level=level,
        new_score=score,
        test_attempt_id=test_attempt.id if test_attempt else None,
        school_id=school_id
    )

    return (level, score)
```

#### 2.3 Метод _update_chapter_mastery_record()

```python
async def _update_chapter_mastery_record(
    self,
    student_id: int,
    chapter_id: int,
    school_id: int,
    mastery_level: str,
    mastery_score: float,
    test_attempt: Optional[TestAttempt] = None
) -> ChapterMastery:
    """
    Обновить ChapterMastery со всеми полями.

    Обновляемые поля:
    - mastery_level, mastery_score
    - progress_percentage
    - total/completed/mastered/struggling_paragraphs
    - summative_score/summative_passed (если summative test)
    """
    # 1. Get paragraph stats
    para_stats = await self.paragraph_repo.get_chapter_stats(
        student_id=student_id,
        chapter_id=chapter_id
    )

    # 2. Calculate progress percentage
    progress_pct = 0
    if para_stats['total'] > 0:
        progress_pct = int(100 * para_stats['completed'] / para_stats['total'])

    # 3. Prepare update fields
    update_fields = {
        "mastery_level": mastery_level,
        "mastery_score": mastery_score,
        "progress_percentage": progress_pct,

        # Paragraph counters
        "total_paragraphs": para_stats['total'],
        "completed_paragraphs": para_stats['completed'],
        "mastered_paragraphs": para_stats['mastered'],
        "struggling_paragraphs": para_stats['struggling'],
    }

    # 4. Summative test results (if applicable)
    if (test_attempt and
        hasattr(test_attempt, 'test') and
        test_attempt.test.test_purpose == TestPurpose.SUMMATIVE):
        update_fields["summative_score"] = test_attempt.score
        update_fields["summative_passed"] = test_attempt.passed
        logger.info(
            f"Updating summative results: score={test_attempt.score}, "
            f"passed={test_attempt.passed}"
        )

    # 5. Upsert ChapterMastery
    mastery = await self.chapter_repo.upsert(
        student_id=student_id,
        chapter_id=chapter_id,
        school_id=school_id,
        **update_fields
    )

    logger.info(f"ChapterMastery updated: {mastery}")

    return mastery
```

#### 2.4 Метод _create_mastery_history_if_changed()

```python
async def _create_mastery_history_if_changed(
    self,
    mastery: ChapterMastery,
    new_level: str,
    new_score: float,
    test_attempt_id: Optional[int],
    school_id: int
) -> None:
    """
    Создать MasteryHistory если level изменился.

    NOTE: Сравниваем old_level vs new_level.
    При первом создании mastery (old_level=None) history НЕ создается.
    """
    # Get old values from current mastery record
    # (assumes mastery was fetched BEFORE update in upsert)
    old_level = mastery.mastery_level
    old_score = mastery.mastery_score

    # Если level изменился (и это НЕ первое создание)
    if old_level and old_level != new_level:
        history = MasteryHistory(
            student_id=mastery.student_id,
            chapter_id=mastery.chapter_id,
            paragraph_id=None,  # chapter-level history
            school_id=school_id,
            previous_level=old_level,
            new_level=new_level,
            previous_score=old_score,
            new_score=new_score,
            test_attempt_id=test_attempt_id
        )
        self.db.add(history)
        await self.db.commit()

        logger.info(
            f"MasteryHistory created: {old_level} -> {new_level} "
            f"(score: {old_score:.2f} -> {new_score:.2f})"
        )
    else:
        logger.info(
            f"MasteryHistory NOT created: level unchanged ({new_level}) "
            f"or first creation"
        )
```

**🔴 ПРОБЛЕМА:** ChapterMasteryRepository.upsert() может перезаписать old values.

**РЕШЕНИЕ:** Сначала GET, потом UPDATE:

```python
# В _update_chapter_mastery_record() изменить:

# 5a. Get existing mastery (for history tracking)
existing = await self.chapter_repo.get_by_student_chapter(
    student_id=student_id,
    chapter_id=chapter_id
)

old_level = existing.mastery_level if existing else None
old_score = existing.mastery_score if existing else None

# 5b. Upsert ChapterMastery
mastery = await self.chapter_repo.upsert(...)

# 5c. Attach old values for history tracking
mastery._old_level = old_level
mastery._old_score = old_score

return mastery
```

Затем в `_create_mastery_history_if_changed()`:
```python
old_level = getattr(mastery, '_old_level', None)
old_score = getattr(mastery, '_old_score', None)
```

**✅ Критерии завершения ФАЗЫ 2:**
- [ ] 4 приватных метода реализованы
- [ ] calculate_chapter_mastery() реализован
- [ ] _update_chapter_mastery_record() обновляет ВСЕ поля
- [ ] _create_mastery_history_if_changed() корректно работает
- [ ] Code quality: black + ruff
- [ ] Manual test: алгоритм работает на toy data
- [ ] **ОСТАНОВИТЬСЯ И ЖДАТЬ ОДОБРЕНИЯ**

---

### **ФАЗА 3: trigger_chapter_recalculation()** (15 мин)

**Файл:** `backend/app/services/mastery_service.py`

**Убрать placeholder:**

```python
async def trigger_chapter_recalculation(
    self,
    student_id: int,
    chapter_id: int,
    school_id: int,
    test_attempt: Optional[TestAttempt] = None
) -> Optional[ChapterMastery]:
    """
    Пересчитать chapter mastery.

    Вызывается после:
    - Формативного теста (опционально, если есть chapter_id)
    - Суммативного теста (обязательно)

    Args:
        test_attempt: Передать для обновления summative_score

    Returns:
        Updated ChapterMastery или None
    """
    logger.info(
        f"Triggering chapter mastery recalculation: "
        f"student={student_id}, chapter={chapter_id}"
    )

    # Calculate new mastery level
    level, score = await self.calculate_chapter_mastery(
        student_id=student_id,
        chapter_id=chapter_id,
        school_id=school_id,
        test_attempt=test_attempt
    )

    logger.info(
        f"Chapter mastery recalculated: level={level}, score={score}"
    )

    # Return updated ChapterMastery
    mastery = await self.chapter_repo.get_by_student_chapter(
        student_id=student_id,
        chapter_id=chapter_id
    )

    return mastery
```

**✅ Критерии завершения ФАЗЫ 3:**
- [ ] Placeholder убран
- [ ] Метод корректно вызывает calculate_chapter_mastery()
- [ ] **ОСТАНОВИТЬСЯ И ЖДАТЬ ОДОБРЕНИЯ**

---

### **ФАЗА 4: Интеграция с GradingService** (15 мин)

**Файл:** `backend/app/services/grading_service.py`

**Изменения в методе grade_attempt():**

Найти секцию (примерно строка 251):
```python
# 8. Trigger mastery update для ФОРМАТИВНЫХ и СУММАТИВНЫХ
```

**Заменить на:**

```python
# 8. Trigger mastery update для ФОРМАТИВНЫХ и СУММАТИВНЫХ
if attempt.test.test_purpose in (TestPurpose.FORMATIVE, TestPurpose.SUMMATIVE):

    # 8a. Paragraph mastery (если тест paragraph-level)
    if attempt.test.paragraph_id:
        await mastery_service.update_paragraph_mastery(
            student_id=attempt.student_id,
            paragraph_id=attempt.test.paragraph_id,
            test_score=attempt.score,
            test_attempt_id=attempt.id,
            school_id=attempt.school_id
        )

    # 8b. Chapter mastery (ВСЕГДА если есть chapter_id)
    # 🆕 ИЗМЕНЕНИЕ: вызывать для ЛЮБОГО теста (формативного/суммативного)
    if attempt.test.chapter_id:
        await mastery_service.trigger_chapter_recalculation(
            student_id=attempt.student_id,
            chapter_id=attempt.test.chapter_id,
            school_id=attempt.school_id,
            test_attempt=attempt  # 🆕 Передать для summative_score
        )
        logger.info(
            f"Chapter mastery triggered for chapter {attempt.test.chapter_id}"
        )
```

**Обоснование:** ChapterMastery должен обновляться после ЛЮБОГО теста главы, не только summative.

**✅ Критерии завершения ФАЗЫ 4:**
- [ ] Интеграция реализована
- [ ] Код проходит black/ruff
- [ ] Manual test: после submit теста ChapterMastery обновляется
- [ ] **ОСТАНОВИТЬСЯ И ЖДАТЬ ОДОБРЕНИЯ**

---

### **ФАЗА 5: Pydantic Schemas** (30 мин)

**Файл:** `backend/app/schemas/mastery.py` (НОВЫЙ файл)

**Создать 3 схемы:**

```python
"""Pydantic schemas for mastery responses."""

from pydantic import BaseModel, ConfigDict
from typing import Optional


class ParagraphMasteryResponse(BaseModel):
    """Response schema for paragraph mastery."""

    model_config = ConfigDict(from_attributes=True)

    paragraph_id: int
    paragraph_title: str

    # Status
    status: str  # struggling, progressing, mastered

    # Scores
    test_score: Optional[float] = None  # 0.0 to 1.0
    average_score: Optional[float] = None
    best_score: Optional[float] = None

    # Stats
    attempts_count: int
    is_completed: bool


class ChapterMasteryResponse(BaseModel):
    """Response schema for chapter mastery."""

    model_config = ConfigDict(from_attributes=True)

    chapter_id: int
    chapter_title: str

    # A/B/C Grouping
    mastery_level: str  # A, B, or C
    mastery_score: float  # 0.0 to 100.0

    # Progress
    progress_percentage: int  # 0 to 100

    # Paragraph stats
    total_paragraphs: int
    completed_paragraphs: int
    mastered_paragraphs: int
    struggling_paragraphs: int

    # Summative test (optional)
    summative_score: Optional[float] = None
    summative_passed: Optional[bool] = None


class ChapterMasteryDetailResponse(ChapterMasteryResponse):
    """Detailed response with paragraph breakdown."""

    paragraphs: list[ParagraphMasteryResponse]
```

**Также обновить:**

`backend/app/schemas/__init__.py`:
```python
# Добавить импорты
from .mastery import (
    ParagraphMasteryResponse,
    ChapterMasteryResponse,
    ChapterMasteryDetailResponse
)
```

**✅ Критерии завершения ФАЗЫ 5:**
- [ ] 3 схемы созданы
- [ ] Экспорты добавлены в __init__.py
- [ ] **ОСТАНОВИТЬСЯ И ЖДАТЬ ОДОБРЕНИЯ**

---

### **ФАЗА 6: API Endpoints** (30 мин)

**Файл:** `backend/app/api/v1/students.py`

**Добавить 2 endpoint:**

```python
# В начало файла добавить импорты:
from app.schemas.mastery import (
    ChapterMasteryResponse,
    ChapterMasteryDetailResponse,
    ParagraphMasteryResponse
)
from app.repositories.chapter_mastery_repo import ChapterMasteryRepository
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph

# ... существующие endpoints ...

@router.get(
    "/mastery/chapter/{chapter_id}",
    response_model=ChapterMasteryDetailResponse,
    summary="Get chapter mastery for current student"
)
async def get_chapter_mastery(
    chapter_id: int,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed chapter mastery for the current student.

    Returns:
    - mastery_level (A/B/C)
    - mastery_score (0-100)
    - progress_percentage
    - paragraph breakdown with individual mastery statuses
    """
    # 1. Get ChapterMastery
    chapter_repo = ChapterMasteryRepository(db)
    mastery = await chapter_repo.get_by_student_chapter(
        student_id=current_student.id,
        chapter_id=chapter_id
    )

    if not mastery:
        raise HTTPException(
            status_code=404,
            detail=f"Chapter mastery not found for chapter {chapter_id}"
        )

    # 2. Get Chapter details
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id)
    )
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # 3. Get paragraph mastery details
    para_repo = ParagraphMasteryRepository(db)
    para_masteries = await para_repo.get_by_student(
        student_id=current_student.id
    )

    # Filter for this chapter (через JOIN с paragraphs)
    result = await db.execute(
        select(ParagraphMastery, Paragraph)
        .join(Paragraph, Paragraph.id == ParagraphMastery.paragraph_id)
        .where(
            ParagraphMastery.student_id == current_student.id,
            Paragraph.chapter_id == chapter_id
        )
    )
    para_data = result.all()

    # 4. Build paragraph responses
    paragraphs = [
        ParagraphMasteryResponse(
            **pm.__dict__,
            paragraph_title=p.title
        )
        for pm, p in para_data
    ]

    # 5. Build response
    return ChapterMasteryDetailResponse(
        **mastery.__dict__,
        chapter_title=chapter.title,
        paragraphs=paragraphs
    )


@router.get(
    "/mastery/overview",
    response_model=list[ChapterMasteryResponse],
    summary="Get mastery overview for current student"
)
async def get_mastery_overview(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get mastery overview for all chapters of the current student.

    Returns list of chapter masteries with A/B/C levels.
    """
    # 1. Get all ChapterMastery for student
    chapter_repo = ChapterMasteryRepository(db)
    masteries = await chapter_repo.get_by_student(
        student_id=current_student.id
    )

    if not masteries:
        return []

    # 2. Get chapter details (bulk)
    chapter_ids = [m.chapter_id for m in masteries]
    result = await db.execute(
        select(Chapter).where(Chapter.id.in_(chapter_ids))
    )
    chapters = {c.id: c for c in result.scalars().all()}

    # 3. Build responses
    responses = []
    for mastery in masteries:
        chapter = chapters.get(mastery.chapter_id)
        if chapter:
            responses.append(
                ChapterMasteryResponse(
                    **mastery.__dict__,
                    chapter_title=chapter.title
                )
            )

    return responses
```

**Также добавить импорты в начало файла:**
```python
from sqlalchemy import select
```

**✅ Критерии завершения ФАЗЫ 6:**
- [ ] 2 endpoint реализованы
- [ ] Code quality проходит
- [ ] Swagger UI отображает endpoints корректно
- [ ] Manual test через Swagger UI работает
- [ ] **ОСТАНОВИТЬСЯ И ЖДАТЬ ОДОБРЕНИЯ**

---

### **ФАЗА 7: Тесты** (2.5 часа)

**Файл:** `backend/tests/test_mastery_service.py` (НОВЫЙ файл)

**Структура тестового файла:**

```python
"""Tests for MasteryService (A/B/C algorithm)."""

import pytest
from datetime import datetime, timedelta

from app.models.test_attempt import TestAttempt, AttemptStatus
from app.models.mastery import ChapterMastery, MasteryHistory
from app.services.mastery_service import MasteryService


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def create_test_attempt(
    db,
    student_id: int,
    test_id: int,
    school_id: int,
    score: float,  # 0.0 to 1.0
    passed: bool,
    completed_at: datetime
) -> TestAttempt:
    """Helper to create a completed test attempt."""
    attempt = TestAttempt(
        student_id=student_id,
        test_id=test_id,
        school_id=school_id,
        status=AttemptStatus.COMPLETED,
        score=score,
        passed=passed,
        started_at=completed_at - timedelta(minutes=30),
        completed_at=completed_at
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return attempt


# ============================================================================
# БАЗОВЫЕ 8 ТЕСТОВ
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_chapter_mastery_level_A(
    db_session,
    student,
    school,
    chapter,
    test_summative
):
    """Студент с 85%+ и стабильными результатами → A."""
    # TODO: Реализовать
    pass


@pytest.mark.asyncio
async def test_calculate_chapter_mastery_level_B(
    db_session,
    student,
    school,
    chapter,
    test_summative
):
    """Студент с 60-84% → B."""
    # TODO: Реализовать
    pass


@pytest.mark.asyncio
async def test_calculate_chapter_mastery_level_C(
    db_session,
    student,
    school,
    chapter,
    test_summative
):
    """Студент с <60% → C."""
    # TODO: Реализовать
    pass


@pytest.mark.asyncio
async def test_calculate_chapter_mastery_improving_trend(
    db_session,
    student,
    school,
    chapter,
    test_summative
):
    """Проверка улучшения: последние попытки лучше старых."""
    # TODO: Реализовать
    pass


@pytest.mark.asyncio
async def test_calculate_chapter_mastery_degrading_trend(
    db_session,
    student,
    school,
    chapter,
    test_summative
):
    """Проверка ухудшения: A → B → C при падении результатов."""
    # TODO: Реализовать
    pass


@pytest.mark.asyncio
async def test_calculate_chapter_mastery_insufficient_data(
    db_session,
    student,
    school,
    chapter,
    test_summative
):
    """Менее 3 попыток → C, score=0.0."""
    # TODO: Реализовать
    pass


@pytest.mark.asyncio
async def test_chapter_mastery_history_created(
    db_session,
    student,
    school,
    chapter,
    test_summative
):
    """При изменении level создается MasteryHistory."""
    # TODO: Реализовать
    pass


@pytest.mark.asyncio
async def test_chapter_mastery_tenant_isolation(
    db_session,
    student,
    student2_other_school,
    school,
    school2,
    chapter,
    test_summative
):
    """school_id изоляция работает корректно."""
    # TODO: Реализовать
    pass


# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ 4 ТЕСТА
# ============================================================================

@pytest.mark.asyncio
async def test_chapter_mastery_with_summative_test(
    db_session,
    student,
    school,
    chapter,
    test_summative
):
    """Проверка обновления summative_score/summative_passed."""
    # TODO: Реализовать
    pass


@pytest.mark.asyncio
async def test_chapter_mastery_paragraph_stats_update(
    db_session,
    student,
    school,
    chapter,
    paragraph,
    test_summative
):
    """Счетчики параграфов обновляются корректно."""
    # TODO: Реализовать
    pass


@pytest.mark.asyncio
async def test_chapter_mastery_no_paragraphs(
    db_session,
    student,
    school,
    chapter,
    test_summative
):
    """Edge case: глава без параграфов."""
    # TODO: Реализовать
    pass


@pytest.mark.asyncio
async def test_chapter_mastery_idempotency(
    db_session,
    student,
    school,
    chapter,
    test_summative
):
    """Повторный вызов с теми же данными не меняет результат."""
    # TODO: Реализовать
    pass
```

**Детальная реализация каждого теста:**

*(Будет заполнено в процессе реализации ФАЗЫ 7)*

**✅ Критерии завершения ФАЗЫ 7:**
- [ ] 12/12 тестов реализованы
- [ ] Все тесты проходят (green)
- [ ] Coverage для mastery_service.py > 90%
- [ ] Fixtures используются из conftest.py
- [ ] **ОСТАНОВИТЬСЯ И ЖДАТЬ ОДОБРЕНИЯ**

---

## 📊 КРИТЕРИИ ЗАВЕРШЕНИЯ ИТЕРАЦИИ 8

**Обязательно (100%):**
- [ ] calculate_chapter_mastery() реализован с приватными методами
- [ ] Использует attempt.score * 100 (не percentage)
- [ ] Обновляет счетчики параграфов (total, completed, mastered, struggling)
- [ ] Обновляет summative_score/summative_passed
- [ ] trigger_chapter_recalculation() убран placeholder
- [ ] get_chapter_attempts() создан
- [ ] get_chapter_stats() создан
- [ ] Интеграция с GradingService (вызов ВСЕГДА для chapter tests)
- [ ] 2 API endpoints работают
- [ ] 3 Pydantic схемы созданы
- [ ] 12/12 тестов проходят
- [ ] MasteryHistory создается при изменении level
- [ ] Tenant isolation (school_id) работает

**После завершения:**
- [ ] ChapterMastery автоматически обновляется после каждого теста
- [ ] Студенты распределяются по группам A/B/C
- [ ] MasteryHistory отслеживает прогресс (C→B→A)
- [ ] API endpoints готовы для frontend
- [ ] Готовность к Итерации 9 (RAG Service)

---

## 📝 ЖУРНАЛ РАБОТЫ

### 2025-01-07 (14:00-15:30) - ✅ ФАЗА 1 ЗАВЕРШЕНА

**Реализовано:**
1. ✅ TestAttemptRepository.get_chapter_attempts()
   - JOIN с таблицей tests
   - Фильтрация по chapter_id, student_id, school_id, status
   - Сортировка по completed_at DESC
   - Limit 5 (для алгоритма)

2. ✅ ParagraphMasteryRepository.get_chapter_stats()
   - LEFT JOIN paragraph_mastery с paragraphs
   - Агрегация: total, completed, mastered, struggling
   - Возвращает Dict[str, int]

**Файлы изменены:**
- backend/app/repositories/test_attempt_repo.py (+40 строк)
- backend/app/repositories/paragraph_mastery_repo.py (+54 строки)

**Итого:** ~94 строки кода

---

### 2025-01-07 (15:30-17:00) - ✅ ФАЗА 2 ЗАВЕРШЕНА

**Реализовано:**

**2.1 Приватные вспомогательные методы (4 шт):**
1. ✅ _calculate_weighted_average()
   - Веса: [0.35, 0.25, 0.20, 0.12, 0.08]
   - **КРИТИЧНО:** Конвертация attempt.score * 100 (0-1 → 0-100)
   - Возвращает weighted average (0-100)

2. ✅ _calculate_trend()
   - Сравнивает первые 2 vs последние 2 попытки
   - Положительный тренд = улучшение
   - Возвращает разницу в процентах

3. ✅ _calculate_consistency()
   - Вычисляет стандартное отклонение
   - Низкая std_dev = стабильные результаты

4. ✅ _determine_mastery_level()
   - **A**: weighted_avg >= 85 AND (trend >= 0 OR std_dev < 10)
   - **C**: weighted_avg < 60 OR (weighted_avg < 70 AND trend < -10)
   - **B**: все остальные

**2.2 Основной метод calculate_chapter_mastery():**
- ✅ Получение последних 5 test attempts
- ✅ Проверка на insufficient data (< 3 attempts)
- ✅ Расчет метрик (weighted_avg, trend, std_dev)
- ✅ Определение mastery_level (A/B/C)
- ✅ Обновление ChapterMastery
- ✅ Создание MasteryHistory при изменении

**2.3 Вспомогательный метод _update_chapter_mastery_record():**
- ✅ Обновление mastery_level, mastery_score
- ✅ Обновление progress_percentage
- ✅ Обновление счетчиков параграфов (total, completed, mastered, struggling)
- ✅ Обновление summative_score/summative_passed (если SUMMATIVE test)
- ✅ GET existing для old values (для history tracking)
- ✅ Attach _old_level, _old_score для history

**2.4 Вспомогательный метод _create_mastery_history_if_changed():**
- ✅ Сравнение old_level vs new_level
- ✅ Создание MasteryHistory только при изменении
- ✅ Полиморфная модель (chapter_id != NULL, paragraph_id = NULL)

**Файлы изменены:**
- backend/app/services/mastery_service.py (+356 строк)
  - Обновление импортов (+5 строк)
  - __init__ (+2 строки)
  - 4 приватных метода (~98 строк)
  - calculate_chapter_mastery() (~100 строк)
  - _update_chapter_mastery_record() (~95 строк)
  - _create_mastery_history_if_changed() (~56 строк)

**Итого:** ~356 строк кода

---

### 2025-01-07 (17:00-17:15) - ✅ ФАЗА 3 ЗАВЕРШЕНА

**Реализовано:**
1. ✅ trigger_chapter_recalculation() - убран placeholder
   - Добавлен параметр `test_attempt: Optional[TestAttempt] = None`
   - Изменен return type: `None` → `Optional[ChapterMastery]`
   - Реализован вызов `calculate_chapter_mastery()` с передачей test_attempt
   - Добавлен возврат обновленной записи ChapterMastery
   - Обновлен docstring с пояснением "Called after ANY test attempt"

**Файлы изменены:**
- backend/app/services/mastery_service.py (~52 строки изменены)
  - Сигнатура метода (4 строки)
  - Docstring (22 строки)
  - Реализация (26 строк)

**Ключевые изменения:**
- Метод теперь принимает `test_attempt` для summative results
- Возвращает `Optional[ChapterMastery]` вместо `None`
- Полностью интегрирован с алгоритмом A/B/C из ФАЗЫ 2

**Итого:** ~52 строки кода (замена placeholder)

---

### 2025-01-07 (17:15-17:25) - ✅ ФАЗА 4 ЗАВЕРШЕНА

**Реализовано:**
1. ✅ Интеграция с GradingService.grade_attempt()
   - Добавлен вызов `trigger_chapter_recalculation()` после оценки теста
   - Вызывается для ВСЕХ FORMATIVE и SUMMATIVE тестов с chapter_id
   - Передается `test_attempt` для summative results
   - Перенесена инициализация MasteryService наверх блока (DRY)

**Файлы изменены:**
- backend/app/services/grading_service.py (~20 строк изменены)
  - Секция 8b: Chapter mastery recalculation (15 строк)
  - Рефакторинг секции 8a (5 строк)

**Ключевые изменения:**
- Теперь chapter mastery пересчитывается АВТОМАТИЧЕСКИ после каждого теста
- Работает для параграфных тестов (с paragraph_id) И глав-level тестов
- MasteryService инстанцируется один раз для обоих вызовов

**Логика флоу:**
```
FORMATIVE/SUMMATIVE test completed
  → grade_attempt()
    → if test.paragraph_id: update_paragraph_mastery()
    → if test.chapter_id: trigger_chapter_recalculation()
      → calculate_chapter_mastery()
        → A/B/C алгоритм
        → update ChapterMastery
        → create MasteryHistory (если изменился уровень)
```

**Итого:** ~20 строк кода (интеграция)

---

### 2025-01-07 (17:25-17:35) - ✅ ФАЗА 5 ЗАВЕРШЕНА

**Реализовано:**
1. ✅ Создан файл backend/app/schemas/mastery.py с 4 схемами:
   - **ParagraphMasteryResponse** - для GET /students/mastery/paragraph/{id}
   - **ChapterMasteryResponse** - для GET /students/mastery/chapter/{id}
   - **ChapterMasteryDetailResponse** - расширенная с chapter info
   - **MasteryOverviewResponse** - для GET /students/mastery/overview

2. ✅ Обновлен backend/app/schemas/__init__.py
   - Добавлен импорт из mastery
   - Добавлены 4 схемы в __all__

**Файлы изменены:**
- backend/app/schemas/mastery.py (NEW FILE, ~150 строк)
- backend/app/schemas/__init__.py (+9 строк)

**Ключевые особенности схем:**
- ConfigDict(from_attributes=True) для ORM mapping
- Field() с description для документации
- Поддержка Optional полей (summative_score, average_score)
- MasteryOverviewResponse с агрегацией (level_a_count, level_b_count, level_c_count)

**Схемы готовы для:**
- API endpoints (ФАЗА 6)
- OpenAPI documentation (автоматически через FastAPI)
- Frontend integration

**Итого:** ~159 строк кода (новый файл + обновление __init__)

---

### 2025-01-07 (17:35-17:55) - ✅ ФАЗА 6 ЗАВЕРШЕНА

**Реализовано:**
1. ✅ Созданы 2 API endpoints для студентов в backend/app/api/v1/students.py:

   **a) GET /students/mastery/chapter/{chapter_id}**
   - Принимает chapter_id как path parameter
   - Использует зависимости: require_student, get_current_user_school_id
   - Возвращает ChapterMasteryResponse с A/B/C уровнем
   - Проверяет tenant isolation (school_id)
   - Возвращает 404 если student еще не начал главу
   - Логирует получение данных с level и score

   **b) GET /students/mastery/overview**
   - Возвращает все главы для текущего студента
   - Обогащает данные chapter title и order из Chapter model
   - Вычисляет агрегированную статистику:
     - total_chapters (общее количество)
     - level_a_count, level_b_count, level_c_count (распределение)
     - average_mastery_score (средний балл по всем главам)
   - Возвращает MasteryOverviewResponse
   - Логирует overview с детализацией по уровням

2. ✅ Добавлены импорты:
   - ChapterMasteryRepository
   - Mastery schemas (ChapterMasteryResponse, ChapterMasteryDetailResponse, MasteryOverviewResponse)

**Файлы изменены:**
- backend/app/api/v1/students.py (~150 строк)
  - Импорты (+6 строк)
  - GET /mastery/chapter/{chapter_id} endpoint (~55 строк)
  - GET /mastery/overview endpoint (~90 строк)

**Ключевые особенности:**
- Оба endpoint используют существующий authentication flow (require_student)
- Tenant isolation обеспечивается через get_current_user_school_id
- Обогащение данных: mastery records + chapter info (title, order)
- Агрегированная статистика для overview (level distribution)
- Детальное логирование для debugging
- Возвращают typed Pydantic responses для OpenAPI

**API готово для:**
- Frontend integration
- Swagger UI testing (http://localhost:8000/docs)
- Mobile app integration

**Итого:** ~150 строк кода (2 endpoints)

---

### 2025-01-07 (17:55-18:30) - ✅ ФАЗА 7 ЗАВЕРШЕНА

**Реализовано:**
1. ✅ Создан файл backend/tests/test_mastery_service.py с 12 тестами:

   **8 базовых тестов:**
   1. `test_calculate_chapter_mastery_level_A` - студент с 85%+ → A
   2. `test_calculate_chapter_mastery_level_B` - студент с 60-84% → B
   3. `test_calculate_chapter_mastery_level_C` - студент с <60% → C
   4. `test_calculate_chapter_mastery_improving_trend` - positive trend
   5. `test_calculate_chapter_mastery_degrading_trend` - negative trend
   6. `test_calculate_chapter_mastery_insufficient_data` - < 3 attempts → C, 0.0
   7. `test_chapter_mastery_history_created` - MasteryHistory при изменении level
   8. `test_chapter_mastery_tenant_isolation` - school_id изоляция

   **4 дополнительных теста:**
   9. `test_chapter_mastery_with_summative_test` - summative_score/summative_passed
   10. `test_chapter_mastery_paragraph_stats_update` - счетчики параграфов
   11. `test_chapter_mastery_edge_cases` - boundary cases (exactly 3 attempts, 85%, 60%)
   12. `test_chapter_mastery_idempotency` - повторный вызов не меняет результат

2. ✅ Созданы helper fixtures:
   - `summative_test` - суммативный тест для главы
   - `paragraph2` - второй параграф для тестов статистики
   - `create_test_attempt()` - helper для создания test attempts

3. ✅ Запущены тесты: **12/12 PASSED** за 12.26 секунд

**Файлы изменены:**
- backend/tests/test_mastery_service.py (NEW FILE, ~800 строк)
  - Импорты и helper fixtures (~80 строк)
  - 8 базовых тестов (~400 строк)
  - 4 дополнительных теста (~320 строк)

**Результаты тестирования:**
```
============================= test session starts ==============================
tests/test_mastery_service.py::test_calculate_chapter_mastery_level_A PASSED [  8%]
tests/test_mastery_service.py::test_calculate_chapter_mastery_level_B PASSED [ 16%]
tests/test_mastery_service.py::test_calculate_chapter_mastery_level_C PASSED [ 25%]
tests/test_mastery_service.py::test_calculate_chapter_mastery_improving_trend PASSED [ 33%]
tests/test_mastery_service.py::test_calculate_chapter_mastery_degrading_trend PASSED [ 41%]
tests/test_mastery_service.py::test_calculate_chapter_mastery_insufficient_data PASSED [ 50%]
tests/test_mastery_service.py::test_chapter_mastery_history_created PASSED [ 58%]
tests/test_mastery_service.py::test_chapter_mastery_tenant_isolation PASSED [ 66%]
tests/test_mastery_service.py::test_chapter_mastery_with_summative_test PASSED [ 75%]
tests/test_mastery_service.py::test_chapter_mastery_paragraph_stats_update PASSED [ 83%]
tests/test_mastery_service.py::test_chapter_mastery_edge_cases PASSED [ 91%]
tests/test_mastery_service.py::test_chapter_mastery_idempotency PASSED [100%]

======================= 12 passed, 24 warnings in 12.26s =======================
```

**Покрытие тестами:**
- ✅ Алгоритм A/B/C (все 4 приватных метода)
- ✅ calculate_chapter_mastery() (основной метод)
- ✅ _update_chapter_mastery_record() (обновление полей)
- ✅ _create_mastery_history_if_changed() (история изменений)
- ✅ trigger_chapter_recalculation() (интеграция)
- ✅ Tenant isolation (school_id)
- ✅ Paragraph stats aggregation
- ✅ Summative test results
- ✅ Edge cases (boundary values, insufficient data)
- ✅ Idempotency (повторные вызовы)

**Итого:** ~800 строк тестов

---

### 2025-01-07 (18:30) - ✅ ИТЕРАЦИЯ 8 ЗАВЕРШЕНА

**Выполнено:**
- ✅ ФАЗА 1: Repository слой (2 метода)
- ✅ ФАЗА 2: Алгоритм A/B/C (6 методов)
- ✅ ФАЗА 3: Trigger recalculation
- ✅ ФАЗА 4: Интеграция с GradingService
- ✅ ФАЗА 5: Pydantic схемы (4 схемы)
- ✅ ФАЗА 6: API endpoints (2 endpoint)
- ✅ ФАЗА 7: Тесты (12 тестов)

**Всего добавлено:** ~1,630 строк кода
- Repository слой: ~94 строки
- Алгоритм A/B/C: ~356 строк
- Trigger: ~52 строки
- Интеграция: ~20 строк
- Pydantic схемы: ~159 строк
- API endpoints: ~150 строк
- Тесты: ~800 строк

**Результаты:**
- ✅ ChapterMastery автоматически обновляется после каждого теста
- ✅ Студенты распределяются по группам A/B/C
- ✅ MasteryHistory отслеживает прогресс (C→B→A)
- ✅ API endpoints готовы для frontend
- ✅ 12/12 тестов проходят успешно
- ✅ Tenant isolation работает корректно

**Готовность к Итерации 9:** 100%

---

## 🔧 ТЕХНИЧЕСКИЕ ЗАМЕЧАНИЯ

### Критические моменты

1. **TestAttempt.score** - это float (0.0 to 1.0), НЕ percentage (0-100)
   - В алгоритме использовать: `attempt.score * 100`

2. **ChapterMastery.mastery_score** - это float (0.0 to 100.0)

3. **MasteryHistory** - полиморфная модель:
   - chapter_id OR paragraph_id (один из них NULL)
   - Для chapter-level: chapter_id != NULL, paragraph_id = NULL

4. **Async/await** - все методы асинхронные

5. **Upsert pattern** - получить old values ДО update для history tracking

### Workflow

```
TestAttempt (COMPLETED)
  ↓
GradingService.grade_attempt()
  ↓
MasteryService.update_paragraph_mastery() (если paragraph_id)
  ↓
MasteryService.trigger_chapter_recalculation() (если chapter_id)
  ↓
MasteryService.calculate_chapter_mastery()
  ↓
ChapterMastery (upsert)
  ↓
MasteryHistory (если level изменился)
```

---

## 🎯 ИТОГОВЫЕ МЕТРИКИ

**Оценка времени:** 5-7 часов
**Приоритет:** Высокий
**Риски:** Низкие
**Зависимости:** Все готовы (Итерация 7 завершена)

**Ожидаемый результат:**
- Полный алгоритм A/B/C работает
- ChapterMastery обновляется автоматически
- Teacher Dashboard (Итерация 10) сможет показывать A/B/C группировку класса
