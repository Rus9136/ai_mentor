# Техническое задание для AI: Создание адаптивной образовательной платформы

> **Область проекта:** Backend API + Админ панель
> **Технологии:** Python, FastAPI, PostgreSQL, SQLAlchemy, pgvector
> **Архитектура:** Multi-tenant REST API с Row Level Security
>
> **Важно:** Мобильное приложение разрабатывается в отдельном проекте и будет использовать созданный API.

## 1. ОПИСАНИЕ ПРОЕКТА

### 1.1 Общая концепция
Создать backend и админ панель для адаптивной образовательной платформы с интеллектуальной системой оценки прогресса. Платформа автоматически группирует учеников по уровню усвоения материала (A/B/C) и предоставляет учителям рекомендации по индивидуализации обучения. Мобильное приложение будет разрабатываться в отдельном проекте.

### 1.2 Целевая аудитория
- **Ученики** (7-11 классы): проходят тесты через мобильное приложение, получают персонализированные задания
- **Учителя**: используют админ панель для мониторинга прогресса класса, получают рекомендации по работе с группами
- **Родители**: отслеживают успеваемость детей через мобильное приложение
- **Администраторы/Content Managers**: используют админ панель для управления контентом, создания тестов, управления пользователями

### 1.3 Ключевые особенности
- **Адаптивное обучение**: система автоматически определяет уровень каждого ученика
- **Привязка к программе**: тесты синхронизированы с текущими темами школьной программы
- **RAG-система**: интеллектуальный поиск по учебникам и генерация пояснений
- **Multi-tenancy**: каждая школа — изолированный tenant с RLS
- **Офлайн-режим**: работа без интернета с последующей синхронизацией

### 1.4 Бизнес-модель
Продажа лицензий школам (SaaS модель), каждая школа — отдельный tenant с полной изоляцией данных.

---

## 2. ТЕХНИЧЕСКОЕ ЗАДАНИЕ ДЛЯ AI

**Задача**: Создать backend (REST API), базу данных и админ панель для управления образовательной платформой. Мобильное приложение разрабатывается отдельно и будет использовать созданный API.

### 2.1 Технологический стек

**Backend:**
- Python 3.11+
- FastAPI для REST API
- PostgreSQL 15+ с расширениями: pgvector, uuid-ossp
- SQLAlchemy 2.0+ для ORM
- Alembic для миграций
- Pydantic для валидации
- Python-jose для JWT аутентификации
- LangChain/LlamaIndex для RAG компонента
- Redis для кеширования (опционально)

**База данных:**
- PostgreSQL с Row Level Security (RLS)
- pgvector для векторных embeddings
- Multi-tenant архитектура

**Админ панель:**
- FastAPI Admin / Flask-Admin или отдельный SPA (React/Vue.js)
- Интерфейс для управления контентом, пользователями, мониторинга
- Dashboard для учителей и администраторов

**Инфраструктура:**
- Docker & Docker Compose для локальной разработки
- Poetry или pip-tools для управления зависимостями
- pytest для тестирования
- pre-commit hooks для code quality

---

## 3. СТРУКТУРА ПРОЕКТА

Создай следующую структуру:

```
education-platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application
│   │   ├── config.py               # Configuration settings
│   │   ├── database.py             # Database connection
│   │   ├── dependencies.py         # FastAPI dependencies
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py         # JWT, password hashing
│   │   │   ├── rls.py              # RLS context management
│   │   │   └── tenancy.py          # Multi-tenant utilities
│   │   │
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Base model with school_id
│   │   │   ├── school.py
│   │   │   ├── user.py
│   │   │   ├── content.py          # Textbooks, chapters, paragraphs
│   │   │   ├── test.py             # Tests, questions
│   │   │   ├── student.py          # Students, progress
│   │   │   └── analytics.py        # Mastery history, stats
│   │   │
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── school.py
│   │   │   ├── user.py
│   │   │   ├── content.py
│   │   │   ├── test.py
│   │   │   └── analytics.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # API dependencies
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py       # Main router
│   │   │       ├── auth.py         # Authentication endpoints
│   │   │       ├── schools.py
│   │   │       ├── users.py
│   │   │       ├── content.py      # CRUD for textbooks/chapters
│   │   │       ├── tests.py        # Test management
│   │   │       ├── student.py      # Student progress, attempts
│   │   │       ├── teacher.py      # Teacher dashboard
│   │   │       ├── parent.py       # Parent views
│   │   │       └── analytics.py    # Analytics endpoints
│   │   │
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── content_service.py
│   │   │   ├── test_service.py
│   │   │   ├── mastery_service.py  # A/B/C grouping logic
│   │   │   ├── rag_service.py      # RAG for explanations
│   │   │   └── sync_service.py     # Offline sync logic
│   │   │
│   │   ├── repositories/           # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── school_repo.py
│   │   │   ├── user_repo.py
│   │   │   ├── content_repo.py
│   │   │   ├── test_repo.py
│   │   │   └── analytics_repo.py
│   │   │
│   │   ├── admin/                  # Admin panel
│   │   │   ├── __init__.py
│   │   │   ├── views.py            # Admin views
│   │   │   ├── dashboard.py        # Admin dashboard
│   │   │   └── templates/          # HTML templates (if not SPA)
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── embeddings.py       # OpenAI embeddings wrapper
│   │       └── validators.py
│   │
│   ├── alembic/                    # Database migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_content.py
│   │   └── test_mastery.py
│   │
│   ├── scripts/
│   │   ├── init_db.py              # Initial DB setup
│   │   ├── seed_data.py            # Seed sample data
│   │   └── create_embeddings.py    # Generate embeddings
│   │
│   ├── .env.example
│   ├── .gitignore
│   ├── pyproject.toml              # Poetry config
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── docs/
│   ├── API.md                      # API documentation
│   ├── DATABASE.md                 # DB schema documentation
│   ├── DEPLOYMENT.md
│   └── ARCHITECTURE.md
│
└── README.md
```

---

## 4. ДЕТАЛЬНЫЕ ТРЕБОВАНИЯ К РЕАЛИЗАЦИИ

### 4.1 База данных (PostgreSQL)

**Создай полную схему БД со следующими таблицами:**

#### 4.1.1 Core Tables

```sql
-- Multi-tenancy
CREATE TABLE schools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    region VARCHAR(100),
    license_type VARCHAR(50) CHECK (license_type IN ('basic', 'premium', 'enterprise')),
    active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TYPE user_role AS ENUM ('admin', 'teacher', 'student', 'parent', 'content_manager');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role user_role NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, email)
);

CREATE INDEX idx_users_school_id ON users(school_id);
CREATE INDEX idx_users_email ON users(email);
```

#### 4.1.2 Content Management Tables

```sql
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    name_kz VARCHAR(100),  -- казахский перевод
    name_ru VARCHAR(100),  -- русский перевод
    grade_level INTEGER CHECK (grade_level BETWEEN 1 AND 11),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE textbooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    publisher VARCHAR(255),
    year INTEGER,
    isbn VARCHAR(20),
    version VARCHAR(50),
    language VARCHAR(10) DEFAULT 'ru',
    cover_image_url TEXT,
    file_url TEXT,  -- PDF файл учебника
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    textbook_id UUID REFERENCES textbooks(id) ON DELETE CASCADE,
    parent_chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    chapter_number VARCHAR(20) NOT NULL,  -- "1", "1.1", "1.1.2"
    title VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,
    learning_objectives TEXT[],  -- цели обучения
    keywords TEXT[],
    estimated_duration_minutes INTEGER,  -- примерное время изучения
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE paragraphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    paragraph_number VARCHAR(20),
    title VARCHAR(255),
    content TEXT NOT NULL,
    content_cleaned TEXT,  -- очищенный текст для RAG
    content_html TEXT,  -- форматированный HTML
    page_number INTEGER,
    keywords TEXT[],
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    order_index INTEGER NOT NULL,
    has_images BOOLEAN DEFAULT false,
    has_formulas BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Для RAG (векторное хранилище)
CREATE TABLE paragraph_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    paragraph_id UUID REFERENCES paragraphs(id) ON DELETE CASCADE,
    embedding vector(1536),  -- OpenAI ada-002 размерность
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER DEFAULT 0,
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_paragraph_embeddings_vector 
ON paragraph_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

#### 4.1.3 Testing System Tables

```sql
CREATE TYPE test_type AS ENUM ('lesson', 'chapter', 'final', 'practice');
CREATE TYPE question_type AS ENUM ('multiple_choice', 'true_false', 'short_answer', 'matching', 'ordering');

CREATE TABLE tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    test_type test_type NOT NULL,
    duration_minutes INTEGER,
    passing_score INTEGER NOT NULL,  -- минимальный процент для прохождения
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    max_attempts INTEGER DEFAULT 3,
    shuffle_questions BOOLEAN DEFAULT true,
    show_correct_answers BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    test_id UUID REFERENCES tests(id) ON DELETE CASCADE,
    question_type question_type NOT NULL,
    question_text TEXT NOT NULL,
    question_html TEXT,  -- для форматирования
    correct_answer TEXT,  -- JSON для сложных типов
    explanation TEXT NOT NULL,  -- пояснение к правильному ответу
    explanation_source UUID REFERENCES paragraphs(id),  -- ссылка на параграф
    points INTEGER DEFAULT 1,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    order_index INTEGER,
    time_limit_seconds INTEGER,
    options JSONB,  -- варианты ответов для multiple_choice
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_questions_test_id ON questions(test_id);
```

#### 4.1.4 Student Management Tables

```sql
CREATE TABLE teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    employee_id VARCHAR(50),
    subjects UUID[],  -- массив subject_id
    bio TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    student_id VARCHAR(50),
    grade_level INTEGER CHECK (grade_level BETWEEN 1 AND 11),
    class_name VARCHAR(50),  -- "7А", "8Б"
    date_of_birth DATE,
    enrollment_date DATE,
    overall_mastery_level VARCHAR(1) DEFAULT 'C' CHECK (overall_mastery_level IN ('A', 'B', 'C')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE parents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    phone_number VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE parent_student_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES parents(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) CHECK (relation_type IN ('mother', 'father', 'guardian', 'other')),
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(parent_id, student_id)
);

CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,  -- "7А"
    grade_level INTEGER CHECK (grade_level BETWEEN 1 AND 11),
    teacher_id UUID REFERENCES teachers(id),
    academic_year VARCHAR(20),  -- "2024-2025"
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE class_students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(class_id, student_id)
);
```

#### 4.1.5 Progress Tracking & Analytics Tables

```sql
CREATE TYPE attempt_status AS ENUM ('started', 'in_progress', 'completed', 'abandoned');

CREATE TABLE test_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    test_id UUID REFERENCES tests(id) ON DELETE CASCADE,
    status attempt_status DEFAULT 'started',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    score INTEGER,
    max_score INTEGER,
    percentage DECIMAL(5,2),
    passed BOOLEAN,
    time_spent_seconds INTEGER,
    attempt_number INTEGER DEFAULT 1,
    
    -- Для офлайн режима
    is_offline_synced BOOLEAN DEFAULT false,
    synced_at TIMESTAMPTZ,
    device_id VARCHAR(255),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE answer_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    attempt_id UUID REFERENCES test_attempts(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    student_answer TEXT,
    is_correct BOOLEAN,
    points_earned INTEGER,
    time_spent_seconds INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- История изменения уровня мастерства
CREATE TABLE mastery_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    previous_level VARCHAR(1) CHECK (previous_level IN ('A', 'B', 'C')),
    new_level VARCHAR(1) CHECK (new_level IN ('A', 'B', 'C')),
    change_reason VARCHAR(50),  -- 'test_passed', 'test_failed', 'improved', 'declined'
    test_attempt_id UUID REFERENCES test_attempts(id),
    score_change DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Агрегированная статистика по ученику и главе
CREATE TABLE student_chapter_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    
    total_attempts INTEGER DEFAULT 0,
    successful_attempts INTEGER DEFAULT 0,
    failed_attempts INTEGER DEFAULT 0,
    average_score DECIMAL(5,2),
    best_score DECIMAL(5,2),
    latest_score DECIMAL(5,2),
    
    current_mastery_level VARCHAR(1) DEFAULT 'C' CHECK (current_mastery_level IN ('A', 'B', 'C')),
    mastery_score DECIMAL(5,2) DEFAULT 0,  -- 0-100
    trend VARCHAR(20) DEFAULT 'stable',  -- 'improving', 'stable', 'declining'
    
    total_time_spent_seconds INTEGER DEFAULT 0,
    last_attempt_date TIMESTAMPTZ,
    first_attempt_date TIMESTAMPTZ,
    
    strengths TEXT[],  -- темы, которые усвоены хорошо
    weaknesses TEXT[],  -- темы, требующие внимания
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(student_id, chapter_id)
);

CREATE INDEX idx_student_chapter_stats_student ON student_chapter_stats(student_id);
CREATE INDEX idx_student_chapter_stats_chapter ON student_chapter_stats(chapter_id);
CREATE INDEX idx_student_chapter_stats_mastery ON student_chapter_stats(current_mastery_level);
```

#### 4.1.6 Offline Sync Tables

```sql
CREATE TABLE offline_sync_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,  -- 'test_attempt', 'answer_submission'
    entity_id UUID NOT NULL,
    operation VARCHAR(20) NOT NULL,  -- 'create', 'update'
    payload JSONB NOT NULL,
    device_id VARCHAR(255),
    client_timestamp TIMESTAMPTZ NOT NULL,
    synced BOOLEAN DEFAULT false,
    synced_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_offline_sync_queue_student ON offline_sync_queue(student_id) WHERE NOT synced;
```

---

### 4.2 Row Level Security (RLS) Политики

**Для КАЖДОЙ таблицы с school_id создай RLS политики:**

```sql
-- Пример для students table
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- Админ школы видит всех учеников своей школы
CREATE POLICY admin_all_students ON students
    FOR ALL
    TO authenticated
    USING (
        school_id = current_setting('app.current_school_id', true)::UUID
        AND EXISTS (
            SELECT 1 FROM users u
            WHERE u.id = current_setting('app.current_user_id', true)::UUID
            AND u.role = 'admin'
            AND u.school_id = students.school_id
        )
    );

-- Учитель видит учеников своих классов
CREATE POLICY teacher_view_students ON students
    FOR SELECT
    TO authenticated
    USING (
        school_id = current_setting('app.current_school_id', true)::UUID
        AND (
            EXISTS (
                SELECT 1 FROM users u
                JOIN teachers t ON t.user_id = u.id
                JOIN classes c ON c.teacher_id = t.id
                JOIN class_students cs ON cs.class_id = c.id
                WHERE u.id = current_setting('app.current_user_id', true)::UUID
                AND cs.student_id = students.id
            )
            OR EXISTS (
                SELECT 1 FROM users u
                WHERE u.id = current_setting('app.current_user_id', true)::UUID
                AND u.role = 'admin'
            )
        )
    );

-- Родитель видит только своих детей
CREATE POLICY parent_view_own_children ON students
    FOR SELECT
    TO authenticated
    USING (
        school_id = current_setting('app.current_school_id', true)::UUID
        AND id IN (
            SELECT psr.student_id
            FROM parent_student_relations psr
            JOIN parents p ON p.id = psr.parent_id
            JOIN users u ON u.id = p.user_id
            WHERE u.id = current_setting('app.current_user_id', true)::UUID
        )
    );

-- Ученик видит только себя
CREATE POLICY student_view_self ON students
    FOR SELECT
    TO authenticated
    USING (
        user_id = current_setting('app.current_user_id', true)::UUID
    );
```

**Реализуй подобные политики для всех таблиц с учетом ролей.**

---

### 4.3 Backend API (FastAPI)

#### 4.3.1 Основные модули

**`app/main.py`** - точка входа:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # настроить для production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**`app/config.py`** - конфигурация:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Education Platform API"
    API_V1_STR: str = "/api/v1"
    
    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str = None
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI for RAG
    OPENAI_API_KEY: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**`app/database.py`** - подключение к БД:
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 4.3.2 RLS Context Manager

**`app/core/rls.py`**:
```python
from sqlalchemy.orm import Session
from contextlib import contextmanager
from uuid import UUID

@contextmanager
def rls_context(db: Session, school_id: UUID, user_id: UUID):
    """
    Устанавливает контекст RLS для текущей сессии
    """
    try:
        db.execute(f"SET app.current_school_id = '{school_id}'")
        db.execute(f"SET app.current_user_id = '{user_id}'")
        yield db
    finally:
        db.execute("RESET app.current_school_id")
        db.execute("RESET app.current_user_id")
```

#### 4.3.3 Алгоритм группировки (Mastery Service)

**`app/services/mastery_service.py`**:
```python
from typing import List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from app.models import TestAttempt, StudentChapterStats
from datetime import datetime, timedelta

class MasteryService:
    
    @staticmethod
    def calculate_mastery_level(
        db: Session,
        student_id: UUID,
        chapter_id: UUID
    ) -> Tuple[str, float]:
        """
        Вычисляет уровень мастерства (A/B/C) и mastery_score (0-100)
        
        Критерии:
        - Последние 5 попыток по главе
        - Взвешенный средний балл (новые попытки важнее)
        - Тренд (улучшается/стабильно/ухудшается)
        - Консистентность результатов
        
        Уровни:
        - A: 85%+, стабильные результаты или улучшение
        - C: <60% или стабильное ухудшение
        - B: все остальные
        """
        
        # Получаем последние 5 попыток
        recent_attempts = db.query(TestAttempt).filter(
            TestAttempt.student_id == student_id,
            TestAttempt.test_id.in_(
                # подзапрос для получения test_id по chapter_id
            ),
            TestAttempt.status == 'completed'
        ).order_by(TestAttempt.completed_at.desc()).limit(5).all()
        
        if not recent_attempts:
            return ('C', 0.0)
        
        # Взвешенный средний (новые попытки важнее)
        weights = [0.35, 0.25, 0.20, 0.12, 0.08]
        weighted_avg = sum(
            attempt.percentage * weight 
            for attempt, weight in zip(recent_attempts, weights)
        ) / sum(weights[:len(recent_attempts)])
        
        # Тренд: сравниваем первые 2 и последние 2 попытки
        if len(recent_attempts) >= 3:
            recent_avg = sum(a.percentage for a in recent_attempts[:2]) / 2
            older_avg = sum(a.percentage for a in recent_attempts[-2:]) / 2
            trend = recent_avg - older_avg
        else:
            trend = 0
        
        # Консистентность (стандартное отклонение)
        scores = [a.percentage for a in recent_attempts]
        std_dev = (sum((x - weighted_avg) ** 2 for x in scores) / len(scores)) ** 0.5
        
        # Определяем уровень
        if weighted_avg >= 85 and (trend >= 0 or std_dev < 10):
            level = 'A'
            mastery_score = min(100, weighted_avg + (trend * 0.2))
        elif weighted_avg < 60 or (weighted_avg < 70 and trend < -10):
            level = 'C'
            mastery_score = max(0, weighted_avg + (trend * 0.2))
        else:
            level = 'B'
            mastery_score = weighted_avg
        
        return (level, round(mastery_score, 2))
    
    @staticmethod
    def update_student_stats(
        db: Session,
        student_id: UUID,
        chapter_id: UUID,
        attempt: TestAttempt
    ):
        """
        Обновляет статистику студента после прохождения теста
        """
        stats = db.query(StudentChapterStats).filter(
            StudentChapterStats.student_id == student_id,
            StudentChapterStats.chapter_id == chapter_id
        ).first()
        
        if not stats:
            stats = StudentChapterStats(
                student_id=student_id,
                chapter_id=chapter_id,
                school_id=attempt.school_id
            )
            db.add(stats)
        
        # Обновляем счетчики
        stats.total_attempts += 1
        if attempt.passed:
            stats.successful_attempts += 1
        else:
            stats.failed_attempts += 1
        
        # Пересчитываем уровень мастерства
        new_level, mastery_score = MasteryService.calculate_mastery_level(
            db, student_id, chapter_id
        )
        
        old_level = stats.current_mastery_level
        stats.current_mastery_level = new_level
        stats.mastery_score = mastery_score
        
        # Записываем в историю, если уровень изменился
        if old_level != new_level:
            from app.models import MasteryHistory
            history = MasteryHistory(
                student_id=student_id,
                chapter_id=chapter_id,
                previous_level=old_level,
                new_level=new_level,
                test_attempt_id=attempt.id,
                school_id=attempt.school_id
            )
            db.add(history)
        
        db.commit()
        return stats
```

#### 4.3.4 RAG Service для пояснений

**`app/services/rag_service.py`**:
```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.pgvector import PGVector
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from app.core.config import settings

class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.llm = OpenAI(
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    async def get_explanation(
        self,
        question_text: str,
        student_answer: str,
        correct_answer: str,
        chapter_id: str
    ) -> str:
        """
        Генерирует персонализированное пояснение для ошибки ученика
        используя RAG по учебнику
        """
        
        # Поиск релевантных параграфов
        query = f"Тема: {question_text}. Ученик ответил: {student_answer}. Правильный ответ: {correct_answer}"
        
        # Используем pgvector для поиска похожих параграфов
        vector_store = PGVector(
            connection_string=settings.DATABASE_URL,
            embedding_function=self.embeddings,
            collection_name="paragraph_embeddings"
        )
        
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever
        )
        
        prompt = f"""
        На основе учебного материала, объясни ученику, почему его ответ "{student_answer}" 
        неправильный, а правильный ответ "{correct_answer}".
        
        Объяснение должно быть:
        - Понятным для школьника
        - Основано на материале учебника
        - Содержать примеры
        - Не более 150 слов
        
        Вопрос: {question_text}
        """
        
        explanation = await qa_chain.arun(prompt)
        return explanation
```

#### 4.3.5 Teacher Dashboard Endpoint

**`app/api/v1/teacher.py`**:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.models import Student, StudentChapterStats
from app.schemas import TeacherDashboard, StudentGroup
from app.dependencies import get_current_user, get_db

router = APIRouter()

@router.get("/dashboard/{class_id}", response_model=TeacherDashboard)
async def get_teacher_dashboard(
    class_id: str,
    chapter_id: str,  # текущая изучаемая глава
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить дашборд учителя с группировкой учеников по уровню (A/B/C)
    """
    
    # Получаем всех учеников класса
    students = db.query(Student).join(ClassStudents).filter(
        ClassStudents.class_id == class_id
    ).all()
    
    # Группируем по уровню мастерства
    groups = {'A': [], 'B': [], 'C': []}
    
    for student in students:
        stats = db.query(StudentChapterStats).filter(
            StudentChapterStats.student_id == student.id,
            StudentChapterStats.chapter_id == chapter_id
        ).first()
        
        level = stats.current_mastery_level if stats else 'C'
        groups[level].append({
            'student': student,
            'stats': stats,
            'mastery_score': stats.mastery_score if stats else 0
        })
    
    # Рекомендации для каждой группы
    recommendations = {
        'A': "Группа А: дайте более сложные задачи, олимпиадные задания",
        'B': "Группа Б: стандартные задачи с дополнительными упражнениями",
        'C': "Группа С: базовые задачи, требуется дополнительное объяснение"
    }
    
    return TeacherDashboard(
        groups=groups,
        recommendations=recommendations,
        total_students=len(students)
    )
```

---

### 4.4 Офлайн режим (Sync Service)

**`app/services/sync_service.py`**:
```python
from sqlalchemy.orm import Session
from app.models import OfflineSyncQueue, TestAttempt
from uuid import UUID
from datetime import datetime

class SyncService:
    
    @staticmethod
    def queue_offline_action(
        db: Session,
        school_id: UUID,
        student_id: UUID,
        entity_type: str,
        entity_id: UUID,
        operation: str,
        payload: dict,
        device_id: str
    ):
        """
        Добавляет действие в очередь синхронизации
        """
        queue_item = OfflineSyncQueue(
            school_id=school_id,
            student_id=student_id,
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            payload=payload,
            device_id=device_id,
            client_timestamp=datetime.utcnow()
        )
        db.add(queue_item)
        db.commit()
        return queue_item
    
    @staticmethod
    async def process_sync_queue(
        db: Session,
        student_id: UUID,
        device_id: str
    ):
        """
        Обрабатывает очередь синхронизации для студента
        """
        pending_items = db.query(OfflineSyncQueue).filter(
            OfflineSyncQueue.student_id == student_id,
            OfflineSyncQueue.device_id == device_id,
            OfflineSyncQueue.synced == False
        ).order_by(OfflineSyncQueue.client_timestamp).all()
        
        results = []
        
        for item in pending_items:
            try:
                if item.entity_type == 'test_attempt':
                    # Создаем или обновляем test_attempt
                    await SyncService._sync_test_attempt(db, item)
                
                elif item.entity_type == 'answer_submission':
                    await SyncService._sync_answer(db, item)
                
                item.synced = True
                item.synced_at = datetime.utcnow()
                results.append({'id': item.id, 'status': 'success'})
                
            except Exception as e:
                item.retry_count += 1
                item.last_error = str(e)
                results.append({'id': item.id, 'status': 'error', 'error': str(e)})
        
        db.commit()
        return results
```

---

### 4.5 Миграции (Alembic)

Создай начальную миграцию со всеми таблицами:

```bash
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
```

**`alembic/env.py`** должен импортировать все модели.

---

### 4.6 Seed данные

**`scripts/seed_data.py`**:
```python
# Создай скрипт для заполнения тестовыми данными:
# - 1 школа (тестовая)
# - Предметы (Математика, Физика для 7-9 классов)
# - 1 учебник с главами и параграфами
# - Несколько тестов с вопросами
# - Роли: 1 admin, 2 учителя, 10 учеников, 5 родителей
# - Связи родитель-ученик
```

---

### 4.7 Docker Compose

**`docker-compose.yml`**:
```yaml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_USER: eduplatform
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: eduplatform_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    command: postgres -c shared_preload_libraries=vector

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://eduplatform:secret@postgres/eduplatform_db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

---

## 5. ДОПОЛНИТЕЛЬНЫЕ ТРЕБОВАНИЯ

### 5.1 API Endpoints (минимум)

Создай следующие endpoints:

**Auth:**
- `POST /api/v1/auth/login` - вход
- `POST /api/v1/auth/refresh` - обновление токена
- `POST /api/v1/auth/logout` - выход

**Content Management (Admin/Content Manager):**
- `POST /api/v1/textbooks` - создать учебник
- `GET /api/v1/textbooks` - список учебников
- `POST /api/v1/chapters` - создать главу
- `POST /api/v1/paragraphs` - создать параграф
- `POST /api/v1/paragraphs/{id}/generate-embeddings` - генерация embeddings

**Tests (Teachers/Content Managers):**
- `POST /api/v1/tests` - создать тест
- `GET /api/v1/tests?chapter_id=xxx` - список тестов по главе
- `POST /api/v1/questions` - добавить вопрос
- `PUT /api/v1/tests/{id}` - обновить тест

**Student:**
- `GET /api/v1/student/available-tests` - доступные тесты
- `POST /api/v1/student/start-test/{test_id}` - начать тест
- `POST /api/v1/student/submit-answer` - отправить ответ
- `POST /api/v1/student/complete-test/{attempt_id}` - завершить тест
- `GET /api/v1/student/my-progress` - мой прогресс

**Teacher Dashboard:**
- `GET /api/v1/teacher/dashboard/{class_id}` - дашборд класса
- `GET /api/v1/teacher/student-details/{student_id}` - детали ученика
- `GET /api/v1/teacher/recommendations/{class_id}/{chapter_id}` - рекомендации

**Parent:**
- `GET /api/v1/parent/children` - список детей
- `GET /api/v1/parent/child-progress/{student_id}` - прогресс ребенка

**Offline Sync:**
- `POST /api/v1/sync/queue` - добавить в очередь
- `POST /api/v1/sync/process` - обработать очередь
- `GET /api/v1/sync/status` - статус синхронизации

### 5.2 Документация

Создай в папке `docs/`:
- `API.md` - описание всех endpoints с примерами
- `DATABASE.md` - схема БД с описанием таблиц
- `ARCHITECTURE.md` - архитектура системы
- `DEPLOYMENT.md` - инструкции по развертыванию

### 5.3 Тестирование

Создай базовые тесты в `backend/tests/`:
- `test_auth.py` - тесты аутентификации
- `test_mastery.py` - тесты алгоритма группировки
- `test_rls.py` - тесты RLS политик
- `test_sync.py` - тесты офлайн синхронизации

---

## 6. РЕЗУЛЬТАТ

После выполнения этого технического задания должен получиться:

1. ✅ **Полная структура проекта** с правильной организацией файлов
2. ✅ **База данных PostgreSQL** со всеми таблицами, индексами, RLS политиками
3. ✅ **FastAPI backend** с базовыми endpoints и бизнес-логикой
4. ✅ **REST API** готовое для использования мобильным приложением
5. ✅ **Админ панель** для управления контентом, пользователями и мониторинга
6. ✅ **Алгоритм группировки A/B/C** с расчетом mastery score
7. ✅ **RAG компонент** для генерации пояснений
8. ✅ **Multi-tenancy** с изоляцией на уровне БД
9. ✅ **Офлайн синхронизация** с очередью
10. ✅ **Docker Compose** для локальной разработки
11. ✅ **Seed данные** для тестирования
12. ✅ **Документация** по API и архитектуре

---

## 7. ИНСТРУКЦИИ ПО ЗАПУСКУ

После генерации проекта, пользователь должен:

```bash
# 1. Клонировать и перейти в проект
cd education-platform

# 2. Создать .env файл
cp backend/.env.example backend/.env
# Заполнить OPENAI_API_KEY и другие переменные

# 3. Запустить Docker Compose
docker-compose up -d

# 4. Применить миграции
docker-compose exec api alembic upgrade head

# 5. Заполнить seed данными
docker-compose exec api python scripts/seed_data.py

# 6. Создать embeddings для параграфов
docker-compose exec api python scripts/create_embeddings.py

# 7. API доступен на http://localhost:8000
# 8. Документация: http://localhost:8000/docs
```

---

## 8. NEXT STEPS (после базовой реализации)

После того как базовая структура будет готова, следующие шаги:

1. **Админ панель (Frontend)** - доработка UI для администраторов и учителей
2. **Websockets** - для real-time обновлений дашборда учителя
3. **Notifications** - email-уведомления для учителей и родителей
4. **Analytics Dashboard** - расширенная визуализация прогресса и статистики
5. **CI/CD** - автоматическое развертывание (GitHub Actions, GitLab CI)
6. **Monitoring** - логирование и мониторинг (Sentry, Prometheus, Grafana)
7. **API Documentation** - расширенная документация для мобильного приложения

**Примечание:** Мобильное приложение разрабатывается в отдельном проекте и использует созданное API.

---

