# AI Mentor API - Полная документация

**Полная документация REST API платформы AI Mentor.**

**Версия API:** v1
**Base URL:** `https://api.ai-mentor.kz/api/v1`
**Swagger Docs:** `https://api.ai-mentor.kz/docs`

---

## Содержание

1. [Обзор архитектуры](#обзор-архитектуры)
2. [Авторизация](#1-авторизация-authentication)
3. [Управление школами (SUPER_ADMIN)](#2-управление-школами-super_admin)
4. [Глобальный контент (SUPER_ADMIN)](#3-глобальный-контент-super_admin)
5. [Школьный контент (ADMIN)](#4-школьный-контент-admin)
6. [Управление пользователями школы (ADMIN)](#5-управление-пользователями-школы-admin)
7. [Студенты - Тесты и прогресс](#6-студенты---тесты-и-прогресс)
8. [ГОСО - Стандарты образования](#7-госо---стандарты-образования)
9. [Загрузка файлов](#8-загрузка-файлов)
10. [Примеры использования](#9-примеры-использования)

---

## Обзор архитектуры

### Двухуровневая система администрирования

| Уровень | Роль | Prefix | Описание |
|---------|------|--------|----------|
| **Глобальный** | SUPER_ADMIN | `/admin/global/*` | Глобальный контент (school_id = NULL), управление школами |
| **Школьный** | ADMIN | `/admin/school/*` | Школьный контент, управление пользователями школы |

### Роли и права доступа

| Роль | Описание | Доступ |
|------|----------|--------|
| **SUPER_ADMIN** | Суперадмин платформы | Глобальный контент, школы |
| **ADMIN** | Администратор школы | Школьный контент, пользователи |
| **TEACHER** | Учитель | Просмотр классов, создание заданий |
| **STUDENT** | Ученик | Тесты, прогресс |
| **PARENT** | Родитель | Просмотр прогресса детей |

---

## 1. Авторизация (Authentication)

**Prefix:** `/api/v1/auth`

### Endpoints

| Method | Endpoint | Описание | Роль |
|--------|----------|----------|------|
| POST | `/login` | Авторизация | Публичный |
| POST | `/refresh` | Обновить токен | Авторизованный |
| GET | `/me` | Текущий пользователь | Авторизованный |

### POST /auth/login

Авторизация пользователя. Возвращает access и refresh токены.

**Request:**
```json
{
  "email": "superadmin@aimentor.com",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### POST /auth/refresh

Обновление токена доступа.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### GET /auth/me

Получить информацию о текущем пользователе.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "email": "superadmin@aimentor.com",
  "first_name": "Super",
  "last_name": "Admin",
  "role": "super_admin",
  "school_id": null,
  "is_active": true
}
```

---

## 2. Управление школами (SUPER_ADMIN)

**Prefix:** `/api/v1/admin`
**Требуется:** роль SUPER_ADMIN

### Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/schools` | Список всех школ |
| POST | `/schools` | Создать школу |
| GET | `/schools/{id}` | Получить школу |
| PUT | `/schools/{id}` | Обновить школу |
| DELETE | `/schools/{id}` | Удалить школу (soft delete) |
| PATCH | `/schools/{id}/block` | Заблокировать школу |
| PATCH | `/schools/{id}/unblock` | Разблокировать школу |

### POST /admin/schools

**Request:**
```json
{
  "name": "Школа №45 г. Алматы",
  "code": "school45-almaty",
  "address": "ул. Абая, 123",
  "phone": "+7 727 123 45 67",
  "email": "school45@edu.kz"
}
```

**Response:**
```json
{
  "id": 15,
  "name": "Школа №45 г. Алматы",
  "code": "school45-almaty",
  "address": "ул. Абая, 123",
  "phone": "+7 727 123 45 67",
  "email": "school45@edu.kz",
  "is_active": true,
  "created_at": "2025-12-16T10:00:00Z"
}
```

---

## 3. Глобальный контент (SUPER_ADMIN)

**Prefix:** `/api/v1/admin/global`
**Требуется:** роль SUPER_ADMIN
**Контент:** school_id = NULL (доступен всем школам)

### 3.1 Учебники (Textbooks)

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/textbooks` | Список глобальных учебников |
| POST | `/textbooks` | Создать учебник |
| GET | `/textbooks/{id}` | Получить учебник |
| PUT | `/textbooks/{id}` | Обновить учебник |
| DELETE | `/textbooks/{id}` | Удалить учебник |

**POST /admin/global/textbooks:**
```json
{
  "title": "Алгебра 7 класс",
  "subject": "Математика",
  "grade_level": 7,
  "author": "А. Абылкасымова",
  "publisher": "Мектеп",
  "year": 2024,
  "isbn": "978-601-293-456-7",
  "description": "Учебник алгебры для 7 класса",
  "is_active": true
}
```

### 3.2 Главы (Chapters)

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/chapters` | Создать главу |
| GET | `/textbooks/{id}/chapters` | Главы учебника |
| GET | `/chapters/{id}` | Получить главу |
| PUT | `/chapters/{id}` | Обновить главу |
| DELETE | `/chapters/{id}` | Удалить главу |

**POST /admin/global/chapters:**
```json
{
  "textbook_id": 15,
  "title": "Линейные уравнения",
  "number": 1,
  "order": 1,
  "description": "Введение в линейные уравнения",
  "learning_objective": "Изучить методы решения линейных уравнений"
}
```

### 3.3 Параграфы (Paragraphs)

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/paragraphs` | Создать параграф |
| GET | `/chapters/{id}/paragraphs` | Параграфы главы |
| GET | `/paragraphs/{id}` | Получить параграф |
| PUT | `/paragraphs/{id}` | Обновить параграф |
| DELETE | `/paragraphs/{id}` | Удалить параграф |

**POST /admin/global/paragraphs:**
```json
{
  "chapter_id": 42,
  "title": "Решение уравнений методом переноса",
  "number": 1,
  "order": 1,
  "content": "<h2>Метод переноса</h2><p>При решении уравнений...</p>",
  "summary": "Основы метода переноса слагаемых",
  "learning_objective": "Освоить метод переноса",
  "lesson_objective": "Решить 10 уравнений",
  "key_terms": ["уравнение", "переменная", "перенос"],
  "questions": [
    {"order": 1, "text": "Что происходит со знаком при переносе?"},
    {"order": 2, "text": "Решите уравнение: x + 5 = 12"}
  ]
}
```

### 3.4 Тесты (Tests)

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/tests` | Список тестов (опционально ?chapter_id=X) |
| POST | `/tests` | Создать тест |
| GET | `/tests/{id}` | Получить тест |
| PUT | `/tests/{id}` | Обновить тест |
| DELETE | `/tests/{id}` | Удалить тест |

**POST /admin/global/tests:**
```json
{
  "title": "Контрольная по линейным уравнениям",
  "description": "Проверка знаний по теме",
  "chapter_id": 42,
  "paragraph_id": null,
  "difficulty": "medium",
  "time_limit": 45,
  "passing_score": 70,
  "is_active": true
}
```

### 3.5 Вопросы (Questions)

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/tests/{id}/questions` | Создать вопрос с вариантами |
| GET | `/tests/{id}/questions` | Вопросы теста |
| GET | `/questions/{id}` | Получить вопрос |
| PUT | `/questions/{id}` | Обновить вопрос |
| DELETE | `/questions/{id}` | Удалить вопрос |

**POST /admin/global/tests/{id}/questions:**
```json
{
  "sort_order": 1,
  "question_type": "single_choice",
  "question_text": "Решите уравнение: 2x + 4 = 10",
  "explanation": "Перенесем 4 в правую часть: 2x = 6, x = 3",
  "points": 1,
  "options": [
    {"sort_order": 1, "option_text": "x = 2", "is_correct": false},
    {"sort_order": 2, "option_text": "x = 3", "is_correct": true},
    {"sort_order": 3, "option_text": "x = 4", "is_correct": false},
    {"sort_order": 4, "option_text": "x = 5", "is_correct": false}
  ]
}
```

### 3.6 Варианты ответов (Options)

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/questions/{id}/options` | Добавить вариант |
| PUT | `/options/{id}` | Обновить вариант |
| DELETE | `/options/{id}` | Удалить вариант |

### 3.7 Связи параграф-ГОСО (Paragraph Outcomes)

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/paragraph-outcomes` | Создать связь |
| GET | `/paragraphs/{id}/outcomes` | Связи параграфа |
| PUT | `/paragraph-outcomes/{id}` | Обновить связь |
| DELETE | `/paragraph-outcomes/{id}` | Удалить связь |

---

## 4. Школьный контент (ADMIN)

**Prefix:** `/api/v1/admin/school`
**Требуется:** роль ADMIN
**Контент:** привязан к school_id текущего пользователя

### 4.1 Учебники

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/textbooks` | Список (школьные + глобальные) |
| POST | `/textbooks` | Создать школьный учебник |
| POST | `/textbooks/{global_id}/customize` | Форк глобального учебника |
| GET | `/textbooks/{id}` | Получить учебник |
| PUT | `/textbooks/{id}` | Обновить (только школьные) |
| DELETE | `/textbooks/{id}` | Удалить (только школьные) |

**Кастомизация (fork) глобального учебника:**
```bash
POST /api/v1/admin/school/textbooks/15/customize
```

Создает полную копию глобального учебника со всеми главами и параграфами:
```json
{
  "id": 45,
  "school_id": 7,
  "global_textbook_id": 15,
  "is_customized": true,
  "title": "Алгебра 7 класс",
  ...
}
```

### 4.2 Главы

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/chapters` | Создать главу (только в школьных учебниках) |
| GET | `/textbooks/{id}/chapters` | Главы учебника |
| GET | `/chapters/{id}` | Получить главу |
| PUT | `/chapters/{id}` | Обновить (только школьные) |
| DELETE | `/chapters/{id}` | Удалить (только школьные) |

### 4.3 Параграфы

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/paragraphs` | Создать параграф |
| GET | `/chapters/{id}/paragraphs` | Параграфы главы |
| GET | `/paragraphs/{id}` | Получить параграф |
| PUT | `/paragraphs/{id}` | Обновить |
| DELETE | `/paragraphs/{id}` | Удалить |

### 4.4 Тесты

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/tests` | Список (школьные + глобальные) |
| POST | `/tests` | Создать школьный тест |
| GET | `/tests/{id}` | Получить тест |
| PUT | `/tests/{id}` | Обновить (только школьные) |
| DELETE | `/tests/{id}` | Удалить (только школьные) |

### 4.5 Вопросы и варианты

Аналогично глобальным, но только для школьных тестов.

### 4.6 Связи параграф-ГОСО

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/paragraph-outcomes` | Создать связь (для школьных параграфов) |
| GET | `/paragraphs/{id}/outcomes` | Связи параграфа |
| PUT | `/paragraph-outcomes/{id}` | Обновить |
| DELETE | `/paragraph-outcomes/{id}` | Удалить |

### 4.7 Настройки школы

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/settings` | Получить настройки школы |
| PUT | `/settings` | Обновить настройки школы |

---

## 5. Управление пользователями школы (ADMIN)

**Prefix:** `/api/v1/admin/school`
**Требуется:** роль ADMIN

### 5.1 Пользователи (Users)

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/users` | Список пользователей (?role=X, ?is_active=X) |
| GET | `/users/{id}` | Получить пользователя |
| PUT | `/users/{id}` | Обновить (имя, телефон) |
| POST | `/users/{id}/deactivate` | Деактивировать |
| POST | `/users/{id}/activate` | Активировать |
| DELETE | `/users/{id}` | Удалить (soft delete) |

### 5.2 Ученики (Students)

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/students` | Список (?grade_level=X, ?class_id=X) |
| POST | `/students` | Создать (User + Student) |
| GET | `/students/{id}` | Получить ученика |
| PUT | `/students/{id}` | Обновить |
| DELETE | `/students/{id}` | Удалить |

**POST /admin/school/students:**
```json
{
  "email": "student@school.com",
  "password": "student123",
  "first_name": "Алихан",
  "last_name": "Султанов",
  "middle_name": "Маратович",
  "phone": "+7 777 123 45 67",
  "grade_level": 7,
  "birth_date": "2010-05-15",
  "student_code": "STU00001"
}
```

### 5.3 Учителя (Teachers)

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/teachers` | Список (?subject=X, ?class_id=X) |
| POST | `/teachers` | Создать (User + Teacher) |
| GET | `/teachers/{id}` | Получить учителя |
| PUT | `/teachers/{id}` | Обновить |
| DELETE | `/teachers/{id}` | Удалить |

**POST /admin/school/teachers:**
```json
{
  "email": "teacher@school.com",
  "password": "teacher123",
  "first_name": "Айгерим",
  "last_name": "Нурсултанова",
  "subject": "Математика",
  "bio": "Опыт работы 10 лет",
  "teacher_code": "TCHR0001"
}
```

### 5.4 Родители (Parents)

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/parents` | Список родителей |
| POST | `/parents` | Создать (с опциональными детьми) |
| GET | `/parents/{id}` | Получить родителя |
| DELETE | `/parents/{id}` | Удалить |
| GET | `/parents/{id}/children` | Дети родителя |
| POST | `/parents/{id}/children` | Добавить детей |
| DELETE | `/parents/{id}/children/{student_id}` | Удалить ребенка |

**POST /admin/school/parents:**
```json
{
  "email": "parent@mail.com",
  "password": "parent123",
  "first_name": "Марат",
  "last_name": "Султанов",
  "phone": "+7 777 987 65 43",
  "student_ids": [1, 2]
}
```

### 5.5 Классы (Classes)

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/classes` | Список (?grade_level=X, ?academic_year=X) |
| POST | `/classes` | Создать класс |
| GET | `/classes/{id}` | Получить класс |
| PUT | `/classes/{id}` | Обновить |
| DELETE | `/classes/{id}` | Удалить |
| POST | `/classes/{id}/students` | Добавить учеников |
| DELETE | `/classes/{id}/students/{student_id}` | Удалить ученика |
| POST | `/classes/{id}/teachers` | Добавить учителей |
| DELETE | `/classes/{id}/teachers/{teacher_id}` | Удалить учителя |

**POST /admin/school/classes:**
```json
{
  "name": "7-А класс",
  "code": "7A",
  "grade_level": 7,
  "academic_year": "2024-2025"
}
```

---

## 6. Студенты - Тесты и прогресс

**Prefix:** `/api/v1/students`
**Требуется:** роль STUDENT

### Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/tests` | Доступные тесты |
| POST | `/tests/{id}/start` | Начать тест |
| GET | `/attempts/{id}` | Получить попытку |
| POST | `/attempts/{id}/submit` | Отправить ответы |
| GET | `/progress` | Прогресс обучения |
| GET | `/mastery/chapter/{id}` | Мастерство по главе (A/B/C) |
| GET | `/mastery/overview` | Обзор мастерства |

### GET /students/tests

Получить доступные тесты (глобальные + школьные).

**Query параметры:**
- `chapter_id` - фильтр по главе
- `paragraph_id` - фильтр по параграфу
- `test_purpose` - тип теста (formative/summative)
- `difficulty` - сложность (easy/medium/hard)

**Response:**
```json
[
  {
    "id": 5,
    "title": "Контрольная по линейным уравнениям",
    "description": "...",
    "difficulty": "medium",
    "time_limit": 45,
    "passing_score": 70,
    "question_count": 10,
    "attempts_count": 2,
    "best_score": 85.0,
    "chapter_id": 42,
    "school_id": null
  }
]
```

### POST /students/tests/{id}/start

Начать новую попытку теста.

**Response:** Тест с вопросами БЕЗ правильных ответов.

### POST /students/attempts/{id}/submit

Отправить ответы на тест.

**Request:**
```json
{
  "answers": [
    {"question_id": 1, "selected_option_ids": [2]},
    {"question_id": 2, "selected_option_ids": [5]},
    {"question_id": 3, "answer_text": "x = 5"}
  ]
}
```

**Response:** Результат с оценкой и правильными ответами.

### GET /students/mastery/overview

Обзор мастерства по всем главам.

**Response:**
```json
{
  "student_id": 15,
  "chapters": [
    {
      "chapter_id": 42,
      "chapter_title": "Линейные уравнения",
      "mastery_level": "A",
      "mastery_score": 87.5,
      "total_paragraphs": 5,
      "completed_paragraphs": 4
    }
  ],
  "total_chapters": 5,
  "average_mastery_score": 78.3,
  "level_a_count": 2,
  "level_b_count": 2,
  "level_c_count": 1
}
```

---

## 7. ГОСО - Стандарты образования

**Prefix:** `/api/v1/goso`
**Требуется:** Любая авторизованная роль

### Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/subjects` | Список предметов |
| GET | `/subjects/{id}` | Предмет |
| GET | `/frameworks` | Фреймворки ГОСО |
| GET | `/frameworks/{id}` | Фреймворк |
| GET | `/frameworks/{id}/structure` | Структура (разделы, подразделы) |
| GET | `/outcomes` | Цели обучения |
| GET | `/outcomes/{id}` | Цель обучения с контекстом |
| GET | `/paragraphs/{id}/outcomes` | Связи параграфа с целями |

### GET /goso/outcomes

Получить цели обучения с фильтрами.

**Query параметры:**
- `framework_id` - ID фреймворка ГОСО
- `grade` - класс (1-11)
- `section_id` - ID раздела
- `subsection_id` - ID подраздела
- `is_active` - активные (true/false)
- `limit`, `offset` - пагинация

**Response:**
```json
[
  {
    "id": 42,
    "framework_id": 1,
    "subsection_id": 5,
    "grade": 7,
    "code": "7.1.2.1",
    "title_ru": "Определять причины и последствия событий",
    "title_kz": "...",
    "cognitive_level": "understanding",
    "is_active": true
  }
]
```

---

## 8. Загрузка файлов

**Prefix:** `/api/v1/upload`
**Требуется:** роль SUPER_ADMIN

### Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/image` | Загрузить изображение (JPEG, PNG, WebP, GIF, max 5MB) |
| POST | `/pdf` | Загрузить PDF (max 50MB) |

**POST /upload/image:**

```bash
curl -X POST https://api.ai-mentor.kz/api/v1/upload/image \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@image.png"
```

**Response:**
```json
{
  "url": "/uploads/images/abc123.png",
  "filename": "image.png",
  "size": 125000,
  "mime_type": "image/png"
}
```

---

## 9. Примеры использования

### Python скрипт для заполнения контента

```python
import requests

API_URL = "https://api.ai-mentor.kz/api/v1"

class ContentAPI:
    def __init__(self, is_super_admin=True):
        self.token = None
        self.prefix = "admin/global" if is_super_admin else "admin/school"

    def login(self, email: str, password: str):
        response = requests.post(f"{API_URL}/auth/login", json={
            "email": email,
            "password": password
        })
        response.raise_for_status()
        self.token = response.json()["access_token"]

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def create_textbook(self, data: dict):
        response = requests.post(
            f"{API_URL}/{self.prefix}/textbooks",
            json=data,
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def create_chapter(self, data: dict):
        response = requests.post(
            f"{API_URL}/{self.prefix}/chapters",
            json=data,
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def create_paragraph(self, data: dict):
        response = requests.post(
            f"{API_URL}/{self.prefix}/paragraphs",
            json=data,
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

# Пример использования
api = ContentAPI(is_super_admin=True)
api.login("superadmin@aimentor.com", "admin123")

textbook = api.create_textbook({
    "title": "История Казахстана 8 класс",
    "subject": "История",
    "grade_level": 8,
    "author": "К. Жумагулов",
    "is_active": True
})

chapter = api.create_chapter({
    "textbook_id": textbook["id"],
    "title": "Жоңғар шапқыншылығы",
    "number": 1,
    "order": 1
})

paragraph = api.create_paragraph({
    "chapter_id": chapter["id"],
    "title": "Ақтабан шұбырынды",
    "number": 1,
    "order": 1,
    "content": "<h2>Ақтабан шұбырынды</h2><p>...</p>",
    "key_terms": ["Жоңғар", "Ақтабан"],
    "questions": [
        {"order": 1, "text": "Қай жылы болды?"}
    ]
})

print(f"Created: Textbook={textbook['id']}, Chapter={chapter['id']}, Paragraph={paragraph['id']}")
```

### Bash/cURL пример

```bash
#!/bin/bash

API_URL="https://api.ai-mentor.kz/api/v1"

# 1. Авторизация
TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@aimentor.com","password":"admin123"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 2. Создание учебника
TEXTBOOK=$(curl -s -X POST "$API_URL/admin/global/textbooks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Алгебра 7 класс",
    "subject": "Математика",
    "grade_level": 7,
    "is_active": true
  }')

TEXTBOOK_ID=$(echo "$TEXTBOOK" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
echo "Textbook ID: $TEXTBOOK_ID"

# 3. Создание главы
CHAPTER=$(curl -s -X POST "$API_URL/admin/global/chapters" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"textbook_id\": $TEXTBOOK_ID,
    \"title\": \"Линейные уравнения\",
    \"number\": 1,
    \"order\": 1
  }")

CHAPTER_ID=$(echo "$CHAPTER" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
echo "Chapter ID: $CHAPTER_ID"
```

---

## Тестовые аккаунты

### Администраторы

| Роль | Email | Пароль |
|------|-------|--------|
| SUPER_ADMIN | superadmin@aimentor.com | admin123 |
| School ADMIN | school.admin@test.com | admin123 |

### Учителя (Школа №7)

| Email | Пароль | Предмет |
|-------|--------|---------|
| teacher.math@school001.com | teacher123 | Математика |
| teacher.physics@school001.com | teacher123 | Физика |
| teacher.history@school001.com | teacher123 | История |

### Ученики (Школа №7)

| Email | Пароль | Класс |
|-------|--------|-------|
| student1@school001.com | student123 | 7-А |
| student2@school001.com | student123 | 7-А |
| student3@school001.com | student123 | 8-Б |

---

## Полезные советы

### 1. Проверка токена

Токен действует 30 минут. При истечении используйте `/auth/refresh`.

### 2. Формат content

Поле `content` в параграфе принимает HTML:
```html
<h2>Заголовок</h2>
<p>Текст параграфа...</p>
<ul>
  <li>Пункт 1</li>
  <li>Пункт 2</li>
</ul>
```

### 3. key_terms и questions

```json
{
  "key_terms": ["термин1", "термин2"],
  "questions": [
    {"order": 1, "text": "Вопрос 1?"},
    {"order": 2, "text": "Вопрос 2?"}
  ]
}
```

### 4. Swagger документация

Интерактивная документация доступна по адресу:
```
https://api.ai-mentor.kz/docs
```

---

**Готово!** Используйте API для автоматизации работы с контентом.
