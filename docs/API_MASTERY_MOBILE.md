# Mastery System — API для мобильного приложения

Документ для мобильного разработчика. Описывает как работает система мастерства, все API эндпоинты и задачи для реализации.

**Base URL:** `https://api.ai-mentor.kz/api/v1/students`
**Авторизация:** JWT токен в `Authorization: Bearer <token>` (роль STUDENT)
**Формат:** JSON. Даты в ISO 8601. Пагинация offset-based (`page`, `page_size`).

---

## Содержание

1. [Как работает мастерство](#1-как-работает-мастерство)
2. [API: Контент и навигация](#2-api-контент-и-навигация)
3. [API: Прогресс и шаги обучения](#3-api-прогресс-и-шаги-обучения)
4. [API: Тесты и оценивание](#4-api-тесты-и-оценивание)
5. [API: Самооценка](#5-api-самооценка)
6. [API: Mastery Levels (A/B/C)](#6-api-mastery-levels-abc)
7. [API: Spaced Repetition (повторение)](#7-api-spaced-repetition-повторение)
8. [API: Prerequisites (граф зависимостей)](#8-api-prerequisites-граф-зависимостей)
9. [API: Metacognitive Coaching](#9-api-metacognitive-coaching)
10. [Задачи для мобильной разработки](#10-задачи-для-мобильной-разработки)

---

## 1. Как работает мастерство

### Два вида мастерства (не объединяются!)

| Тип | Источник | Таблица | Шкала |
|-----|----------|---------|-------|
| **Объективный** | Результаты тестов | `paragraph_mastery` | 0.0–1.0, статусы: struggling / progressing / mastered |
| **Субъективный** | Самооценка ученика | `paragraph_self_assessments` | understood / questions / difficult, impact ±5.0 |

Расхождение между ними — ценный метакогнитивный сигнал ("думает что понял, но тесты говорят обратное").

### Time Decay (временное затухание)

Знания забываются без повторения. Система учитывает это:

- `best_score` — исторический максимум, **никогда не снижается**
- `effective_score` — балл с учётом затухания, **снижается со временем**
- `effective_status` — статус на основе `effective_score` (struggling/progressing/mastered)
- `needs_review` — `true` если mastered параграф затух более чем на 15%

```
Формула: effective_score = best_score × e^(-0.002 × дней_с_последнего_теста)

Пример (best_score = 0.90):
  Через 30 дней:  effective = 0.85 → mastered (ещё ОК)
  Через 90 дней:  effective = 0.75 → progressing (пора повторить)
  Через 180 дней: effective = 0.63 → progressing (нужно повторение)
  Через 365 дней: effective = 0.43 → struggling (критично)
```

**Важно для мобильного:** `effective_score` и `effective_status` вычисляются на сервере. Клиент **не должен** пересчитывать decay — просто отображает серверные значения.

### A/B/C Уровни (по главам)

| Уровень | Условие | Описание |
|---------|---------|----------|
| **A** | mastery_score ≥ 85, тренд ≥ 0 | Отличное владение |
| **B** | mastery_score 60–84 | Хорошее, есть куда расти |
| **C** | mastery_score < 60 | Нужна помощь |

**Provisional (предварительная оценка):** если < 3 попыток тестов, `is_provisional = true`. Никогда не ставится A (недостаточно данных).

### Spaced Repetition (интервальное повторение)

При достижении "mastered" система планирует мини-тесты через увеличивающиеся интервалы (Leitner system):

```
Streak 0 → через 1 день
Streak 1 → через 3 дня
Streak 2 → через 7 дней
Streak 3 → через 14 дней
Streak 4 → через 30 дней
Streak 5 → через 60 дней
Streak 6 → через 120 дней (максимум)
```

- Успешный review (≥ 80%): streak + 1, интервал растёт
- Неудачный review (< 80%): streak - 2 (min 0), интервал сокращается

### Prerequisites (граф зависимостей)

Параграфы имеют зависимости. Например, "Квадратные уравнения" требует знания "Линейных уравнений".

- `required` — блокирующий: `can_proceed = false` если effective_score < 0.60
- `recommended` — предупреждение: `can_proceed = true`, но показывается warning

---

## 2. API: Контент и навигация

### GET `/textbooks`

Список доступных учебников с прогрессом ученика.

**Query:** `page=1`, `page_size=20`, `subject_id` (опционально)

**Response:**
```json
{
  "items": [
    {
      "id": 24,
      "title": "Алгебра 7 класс",
      "subject_id": 1,
      "subject_name": "Математика",
      "grade_level": 7,
      "language": "ru",
      "cover_image_url": "/uploads/textbook-covers/24.jpg",
      "chapters_count": 8,
      "paragraphs_count": 57,
      "mastery_level": "B",
      "last_activity": "2025-03-01T10:00:00Z",
      "progress": {
        "chapters_total": 8,
        "chapters_completed": 3,
        "paragraphs_total": 57,
        "paragraphs_completed": 21,
        "percentage": 37
      }
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

### GET `/textbooks/{textbook_id}/chapters`

Главы учебника с mastery-уровнями.

**Response:**
```json
{
  "items": [
    {
      "id": 101,
      "title": "Глава 1. Линейные уравнения",
      "order": 1,
      "paragraphs_count": 8,
      "mastery_level": "A",
      "mastery_score": 92.5,
      "has_summative_test": true,
      "summative_passed": true,
      "progress": {
        "total": 8,
        "completed": 8,
        "percentage": 100
      }
    }
  ],
  "total": 8,
  "page": 1,
  "page_size": 20
}
```

### GET `/chapters/{chapter_id}/paragraphs`

Параграфы главы со статусами.

**Response:**
```json
{
  "items": [
    {
      "id": 501,
      "number": 1,
      "title": "§1. Линейные уравнения с одной переменной",
      "order": 1,
      "status": "completed",
      "has_practice": true,
      "practice_score": 0.85,
      "has_audio": true,
      "has_video": false,
      "prerequisite_warnings": [
        {
          "paragraph_id": 480,
          "paragraph_title": "§5. Дроби",
          "strength": "recommended",
          "current_score": 0.55
        }
      ]
    }
  ],
  "total": 8,
  "page": 1,
  "page_size": 50
}
```

**Поле `status`:** `not_started` | `in_progress` | `completed`

**Поле `prerequisite_warnings`:** массив, может быть пустым. Приходит при наличии unmet prerequisites.

### GET `/paragraphs/{paragraph_id}`

Полный контент параграфа.

**Response:**
```json
{
  "id": 501,
  "number": 1,
  "title": "§1. Линейные уравнения с одной переменной",
  "content": "<p>Текст параграфа в HTML...</p>",
  "content_language": "ru",
  "status": "in_progress",
  "has_practice": true,
  "has_audio": true,
  "has_video": false,
  "has_slides": false,
  "has_cards": true,
  "images": [
    { "id": 1, "url": "/uploads/textbook-images/24/img1.png", "order": 1 }
  ]
}
```

**Side effect:** обновляет `last_accessed_at` ученика.

### GET `/paragraphs/{paragraph_id}/content`

Rich-контент параграфа (аудио, видео, слайды, карточки).

**Query:** `language=ru` (или `kk`)

**Response:**
```json
{
  "paragraph_id": 501,
  "language": "ru",
  "explain_text": "Упрощённое объяснение для ученика...",
  "audio_url": "/uploads/audio/501_ru.mp3",
  "video_url": null,
  "slides_url": null,
  "cards": [
    { "front": "Что такое линейное уравнение?", "back": "Уравнение вида ax + b = 0" }
  ],
  "has_explain": true,
  "has_audio": true,
  "has_video": false,
  "has_slides": false,
  "has_cards": true
}
```

### GET `/paragraphs/{paragraph_id}/navigation`

Контекст навигации (предыдущий/следующий параграф).

**Response:**
```json
{
  "current_paragraph_id": 501,
  "current_number": 1,
  "current_title": "§1. Линейные уравнения",
  "chapter_id": 101,
  "chapter_title": "Глава 1",
  "textbook_id": 24,
  "textbook_title": "Алгебра 7",
  "previous_paragraph_id": null,
  "next_paragraph_id": 502,
  "total_paragraphs_in_chapter": 8,
  "current_position_in_chapter": 1
}
```

---

## 3. API: Прогресс и шаги обучения

### GET `/paragraphs/{paragraph_id}/progress`

Прогресс ученика по параграфу (текущий шаг, время, встроенные вопросы).

**Response:**
```json
{
  "paragraph_id": 501,
  "is_completed": false,
  "current_step": "content",
  "time_spent": 320,
  "last_accessed_at": "2025-03-01T10:30:00Z",
  "completed_at": null,
  "self_assessment": null,
  "self_assessment_at": null,
  "available_steps": ["intro", "content", "practice", "summary"],
  "embedded_questions_total": 3,
  "embedded_questions_answered": 1,
  "embedded_questions_correct": 1
}
```

**Шаги обучения:**
1. `intro` — введение
2. `content` — основной контент
3. `practice` — практика (тест)
4. `summary` — итоги (самооценка)
5. `completed` — завершён

### POST `/paragraphs/{paragraph_id}/progress`

Обновить шаг прогресса.

**Request:**
```json
{
  "step": "practice",
  "time_spent": 60
}
```

**Валидация:** `step` — одно из: `intro`, `content`, `practice`, `summary`, `completed`. `time_spent` — 0–3600 секунд.

**Response:**
```json
{
  "paragraph_id": 501,
  "current_step": "practice",
  "is_completed": false,
  "time_spent": 380,
  "available_steps": ["intro", "content", "practice", "summary"],
  "self_assessment": null
}
```

### GET `/progress`

Сводка прогресса по параграфам (по главе или общий).

**Query:** `chapter_id=101` (опционально)

**Response:**
```json
{
  "chapter_id": 101,
  "chapter_name": "Глава 1. Линейные уравнения",
  "total_paragraphs": 8,
  "completed_paragraphs": 5,
  "mastered_paragraphs": 3,
  "struggling_paragraphs": 1,
  "average_score": 0.72,
  "best_score": 0.95,
  "total_attempts": 12,
  "paragraphs": [
    {
      "paragraph_id": 501,
      "paragraph_title": "§1. Линейные уравнения с одной переменной",
      "paragraph_number": 1,
      "status": "mastered",
      "effective_score": 0.88,
      "best_score": 0.95,
      "average_score": 0.82,
      "is_completed": true,
      "attempts_count": 3,
      "time_spent": 1200,
      "needs_review": false
    }
  ]
}
```

**Важно:** `status` здесь — это `effective_status` (с decay), а не исторический.

---

## 4. API: Тесты и оценивание

### GET `/paragraphs/{paragraph_id}/tests`

Доступные тесты по параграфу.

**Response:**
```json
{
  "items": [
    {
      "id": 201,
      "title": "Тест по §1",
      "test_type": "FORMATIVE",
      "questions_count": 5,
      "time_limit": 600,
      "attempts_allowed": 3,
      "best_score": 0.80,
      "attempts_used": 1
    }
  ]
}
```

**Типы тестов:** `FORMATIVE` (по параграфу), `SUMMATIVE` (по главе), `REVIEW` (повторение)

### POST `/tests/{test_id}/start`

Начать тест.

**Response:**
```json
{
  "attempt_id": 3001,
  "test_id": 201,
  "status": "IN_PROGRESS",
  "started_at": "2025-03-01T10:45:00Z",
  "time_limit": 600,
  "questions": [
    {
      "id": 1001,
      "order": 1,
      "question_text": "Решите уравнение: 2x + 5 = 11",
      "question_type": "single_choice",
      "options": [
        { "id": 5001, "text": "x = 2", "order": 1 },
        { "id": 5002, "text": "x = 3", "order": 2 },
        { "id": 5003, "text": "x = 4", "order": 3 },
        { "id": 5004, "text": "x = 5", "order": 4 }
      ]
    }
  ]
}
```

### POST `/attempts/{attempt_id}/answer`

Ответить на вопрос (по одному).

**Request:**
```json
{
  "question_id": 1001,
  "selected_option_ids": [5002]
}
```

**Response:**
```json
{
  "question_id": 1001,
  "is_correct": true,
  "correct_option_ids": [5002],
  "explanation": "2x = 11 - 5 = 6, x = 3",
  "auto_completed": false
}
```

**`auto_completed: true`** — тест автоматически завершён (последний вопрос). Далее обновляется mastery.

### POST `/attempts/{attempt_id}/submit`

Отправить все ответы сразу (bulk submit).

**Request:**
```json
{
  "answers": [
    { "question_id": 1001, "selected_option_ids": [5002] },
    { "question_id": 1002, "selected_option_ids": [5010] }
  ]
}
```

**Response:**
```json
{
  "attempt_id": 3001,
  "status": "COMPLETED",
  "score": 0.80,
  "total_questions": 5,
  "correct_answers": 4,
  "completed_at": "2025-03-01T10:55:00Z",
  "results": [
    {
      "question_id": 1001,
      "is_correct": true,
      "correct_option_ids": [5002],
      "explanation": "..."
    }
  ]
}
```

**Side effects при завершении теста:**
- Обновляется `paragraph_mastery` (test_score, best_score, average_score, attempts_count, status)
- Пересчитывается `effective_score` (decay сбрасывается)
- Обновляется `chapter_mastery` (A/B/C уровень)
- Если достигнут "mastered" → создаётся запись в `review_schedule`

---

## 5. API: Самооценка

### POST `/paragraphs/{paragraph_id}/self-assessment`

Ученик оценивает своё понимание после завершения параграфа.

**Request:**
```json
{
  "rating": "understood",
  "practice_score": 85.0,
  "time_spent": 600
}
```

**`rating`:** `understood` | `questions` | `difficult`
**`practice_score`:** результат practice-теста (0–100), опционально
**`time_spent`:** время в секундах (0–36000), опционально

**Response:**
```json
{
  "id": 4001,
  "paragraph_id": 501,
  "rating": "understood",
  "practice_score": 85.0,
  "mastery_impact": 5.0,
  "next_recommendation": "next_paragraph",
  "created_at": "2025-03-01T11:00:00Z"
}
```

**`mastery_impact`** — влияние на субъективное мастерство:
- `understood` → +5.0 (корректируется вниз если practice_score < 70%)
- `questions` → 0.0
- `difficult` → -5.0 (корректируется вверх если practice_score > 70%)

**`next_recommendation`:**
- `next_paragraph` — переходи к следующей теме
- `review` — повтори материал
- `chat_tutor` — обратись к ИИ-репетитору
- `practice_retry` — попробуй тест ещё раз

**Идемпотентность:** Повторная отправка той же самооценки вернёт тот же результат (для оффлайн-синхронизации).

**Side effect:** Если у ученика >= 5 самооценок, запускается детекция метакогнитивного паттерна.

---

## 6. API: Mastery Levels (A/B/C)

### GET `/mastery/chapter/{chapter_id}`

Mastery-метрики по конкретной главе.

**Response:**
```json
{
  "id": 2001,
  "student_id": 100,
  "chapter_id": 101,
  "total_paragraphs": 8,
  "completed_paragraphs": 5,
  "mastered_paragraphs": 3,
  "struggling_paragraphs": 1,
  "average_score": 0.72,
  "weighted_score": 0.75,
  "summative_score": 0.82,
  "summative_passed": true,
  "mastery_level": "B",
  "mastery_score": 75.5,
  "is_provisional": false,
  "progress_percentage": 62,
  "estimated_completion_date": "2025-04-15",
  "last_updated_at": "2025-03-01T10:00:00Z"
}
```

### GET `/mastery/overview`

Обзор mastery по всем главам (для dashboard).

**Response:**
```json
{
  "student_id": 100,
  "chapters": [
    {
      "id": 2001,
      "student_id": 100,
      "chapter_id": 101,
      "total_paragraphs": 8,
      "completed_paragraphs": 8,
      "mastered_paragraphs": 6,
      "struggling_paragraphs": 0,
      "mastery_level": "A",
      "mastery_score": 92.5,
      "is_provisional": false,
      "progress_percentage": 100,
      "summative_score": 0.90,
      "summative_passed": true,
      "last_updated_at": "2025-02-15T10:00:00Z",
      "chapter_title": "Глава 1. Линейные уравнения",
      "chapter_order": 1
    },
    {
      "id": 2002,
      "student_id": 100,
      "chapter_id": 102,
      "total_paragraphs": 6,
      "completed_paragraphs": 2,
      "mastered_paragraphs": 1,
      "struggling_paragraphs": 0,
      "mastery_level": "B",
      "mastery_score": 68.0,
      "is_provisional": true,
      "progress_percentage": 33,
      "summative_score": null,
      "summative_passed": null,
      "last_updated_at": "2025-03-01T10:00:00Z",
      "chapter_title": "Глава 2. Квадратные уравнения",
      "chapter_order": 2
    }
  ],
  "total_chapters": 8,
  "average_mastery_score": 72.3,
  "level_a_count": 3,
  "level_b_count": 4,
  "level_c_count": 1
}
```

---

## 7. API: Spaced Repetition (повторение)

### GET `/reviews/due`

Параграфы, которые нужно повторить сегодня.

**Response:**
```json
{
  "due_today": [
    {
      "id": 6001,
      "paragraph_id": 501,
      "paragraph_title": "§1. Линейные уравнения",
      "paragraph_number": "1",
      "chapter_title": "Глава 1. Линейные уравнения",
      "textbook_title": "Алгебра 7 класс",
      "streak": 2,
      "next_review_date": "2025-03-09",
      "last_review_date": "2025-03-02T14:00:00Z",
      "total_reviews": 3,
      "successful_reviews": 2,
      "best_score": 0.95,
      "effective_score": 0.88
    },
    {
      "id": 6002,
      "paragraph_id": 505,
      "paragraph_title": "§5. Системы уравнений",
      "paragraph_number": "5",
      "chapter_title": "Глава 1. Линейные уравнения",
      "textbook_title": "Алгебра 7 класс",
      "streak": 0,
      "next_review_date": "2025-03-09",
      "last_review_date": null,
      "total_reviews": 0,
      "successful_reviews": 0,
      "best_score": 0.90,
      "effective_score": 0.72
    }
  ],
  "due_today_count": 2,
  "upcoming_week_count": 5,
  "total_active": 12
}
```

### POST `/reviews/{paragraph_id}/complete`

Отправить результат мини-теста повторения.

**Request:**
```json
{
  "score": 0.85
}
```

**`score`:** 0.0–1.0 — результат review-теста

**Response:**
```json
{
  "paragraph_id": 501,
  "passed": true,
  "score": 0.85,
  "new_streak": 3,
  "next_review_date": "2025-03-23",
  "message": "Отлично! Следующее повторение через 14 дней"
}
```

**Логика:**
- `score >= 0.80` → `passed: true`, streak + 1, интервал растёт, `last_updated_at` в mastery обновляется (decay сбрасывается)
- `score < 0.80` → `passed: false`, streak - 2 (min 0), интервал сокращается, decay **не** сбрасывается

### GET `/reviews/stats`

Статистика повторений ученика.

**Response:**
```json
{
  "total_active_reviews": 12,
  "due_today": 2,
  "due_this_week": 5,
  "total_completed_reviews": 45,
  "success_rate": 0.82,
  "average_streak": 3.2
}
```

---

## 8. API: Prerequisites (граф зависимостей)

### GET `/paragraphs/{paragraph_id}/prerequisites`

Проверить, готов ли ученик к изучению параграфа.

**Response (нет проблем):**
```json
{
  "paragraph_id": 501,
  "has_warnings": false,
  "warnings": [],
  "can_proceed": true
}
```

**Response (есть проблемы):**
```json
{
  "paragraph_id": 520,
  "has_warnings": true,
  "warnings": [
    {
      "paragraph_id": 501,
      "paragraph_title": "§1. Линейные уравнения",
      "paragraph_number": 1,
      "chapter_title": "Глава 1. Линейные уравнения",
      "textbook_title": "Алгебра 7 класс",
      "grade_level": 7,
      "current_score": 0.45,
      "strength": "required",
      "recommendation": "review_first"
    },
    {
      "paragraph_id": 510,
      "paragraph_title": "§10. Неравенства",
      "paragraph_number": 10,
      "chapter_title": "Глава 2",
      "textbook_title": "Алгебра 7 класс",
      "grade_level": 7,
      "current_score": 0.55,
      "strength": "recommended",
      "recommendation": "consider_review"
    }
  ],
  "can_proceed": false
}
```

**Ключевые поля:**
- `can_proceed: false` — есть `required` prerequisite с effective_score < 0.60
- `strength: "required"` — обязательная зависимость (блокирует)
- `strength: "recommended"` — рекомендация (не блокирует)
- `textbook_title` / `grade_level` — зависимость может быть из другого учебника того же предмета

---

## 9. API: Metacognitive Coaching

### GET `/metacognitive`

Метакогнитивный паттерн ученика и coaching-сообщение.

**Query:** `lang=ru` (или `kk`)

**Response (паттерн определён):**
```json
{
  "pattern": "underconfident",
  "message": "Ты знаешь больше, чем думаешь! Твои результаты тестов стабильно выше 80%. Доверяй себе.",
  "updated_at": "2025-03-01T10:00:00Z",
  "recent_assessments": 8,
  "rating_breakdown": {
    "understood": 1,
    "questions": 2,
    "difficult": 5
  }
}
```

**Response (паттерн не определён):**
```json
{
  "pattern": null,
  "message": null,
  "updated_at": null,
  "recent_assessments": 3,
  "rating_breakdown": {
    "understood": 1,
    "questions": 1,
    "difficult": 1
  }
}
```

**Паттерны:**

| Паттерн | Условие | Для ученика |
|---------|---------|-------------|
| `overconfident` | 4+ "understood" из 5, avg effective_score < 60% | "Попробуй контрольный вопрос перед самооценкой" |
| `underconfident` | 4+ "difficult" из 5, avg effective_score > 80% | "Ты знаешь больше, чем думаешь!" |
| `well_calibrated` | 60%+ оценок совпадают с результатами | "Отличная самооценка!" |
| `null` | < 5 оценок или нет чёткого паттерна | Не показывать |

---

## 10. Задачи для мобильной разработки

### Задача M1: Список учебников с прогрессом

**Приоритет: ВЫСОКИЙ | Сложность: НИЗКАЯ**

Экран "Мои учебники" — карточки учебников с прогрессом.

**API:** `GET /textbooks`

**Что показать:**
- Обложка учебника
- Название, предмет, класс
- Прогресс-бар (percentage)
- Бейдж mastery_level (A/B/C) если есть
- "Продолжить" → последний активный учебник

---

### Задача M2: Главы и параграфы

**Приоритет: ВЫСОКИЙ | Сложность: НИЗКАЯ**

**API:** `GET /textbooks/{id}/chapters` → `GET /chapters/{id}/paragraphs`

**Что показать на главах:**
- Бейдж A/B/C с цветом (A=зелёный, B=синий, C=оранжевый)
- Если `is_provisional = true` → пометка "предварительно" / пунктирная рамка / opacity
- Прогресс: "5 из 8 параграфов"
- Если `summative_passed = true` → галочка

**Что показать на параграфах:**
- Статус: иконка (not_started=серый, in_progress=синий, completed=зелёный)
- `practice_score` если есть
- `prerequisite_warnings` → иконка замка (required) или предупреждения (recommended)

---

### Задача M3: Learning Flow (шаги обучения)

**Приоритет: ВЫСОКИЙ | Сложность: СРЕДНЯЯ**

Экран параграфа — пошаговое прохождение: intro → content → practice → summary.

**API:**
1. `GET /paragraphs/{id}` — контент
2. `GET /paragraphs/{id}/progress` — текущий шаг
3. `GET /paragraphs/{id}/content?language=ru` — rich-контент
4. `GET /paragraphs/{id}/navigation` — prev/next
5. `POST /paragraphs/{id}/progress` — обновить шаг

**UI:**
- Stepper/tabs: intro → content → practice → summary
- Контент в HTML (WebView или markdown renderer)
- Аудио-плеер если `has_audio`
- Карточки (flashcards) если `has_cards`
- Встроенные вопросы (embedded questions)
- Навигация prev/next параграф

---

### Задача M4: Тесты

**Приоритет: ВЫСОКИЙ | Сложность: СРЕДНЯЯ**

**API:**
1. `POST /tests/{id}/start` — начать тест
2. `POST /attempts/{id}/answer` — ответить на вопрос (по одному)
3. Или: `POST /attempts/{id}/submit` — отправить все ответы сразу

**UI:**
- Список вопросов (single_choice / multiple_choice)
- Таймер если есть time_limit
- После ответа — показать is_correct + explanation
- Экран результатов: score, правильных/неправильных

---

### Задача M5: Самооценка

**Приоритет: ВЫСОКИЙ | Сложность: НИЗКАЯ**

На шаге "Итоги" (summary) — три кнопки:
- "Понял" (understood) — зелёный
- "Есть вопросы" (questions) — жёлтый
- "Сложно" (difficult) — красный

**API:** `POST /paragraphs/{id}/self-assessment`

**Что показать после отправки:**
- `next_recommendation` → подсказка куда идти дальше
- Навигация к следующему параграфу или повторение

---

### Задача M6: Prerequisites — предупреждение перед параграфом

**Приоритет: ВЫСОКИЙ | Сложность: СРЕДНЯЯ**

Перед открытием параграфа проверить зависимости.

**API:** `GET /paragraphs/{id}/prerequisites`

**UI:**
- Если `can_proceed = false` → блокирующий модал:
  - "Сначала повтори: §1. Линейные уравнения (Алгебра 7)"
  - "Твой уровень: 45% — нужно 60%+"
  - Кнопка "Перейти к §1" + кнопка "Всё равно продолжить"
- Если `can_proceed = true` но `has_warnings = true` → жёлтый баннер сверху (не блокирует):
  - "Рекомендуем повторить §10. Неравенства (55%)"

**Навигация:** по нажатию на prerequisite — перейти к этому параграфу.

---

### Задача M7: Spaced Repetition — секция "Повторение"

**Приоритет: ОЧЕНЬ ВЫСОКИЙ | Сложность: ВЫСОКАЯ**

Самый ценный блок. Без UI spaced repetition не работает.

**API:**
1. `GET /reviews/due` — что повторить сегодня
2. `POST /reviews/{paragraph_id}/complete` — отправить результат
3. `GET /reviews/stats` — статистика

**UI — секция на главном экране:**
```
┌──────────────────────────────────┐
│ 🔄 Повторение  (2 на сегодня)   │
│                                  │
│ §1. Линейные уравнения   [2мин] │
│ Streak: ●●●○○○  (3/6)          │
│                                  │
│ §5. Системы уравнений    [2мин] │
│ Streak: ○○○○○○  (0/6)          │
│                                  │
│ На этой неделе: ещё 3 темы      │
│ [Начать повторение →]           │
└──────────────────────────────────┘
```

**UI — мини-тест (review quiz):**
- 3-5 вопросов из банка вопросов параграфа
- Тип теста: `REVIEW` (не влияет на best_score)
- После завершения — экран результата:
  - Passed (≥80%): "Отлично! Следующее повторение через N дней" 🟢
  - Failed (<80%): "Нужно повторить. Следующая попытка через N дней" 🟡
  - Streak visualization (●●●○○○)

**UI — статистика повторений (профиль/dashboard):**
- Активных тем: 12
- Успешность: 82%
- Средний streak: 3.2

---

### Задача M8: Time Decay индикаторы

**Приоритет: СРЕДНИЙ | Сложность: НИЗКАЯ**

Показать что знания "тускнеют" без повторения.

**Где показать:**
- На списке параграфов: если `needs_review = true` → иконка 🔄 или badge "Повтори"
- На прогресс-баре: использовать `effective_score` вместо `best_score`
- В сводке прогресса (`GET /progress`): считать mastered/struggling по effective-значениям (уже приходит с сервера)

**Визуализация decay:**
- Прогресс-бар с двумя слоями:
  - Фон (тусклый) = `best_score` (что было)
  - Передний (яркий) = `effective_score` (что сейчас)
- Tooltip / подпись: "Лучший результат: 90% → Сейчас: 72%"

---

### Задача M9: Provisional Status

**Приоритет: НИЗКИЙ | Сложность: ОЧЕНЬ НИЗКАЯ**

На бейджах A/B/C показать пометку если `is_provisional = true`.

**UI:** Пунктирная рамка + подпись "предварительно" или звёздочка `B*`.

---

### Задача M10: Metacognitive Coaching

**Приоритет: НИЗКИЙ | Сложность: НИЗКАЯ**

**API:** `GET /metacognitive?lang=ru`

**Где показать:**
- После самооценки (на CompletionScreen) — coaching-сообщение
- В профиле — карточка "Навык самооценки" с иконкой паттерна

**Не показывать** если `pattern = null` (< 5 оценок).

---

### Порядок реализации

| Этап | Задача | Описание | Зависимости |
|------|--------|----------|-------------|
| 1 | **M1–M5** | Базовый learning flow | Нет (основной функционал) |
| 2 | **M7** | Spaced Repetition | M4 (тесты) |
| 3 | **M6** | Prerequisites | M2 (параграфы) |
| 4 | **M8** | Time Decay индикаторы | M2 (параграфы) |
| 5 | **M9** | Provisional status | M2 (главы) |
| 6 | **M10** | Metacognitive | M5 (самооценка) |

---

## Справка: Полный список Student API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/textbooks` | Список учебников с прогрессом |
| GET | `/textbooks/{id}/chapters` | Главы учебника |
| GET | `/chapters/{id}/paragraphs` | Параграфы главы |
| GET | `/paragraphs/{id}` | Контент параграфа |
| GET | `/paragraphs/{id}/content` | Rich-контент (аудио, видео, карточки) |
| GET | `/paragraphs/{id}/navigation` | Навигация prev/next |
| GET | `/paragraphs/{id}/progress` | Прогресс по параграфу |
| POST | `/paragraphs/{id}/progress` | Обновить шаг |
| POST | `/paragraphs/{id}/self-assessment` | Самооценка |
| GET | `/paragraphs/{id}/prerequisites` | Проверка prerequisites |
| GET | `/paragraphs/{id}/tests` | Тесты параграфа |
| POST | `/tests/{id}/start` | Начать тест |
| POST | `/attempts/{id}/answer` | Ответить на вопрос |
| POST | `/attempts/{id}/submit` | Отправить все ответы |
| GET | `/mastery/chapter/{id}` | Mastery по главе |
| GET | `/mastery/overview` | Обзор A/B/C по всем главам |
| GET | `/progress` | Сводка прогресса |
| GET | `/reviews/due` | Параграфы для повторения |
| POST | `/reviews/{paragraph_id}/complete` | Результат повторения |
| GET | `/reviews/stats` | Статистика повторений |
| GET | `/metacognitive` | Метакогнитивный паттерн |
