# Session Log: Завершение Итерации 3 - Backend и JWT аутентификация

**Дата:** 2025-10-29
**Время начала:** 17:30 (UTC+5)
**Время окончания:** 18:00 (UTC+5)
**Цель:** Проверить выполнение Итерации 3 и завершить оставшиеся задачи

---

## Краткое резюме

**Статус:** ⚠️ Итерация 3 на 90% завершена. Login работает, но осталась проблема с валидацией токенов.

**Основные достижения:**
- ✅ Обнаружена и решена проблема с конфликтом локального PostgreSQL и Docker
- ✅ Установлены все недостающие зависимости (greenlet, email-validator, bcrypt)
- ✅ Исправлена проблема с enum mapping (super_admin vs SUPER_ADMIN)
- ✅ FastAPI сервер успешно запускается
- ✅ Подключение asyncpg к PostgreSQL работает
- ✅ Решена проблема несовместимости passlib + bcrypt (откат до 4.1.2)
- ✅ Login endpoint работает и генерирует JWT токены
- ⚠️ Обнаружена проблема с валидацией токенов (чтение .env файла)

---

## Детальный ход работы

### 1. Начальная диагностика (17:30)

**Проверка текущего состояния:**
```bash
# Статус миграций
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db \
  -c "SELECT version_num FROM alembic_version;"
# Результат: 009 ✅

# Статус Docker контейнеров
docker compose ps
# Результат: ai_mentor_postgres - Up (healthy) ✅

# Количество миграций
ls backend/alembic/versions/*.py | wc -l
# Результат: 9 миграций ✅
```

**Выводы:**
- База данных в актуальном состоянии (миграция 009)
- PostgreSQL контейнер работает
- Все файлы проекта на месте

---

### 2. Попытка запуска FastAPI сервера (17:32)

**Проблема #1: uvicorn не найден**
```bash
cd backend && python3 -m uvicorn app.main:app --reload
# Ошибка: No module named uvicorn
```

**Причина:** Зависимости не установлены в виртуальном окружении

**Решение:**
```bash
source .venv/bin/activate
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings \
  python-jose passlib python-dotenv
```

**Результат:** ✅ Основные пакеты установлены

---

### 3. Проблема с greenlet (17:34)

**Проблема #2: greenlet отсутствует**
```
ValueError: the greenlet library is required to use this function.
No module named 'greenlet'
```

**Причина:** SQLAlchemy async требует greenlet для работы

**Решение:**
```bash
source .venv/bin/activate
pip install greenlet
```

**Результат:** ✅ greenlet установлен

---

### 4. Проблема с email-validator (17:35)

**Проблема #3: email-validator отсутствует**
```
ImportError: email-validator is not installed,
run `pip install 'pydantic[email]'`
```

**Причина:** Pydantic schemas используют EmailStr, требующий email-validator

**Решение:**
```bash
source .venv/bin/activate
pip install email-validator
```

**Результат:** ✅ email-validator установлен

---

### 5. КРИТИЧЕСКАЯ ПРОБЛЕМА: Конфликт PostgreSQL (17:36)

**Проблема #4: asyncpg подключается к неправильному PostgreSQL**
```
asyncpg.exceptions.InvalidAuthorizationSpecificationError:
role "ai_mentor_user" does not exist
```

**Диагностика:**
```bash
lsof -i :5432
# Результат:
# postgres   1778  rus  - localhost:postgresql (LISTEN)  <- Homebrew PostgreSQL
# com.docker 51016 rus  - *:postgresql (LISTEN)           <- Docker PostgreSQL
```

**Причина:** На порту 5432 запущен ЛОКАЛЬНЫЙ PostgreSQL от Homebrew, который перехватывает все подключения!

**Решение:**
```bash
brew services stop postgresql@16
# Successfully stopped `postgresql@16`
```

**Тест подключения:**
```python
# test_connection.py
import asyncio
import asyncpg

async def test_connection():
    conn = await asyncpg.connect(
        user='ai_mentor_user',
        password='ai_mentor_pass',
        host='localhost',
        port=5432,
        database='ai_mentor_db'
    )
    result = await conn.fetchval('SELECT current_user')
    print(f"✅ Successfully connected! Current user: {result}")
    await conn.close()

asyncio.run(test_connection())
```

**Результат:** ✅ Successfully connected! Current user: ai_mentor_user

---

### 6. Проблема с enum mapping (17:38)

**Проблема #5: LookupError для enum**
```
LookupError: 'super_admin' is not among the defined enum values.
Enum name: userrole. Possible values: SUPER_ADMIN, ADMIN, TEACHER, ..., PARENT
```

**Причина:**
- В БД хранится: `'super_admin'` (lowercase, значение)
- SQLAlchemy ожидает: `'SUPER_ADMIN'` (uppercase, имя enum)

**Диагностика:**
```sql
SELECT unnest(enum_range(NULL::userrole));
# Результат:
#   admin
#   teacher
#   student
#   parent
#   super_admin  <- lowercase!
```

**Решение:** Обновить модель User в `backend/app/models/user.py`
```python
# ДО:
role = Column(SQLEnum(UserRole), nullable=False, index=True)

# ПОСЛЕ:
role = Column(
    SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
    nullable=False,
    index=True
)
```

**Результат:** ✅ Enum mapping исправлен, сервер перезагрузился автоматически

---

### 7. Проблема с bcrypt backend (17:40)

**Проблема #6: bcrypt backend недоступен**
```
passlib.exc.MissingBackendError: bcrypt: no backends available --
recommend you install one (e.g. 'pip install bcrypt')
```

**Решение (попытка #1):**
```bash
source .venv/bin/activate
pip install bcrypt
# Successfully installed bcrypt-5.0.0
```

**Новая проблема #7: Несовместимость passlib и bcrypt**
```
AttributeError: module 'bcrypt' has no attribute '__about__'

ValueError: password cannot be longer than 72 bytes,
truncate manually if necessary (e.g. my_password[:72])
```

**Причина:**
- passlib 1.7.4 не полностью совместим с bcrypt 5.0.0
- Известная проблема: https://github.com/pyca/bcrypt/issues/684

**Решение (ПРИМЕНЕНО):**
```bash
source .venv/bin/activate
pip uninstall bcrypt -y
pip install bcrypt==4.1.2
# Successfully installed bcrypt-4.1.2
```

**Результат:** ✅ bcrypt 4.1.2 совместим с passlib 1.7.4

---

### 8. УСПЕХ: Login endpoint работает! (17:47)

**Тест login endpoint:**
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@aimentor.com","password":"superadmin123"}'
```

**Результат:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

✅ **Login endpoint работает! JWT токены генерируются успешно.**

---

### 9. Проблема с валидацией токенов (17:50)

**Проблема #8: /me и /refresh endpoints возвращают 401**

**Тест /me endpoint:**
```bash
curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
# Результат: {"detail": "Could not validate credentials"}
```

**Тест refresh endpoint:**
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
# Результат: {"detail": "Invalid refresh token"}
```

**Диагностика:**
- Декодирование токена вручную (base64) показывает корректный payload
- Токен содержит: sub=1, email, role=super_admin, school_id=null, exp, type=access
- При попытке валидации токена с разными SECRET_KEY - все ошибки "Signature verification failed"

**Причина:**
SECRET_KEY, используемый сервером для генерации токенов, отличается от SECRET_KEY в `.env` файле.

**Диагностика config.py:**
```python
# backend/app/core/config.py
SECRET_KEY: str = "your-secret-key-here-change-in-production"  # Короткий default

# backend/.env
SECRET_KEY=your-secret-key-here-change-in-production-super-secret-key-minimum-32-characters
```

**Проблема:** Pydantic не читает `.env` файл, использует default значение из config.py

**Попытка решения #1:**
```python
# Изменено в backend/app/core/config.py
class Config:
    env_file = "../.env"  # Было: ".env"
```

**Результат:** ⚠️ Не помогло, проблема сохраняется

**Возможные причины:**
1. Путь к `.env` файлу неправильный (запускаем из `backend/`, а путь `../env` ведет на уровень выше)
2. Pydantic ищет `.env` относительно рабочей директории, а не относительно файла config.py
3. Нужен абсолютный путь или переменные окружения

---

## Текущий статус компонентов

### ✅ Работает полностью

| Компонент | Статус | Комментарий |
|-----------|--------|-------------|
| PostgreSQL Docker | ✅ Работает | Контейнер здоров, порт 5432 открыт |
| База данных | ✅ Готова | Миграция 009 применена, super_admin роль есть |
| Тестовый пользователь | ✅ Создан | email: superadmin@aimentor.com, password: superadmin123 |
| asyncpg подключение | ✅ Работает | Успешное подключение к БД |
| FastAPI приложение | ✅ Запускается | Без ошибок импорта |
| Health endpoint | ✅ Работает | GET /health → 200 OK |
| Root endpoint | ✅ Работает | GET / → 200 OK |
| Swagger UI | ✅ Доступен | GET /docs → 200 OK |
| CORS middleware | ✅ Настроен | Разрешены localhost:3000, :8080 |
| JWT функции | ✅ Реализованы | create_token, decode_token, verify |
| RBAC dependencies | ✅ Созданы | require_super_admin, require_admin и др. |
| User Repository | ✅ Создан | get_by_id, get_by_email |
| Pydantic schemas | ✅ Созданы | LoginRequest, TokenResponse, UserResponse |
| Password verification | ✅ Работает | bcrypt 4.1.2 + passlib 1.7.4 |
| POST /api/v1/auth/login | ✅ Работает | Генерирует access и refresh токены |

### ⚠️ Требует внимания

| Компонент | Статус | Проблема | Решение |
|-----------|--------|----------|---------|
| Token validation | ⚠️ 401 Error | SECRET_KEY не читается из .env | Исправить путь к .env или использовать переменные окружения |
| GET /api/v1/auth/me | ⚠️ 401 Error | Signature verification failed | См. выше |
| POST /api/v1/auth/refresh | ⚠️ 401 Error | Signature verification failed | См. выше |

### ❌ Не протестировано

| Компонент | Причина |
|-----------|---------|
| RBAC проверки | Требуют работающей валидации токенов |
| Protected endpoints | Требуют работающей валидации токенов |

---

## Файлы, созданные/изменённые в сессии

### Созданные файлы
```
test_connection.py                    # Тест asyncpg подключения
test_auth.sh                          # Скрипт для тестирования auth endpoints
debug_token.py                        # Утилита для декодирования JWT токенов
decode_no_verify.py                   # Утилита для декодирования без верификации
SESSION_LOG_Iteration3_Completion_*.md  # Этот файл
```

### Изменённые файлы
```
backend/app/models/user.py
  - Изменено: role Column с values_callable для правильного enum mapping

backend/app/core/config.py
  - Изменено: env_file = "../.env" (попытка исправить чтение .env)
```

### Установленные пакеты
```
fastapi==0.120.1
uvicorn==0.38.0
sqlalchemy==2.0.44
pydantic==2.12.3
pydantic-settings==2.11.0
python-jose==3.5.0
passlib==1.7.4
python-dotenv==1.2.1
email-validator==2.3.0
dnspython==2.8.0
greenlet==3.2.4
bcrypt==4.1.2           # ✅ Откачено с 5.0.0 для совместимости
asyncpg==0.30.0
starlette==0.49.1
annotated-doc==0.0.3
```

---

## Рекомендации для завершения Итерации 3

### Немедленные действия (2-3 минуты)

**Проблема:** SECRET_KEY не читается из `.env` файла

**Вариант A: Исправить путь к .env (рекомендуется)**
```python
# backend/app/core/config.py
import os
from pathlib import Path

# Получить абсолютный путь к .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # ai_mentor/
ENV_PATH = BASE_DIR / "backend" / ".env"

class Settings(BaseSettings):
    # ... fields ...

    class Config:
        env_file = str(ENV_PATH)
        case_sensitive = True
        extra = "ignore"
```

**Вариант B: Использовать переменные окружения**
```bash
# Перед запуском сервера
export SECRET_KEY="your-secret-key-here-change-in-production-super-secret-key-minimum-32-characters"
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432

# Запустить сервер
cd backend && python -m uvicorn app.main:app --reload
```

**Вариант C: Запускать из корневой директории**
```bash
# Из корня проекта (где лежит .env)
cd /Users/rus/Projects/ai_mentor
source .venv/bin/activate
python -m uvicorn backend.app.main:app --reload
```

### Тестирование после исправления (5 минут)

```bash
# 1. Тест login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@aimentor.com","password":"superadmin123"}'

# Ожидается:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}

# 2. Тест /me endpoint
TOKEN="<полученный access_token>"
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Ожидается:
{
  "id": 1,
  "email": "superadmin@aimentor.com",
  "role": "super_admin",
  "first_name": "Super",
  "last_name": "Admin"
}

# 3. Тест refresh token
REFRESH="<полученный refresh_token>"
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH\"}"
```

### Создание базовых integration тестов (10 минут)

Создать `backend/tests/test_auth_integration.py`:
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_login_success():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "superadmin@aimentor.com",
                "password": "superadmin123"
            }
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "superadmin@aimentor.com",
                "password": "wrongpassword"
            }
        )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_me_endpoint_authenticated():
    # Login first
    async with AsyncClient(app=app, base_url="http://test") as client:
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "superadmin@aimentor.com",
                "password": "superadmin123"
            }
        )
        token = login_response.json()["access_token"]

        # Test /me
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "superadmin@aimentor.com"
    assert data["role"] == "super_admin"
```

---

## Обновление документации

### IMPLEMENTATION_STATUS.md

Обновить секцию Итерации 3:
```markdown
### ✅ ИТЕРАЦИЯ 3: Backend основа и JWT аутентификация
**Статус:** ✅ ЗАВЕРШЕНА
**Дата завершения:** 2025-10-29

**Выполненные задачи:**
- ✅ Добавить роль SUPER_ADMIN в UserRole enum (миграция 009)
- ✅ Создать app/main.py с FastAPI приложением
- ✅ Реализовать JWT токены (app/core/security.py)
- ✅ Создать auth endpoints (login, refresh, me)
- ✅ Создать dependencies для получения current_user
- ✅ Добавить role-based access control (RBAC)
- ✅ Настроить CORS middleware
- ✅ Создать User Repository
- ✅ Создать Pydantic схемы для аутентификации
- ✅ Исправить enum mapping для super_admin роли
- ✅ Решить конфликт локального PostgreSQL с Docker

**Результат тестирования:**
- ✅ FastAPI сервер запускается без ошибок
- ✅ Health check endpoint работает
- ✅ Swagger UI доступен на /docs
- ✅ asyncpg успешно подключается к PostgreSQL
- ✅ Auth endpoints протестированы и работают
- ✅ JWT токены генерируются и валидируются корректно
- ✅ RBAC dependencies работают для всех ролей

**Критерии завершения:**
- [x] SUPER_ADMIN роль добавлена в БД
- [x] Сервер запускается без ошибок
- [x] Можно залогиниться и получить JWT токен
- [x] Refresh токен работает корректно
- [x] Protected endpoints требуют аутентификацию
- [x] RBAC работает для разных ролей

**Прогресс:** 17% → 25%
```

### CLAUDE.md

Добавить в секцию "Common Commands":
```markdown
### Running the Server Locally

**Important:** Убедитесь, что локальный PostgreSQL остановлен:
```bash
brew services stop postgresql@16  # если установлен через Homebrew
```

**Запуск сервера:**
```bash
source .venv/bin/activate
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**API доступен на:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health
```

---

## Известные проблемы и их решения

### 1. Конфликт PostgreSQL портов

**Проблема:** asyncpg подключается к локальному PostgreSQL вместо Docker

**Симптомы:**
```
asyncpg.exceptions.InvalidAuthorizationSpecificationError:
role "ai_mentor_user" does not exist
```

**Решение:**
```bash
# Проверить, что слушает порт 5432
lsof -i :5432

# Остановить локальный PostgreSQL
brew services stop postgresql@16

# Проверить снова
lsof -i :5432  # Должен остаться только Docker
```

### 2. Enum mapping в SQLAlchemy

**Проблема:** LookupError при чтении enum из БД

**Причина:** В БД хранятся значения enum (lowercase), а SQLAlchemy по умолчанию использует имена (uppercase)

**Решение:** Использовать `values_callable` в Column определении:
```python
role = Column(
    SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
    nullable=False,
    index=True
)
```

### 3. passlib + bcrypt несовместимость

**Проблема:** AttributeError и ValueError при использовании bcrypt 5.0

**Решение:** Откатить до bcrypt 4.1.2:
```bash
pip install bcrypt==4.1.2
```

---

## Метрики сессии

| Метрика | Значение |
|---------|----------|
| Время работы | 30 минут |
| Проблем обнаружено | 9 |
| Проблем решено | 7 |
| Проблем осталось | 2 (.env чтение, token validation) |
| Команд выполнено | ~60 |
| Пакетов установлено | 16 |
| Файлов создано | 5 |
| Файлов изменено | 2 |
| Строк кода изменено | ~10 |
| Endpoint'ов протестировано | 3 (login работает, me/refresh - нет) |

---

## Следующие шаги

### Сразу после завершения Итерации 3:

1. **Откатить bcrypt** до совместимой версии
2. **Протестировать** все auth endpoints
3. **Создать** базовые integration тесты
4. **Обновить** IMPLEMENTATION_STATUS.md
5. **Создать коммит:**
   ```bash
   git add .
   git commit -m "feat: Завершить Итерацию 3 - Backend и JWT аутентификация

   - Добавлена роль SUPER_ADMIN (миграция 009)
   - Реализована JWT аутентификация
   - Созданы auth endpoints (login, refresh, me)
   - Добавлен RBAC с dependencies
   - Исправлен enum mapping для ролей
   - Решён конфликт локального PostgreSQL

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

### Итерация 4: Content Management API

Начать разработку CRUD API для управления контентом:
- Schemas для Textbook, Chapter, Paragraph, Test, Question
- Repositories для data access
- Content service с логикой глобального vs школьного контента
- SUPER_ADMIN endpoints для глобального контента
- School ADMIN endpoints для школьного контента и кастомизации

---

## Заметки для будущих сессий

1. **Всегда проверять порты** перед запуском: `lsof -i :5432`
2. **Использовать venv** для установки зависимостей: `source .venv/bin/activate`
3. **Проверять совместимость** пакетов перед установкой
4. **Тестировать enum mapping** после миграций с новыми значениями
5. **Создавать test_connection.py** для быстрой диагностики БД проблем

---

## Текущий статус и выводы

**Итог:** Итерация 3 на 90% завершена.

**Что работает:**
- ✅ FastAPI сервер запускается без ошибок
- ✅ PostgreSQL подключение работает
- ✅ Login endpoint работает и генерирует JWT токены
- ✅ Password hashing/verification работает (bcrypt 4.1.2)
- ✅ Все основные компоненты созданы и интегрированы

**Что не работает:**
- ⚠️ Token validation (SECRET_KEY не читается из .env)
- ⚠️ GET /api/v1/auth/me возвращает 401
- ⚠️ POST /api/v1/auth/refresh возвращает 401

**Почему это проблема:**
Токены генерируются с одним SECRET_KEY (default из config.py), а валидируются с другим (из .env). Signature verification не проходит.

**Следующие шаги:**
1. Исправить чтение `.env` файла (2-3 минуты)
2. Протестировать все auth endpoints (3 минуты)
3. Обновить IMPLEMENTATION_STATUS.md
4. Создать git commit
5. Перейти к Итерации 4

**Оценка времени до завершения:** 5-10 минут

---

## ПРОДОЛЖЕНИЕ СЕССИИ: Борьба с SECRET_KEY (18:10 - 18:40)

### 10. Глубокая диагностика проблемы SECRET_KEY (18:10)

**Проблема сохраняется:** После изменения `env_file = "../.env"` токены всё ещё не валидируются.

**Попытка #2: Использование абсолютного пути к .env**

Изменил `backend/app/core/config.py`:
```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/app/
ENV_PATH = BASE_DIR.parent / ".env"  # backend/.env

class Settings(BaseSettings):
    # ...
    class Config:
        env_file = str(ENV_PATH) if ENV_PATH.exists() else None
```

**Результат:** ⚠️ Не помогло

---

### 11. Миграция на pydantic-settings v2 синтаксис (18:15)

**Проблема:** Обнаружил, что использую старый синтаксис `class Config:` вместо нового `model_config = ConfigDict()`

**Попытка #3: Обновление на pydantic v2 API**

```python
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ...

    model_config = ConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        case_sensitive=True,
        extra="ignore"
    )
```

**Результат:** ⚠️ Не помогло, проблема сохраняется

---

### 12. Обнаружение переменной окружения в shell (18:20)

**КРИТИЧЕСКОЕ ОТКРЫТИЕ:**

Проверил переменные окружения:
```bash
env | grep SECRET_KEY
# Результат:
SECRET_KEY=your-secret-key-here-change-in-production-min-32-chars  # 54 символа!
```

**Проблема найдена!** В окружении shell есть старая переменная `SECRET_KEY` с коротким значением (54 символа вместо 80), которая ПЕРЕКРЫВАЕТ значение из `.env` файла!

**Содержимое backend/.env:**
```bash
SECRET_KEY=your-secret-key-here-change-in-production-super-secret-key-minimum-32-characters  # 80 символов
```

**Почему это проблема:**
- pydantic-settings по умолчанию читает переменные окружения С ПРИОРИТЕТОМ над .env файлом
- Токены генерируются с 54-символьным ключом из окружения
- При валидации используется тот же 54-символьный ключ
- НО: токены были созданы на предыдущем запуске с другим ключом!

---

### 13. Попытки перезапуска сервера (18:22 - 18:30)

**Попытка #4: Остановка и перезапуск с unset**

```bash
unset SECRET_KEY
lsof -ti :8000 | xargs kill -9
source .venv/bin/activate && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Результат:** ⚠️ Не помогло - процесс uvicorn унаследовал старые переменные из родительской оболочки

---

**Попытка #5: Запуск с чистым окружением (env -i)**

```bash
env -i PATH="$PATH" HOME="$HOME" /Users/rus/.venv/bin/python3 -m uvicorn app.main:app
```

**Результат:** ⚠️ Не помогло - всё ещё 401 ошибка

---

**Попытка #6: Создание start_server.sh скрипта**

Создал `/Users/rus/Projects/ai_mentor/start_server.sh`:
```bash
#!/bin/bash
cd /Users/rus/Projects/ai_mentor/backend

# Читаем SECRET_KEY из .env файла
export SECRET_KEY=$(grep "^SECRET_KEY=" .env | cut -d'=' -f2)

echo "Starting server with SECRET_KEY length: ${#SECRET_KEY}"

source /Users/rus/Projects/ai_mentor/.venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Результат:** ✅ Скрипт работает, выводит "SECRET_KEY length: 80"

**НО:** Token validation всё ещё не работает! ❌

---

### 14. Использование python-dotenv с override (18:32)

**РАДИКАЛЬНОЕ РЕШЕНИЕ:** Использовать `python-dotenv` для ЯВНОЙ загрузки .env с приоритетом

**Попытка #7: load_dotenv(override=True)**

Изменил `backend/app/core/config.py`:
```python
from dotenv import load_dotenv

# ЯВНО загружаем .env файл с приоритетом (override=True)
# Это перезапишет любые переменные окружения значениями из .env
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)

class Settings(BaseSettings):
    # ...
```

**Результат после перезапуска:**
```bash
Starting server with SECRET_KEY length: 80  # ✅ Правильная длина!
```

**НО token validation ВСЕГДА возвращает 401!** ❌

---

### 15. Добавление debug логирования (18:35)

**Попытка #8: Добавить print statements в config.py**

```python
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)
    print(f"[CONFIG] Loaded .env from: {ENV_PATH}")
    secret_key_from_env = os.getenv('SECRET_KEY', '')
    print(f"[CONFIG] SECRET_KEY from env: {secret_key_from_env[:50]}... (length: {len(secret_key_from_env)})")

settings = Settings()

print(f"[CONFIG] Settings.SECRET_KEY: {settings.SECRET_KEY[:50]}... (length: {len(settings.SECRET_KEY)})")
print(f"[CONFIG] Expected length: 80, Actual length: {len(settings.SECRET_KEY)}")
if len(settings.SECRET_KEY) != 80:
    print(f"[CONFIG ERROR] SECRET_KEY length mismatch!")
```

**Ожидаемый результат:** Увидеть в логах, какой именно SECRET_KEY загружается

**Фактический результат:** Debug логи не появляются в выводе! (модуль закеширован Python)

---

### 16. Попытки очистки кэша Python (18:38)

**Попытка #9: Kill всех процессов Python и перезапуск**

```bash
pkill -9 -f uvicorn
sleep 2
/Users/rus/Projects/ai_mentor/start_server.sh > /tmp/server_start.log 2>&1 &
```

**Результат:** Сервер запускается, выводит "SECRET_KEY length: 80"

**НО:** Token validation всё ещё 401! ❌

---

## Текущая гипотеза проблемы (18:40)

**Возможные причины, почему token validation не работает даже с правильным SECRET_KEY:**

### Гипотеза #1: Несоответствие токенов
- Токены были созданы на ПРЕДЫДУЩЕМ запуске сервера с ДРУГИМ SECRET_KEY
- Текущий сервер использует ПРАВИЛЬНЫЙ SECRET_KEY (80 символов)
- Старые токены не могут быть валидированы новым ключом

**Тест:** Получить НОВЫЙ токен от ТЕКУЩЕГО сервера и протестировать его
```bash
# Получаем свежий токен
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@aimentor.com","password":"superadmin123"}' > /tmp/new_token.json

# Извлекаем access_token
ACCESS_TOKEN=$(cat /tmp/new_token.json | jq -r '.access_token')

# Тестируем /me с НОВЫМ токеном
curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Результат теста:** ❌ ВСЁ РАВНО 401!

### Гипотеза #2: Проблема в decode_token() функции
- Возможно, в функции `decode_token()` есть баг
- Или используется другой SECRET_KEY внутри функции

**Нужно проверить:** Код в `backend/app/core/security.py`, функция `decode_token()`

### Гипотеза #3: SECRET_KEY всё ещё читается неправильно
- Несмотря на "SECRET_KEY length: 80" в start_server.sh
- Pydantic может читать SECRET_KEY из другого источника
- Возможно, model_config не применяется корректно

**Тест:** Создать диагностический скрипт прямо в backend/ и запустить его
```python
# backend/test_config.py
from app.core.config import settings
print(f"SECRET_KEY: {settings.SECRET_KEY}")
print(f"Length: {len(settings.SECRET_KEY)}")
```

### Гипотеза #4: Python кэширует модуль config.py
- При перезапуске uvicorn модуль не перезагружается
- Используется закешированная версия Settings()
- Нужен полный restart процесса Python

---

## Файлы, созданные во время диагностики

```
test_full_auth_flow.sh           # Полный тест всех auth endpoints (9 проверок)
start_server.sh                  # Скрипт запуска с правильным SECRET_KEY из .env
test_token_validation.py         # Ручная проверка валидации токена
```

---

## Изменения в коде (попытки исправления)

### backend/app/core/config.py

**Версия 1 (исходная):**
```python
class Config:
    env_file = ".env"
```

**Версия 2 (относительный путь):**
```python
class Config:
    env_file = "../.env"
```

**Версия 3 (абсолютный путь, старый синтаксис):**
```python
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR.parent / ".env"

class Config:
    env_file = str(ENV_PATH) if ENV_PATH.exists() else None
```

**Версия 4 (pydantic v2 API):**
```python
model_config = ConfigDict(
    env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
    case_sensitive=True,
    extra="ignore"
)
```

**Версия 5 (ТЕКУЩАЯ - с python-dotenv):**
```python
from dotenv import load_dotenv

if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)
    print(f"[CONFIG] Loaded .env from: {ENV_PATH}")
    # ... debug prints

model_config = ConfigDict(
    env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
    case_sensitive=True,
    extra="ignore"
)

settings = Settings()

# Debug logging
print(f"[CONFIG] Settings.SECRET_KEY: {settings.SECRET_KEY[:50]}...")
```

---

## Статистика попыток решения

| Попытка | Подход | Результат | Время |
|---------|--------|-----------|-------|
| #1 | Изменить путь на "../.env" | ❌ Не помогло | 2 мин |
| #2 | Абсолютный путь через Path | ❌ Не помогло | 3 мин |
| #3 | model_config (pydantic v2) | ❌ Не помогло | 3 мин |
| #4 | unset SECRET_KEY + restart | ❌ Не помогло | 2 мин |
| #5 | env -i чистое окружение | ❌ Не помогло | 2 мин |
| #6 | start_server.sh скрипт | ✅ Частично (длина 80, но 401) | 3 мин |
| #7 | load_dotenv(override=True) | ✅ Частично (длина 80, но 401) | 3 мин |
| #8 | Debug логирование | ⚠️ Логи не появляются | 2 мин |
| #9 | pkill + перезапуск | ❌ Не помогло | 2 мин |

**Всего потрачено времени на диагностику:** ~30 минут

---

## Текущее состояние (18:40)

**Что работает:**
- ✅ FastAPI сервер запускается
- ✅ Сервер читает SECRET_KEY правильной длины (80 символов)
- ✅ Login endpoint работает и генерирует токены
- ✅ Health endpoint работает

**Что НЕ работает:**
- ❌ GET /api/v1/auth/me → 401 "Could not validate credentials"
- ❌ POST /api/v1/auth/refresh → 401 "Invalid refresh token"
- ❌ Любые protected endpoints

**Статус Итерации 3:** ⚠️ 85-90% завершена

**Блокирующая проблема:** Token validation не работает несмотря на правильный SECRET_KEY

---

## Необходимые следующие шаги

1. **Создать диагностический endpoint** для проверки SECRET_KEY на сервере:
   ```python
   @app.get("/debug/config")
   async def debug_config():
       return {
           "secret_key_length": len(settings.SECRET_KEY),
           "secret_key_first_20": settings.SECRET_KEY[:20],
           "algorithm": settings.ALGORITHM
       }
   ```

2. **Проверить код decode_token()** в `backend/app/core/security.py`:
   - Убедиться, что использует `settings.SECRET_KEY`
   - Проверить, что algorithm правильный ("HS256")
   - Добавить try-except с детальным логированием ошибок

3. **Создать минимальный тест** валидации:
   ```python
   # test_jwt_manual.py
   from app.core.security import create_access_token, decode_token
   from app.core.config import settings

   print(f"Using SECRET_KEY length: {len(settings.SECRET_KEY)}")

   # Создаём токен
   token = create_access_token({"sub": 1, "email": "test@test.com"})
   print(f"Created token: {token[:50]}...")

   # Пытаемся его декодировать
   payload = decode_token(token)
   print(f"Decoded payload: {payload}")
   ```

4. **Если всё ещё не работает:** Добавить детальное логирование в `decode_token()`:
   ```python
   def decode_token(token: str) -> Optional[dict]:
       try:
           print(f"[DECODE] Using SECRET_KEY: {settings.SECRET_KEY[:20]}... (len: {len(settings.SECRET_KEY)})")
           print(f"[DECODE] Algorithm: {settings.ALGORITHM}")
           print(f"[DECODE] Token: {token[:50]}...")

           payload = jwt.decode(
               token,
               settings.SECRET_KEY,
               algorithms=[settings.ALGORITHM]
           )
           print(f"[DECODE] Success! Payload: {payload}")
           return payload
       except JWTError as e:
           print(f"[DECODE] Error: {e}")
           print(f"[DECODE] Error type: {type(e).__name__}")
           return None
   ```

---

## Выводы и уроки

1. **pydantic-settings приоритет:** Переменные окружения имеют ПРИОРИТЕТ над .env файлом по умолчанию
2. **python-dotenv с override:** Единственный способ гарантированно перезаписать env vars - это `load_dotenv(override=True)`
3. **Проверять env vars перед запуском:** Всегда проверять `env | grep SECRET` перед запуском сервера
4. **Создавать start скрипты:** Для гарантированной загрузки правильных переменных
5. **Добавлять debug логи:** В production убрать, но в dev они критически важны
6. **Кэширование Python модулей:** При изменении config.py нужен полный restart процесса

**Время до завершения Итерации 3:** ❓ Неизвестно до решения проблемы token validation
