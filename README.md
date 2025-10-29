# AI Mentor - Адаптивная образовательная платформа

Мобильное приложение для адаптивного обучения школьников (7-11 классы) с автоматической группировкой по уровню усвоения материала.

## Ключевые особенности

- **Адаптивное обучение**: автоматическая группировка учеников на группы A/B/C по уровню мастерства
- **Multi-tenancy**: каждая школа работает как изолированный tenant с Row Level Security
- **RAG система**: персонализированные объяснения на основе учебников через OpenAI
- **Офлайн режим**: работа без интернета с последующей синхронизацией
- **Teacher Dashboard**: мониторинг прогресса класса с рекомендациями

## Технологический стек

### Backend
- **Python 3.11+**
- **FastAPI** - современный веб-фреймворк
- **PostgreSQL 15+** с расширением pgvector
- **SQLAlchemy 2.0+** - ORM
- **Alembic** - миграции БД
- **LangChain** - RAG система
- **OpenAI API** - генерация embeddings и объяснений

### Инфраструктура
- **Docker & Docker Compose**
- **Poetry** - управление зависимостями
- **pytest** - тестирование

## Быстрый старт

### Предварительные требования

- Python 3.11 или выше
- Docker и Docker Compose
- Poetry (опционально)

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd ai_mentor
```

### 2. Настройка окружения

Скопируйте пример конфигурации и настройте переменные:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите:
- `SECRET_KEY` - секретный ключ для JWT (минимум 32 символа)
- `OPENAI_API_KEY` - ваш API ключ OpenAI

### 3. Установка зависимостей

#### Вариант A: Используя Poetry (рекомендуется)

```bash
poetry install
poetry shell
```

#### Вариант B: Используя pip

```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -e .
```

### 4. Запуск базы данных

```bash
docker compose up -d postgres
```

Проверьте, что PostgreSQL запущен:

```bash
docker compose ps
docker compose logs postgres
```

### 5. Применение миграций

```bash
cd backend
alembic upgrade head
```

### 6. Запуск сервера разработки

#### Вариант A: Локально

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Вариант B: В Docker

```bash
docker compose up backend
```

### 7. Проверка работы

Откройте в браузере:
- API документация (Swagger UI): http://localhost:8000/docs
- Альтернативная документация (ReDoc): http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Структура проекта

```
ai_mentor/
├── backend/              # Backend приложение
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Security, RLS, tenancy
│   │   ├── models/      # SQLAlchemy модели
│   │   ├── schemas/     # Pydantic схемы
│   │   ├── services/    # Бизнес-логика
│   │   ├── repositories/# Data access layer
│   │   └── utils/       # Утилиты
│   ├── alembic/         # Миграции БД
│   ├── tests/           # Тесты
│   └── scripts/         # Скрипты для инициализации и seed данных
├── docs/                # Документация
│   ├── ARCHITECTURE.md  # Техническое задание
│   └── IMPLEMENTATION_STATUS.md  # Статус реализации
├── docker-compose.yml   # Docker конфигурация
├── pyproject.toml       # Зависимости и настройки проекта
└── README.md           # Этот файл
```

## Разработка

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием кода
pytest --cov=backend/app --cov-report=html

# Конкретный тест
pytest backend/tests/test_auth.py
```

### Форматирование кода

```bash
# Black
black backend/

# Ruff (линтер)
ruff check backend/
```

### Создание новой миграции

```bash
cd backend
alembic revision --autogenerate -m "описание миграции"
alembic upgrade head
```

### Заполнение тестовыми данными

```bash
python backend/scripts/seed_data.py
```

### Генерация embeddings для RAG

```bash
python backend/scripts/create_embeddings.py
```

## API Endpoints

### Аутентификация
- `POST /api/v1/auth/register` - Регистрация
- `POST /api/v1/auth/login` - Вход
- `POST /api/v1/auth/refresh` - Обновление токена
- `POST /api/v1/auth/logout` - Выход

### Студент
- `GET /api/v1/students/tests` - Список доступных тестов
- `POST /api/v1/students/tests/{test_id}/attempts` - Начать тест
- `POST /api/v1/students/attempts/{attempt_id}/submit` - Отправить ответы
- `GET /api/v1/students/progress` - Прогресс студента
- `GET /api/v1/students/mastery-level` - Текущий уровень мастерства (A/B/C)

### Учитель
- `GET /api/v1/teachers/classes/{class_id}/overview` - Обзор класса
- `GET /api/v1/teachers/students/{student_id}/progress` - Детальный прогресс студента
- `GET /api/v1/teachers/analytics/mastery-distribution` - Распределение по группам A/B/C

### Контент (Admin)
- `GET/POST/PUT/DELETE /api/v1/content/textbooks` - Управление учебниками
- `GET/POST/PUT/DELETE /api/v1/content/tests` - Управление тестами

Полная документация API: http://localhost:8000/docs

## Архитектура

### Multi-tenancy
Каждая школа изолирована через `tenant_id` с использованием PostgreSQL Row Level Security (RLS). Все запросы автоматически фильтруются на уровне БД.

### Алгоритм группировки A/B/C
Автоматическая группировка на основе последних 3 попыток:
- **Группа A**: > 85% правильных ответов
- **Группа B**: 65-85% правильных ответов
- **Группа C**: < 65% правильных ответов

### RAG система
Использует OpenAI embeddings (text-embedding-3-small) и pgvector для векторного поиска релевантных параграфов учебника. Генерирует персонализированные объяснения с учетом уровня мастерства студента.

## Статус реализации

См. [IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) для детального отслеживания прогресса разработки.

## Лицензия

Proprietary - все права защищены.

## Команда

AI Mentor Team

## Поддержка

По вопросам обращайтесь: [email]
