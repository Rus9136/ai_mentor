# API: Самооценка ученика (Self-Assessment)

Документация для мобильных разработчиков.

**Base URL:** `https://api.ai-mentor.kz/api/v1/students`
**Авторизация:** `Authorization: Bearer <access_token>` (роль: `student`)

---

## Обзор

После изучения параграфа (шаг "Итоги") ученик выбирает самооценку. Сервер сохраняет оценку, рассчитывает влияние на mastery и возвращает рекомендацию следующего действия.

### Learning Flow

```
Введение → Материал → Практика → Итоги → [Самооценка] → Завершить
 (intro)   (content)  (practice)  (summary)                (completed)
```

На шаге **Итоги** ученик видит три кнопки:

| Кнопка (UI) | Значение API | Описание |
|-------------|-------------|----------|
| "Всё понял" | `understood` | Ученик уверен, что усвоил материал |
| "Есть вопросы" | `questions` | Частично понял, есть неясности |
| "Нужна помощь" | `difficult` | Не понял тему |

---

## Эндпоинты

### 1. POST /paragraphs/{paragraph_id}/self-assessment

Отправить самооценку за параграф.

#### Request

```
POST /api/v1/students/paragraphs/{paragraph_id}/self-assessment
Authorization: Bearer <token>
Content-Type: application/json
```

**Path Parameters:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `paragraph_id` | `int` | ID параграфа |

**Body:**

| Поле | Тип | Обязательное | Описание |
|------|-----|:---:|----------|
| `rating` | `string` | да | Одно из: `understood`, `questions`, `difficult` |
| `practice_score` | `float \| null` | нет | Процент за практику (0.0–100.0). `null` если практики не было |
| `time_spent` | `int \| null` | нет | Время на параграф в секундах (0–36000) |

**Минимальный запрос:**
```json
{
  "rating": "understood"
}
```

**Полный запрос (с практикой):**
```json
{
  "rating": "understood",
  "practice_score": 85.0,
  "time_spent": 420
}
```

#### Response (200 OK)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | `int` | ID записи самооценки |
| `paragraph_id` | `int` | ID параграфа |
| `rating` | `string` | Сохранённая оценка |
| `practice_score` | `float \| null` | Переданный practice_score (или `null`) |
| `mastery_impact` | `float` | Влияние на mastery (может быть отрицательным) |
| `next_recommendation` | `string` | Рекомендация следующего действия (см. таблицу ниже) |
| `created_at` | `string (ISO 8601)` | Время создания записи |

**Пример ответа:**
```json
{
  "id": 123,
  "paragraph_id": 280,
  "rating": "understood",
  "practice_score": 85.0,
  "mastery_impact": 5.0,
  "next_recommendation": "next_paragraph",
  "created_at": "2026-02-11T14:40:00.955893Z"
}
```

#### Ошибки

| Код | Описание |
|-----|----------|
| `400` | Невалидный `rating` (не understood/questions/difficult) |
| `401` | Не авторизован или токен истёк |
| `403` | Параграф недоступен этому ученику |
| `404` | Параграф не найден |
| `422` | Ошибка валидации (practice_score вне диапазона и т.д.) |

---

### 2. GET /paragraphs/{paragraph_id}/progress

Получить прогресс ученика по параграфу. Включает текущую самооценку.

#### Request

```
GET /api/v1/students/paragraphs/{paragraph_id}/progress
Authorization: Bearer <token>
```

#### Response (200 OK)

| Поле | Тип | Описание |
|------|-----|----------|
| `paragraph_id` | `int` | ID параграфа |
| `is_completed` | `bool` | Параграф пройден |
| `current_step` | `string` | Текущий шаг: `intro`, `content`, `practice`, `summary`, `completed` |
| `time_spent` | `int` | Суммарное время в секундах |
| `last_accessed_at` | `string \| null` | Время последнего доступа (ISO 8601) |
| `completed_at` | `string \| null` | Время завершения (ISO 8601) |
| `self_assessment` | `string \| null` | Последняя самооценка: `understood`, `questions`, `difficult` или `null` |
| `self_assessment_at` | `string \| null` | Время последней самооценки (ISO 8601) |
| `available_steps` | `string[]` | Доступные шаги для этого параграфа |
| `embedded_questions_total` | `int` | Всего встроенных вопросов |
| `embedded_questions_answered` | `int` | Отвечено вопросов |
| `embedded_questions_correct` | `int` | Правильных ответов |

**Пример ответа:**
```json
{
  "paragraph_id": 280,
  "is_completed": false,
  "current_step": "summary",
  "time_spent": 420,
  "last_accessed_at": "2026-02-11T14:38:00Z",
  "completed_at": null,
  "self_assessment": "understood",
  "self_assessment_at": "2026-02-11T14:40:00Z",
  "available_steps": ["intro", "content", "practice", "summary"],
  "embedded_questions_total": 3,
  "embedded_questions_answered": 3,
  "embedded_questions_correct": 2
}
```

---

### 3. POST /paragraphs/{paragraph_id}/progress

Обновить текущий шаг ученика в параграфе.

#### Request

```
POST /api/v1/students/paragraphs/{paragraph_id}/progress
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:**

| Поле | Тип | Обязательное | Описание |
|------|-----|:---:|----------|
| `step` | `string` | да | Один из: `intro`, `content`, `practice`, `summary`, `completed` |
| `time_spent` | `int \| null` | нет | Доп. время в секундах (0–3600, макс 1 час за обновление) |

```json
{
  "step": "summary",
  "time_spent": 120
}
```

#### Response (200 OK)

| Поле | Тип | Описание |
|------|-----|----------|
| `paragraph_id` | `int` | ID параграфа |
| `current_step` | `string` | Текущий шаг |
| `is_completed` | `bool` | Параграф пройден |
| `time_spent` | `int` | Суммарное время в секундах |
| `available_steps` | `string[]` | Доступные шаги |
| `self_assessment` | `string \| null` | Последняя самооценка |

---

## Бизнес-логика

### Расчёт mastery_impact

Сервер корректирует базовый impact по `practice_score`, если он передан:

**Без practice_score (базовые значения):**

| rating | mastery_impact |
|--------|---------------|
| `understood` | `+5.0` |
| `questions` | `0.0` |
| `difficult` | `−5.0` |

**С practice_score (корректировка):**

| rating | practice_score | mastery_impact | Причина |
|--------|---------------|---------------|---------|
| `understood` | ≥ 60% | `+5.0` | Самооценка совпадает |
| `understood` | < 60% | `−2.0` | Переоценка (overconfidence) |
| `questions` | ≥ 80% | `+2.0` | Недооценка, знания хорошие |
| `questions` | < 80% | `0.0` | Адекватная оценка |
| `difficult` | ≥ 80% | `+2.0` | Недооценка |
| `difficult` | 60–79% | `−2.0` | Частичное понимание |
| `difficult` | < 60% | `−5.0` | Реальная проблема |

### Значения next_recommendation

| Условие | Значение | Действие в UI |
|---------|----------|---------------|
| `difficult` (любой practice_score) | `review` | Кнопка "Перечитать параграф" |
| `questions` + practice < 80% | `chat_tutor` | Кнопка "Открыть AI-помощника" |
| `questions` + practice ≥ 80% | `next_paragraph` | Кнопка "Следующий параграф" |
| `understood` + practice < 60% | `practice_retry` | Кнопка "Повторить практику" |
| `understood` + practice ≥ 60% | `next_paragraph` | Кнопка "Следующий параграф" |
| `understood` + нет практики | `next_paragraph` | Кнопка "Следующий параграф" |

---

## Оффлайн-сценарий

Если при нажатии "Завершить" нет интернета:

1. Сохранить `{ rating, practice_score, time_spent }` в локальную очередь
2. При появлении сети — отправить `POST /self-assessment`
3. **Идемпотентность:** сервер проверяет, если за последние 60 секунд уже есть запись с тем же `(student_id, paragraph_id, rating)` — вернёт существующую запись без создания дубликата

---

## Типичный сценарий интеграции

```
1. Ученик открывает параграф
   → POST /paragraphs/{id}/progress  { "step": "intro" }

2. Ученик читает материал
   → POST /paragraphs/{id}/progress  { "step": "content", "time_spent": 180 }

3. Ученик проходит практику (embedded questions)
   → POST /paragraphs/{id}/progress  { "step": "practice" }
   → POST /embedded-questions/{qid}/answer  { "answer": "b" }
   → ...

4. Ученик переходит к итогам
   → POST /paragraphs/{id}/progress  { "step": "summary" }

5. Ученик выбирает самооценку
   → POST /paragraphs/{id}/self-assessment  { "rating": "understood", "practice_score": 85.0 }
   ← { "mastery_impact": 5.0, "next_recommendation": "next_paragraph" }

6. Показать кнопку по next_recommendation

7. Ученик нажимает "Завершить"
   → POST /paragraphs/{id}/progress  { "step": "completed" }
```

---

## Как вычислить practice_score на клиенте

```
practice_score = (embedded_questions_correct / embedded_questions_total) * 100
```

Данные `embedded_questions_correct` и `embedded_questions_total` доступны из `GET /paragraphs/{id}/progress`.

Если `embedded_questions_total = 0` (вопросов не было) — передавайте `practice_score: null`.
