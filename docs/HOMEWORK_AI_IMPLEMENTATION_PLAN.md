# Homework AI System — План реализации

**Версия:** 2.3
**Последнее обновление:** 2026-01-06
**Статус:** Все фазы выполнены ✅ (Backend + AI + Teacher + Student Frontend + Tests)

---

## Прогресс реализации

| Фаза | Описание | Статус | Дата |
|------|----------|--------|------|
| Фаза 1 | Models + Migrations | ✅ Выполнено | 2026-01-04 |
| Фаза 2 | Schemas + Repositories | ✅ Выполнено | 2026-01-04 |
| Фаза 3 | Services | ✅ Выполнено | 2026-01-04 |
| Фаза 4 | API Endpoints | ✅ Выполнено | 2026-01-04 |
| Фаза 5 | AI Integration | ✅ Выполнено | 2026-01-05 |
| Фаза 6 | Teacher Frontend | ✅ Выполнено | 2026-01-05 |
| Фаза 7 | Student Frontend | ✅ Выполнено | 2026-01-06 |
| Фаза 8 | Frontend Tests | ✅ Выполнено | 2026-01-06 |

---

## 1. Обзор системы

### Цель

Система домашних заданий с AI-интеграцией:
- Автоматическая генерация вопросов на основе параграфов
- Автоматическая проверка открытых ответов
- Персонализация по уровню mastery (A/B/C)
- Human-in-the-loop для низкой уверенности AI

### Ключевые пользователи

| Роль | Функции |
|------|---------|
| **Teacher** | Создание ДЗ, настройка AI, проверка флагов, аналитика |
| **Student** | Выполнение ДЗ, просмотр feedback |
| **AI** | Генерация вопросов, автопроверка, персонализация |

---

## 2. Архитектура БД

```
Homework (ДЗ для класса)
    └── HomeworkTask (задача = параграф) + school_id
            └── HomeworkTaskQuestion (вопрос + version)

HomeworkStudent (назначение ученику)
    └── StudentTaskSubmission (попытка + attempt_number)
            └── StudentTaskAnswer (ответ + ai_grading)

AIGenerationLog (аудит AI операций)
```

### Ключевые особенности
- `school_id` в HomeworkTask для быстрого RLS
- `version` + `is_active` для версионирования вопросов
- `max_attempts` / `attempt_number` для попыток
- Late submission policy с grace period и штрафами

---

## 3. Фаза 1: Models + Migrations ✅

### Созданные/обновлённые файлы

| Файл | Описание |
|------|----------|
| `models/homework.py` | Модели Homework, HomeworkTask, HomeworkTaskQuestion, etc. |
| `alembic/versions/022_homework_ai_v2_improvements.py` | Миграция с новыми полями |

### Добавленные поля
- `homework`: late_submission_allowed, late_penalty_per_day, grace_period_hours, max_late_days
- `homework_tasks`: school_id, max_attempts
- `homework_task_questions`: version, is_active, replaced_by_id
- `student_task_submissions`: attempt_number, is_late, late_penalty_applied, original_score

---

## 4. Фаза 2: Schemas + Repositories ✅

### Созданные файлы

| Файл | Строк | Описание |
|------|-------|----------|
| `schemas/homework.py` | ~250 | Pydantic schemas (Create, Response, Enums) |
| `repositories/homework_repo.py` | ~300 | CRUD операции, версионирование вопросов |

### Ключевые схемы
- `HomeworkCreate`, `HomeworkTaskCreate`, `QuestionCreate`
- `HomeworkResponse`, `StudentHomeworkResponse`, `SubmissionResult`
- Enums: `HomeworkStatus`, `TaskType`, `QuestionType`, `BloomLevel`

---

## 5. Фаза 3: Services ✅

### Созданные файлы

| Файл | Строк | Описание |
|------|-------|----------|
| `services/homework_service.py` | ~400 | Бизнес-логика ДЗ |
| `services/homework_ai_service.py` | ~650 | AI генерация и grading |

### Ключевые методы HomeworkService
- `create_homework()`, `publish_homework()`
- `generate_questions_for_task()`
- `start_task()`, `submit_answer()`
- `calculate_late_penalty()`

### Ключевые методы HomeworkAIService
- `generate_questions()` — генерация вопросов из параграфа
- `grade_answer()` — AI оценка открытых ответов
- `personalize_difficulty()` — адаптация по mastery

---

## 6. Фаза 4: API Endpoints ✅

### Teacher Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/teachers/homework` | Создать ДЗ (draft) |
| GET | `/teachers/homework` | Список ДЗ учителя |
| GET | `/teachers/homework/{id}` | Получить ДЗ с задачами |
| PUT | `/teachers/homework/{id}` | Обновить ДЗ |
| POST | `/teachers/homework/{id}/publish` | Опубликовать ДЗ |
| POST | `/teachers/homework/{id}/tasks` | Добавить задачу |
| POST | `/teachers/homework/tasks/{id}/generate-questions` | AI генерация |
| GET | `/teachers/homework/review-queue` | Очередь на проверку |
| POST | `/teachers/homework/answers/{id}/review` | Проверить ответ |
| GET | `/teachers/textbooks` | Список учебников (Фаза 6) |
| GET | `/teachers/textbooks/{id}/chapters` | Главы учебника (Фаза 6) |
| GET | `/teachers/chapters/{id}/paragraphs` | Параграфы главы (Фаза 6) |

### Student Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/students/homework` | Мои ДЗ |
| GET | `/students/homework/{id}` | ДЗ с прогрессом |
| POST | `/students/homework/{id}/tasks/{task_id}/start` | Начать задачу |
| POST | `/students/homework/submissions/{id}/answer` | Отправить ответ |
| POST | `/students/homework/submissions/{id}/complete` | Завершить задачу |

### Созданные файлы

| Файл | Строк |
|------|-------|
| `api/v1/teachers_homework.py` | ~500 |
| `api/v1/students/homework.py` | ~280 |

---

## 7. Фаза 5: AI Integration ✅

### Реализовано

- [x] `HomeworkAIService` (~650 строк)
- [x] Интеграция с `LLMService` (Cerebras/OpenRouter/OpenAI)
- [x] Промпты на русском (казахский через `language` параметр)
- [x] Fallback при ошибках AI (возвращает `confidence=0.0`)
- [x] Unit тесты парсинга JSON (35 тестов)

### Тесты

| Файл | Тестов | Описание |
|------|--------|----------|
| `tests/test_homework_ai_service.py` | ~30 | Полные тесты с мок LLM |
| `tests/test_homework_ai_parsing.py` | 35 ✅ | Standalone тесты парсинга |

### Оставшиеся улучшения (опционально)

- [ ] Rate limiting для AI вызовов
- [ ] Казахские варианты системных промптов
- [ ] Кэширование AI ответов

---

## 8. Фаза 6: Teacher Frontend ✅

### Структура страниц

```
teacher-app/src/app/[locale]/(dashboard)/homework/
├── page.tsx                    # Список ДЗ ✅
├── create/page.tsx             # Создание ДЗ (4-step wizard) ✅
├── [id]/page.tsx               # Просмотр ДЗ ✅
├── [id]/edit/page.tsx          # Редактирование (post-MVP)
└── review/page.tsx             # Очередь проверки ✅
```

### Созданные файлы

| Файл | Описание |
|------|----------|
| `types/homework.ts` | TypeScript типы (Enums, Interfaces) |
| `types/content.ts` | Типы для учебников/глав/параграфов |
| `lib/api/homework.ts` | API функции для ДЗ |
| `lib/api/content.ts` | API для ContentSelector |
| `lib/hooks/use-homework.ts` | React Query hooks (useMutation!) |
| `lib/hooks/use-content.ts` | Hooks для учебников/глав/параграфов |
| `components/homework/*` | 7 компонентов (Badge, Card, Selector, etc.) |
| `components/ui/*` | 5 shadcn/ui компонентов |

### Backend endpoints (добавлены для ContentSelector)

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/teachers/textbooks` | Список учебников (global + school) |
| GET | `/teachers/textbooks/{id}/chapters` | Главы учебника |
| GET | `/teachers/chapters/{id}/paragraphs` | Параграфы главы |

### Чеклист

- [x] Страница списка ДЗ с фильтрацией по статусу
- [x] Форма создания ДЗ с 4-step wizard
- [x] Добавление задач из параграфов (ContentSelector)
- [x] AI генерация вопросов (AIGenerationPanel)
- [x] Публикация ДЗ
- [x] Очередь проверки (review queue)
- [x] Просмотр ДЗ с статистикой
- [x] Навигация в sidebar
- [x] Локализация (RU/KZ)
- [ ] Редактирование черновиков (post-MVP)
- [ ] Детальная аналитика (post-MVP)

---

## 9. Фаза 7: Student Frontend ✅

### Структура страниц

```
student-app/src/app/[locale]/(app)/homework/
├── page.tsx                    # Список моих ДЗ ✅
└── [id]/
    ├── page.tsx                # Просмотр ДЗ ✅
    └── tasks/[taskId]/page.tsx # Выполнение задачи ✅
```

### Созданные файлы

| Файл | Описание |
|------|----------|
| `lib/api/homework.ts` | Types + API функции (~200 строк) |
| `lib/hooks/use-homework.ts` | React Query hooks (~120 строк) |
| `components/homework/HomeworkStatusBadge.tsx` | Badge статуса |
| `components/homework/HomeworkCard.tsx` | Карточка в списке |
| `components/homework/TaskCard.tsx` | Карточка задачи |
| `components/homework/ChoiceQuestion.tsx` | single/multiple choice |
| `components/homework/TextQuestion.tsx` | short_answer/open_ended |
| `components/homework/QuestionFeedback.tsx` | Feedback после ответа |
| `components/homework/SubmissionResultCard.tsx` | Результаты попытки |
| `components/homework/LateWarning.tsx` | Предупреждение просрочки |
| `components/homework/index.ts` | Barrel export |

### Чеклист

- [x] Список ДЗ с фильтрами (активные, выполненные)
- [x] Просмотр ДЗ с прогрессом
- [x] Выполнение задачи (quiz-like UI)
- [x] Поддержка всех типов вопросов
- [x] Instant feedback для choice вопросов
- [x] AI feedback для open-ended
- [x] Отображение попыток
- [x] Late submission warning
- [x] Локализация (RU/KZ)
- [x] Навигация в bottom nav

---

## 10. Фаза 8: Frontend Tests ✅

### Unit тесты для Student Homework

| Файл | Тестов | Описание |
|------|--------|----------|
| `__tests__/api/homework.test.ts` | 15 | API функции, enums |
| `__tests__/components/homework/HomeworkStatusBadge.test.tsx` | 13 | Статусы, стили, overdue |
| `__tests__/components/homework/ChoiceQuestion.test.tsx` | 19 | Single/multiple choice, submit |
| `__tests__/components/homework/TextQuestion.test.tsx` | 21 | Short answer, open-ended, submit |
| `__tests__/components/homework/QuestionFeedback.test.tsx` | 27 | Correct/incorrect/pending, AI feedback |
| `__tests__/components/homework/SubmissionResultCard.test.tsx` | 27 | Passed/failed, penalties, navigation |
| `__tests__/components/homework/HomeworkCard.test.tsx` | 28 | Card rendering, progress, due date |

**Итого: 150 тестов для homework модуля**

### Покрытие

- [x] API функции (listMyHomework, getHomeworkDetail, startTask, submitAnswer, etc.)
- [x] Все TypeScript enums
- [x] Компонент рендеринг для всех состояний
- [x] User interactions (клики, ввод текста, submit)
- [x] Feedback стилизация (correct/incorrect/pending)
- [x] AI feedback с confidence bar
- [x] Late penalties и overdue styling
- [x] Navigation callbacks

### Запуск тестов

```bash
cd student-app
npm test                # Запуск всех тестов
npm run test:coverage   # С покрытием
```

---

## 11. Риски и митигация

| Риск | Митигация |
|------|-----------|
| AI генерирует некорректные вопросы | Human review, confidence threshold |
| AI неправильно оценивает ответы | `flagged_for_review`, teacher override |
| Высокие затраты на AI | Rate limiting, caching |
| Потеря данных при регенерации | Версионирование вопросов |

---

## 12. Зависимости между фазами

```
Фаза 1 ──▶ Фаза 2 ──▶ Фаза 3 ──▶ Фаза 4 ──▶ Фаза 5
                                      │
                                      ├──▶ Фаза 6 (Teacher UI)
                                      │
                                      └──▶ Фаза 7 (Student UI) ──▶ Фаза 8 (Tests)
```

Фазы 6 и 7 могут выполняться параллельно.

---

## 13. Что дальше (post-MVP)

- [ ] Редактирование черновиков ДЗ (Teacher)
- [ ] Детальная аналитика по ДЗ (Teacher)
- [ ] Rate limiting для AI вызовов
- [ ] Казахские системные промпты для AI
- [ ] Кэширование AI ответов
- [ ] E2E тесты (Playwright)

---

*Документ обновляется по мере реализации.*
