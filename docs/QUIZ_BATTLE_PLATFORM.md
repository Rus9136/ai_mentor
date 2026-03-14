# Quiz Battle Platform — Полный план разработки

> Дата: 2026-03-14
> Статус: **Фаза 2.0 — РЕАЛИЗОВАНА** (коммит `0227d71`, деплой 2026-03-14)
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
| **2.1** | Улучшения Live Quiz | ✅ **ЧАСТИЧНО** (2.1.1-2.1.4) | ~3-4 дня |
| **2.2** | Новые режимы | Планируется | ~5-7 дней |
| **2.3** | Формативное оценивание | Планируется | ~5-7 дней |
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

## Фаза 2.1 — Улучшения Live Quiz (частично ✅)

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

### 2.1.5 Звуки и музыка

- Файлы: `student-app/public/sounds/quiz/*.mp3`
- Хук: `useQuizSounds()` через Web Audio API
- Моменты: лобби, вопрос, таймер <5с, правильный/неправильный, лидерборд, подиум
- Кнопка mute

### Шаги реализации

| Шаг | Задача | Статус |
|-----|--------|--------|
| 2.1.1 | Backend: streak logic + participant fields | ✅ |
| 2.1.2 | Frontend: streak отображение (огонь + бонус) | ✅ |
| 2.1.3 | Backend: shuffle logic (deterministic seed) | ✅ |
| 2.1.4 | Backend + Frontend: accuracy mode | ✅ |
| 2.1.5 | Frontend: image_url рендеринг | ✅ |
| 2.1.6 | Teacher: настройки квиза (shuffle, accuracy) | ✅ |
| 2.1.7 | Frontend: звуки (файлы + хук + mute) | ❌ |

---

## Фаза 2.2 — Новые режимы игры

> Ключевые файлы: `quiz_service.py`, `ws_quiz.py`, `quiz_repo.py`

### 2.2.1 Team Mode

- Таблица `quiz_teams` (id, quiz_session_id, name, color, total_score)
- `quiz_participants.team_id` FK
- 5 сек "Team Talk" перед вопросом, очки суммируются по команде
- Лидерборд по командам

### 2.2.2 Space Race

- Визуализация: ракеты двигаются по дорожке при правильных ответах
- `SpaceRaceTrack.tsx`, WS: `team_progress`

### 2.2.3 Self-Paced Challenge

- `settings.mode: "live" | "self_paced"`, `settings.deadline: datetime`
- REST API вместо WebSocket, accuracy mode, прогресс сохраняется
- Teacher: прогресс по ученикам

### 2.2.4 Quick Question

- Устный вопрос → A/B/C/D или текст на телефоне → bar chart у учителя
- In-memory, не сохраняется в историю

### Шаги реализации

| Шаг | Задача | Зависимости |
|-----|--------|-------------|
| 2.2.1 | Backend: quiz_teams таблица + миграция | ✅ 2.0 |
| 2.2.2 | Backend: team assignment + team scoring | 2.2.1 |
| 2.2.3 | Frontend: Team Mode UI | 2.2.2 |
| 2.2.4 | Frontend: Space Race визуализация | 2.2.2 |
| 2.2.5 | Backend: self-paced mode | ✅ 2.0 |
| 2.2.6 | Frontend: Self-Paced quiz page | 2.2.5 |
| 2.2.7 | Teacher: self-paced dashboard | 2.2.5 |
| 2.2.8 | Backend + Frontend: Quick Question | ✅ 2.0 |

---

## Фаза 2.3 — Формативное оценивание

> Ключевые файлы: `quiz_service.py`, `ws_quiz.py`, `teachers_quiz.py`

### 2.3.1 Teacher Paced Mode

- `settings.pacing: "timed" | "teacher_paced"`
- Без таймера, возможность вернуться к предыдущему вопросу
- WS: `go_to_question` с произвольным index

### 2.3.2 Exit Ticket

- 3 фиксированных вопроса в конце урока (понимание, интересное/сложное, по теме)
- Интеграция с `paragraph_self_assessments`

### 2.3.3 Live Results Matrix

- Матрица Ученик × Вопрос (зелёный/красный/серый)
- `QuizLiveMatrix.tsx`, endpoint `GET /quiz-sessions/{id}/matrix`

### 2.3.4 Short Answer

- `quiz_answers.text_answer: TEXT`
- Проверка: exact + fuzzy + LLM fallback
- `QuizShortAnswer.tsx`, голосование за лучший ответ

### 2.3.5 Отчёты

- По классу (XLSX), по ученику (PDF), по вопросу (PDF), трендовый (XLSX)
- `quiz_report_service.py`, `openpyxl` / `weasyprint`

### Шаги реализации

| Шаг | Задача | Зависимости |
|-----|--------|-------------|
| 2.3.1 | Backend: teacher_paced mode | ✅ 2.0 |
| 2.3.2 | Frontend: teacher_paced UI | 2.3.1 |
| 2.3.3 | Backend + Frontend: Exit Ticket | ✅ 2.0 |
| 2.3.4 | Exit Ticket интеграция с self-assessment | 2.3.3 |
| 2.3.5 | Frontend: QuizLiveMatrix | ✅ 2.0 |
| 2.3.6 | Backend: short_answer + check logic | ✅ 2.0 |
| 2.3.7 | AI-проверка short answer через LLM | 2.3.6 |
| 2.3.8 | Frontend: QuizShortAnswer + голосование | 2.3.6 |
| 2.3.9 | Backend: отчёты (XLSX + PDF) | ✅ 2.0 |
| 2.3.10 | Teacher: UI скачивания отчётов | 2.3.9 |

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
| Answer Streak, Shuffle, Accuracy Mode, Звуки | 2.1 | |
| Team Mode, Self-Paced Challenge | 2.2 | |
| Power-ups, Confidence Mode | 2.4 | |

### Что берём от Socrative

| Фича | Фаза | Статус |
|------|------|--------|
| Teacher Paced, Exit Ticket, Live Matrix | 2.3 | |
| Short Answer, Отчёты (XLSX/PDF) | 2.3 | |
| Space Race, Quick Question | 2.2 | |

### Наши уникальные фичи

| Фича | Фаза | Статус |
|------|------|--------|
| XP геймификация (квиз = источник XP) | 2.0 | ✅ |
| AI-генерация квизов | 2.5 | |
| Адаптивная сложность по mastery | 2.5 | |
| AI Short Answer (LLM-проверка) | 2.3 | |
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
│   ├── 053_quiz_teams.py                 ← Фаза 2.2
│   └── 054_quiz_powerups.py              ← Фаза 2.4
├── app/
│   ├── models/quiz.py                    ← ✅
│   ├── schemas/quiz.py                   ← ✅
│   ├── repositories/quiz_repo.py         ← ✅
│   ├── services/
│   │   ├── quiz_service.py               ← ✅
│   │   └── quiz_report_service.py        ← Фаза 2.3
│   └── api/v1/
│       ├── teachers_quiz.py              ← ✅
│       ├── students_quiz.py              ← ✅
│       └── ws_quiz.py                    ← ✅

student-app/src/
├── app/[locale]/webview/
│   ├── layout.tsx                        ← ✅
│   └── quiz/page.tsx                     ← ✅
├── components/quiz/
│   ├── QuizJoinScreen.tsx                ← ✅
│   ├── QuizLobby.tsx                     ← ✅
│   ├── QuizQuestion.tsx                  ← ✅
│   ├── QuizTimer.tsx                     ← ✅
│   ├── QuizAnswered.tsx                  ← ✅
│   ├── QuizQuestionResult.tsx            ← ✅
│   ├── QuizMiniLeaderboard.tsx           ← ✅
│   ├── QuizFinished.tsx                  ← ✅
│   ├── QuizShortAnswer.tsx               ← Фаза 2.3
│   ├── QuizPodium.tsx                    ← Фаза 2.4
│   └── SpaceRaceTrack.tsx                ← Фаза 2.2
└── lib/
    ├── api/quiz.ts                       ← ✅
    └── hooks/
        ├── use-quiz-websocket.ts         ← ✅
        └── use-quiz-sounds.ts            ← Фаза 2.1

teacher-app/src/
├── app/[locale]/(dashboard)/quiz/
│   ├── page.tsx                          ← ✅
│   ├── create/page.tsx                   ← ✅
│   └── [id]/page.tsx                     ← ✅
├── components/quiz/
│   ├── QuizCreateForm.tsx                ← ✅
│   ├── QuizLobbyTeacher.tsx              ← ✅
│   ├── QuizLiveProgress.tsx              ← ✅
│   ├── QuizResults.tsx                   ← ✅
│   ├── QuizLiveMatrix.tsx                ← Фаза 2.3
│   ├── QuizReportDownload.tsx            ← Фаза 2.3
│   └── QuizAIGenerate.tsx                ← Фаза 2.5
└── lib/
    ├── api/quiz.ts                       ← ✅
    └── hooks/
        ├── use-quiz.ts                   ← ✅
        └── use-quiz-websocket.ts         ← ✅
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
