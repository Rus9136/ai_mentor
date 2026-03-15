# Quiz Battle Platform — Полный план разработки

> Дата: 2026-03-15
> Статус: **Фаза 2.3 — РЕАЛИЗОВАНА** (Teacher Paced, Exit Ticket, Live Matrix, Short Answer, Reports)
> Вдохновение: [Kahoot](https://kahoot.it/), [Socrative](https://www.socrative.com/)
> Связь: `docs/GAMIFICATION_FRONTEND_PLAN.md` (Фаза 2)

---

## Концепция

Платформа живых соревнований для школьников 5-11 классов Казахстана. Учитель запускает квиз — ученики соревнуются в реальном времени с телефона, планшета или компьютера.

**Ключевые принципы:**

| Принцип | Описание | Источник |
|---------|----------|----------|
| **Zero friction** | Вход по 6-значному коду или QR, без регистрации | Kahoot |
| **Mobile-first** | WebView в мобилке + полноценный веб | Оба |
| **Учитель = режиссёр** | Полный контроль темпа, паузы, обсуждения | Socrative |
| **Speed + Accuracy** | Быстрый правильный ответ = больше очков | Kahoot |
| **Данные = ценность** | Каждый квиз влияет на mastery и аналитику | Своё |
| **Engagement** | Лидерборд, стрики, подиум, XP, но с "мягким" режимом | Оба |

**Режимы отображения вопросов:**
- **"Мобильный"** (по умолчанию): вопрос + варианты на экране ученика — для дома и без проектора
- **"Класс"** (будущее): на экране ученика только цветные кнопки, учитель проецирует dashboard

---

## Обзор фаз

| Фаза | Название | Статус | Объём |
|------|----------|--------|-------|
| **2.0** | MVP Live Quiz | ✅ **ГОТОВО** | ~7-10 дней |
| **2.1** | Улучшения Live Quiz | ✅ **ГОТОВО** | ~3-4 дня |
| **2.2** | Новые режимы | ✅ **ГОТОВО** | ~5-7 дней |
| **2.3** | Формативное оценивание | ✅ **ГОТОВО** | ~5-7 дней |
| **2.4** | Продвинутая геймификация | Планируется | ~4-5 дней |
| **2.5** | Уникальные AI-фичи | Планируется | ~5-7 дней |

---

## Фаза 2.0 — MVP Live Quiz ✅ ГОТОВО

**Реализовано:** 2026-03-14

### Что реализовано

#### Backend

| Компонент | Файл | Описание |
|-----------|------|----------|
| Миграция | `backend/alembic/versions/052_quiz_sessions.py` | 3 таблицы + enum + RLS + GRANTS |
| Модели | `backend/app/models/quiz.py` | QuizSession, QuizParticipant, QuizAnswer |
| Схемы | `backend/app/schemas/quiz.py` | Create/Response/Join/Question/Results |
| Репозиторий | `backend/app/repositories/quiz_repo.py` | CRUD, leaderboard, stats |
| Сервис | `backend/app/services/quiz_service.py` | State machine, scoring, XP integration |
| REST API (teacher) | `backend/app/api/v1/teachers_quiz.py` | 7 endpoints (create, list, tests, detail, start, cancel, results) |
| REST API (student) | `backend/app/api/v1/students_quiz.py` | 2 endpoints (join, results) |
| WebSocket | `backend/app/api/v1/ws_quiz.py` | QuizConnectionManager, room broadcasting, JWT auth |
| XP enum | `backend/app/models/gamification.py` | Добавлен `QUIZ_BATTLE` в XpSourceType |

**Формула очков:** `score = round(1000 * max(0, 1 - answer_time / time_limit / 2))`
**XP:** участие +10, правильный +5, 1 место +50, 2 +30, 3 +15, perfect +25
**State machine:** lobby → in_progress → finished/cancelled

#### Student WebView

| Компонент | Файл |
|-----------|------|
| Layout (полноэкранный, token из URL) | `student-app/src/app/[locale]/webview/layout.tsx` |
| Quiz page (state machine) | `student-app/src/app/[locale]/webview/quiz/page.tsx` |
| WebSocket hook | `student-app/src/lib/hooks/use-quiz-websocket.ts` |
| API клиент | `student-app/src/lib/api/quiz.ts` |
| Типы | `student-app/src/types/quiz.ts` |
| QuizJoinScreen | `student-app/src/components/quiz/QuizJoinScreen.tsx` |
| QuizLobby | `student-app/src/components/quiz/QuizLobby.tsx` |
| QuizQuestion (4 цветные кнопки Kahoot-стиль) | `student-app/src/components/quiz/QuizQuestion.tsx` |
| QuizTimer (SVG circle countdown) | `student-app/src/components/quiz/QuizTimer.tsx` |
| QuizAnswered | `student-app/src/components/quiz/QuizAnswered.tsx` |
| QuizQuestionResult + MiniLeaderboard | `student-app/src/components/quiz/QuizQuestionResult.tsx` |
| QuizFinished (confetti для топ-3) | `student-app/src/components/quiz/QuizFinished.tsx` |
| Локализация ru + kk | `student-app/messages/ru.json`, `kk.json` → секция `quiz` |

#### Teacher Dashboard

| Компонент | Файл |
|-----------|------|
| Список квизов | `teacher-app/src/app/[locale]/(dashboard)/quiz/page.tsx` |
| Создание квиза | `teacher-app/src/app/[locale]/(dashboard)/quiz/create/page.tsx` |
| Управление (lobby/live/results) | `teacher-app/src/app/[locale]/(dashboard)/quiz/[id]/page.tsx` |
| QuizCreateForm (каскад: учебник→глава→параграф→тест) | `teacher-app/src/components/quiz/QuizCreateForm.tsx` |
| QuizLobbyTeacher (QR-код, список участников) | `teacher-app/src/components/quiz/QuizLobbyTeacher.tsx` |
| QuizLiveProgress (прогресс ответов, сетка учеников) | `teacher-app/src/components/quiz/QuizLiveProgress.tsx` |
| QuizResults (подиум, таблица, статистика) | `teacher-app/src/components/quiz/QuizResults.tsx` |
| API клиент | `teacher-app/src/lib/api/quiz.ts` |
| React Query хуки | `teacher-app/src/lib/hooks/use-quiz.ts` |
| WebSocket hook | `teacher-app/src/lib/hooks/use-quiz-websocket.ts` |
| Навигация (sidebar) | `teacher-app/src/app/[locale]/(dashboard)/layout.tsx` → navItems |
| Локализация ru + kz | `teacher-app/src/messages/ru/index.json`, `kz/index.json` → секция `quiz` |

---

## Фаза 2.1 — Улучшения Live Quiz ✅ ГОТОВО

> Зависимость: Фаза 2.0 ✅
> Реализовано: 2026-03-14

### 2.1.1 Answer Streak (серия правильных ответов) ✅

- Бонусы: 2 подряд +100, 3 +200, 4 +300, 5+ +500 (cap)
- Миграция: `054_quiz_streak_columns` — `current_streak`, `max_streak` в `quiz_participants`
- Backend: `submit_answer()` обновляет streak + начисляет бонусные очки
- Frontend: `QuizAnswered.tsx` показывает огонь 🔥 и бонус за серию
- WebSocket: `answer_accepted` включает `current_streak`, `max_streak`, `streak_bonus`

### 2.1.2 Shuffle (перемешивание) ✅

- `settings.shuffle_questions` / `settings.shuffle_answers` в JSONB
- Backend: детерминированный seed = session_id (вопросы) / session_id * 10000 + question_index (ответы)
- Одинаковый shuffle для _load_question и _check_answer → корректная проверка
- Teacher UI: чекбоксы в `QuizCreateForm.tsx`

### 2.1.3 Accuracy Mode ✅

- `settings.scoring_mode: "speed" | "accuracy"`
- Accuracy: 1000 очков за правильный, 0 за неправильный, без бонуса за скорость
- Teacher UI: dropdown в `QuizCreateForm.tsx`

### 2.1.4 Изображения в вопросах ✅

- `QuizQuestion.tsx` рендерит `image_url` если оно не null
- Пока Question модель не имеет image_url → поле остаётся null
- Готово к использованию когда вопросы получат изображения

### 2.1.5 Звуки и музыка ✅

- Процедурная генерация звуков через Web Audio API (без mp3 файлов)
- `QuizSoundManager` класс: `student-app/src/lib/quiz-sounds.ts`
- `useQuizSounds()` хук: `student-app/src/lib/hooks/use-quiz-sounds.ts`
- 9 звуков: lobby, questionAppear, tick, timeUp, correct, incorrect, streak, result, victory
- Триггеры: state transitions (page useEffect), timer urgent tick (QuizTimer), time expired (QuizQuestion)
- Кнопка mute (fixed, top-right) с сохранением в localStorage

### Шаги реализации

| Шаг | Задача | Статус |
|-----|--------|--------|
| 2.1.1 | Backend: streak logic + participant fields | ✅ |
| 2.1.2 | Frontend: streak отображение (огонь + бонус) | ✅ |
| 2.1.3 | Backend: shuffle logic (deterministic seed) | ✅ |
| 2.1.4 | Backend + Frontend: accuracy mode | ✅ |
| 2.1.5 | Frontend: image_url рендеринг | ✅ |
| 2.1.6 | Teacher: настройки квиза (shuffle, accuracy) | ✅ |
| 2.1.7 | Frontend: звуки (Web Audio API + хук + mute) | ✅ |

---

## Фаза 2.2 — Новые режимы игры ✅ ГОТОВО

> Зависимость: Фаза 2.0 ✅
> Реализовано: 2026-03-15

### 2.2.1 Team Mode ✅

- Миграция: `058_quiz_teams_and_modes` — таблица `quiz_teams`, `team_id` в participants, nullable `test_id`
- Модель: `QuizTeam` (name, color, total_score, correct_answers)
- `settings.mode: "team"`, `settings.team_count: 2-6`
- Авто-назначение команд: round-robin при join (команда с наименьшим количеством участников)
- 6 предустановленных команд: Red, Blue, Green, Yellow, Purple, Orange
- Агрегация очков команды после каждого ответа
- WS: `team_assigned` (при join), `team_progress` (учителю), `team_leaderboard` (всем)
- Сервис: `quiz_team_service.py`, Репозиторий: `quiz_team_repo.py`
- Frontend student: team badge в лобби, team leaderboard в результатах
- Frontend teacher: team_count selector в форме создания, team leaderboard в результатах
- REST: `GET /teachers/quiz-sessions/{id}/team-leaderboard`

### 2.2.2 Space Race ✅

- Надстройка над Team Mode: `settings.show_space_race: true`
- Визуализация: горизонтальный трек с ракетами, прогресс = correct_answers / total_questions
- Компонент: `teacher-app/src/components/quiz/SpaceRaceTrack.tsx`
- CSS transitions для плавного перемещения
- Данные из WS `team_progress`

### 2.2.3 Self-Paced Challenge ✅

- `settings.mode: "self_paced"`, scoring_mode автоматически "accuracy"
- REST API вместо WebSocket для вопросов (студент может делать перерывы)
- WS используется только для лобби/старт + уведомление учителю о прогрессе
- Сервис: `quiz_selfpaced_service.py`
- Student endpoints: `GET /{id}/next-question`, `POST /{id}/submit-answer`
- Teacher endpoint: `GET /{id}/student-progress`
- Frontend student: `QuizSelfPacedFeedback.tsx` — немедленная обратная связь с правильным ответом
- Frontend teacher: `QuizSelfPacedProgress.tsx` — progress bars по каждому ученику
- WS: `student_progress` (учителю после каждого ответа)

### 2.2.4 Quick Question ✅

- `settings.mode: "quick_question"`, `test_id = NULL`
- Учитель создаёт комнату → ученики подключаются → учитель отправляет вопрос через WS
- Ответы хранятся in-memory в QuizRoom (не в quiz_answers)
- WS: `quick_question` (broadcast), `quick_answer` (студент→сервер), `quick_response_update` (live bar chart), `end_quick_question`
- REST: `POST /teachers/quiz-sessions/quick-question`
- Frontend teacher: `quiz/quick/page.tsx` — создание + лобби + bar chart ответов
- Frontend student: `QuizQuickAnswer.tsx` — цветные кнопки A/B/C/D

### Шаги реализации

| Шаг | Задача | Статус |
|-----|--------|--------|
| 2.2.1 | Backend: quiz_teams таблица + миграция | ✅ |
| 2.2.2 | Backend: team assignment + team scoring | ✅ |
| 2.2.3 | Frontend: Team Mode UI (student + teacher) | ✅ |
| 2.2.4 | Frontend: Space Race визуализация | ✅ |
| 2.2.5 | Backend: self-paced mode (service + REST) | ✅ |
| 2.2.6 | Frontend: Self-Paced quiz page | ✅ |
| 2.2.7 | Teacher: self-paced dashboard | ✅ |
| 2.2.8 | Backend + Frontend: Quick Question | ✅ |
| 2.2.9 | Локализация (ru/kk/kz) | ✅ |

---

## Фаза 2.3 — Формативное оценивание ✅ ГОТОВО

> Зависимость: Фаза 2.0 ✅
> Реализовано: 2026-03-15

### 2.3.1 Teacher Paced Mode ✅

- `settings.pacing: "timed" | "teacher_paced"`
- Без таймера, возможность вернуться к предыдущему вопросу
- WS: `go_to_question` с произвольным index
- Ученики могут перезаписать ответ при возврате учителя к вопросу
- Сервис: `quiz_service.py` → `go_to_question()`, `reverse_answer_score()`
- WS Handler: `ws_quiz_handlers.py` → `handle_go_to_question()`
- Frontend teacher: `QuizTeacherPacedProgress.tsx` — навигация по вопросам
- Frontend teacher: pacing selector в `QuizCreateForm.tsx`

### 2.3.2 Exit Ticket ✅

- 3 фиксированных вопроса: самооценка, рефлексия (текст), вопрос по теме
- `settings.mode: "exit_ticket"`, всегда teacher_paced
- Сервис: `quiz_exit_ticket_service.py`
- Интеграция с `paragraph_self_assessments` через `SelfAssessmentService`
- Миграция: `059_short_answer_and_exit_ticket` — `paragraph_id` в `quiz_sessions`
- REST: `POST /teachers/quiz-sessions/exit-ticket`, `POST /{id}/exit-ticket/finalize`

### 2.3.3 Live Results Matrix ✅

- Матрица Ученик × Вопрос (зелёный/красный/серый)
- `QuizLiveMatrix.tsx`, endpoint `GET /quiz-sessions/{id}/matrix`
- API файл: `teachers_quiz_analytics.py` (вынесено из teachers_quiz.py)
- Auto-refresh через React Query (5s)
- Отображается во время квиза и после завершения

### 2.3.4 Short Answer ✅

- `quiz_answers.text_answer: TEXT`
- Проверка: exact match → fuzzy match (0.85) → LLM fallback (5s timeout)
- Сервис: `quiz_short_answer_service.py`
- `QuizShortAnswer.tsx` — текстовый input вместо цветных кнопок
- `QuizQuestionOut.question_type: "single_choice" | "short_answer"`
- WS answer: `text_answer` поле в data

### 2.3.5 Отчёты ✅

- По классу (XLSX), по вопросам (XLSX), тренды (XLSX)
- `quiz_report_service.py` + `openpyxl`
- API: `teachers_quiz_reports.py` — StreamingResponse XLSX
- Frontend: `QuizReportDownloads.tsx` — кнопки скачивания

### Шаги реализации

| Шаг | Задача | Статус |
|-----|--------|--------|
| 2.3.1 | Backend: teacher_paced mode | ✅ |
| 2.3.2 | Frontend: teacher_paced UI | ✅ |
| 2.3.3 | Backend + Frontend: Exit Ticket | ✅ |
| 2.3.4 | Exit Ticket интеграция с self-assessment | ✅ |
| 2.3.5 | Frontend: QuizLiveMatrix | ✅ |
| 2.3.6 | Backend: short_answer + check logic | ✅ |
| 2.3.7 | AI-проверка short answer через LLM | ✅ |
| 2.3.8 | Frontend: QuizShortAnswer | ✅ |
| 2.3.9 | Backend: отчёты (XLSX) | ✅ |
| 2.3.10 | Teacher: UI скачивания отчётов | ✅ |

---

## Фаза 2.4 — Продвинутая геймификация

> Ключевые файлы: `quiz_service.py`, `QuizQuestion.tsx`, `QuizFinished.tsx`

### 2.4.1 Power-ups

| Power-up | Эффект | Стоимость |
|----------|--------|-----------|
| Double Points | x2 очки за вопрос | 50 XP |
| 50/50 | Убирает 2 варианта | 75 XP |
| Time Freeze | +10 сек | 40 XP |
| Shield | Серия не сбрасывается | 60 XP |

- Таблица `quiz_participant_powerups`, один power-up за вопрос

### 2.4.2 Confidence Mode

- "Рискну" (speed-based) vs "Безопасно" (500 фиксированных), стратегический элемент

### 2.4.3 Подиум с анимацией

- `QuizPodium.tsx`, countdown 3→2→1, конфетти, медали, фанфары

### 2.4.4 Еженедельный турнир

- Cron (пятница 15:00) → auto-генерация квиза по пройденному за неделю
- Self-paced, рейтинг между классами, +100/+200 XP

### Шаги реализации

| Шаг | Задача | Зависимости |
|-----|--------|-------------|
| 2.4.1 | Backend: power-ups (таблица, activate, apply) | ✅ 2.0 |
| 2.4.2 | Frontend: power-ups UI | 2.4.1 |
| 2.4.3 | Backend: confidence mode logic | ✅ 2.0 |
| 2.4.4 | Frontend: confidence choice UI | 2.4.3 |
| 2.4.5 | Frontend: QuizPodium + звук | ✅ 2.0 |
| 2.4.6 | Backend: weekly tournament cron | ✅ 2.0, 2.2.5 |
| 2.4.7 | Frontend: tournament banner + leaderboard | 2.4.6 |

---

## Фаза 2.5 — Уникальные AI-фичи

> Ключевые файлы: `quiz_service.py`, `llm_service.py`, `teachers_quiz.py`

### 2.5.1 AI-генерация квизов

- Учитель выбирает параграф → LLM генерирует вопросы → предпросмотр → утверждение
- `POST /teachers/quiz-sessions/generate`, `QuizAIGenerate.tsx`

### 2.5.2 Адаптивная сложность

- Вопросы по mastery ученика, `score_multiplier = 0.5 + difficulty`

### 2.5.3 Интеграция с Mastery

- В `finish_session()` обновить `paragraph_mastery` по результатам квиза
- Teacher: "Пробелы класса" после квиза

### 2.5.4 Межклассовые соревнования

- `quiz_sessions.class_ids: INT[]`, рейтинг между классами

### 2.5.5 Родительский отчёт

- Push-уведомление после квиза через Firebase/SMS

### Шаги реализации

| Шаг | Задача | Зависимости |
|-----|--------|-------------|
| 2.5.1 | Backend: AI-генерация вопросов | ✅ 2.0 |
| 2.5.2 | Teacher: UI генерации + редактирование | 2.5.1 |
| 2.5.3 | Backend: adaptive difficulty | ✅ 2.0 |
| 2.5.4 | Backend: mastery integration | ✅ 2.0 |
| 2.5.5 | Teacher: "Пробелы класса" | 2.5.4 |
| 2.5.6 | Backend: multi-class quiz | ✅ 2.0 |
| 2.5.7 | Frontend: межклассовый лидерборд | 2.5.6 |
| 2.5.8 | Backend: parent notifications | ✅ 2.0 |

---

## Сравнение с конкурентами

### Что берём от Kahoot

| Фича | Фаза | Статус |
|------|------|--------|
| Вход по коду, speed scoring, 4 цветных варианта | 2.0 | ✅ |
| Лидерборд, подиум топ-3, QR-код | 2.0 | ✅ |
| Answer Streak, Shuffle, Accuracy Mode, Звуки | 2.1 | ✅ |
| Team Mode, Self-Paced Challenge | 2.2 | ✅ |
| Power-ups, Confidence Mode | 2.4 | |

### Что берём от Socrative

| Фича | Фаза | Статус |
|------|------|--------|
| Teacher Paced, Exit Ticket, Live Matrix | 2.3 | ✅ |
| Short Answer, Отчёты (XLSX) | 2.3 | ✅ |
| Space Race, Quick Question | 2.2 | ✅ |

### Наши уникальные фичи

| Фича | Фаза | Статус |
|------|------|--------|
| XP геймификация (квиз = источник XP) | 2.0 | ✅ |
| AI-генерация квизов | 2.5 | |
| Адаптивная сложность по mastery | 2.5 | |
| AI Short Answer (LLM-проверка) | 2.3 | ✅ |
| Межклассовые баттлы | 2.5 | |
| Еженедельный турнир | 2.4 | |
| Родительский отчёт | 2.5 | |
| Видео-анимации (Remotion) | 3.0 | |

---

## Структура файлов (текущая + планируемая)

```
backend/
├── alembic/versions/
│   ├── 052_quiz_sessions.py              ← ✅ Фаза 2.0
│   ├── 054_quiz_streak_columns.py        ← ✅ Фаза 2.1
│   ├── 057_quiz_timestamp_columns.py     ← ✅ Фаза 2.1
│   ├── 058_quiz_teams_and_modes.py       ← ✅ Фаза 2.2
│   ├── 059_short_answer_and_exit_ticket.py ← ✅ Фаза 2.3
│   └── ???_quiz_powerups.py              ← Фаза 2.4
├── app/
│   ├── models/quiz.py                    ← ✅ QuizSession, QuizTeam, QuizParticipant, QuizAnswer
│   ├── schemas/quiz.py                   ← ✅ classic/team/self_paced/quick_question schemas
│   ├── repositories/
│   │   ├── quiz_repo.py                  ← ✅
│   │   └── quiz_team_repo.py             ← ✅ Фаза 2.2
│   ├── services/
│   │   ├── quiz_service.py               ← ✅ mode-aware create/join
│   │   ├── quiz_team_service.py          ← ✅ Фаза 2.2
│   │   ├── quiz_selfpaced_service.py     ← ✅ Фаза 2.2
│   │   ├── quiz_short_answer_service.py ← ✅ Фаза 2.3 (exact+fuzzy+LLM)
│   │   ├── quiz_exit_ticket_service.py  ← ✅ Фаза 2.3
│   │   └── quiz_report_service.py       ← ✅ Фаза 2.3 (XLSX reports)
│   └── api/v1/
│       ├── teachers_quiz.py              ← ✅ +quick-question, student-progress, team-leaderboard
│       ├── teachers_quiz_analytics.py    ← ✅ Фаза 2.3 (matrix, exit-ticket)
│       ├── teachers_quiz_reports.py      ← ✅ Фаза 2.3 (XLSX downloads)
│       ├── students_quiz.py              ← ✅ +next-question, submit-answer
│       ├── ws_quiz.py                    ← ✅ +team/quick/go_to_question routing
│       └── ws_quiz_handlers.py           ← ✅ +go_to_question handler

student-app/src/
├── app/[locale]/webview/
│   ├── layout.tsx                        ← ✅
│   └── quiz/page.tsx                     ← ✅ +team/self_paced/quick states
├── components/quiz/
│   ├── QuizJoinScreen.tsx                ← ✅
│   ├── QuizLobby.tsx                     ← ✅ +team badge
│   ├── QuizQuestion.tsx                  ← ✅ +hideTimer prop
│   ├── QuizTimer.tsx                     ← ✅
│   ├── QuizAnswered.tsx                  ← ✅
│   ├── QuizQuestionResult.tsx            ← ✅ +team leaderboard
│   ├── QuizMiniLeaderboard.tsx           ← ✅
│   ├── QuizFinished.tsx                  ← ✅ +team results
│   ├── QuizTeamBadge.tsx                 ← ✅ Фаза 2.2
│   ├── QuizQuickAnswer.tsx              ← ✅ Фаза 2.2
│   ├── QuizSelfPacedFeedback.tsx         ← ✅ Фаза 2.2
│   ├── QuizShortAnswer.tsx               ← ✅ Фаза 2.3
│   └── QuizPodium.tsx                    ← Фаза 2.4
├── lib/
│   ├── api/quiz.ts                       ← ✅ +self-paced endpoints
│   ├── quiz-sounds.ts                    ← ✅
│   └── hooks/
│       ├── use-quiz-websocket.ts         ← ✅
│       └── use-quiz-sounds.ts            ← ✅
├── types/quiz.ts                         ← ✅ +team/quick/self-paced types

teacher-app/src/
├── app/[locale]/(dashboard)/quiz/
│   ├── page.tsx                          ← ✅ +Quick Question button
│   ├── create/page.tsx                   ← ✅
│   ├── [id]/page.tsx                     ← ✅ +mode-based rendering
│   └── quick/page.tsx                    ← ✅ Фаза 2.2
├── components/quiz/
│   ├── QuizCreateForm.tsx                ← ✅ +mode selector, team settings, pacing
│   ├── QuizLobbyTeacher.tsx              ← ✅
│   ├── QuizLiveProgress.tsx              ← ✅
│   ├── QuizTeacherPacedProgress.tsx      ← ✅ Фаза 2.3
│   ├── QuizLiveMatrix.tsx                ← ✅ Фаза 2.3
│   ├── QuizReportDownloads.tsx           ← ✅ Фаза 2.3
│   ├── QuizResults.tsx                   ← ✅
│   ├── SpaceRaceTrack.tsx                ← ✅ Фаза 2.2
│   ├── QuizSelfPacedProgress.tsx         ← ✅ Фаза 2.2
│   ├── QuizLiveMatrix.tsx                ← Фаза 2.3
│   ├── QuizReportDownload.tsx            ← Фаза 2.3
│   └── QuizAIGenerate.tsx                ← Фаза 2.5
└── lib/
    ├── api/quiz.ts                       ← ✅ +quick, progress, team APIs
    └── hooks/
        ├── use-quiz.ts                   ← ✅ +useStudentProgress, useTeamLeaderboard
        └── use-quiz-websocket.ts         ← ✅ +sendQuickQuestion
```

---

## Приоритизация

**Рекомендуемый порядок после MVP:**

1. **Фаза 2.1** (Улучшения) — быстрые wins, улучшают engagement
2. **Фаза 2.3** (Оценивание) — ценность для учителей, retention
3. **Фаза 2.2** (Режимы) — разнообразие, viral-потенциал
4. **Фаза 2.5** (AI-фичи) — уникальность, конкурентное преимущество
5. **Фаза 2.4** (Геймификация) — polish, wow-эффект

Приоритеты могут меняться в зависимости от обратной связи учителей после запуска MVP.
