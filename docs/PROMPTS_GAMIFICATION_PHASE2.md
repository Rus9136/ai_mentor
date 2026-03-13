# Промт для Claude Code — Фаза 2: Живые квизы (Quiz Battle)

> Эта фаза большая — рекомендуется разбить на 3 сессии:
> - **Сессия A**: Backend (миграция + модели + repo + service + REST API + WebSocket)
> - **Сессия B**: Student WebView (layout + quiz page + WebSocket hook)
> - **Сессия C**: Teacher Dashboard (создание + лобби + live + результаты)
>
> Каждая сессия ниже — отдельный промт. Копируй нужную секцию.

---

## Сессия A: Backend — Quiz Sessions + WebSocket

### Задача

Реализуй backend для живых квизов (Kahoot-стиль). Учитель создаёт quiz session из существующего теста, ученики присоединяются по коду, отвечают на вопросы в реальном времени через WebSocket, получают XP.

### Перед началом — изучи

Прочитай эти файлы чтобы понять существующие паттерны:

1. **План** — `docs/GAMIFICATION_FRONTEND_PLAN.md` (секции 2.1–2.5 — схемы таблиц, WebSocket протокол, REST API, формула очков, XP после квиза)
2. **Модель тестов** — `backend/app/models/test.py` (Test → Question → QuestionOption — quiz session ссылается на test_id)
3. **Миграция-образец** — `backend/alembic/versions/050_gamification.py` (паттерн: CREATE TABLE, enums, GRANTS, RLS, seed data, revision chain)
4. **Модели-образец** — `backend/app/models/gamification.py` (SQLAlchemy модели с enums, JSONB, relationships)
5. **Repo-образец** — `backend/app/repositories/gamification_repo.py` (CRUD, __init__(db), async методы, select/update)
6. **Service-образец** — `backend/app/services/gamification_service.py` (constants, __init__(db), repo, бизнес-логика, hooks)
7. **API-образец** — `backend/app/api/v1/students/gamification.py` (router, Depends(get_student_from_user), Depends(get_db), response_model)
8. **Teacher API-образец** — `backend/app/api/v1/teachers_gamification.py` (teacher dependencies)
9. **Dependencies** — найди `get_teacher_from_user` или аналогичную teacher dependency в `backend/app/api/deps.py` или `backend/app/api/v1/`
10. **Регистрация роутеров** — `backend/app/main.py` (import + include_router)
11. **Gamification service** — `backend/app/services/gamification_service.py` (метод `award_xp` — вызвать после квиза для начисления XP)
12. **Config** — `backend/app/core/config.py` (Settings class)
13. **Models __init__** — `backend/app/models/__init__.py` (сюда добавить import новых моделей)

### Что реализовать

#### Шаг A.1 — Миграция `051_quiz_sessions`

**Файл:** `backend/alembic/versions/051_quiz_sessions.py`

```python
revision = '051_quiz_sessions'
down_revision = '050_gamification'
```

**Enum:**
```sql
CREATE TYPE quiz_session_status AS ENUM ('lobby', 'in_progress', 'finished', 'cancelled');
```

**Таблица `quiz_sessions`:**

| Колонка | Тип | Constraints |
|---------|-----|-------------|
| id | SERIAL | PRIMARY KEY |
| school_id | INT | NOT NULL, FK → schools(id) |
| teacher_id | INT | NOT NULL, FK → teachers(id) |
| class_id | INT | NULL, FK → classes(id) |
| test_id | INT | NOT NULL, FK → tests(id) |
| join_code | VARCHAR(6) | NOT NULL, UNIQUE |
| status | quiz_session_status | NOT NULL, DEFAULT 'lobby' |
| settings | JSONB | NOT NULL, DEFAULT '{}' |
| question_count | INT | NOT NULL |
| current_question_index | INT | NOT NULL, DEFAULT -1 |
| started_at | TIMESTAMPTZ | NULL |
| finished_at | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |

Индексы: `(join_code)` UNIQUE, `(school_id, status)`, `(teacher_id, created_at DESC)`.

**Таблица `quiz_participants`:**

| Колонка | Тип | Constraints |
|---------|-----|-------------|
| id | SERIAL | PRIMARY KEY |
| quiz_session_id | INT | NOT NULL, FK → quiz_sessions(id) ON DELETE CASCADE |
| student_id | INT | NOT NULL, FK → students(id) |
| school_id | INT | NOT NULL, FK → schools(id) |
| total_score | INT | NOT NULL, DEFAULT 0 |
| correct_answers | INT | NOT NULL, DEFAULT 0 |
| rank | INT | NULL |
| xp_earned | INT | NOT NULL, DEFAULT 0 |
| joined_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |
| finished_at | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |

UNIQUE: `(quiz_session_id, student_id)`.
Индексы: `(quiz_session_id, total_score DESC)`.

**Таблица `quiz_answers`:**

| Колонка | Тип | Constraints |
|---------|-----|-------------|
| id | SERIAL | PRIMARY KEY |
| quiz_session_id | INT | NOT NULL, FK → quiz_sessions(id) ON DELETE CASCADE |
| participant_id | INT | NOT NULL, FK → quiz_participants(id) ON DELETE CASCADE |
| school_id | INT | NOT NULL, FK → schools(id) |
| question_index | INT | NOT NULL |
| selected_option | INT | NOT NULL |
| is_correct | BOOLEAN | NOT NULL |
| answer_time_ms | INT | NOT NULL |
| score | INT | NOT NULL, DEFAULT 0 |
| answered_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |

UNIQUE: `(participant_id, question_index)` — один ответ на вопрос.

**RLS:** все 3 таблицы — tenant isolation по school_id (используй тот же шаблон что в 050).
**GRANTS:** SELECT, INSERT, UPDATE для ai_mentor_app + SEQUENCE grants.

#### Шаг A.2 — Модели

**Файл:** `backend/app/models/quiz.py`

Модели: `QuizSession`, `QuizParticipant`, `QuizAnswer` с enums `QuizSessionStatus`.

Следуй паттерну `gamification.py`:
- Enum через Python `enum.Enum` с `values_callable=lambda e: [v.value for v in e]`
- JSONB колонки через `Column(JSON)`
- Колонка `metadata` в БД → назови поле `settings` в Python (или `extra_data` если конфликт)
- Relationships: QuizSession → participants, answers; QuizParticipant → answers

Добавь import в `backend/app/models/__init__.py`.

#### Шаг A.3 — Schemas

**Файл:** `backend/app/schemas/quiz.py`

```python
# Request schemas
class QuizSessionCreate(BaseModel):
    test_id: int
    class_id: int | None = None
    settings: QuizSettings = QuizSettings()

class QuizSettings(BaseModel):
    time_per_question_ms: int = 30000  # 30 секунд по умолчанию
    show_leaderboard_after_each: bool = True
    max_participants: int = 50

class QuizJoinRequest(BaseModel):
    join_code: str

class QuizAnswerSubmit(BaseModel):
    question_index: int
    selected_option: int

# Response schemas
class QuizSessionResponse(BaseModel): ...       # id, join_code, status, question_count, settings, created_at
class QuizSessionDetailResponse(BaseModel): ...  # + participants list, current_question_index
class QuizParticipantResponse(BaseModel): ...    # student_id, student_name, total_score, correct_answers, rank
class QuizResultsResponse(BaseModel): ...        # leaderboard, per-question stats, average_score
class QuizStudentResultResponse(BaseModel): ...  # your_rank, your_score, xp_earned, correct_answers, total_questions
```

#### Шаг A.4 — Repository

**Файл:** `backend/app/repositories/quiz_repo.py`

Методы:
- `create_session(teacher_id, school_id, test_id, class_id, question_count, settings)` → QuizSession
- `get_session_by_code(join_code)` → QuizSession | None
- `get_session_by_id(session_id)` → QuizSession | None
- `update_session_status(session_id, status, **kwargs)` (kwargs: started_at, finished_at, current_question_index)
- `add_participant(quiz_session_id, student_id, school_id)` → QuizParticipant
- `get_participants(quiz_session_id)` → list[QuizParticipant]
- `get_participant(quiz_session_id, student_id)` → QuizParticipant | None
- `add_answer(participant_id, quiz_session_id, school_id, question_index, selected_option, is_correct, answer_time_ms, score)` → QuizAnswer
- `get_answers_for_question(quiz_session_id, question_index)` → list[QuizAnswer]
- `get_leaderboard(quiz_session_id)` → list[QuizParticipant] (ordered by total_score DESC)
- `update_participant_score(participant_id, score_delta, correct_delta)` — atomic increment
- `finalize_ranks(quiz_session_id)` — set rank based on total_score
- `get_teacher_sessions(teacher_id, limit=20)` → list[QuizSession]
- `generate_join_code()` → str (6 цифр, уникальный)

#### Шаг A.5 — Service

**Файл:** `backend/app/services/quiz_service.py`

Константы:
```python
MAX_QUESTION_SCORE = 1000
XP_PARTICIPATION = 10
XP_PER_CORRECT = 5
XP_FIRST_PLACE = 50
XP_SECOND_PLACE = 30
XP_THIRD_PLACE = 15
XP_PERFECT_QUIZ = 25
```

Методы:
- `create_session(teacher_id, school_id, test_id, class_id, settings)` → QuizSession
  - Загрузить Test с questions, посчитать question_count
  - Сгенерировать join_code
  - Сохранить через repo
- `join_session(join_code, student_id, school_id)` → QuizParticipant
  - Проверить: status == 'lobby', ученик ещё не в сессии, не превышен max_participants
  - Создать participant
- `start_session(session_id, teacher_id)` → None
  - Проверить: teacher_id совпадает, status == 'lobby', есть участники
  - Обновить status → 'in_progress', started_at, current_question_index = 0
- `get_current_question(session_id)` → dict
  - Загрузить Test.questions[current_question_index] с options
  - Вернуть: index, text, options (без is_correct!), time_limit_ms, image_url
- `submit_answer(session_id, student_id, question_index, selected_option, answer_time_ms)` → dict
  - Проверить: status == 'in_progress', question_index == current_question_index, ученик ещё не ответил
  - Определить is_correct из QuestionOption.is_correct
  - Рассчитать score: `calculate_question_score(is_correct, answer_time_ms, time_limit_ms)`
  - Сохранить answer, обновить participant.total_score и correct_answers
  - Вернуть: is_correct, score
- `advance_question(session_id, teacher_id)` → dict | None
  - current_question_index += 1
  - Если >= question_count → finish quiz
  - Вернуть question_result предыдущего вопроса (correct_option, stats, leaderboard_top5)
- `finish_session(session_id, teacher_id)` → dict
  - Финализировать ranks
  - Начислить XP каждому участнику через `GamificationService.award_xp()`
  - Обновить status → 'finished', finished_at
  - Вернуть итоги
- `cancel_session(session_id, teacher_id)` → None
- `get_question_stats(session_id, question_index)` → dict (сколько выбрали каждый вариант)
- `get_answer_progress(session_id, question_index)` → dict (answered/total, list кто ответил)

Формула очков:
```python
@staticmethod
def calculate_question_score(is_correct: bool, answer_time_ms: int, time_limit_ms: int) -> int:
    if not is_correct:
        return 0
    time_factor = max(0.0, 1.0 - (answer_time_ms / time_limit_ms) / 2)
    return round(MAX_QUESTION_SCORE * time_factor)
```

#### Шаг A.6 — REST API

**Файл:** `backend/app/api/v1/teachers_quiz.py`

```python
router = APIRouter(prefix="/quiz-sessions", tags=["Quiz Sessions (Teacher)"])

POST   /                              → create_quiz_session (teacher creates)
GET    /                              → list_quiz_sessions (teacher's history)
GET    /{session_id}                  → get_quiz_session (detail + participants)
PATCH  /{session_id}/start            → start_quiz_session
PATCH  /{session_id}/cancel           → cancel_quiz_session
GET    /{session_id}/results          → get_quiz_results
```

Зависимости: `get_teacher_from_user` (или аналог для учителя), `get_db`.

**Файл:** `backend/app/api/v1/students_quiz.py`

```python
router = APIRouter(prefix="/quiz-sessions", tags=["Quiz Sessions (Student)"])

POST   /join                          → join_quiz_session (student joins by code)
GET    /{session_id}/results          → get_student_results (personal results)
```

Зарегистрируй оба роутера в `backend/app/main.py`:
- Teachers: `prefix="/api/v1/teachers/quiz-sessions"`
- Students: `prefix="/api/v1/students/quiz-sessions"`

#### Шаг A.7 — WebSocket

**Файл:** `backend/app/api/v1/ws_quiz.py`

Это ключевая часть — real-time коммуникация.

**Endpoint:** `ws://api.ai-mentor.kz/api/v1/ws/quiz/{join_code}?token={jwt}`

**Архитектура:**

```python
class QuizConnectionManager:
    """Manages WebSocket connections for quiz sessions."""

    def __init__(self):
        # join_code → { "teacher": WebSocket, "students": {student_id: WebSocket} }
        self.rooms: dict[str, dict] = {}

    async def connect_teacher(self, join_code: str, websocket: WebSocket) -> None: ...
    async def connect_student(self, join_code: str, student_id: int, websocket: WebSocket) -> None: ...
    async def disconnect(self, join_code: str, user_id: int) -> None: ...
    async def broadcast_to_students(self, join_code: str, message: dict) -> None: ...
    async def send_to_teacher(self, join_code: str, message: dict) -> None: ...
    async def broadcast_all(self, join_code: str, message: dict) -> None: ...

manager = QuizConnectionManager()  # singleton
```

**WebSocket endpoint:**

```python
@router.websocket("/ws/quiz/{join_code}")
async def quiz_websocket(websocket: WebSocket, join_code: str, token: str = Query(...)):
    # 1. Verify JWT token → get user_id, role
    # 2. Verify quiz session exists and status in ('lobby', 'in_progress')
    # 3. Connect to room (teacher or student based on role)
    # 4. Broadcast participant_joined to all
    # 5. Message loop:
    #    - Teacher sends: "next_question", "finish_quiz"
    #    - Student sends: "answer" with {question_index, selected_option}
    #    - Server broadcasts: question, answer_progress, question_result, quiz_finished
```

**Обработка сообщений от учителя:**
- `{"type": "next_question"}`:
  1. Вызвать `quiz_service.advance_question()` — получить результат предыдущего вопроса
  2. `broadcast_all(question_result)` — результат предыдущего вопроса
  3. Через 3 сек (или сразу): `quiz_service.get_current_question()`
  4. `broadcast_to_students(question)` — новый вопрос (без is_correct)
  5. `send_to_teacher(question + answer_progress)` — учителю показать вопрос + прогресс

- `{"type": "finish_quiz"}`:
  1. `quiz_service.finish_session()` — финализация, XP
  2. Каждому студенту отправить персональный `quiz_finished` (с your_rank, your_score, xp_earned)
  3. Учителю отправить полные результаты

**Обработка сообщений от ученика:**
- `{"type": "answer", "data": {"question_index": N, "selected_option": M}}`:
  1. Засечь answer_time_ms (время от отправки вопроса)
  2. `quiz_service.submit_answer()` → is_correct, score
  3. Отправить ученику: `{"type": "answer_accepted", "data": {"is_correct": ..., "score": ...}}`
  4. `send_to_teacher(answer_progress)` — обновить прогресс ответов

**Важно:**
- Каждый вопрос имеет дедлайн — `question_sent_at + time_limit_ms`. После дедлайна сервер автоматически переходит к результатам (не ждёт "next_question" от учителя)
- При disconnect — удалить из room, broadcast updated count
- При reconnect — восстановить состояние (текущий вопрос, уже отвеченные)
- Определение роли по JWT: проверить есть ли Teacher с этим user_id

**Зарегистрируй WebSocket роутер в main.py** отдельно (WebSocket не работает через include_router с prefix у FastAPI — используй `app.include_router(ws_quiz_router)`).

#### Шаг A.8 — Интеграция с геймификацией

В `quiz_service.finish_session()`:

```python
from app.services.gamification_service import GamificationService

async def _award_quiz_xp(self, session_id: int) -> None:
    """Award XP to all participants after quiz finishes."""
    gamification = GamificationService(self.db)
    participants = await self.repo.get_leaderboard(session_id)

    for p in participants:
        xp = XP_PARTICIPATION  # +10 за участие
        xp += p.correct_answers * XP_PER_CORRECT  # +5 за каждый правильный

        if p.rank == 1: xp += XP_FIRST_PLACE    # +50
        elif p.rank == 2: xp += XP_SECOND_PLACE  # +30
        elif p.rank == 3: xp += XP_THIRD_PLACE   # +15

        # Нужно знать question_count для проверки perfect
        session = await self.repo.get_session_by_id(session_id)
        if p.correct_answers == session.question_count:
            xp += XP_PERFECT_QUIZ  # +25

        await gamification.award_xp(
            student_id=p.student_id,
            school_id=p.school_id,
            amount=xp,
            source_type=XpSourceType.TEST_PASSED,  # или добавить QUIZ_COMPLETED в enum
            source_id=session_id,
            extra_data={"quiz_rank": p.rank, "quiz_score": p.total_score},
        )

        # Обновить participant.xp_earned
        p.xp_earned = xp

    await self.db.flush()
```

**Важно:** если нужен новый XpSourceType `QUIZ_COMPLETED`, добавь его в:
1. Enum `xp_source_type` в миграции 051 (ALTER TYPE ... ADD VALUE)
2. Python enum `XpSourceType` в `backend/app/models/gamification.py`

### Проверки после реализации

```bash
# 1. Python syntax/imports
cd backend && python -c "from app.models.quiz import QuizSession, QuizParticipant, QuizAnswer; print('Models OK')"
cd backend && python -c "from app.services.quiz_service import QuizService; print('Service OK')"
cd backend && python -c "from app.api.v1.ws_quiz import router; print('WebSocket OK')"

# 2. Ruff lint
ruff check backend/app/models/quiz.py backend/app/services/quiz_service.py backend/app/api/v1/ws_quiz.py

# 3. Проверить что main.py импортирует без ошибок
cd backend && python -c "from app.main import app; print('Main OK')"
```

### Правила

- Следуй Layered Architecture: API (thin) → Service (logic) → Repository (CRUD)
- Каждый файл < 400 строк (service может быть до 300)
- Все SQL через SQLAlchemy ORM (select, update, insert) — не raw SQL в repo/service
- school_id ВСЕГДА из токена/dependency — НИКОГДА от клиента
- Миграция пишется вручную (не autogenerate) — следуй формату 050
- WebSocket: обработай disconnect/reconnect gracefully
- Все хуки gamification обёрнуты в try/except с logger.warning — сбой XP не должен ломать квиз
- Не добавляй `updated_at` trigger — он уже есть на уровне приложения (BaseModel)

---

## Сессия B: Student WebView — Quiz UI

### Задача

Реализуй WebView страницу квиза для учеников в student-app. Страница открывается в мобилке через URL с токеном, подключается к WebSocket, показывает вопросы в реальном времени.

### Перед началом — изучи

1. **План** — `docs/GAMIFICATION_FRONTEND_PLAN.md` (секция 2.6 — экраны, компоненты, URL)
2. **Backend WebSocket протокол** — прочитай `backend/app/api/v1/ws_quiz.py` (какие сообщения отправляет/принимает)
3. **Backend REST API (student)** — прочитай `backend/app/api/v1/students_quiz.py` (join, results endpoints)
4. **Backend schemas** — прочитай `backend/app/schemas/quiz.py` (response types)
5. **Существующий API клиент** — прочитай `student-app/src/lib/api/client.ts` (axios setup, token management)
6. **Auth flow** — прочитай `student-app/src/providers/auth-provider.tsx` (как работает localStorage token)
7. **Существующий layout (app)** — прочитай `student-app/src/app/[locale]/(app)/layout.tsx` (чтобы сделать webview layout МИНИМАЛЬНЫМ — без sidebar/nav)
8. **Tailwind config** — прочитай `student-app/tailwind.config.ts` (цвета, fonts)
9. **i18n** — прочитай `student-app/src/i18n/routing.ts` и `student-app/messages/ru.json` (секция gamification.*)
10. **Gamification components** — посмотри `student-app/src/components/gamification/` (XpProgressBar, StreakBadge — можно переиспользовать)

### Что реализовать

#### Шаг B.1 — WebView layout

**Файл:** `student-app/src/app/[locale]/(webview)/layout.tsx`

Минимальный layout:
- Без sidebar, topbar, bottom nav
- Полноэкранный (h-screen, overflow-hidden)
- Mobile-first
- Читает `?token=xxx` из URL → сохраняет в localStorage как `ai_mentor_access_token`
- Оборачивает children в QueryProvider (React Query)
- Шрифт Nunito (как в основном приложении)

```typescript
'use client';

import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { QueryProvider } from '@/providers/query-provider';

export default function WebViewLayout({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      localStorage.setItem('ai_mentor_access_token', token);
    }
  }, [searchParams]);

  return (
    <QueryProvider>
      <div className="h-screen overflow-hidden bg-background">
        {children}
      </div>
    </QueryProvider>
  );
}
```

#### Шаг B.2 — WebSocket hook

**Файл:** `student-app/src/lib/hooks/use-quiz-websocket.ts`

```typescript
type QuizWsMessage =
  | { type: 'participant_joined'; data: { student_name: string; count: number } }
  | { type: 'quiz_started'; data: { total_questions: number } }
  | { type: 'question'; data: { index: number; text: string; options: string[]; time_limit_ms: number; image_url: string | null } }
  | { type: 'answer_accepted'; data: { is_correct: boolean; score: number } }
  | { type: 'question_result'; data: { correct_option: number; stats: Record<string, number>; leaderboard_top5: Array<{ name: string; score: number; rank: number }> } }
  | { type: 'quiz_finished'; data: { leaderboard: Array<{ name: string; score: number; rank: number }>; your_rank: number; your_score: number; xp_earned: number; correct_answers: number; total_questions: number } };

function useQuizWebSocket(joinCode: string | null, onMessage: (msg: QuizWsMessage) => void)
```

Хук:
- Подключается к `ws(s)://api.ai-mentor.kz/api/v1/ws/quiz/{joinCode}?token={jwt}`
- Определяет ws/wss по `window.location.protocol`
- Берёт token из localStorage
- Auto-reconnect при обрыве (3 попытки, backoff)
- Возвращает: `{ send: (msg) => void, isConnected: boolean, error: string | null }`
- cleanup: закрывает соединение при unmount или смене joinCode

#### Шаг B.3 — Quiz REST API клиент

**Файл:** `student-app/src/lib/api/quiz.ts`

```typescript
joinQuizSession(joinCode: string): Promise<{ quiz_session_id: number; status: string }>
getQuizResults(sessionId: number): Promise<QuizStudentResult>
```

#### Шаг B.4 — Quiz page (state machine)

**Файл:** `student-app/src/app/[locale]/(webview)/quiz/page.tsx`

Страница управляется state machine через zustand или useReducer:

```typescript
type QuizScreen = 'join' | 'lobby' | 'question' | 'answered' | 'result' | 'finished';
```

Логика переходов:
```
join → (user enters code, POST /join succeeds) → lobby
lobby → (ws: quiz_started) → question
question → (user taps option) → answered
answered → (ws: question_result) → result
result → (ws: question — next) → question
result → (ws: quiz_finished) → finished
```

State:
```typescript
interface QuizState {
  screen: QuizScreen;
  joinCode: string;
  sessionId: number | null;
  participantCount: number;
  currentQuestion: { index: number; text: string; options: string[]; time_limit_ms: number; image_url: string | null } | null;
  selectedOption: number | null;
  lastResult: { correct_option: number; stats: Record<string, number>; leaderboard_top5: any[] } | null;
  finalResult: { your_rank: number; your_score: number; xp_earned: number; correct_answers: number; total_questions: number; leaderboard: any[] } | null;
  questionStartTime: number;  // Date.now() when question received — для расчёта answer_time_ms
  myScore: number;
}
```

#### Шаг B.5 — Компоненты квиза

Создай в `student-app/src/components/quiz/`:

**QuizJoinScreen.tsx:**
- Поле ввода 6-значного кода (крупные цифры, auto-focus)
- Кнопка "Присоединиться"
- Или auto-join если `?code=XXXX` в URL
- При ошибке — показать сообщение (неверный код, квиз уже начался)

**QuizLobby.tsx:**
- "Ждём начала..."
- Счётчик подключённых: "Подключено: {count} учеников"
- Анимация ожидания (пульсирующая точка или spinner)

**QuizQuestion.tsx:**
- Текст вопроса (поддержка LaTeX если есть — проверь как рендерится в test components)
- 4 варианта ответа — большие кнопки, цветные (A=красный, B=синий, C=жёлтый, D=зелёный — как Kahoot)
- Круговой таймер (QuizTimer) в правом верхнем углу
- Номер вопроса: "Вопрос {index+1} / {total}"
- Image (если есть image_url)

**QuizTimer.tsx:**
- Круговой countdown (SVG circle с stroke-dashoffset анимацией)
- Props: `totalMs`, `onTimeout`
- Обратный отсчёт в секундах внутри круга
- Красный когда < 5 сек

**QuizAnswered.tsx:**
- "Ответ принят!"
- Показать: "+{score} очков" если известно (из answer_accepted)
- "Ждём остальных..."
- Spinner

**QuizQuestionResult.tsx:**
- Правильный вариант подсвечен зелёным
- Статистика: сколько выбрали каждый вариант (горизонтальные бары)
- Мини-лидерборд топ-5 (QuizMiniLeaderboard)

**QuizMiniLeaderboard.tsx:**
- 5 строк: ранг, имя, очки
- Анимация появления (staggered)

**QuizFinished.tsx:**
- "Квиз завершён!"
- Твоё место: {rank} с медалью если топ-3
- Твои очки: {score}
- XP заработано: "+{xp} XP" (с анимацией)
- Правильных: {correct} / {total}
- Полный лидерборд (все участники)
- Кнопка "Закрыть" (для WebView — window.close() или postMessage)

#### Шаг B.6 — Локализация

Добавь ключи `quiz.*` в `student-app/messages/ru.json` и `student-app/messages/kk.json`:

```
quiz.joinTitle, quiz.enterCode, quiz.join, quiz.invalidCode,
quiz.waitingForStart, quiz.connectedCount, quiz.questionOf,
quiz.answerAccepted, quiz.waitingForOthers, quiz.correctAnswer,
quiz.yourPlace, quiz.yourScore, quiz.xpEarned, quiz.correctAnswers,
quiz.quizFinished, quiz.close, quiz.timeUp
```

### Правила

- Layout (webview) — НИКАКОЙ навигации (sidebar, topbar, bottom nav). Только content.
- Mobile-first — все размеры для экрана 375px+ (iPhone SE)
- Варианты ответов — большие touch-targets (min-h-14, p-4)
- Цвета вариантов: A=#EF4444, B=#3B82F6, C=#F59E0B, D=#22C55E
- WebSocket reconnect — 3 попытки с экспоненциальным backoff (1s, 2s, 4s)
- При потере соединения — overlay "Переподключение..."
- Все тексты через useTranslations — не хардкодь строки
- Каждый файл < 400 строк
- После реализации: `cd student-app && npm run build` — билд без ошибок

---

## Сессия C: Teacher Dashboard — Quiz Management

### Задача

Реализуй UI для учителя в teacher-app: создание квиза, лобби с QR-кодом, live-управление (следующий вопрос, прогресс), экран результатов.

### Перед началом — изучи

1. **План** — `docs/GAMIFICATION_FRONTEND_PLAN.md` (секция 2.7 — wireframes экранов учителя)
2. **Backend REST API (teacher)** — прочитай `backend/app/api/v1/teachers_quiz.py` (endpoints: create, list, start, cancel, results)
3. **Backend WebSocket** — прочитай `backend/app/api/v1/ws_quiz.py` (сообщения answer_progress, question_result для учителя)
4. **Backend schemas** — прочитай `backend/app/schemas/quiz.py`
5. **Teacher-app API клиент** — прочитай `teacher-app/src/lib/api/client.ts` (axios setup, token key: `ai_mentor_teacher_access_token`)
6. **Teacher-app routing** — посмотри структуру `teacher-app/src/app/[locale]/(dashboard)/` (layout, sidebar)
7. **Teacher-app пример страницы** — прочитай одну существующую страницу (например homework или classes) для паттерна
8. **Teacher-app sidebar** — найди sidebar/navigation компонент чтобы добавить ссылку на /quiz
9. **Teacher-app i18n** — прочитай `teacher-app/src/messages/ru/index.json` (структура ключей)
10. **Teacher-app components** — посмотри `teacher-app/src/components/` (существующие UI компоненты)
11. **Tests API** — найди как учитель получает список тестов (чтобы в создании квиза показать выбор теста). Проверь есть ли endpoint GET /teachers/tests или аналог. Если нет — используй GET /admin/school/tests или покажи тесты по textbook/chapter.

### Что реализовать

#### Шаг C.1 — API клиент + хуки

**Файл:** `teacher-app/src/lib/api/quiz.ts`

```typescript
createQuizSession(data: { test_id: number; class_id?: number; settings?: QuizSettings }): Promise<QuizSession>
getQuizSessions(): Promise<QuizSession[]>
getQuizSession(sessionId: number): Promise<QuizSessionDetail>
startQuizSession(sessionId: number): Promise<void>
cancelQuizSession(sessionId: number): Promise<void>
getQuizResults(sessionId: number): Promise<QuizResults>
```

**Файл:** `teacher-app/src/lib/hooks/use-quiz.ts` — React Query хуки для CRUD.

**Файл:** `teacher-app/src/lib/hooks/use-quiz-websocket.ts` — WebSocket хук (аналогичный student-app, но teacher-specific messages: answer_progress).

#### Шаг C.2 — Список квизов

**Роут:** `teacher-app/src/app/[locale]/(dashboard)/quiz/page.tsx`

- Список прошлых и текущих квизов учителя
- Карточки: тест, класс, дата, статус (lobby/in_progress/finished), кол-во участников
- Кнопка "Создать квиз" → переход на /quiz/create
- Клик на квиз → /quiz/[id]

#### Шаг C.3 — Создание квиза

**Роут:** `teacher-app/src/app/[locale]/(dashboard)/quiz/create/page.tsx`

**Компонент:** `teacher-app/src/components/quiz/QuizCreateForm.tsx`

Форма:
1. **Выбор класса** — dropdown из классов учителя (GET /teachers/classes или аналог)
2. **Выбор теста** — список тестов (фильтр по предмету/главе). Показать: название, кол-во вопросов, сложность
3. **Настройки:**
   - Время на вопрос: 15 / 20 / 30 / 45 / 60 сек (radio/select, default 30)
   - Показывать лидерборд после каждого вопроса: toggle (default: да)
4. **Кнопка "Создать"** → POST, redirect на /quiz/[id] (лобби)

#### Шаг C.4 — Лобби (ожидание учеников)

**Роут:** `teacher-app/src/app/[locale]/(dashboard)/quiz/[id]/page.tsx` (когда status == 'lobby')

**Компонент:** `teacher-app/src/components/quiz/QuizLobbyTeacher.tsx`

- **Join code** — крупные цифры (text-6xl font-mono), можно скопировать
- **QR-код** — ссылка `https://ai-mentor.kz/ru/webview/quiz?code={join_code}` закодированная в QR
  - Для QR: установить `qrcode.react` или `react-qr-code` npm-пакет
- **Список подключённых** — grid с именами учеников (обновляется через WebSocket participant_joined)
- **Счётчик** — "Подключились: {count}" (если есть class_id — "/total из класса")
- **Кнопка "Начать квиз"** — disabled если 0 участников
- **Кнопка "Отменить"** — cancel с подтверждением

#### Шаг C.5 — Live управление квизом

**Тот же роут** `/quiz/[id]/page.tsx` (когда status == 'in_progress')

**Компонент:** `teacher-app/src/components/quiz/QuizLiveProgress.tsx`

- **Номер вопроса** — "Вопрос {index+1} / {total}"
- **Таймер** — обратный отсчёт (синхронизирован с сервером)
- **Прогресс ответов** — progress bar "{answered}/{total} ответили"
- **Сетка учеников** — `QuizStudentGrid.tsx`:
  - Имя + статус: ⏳ (ждёт) или ✅ (ответил)
  - Обновляется через WebSocket answer_progress
- **Кнопка "Следующий вопрос"** — отправляет `{"type": "next_question"}` через WebSocket
- **Кнопка "Завершить досрочно"** — отправляет `{"type": "finish_quiz"}`

**После question_result от сервера:**
- Показать статистику: сколько выбрали каждый вариант (bar chart или горизонтальные бары)
- Подсветить правильный ответ
- 3-5 секунд задержки → "Следующий вопрос" становится активной

#### Шаг C.6 — Результаты

**Тот же роут** `/quiz/[id]/page.tsx` (когда status == 'finished')

**Компонент:** `teacher-app/src/components/quiz/QuizResults.tsx`

- **Лидерборд** — полная таблица (ранг, имя, очки, правильных, XP)
- **Топ-3 с медалями** — выделенная секция
- **Статистика:**
  - Средний балл (% правильных)
  - Самый сложный вопрос (наименьший % правильных)
  - Самый лёгкий вопрос
- **Per-question breakdown** (expandable) — вопрос, распределение ответов
- **Кнопки:** "Новый квиз", "Назад к списку"

#### Шаг C.7 — Навигация

Добавь ссылку "Квизы" (или "Соревнования") в sidebar teacher-app:
- Иконка: Swords, Gamepad2, или Zap из lucide-react
- Путь: /quiz

#### Шаг C.8 — Локализация

Добавь ключи `quiz.*` в `teacher-app/src/messages/ru/index.json` и `teacher-app/src/messages/kz/index.json`:

```
quiz.title, quiz.create, quiz.createQuiz, quiz.selectClass, quiz.selectTest,
quiz.timePerQuestion, quiz.showLeaderboard, quiz.joinCode, quiz.qrCode,
quiz.connected, quiz.startQuiz, quiz.cancel, quiz.cancelConfirm,
quiz.questionOf, quiz.answered, quiz.nextQuestion, quiz.finishEarly,
quiz.results, quiz.rank, quiz.score, quiz.correctAnswers, quiz.xpEarned,
quiz.averageScore, quiz.hardestQuestion, quiz.easiestQuestion,
quiz.newQuiz, quiz.backToList, quiz.noQuizzes, quiz.history,
quiz.settings, quiz.seconds
```

### Правила

- Следуй существующим паттернам teacher-app (layout, components, API client)
- QR-код: установи пакет `react-qr-code` или `qrcode.react`
- WebSocket: тот же паттерн что в student-app (reconnect, cleanup)
- Responsive: teacher скорее всего на ноутбуке/проекторе — optimize for 1024px+
- Каждый файл < 400 строк
- После реализации: `cd teacher-app && npm run build` — билд без ошибок
