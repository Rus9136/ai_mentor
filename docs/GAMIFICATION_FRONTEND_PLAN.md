# Gamification Frontend — План реализации

> Дата: 2026-03-13
> Статус: **Фаза 1 — РЕАЛИЗОВАНА** (коммит 4a94d50)
> Backend: полностью реализован (миграция 050, 6 student + 1 teacher endpoint)

---

## Обзор

Два направления геймификации:

| Направление | Где показывать | Назначение |
|-------------|---------------|------------|
| **Фаза 1** — Уровень, XP, ачивки, стрик, квесты | Нативно (student-app, teacher-app) | Постоянная мотивация | **ГОТОВО** |
| **Фаза 2** — Живые соревнования (квизы) | WebView (в мобилке) | Событийная мотивация на уроке | **MVP ГОТОВО** |

---

## Фаза 1 — Нативная геймификация ✅ ГОТОВО

**Цель:** ученик всегда видит свой прогресс — уровень растёт при прохождении параграфов и тестов.

**Статус:** Реализовано 2026-03-13 (коммит `4a94d50`)

### Что реализовано

| Компонент | Файл | Статус |
|-----------|------|--------|
| API клиент (6 endpoints) | `src/lib/api/gamification.ts` | ✅ |
| React Query хуки | `src/lib/hooks/use-gamification.ts` | ✅ |
| TypeScript типы | `src/types/gamification.ts` | ✅ |
| Zustand store (XP toast) | `src/stores/gamification-store.ts` | ✅ |
| XpProgressBar | `src/components/gamification/XpProgressBar.tsx` | ✅ |
| StreakBadge | `src/components/gamification/StreakBadge.tsx` | ✅ |
| XpLevelWidget (на главной) | `src/components/gamification/XpLevelWidget.tsx` | ✅ |
| AchievementCard + Grid | `src/components/gamification/Achievement*.tsx` | ✅ |
| Leaderboard + TopThree | `src/components/gamification/Leaderboard*.tsx` | ✅ |
| DailyQuests + Card | `src/components/gamification/DailyQuest*.tsx` | ✅ |
| XpToast (уведомление +XP) | `src/components/gamification/XpToast.tsx` | ✅ |
| AchievementPopup (polling) | `src/components/gamification/AchievementPopup.tsx` | ✅ |
| Страница /gamification (4 таба) | `src/app/[locale]/(app)/gamification/page.tsx` | ✅ |
| Навигация (sidebar + bottom nav) | `AppSidebar.tsx`, `MobileBottomNav.tsx` | ✅ |
| Локализация (ru + kk) | `messages/ru.json`, `messages/kk.json` | ✅ |
| Teacher-app: лидерборд класса | — | ❌ (Фаза 1.11, отложено) |

### 1.1 API-клиент (student-app)

**Файл:** `student-app/src/lib/api/gamification.ts`

```typescript
// Методы:
getGamificationProfile()        // GET /students/gamification/profile
getAchievements()               // GET /students/gamification/achievements
getRecentAchievements()         // GET /students/gamification/achievements/recent
getLeaderboard(scope, classId?) // GET /students/gamification/leaderboard
getDailyQuests()                // GET /students/gamification/daily-quests
getXpHistory(days?)             // GET /students/gamification/xp-history
```

**Файл:** `student-app/src/lib/hooks/use-gamification.ts`

```typescript
// React Query хуки:
useGamificationProfile()
useAchievements()
useRecentAchievements()   // polling каждые 30 сек
useLeaderboard(scope, classId?)
useDailyQuests()
useXpHistory(days?)
```

### 1.2 Виджет уровня на главной странице

**Где:** `student-app/src/app/[locale]/(app)/home/page.tsx` — вставить в верхнюю часть дашборда

**Компонент:** `student-app/src/components/gamification/XpLevelWidget.tsx`

Содержание:
- Номер уровня (крупно)
- Прогресс-бар XP до следующего уровня (цветной, анимированный)
- Текущий XP / нужный XP (текстом под баром)
- Иконка стрика (огонёк) + число дней
- Кнопка → переход на полный профиль геймификации

```
┌─────────────────────────────────────────┐
│  ⭐ Уровень 5       🔥 12 дней подряд  │
│  ████████████░░░░░░░  1,240 / 1,837 XP │
└─────────────────────────────────────────┘
```

### 1.3 Страница профиля геймификации

**Роут:** `student-app/src/app/[locale]/(app)/gamification/page.tsx`

**Секции (табы или scroll-секции):**

#### Tab 1 — Профиль
- Уровень + XP прогресс-бар (крупнее чем виджет)
- Стрик (текущий / рекорд)
- Общая статистика: тестов пройдено, параграфов освоено

#### Tab 2 — Ачивки
**Компонент:** `AchievementGrid.tsx`
- Карточки 3 в ряд (mobile: 2 в ряд)
- Earned: цветная иконка + название + дата получения
- Locked: серая иконка + прогресс-бар (0.6 = 60%)
- Редкость: обводка карточки (common=серый, rare=синий, epic=фиолетовый, legendary=золотой)

```
┌──────────┐ ┌──────────┐ ┌──────────┐
│ 🏆 color │ │ 🎯 color │ │ 🔒 gray  │
│ Первый   │ │ 10 тестов│ │ 50 тестов│
│ тест     │ │ Пройдено │ │ ████░ 60%│
│ ✅ 12.03 │ │ ✅ 13.03 │ │          │
└──────────┘ └──────────┘ └──────────┘
```

#### Tab 3 — Лидерборд
**Компонент:** `Leaderboard.tsx`
- Переключатель: Школа / Класс
- Топ-3 с выделением (крупные аватары/медали)
- Остальные — таблица (ранг, имя, уровень, XP)
- Текущий ученик подсвечен в списке
- Если ученик не в топ-50 — его позиция показана внизу отдельно

```
┌─────────────────────────────┐
│  [Школа]  [Класс]          │
│                             │
│  🥇 Айдана    Ур.8  2,450  │
│  🥈 Олжас     Ур.7  2,180  │
│  🥉 Дана      Ур.7  1,950  │
│  ─────────────────────────  │
│  4. Бекзат    Ур.6  1,820  │
│  5. Арман     Ур.5  1,640  │
│ ▸6. Ты        Ур.5  1,240◂ │ ← подсветка
│  7. Камила    Ур.4  1,100  │
└─────────────────────────────┘
```

#### Tab 4 — Ежедневные квесты
**Компонент:** `DailyQuests.tsx`
- Карточки квестов с прогресс-баром
- Завершённые — галочка + XP награда
- Незавершённые — прогресс (1/3)

```
┌─────────────────────────────────┐
│ 📝 Пройди 3 теста     +30 XP   │
│ ████████░░░░  2/3               │
├─────────────────────────────────┤
│ ✅ Освой параграф     +20 XP   │
│ ████████████  1/1  Готово!      │
└─────────────────────────────────┘
```

### 1.4 XP Toast (уведомление о начислении)

**Компонент:** `student-app/src/components/gamification/XpToast.tsx`

- Появляется после прохождения теста / mastery change
- Показывает "+25 XP" с анимацией (fly-up)
- При level-up: расширенный toast "Уровень 6! 🎉"

**Механизм:**
- После mutation (тест пройден, self-assessment) → refetch gamification profile
- Сравнить XP до/после → показать разницу в toast
- Хранить prev_xp в zustand store

### 1.5 Popup новой ачивки

**Компонент:** `student-app/src/components/gamification/AchievementPopup.tsx`

- Polling `GET /achievements/recent` каждые 30 секунд (через React Query refetchInterval)
- При получении новых ачивок — модалка с анимацией
- Иконка + название + описание + XP награда

### 1.6 Мини-бар XP в навигации

**Где:** `student-app/src/components/layout/MobileBottomNav.tsx` или `TopBar.tsx`

- Компактный уровень + XP бар (тонкая полоска)
- Видно на каждой странице
- Кликабельный → переход на /gamification

### 1.7 Teacher-app: Лидерборд класса

**Роут:** `teacher-app/src/app/[locale]/(app)/classes/[id]/leaderboard/page.tsx`

- Таблица рейтинга учеников класса (имя, уровень, XP, стрик)
- API: `GET /teachers/gamification/class/{class_id}/leaderboard`
- Доступ из страницы класса (новый таб или кнопка)

### 1.8 Локализация

Добавить ключи в оба файла:
- `student-app/messages/ru.json` → секция `gamification.*`
- `student-app/messages/kk.json` → секция `gamification.*`

Ключи:
```json
{
  "gamification": {
    "level": "Уровень",
    "xpProgress": "{current} / {total} XP",
    "streak": "{days} дней подряд",
    "achievements": "Достижения",
    "leaderboard": "Рейтинг",
    "dailyQuests": "Ежедневные задания",
    "school": "Школа",
    "class": "Класс",
    "earned": "Получено",
    "locked": "Заблокировано",
    "xpAwarded": "+{amount} XP",
    "levelUp": "Уровень {level}!",
    "questComplete": "Задание выполнено!",
    "yourRank": "Твоё место: {rank}",
    "xpHistory": "История XP",
    "noAchievements": "Пока нет достижений",
    "keepLearning": "Продолжай учиться!"
  }
}
```

### 1.9 Структура файлов (Фаза 1)

```
student-app/src/
├── lib/
│   ├── api/gamification.ts              ← API клиент
│   └── hooks/use-gamification.ts        ← React Query хуки
├── components/gamification/
│   ├── XpLevelWidget.tsx                ← Виджет для home
│   ├── XpProgressBar.tsx                ← Переиспользуемый прогресс-бар
│   ├── AchievementGrid.tsx              ← Сетка ачивок
│   ├── AchievementCard.tsx              ← Карточка одной ачивки
│   ├── AchievementPopup.tsx             ← Модалка новой ачивки
│   ├── Leaderboard.tsx                  ← Таблица рейтинга
│   ├── LeaderboardTopThree.tsx          ← Топ-3 с медалями
│   ├── DailyQuests.tsx                  ← Список квестов
│   ├── DailyQuestCard.tsx               ← Карточка квеста
│   ├── StreakBadge.tsx                   ← Иконка стрика
│   └── XpToast.tsx                      ← Toast +XP
├── app/[locale]/(app)/
│   └── gamification/
│       └── page.tsx                     ← Полная страница
└── stores/
    └── gamification-store.ts            ← Zustand (prev_xp для toast)
```

---

## Фаза 2 — Живые соревнования (Quiz Battle) ✅ MVP ГОТОВО

**Цель:** учитель запускает квиз на уроке → ученики соревнуются в реальном времени → зарабатывают XP.

**Статус MVP:** Реализовано 2026-03-14 (коммит `0227d71`)

**Полный план:** [`docs/QUIZ_BATTLE_PLATFORM.md`](./QUIZ_BATTLE_PLATFORM.md) — 6 фаз (MVP + 5 расширений), сравнение с Kahoot/Socrative, уникальные AI-фичи.

### 2.1 Концепция

```
Учитель (teacher-app)              Ученики (WebView в мобилке)

1. Выбирает тест из учебника
2. Создаёт Quiz Session
3. Показывает код: 4829            → 4. Вводят код / сканируют QR
5. Видит кто подключился           ← 6. Лобби "Ждём старта..."
7. Нажимает "Начать"               → 8. Вопрос 1 появляется у всех
9. Видит прогресс в реальном       ← 10. Отвечают (таймер общий)
   времени (кто ответил,
   кто правильно)
11. Следующий вопрос               → 12. Мини-лидерборд между вопросами
13. Финальные результаты           ← 14. Итоговое место + XP
```

### 2.2 Backend — Новые модели

**Миграция:** `051_quiz_sessions`

#### Таблица `quiz_sessions`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | SERIAL PK | |
| school_id | INT FK | Школа |
| teacher_id | INT FK | Учитель-создатель |
| class_id | INT FK | Класс (опционально) |
| test_id | INT FK | Тест-источник вопросов |
| join_code | VARCHAR(6) UNIQUE | Код для входа (4-6 цифр) |
| status | ENUM | draft → lobby → in_progress → finished → cancelled |
| settings | JSONB | Настройки (time_per_question, show_leaderboard_after_each, etc.) |
| question_count | INT | Число вопросов |
| current_question_index | INT | Текущий вопрос (0-based) |
| started_at | TIMESTAMP | Начало квиза |
| finished_at | TIMESTAMP | Конец квиза |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### Таблица `quiz_participants`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | SERIAL PK | |
| quiz_session_id | INT FK | Сессия |
| student_id | INT FK | Ученик |
| school_id | INT FK | Школа |
| total_score | INT DEFAULT 0 | Очки в этом квизе |
| correct_answers | INT DEFAULT 0 | Правильных ответов |
| rank | INT | Итоговое место |
| xp_earned | INT DEFAULT 0 | XP начисленный после квиза |
| joined_at | TIMESTAMP | Когда подключился |
| finished_at | TIMESTAMP | |

#### Таблица `quiz_answers`

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | SERIAL PK | |
| quiz_session_id | INT FK | Сессия |
| participant_id | INT FK | Участник |
| school_id | INT FK | Школа |
| question_index | INT | Номер вопроса (0-based) |
| selected_option | INT | Выбранный вариант |
| is_correct | BOOLEAN | Правильно ли |
| answer_time_ms | INT | Время ответа в мс |
| score | INT | Очки за этот вопрос |
| answered_at | TIMESTAMP | |

### 2.3 Backend — Quiz Score Formula

Очки за вопрос в квизе (не путать с XP):

```python
MAX_QUESTION_SCORE = 1000
TIME_LIMIT_MS = 30_000  # настраивается учителем

def calculate_question_score(is_correct: bool, answer_time_ms: int, time_limit_ms: int) -> int:
    if not is_correct:
        return 0
    # Быстрый ответ = больше очков (Kahoot-формула)
    time_factor = max(0, 1 - (answer_time_ms / time_limit_ms) / 2)
    return round(MAX_QUESTION_SCORE * time_factor)
```

Пример: правильный ответ за 5 сек (лимит 30 сек) → `1000 * (1 - 0.083) = 917 очков`

**XP после квиза:**

| Условие | XP |
|---------|-----|
| Участие | +10 |
| За каждый правильный ответ | +5 |
| 1 место | +50 бонус |
| 2 место | +30 бонус |
| 3 место | +15 бонус |
| 100% правильных | +25 бонус |

### 2.4 Backend — WebSocket API

**Технология:** FastAPI WebSocket (встроенный, без дополнительных зависимостей)

**Endpoint:** `ws://api.ai-mentor.kz/api/v1/ws/quiz/{join_code}?token={jwt}`

#### Сообщения Server → Client

```jsonc
// Новый участник подключился (всем)
{"type": "participant_joined", "data": {"student_name": "Айдана", "count": 15}}

// Квиз стартовал
{"type": "quiz_started", "data": {"total_questions": 10}}

// Новый вопрос (ученикам)
{"type": "question", "data": {
  "index": 0,
  "text": "Решите уравнение...",
  "options": ["x=2", "x=3", "x=-2", "x=5"],
  "time_limit_ms": 30000,
  "image_url": null
}}

// Прогресс ответов (учителю)
{"type": "answer_progress", "data": {
  "answered": 18, "total": 24,
  "students": [{"name": "Айдана", "answered": true}, ...]
}}

// Результат вопроса (всем после дедлайна)
{"type": "question_result", "data": {
  "correct_option": 2,
  "stats": {"option_0": 5, "option_1": 3, "option_2": 14, "option_3": 2},
  "leaderboard_top5": [
    {"name": "Айдана", "score": 2750, "rank": 1},
    ...
  ]
}}

// Финальные результаты
{"type": "quiz_finished", "data": {
  "leaderboard": [...],
  "your_rank": 3,
  "your_score": 6200,
  "xp_earned": 55,
  "correct_answers": 7,
  "total_questions": 10
}}
```

#### Сообщения Client → Server

```jsonc
// Ученик отвечает на вопрос
{"type": "answer", "data": {"question_index": 0, "selected_option": 2}}

// Учитель: следующий вопрос
{"type": "next_question"}

// Учитель: завершить квиз досрочно
{"type": "finish_quiz"}
```

### 2.5 Backend — REST API (Quiz Management)

**Учитель (teacher-app):**

```
POST   /api/v1/teachers/quiz-sessions
       Body: {test_id, class_id?, settings: {time_per_question, ...}}
       → {id, join_code, status: "lobby", qr_url}

GET    /api/v1/teachers/quiz-sessions/{id}
       → Полная информация о сессии + участники

PATCH  /api/v1/teachers/quiz-sessions/{id}/start
       → Запуск квиза (status: lobby → in_progress)

PATCH  /api/v1/teachers/quiz-sessions/{id}/cancel
       → Отмена (status → cancelled)

GET    /api/v1/teachers/quiz-sessions/{id}/results
       → Итоги: лидерборд, статистика по вопросам, XP

GET    /api/v1/teachers/quiz-sessions
       → Список прошлых квизов учителя (history)
```

**Ученик (присоединение через WebView):**

```
POST   /api/v1/students/quiz-sessions/join
       Body: {join_code: "4829"}
       → {quiz_session_id, ws_url, status}

GET    /api/v1/students/quiz-sessions/{id}/results
       → Личные результаты + место в рейтинге
```

### 2.6 Frontend — WebView страница (student)

**Роут:** `student-app/src/app/[locale]/(webview)/quiz/page.tsx`

**Layout:** `student-app/src/app/[locale]/(webview)/layout.tsx`
- Минимальный: без sidebar, topbar, bottom nav
- Полноэкранный, mobile-first
- Принимает `?token=xxx` → сохраняет в localStorage

**Экраны квиза (состояния):**

```
1. JOIN        → Поле ввода кода (или auto-join из URL ?code=4829)
2. LOBBY       → "Ждём старта... Подключено: 24 ученика"
3. QUESTION    → Вопрос + 4 варианта + таймер (обратный отсчёт)
4. ANSWERED    → "Ответ принят! Ждём остальных..."
5. RESULT      → Правильный ответ + мини-лидерборд топ-5
6. FINISHED    → Итоги: место, очки, XP earned, статистика
```

**Компоненты:**

```
student-app/src/components/quiz/
├── QuizJoinScreen.tsx          ← Ввод кода
├── QuizLobby.tsx               ← Ожидание старта
├── QuizQuestion.tsx            ← Вопрос + варианты + таймер
├── QuizAnswered.tsx            ← Ожидание после ответа
├── QuizQuestionResult.tsx      ← Результат вопроса + топ-5
├── QuizFinished.tsx            ← Финальные результаты
├── QuizTimer.tsx               ← Круговой таймер
└── QuizMiniLeaderboard.tsx     ← Компактный лидерборд
```

**URL для мобилки:**
```
https://ai-mentor.kz/ru/webview/quiz?token=eyJ...&code=4829
```

### 2.7 Frontend — Teacher Dashboard (квизы)

**Роут:** `teacher-app/src/app/[locale]/(app)/quiz/page.tsx` — список квизов
**Роут:** `teacher-app/src/app/[locale]/(app)/quiz/[id]/page.tsx` — управление квизом

**Экраны:**

#### Создание квиза
1. Выбрать класс (dropdown)
2. Выбрать тест из учебника (или главы)
3. Настройки: время на вопрос (15/20/30/45/60 сек)
4. Создать → показать код + QR

#### Лобби (учитель видит)
```
┌──────────────────────────────┐
│  Код: 4829     [QR-код]     │
│                              │
│  Подключились: 24/28         │
│                              │
│  Айдана ✓  Олжас ✓  Дана ✓  │
│  Бекзат ✓  Арман ✓  ...     │
│                              │
│       [ ▶ Начать квиз ]     │
└──────────────────────────────┘
```

#### Во время квиза (учитель видит)
```
┌──────────────────────────────┐
│  Вопрос 3/10          ⏱ 18с │
│                              │
│  Ответили: 18/24             │
│  ████████████░░░░  75%       │
│                              │
│  Айдана ✅  Олжас ⏳         │
│  Дана ✅    Бекзат ✅        │
│                              │
│       [ Следующий → ]        │
└──────────────────────────────┘
```

#### Результаты (после квиза)
```
┌──────────────────────────────┐
│  🏆 Результаты квиза        │
│                              │
│  1. Айдана — 8,520 pts (+50) │
│  2. Олжас — 7,180 pts (+30) │
│  3. Дана — 6,940 pts  (+15) │
│  4. Бекзат — 6,200 pts      │
│  ...                         │
│                              │
│  Средний балл: 72%           │
│  Самый сложный: Вопрос 7     │
│                              │
│  [Экспорт] [Новый квиз]     │
└──────────────────────────────┘
```

### 2.8 Структура файлов (Фаза 2)

```
backend/
├── alembic/versions/051_quiz_sessions.py
├── app/models/quiz.py                    ← QuizSession, QuizParticipant, QuizAnswer
├── app/schemas/quiz.py                   ← Request/Response schemas
├── app/repositories/quiz_repo.py         ← CRUD
├── app/services/quiz_service.py          ← Логика: scoring, XP, state machine
├── app/api/v1/teachers_quiz.py           ← REST: создание, управление
├── app/api/v1/students_quiz.py           ← REST: join, results
└── app/api/v1/ws_quiz.py                 ← WebSocket endpoint

student-app/src/
├── app/[locale]/(webview)/
│   ├── layout.tsx                        ← Минимальный layout
│   └── quiz/
│       └── page.tsx                      ← Квиз-страница (все состояния)
├── components/quiz/
│   ├── QuizJoinScreen.tsx
│   ├── QuizLobby.tsx
│   ├── QuizQuestion.tsx
│   ├── QuizAnswered.tsx
│   ├── QuizQuestionResult.tsx
│   ├── QuizFinished.tsx
│   ├── QuizTimer.tsx
│   └── QuizMiniLeaderboard.tsx
└── lib/
    ├── api/quiz.ts                       ← REST клиент
    └── hooks/use-quiz-websocket.ts       ← WebSocket хук

teacher-app/src/
├── app/[locale]/(app)/quiz/
│   ├── page.tsx                          ← Список квизов
│   ├── create/page.tsx                   ← Создание
│   └── [id]/page.tsx                     ← Управление live
├── components/quiz/
│   ├── QuizCreateForm.tsx
│   ├── QuizLobbyTeacher.tsx
│   ├── QuizLiveProgress.tsx
│   ├── QuizResults.tsx
│   └── QuizStudentGrid.tsx
└── lib/
    ├── api/quiz.ts
    └── hooks/use-quiz-websocket.ts
```

---

## Порядок реализации

### Фаза 1 — Нативная геймификация ✅

| Шаг | Задача | Зависимости | Статус |
|-----|--------|-------------|--------|
| 1.1 | API клиент + React Query хуки | — | ✅ |
| 1.2 | `XpProgressBar`, `StreakBadge` (базовые компоненты) | — | ✅ |
| 1.3 | `XpLevelWidget` на главной | 1.1, 1.2 | ✅ |
| 1.4 | Страница `/gamification` (профиль + ачивки) | 1.1, 1.2 | ✅ |
| 1.5 | Лидерборд (таб на странице) | 1.1 | ✅ |
| 1.6 | Ежедневные квесты (таб на странице) | 1.1 | ✅ |
| 1.7 | `XpToast` + zustand store | 1.1 | ✅ |
| 1.8 | `AchievementPopup` (polling recent) | 1.1 | ✅ |
| 1.9 | Навигация (sidebar + bottom nav) | 1.1, 1.2 | ✅ |
| 1.10 | Локализация (ru + kk) | 1.3-1.9 | ✅ |
| 1.11 | Teacher-app: лидерборд класса | — | ❌ отложено |

### Фаза 2 — Живые квизы

| Шаг | Задача | Зависимости |
|-----|--------|-------------|
| 2.1 | Миграция 051: таблицы quiz_sessions, quiz_participants, quiz_answers | — |
| 2.2 | Backend модели + schemas + repo | 2.1 |
| 2.3 | Quiz service (state machine, scoring) | 2.2 |
| 2.4 | REST API (teacher: create/start/cancel, student: join/results) | 2.3 |
| 2.5 | WebSocket endpoint + hub (broadcast) | 2.3 |
| 2.6 | WebView layout в student-app | — |
| 2.7 | Quiz WebView (все 6 экранов) | 2.5, 2.6 |
| 2.8 | Teacher quiz dashboard (create + live + results) | 2.4, 2.5 |
| 2.9 | XP начисление после квиза (интеграция с gamification_service) | 2.3 |
| 2.10 | Локализация (ru + kk) | 2.7, 2.8 |
| 2.11 | QR-код генерация для join_code | 2.4 |

---

## Известные gaps (backend — нужно исправить для полноценной работы)

1. **on_test_passed hook отсутствует** — `test_taking_service.py` не вызывает `gamification_service.on_test_passed()`. Это основной источник XP. Нужно добавить хук.
2. **Achievement XP duplication risk** — в `check_achievements()` проверка существующей XP транзакции использует неправильный `source_type` (DAILY_QUEST вместо нужного). Нужно исправить.
3. **study_time quest** — тип квеста `study_time` есть в seed data, но нет механизма трекинга времени. Либо добавить трекинг, либо деактивировать этот квест.

---

## Фаза 3 — Видео-анимации (Remotion)

**Цель:** создание эффектных видео-анимаций для ключевых моментов геймификации — level-up, получение ачивки, итоги квиза, промо-ролики.

**Технология:** [Remotion](https://www.remotion.dev/) — React-фреймворк для программного создания видео.

**Скилл:** использовать `remotion-best-practices` — он помогает писать код по best practices Remotion.

### Зачем Remotion

Обычные CSS/Framer Motion анимации хороши для UI, но для wow-эффектов (level-up celebration, epic achievement unlock, quiz recap video) нужны полноценные видео-анимации:
- Можно рендерить в MP4/GIF и шарить в соцсетях
- Анимации на порядок сложнее и эффектнее чем CSS transitions
- Можно встроить звук, 3D, Lottie, графики
- Отдельный проект — не утяжеляет student-app

### 3.1 Remotion-проект

**Создание:**
```bash
npx create-video@latest gamification-videos
```

**Расположение:** `gamification-videos/` в корне репозитория

### 3.2 Видео-композиции (что создаём)

#### Level-Up Celebration
- Триггер: ученик получает новый уровень
- Анимация: число уровня с scale+glow эффектом, частицы, звук
- Длительность: 3-5 секунд
- Скилл Remotion: `animations.md` (scale, opacity), `text-animations.md` (число уровня), `audio.md` (звук celebration), `timing.md` (spring easing)

#### Achievement Unlock
- Триггер: ученик получает ачивку
- Анимация: иконка бейджа появляется с эффектом "раскрытия", название + описание, частицы по редкости (legendary = золотые)
- Длительность: 4-6 секунд
- Скилл Remotion: `animations.md`, `light-leaks.md` (glow для legendary), `lottie.md` (confetti), `sequencing.md` (последовательность: иконка → текст → частицы)

#### Quiz Results Video
- Триггер: после живого квиза — учитель может скачать / показать на проекторе
- Анимация: countdown топ-3, имена вылетают с очками, финальный лидерборд
- Длительность: 15-20 секунд
- Скилл Remotion: `text-animations.md` (имена), `charts.md` (bar chart очков), `transitions.md` (переходы между слайдами), `audio.md` (drumroll)

#### Weekly Recap (ученику)
- Триггер: еженедельная сводка (воскресенье)
- Анимация: "Твоя неделя" — XP заработано, тестов пройдено, место в рейтинге, стрик
- Длительность: 10-15 секунд
- Скилл Remotion: `charts.md` (line chart XP по дням), `text-animations.md`, `sequencing.md`

#### Promo / Onboarding Video
- Объяснение системы геймификации для новых учеников
- Скилл Remotion: `voiceover.md` (AI-озвучка через ElevenLabs), `transitions.md`, `text-animations.md`

### 3.3 Возможности скилла remotion-best-practices

| Категория | Файлы скилла | Применение в проекте |
|-----------|-------------|---------------------|
| **Анимации** | `animations.md` | Level-up scale/glow, achievement reveal |
| | `text-animations.md` | Typewriter для имён, подсветка XP числа |
| | `timing.md` | Spring easing для упругих анимаций |
| | `transitions.md` | Переходы между сценами в quiz recap |
| | `sequencing.md` | Цепочки анимаций (иконка → текст → confetti) |
| **Медиа** | `audio.md` | Celebration звуки, drumroll |
| | `audio-visualization.md` | Визуализация при воспроизведении музыки |
| | `voiceover.md` | AI-озвучка для onboarding видео |
| **Эффекты** | `3d.md` | 3D-медаль для топ-3 в quiz |
| | `charts.md` | Animated bar/line charts (XP, рейтинг) |
| | `lottie.md` | Confetti, fireworks, sparkles |
| | `light-leaks.md` | Glow для legendary ачивок |
| | `gifs.md` | Экспорт коротких анимаций в GIF для шаринга |

### 3.4 Интеграция с платформой

**Рендеринг:**
- Серверный через Remotion Lambda или локальный `npx remotion render`
- Видео генерируются по запросу (level-up, achievement) или по расписанию (weekly recap)
- Результат: MP4 файл → сохраняется в `uploads/gamification-videos/`

**Показ ученику:**
- В student-app: `<video>` тег в модалке (level-up, achievement)
- В WebView quiz: итоговое видео после квиза
- Weekly recap: push-уведомление со ссылкой на видео

**API:**
```
GET /api/v1/students/gamification/videos/level-up/{level}
GET /api/v1/students/gamification/videos/achievement/{code}
GET /api/v1/students/gamification/videos/weekly-recap
POST /api/v1/teachers/quiz-sessions/{id}/render-recap
```

### 3.5 Структура Remotion-проекта

```
gamification-videos/
├── src/
│   ├── compositions/
│   │   ├── LevelUp.tsx              ← Level-up celebration
│   │   ├── AchievementUnlock.tsx    ← Achievement reveal
│   │   ├── QuizResults.tsx          ← Quiz recap video
│   │   ├── WeeklyRecap.tsx          ← Weekly summary
│   │   └── PromoOnboarding.tsx      ← Explainer video
│   ├── components/
│   │   ├── ParticleSystem.tsx       ← Confetti / sparkles
│   │   ├── AnimatedNumber.tsx       ← XP / score counter
│   │   ├── GlowBadge.tsx           ← Achievement icon with glow
│   │   ├── BarChart.tsx             ← Animated bar chart
│   │   └── Countdown.tsx            ← 3-2-1 countdown
│   ├── assets/
│   │   ├── sounds/                  ← celebration.mp3, drumroll.mp3
│   │   ├── lottie/                  ← confetti.json, fireworks.json
│   │   └── fonts/                   ← Nunito (consistency with app)
│   ├── Root.tsx                     ← Composition registry
│   └── index.ts
├── package.json
├── remotion.config.ts
└── tsconfig.json
```

### 3.6 Порядок реализации (Фаза 3)

| Шаг | Задача | Зависимости |
|-----|--------|-------------|
| 3.1 | Создать Remotion-проект (`npx create-video@latest`) | — |
| 3.2 | Level-Up композиция (scale + glow + sound) | 3.1 |
| 3.3 | Achievement Unlock композиция (по редкостям) | 3.1 |
| 3.4 | Backend: API рендеринга + хранение видео | Фаза 1 |
| 3.5 | Интеграция в student-app (модалка с видео) | 3.2, 3.3, 3.4 |
| 3.6 | Quiz Results композиция | Фаза 2 |
| 3.7 | Weekly Recap композиция + cron-задача | 3.4 |
| 3.8 | Promo/Onboarding видео с AI-озвучкой | 3.1 |

---

## Технические решения

| Вопрос | Решение |
|--------|---------|
| Real-time для квиза | FastAPI WebSocket (встроенный) |
| State management квиза | Zustand store (client-side) |
| WebView auth | JWT через `?token=` в URL → localStorage |
| Polling ачивок | React Query refetchInterval: 30 сек |
| XP animation (простая) | CSS transition + Framer Motion (уже в deps student-app) |
| XP animation (эффектная) | Remotion видео (level-up, achievement unlock) |
| Remotion best practices | Скилл `remotion-best-practices` — вызывать при написании Remotion-кода |
| QR-код | `qrcode` npm-пакет (teacher-app) |
| Quiz timer sync | Server отправляет `server_time` + `deadline` → клиент считает локально |
| Видео-рендеринг | Remotion Lambda (prod) или `npx remotion render` (dev) |
