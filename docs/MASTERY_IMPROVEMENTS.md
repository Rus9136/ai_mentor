# Улучшение системы мастерства (Mastery System v2)

## Содержание

1. [Текущая система — что работает хорошо](#1-текущая-система--что-работает-хорошо)
2. [Фундаментальная проблема](#2-фундаментальная-проблема)
3. [Блок 1: Time Decay (временное затухание)](#3-блок-1-time-decay-временное-затухание) — **ВЫПОЛНЕНО**
4. [Блок 2: Spaced Repetition (интервальное повторение)](#4-блок-2-spaced-repetition-интервальное-повторение) — **ВЫПОЛНЕНО**
5. [Блок 3: Паттерны самооценки (Metacognitive Coaching)](#5-блок-3-паттерны-самооценки-metacognitive-coaching)
6. [Блок 4: Provisional статус для новых учеников](#6-блок-4-provisional-статус-для-новых-учеников)
7. [Блок 5: Knowledge Graph (граф зависимостей)](#7-блок-5-knowledge-graph-граф-зависимостей)
8. [Блок 6: Confidence-Weighted Mastery (BKT)](#8-блок-6-confidence-weighted-mastery-bkt)
9. [Блок 7: Difficulty-Weighted Scoring (Bloom's Taxonomy)](#9-блок-7-difficulty-weighted-scoring-blooms-taxonomy)
10. [Дорожная карта внедрения](#10-дорожная-карта-внедрения)

---

## 1. Текущая система — что работает хорошо

### Разделение объективного и субъективного мастерства

Большинство EdTech платформ смешивают результаты тестов и самооценку в один балл, теряя метакогнитивный сигнал. В AI Mentor это разделено:

- **Объективное** (`paragraph_mastery`) — результаты formative/summative тестов, шкала 0.0–1.0
- **Субъективное** (`paragraph_self_assessments`) — самооценка ученика (understood/questions/difficult)

Расхождение между ними — ценная аналитика для учителя: "ученик думает что понял, но тесты говорят обратное".

### A/B/C группировка с учётом тренда

Текущий алгоритм учитывает не только абсолютный балл, но и **направление динамики** (улучшается/ухудшается) и **стабильность** (стандартное отклонение). Это лучше, чем статические пороги.

### Append-only история изменений

Таблица `mastery_history` хранит полный аудит всех изменений статусов и уровней. Данные никогда не удаляются — это позволяет строить аналитику за любой период.

---

## 2. Фундаментальная проблема

### best_score никогда не снижается

Текущая формула: `best_score = max(предыдущий_лучший, новый_результат)`

Это противоречит **кривой забывания Эббингауза** — доказанному факту, что знания деградируют без повторения.

**Реальный сценарий:**

```
Октябрь: ученик сдал тест на 90% → статус "mastered"
Март (5 месяцев спустя): ученик забыл 70% материала
Система всё ещё показывает "mastered" ← ПРОБЛЕМА
```

**Последствия:**
- Ложное чувство прогресса у ученика и учителя
- Нет мотивации к повторению пройденного
- Итоговая аттестация показывает реальные пробелы, которые система не предсказала
- Система измеряет "что ученик когда-то знал", а должна — "что ученик знает сейчас"

Платформы уровня Duolingo, Khan Academy, Anki решают это через time decay и spaced repetition.

---

## 3. Блок 1: Time Decay (временное затухание) — ВЫПОЛНЕНО

### Приоритет: ВЫСОКИЙ | Сложность: НИЗКАЯ | Статус: ВЫПОЛНЕНО

### Суть

Ввести `effective_score` — скорректированный балл, который снижается со временем без повторения. `best_score` остаётся как исторический факт (лучшая попытка за всё время), но для отображения статуса и рекомендаций используется `effective_score`.

### Формула

```python
import math

def calculate_effective_score(best_score: float, last_updated_at: datetime) -> float:
    """
    Рассчитывает effective_score с экспоненциальным затуханием.

    Параметры затухания:
    - decay_rate = 0.002 в день
    - За 30 дней: сохраняется ~94% (минимальное затухание)
    - За 90 дней: сохраняется ~83%
    - За 180 дней: сохраняется ~70%
    - За 365 дней: сохраняется ~48%
    """
    days_since_last = (datetime.utcnow() - last_updated_at).days
    decay_rate = 0.002
    effective_score = best_score * math.exp(-decay_rate * days_since_last)
    return round(effective_score, 4)
```

### Поведение статусов с decay

```
Ученик сдал на 90% (mastered) и не возвращается:
- Через 1 месяц:  effective = 84% → progressing (ещё ОК)
- Через 3 месяца: effective = 75% → progressing (пора повторить)
- Через 6 месяцев: effective = 63% → progressing (нужно повторение)
- Через 9 месяцев: effective = 53% → struggling (критично)

Ученик сдал на 70% (progressing) и не возвращается:
- Через 3 месяца: effective = 58% → struggling
```

### Сброс decay

При повторном прохождении теста:
- `best_score = max(best_score, new_score)` — обновляется если новый результат лучше
- `last_updated_at = now()` — decay сбрасывается
- `effective_score` снова равен `best_score`

### Изменения в БД

```sql
-- Добавить поле в paragraph_mastery
ALTER TABLE paragraph_mastery ADD COLUMN effective_score FLOAT DEFAULT NULL;
ALTER TABLE paragraph_mastery ADD COLUMN decay_rate FLOAT DEFAULT 0.002;
```

### Изменения в коде

```python
# mastery_service.py — при запросе статуса
def get_paragraph_status(mastery: ParagraphMastery) -> str:
    effective = calculate_effective_score(
        mastery.best_score,
        mastery.last_updated_at
    )
    if effective >= 0.85:
        return "mastered"
    elif effective >= 0.60:
        return "progressing"
    else:
        return "struggling"
```

### UI-индикация

- Параграфы с decay > 15% помечаются значком "нужно повторение"
- Цвет прогресс-бара плавно тускнеет со временем
- Tooltip: "Последний тест 3 месяца назад. Повтори, чтобы закрепить знания"

### Реализация (выполнено)

**Подход:** `effective_score` вычисляется на лету через `@property` на модели (без миграции БД).

**Файлы:**

| Файл | Изменение |
|------|-----------|
| `backend/app/utils/mastery_decay.py` | Новый — утилиты `calculate_effective_score()`, `get_effective_status()`, `needs_review()` |
| `backend/app/models/mastery.py` | `@property`: `effective_score`, `effective_status`, `needs_review` на ParagraphMastery |
| `backend/app/schemas/mastery.py` | Поля `effective_score`, `effective_status`, `needs_review` в ParagraphMasteryResponse |
| `backend/app/api/v1/students/learning.py` | Прогресс-сводка считает mastered/struggling по `effective_status` |
| `backend/app/services/student_content_service.py` | Список параграфов возвращает effective-поля |
| `backend/app/services/homework/ai/personalization_service.py` | Персонализация ДЗ по `effective_status` |
| `backend/app/services/lesson_plan_service.py` | План урока A/B/C по `effective_status` |

**Ключевые решения:**
- `best_score` не изменяется (исторический факт)
- `status` в БД фиксируется на момент теста (для SQL-аналитики учителя)
- Все student-facing данные используют effective-значения
- Миграция БД не требуется — всё вычисляется на лету

---

## 4. Блок 2: Spaced Repetition (интервальное повторение) — ВЫПОЛНЕНО

### Приоритет: ОЧЕНЬ ВЫСОКИЙ | Сложность: СРЕДНЯЯ | Статус: ВЫПОЛНЕНО

### Суть

После достижения "mastered" система планирует короткие проверки (3-5 вопросов) через увеличивающиеся интервалы. Это один из самых доказанных методов в когнитивной психологии (Leitner system, SM-2 algorithm).

### Алгоритм интервалов

```python
INTERVALS = {
    0: 1,     # первая проверка через 1 день
    1: 3,     # если прошёл — через 3 дня
    2: 7,     # через 7 дней
    3: 14,    # через 14 дней
    4: 30,    # через 30 дней
    5: 60,    # через 60 дней
    6: 120,   # через 120 дней (максимум)
}

def calculate_next_review(streak: int, passed: bool) -> tuple[int, int]:
    """
    Возвращает (новый streak, интервал в днях).

    При провале — откат на 2 уровня (но не ниже 0).
    При успехе — продвижение на 1 уровень.
    """
    if passed:
        new_streak = min(streak + 1, 6)
    else:
        new_streak = max(streak - 2, 0)

    interval = INTERVALS[new_streak]
    return new_streak, interval
```

### Новая таблица

```sql
CREATE TABLE review_schedule (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id),
    school_id INTEGER NOT NULL,

    -- Интервальное повторение
    streak INTEGER DEFAULT 0,              -- текущий уровень в Leitner system
    next_review_date DATE NOT NULL,        -- когда нужна проверка
    last_review_date TIMESTAMP,            -- когда последний раз проверяли

    -- Статистика
    total_reviews INTEGER DEFAULT 0,       -- всего проверок
    successful_reviews INTEGER DEFAULT 0,  -- успешных проверок

    -- Статус
    is_active BOOLEAN DEFAULT TRUE,        -- FALSE если ученик ещё не mastered

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(student_id, paragraph_id)
);
```

### Поток данных

```
Ученик достигает "mastered" на параграфе
    ↓
Создаётся запись в review_schedule:
    streak = 0, next_review_date = завтра
    ↓
На главном экране ученика: "5 тем требуют повторения"
    ↓
Ученик проходит мини-тест (3-5 вопросов)
    ↓
Если результат ≥ 80%:
    streak += 1, next_review = через INTERVALS[streak] дней
    ↓
Если результат < 80%:
    streak = max(streak - 2, 0), next_review = через INTERVALS[streak] дней
    effective_score пересчитывается
```

### Мини-тест (Review Quiz)

- 3-5 случайных вопросов из банка вопросов параграфа
- Время: 2-3 минуты (не полноценный тест)
- Тип теста: `REVIEW` (новый тип, не влияет на best_score)
- Влияет на: `effective_score` и `review_schedule`

### UI для ученика

```
┌─────────────────────────────────────────┐
│  📋 Повторение (3 темы на сегодня)      │
│                                         │
│  ● §5. Квадратные уравнения    [2 мин]  │
│  ● §8. Неравенства             [2 мин]  │
│  ● §12. Системы уравнений      [3 мин]  │
│                                         │
│  Завтра: 1 тема  |  На этой неделе: 5   │
└─────────────────────────────────────────┘
```

### Реализация (выполнено)

**Подход:** Leitner system с 7 уровнями интервалов (1, 3, 7, 14, 30, 60, 120 дней). Таблица `review_schedule` хранит расписание. При достижении "mastered" автоматически создаётся запись. Успешный review (≥80%) обновляет `last_updated_at` в `paragraph_mastery`, сбрасывая time decay.

**Файлы:**

| Файл | Изменение |
|------|-----------|
| `backend/app/models/review_schedule.py` | Новый — ORM модель ReviewSchedule (student, paragraph, streak, next_review_date) |
| `backend/app/repositories/review_schedule_repo.py` | Новый — CRUD: get_due_reviews, get_upcoming_count, get_stats |
| `backend/app/services/spaced_repetition_service.py` | Новый — activate_review(), process_review_result(), deactivate_review() |
| `backend/app/schemas/review_schedule.py` | Новый — DueReviewsResponse, ReviewResultRequest/Response, ReviewStatsResponse |
| `backend/app/api/v1/students/reviews.py` | Новый — GET /reviews/due, POST /reviews/{id}/complete, GET /reviews/stats |
| `backend/alembic/versions/044_review_schedule.py` | Новый — миграция таблицы с RLS и индексами |
| `backend/app/services/mastery_service.py` | Хук: при status=="mastered" → activate_review() |
| `backend/app/models/__init__.py` | Регистрация ReviewSchedule |
| `backend/app/api/v1/students/__init__.py` | Подключение reviews router |

**Ключевые решения:**
- При успешном review (≥80%): streak+1, обновляется `last_updated_at` → decay сбрасывается
- При неудачном review (<80%): streak-2 (min 0), `last_updated_at` не обновляется → decay продолжается
- Review не влияет на `best_score` — только на расписание и time decay
- Автоматическая активация при достижении mastered через хук в mastery_service
- Partial index `idx_review_schedule_due` для быстрого поиска активных reviews

**API эндпоинты:**
- `GET /api/v1/students/reviews/due` — параграфы для повторения сегодня
- `POST /api/v1/students/reviews/{paragraph_id}/complete` — отправить результат
- `GET /api/v1/students/reviews/stats` — статистика повторений

---

## 5. Блок 3: Паттерны самооценки (Metacognitive Coaching)

### Приоритет: СРЕДНИЙ | Сложность: НИЗКАЯ

### Суть

Анализировать историю самооценок ученика и выявлять устойчивые паттерны. Давать ученику и учителю обратную связь о метакогнитивных навыках.

### Паттерны для детекции

```python
def detect_metacognitive_pattern(
    assessments: list[SelfAssessment],
    test_scores: list[float]
) -> str | None:
    """
    Анализирует последние 5+ самооценок и соответствующие тесты.
    """
    last_5 = assessments[-5:]
    avg_score = mean(test_scores[-5:])

    understood_count = sum(1 for a in last_5 if a.rating == "understood")
    difficult_count = sum(1 for a in last_5 if a.rating == "difficult")

    # Паттерн 1: Хронический переоценщик (Dunning-Kruger)
    if understood_count >= 4 and avg_score < 0.60:
        return "overconfident"

    # Паттерн 2: Хронический недооценщик (Impostor Syndrome)
    if difficult_count >= 4 and avg_score > 0.80:
        return "underconfident"

    # Паттерн 3: Точная самооценка (хороший метакогнитивный навык)
    alignment = calculate_alignment(assessments, test_scores)
    if alignment > 0.8:
        return "well_calibrated"

    return None
```

### Реакция системы на паттерны

**Переоценщик (overconfident):**
- Уведомление учителю: "Ученик X систематически переоценивает свои знания (самооценка: understood, средний балл: 45%)"
- Сообщение ученику: "Ты часто оцениваешь себя выше результатов тестов. Попробуй перед самооценкой ответить на контрольный вопрос."
- Рекомендация: обязательный practice test перед самооценкой

**Недооценщик (underconfident):**
- Сообщение ученику: "Ты знаешь больше, чем думаешь! Твои результаты тестов стабильно выше 80%. Доверяй себе."
- Учителю: позитивный сигнал, ученик перфекционист

**Точная калибровка (well_calibrated):**
- Бейдж/достижение: "Мастер самоанализа"
- Учителю: ученик хорошо понимает свой уровень

### Хранение

```sql
-- Новые поля в student_paragraphs или отдельная таблица
ALTER TABLE students ADD COLUMN metacognitive_pattern VARCHAR(20) DEFAULT NULL;
ALTER TABLE students ADD COLUMN metacognitive_updated_at TIMESTAMP DEFAULT NULL;
```

Пересчитывается после каждой самооценки, если накоплено ≥ 5 записей.

---

## 6. Блок 4: Provisional статус для новых учеников

### Приоритет: СРЕДНИЙ | Сложность: НИЗКАЯ

### Проблема

Текущий алгоритм: если < 3 попыток → автоматически группа C. Это значит, что новый ученик, сдавший первые 2 теста на 95%, всё равно в группе C и получает упрощённый контент.

### Решение

```python
def determine_chapter_level(attempts: list, weighted_avg: float, trend: float, std_dev: float) -> tuple[str, bool]:
    """
    Возвращает (level, is_provisional).
    """
    if len(attempts) < 3:
        # Provisional: оцениваем по имеющимся данным, но помечаем как предварительный
        avg = mean([a.score for a in attempts]) * 100
        if avg >= 85:
            return ('B', True)   # не A (недостаточно данных), но и не C
        elif avg >= 60:
            return ('B', True)
        else:
            return ('C', True)

    # Обычная логика для ≥ 3 попыток
    provisional = False
    if weighted_avg >= 85 and (trend >= 0 or std_dev < 10):
        return ('A', provisional)
    elif weighted_avg < 60 or (weighted_avg < 70 and trend < -10):
        return ('C', provisional)
    else:
        return ('B', provisional)
```

### Изменения в БД

```sql
ALTER TABLE chapter_mastery ADD COLUMN is_provisional BOOLEAN DEFAULT FALSE;
```

### UI-индикация

Provisional статус показывается с пометкой: "Предварительная оценка (нужно ещё N тестов для точного определения)".

---

## 7. Блок 5: Knowledge Graph (граф зависимостей)

### Приоритет: ВЫСОКИЙ | Сложность: ВЫСОКАЯ

### Суть

Параграфы имеют **зависимости**: нельзя понять квадратные уравнения, не зная линейных. Сейчас система не учитывает эту связь.

### Модель данных

```sql
CREATE TABLE paragraph_prerequisites (
    id SERIAL PRIMARY KEY,
    paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id),
    prerequisite_paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id),
    strength VARCHAR(10) DEFAULT 'required',  -- 'required' | 'recommended'
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(paragraph_id, prerequisite_paragraph_id),
    CHECK(paragraph_id != prerequisite_paragraph_id)
);

-- Пример: §15 "Квадратные уравнения" требует §8 "Линейные уравнения"
INSERT INTO paragraph_prerequisites (paragraph_id, prerequisite_paragraph_id, strength)
VALUES (15, 8, 'required');
```

### Логика проверки

```python
async def check_prerequisites(student_id: int, paragraph_id: int) -> list[dict]:
    """
    Проверяет готовность ученика к параграфу.
    Возвращает список проблемных prerequisites.
    """
    prerequisites = await get_prerequisites(paragraph_id)
    warnings = []

    for prereq in prerequisites:
        mastery = await get_paragraph_mastery(student_id, prereq.prerequisite_paragraph_id)

        if mastery is None or mastery.effective_score < 0.60:
            warnings.append({
                "paragraph_id": prereq.prerequisite_paragraph_id,
                "paragraph_title": prereq.title,
                "current_score": mastery.effective_score if mastery else 0,
                "strength": prereq.strength,
                "recommendation": "review_first" if prereq.strength == "required" else "consider_review"
            })

    return warnings
```

### Что это даёт

1. **Ученику:** предупреждение перед началом новой темы: "Рекомендуем сначала повторить §8 — твой уровень 45%"
2. **Учителю:** аналитика: "У 12 учеников проблема не в §15, а в §8, на котором §15 построен"
3. **Системе:** более точные рекомендации, адаптивные маршруты обучения

### Заполнение данных

- Начать с математики (алгебра) — там зависимости наиболее явные и линейные
- Можно заполнять постепенно, предмет за предметом
- В будущем: автоматическое определение зависимостей через анализ корреляций результатов тестов

---

## 8. Блок 6: Confidence-Weighted Mastery (BKT)

### Приоритет: СРЕДНИЙ | Сложность: СРЕДНЯЯ

### Суть

Сейчас 1 попытка на 90% и 10 попыток на 90% дают одинаковый статус "mastered". Но **достоверность** этих результатов разная. Bayesian Knowledge Tracing (BKT) — стандартный подход в адаптивных системах для учёта неопределённости.

### Упрощённая модель

```python
import math

def calculate_confidence(attempts_count: int) -> float:
    """
    Уровень уверенности системы в оценке знаний.

    attempts:  1 → 0.00 (не уверены)
    attempts:  2 → 0.29
    attempts:  4 → 0.50
    attempts:  9 → 0.67
    attempts: 16 → 0.75
    attempts: 25 → 0.80
    """
    if attempts_count <= 1:
        return 0.0
    return 1 - (1 / math.sqrt(attempts_count))


def calculate_display_mastery(
    effective_score: float,
    attempts_count: int,
    prior: float = 0.5  # начальное предположение — "не знает"
) -> float:
    """
    Взвешенное мастерство с учётом уверенности.

    При 1 попытке: сильное влияние prior (0.5), балл ближе к 50%
    При 10+ попытках: prior почти не влияет, балл ≈ effective_score
    """
    confidence = calculate_confidence(attempts_count)
    return effective_score * confidence + prior * (1 - confidence)
```

### Примеры

```
1 попытка на 90%:   display = 90% * 0.0 + 50% * 1.0 = 50% → progressing
4 попытки на 90%:   display = 90% * 0.5 + 50% * 0.5 = 70% → progressing
9 попыток на 90%:   display = 90% * 0.67 + 50% * 0.33 = 77% → progressing
16 попыток на 90%:  display = 90% * 0.75 + 50% * 0.25 = 80% → progressing
25 попыток на 90%:  display = 90% * 0.80 + 50% * 0.20 = 82% → progressing
```

### Важно

Этот подход консервативен — требуется больше попыток для достижения "mastered". Это может быть как плюсом (точнее), так и минусом (демотивирует). Рекомендуется тестировать на пилотной группе.

### Альтернативный подход (менее агрессивный)

```python
# Использовать confidence только как индикатор, не для расчёта статуса
class MasteryDisplay:
    score: float          # effective_score
    status: str           # на основе effective_score
    confidence: str       # "low" | "medium" | "high"
    confidence_hint: str  # "Пройди ещё 2 теста для точной оценки"
```

---

## 9. Блок 7: Difficulty-Weighted Scoring (Bloom's Taxonomy)

### Приоритет: НИЗКИЙ | Сложность: СРЕДНЯЯ

### Суть

Сейчас все вопросы теста равноценны. Вопрос "Назови год события" (запоминание) и "Примени формулу к нестандартной задаче" (применение) дают одинаковый вклад в балл. Это не отражает глубину понимания.

### Уровни Bloom's Taxonomy

```python
BLOOM_LEVELS = {
    "remember": {"weight": 1.0, "label": "Запоминание"},
    "understand": {"weight": 1.2, "label": "Понимание"},
    "apply": {"weight": 1.5, "label": "Применение"},
    "analyze": {"weight": 1.8, "label": "Анализ"},
    "evaluate": {"weight": 2.0, "label": "Оценка"},
    "create": {"weight": 2.5, "label": "Создание"},
}
```

### Изменения в модели вопросов

```sql
ALTER TABLE exercises ADD COLUMN bloom_level VARCHAR(20) DEFAULT 'remember';
```

### Взвешенный расчёт балла

```python
def calculate_weighted_test_score(answers: list[dict]) -> float:
    """
    Вместо простого: correct / total
    Используем: sum(weight * correct) / sum(weight)
    """
    total_weight = 0
    earned_weight = 0

    for answer in answers:
        weight = BLOOM_LEVELS[answer["bloom_level"]]["weight"]
        total_weight += weight
        if answer["is_correct"]:
            earned_weight += weight

    return earned_weight / total_weight if total_weight > 0 else 0
```

### Что это даёт

- Ученик, решивший сложные задачи на "apply" и "analyze", получает более высокий балл
- Ученик, заучивший факты, но не умеющий применять — получает ниже
- Более точная дифференциация между поверхностным и глубоким пониманием

### Ограничения

- Требует разметки всех вопросов по Bloom's taxonomy
- Большой объём ручной работы при заполнении
- Можно внедрять постепенно: начать с новых вопросов, старые оставить как "remember"

---

## 10. Дорожная карта внедрения

### Фаза 1: Фундамент (1-2 недели)

| Блок | Сложность | Ценность | Зависимости |
|------|-----------|----------|-------------|
| **Time Decay** | Низкая | Высокая | Нет |
| **Provisional статус** | Низкая | Средняя | Нет |

**Time Decay** решает главную проблему: система перестаёт показывать ложный прогресс. Это минимальные изменения в `mastery_service.py` — добавить расчёт `effective_score` и использовать его для определения статуса.

**Provisional** — быстрый fix для новых учеников. Одно условие в `determine_mastery_level()`.

### Фаза 2: Повторение (2-4 недели)

| Блок | Сложность | Ценность | Зависимости |
|------|-----------|----------|-------------|
| **Spaced Repetition** | Средняя | Очень высокая | Time Decay |

Это самый ценный блок. Требует:
- Новая таблица `review_schedule`
- Новый тип теста `REVIEW` (мини-тест на 3-5 вопросов)
- UI-компонент "Темы для повторения" на главном экране
- Cron-job для уведомлений

### Фаза 3: Метакогнитика (1-2 недели)

| Блок | Сложность | Ценность | Зависимости |
|------|-----------|----------|-------------|
| **Паттерны самооценки** | Низкая | Средняя | Нет |

Аналитическая надстройка над существующими данными `paragraph_self_assessments`. Не требует изменений в основном flow — только новый сервис анализа и UI для учителя/ученика.

### Фаза 4: Адаптивность (4-6 недель)

| Блок | Сложность | Ценность | Зависимости |
|------|-----------|----------|-------------|
| **Knowledge Graph** | Высокая | Высокая | Нет |
| **Confidence-Weighted (BKT)** | Средняя | Средняя | Time Decay |

Knowledge Graph требует:
- Новая таблица `paragraph_prerequisites`
- Заполнение данных (начать с алгебры)
- Логика проверки перед началом параграфа
- UI-предупреждения

BKT — дополнительная точность для опытных пользователей. Рекомендуется A/B-тестирование.

### Фаза 5: Глубина (2-4 недели)

| Блок | Сложность | Ценность | Зависимости |
|------|-----------|----------|-------------|
| **Bloom's Taxonomy** | Средняя | Средняя | Разметка вопросов |

Внедрять после накопления достаточного количества размеченных вопросов. Можно начать с новых учебников, постепенно размечая старые.

---

## Сводная таблица

| # | Блок | Приоритет | Сложность | Ценность | Фаза | Статус |
|---|------|-----------|-----------|----------|------|--------|
| 1 | Time Decay | Высокий | Низкая | Высокая | 1 | **ВЫПОЛНЕНО** |
| 2 | Spaced Repetition | Очень высокий | Средняя | Очень высокая | 2 | **ВЫПОЛНЕНО** |
| 3 | Паттерны самооценки | Средний | Низкая | Средняя | 3 | — |
| 4 | Provisional статус | Средний | Низкая | Средняя | 1 | — |
| 5 | Knowledge Graph | Высокий | Высокая | Высокая | 4 | — |
| 6 | Confidence-Weighted (BKT) | Средний | Средняя | Средняя | 4 | — |
| 7 | Bloom's Taxonomy | Низкий | Средняя | Средняя | 5 | — |
