# Homework API Documentation for Mobile Development

> Документация по API домашних заданий для разработчиков мобильного приложения AI Mentor.

**Base URL:** `https://api.ai-mentor.kz/api/v1`

**Authentication:** Bearer token в заголовке `Authorization`

---

## Содержание

1. [Обзор системы](#1-обзор-системы)
2. [Типы заданий (TaskType)](#2-типы-заданий-tasktype)
3. [Статусы и жизненный цикл](#3-статусы-и-жизненный-цикл)
4. [API Endpoints для студента](#4-api-endpoints-для-студента)
5. [Типы данных и схемы](#5-типы-данных-и-схемы)
6. [Работа с вложениями (Attachments)](#6-работа-с-вложениями-attachments)
7. [Получение контента параграфа (для READ задач)](#7-получение-контента-параграфа-для-read-задач)
8. [Flow выполнения домашнего задания](#8-flow-выполнения-домашнего-задания)
9. [Обработка ошибок](#9-обработка-ошибок)
10. [Примеры использования](#10-примеры-использования)

---

## 1. Обзор системы

### Иерархия объектов

```
Homework (домашнее задание)
├── title, description, due_date
├── attachments[] (вложенные файлы)
└── tasks[] (задания)
    ├── HomeworkTask (задание)
    │   ├── task_type (read/quiz/open_question/essay/practice/code)
    │   ├── paragraph_id (связь с контентом)
    │   ├── points, time_limit, max_attempts
    │   ├── attachments[]
    │   └── questions[] (вопросы)
    │       └── HomeworkTaskQuestion
    │           ├── question_type (single_choice/multiple_choice/true_false/short_answer/open_ended/code)
    │           ├── question_text
    │           ├── options[] (для выбора)
    │           └── points
    └── StudentTaskSubmission (отправка студента)
        ├── status, score, attempt_number
        └── answers[] (ответы на вопросы)
            └── StudentTaskAnswer
                ├── answer_text / selected_option_ids
                ├── is_correct, score
                └── ai_feedback, ai_confidence
```

### Ключевые концепции

| Концепция | Описание |
|-----------|----------|
| **Homework** | Домашнее задание, назначенное классу учителем |
| **Task** | Отдельное задание внутри ДЗ (может быть несколько) |
| **Submission** | Попытка студента выполнить задание |
| **Question** | Вопрос внутри задания |
| **Answer** | Ответ студента на вопрос |

---

## 2. Типы заданий (TaskType)

### Enum TaskType

```typescript
enum TaskType {
  READ = 'read',           // Чтение параграфа + вопросы
  QUIZ = 'quiz',           // Тест с выбором ответа
  OPEN_QUESTION = 'open_question', // Открытые вопросы
  ESSAY = 'essay',         // Эссе/сочинение
  PRACTICE = 'practice',   // Практические задачи
  CODE = 'code',           // Программирование
}
```

### Особенности каждого типа

#### READ (Чтение)
- **Цель:** Прочитать параграф и ответить на вопросы
- **Отображение:** Сначала показать контент параграфа, затем вопросы
- **Получение контента:** `GET /students/paragraphs/{paragraph_id}`
- **Вопросы:** Обычно simple_choice или true_false на понимание
- **Проверка:** Автоматическая

#### QUIZ (Тест)
- **Цель:** Проверка знаний через выбор ответов
- **Типы вопросов:** single_choice, multiple_choice, true_false
- **Проверка:** Автоматическая (100% точность)
- **UI:** Показать варианты ответа, один или несколько можно выбрать

#### OPEN_QUESTION (Открытый вопрос)
- **Цель:** Развернутый ответ своими словами
- **Типы вопросов:** short_answer, open_ended
- **Проверка:** AI (если включена) или учитель вручную
- **UI:** Текстовое поле для ввода ответа
- **Feedback:** `ai_feedback` и `ai_confidence` (0.0-1.0)

#### ESSAY (Эссе)
- **Цель:** Написание развернутого текста
- **Проверка:** AI с рубрикой оценки или учитель
- **UI:** Большое текстовое поле (textarea)
- **Особенности:** Может иметь `grading_rubric` с критериями

#### PRACTICE (Практика)
- **Цель:** Решение практических задач
- **Проверка:** Зависит от настроек (авто/AI/учитель)
- **UI:** Зависит от типа вопросов

#### CODE (Код)
- **Цель:** Написание программного кода
- **Типы вопросов:** code
- **UI:** Редактор кода с подсветкой синтаксиса
- **Особенности:** Может иметь тестирование кода

---

## 3. Статусы и жизненный цикл

### StudentHomeworkStatus (статус ДЗ для студента)

```typescript
enum StudentHomeworkStatus {
  ASSIGNED = 'assigned',       // Назначено, еще не начато
  IN_PROGRESS = 'in_progress', // В процессе выполнения
  SUBMITTED = 'submitted',     // Отправлено на проверку
  GRADED = 'graded',           // Проверено и оценено
  RETURNED = 'returned',       // Возвращено на доработку
}
```

### SubmissionStatus (статус отдельного задания)

```typescript
enum SubmissionStatus {
  NOT_STARTED = 'not_started', // Не начато
  IN_PROGRESS = 'in_progress', // В процессе
  SUBMITTED = 'submitted',     // Отправлено
  NEEDS_REVIEW = 'needs_review', // Требует ручной проверки
  GRADED = 'graded',           // Проверено
}
```

### Диаграмма переходов

```
Homework Assignment:
  ASSIGNED ──[start any task]──> IN_PROGRESS
  IN_PROGRESS ──[complete all tasks]──> SUBMITTED
  SUBMITTED ──[teacher grades]──> GRADED
  GRADED ──[teacher returns]──> RETURNED

Task Submission:
  NOT_STARTED ──[start_task]──> IN_PROGRESS
  IN_PROGRESS ──[submit answers + complete]──> SUBMITTED/NEEDS_REVIEW/GRADED
  NEEDS_REVIEW ──[teacher reviews]──> GRADED
```

---

## 4. API Endpoints для студента

### 4.1 Список домашних заданий

```
GET /students/homework
```

**Query Parameters:**

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `page` | int | 1 | Номер страницы |
| `page_size` | int | 20 | Элементов на странице (max 100) |
| `status` | string | - | Фильтр по статусу (assigned/in_progress/submitted/graded/returned) |
| `include_completed` | bool | true | Включить завершенные ДЗ |

**Response:** `PaginatedResponse<StudentHomeworkResponse>`

```json
{
  "items": [
    {
      "id": 1,
      "title": "Домашняя работа №1",
      "description": "Изучение атмосферы",
      "due_date": "2025-02-01T23:59:59Z",
      "is_overdue": false,
      "can_submit": true,
      "my_status": "in_progress",
      "my_score": null,
      "max_score": 100,
      "my_percentage": null,
      "is_late": false,
      "late_penalty": 0,
      "show_explanations": true,
      "attachments": [...],
      "tasks": [...]
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### 4.2 Детали домашнего задания

```
GET /students/homework/{homework_id}
```

**Response:** `StudentHomeworkResponse`

```json
{
  "id": 1,
  "title": "Домашняя работа №1",
  "description": "Описание задания",
  "due_date": "2025-02-01T23:59:59Z",
  "is_overdue": false,
  "can_submit": true,
  "my_status": "in_progress",
  "my_score": 75.0,
  "max_score": 100,
  "my_percentage": 75.0,
  "is_late": false,
  "late_penalty": 0,
  "show_explanations": true,
  "attachments": [
    {
      "url": "/uploads/a1b2c3d4_20231030_150000.pdf",
      "name": "Методичка.pdf",
      "type": "pdf",
      "size": 2048000
    }
  ],
  "tasks": [
    {
      "id": 1,
      "paragraph_id": 123,
      "paragraph_title": "Атмосфера Земли",
      "task_type": "read",
      "instructions": "Прочитайте параграф и ответьте на вопросы",
      "points": 30,
      "time_limit_minutes": null,
      "attachments": [],
      "status": "not_started",
      "current_attempt": 0,
      "max_attempts": 3,
      "attempts_remaining": 3,
      "submission_id": null,
      "my_score": null,
      "questions_count": 5,
      "answered_count": 0
    },
    {
      "id": 2,
      "paragraph_id": 124,
      "paragraph_title": "Состав атмосферы",
      "task_type": "quiz",
      "instructions": "Выберите правильные ответы",
      "points": 40,
      "time_limit_minutes": 15,
      "attachments": [],
      "status": "in_progress",
      "current_attempt": 1,
      "max_attempts": 1,
      "attempts_remaining": 0,
      "submission_id": 42,
      "my_score": null,
      "questions_count": 8,
      "answered_count": 3
    }
  ]
}
```

---

### 4.3 Начать выполнение задания

```
POST /students/homework/{homework_id}/tasks/{task_id}/start
```

**Request Body:** пустое

**Response:** `StudentTaskResponse`

```json
{
  "id": 2,
  "paragraph_id": 124,
  "paragraph_title": "Состав атмосферы",
  "task_type": "quiz",
  "instructions": "Выберите правильные ответы",
  "points": 40,
  "time_limit_minutes": 15,
  "attachments": [],
  "status": "in_progress",
  "current_attempt": 1,
  "max_attempts": 1,
  "attempts_remaining": 0,
  "submission_id": 42,
  "my_score": null,
  "questions_count": 8,
  "answered_count": 0
}
```

**Важно:** Сохраните `submission_id` — он нужен для отправки ответов!

---

### 4.4 Получить вопросы задания

```
GET /students/homework/{homework_id}/tasks/{task_id}/questions
```

**Response:** `StudentQuestionResponse[]`

```json
[
  {
    "id": 10,
    "question_text": "Какой газ составляет большую часть атмосферы Земли?",
    "question_type": "single_choice",
    "options": [
      { "id": "a", "text": "Кислород" },
      { "id": "b", "text": "Азот" },
      { "id": "c", "text": "Углекислый газ" },
      { "id": "d", "text": "Водород" }
    ],
    "points": 5,
    "my_answer": null,
    "my_selected_options": null,
    "is_answered": false
  },
  {
    "id": 11,
    "question_text": "Озоновый слой защищает Землю от ультрафиолета",
    "question_type": "true_false",
    "options": [
      { "id": "a", "text": "Верно" },
      { "id": "b", "text": "Неверно" }
    ],
    "points": 3,
    "my_answer": null,
    "my_selected_options": ["a"],
    "is_answered": true
  },
  {
    "id": 12,
    "question_text": "Объясните роль углекислого газа в парниковом эффекте",
    "question_type": "open_ended",
    "options": null,
    "points": 10,
    "my_answer": "Углекислый газ задерживает тепло...",
    "my_selected_options": null,
    "is_answered": true
  }
]
```

**Важно:** Поле `is_correct` в `options` НЕ возвращается студенту до завершения!

---

### 4.5 Отправить ответ на вопрос

```
POST /students/homework/submissions/{submission_id}/answer
```

**Request Body:** `AnswerSubmit`

```json
{
  "question_id": 10,
  "selected_options": ["b"]
}
```

или для текстового ответа:

```json
{
  "question_id": 12,
  "answer_text": "Углекислый газ задерживает инфракрасное излучение..."
}
```

**Response:** `SubmissionResult`

```json
{
  "submission_id": 42,
  "question_id": 10,
  "is_correct": true,
  "score": 5.0,
  "max_score": 5.0,
  "feedback": "Верно!",
  "explanation": "Азот составляет около 78% атмосферы",
  "ai_feedback": null,
  "ai_confidence": null,
  "needs_review": false
}
```

Для открытых вопросов с AI-проверкой:

```json
{
  "submission_id": 42,
  "question_id": 12,
  "is_correct": null,
  "score": 8.5,
  "max_score": 10.0,
  "feedback": null,
  "explanation": null,
  "ai_feedback": "Хороший ответ! Вы правильно объяснили механизм. Можно было добавить информацию о других парниковых газах.",
  "ai_confidence": 0.85,
  "needs_review": false
}
```

---

### 4.6 Завершить задание

```
POST /students/homework/submissions/{submission_id}/complete
```

**Request Body:** пустое

**Response:** `TaskSubmissionResult`

```json
{
  "submission_id": 42,
  "task_id": 2,
  "status": "graded",
  "attempt_number": 1,
  "total_score": 35.5,
  "max_score": 40.0,
  "percentage": 88.75,
  "is_late": false,
  "late_penalty_applied": 0,
  "original_score": 35.5,
  "answers": [
    {
      "submission_id": 42,
      "question_id": 10,
      "is_correct": true,
      "score": 5.0,
      "max_score": 5.0,
      "feedback": "Верно!",
      "explanation": "Азот составляет около 78%",
      "ai_feedback": null,
      "ai_confidence": null,
      "needs_review": false
    }
  ],
  "correct_count": 6,
  "incorrect_count": 1,
  "needs_review_count": 1
}
```

**Статусы после завершения:**
- `graded` — все ответы проверены автоматически или AI с высокой уверенностью
- `needs_review` — есть ответы, требующие проверки учителем
- `submitted` — отправлено, ожидает проверки

---

### 4.7 Получить результаты задания

```
GET /students/homework/submissions/{submission_id}/results
```

**Response:** `StudentQuestionWithFeedback[]`

```json
[
  {
    "id": 10,
    "question_text": "Какой газ составляет большую часть атмосферы?",
    "question_type": "single_choice",
    "options": [
      { "id": "a", "text": "Кислород" },
      { "id": "b", "text": "Азот" },
      { "id": "c", "text": "Углекислый газ" },
      { "id": "d", "text": "Водород" }
    ],
    "points": 5,
    "my_answer": null,
    "my_selected_options": ["b"],
    "is_answered": true,
    "is_correct": true,
    "score": 5.0,
    "max_score": 5.0,
    "explanation": "Азот (N₂) составляет примерно 78% атмосферы Земли",
    "ai_feedback": null,
    "ai_confidence": null
  }
]
```

**Важно:** `explanation` показывается только если `show_explanations = true` в настройках ДЗ.

---

## 5. Типы данных и схемы

### QuestionType (тип вопроса)

```typescript
enum QuestionType {
  SINGLE_CHOICE = 'single_choice',     // Один правильный ответ
  MULTIPLE_CHOICE = 'multiple_choice', // Несколько правильных
  TRUE_FALSE = 'true_false',           // Верно/Неверно
  SHORT_ANSWER = 'short_answer',       // Короткий текст
  OPEN_ENDED = 'open_ended',           // Развернутый ответ
  CODE = 'code',                       // Код
}
```

### Attachment (вложение)

```typescript
interface Attachment {
  url: string;       // URL файла (относительный или абсолютный)
  name: string;      // Оригинальное имя файла
  type: 'image' | 'pdf' | 'doc' | 'other';
  size: number;      // Размер в байтах
}
```

### QuestionOption (вариант ответа)

```typescript
interface QuestionOption {
  id: string;    // "a", "b", "c", "d"
  text: string;  // Текст варианта
  // is_correct НЕ возвращается студенту!
}
```

### AnswerSubmit (отправка ответа)

```typescript
interface AnswerSubmit {
  question_id: number;
  answer_text?: string;       // Для текстовых ответов
  selected_options?: string[]; // Для вопросов с выбором ["a", "c"]
}
```

**Валидация:** Требуется либо `answer_text`, либо `selected_options`.

---

## 6. Работа с вложениями (Attachments)

### Структура

Вложения могут быть на двух уровнях:
1. **Homework.attachments** — общие файлы для всего ДЗ
2. **Task.attachments** — файлы для конкретного задания

### Получение URL файла

URL вложения может быть:
- **Относительный:** `/uploads/a1b2c3d4_20231030.pdf` — нужно добавить base URL
- **Абсолютный:** `https://api.ai-mentor.kz/uploads/...`

```typescript
function getFileUrl(url: string): string {
  if (url.startsWith('/')) {
    // Относительный URL — добавить base URL сервера (без /api/v1)
    const baseUrl = 'https://api.ai-mentor.kz';
    return `${baseUrl}${url}`;
  }
  return url;
}
```

### Типы файлов

| Тип | MIME типы | Иконка |
|-----|-----------|--------|
| `image` | image/jpeg, image/png, image/webp, image/gif | 🖼️ |
| `pdf` | application/pdf | 📄 |
| `doc` | doc, docx, xls, xlsx, ppt, pptx, txt | 📝 |
| `other` | остальные | 📎 |

### Отображение

```typescript
// Примеры отображения
if (attachment.type === 'image') {
  // Показать как изображение
  return <Image source={{ uri: getFileUrl(attachment.url) }} />;
} else {
  // Показать как ссылку для скачивания
  return (
    <TouchableOpacity onPress={() => openUrl(getFileUrl(attachment.url))}>
      <Text>{attachment.name} ({formatFileSize(attachment.size)})</Text>
    </TouchableOpacity>
  );
}
```

---

## 7. Получение контента параграфа (для READ задач)

Для задач типа `READ` необходимо показать контент параграфа перед вопросами.

### Основной контент параграфа

```
GET /students/paragraphs/{paragraph_id}
```

**Response:** `StudentParagraphDetailResponse`

```json
{
  "id": 123,
  "chapter_id": 45,
  "title": "Атмосфера Земли",
  "number": "3.1",
  "order": 1,
  "content": "# Атмосфера Земли\n\nАтмосфера — это воздушная оболочка...",
  "summary": "Краткое содержание параграфа",
  "learning_objective": "Понимать структуру атмосферы",
  "lesson_objective": "К концу урока студент сможет...",
  "key_terms": ["атмосфера", "тропосфера", "озоновый слой"],
  "questions": [],
  "status": "in_progress",
  "current_step": null,
  "has_audio": true,
  "has_video": false,
  "has_slides": true,
  "has_cards": true,
  "chapter_title": "Глава 3: Атмосфера",
  "textbook_title": "География 7 класс"
}
```

### Дополнительный контент (аудио, видео, карточки)

```
GET /students/paragraphs/{paragraph_id}/content?language=ru
```

**Query Parameters:**
- `language` — `ru` или `kk` (по умолчанию `ru`)

**Response:** `ParagraphRichContent`

```json
{
  "paragraph_id": 123,
  "language": "ru",
  "explain_text": "Простое объяснение: Атмосфера — это...",
  "audio_url": "https://cdn.ai-mentor.kz/audio/para_123_ru.mp3",
  "video_url": null,
  "slides_url": "https://cdn.ai-mentor.kz/slides/para_123_ru.pdf",
  "cards": [
    {
      "id": "card-1",
      "type": "term",
      "front": "Атмосфера",
      "back": "Воздушная оболочка Земли",
      "order": 0
    },
    {
      "id": "card-2",
      "type": "fact",
      "front": "Из чего состоит атмосфера?",
      "back": "78% азот, 21% кислород, 1% другие газы",
      "order": 1
    }
  ],
  "has_explain": true,
  "has_audio": true,
  "has_video": false,
  "has_slides": true,
  "has_cards": true
}
```

### UI для READ задания

1. **Показать заголовок** с названием параграфа
2. **Отобразить контент** (`content` — это Markdown)
3. **Дополнительные материалы** (если есть):
   - Кнопка "Прослушать" (audio_url)
   - Кнопка "Смотреть слайды" (slides_url)
   - Секция "Карточки" для запоминания
   - Упрощенное объяснение (explain_text)
4. **Кнопка "Перейти к вопросам"**

---

## 8. Flow выполнения домашнего задания

### Полный флоу для мобильного приложения

```
1. ЭКРАН СПИСКА ДЗ
   ├── GET /students/homework
   ├── Показать список с фильтрами по статусу
   └── Tap на ДЗ → переход к деталям

2. ЭКРАН ДЕТАЛЕЙ ДЗ
   ├── GET /students/homework/{homework_id}
   ├── Показать:
   │   ├── Название, описание, дедлайн
   │   ├── Вложения (если есть)
   │   ├── Общий прогресс (my_score / max_score)
   │   └── Список заданий (tasks)
   └── Tap на задание → начать выполнение

3. НАЧАЛО ЗАДАНИЯ
   ├── POST /students/homework/{homework_id}/tasks/{task_id}/start
   ├── Сохранить submission_id!
   └── Переход к вопросам

4. ЭКРАН ВОПРОСОВ
   ├── Если task_type === 'read':
   │   ├── GET /students/paragraphs/{paragraph_id}
   │   ├── GET /students/paragraphs/{paragraph_id}/content
   │   └── Показать контент → затем вопросы
   │
   ├── GET /students/homework/{homework_id}/tasks/{task_id}/questions
   │
   ├── Для каждого вопроса:
   │   ├── Показать question_text
   │   ├── Если question_type in (single_choice, multiple_choice, true_false):
   │   │   └── Показать options как кнопки/чекбоксы
   │   ├── Если question_type in (short_answer, open_ended):
   │   │   └── Показать текстовое поле
   │   └── Если question_type === 'code':
   │       └── Показать редактор кода
   │
   └── При ответе на вопрос:
       ├── POST /students/homework/submissions/{submission_id}/answer
       └── Показать feedback (если есть)

5. ЗАВЕРШЕНИЕ ЗАДАНИЯ
   ├── POST /students/homework/submissions/{submission_id}/complete
   ├── Показать результаты:
   │   ├── total_score / max_score
   │   ├── percentage
   │   ├── correct_count / incorrect_count
   │   └── Если needs_review_count > 0: "Ожидает проверки учителя"
   └── Кнопка "Назад к ДЗ" или "Смотреть разбор"

6. ЭКРАН РЕЗУЛЬТАТОВ (опционально)
   ├── GET /students/homework/submissions/{submission_id}/results
   └── Показать каждый вопрос с:
       ├── Мой ответ (my_answer / my_selected_options)
       ├── Правильность (is_correct)
       ├── Объяснение (explanation) — если show_explanations
       └── AI feedback (ai_feedback) — для открытых вопросов
```

### Обработка состояний

```typescript
// При входе на экран задания
if (task.status === 'not_started') {
  // Показать кнопку "Начать"
  // При нажатии: POST /start
}

if (task.status === 'in_progress') {
  // Показать кнопку "Продолжить"
  // Использовать существующий submission_id
}

if (task.status === 'submitted' || task.status === 'graded') {
  // Показать результаты
  // Если attempts_remaining > 0: кнопка "Попробовать снова"
}

if (task.status === 'needs_review') {
  // Показать "Ожидает проверки учителем"
}
```

### Обработка дедлайна

```typescript
if (homework.is_overdue && !homework.can_submit) {
  // Нельзя отправить — показать сообщение
  showMessage("Срок сдачи истек");
}

if (homework.is_late && homework.can_submit) {
  // Можно отправить со штрафом
  showMessage(`Сдача с опозданием. Штраф: ${homework.late_penalty}%`);
}
```

---

## 9. Обработка ошибок

### HTTP коды

| Код | Описание | Действие |
|-----|----------|----------|
| 200 | OK | Обработать ответ |
| 201 | Created | Ресурс создан |
| 400 | Bad Request | Показать ошибку из `detail` |
| 401 | Unauthorized | Перенаправить на логин |
| 403 | Forbidden | "Нет доступа" |
| 404 | Not Found | "Не найдено" |
| 500 | Server Error | "Ошибка сервера" |

### Формат ошибки

```json
{
  "detail": "Превышено максимальное количество попыток"
}
```

### Типичные ошибки

| Ситуация | Ошибка | Как обрабатывать |
|----------|--------|------------------|
| Попытка начать после дедлайна | 400: "Срок сдачи истек" | Показать сообщение, заблокировать UI |
| Превышены попытки | 400: "Превышено макс. попыток" | Скрыть кнопку "Начать" |
| ДЗ не назначено | 404: "Homework not found" | Вернуться к списку |
| Не авторизован | 401 | Перейти на экран логина |

---

## 10. Примеры использования

### TypeScript API Client

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://api.ai-mentor.kz/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Установка токена
api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

// Получить список ДЗ
async function getHomeworkList(status?: string) {
  const response = await api.get('/students/homework', {
    params: { status, page: 1, page_size: 20 }
  });
  return response.data.items;
}

// Получить детали ДЗ
async function getHomework(homeworkId: number) {
  const response = await api.get(`/students/homework/${homeworkId}`);
  return response.data;
}

// Начать задание
async function startTask(homeworkId: number, taskId: number) {
  const response = await api.post(
    `/students/homework/${homeworkId}/tasks/${taskId}/start`
  );
  return response.data; // Сохранить submission_id!
}

// Получить вопросы
async function getQuestions(homeworkId: number, taskId: number) {
  const response = await api.get(
    `/students/homework/${homeworkId}/tasks/${taskId}/questions`
  );
  return response.data;
}

// Отправить ответ
async function submitAnswer(
  submissionId: number,
  questionId: number,
  answer: { answer_text?: string; selected_options?: string[] }
) {
  const response = await api.post(
    `/students/homework/submissions/${submissionId}/answer`,
    {
      question_id: questionId,
      ...answer
    }
  );
  return response.data;
}

// Завершить задание
async function completeSubmission(submissionId: number) {
  const response = await api.post(
    `/students/homework/submissions/${submissionId}/complete`
  );
  return response.data;
}

// Получить результаты
async function getResults(submissionId: number) {
  const response = await api.get(
    `/students/homework/submissions/${submissionId}/results`
  );
  return response.data;
}
```

### React Native компонент вопроса

```tsx
function QuestionCard({ question, onAnswer }: Props) {
  const [selected, setSelected] = useState<string[]>([]);
  const [text, setText] = useState('');

  const handleSubmit = () => {
    if (question.question_type === 'single_choice' ||
        question.question_type === 'multiple_choice' ||
        question.question_type === 'true_false') {
      onAnswer({ selected_options: selected });
    } else {
      onAnswer({ answer_text: text });
    }
  };

  if (question.question_type === 'single_choice') {
    return (
      <View>
        <Text style={styles.question}>{question.question_text}</Text>
        {question.options?.map(opt => (
          <TouchableOpacity
            key={opt.id}
            style={[
              styles.option,
              selected.includes(opt.id) && styles.selected
            ]}
            onPress={() => setSelected([opt.id])}
          >
            <Text>{opt.text}</Text>
          </TouchableOpacity>
        ))}
        <Button title="Ответить" onPress={handleSubmit} />
      </View>
    );
  }

  if (question.question_type === 'multiple_choice') {
    return (
      <View>
        <Text style={styles.question}>{question.question_text}</Text>
        <Text style={styles.hint}>Выберите все подходящие варианты</Text>
        {question.options?.map(opt => (
          <TouchableOpacity
            key={opt.id}
            style={[
              styles.option,
              selected.includes(opt.id) && styles.selected
            ]}
            onPress={() => {
              if (selected.includes(opt.id)) {
                setSelected(selected.filter(s => s !== opt.id));
              } else {
                setSelected([...selected, opt.id]);
              }
            }}
          >
            <Text>{opt.text}</Text>
          </TouchableOpacity>
        ))}
        <Button title="Ответить" onPress={handleSubmit} />
      </View>
    );
  }

  if (question.question_type === 'open_ended' ||
      question.question_type === 'short_answer') {
    return (
      <View>
        <Text style={styles.question}>{question.question_text}</Text>
        <TextInput
          style={styles.textInput}
          multiline={question.question_type === 'open_ended'}
          numberOfLines={question.question_type === 'open_ended' ? 6 : 2}
          value={text}
          onChangeText={setText}
          placeholder="Введите ваш ответ..."
        />
        <Button title="Ответить" onPress={handleSubmit} />
      </View>
    );
  }

  // ... другие типы вопросов
}
```

---

## Дополнительные заметки

### Поддержка языков

- Контент параграфов доступен на русском (`ru`) и казахском (`kk`)
- Используйте query parameter `language` при запросе `/content`

### Кэширование

Рекомендуется кэшировать:
- Список ДЗ (обновлять при pull-to-refresh)
- Контент параграфов (редко меняется)
- Вопросы задания (на время выполнения)

### Offline режим

Для offline поддержки:
1. Сохранять ответы локально при отсутствии сети
2. Синхронизировать при появлении связи
3. Показывать индикатор "Не сохранено"

### Уведомления

Рекомендуемые push-уведомления:
- Новое ДЗ назначено
- Приближается дедлайн (за 24ч, за 1ч)
- ДЗ проверено учителем
- ДЗ возвращено на доработку

---

## Changelog

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2025-01-22 | Первая версия документации |
