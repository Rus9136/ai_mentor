# Homework AI System — План реализации

**Версия:** 1.2
**Дата создания:** 2025-01-04
**Последнее обновление:** 2026-01-04
**Статус:** Backend готов (Фазы 1-4 ✅), следующий шаг — Фаза 5 (AI) или Фаза 6 (Frontend)

## Прогресс реализации

| Фаза | Описание | Статус |
|------|----------|--------|
| Фаза 1 | Models + Migrations | ✅ Выполнено |
| Фаза 2 | Schemas + Repositories | ✅ Выполнено |
| Фаза 3 | Services | ✅ Выполнено |
| Фаза 4 | API Endpoints | ✅ Выполнено |
| Фаза 5 | AI Integration | ⏳ Ожидает |
| Фаза 6 | Teacher Frontend | ⏳ Ожидает |
| Фаза 7 | Student Frontend | ⏳ Ожидает |

---

## Оглавление

1. [Обзор системы](#1-обзор-системы)
2. [Архитектура БД (обновлённая)](#2-архитектура-бд-обновлённая)
3. [Фазы реализации](#3-фазы-реализации)
4. [Фаза 1: Модели и миграции](#4-фаза-1-модели-и-миграции)
5. [Фаза 2: Schemas и Repositories](#5-фаза-2-schemas-и-repositories)
6. [Фаза 3: Services (бизнес-логика)](#6-фаза-3-services-бизнес-логика)
7. [Фаза 4: API Endpoints](#7-фаза-4-api-endpoints)
8. [Фаза 5: AI Integration](#8-фаза-5-ai-integration)
9. [Фаза 6: Frontend (Teacher App)](#9-фаза-6-frontend-teacher-app)
10. [Фаза 7: Frontend (Student App)](#10-фаза-7-frontend-student-app)
11. [Тестирование](#11-тестирование)
12. [Риски и митигация](#12-риски-и-митигация)

---

## 1. Обзор системы

### Цель

Создать систему домашних заданий с AI-интеграцией:
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

## 2. Архитектура БД (обновлённая)

### Схема таблиц

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         HOMEWORK SYSTEM v2 (AI-Ready)                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────┐       ┌──────────────────┐       ┌─────────────────────┐  │
│  │    Homework      │──────▶│  HomeworkTask    │──────▶│ HomeworkTaskQuestion│  │
│  │  (ДЗ для класса) │       │ (задача/параграф)│       │  (вопрос + версия)  │  │
│  │                  │       │ + school_id ⭐    │       │  + version ⭐        │  │
│  └────────┬─────────┘       └────────┬─────────┘       └─────────────────────┘  │
│           │                          │                                          │
│           ▼                          ▼                                          │
│  ┌──────────────────┐       ┌──────────────────┐       ┌─────────────────────┐  │
│  │ HomeworkStudent  │       │ StudentTask      │──────▶│ StudentTaskAnswer   │  │
│  │ (назначение)     │       │ Submission       │       │ (ответ + attempt) ⭐ │  │
│  │                  │       │ + attempt_number │       │ + ai_grading        │  │
│  └──────────────────┘       └────────┬─────────┘       └─────────────────────┘  │
│                                      │                                          │
│                             ┌────────▼─────────┐                                │
│                             │ AIGenerationLog  │                                │
│                             │ (аудит AI)       │                                │
│                             └──────────────────┘                                │
│                                                                                 │
│  ⭐ = Изменения относительно v1                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Ключевые изменения vs v1

| Изменение | Причина | Таблица |
|-----------|---------|---------|
| `school_id` в HomeworkTask | Быстрый RLS без JOIN | `homework_tasks` |
| `version` + `is_active` | Версионирование при AI-регенерации | `homework_task_questions` |
| `max_attempts` | Ограничение попыток | `homework_tasks` |
| `attempt_number` | Трекинг попыток | `student_task_submissions` |
| Late submission policy | Гибкие дедлайны | `homework` |
| VARCHAR вместо ENUM | Легче мигрировать | Все типы статусов |

---

## 3. Фазы реализации

```
┌─────────────────────────────────────────────────────────────────────┐
│  Фаза 1        Фаза 2         Фаза 3        Фаза 4                  │
│  ───────       ───────        ───────       ───────                 │
│  Models   ──▶  Schemas   ──▶  Services  ──▶  API                    │
│  Migrations    Repos          Logic         Endpoints               │
│                                                                     │
│  Фаза 5        Фаза 6         Фаза 7                                │
│  ───────       ───────        ───────                               │
│  AI        ──▶ Teacher   ──▶  Student                               │
│  Integration   Frontend       Frontend                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Фаза 1: Модели и миграции

### 4.1 Обновить модель Homework

**Файл:** `backend/app/models/homework.py`

```python
class Homework(BaseModel):
    __tablename__ = "homework"

    # Основные поля (уже есть)
    title: str
    description: str
    school_id: int
    class_id: int
    teacher_id: int
    due_date: datetime
    status: str  # draft, published, closed, archived

    # AI настройки (уже есть)
    ai_generation_enabled: bool = False
    ai_check_enabled: bool = False
    target_difficulty: str = "auto"  # easy, medium, hard, auto
    personalization_enabled: bool = False

    # ⭐ НОВОЕ: Late submission policy
    late_submission_allowed: bool = False
    late_penalty_per_day: int = 0  # процент штрафа
    grace_period_hours: int = 0  # льготный период
    max_late_days: int = 7  # максимум дней опоздания
```

### 4.2 Обновить HomeworkTask

```python
class HomeworkTask(BaseModel):
    __tablename__ = "homework_tasks"

    homework_id: int
    paragraph_id: int
    task_type: str  # read, quiz, open_question, essay, practice
    sort_order: int

    # ⭐ НОВОЕ: Денормализация для RLS
    school_id: int  # FK to schools.id

    # ⭐ НОВОЕ: Ограничение попыток
    max_attempts: int = 1

    # AI генерация (уже есть)
    ai_prompt_template: str = None
    generation_params: dict = None  # JSONB
    ai_generated: bool = False
```

### 4.3 Обновить HomeworkTaskQuestion

```python
class HomeworkTaskQuestion(BaseModel):
    __tablename__ = "homework_task_questions"

    task_id: int
    question_text: str
    question_type: str  # single_choice, multiple_choice, short_answer, open_ended
    options: dict = None  # JSONB для вариантов ответа
    correct_answer: str = None
    points: int = 1
    bloom_level: str = None  # remember, understand, apply, analyze, evaluate, create

    # AI grading (уже есть)
    grading_rubric: dict = None
    expected_answer_hints: str = None
    ai_grading_prompt: str = None

    # ⭐ НОВОЕ: Версионирование
    version: int = 1
    is_active: bool = True
    replaced_by_id: int = None  # FK self-reference
    created_at: datetime
```

### 4.4 Обновить StudentTaskSubmission

```python
class StudentTaskSubmission(BaseModel):
    __tablename__ = "student_task_submissions"

    homework_student_id: int
    task_id: int
    status: str  # not_started, in_progress, submitted, graded

    # ⭐ НОВОЕ: Номер попытки
    attempt_number: int = 1

    started_at: datetime = None
    submitted_at: datetime = None
    score: float = None
    max_score: float = None

    # ⭐ НОВОЕ: Late submission tracking
    is_late: bool = False
    late_penalty_applied: float = 0  # процент штрафа
    original_score: float = None  # до штрафа

    __table_args__ = (
        UniqueConstraint('homework_student_id', 'task_id', 'attempt_number',
                        name='uq_submission_attempt'),
    )
```

### 4.5 Миграция

**Файл:** `backend/alembic/versions/022_homework_ai_v2_improvements.py`

```python
"""Homework AI v2 improvements

Revision ID: 022
"""

def upgrade():
    # 1. Добавить school_id в homework_tasks
    op.add_column('homework_tasks',
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=True))

    # Заполнить school_id из homework
    op.execute("""
        UPDATE homework_tasks ht
        SET school_id = h.school_id
        FROM homework h
        WHERE ht.homework_id = h.id
    """)

    op.alter_column('homework_tasks', 'school_id', nullable=False)

    # 2. Добавить max_attempts
    op.add_column('homework_tasks',
        sa.Column('max_attempts', sa.Integer(), server_default='1'))

    # 3. Версионирование вопросов
    op.add_column('homework_task_questions',
        sa.Column('version', sa.Integer(), server_default='1'))
    op.add_column('homework_task_questions',
        sa.Column('is_active', sa.Boolean(), server_default='true'))
    op.add_column('homework_task_questions',
        sa.Column('replaced_by_id', sa.Integer(), nullable=True))

    # 4. Late submission policy
    op.add_column('homework',
        sa.Column('late_submission_allowed', sa.Boolean(), server_default='false'))
    op.add_column('homework',
        sa.Column('late_penalty_per_day', sa.Integer(), server_default='0'))
    op.add_column('homework',
        sa.Column('grace_period_hours', sa.Integer(), server_default='0'))
    op.add_column('homework',
        sa.Column('max_late_days', sa.Integer(), server_default='7'))

    # 5. Attempt tracking
    op.add_column('student_task_submissions',
        sa.Column('attempt_number', sa.Integer(), server_default='1'))
    op.add_column('student_task_submissions',
        sa.Column('is_late', sa.Boolean(), server_default='false'))
    op.add_column('student_task_submissions',
        sa.Column('late_penalty_applied', sa.Float(), server_default='0'))
    op.add_column('student_task_submissions',
        sa.Column('original_score', sa.Float(), nullable=True))

    # 6. Индексы
    op.create_index('idx_homework_tasks_school_id', 'homework_tasks', ['school_id'])
    op.create_index('idx_questions_active_version', 'homework_task_questions',
                    ['task_id', 'is_active', 'version'])

    # 7. RLS для homework_tasks (теперь с school_id)
    op.execute("""
        DROP POLICY IF EXISTS homework_tasks_isolation ON homework_tasks;
        CREATE POLICY homework_tasks_isolation ON homework_tasks
            FOR ALL TO ai_mentor_app
            USING (school_id = COALESCE(
                NULLIF(current_setting('app.current_tenant_id', true), '')::int,
                school_id
            ));
    """)
```

### 4.6 Чеклист Фазы 1 ✅

- [x] Обновить `backend/app/models/homework.py`
- [x] Создать миграцию `022_homework_ai_v2_improvements.py`
- [x] Обновить `backend/app/models/__init__.py`
- [x] Протестировать миграцию локально
- [x] Применить миграцию на dev

**Выполнено:** 2026-01-04

---

## 5. Фаза 2: Schemas и Repositories

### 5.1 Pydantic Schemas

**Файл:** `backend/app/schemas/homework.py`

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ─────────────────────────────────────────
# Enums (как строки для гибкости)
# ─────────────────────────────────────────

class HomeworkStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    ARCHIVED = "archived"

class TaskType(str, Enum):
    READ = "read"
    QUIZ = "quiz"
    OPEN_QUESTION = "open_question"
    ESSAY = "essay"
    PRACTICE = "practice"

class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    OPEN_ENDED = "open_ended"

class BloomLevel(str, Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"

# ─────────────────────────────────────────
# Nested Schemas для JSON полей
# ─────────────────────────────────────────

class RubricCriterion(BaseModel):
    name: str
    weight: float = Field(ge=0, le=1)
    levels: List[str]  # ["отлично", "хорошо", "частично", "нет"]
    description: Optional[str] = None

class GradingRubric(BaseModel):
    criteria: List[RubricCriterion]
    max_score: int = Field(ge=1, le=100)

class GenerationParams(BaseModel):
    questions_count: int = Field(ge=1, le=20, default=5)
    question_types: List[QuestionType]
    bloom_levels: List[BloomLevel]
    include_explanation: bool = True
    language: str = "ru"

class QuestionOption(BaseModel):
    id: str
    text: str
    is_correct: bool = False

# ─────────────────────────────────────────
# Create/Update Schemas
# ─────────────────────────────────────────

class HomeworkCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    class_id: int
    due_date: datetime

    # AI settings
    ai_generation_enabled: bool = False
    ai_check_enabled: bool = False
    target_difficulty: str = "auto"
    personalization_enabled: bool = False

    # Late policy
    late_submission_allowed: bool = False
    late_penalty_per_day: int = Field(ge=0, le=100, default=0)
    grace_period_hours: int = Field(ge=0, le=72, default=0)

class HomeworkTaskCreate(BaseModel):
    paragraph_id: int
    task_type: TaskType
    sort_order: int = 0
    max_attempts: int = Field(ge=1, le=10, default=1)

    # AI generation
    ai_prompt_template: Optional[str] = None
    generation_params: Optional[GenerationParams] = None

class QuestionCreate(BaseModel):
    question_text: str = Field(min_length=10)
    question_type: QuestionType
    options: Optional[List[QuestionOption]] = None
    correct_answer: Optional[str] = None
    points: int = Field(ge=1, le=100, default=1)
    bloom_level: Optional[BloomLevel] = None
    grading_rubric: Optional[GradingRubric] = None

    @field_validator('options')
    def validate_options(cls, v, info):
        if info.data.get('question_type') in ['single_choice', 'multiple_choice']:
            if not v or len(v) < 2:
                raise ValueError('Choice questions require at least 2 options')
        return v

# ─────────────────────────────────────────
# Response Schemas
# ─────────────────────────────────────────

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    question_type: QuestionType
    options: Optional[List[QuestionOption]]
    points: int
    bloom_level: Optional[BloomLevel]
    version: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class HomeworkTaskResponse(BaseModel):
    id: int
    paragraph_id: int
    paragraph_title: Optional[str] = None
    task_type: TaskType
    sort_order: int
    max_attempts: int
    ai_generated: bool
    questions: List[QuestionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class HomeworkResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: HomeworkStatus
    due_date: datetime
    class_id: int
    class_name: Optional[str] = None

    ai_generation_enabled: bool
    ai_check_enabled: bool

    late_submission_allowed: bool
    late_penalty_per_day: int

    tasks: List[HomeworkTaskResponse] = []

    # Stats
    total_students: int = 0
    submitted_count: int = 0
    graded_count: int = 0

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ─────────────────────────────────────────
# Student-facing Schemas
# ─────────────────────────────────────────

class StudentHomeworkResponse(BaseModel):
    """Homework как видит студент"""
    id: int
    title: str
    description: Optional[str]
    due_date: datetime
    is_late: bool

    my_status: str  # assigned, in_progress, submitted, graded
    my_score: Optional[float]
    max_score: float
    attempts_used: int
    attempts_remaining: int

    tasks: List["StudentTaskResponse"]

class StudentTaskResponse(BaseModel):
    id: int
    paragraph_id: int
    paragraph_title: str
    task_type: TaskType
    status: str
    current_attempt: int
    max_attempts: int
    questions_count: int
    answered_count: int

class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: str
    selected_options: Optional[List[str]] = None  # для choice questions

class SubmissionResult(BaseModel):
    submission_id: int
    is_correct: Optional[bool]  # None для open-ended
    score: float
    max_score: float
    ai_feedback: Optional[str]
    ai_confidence: Optional[float]
    needs_review: bool
```

### 5.2 Repository

**Файл:** `backend/app/repositories/homework_repo.py`

```python
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

class HomeworkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─────────────────────────────────────────
    # Homework CRUD
    # ─────────────────────────────────────────

    async def create(self, data: dict, school_id: int, teacher_id: int) -> Homework:
        homework = Homework(
            **data,
            school_id=school_id,
            teacher_id=teacher_id,
            status=HomeworkStatus.DRAFT
        )
        self.db.add(homework)
        await self.db.flush()
        return homework

    async def get_by_id(self, homework_id: int, school_id: int) -> Optional[Homework]:
        result = await self.db.execute(
            select(Homework)
            .options(
                selectinload(Homework.tasks)
                .selectinload(HomeworkTask.questions.and_(
                    HomeworkTaskQuestion.is_active == True
                ))
            )
            .where(Homework.id == homework_id)
            .where(Homework.school_id == school_id)
            .where(Homework.is_deleted == False)
        )
        return result.scalars().first()

    async def list_by_class(
        self,
        class_id: int,
        school_id: int,
        status: Optional[str] = None
    ) -> List[Homework]:
        query = (
            select(Homework)
            .where(Homework.class_id == class_id)
            .where(Homework.school_id == school_id)
            .where(Homework.is_deleted == False)
        )
        if status:
            query = query.where(Homework.status == status)

        query = query.order_by(Homework.due_date.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_status(
        self,
        homework_id: int,
        school_id: int,
        status: str
    ) -> Optional[Homework]:
        homework = await self.get_by_id(homework_id, school_id)
        if homework:
            homework.status = status
            await self.db.flush()
        return homework

    # ─────────────────────────────────────────
    # Tasks
    # ─────────────────────────────────────────

    async def add_task(
        self,
        homework_id: int,
        data: dict,
        school_id: int
    ) -> HomeworkTask:
        task = HomeworkTask(
            **data,
            homework_id=homework_id,
            school_id=school_id  # Денормализация
        )
        self.db.add(task)
        await self.db.flush()
        return task

    async def get_task_with_questions(
        self,
        task_id: int,
        school_id: int
    ) -> Optional[HomeworkTask]:
        result = await self.db.execute(
            select(HomeworkTask)
            .options(selectinload(HomeworkTask.questions.and_(
                HomeworkTaskQuestion.is_active == True
            )))
            .where(HomeworkTask.id == task_id)
            .where(HomeworkTask.school_id == school_id)
        )
        return result.scalars().first()

    # ─────────────────────────────────────────
    # Questions с версионированием
    # ─────────────────────────────────────────

    async def add_question(self, task_id: int, data: dict) -> HomeworkTaskQuestion:
        question = HomeworkTaskQuestion(
            **data,
            task_id=task_id,
            version=1,
            is_active=True
        )
        self.db.add(question)
        await self.db.flush()
        return question

    async def replace_question(
        self,
        question_id: int,
        new_data: dict
    ) -> HomeworkTaskQuestion:
        """Создать новую версию вопроса, деактивировать старую"""
        old_question = await self.db.get(HomeworkTaskQuestion, question_id)
        if not old_question:
            raise ValueError(f"Question {question_id} not found")

        # Деактивировать старую версию
        old_question.is_active = False

        # Создать новую версию
        new_question = HomeworkTaskQuestion(
            **new_data,
            task_id=old_question.task_id,
            version=old_question.version + 1,
            is_active=True
        )
        self.db.add(new_question)
        await self.db.flush()

        # Связать версии
        old_question.replaced_by_id = new_question.id

        return new_question

    # ─────────────────────────────────────────
    # Student assignments
    # ─────────────────────────────────────────

    async def assign_to_students(
        self,
        homework_id: int,
        student_ids: List[int]
    ) -> List[HomeworkStudent]:
        assignments = []
        for student_id in student_ids:
            assignment = HomeworkStudent(
                homework_id=homework_id,
                student_id=student_id,
                status="assigned"
            )
            self.db.add(assignment)
            assignments.append(assignment)
        await self.db.flush()
        return assignments

    async def get_student_homework(
        self,
        homework_id: int,
        student_id: int
    ) -> Optional[HomeworkStudent]:
        result = await self.db.execute(
            select(HomeworkStudent)
            .options(selectinload(HomeworkStudent.submissions))
            .where(HomeworkStudent.homework_id == homework_id)
            .where(HomeworkStudent.student_id == student_id)
        )
        return result.scalars().first()

    # ─────────────────────────────────────────
    # Submissions с попытками
    # ─────────────────────────────────────────

    async def create_submission(
        self,
        homework_student_id: int,
        task_id: int,
        attempt_number: int
    ) -> StudentTaskSubmission:
        submission = StudentTaskSubmission(
            homework_student_id=homework_student_id,
            task_id=task_id,
            attempt_number=attempt_number,
            status="in_progress",
            started_at=datetime.utcnow()
        )
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def get_attempts_count(
        self,
        homework_student_id: int,
        task_id: int
    ) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(StudentTaskSubmission)
            .where(StudentTaskSubmission.homework_student_id == homework_student_id)
            .where(StudentTaskSubmission.task_id == task_id)
        )
        return result.scalar() or 0

    # ─────────────────────────────────────────
    # Answers
    # ─────────────────────────────────────────

    async def save_answer(
        self,
        submission_id: int,
        question_id: int,
        answer_text: str,
        selected_options: Optional[List[str]] = None
    ) -> StudentTaskAnswer:
        answer = StudentTaskAnswer(
            submission_id=submission_id,
            question_id=question_id,
            answer_text=answer_text,
            selected_options=selected_options,
            submitted_at=datetime.utcnow()
        )
        self.db.add(answer)
        await self.db.flush()
        return answer

    async def get_answers_for_review(
        self,
        school_id: int,
        limit: int = 50
    ) -> List[StudentTaskAnswer]:
        """Получить ответы, требующие проверки учителем"""
        result = await self.db.execute(
            select(StudentTaskAnswer)
            .join(StudentTaskSubmission)
            .join(HomeworkStudent)
            .join(Homework)
            .where(Homework.school_id == school_id)
            .where(StudentTaskAnswer.flagged_for_review == True)
            .where(StudentTaskAnswer.teacher_override_score.is_(None))
            .order_by(StudentTaskAnswer.submitted_at)
            .limit(limit)
        )
        return result.scalars().all()
```

### 5.3 Чеклист Фазы 2 ✅

- [x] Создать `backend/app/schemas/homework.py`
- [x] Создать `backend/app/repositories/homework_repo.py`
- [x] Обновить `backend/app/repositories/__init__.py`
- [x] Обновить `backend/app/schemas/__init__.py`
- [ ] Unit тесты для schemas (валидация)
- [ ] Unit тесты для repository

**Выполнено:** 2026-01-04 (основные файлы, тесты отложены)

---

## 6. Фаза 3: Services (бизнес-логика)

### 6.1 HomeworkService

**Файл:** `backend/app/services/homework_service.py`

```python
class HomeworkService:
    def __init__(
        self,
        homework_repo: HomeworkRepository,
        student_repo: StudentRepository,
        mastery_service: MasteryService,
        ai_service: "HomeworkAIService",
        db: AsyncSession
    ):
        self.homework_repo = homework_repo
        self.student_repo = student_repo
        self.mastery_service = mastery_service
        self.ai_service = ai_service
        self.db = db

    # ─────────────────────────────────────────
    # Создание и публикация ДЗ
    # ─────────────────────────────────────────

    async def create_homework(
        self,
        data: HomeworkCreate,
        school_id: int,
        teacher_id: int
    ) -> Homework:
        """Создать черновик ДЗ"""
        homework = await self.homework_repo.create(
            data.model_dump(exclude={'tasks'}),
            school_id=school_id,
            teacher_id=teacher_id
        )
        return homework

    async def publish_homework(
        self,
        homework_id: int,
        school_id: int
    ) -> Homework:
        """Опубликовать ДЗ и назначить студентам"""
        homework = await self.homework_repo.get_by_id(homework_id, school_id)
        if not homework:
            raise ValueError("Homework not found")

        if homework.status != HomeworkStatus.DRAFT:
            raise ValueError("Can only publish draft homework")

        if not homework.tasks:
            raise ValueError("Homework must have at least one task")

        # Получить студентов класса
        students = await self.student_repo.list_by_class(
            homework.class_id, school_id
        )

        if not students:
            raise ValueError("No students in class")

        # Назначить всем студентам
        student_ids = [s.id for s in students]
        await self.homework_repo.assign_to_students(homework_id, student_ids)

        # Обновить статус
        homework = await self.homework_repo.update_status(
            homework_id, school_id, HomeworkStatus.PUBLISHED
        )

        return homework

    # ─────────────────────────────────────────
    # AI генерация вопросов
    # ─────────────────────────────────────────

    async def generate_questions_for_task(
        self,
        task_id: int,
        school_id: int,
        regenerate: bool = False
    ) -> List[HomeworkTaskQuestion]:
        """Сгенерировать вопросы AI для задачи"""
        task = await self.homework_repo.get_task_with_questions(task_id, school_id)
        if not task:
            raise ValueError("Task not found")

        if not task.generation_params:
            raise ValueError("Task has no generation params")

        # Если есть вопросы и не регенерация — ошибка
        if task.questions and not regenerate:
            raise ValueError("Task already has questions. Use regenerate=True")

        # Деактивировать старые вопросы при регенерации
        if regenerate:
            for q in task.questions:
                q.is_active = False

        # Генерация через AI сервис
        questions = await self.ai_service.generate_questions(
            paragraph_id=task.paragraph_id,
            params=GenerationParams(**task.generation_params),
            task_id=task_id
        )

        # Сохранить вопросы
        saved = []
        for q_data in questions:
            question = await self.homework_repo.add_question(task_id, q_data)
            saved.append(question)

        # Пометить задачу как AI-generated
        task.ai_generated = True

        return saved

    # ─────────────────────────────────────────
    # Выполнение студентом
    # ─────────────────────────────────────────

    async def start_task(
        self,
        homework_id: int,
        task_id: int,
        student_id: int
    ) -> StudentTaskSubmission:
        """Начать выполнение задачи"""
        hw_student = await self.homework_repo.get_student_homework(
            homework_id, student_id
        )
        if not hw_student:
            raise ValueError("Homework not assigned to student")

        # Проверить попытки
        task = await self.homework_repo.get_task_with_questions(
            task_id, hw_student.homework.school_id
        )
        attempts_used = await self.homework_repo.get_attempts_count(
            hw_student.id, task_id
        )

        if attempts_used >= task.max_attempts:
            raise ValueError(f"Max attempts ({task.max_attempts}) reached")

        # Создать submission
        submission = await self.homework_repo.create_submission(
            hw_student.id,
            task_id,
            attempt_number=attempts_used + 1
        )

        # Обновить статус студента
        if hw_student.status == "assigned":
            hw_student.status = "in_progress"

        return submission

    async def submit_answer(
        self,
        submission_id: int,
        question_id: int,
        answer_text: str,
        selected_options: Optional[List[str]] = None,
        student_id: int = None
    ) -> SubmissionResult:
        """Отправить ответ на вопрос"""
        # Сохранить ответ
        answer = await self.homework_repo.save_answer(
            submission_id, question_id, answer_text, selected_options
        )

        # Получить вопрос для проверки
        question = await self.db.get(HomeworkTaskQuestion, question_id)

        # Автоматическая проверка
        if question.question_type in ['single_choice', 'multiple_choice', 'true_false']:
            # Простая проверка правильности
            is_correct = self._check_choice_answer(question, selected_options)
            answer.is_correct = is_correct
            answer.score = question.points if is_correct else 0
            answer.max_score = question.points

        elif question.question_type in ['short_answer']:
            # Fuzzy matching
            is_correct = self._check_short_answer(question, answer_text)
            answer.is_correct = is_correct
            answer.score = question.points if is_correct else 0
            answer.max_score = question.points

        elif question.question_type == 'open_ended':
            # AI проверка
            submission = await self.db.get(StudentTaskSubmission, submission_id)
            homework = submission.homework_student.homework

            if homework.ai_check_enabled:
                ai_result = await self.ai_service.grade_answer(
                    question=question,
                    answer_text=answer_text,
                    student_id=student_id
                )
                answer.ai_score = ai_result.score
                answer.ai_confidence = ai_result.confidence
                answer.ai_feedback = ai_result.feedback
                answer.ai_rubric_scores = ai_result.rubric_scores
                answer.flagged_for_review = ai_result.confidence < 0.7
                answer.score = ai_result.score * question.points
            else:
                # Ожидает проверки учителем
                answer.flagged_for_review = True

            answer.max_score = question.points

        await self.db.flush()

        return SubmissionResult(
            submission_id=submission_id,
            is_correct=answer.is_correct,
            score=answer.score,
            max_score=answer.max_score,
            ai_feedback=answer.ai_feedback,
            ai_confidence=answer.ai_confidence,
            needs_review=answer.flagged_for_review or False
        )

    # ─────────────────────────────────────────
    # Late submission
    # ─────────────────────────────────────────

    async def calculate_late_penalty(
        self,
        homework: Homework,
        submission_time: datetime
    ) -> tuple[bool, float]:
        """Рассчитать штраф за опоздание"""
        if submission_time <= homework.due_date:
            return False, 0.0

        if not homework.late_submission_allowed:
            raise ValueError("Late submission not allowed")

        # Льготный период
        grace_deadline = homework.due_date + timedelta(hours=homework.grace_period_hours)
        if submission_time <= grace_deadline:
            return False, 0.0

        # Расчёт дней опоздания
        days_late = (submission_time - grace_deadline).days + 1

        if days_late > homework.max_late_days:
            raise ValueError(f"Submission too late (>{homework.max_late_days} days)")

        penalty = min(days_late * homework.late_penalty_per_day, 100)
        return True, penalty

    # ─────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────

    def _check_choice_answer(
        self,
        question: HomeworkTaskQuestion,
        selected: List[str]
    ) -> bool:
        correct_ids = [
            opt['id'] for opt in question.options
            if opt.get('is_correct')
        ]
        return set(selected or []) == set(correct_ids)

    def _check_short_answer(
        self,
        question: HomeworkTaskQuestion,
        answer: str
    ) -> bool:
        # Нормализация и сравнение
        normalized = answer.strip().lower()
        correct = (question.correct_answer or '').strip().lower()
        return normalized == correct
```

### 6.2 Чеклист Фазы 3 ✅

- [x] Создать `backend/app/services/homework_service.py`
- [x] Создать `backend/app/services/homework_ai_service.py`
- [x] Обновить `backend/app/services/__init__.py`
- [ ] Integration тесты для HomeworkService

**Выполнено:** 2026-01-04 (основные файлы, тесты отложены)

---

## 7. Фаза 4: API Endpoints

> **Статус: ✅ Выполнено 2026-01-04**

### 7.1 Teacher Endpoints

**Файл:** `backend/app/api/v1/teachers_homework.py` (~500 строк)

#### Реализованные endpoints:

| Method | Endpoint | Описание |
|--------|----------|----------|
| `POST` | `/teachers/homework` | Создать ДЗ (draft) |
| `GET` | `/teachers/homework` | Список ДЗ учителя |
| `GET` | `/teachers/homework/{id}` | Получить ДЗ с задачами и вопросами |
| `PUT` | `/teachers/homework/{id}` | Обновить ДЗ |
| `POST` | `/teachers/homework/{id}/publish` | Опубликовать и назначить студентам |
| `POST` | `/teachers/homework/{id}/close` | Закрыть ДЗ |
| `POST` | `/teachers/homework/{id}/tasks` | Добавить задачу |
| `DELETE` | `/teachers/homework/tasks/{id}` | Удалить задачу |
| `POST` | `/teachers/homework/tasks/{id}/questions` | Добавить вопрос вручную |
| `POST` | `/teachers/homework/tasks/{id}/generate-questions` | AI генерация вопросов |
| `GET` | `/teachers/homework/review-queue` | Очередь на проверку |
| `POST` | `/teachers/homework/answers/{id}/review` | Проверить ответ (override AI) |

```python
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/teachers/homework", tags=["teachers-homework"])

# ─────────────────────────────────────────
# CRUD Homework
# ─────────────────────────────────────────

@router.post("", response_model=HomeworkResponse)
async def create_homework(
    data: HomeworkCreate,
    teacher: Teacher = Depends(get_teacher_access),
    service: HomeworkService = Depends(get_homework_service)
):
    """Создать черновик ДЗ"""
    homework = await service.create_homework(
        data,
        school_id=teacher.school_id,
        teacher_id=teacher.id
    )
    return homework

@router.get("", response_model=List[HomeworkResponse])
async def list_homework(
    class_id: Optional[int] = None,
    status: Optional[HomeworkStatus] = None,
    teacher: Teacher = Depends(get_teacher_access),
    service: HomeworkService = Depends(get_homework_service)
):
    """Список ДЗ учителя"""
    return await service.list_homework(
        teacher_id=teacher.id,
        school_id=teacher.school_id,
        class_id=class_id,
        status=status
    )

@router.get("/{homework_id}", response_model=HomeworkResponse)
async def get_homework(
    homework_id: int,
    teacher: Teacher = Depends(get_teacher_access),
    service: HomeworkService = Depends(get_homework_service)
):
    """Получить ДЗ с задачами и вопросами"""
    homework = await service.get_homework(homework_id, teacher.school_id)
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    return homework

@router.post("/{homework_id}/publish", response_model=HomeworkResponse)
async def publish_homework(
    homework_id: int,
    teacher: Teacher = Depends(get_teacher_access),
    service: HomeworkService = Depends(get_homework_service)
):
    """Опубликовать ДЗ и назначить студентам"""
    try:
        return await service.publish_homework(homework_id, teacher.school_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─────────────────────────────────────────
# Tasks
# ─────────────────────────────────────────

@router.post("/{homework_id}/tasks", response_model=HomeworkTaskResponse)
async def add_task(
    homework_id: int,
    data: HomeworkTaskCreate,
    teacher: Teacher = Depends(get_teacher_access),
    service: HomeworkService = Depends(get_homework_service)
):
    """Добавить задачу к ДЗ"""
    return await service.add_task(homework_id, data, teacher.school_id)

@router.post("/tasks/{task_id}/generate-questions")
async def generate_questions(
    task_id: int,
    regenerate: bool = False,
    teacher: Teacher = Depends(get_teacher_access),
    service: HomeworkService = Depends(get_homework_service)
):
    """AI генерация вопросов для задачи"""
    try:
        questions = await service.generate_questions_for_task(
            task_id, teacher.school_id, regenerate
        )
        return {"generated": len(questions), "questions": questions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─────────────────────────────────────────
# Questions
# ─────────────────────────────────────────

@router.post("/tasks/{task_id}/questions", response_model=QuestionResponse)
async def add_question(
    task_id: int,
    data: QuestionCreate,
    teacher: Teacher = Depends(get_teacher_access),
    service: HomeworkService = Depends(get_homework_service)
):
    """Добавить вопрос вручную"""
    return await service.add_question(task_id, data, teacher.school_id)

@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    data: QuestionCreate,
    teacher: Teacher = Depends(get_teacher_access),
    service: HomeworkService = Depends(get_homework_service)
):
    """Обновить вопрос (создаст новую версию)"""
    return await service.update_question(question_id, data, teacher.school_id)

# ─────────────────────────────────────────
# Review & Grading
# ─────────────────────────────────────────

@router.get("/review-queue", response_model=List[AnswerForReview])
async def get_review_queue(
    limit: int = 50,
    teacher: Teacher = Depends(get_teacher_access),
    service: HomeworkService = Depends(get_homework_service)
):
    """Получить ответы, требующие проверки учителем"""
    return await service.get_answers_for_review(teacher.school_id, limit)

@router.post("/answers/{answer_id}/review")
async def review_answer(
    answer_id: int,
    score: float,
    feedback: Optional[str] = None,
    teacher: Teacher = Depends(get_teacher_access),
    service: HomeworkService = Depends(get_homework_service)
):
    """Проверить ответ (override AI)"""
    return await service.teacher_review(
        answer_id, score, feedback, teacher.id
    )

# ─────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────

@router.get("/{homework_id}/analytics")
async def get_homework_analytics(
    homework_id: int,
    teacher: Teacher = Depends(get_teacher_access),
    service: HomeworkService = Depends(get_homework_service)
):
    """Аналитика по ДЗ"""
    return await service.get_analytics(homework_id, teacher.school_id)
```

### 7.2 Student Endpoints

**Файл:** `backend/app/api/v1/students/homework.py` (~280 строк)

#### Реализованные endpoints:

| Method | Endpoint | Описание |
|--------|----------|----------|
| `GET` | `/students/homework` | Мои ДЗ (с фильтрами) |
| `GET` | `/students/homework/{id}` | ДЗ с прогрессом по задачам |
| `POST` | `/students/homework/{id}/tasks/{task_id}/start` | Начать выполнение задачи |
| `GET` | `/students/homework/{id}/tasks/{task_id}/questions` | Получить вопросы (без ответов) |
| `POST` | `/students/homework/submissions/{id}/answer` | Отправить ответ |
| `POST` | `/students/homework/submissions/{id}/complete` | Завершить задачу |
| `GET` | `/students/homework/submissions/{id}/results` | Результаты с feedback |

```python
router = APIRouter(tags=["Student Homework"])

@router.get("", response_model=List[StudentHomeworkResponse])
async def list_my_homework(
    status: Optional[str] = None,  # assigned, in_progress, submitted, graded
    student: Student = Depends(get_student_from_user)
):
    """Список моих ДЗ"""
    pass

@router.get("/{homework_id}", response_model=StudentHomeworkResponse)
async def get_my_homework(
    homework_id: int,
    student: Student = Depends(get_student_from_user)
):
    """Получить ДЗ с прогрессом"""
    pass

@router.post("/{homework_id}/tasks/{task_id}/start")
async def start_task(
    homework_id: int,
    task_id: int,
    student: Student = Depends(get_student_from_user),
    service: HomeworkService = Depends(get_homework_service)
):
    """Начать выполнение задачи"""
    return await service.start_task(homework_id, task_id, student.id)

@router.post("/submissions/{submission_id}/answer")
async def submit_answer(
    submission_id: int,
    data: AnswerSubmit,
    student: Student = Depends(get_student_from_user),
    service: HomeworkService = Depends(get_homework_service)
):
    """Отправить ответ на вопрос"""
    return await service.submit_answer(
        submission_id,
        data.question_id,
        data.answer_text,
        data.selected_options,
        student_id=student.id
    )

@router.post("/submissions/{submission_id}/complete")
async def complete_submission(
    submission_id: int,
    student: Student = Depends(get_student_from_user),
    service: HomeworkService = Depends(get_homework_service)
):
    """Завершить задачу"""
    return await service.complete_submission(submission_id, student.id)
```

### 7.3 Регистрация роутеров

**Файл:** `backend/app/main.py`

```python
from app.api.v1 import teachers_homework

app.include_router(
    teachers_homework.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Homework"],
)
```

**Файл:** `backend/app/api/v1/students/__init__.py`

```python
from .homework import router as homework_router

router.include_router(homework_router, tags=["Student Homework"])
```

### 7.4 Чеклист Фазы 4 ✅

- [x] Создать `backend/app/api/v1/teachers_homework.py`
- [x] Создать `backend/app/api/v1/students/homework.py`
- [x] Обновить `backend/app/api/v1/students/__init__.py`
- [x] Зарегистрировать роутеры в `main.py`
- [x] Исправить сигнатуры методов в `HomeworkService`
- [ ] OpenAPI документация (автоматически через FastAPI)
- [ ] E2E тесты для API

**Выполнено:** 2026-01-04

### 7.5 Созданные файлы

| Файл | Строк | Описание |
|------|-------|----------|
| `api/v1/teachers_homework.py` | ~500 | Teacher API для управления ДЗ |
| `api/v1/students/homework.py` | ~280 | Student API для выполнения ДЗ |

---

## 8. Фаза 5: AI Integration

### 8.1 HomeworkAIService

**Файл:** `backend/app/services/homework_ai_service.py`

```python
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

class HomeworkAIService:
    def __init__(
        self,
        llm_service: LLMService,
        embedding_service: EmbeddingService,
        paragraph_repo: ParagraphRepository,
        db: AsyncSession
    ):
        self.llm = llm_service
        self.embeddings = embedding_service
        self.paragraph_repo = paragraph_repo
        self.db = db

    async def generate_questions(
        self,
        paragraph_id: int,
        params: GenerationParams,
        task_id: int
    ) -> List[dict]:
        """Генерация вопросов на основе параграфа"""

        # 1. Получить контент параграфа
        paragraph = await self.paragraph_repo.get_by_id(paragraph_id)
        content = paragraph.content_text or ""

        # 2. Построить промпт
        prompt = self._build_generation_prompt(content, params)

        # 3. Вызвать LLM
        start_time = datetime.utcnow()
        response = await self.llm.generate(
            prompt,
            temperature=0.7,
            max_tokens=2000
        )

        # 4. Парсинг ответа
        questions = self._parse_questions(response.content)

        # 5. Логирование
        await self._log_ai_operation(
            operation_type="question_generation",
            input_context={"paragraph_id": paragraph_id, "params": params.model_dump()},
            prompt_used=prompt,
            output=questions,
            model_used=self.llm.model_name,
            tokens_input=response.usage.prompt_tokens,
            tokens_output=response.usage.completion_tokens,
            latency_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
            task_id=task_id
        )

        return questions

    async def grade_answer(
        self,
        question: HomeworkTaskQuestion,
        answer_text: str,
        student_id: int
    ) -> AIGradingResult:
        """Оценка открытого ответа через AI"""

        # 1. Построить промпт
        prompt = self._build_grading_prompt(question, answer_text)

        # 2. Вызвать LLM
        start_time = datetime.utcnow()
        response = await self.llm.generate(
            prompt,
            temperature=0.3,  # Низкая температура для консистентности
            max_tokens=1000
        )

        # 3. Парсинг результата
        result = self._parse_grading_result(response.content, question)

        # 4. Логирование
        await self._log_ai_operation(
            operation_type="answer_grading",
            input_context={
                "question_id": question.id,
                "answer_length": len(answer_text),
                "student_id": student_id
            },
            prompt_used=prompt,
            output=result.model_dump(),
            model_used=self.llm.model_name,
            tokens_input=response.usage.prompt_tokens,
            tokens_output=response.usage.completion_tokens,
            latency_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
        )

        return result

    def _build_generation_prompt(
        self,
        content: str,
        params: GenerationParams
    ) -> str:
        return f"""
Ты — эксперт по созданию образовательных вопросов для школьников Казахстана.

## Контент параграфа:
{content}

## Задание:
Создай {params.questions_count} вопросов на основе контента.

## Требования:
- Типы вопросов: {', '.join(params.question_types)}
- Когнитивные уровни (Bloom): {', '.join(params.bloom_levels)}
- Язык: {params.language}
- Каждый вопрос должен проверять понимание материала
- Для choice вопросов: 4 варианта, 1 правильный
- Для open-ended: добавь criteria для оценки

## Формат ответа (JSON):
```json
[
  {{
    "question_text": "...",
    "question_type": "single_choice|short_answer|open_ended",
    "options": [{{"id": "a", "text": "...", "is_correct": true/false}}],
    "correct_answer": "...",
    "bloom_level": "understand|apply|analyze",
    "points": 1-5,
    "grading_rubric": {{...}}  // для open_ended
  }}
]
```
"""

    def _build_grading_prompt(
        self,
        question: HomeworkTaskQuestion,
        answer: str
    ) -> str:
        rubric_text = ""
        if question.grading_rubric:
            rubric_text = f"\n## Критерии оценки:\n{json.dumps(question.grading_rubric, ensure_ascii=False, indent=2)}"

        return f"""
Ты — учитель, оценивающий ответ ученика.

## Вопрос:
{question.question_text}

## Ответ ученика:
{answer}
{rubric_text}

## Задание:
Оцени ответ по шкале 0.0-1.0, где 1.0 — идеальный ответ.

## Формат ответа (JSON):
```json
{{
  "score": 0.0-1.0,
  "confidence": 0.0-1.0,
  "feedback": "Конструктивный комментарий для ученика",
  "rubric_scores": [
    {{"name": "Критерий", "score": 0-10, "comment": "..."}}
  ],
  "strengths": ["что хорошо"],
  "improvements": ["что улучшить"]
}}
```

Важно:
- Будь объективным
- Если не уверен — ставь confidence < 0.7
- Feedback должен быть позитивным и конструктивным
"""

    async def _log_ai_operation(self, **kwargs):
        log = AIGenerationLog(**kwargs)
        self.db.add(log)
        await self.db.flush()
```

### 8.2 Персонализация по Mastery

```python
async def personalize_difficulty(
    self,
    student_id: int,
    paragraph_id: int,
    base_params: GenerationParams
) -> GenerationParams:
    """Адаптировать сложность под уровень студента"""

    # Получить mastery студента по главе
    mastery = await self.mastery_service.get_student_mastery(
        student_id, paragraph_id
    )

    params = base_params.model_copy()

    if mastery.level == 'A':
        # Высокий уровень — сложнее
        params.bloom_levels = ['analyze', 'evaluate', 'create']
        params.questions_count = max(3, params.questions_count - 2)

    elif mastery.level == 'B':
        # Средний уровень — стандарт
        params.bloom_levels = ['understand', 'apply', 'analyze']

    else:  # C или новый
        # Низкий уровень — проще
        params.bloom_levels = ['remember', 'understand', 'apply']
        params.questions_count = min(7, params.questions_count + 2)

    return params
```

### 8.3 Чеклист Фазы 5

- [ ] Создать `backend/app/services/homework_ai_service.py`
- [ ] Интегрировать с существующим `LLMService`
- [ ] Промпты на русском и казахском
- [ ] Rate limiting для AI вызовов
- [ ] Fallback при ошибках AI
- [ ] Тесты с мок LLM

---

## 9. Фаза 6: Frontend (Teacher App)

### 9.1 Структура страниц

```
teacher-app/src/app/[locale]/(dashboard)/
├── homework/
│   ├── page.tsx                    # Список ДЗ
│   ├── create/page.tsx             # Создание ДЗ
│   ├── [id]/
│   │   ├── page.tsx                # Просмотр ДЗ
│   │   ├── edit/page.tsx           # Редактирование
│   │   ├── analytics/page.tsx      # Аналитика
│   │   └── tasks/
│   │       └── [taskId]/
│   │           └── questions/page.tsx  # Управление вопросами
│   └── review/page.tsx             # Очередь проверки
```

### 9.2 Компоненты

```
teacher-app/src/components/homework/
├── HomeworkCard.tsx               # Карточка ДЗ в списке
├── HomeworkForm.tsx               # Форма создания/редактирования
├── TaskList.tsx                   # Список задач в ДЗ
├── TaskForm.tsx                   # Добавление задачи
├── QuestionList.tsx               # Список вопросов
├── QuestionForm.tsx               # Форма вопроса
├── QuestionPreview.tsx            # Предпросмотр вопроса
├── AIGenerationModal.tsx          # Модалка AI генерации
├── AISettingsPanel.tsx            # Настройки AI
├── ReviewQueue.tsx                # Очередь на проверку
├── AnswerReviewCard.tsx           # Карточка ответа для проверки
├── HomeworkAnalytics.tsx          # Графики и статистика
└── SubmissionTimeline.tsx         # Timeline сдачи
```

### 9.3 API Hooks

```typescript
// teacher-app/src/lib/hooks/use-homework.ts

export function useHomeworkList(classId?: number) {
  return useQuery({
    queryKey: ['homework', 'list', classId],
    queryFn: () => homeworkApi.list({ classId }),
  });
}

export function useHomework(id: number) {
  return useQuery({
    queryKey: ['homework', id],
    queryFn: () => homeworkApi.get(id),
  });
}

export function useCreateHomework() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: homeworkApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['homework', 'list'] });
      toast.success('ДЗ создано');
    },
  });
}

export function usePublishHomework() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => homeworkApi.publish(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['homework', id] });
      toast.success('ДЗ опубликовано');
    },
  });
}

export function useGenerateQuestions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, regenerate }: { taskId: number; regenerate?: boolean }) =>
      homeworkApi.generateQuestions(taskId, regenerate),
    onSuccess: (data, { taskId }) => {
      queryClient.invalidateQueries({ queryKey: ['homework'] });
      toast.success(`Сгенерировано ${data.generated} вопросов`);
    },
  });
}

export function useReviewQueue() {
  return useQuery({
    queryKey: ['homework', 'review-queue'],
    queryFn: () => homeworkApi.getReviewQueue(),
    refetchInterval: 30000, // Обновлять каждые 30 сек
  });
}

export function useReviewAnswer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ answerId, score, feedback }: ReviewData) =>
      homeworkApi.reviewAnswer(answerId, score, feedback),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['homework', 'review-queue'] });
      toast.success('Ответ проверен');
    },
  });
}
```

### 9.4 Чеклист Фазы 6

- [ ] Страница списка ДЗ
- [ ] Форма создания ДЗ с wizard
- [ ] Добавление задач из параграфов
- [ ] AI генерация вопросов (UI)
- [ ] Ручное добавление/редактирование вопросов
- [ ] Публикация ДЗ
- [ ] Очередь проверки (review queue)
- [ ] Аналитика по ДЗ
- [ ] Локализация (RU/KZ)

---

## 10. Фаза 7: Frontend (Student App)

### 10.1 Структура страниц

```
student-app/src/app/[locale]/(app)/
├── homework/
│   ├── page.tsx                    # Список моих ДЗ
│   └── [id]/
│       ├── page.tsx                # Просмотр ДЗ
│       └── tasks/
│           └── [taskId]/
│               └── page.tsx        # Выполнение задачи
```

### 10.2 Компоненты

```
student-app/src/components/homework/
├── HomeworkList.tsx               # Список ДЗ с фильтрами
├── HomeworkCard.tsx               # Карточка ДЗ (статус, дедлайн)
├── TaskProgress.tsx               # Прогресс по задачам
├── QuestionRenderer.tsx           # Отображение вопроса по типу
├── ChoiceQuestion.tsx             # Single/Multiple choice
├── ShortAnswerQuestion.tsx        # Короткий ответ
├── OpenEndedQuestion.tsx          # Развёрнутый ответ
├── AnswerFeedback.tsx             # Feedback после ответа
├── AIFeedbackCard.tsx             # AI оценка с rubric
├── AttemptIndicator.tsx           # Попытки (1/3)
├── DeadlineWarning.tsx            # Предупреждение о дедлайне
└── HomeworkResult.tsx             # Итоги выполнения
```

### 10.3 Чеклист Фазы 7

- [ ] Список ДЗ с фильтрами (активные, выполненные)
- [ ] Просмотр ДЗ с прогрессом
- [ ] Выполнение задачи (quiz-like UI)
- [ ] Поддержка всех типов вопросов
- [ ] Instant feedback для choice вопросов
- [ ] AI feedback для open-ended
- [ ] Отображение попыток
- [ ] Late submission warning
- [ ] Результаты после сдачи
- [ ] Локализация (RU/KZ)

---

## 11. Тестирование

### 11.1 Unit тесты

| Компонент | Покрытие | Файл |
|-----------|----------|------|
| Schemas | 90%+ | `tests/test_homework_schemas.py` |
| Repository | 80%+ | `tests/test_homework_repo.py` |
| Service | 85%+ | `tests/test_homework_service.py` |
| AI Service | 70%+ | `tests/test_homework_ai_service.py` |

### 11.2 Integration тесты

| Сценарий | Приоритет |
|----------|-----------|
| Создание и публикация ДЗ | High |
| AI генерация вопросов | High |
| Выполнение студентом | High |
| Late submission | Medium |
| Teacher review | Medium |
| Версионирование вопросов | Low |

### 11.3 E2E тесты

```typescript
// Playwright tests
describe('Homework Flow', () => {
  test('Teacher creates and publishes homework', async () => {});
  test('Student completes homework', async () => {});
  test('Teacher reviews AI-graded answers', async () => {});
  test('Late submission with penalty', async () => {});
});
```

---

## 12. Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| AI генерирует некорректные вопросы | Medium | High | Human review, confidence threshold |
| AI неправильно оценивает ответы | Medium | High | `flagged_for_review`, teacher override |
| Высокие затраты на AI | Medium | Medium | Rate limiting, caching, batching |
| Студенты злоупотребляют попытками | Low | Low | `max_attempts` ограничение |
| Потеря данных при регенерации | Medium | High | Версионирование вопросов |
| Сложность миграции | Low | Medium | Тестирование на dev среде |

---

## Приложение A: Оценка трудозатрат

| Фаза | Задачи | Сложность |
|------|--------|-----------|
| Фаза 1 | Models + Migrations | Medium |
| Фаза 2 | Schemas + Repos | Medium |
| Фаза 3 | Services | High |
| Фаза 4 | API Endpoints | Medium |
| Фаза 5 | AI Integration | High |
| Фаза 6 | Teacher Frontend | High |
| Фаза 7 | Student Frontend | Medium |
| Тестирование | All | Medium |

---

## Приложение B: Зависимости между фазами

```
Фаза 1 (Models) ──┬──▶ Фаза 2 (Schemas/Repos)
                  │
                  └──▶ Фаза 3 (Services) ──▶ Фаза 4 (API)
                                │
                                └──▶ Фаза 5 (AI) ──┬──▶ Фаза 6 (Teacher UI)
                                                   │
                                                   └──▶ Фаза 7 (Student UI)
```

**Параллельная работа возможна:**
- Фаза 2 и Фаза 5 (промпты) могут идти параллельно
- Фаза 6 и Фаза 7 могут идти параллельно после Фазы 4

---

*Документ будет обновляться по мере реализации.*
