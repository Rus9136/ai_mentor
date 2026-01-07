# Mobile API Guide for AI Mentor

**Version:** 2.0
**Last Updated:** 2026-01-07
**API Version:** v1

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Base URL & Versioning](#2-base-url--versioning)
3. [Authentication](#3-authentication)
4. [Common Response Format](#4-common-response-format)
5. [Error Handling](#5-error-handling)
6. [Student API Endpoints](#6-student-api-endpoints)
7. [Content API](#7-content-api)
8. [Tests & Assessments](#8-tests--assessments)
9. [Homework System](#9-homework-system)
10. [Mastery Tracking](#10-mastery-tracking)
11. [AI Chat Assistant](#11-ai-chat-assistant)
12. [Pagination](#12-pagination)
13. [Rate Limiting](#13-rate-limiting)
14. [Security Requirements](#14-security-requirements)
15. [Offline Sync Strategy](#15-offline-sync-strategy)

---

## 1. Quick Start

### Basic Flow

```
1. Login → Get access_token + refresh_token
2. Store tokens securely (Keychain/EncryptedSharedPreferences)
3. Add Authorization header to all requests
4. Refresh token when access_token expires (401)
5. Fetch content → Store locally for offline
6. Sync progress when online
```

### First Request Example

```bash
# Login
curl -X POST https://api.ai-mentor.kz/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "student@school.com", "password": "password123"}'

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}

# Authenticated request
curl https://api.ai-mentor.kz/api/v1/students/textbooks \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## 2. Base URL & Versioning

### Environments

| Environment | Base URL |
|-------------|----------|
| **Production** | `https://api.ai-mentor.kz/api/v1` |
| **Staging** | `https://staging-api.ai-mentor.kz/api/v1` |

### Headers

```
Content-Type: application/json
Accept: application/json
Authorization: Bearer <access_token>
```

---

## 3. Authentication

### 3.1 Login

**Endpoint:** `POST /auth/login`

**Request:**
```json
{
  "email": "student@school.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Token Expiration:**
- `access_token`: 30 minutes
- `refresh_token`: 7 days

### 3.2 Refresh Token

**Endpoint:** `POST /auth/refresh`

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...(new)",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...(new)",
  "token_type": "bearer"
}
```

### 3.3 Get Current User

**Endpoint:** `GET /auth/me`

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "student@school.com",
  "role": "student",
  "school_id": 7,
  "first_name": "Иван",
  "last_name": "Сидоров",
  "middle_name": "Петрович",
  "phone": "+7 700 123 45 67",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-20T14:45:00"
}
```

### 3.4 Google OAuth

**Endpoint:** `POST /auth/google`

**Request:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "requires_onboarding": true,
  "user": {
    "id": 1,
    "email": "student@gmail.com",
    "role": "student"
  }
}
```

### 3.5 Token Storage Requirements

| Platform | Required Storage |
|----------|------------------|
| iOS | Keychain Services |
| Android | EncryptedSharedPreferences |
| React Native | react-native-keychain |
| Flutter | flutter_secure_storage |

---

## 4. Common Response Format

### Success Response (Single Object)

```json
{
  "id": 1,
  "title": "Алгебра 9",
  "field": "value"
}
```

### Paginated List Response

All list endpoints return paginated responses:

```json
{
  "items": [
    { "id": 1, "title": "Item 1" },
    { "id": 2, "title": "Item 2" }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### Data Types

| Type | Format | Example |
|------|--------|---------|
| `datetime` | ISO 8601 | `"2024-01-15T10:30:00"` |
| `date` | ISO 8601 | `"2024-01-15"` |
| `boolean` | JSON boolean | `true`, `false` |
| `null` | JSON null | `null` |
| `enum` | string | `"draft"`, `"published"` |
| `float` | decimal | `0.85`, `75.5` |

---

## 5. Error Handling

### Error Response Format

**Standard Error:**
```json
{
  "detail": "Error message description",
  "error_code": "AUTH_001"
}
```

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTH_001` | 401 | Invalid credentials |
| `AUTH_002` | 401 | Token expired |
| `AUTH_003` | 401 | Invalid token |
| `AUTH_004` | 401 | Token revoked |
| `ACCESS_001` | 403 | Permission denied |
| `ACCESS_002` | 403 | Role not allowed |
| `ACCESS_003` | 403 | School access denied |
| `VAL_001` | 400 | Invalid format |
| `VAL_002` | 400 | Required field missing |
| `VAL_003` | 422 | Validation failed |
| `RES_001` | 404 | Resource not found |
| `RES_002` | 409 | Resource already exists |
| `SVC_001` | 500 | Internal server error |
| `SVC_002` | 503 | AI service unavailable |
| `RATE_001` | 429 | Rate limit exceeded |

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| `200` | OK | Successful GET, PUT, PATCH |
| `201` | Created | Successful POST (created resource) |
| `204` | No Content | Successful DELETE |
| `400` | Bad Request | Validation error, invalid data |
| `401` | Unauthorized | Invalid/expired token |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Duplicate entry |
| `422` | Unprocessable Entity | Validation failed |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |

---

## 6. Student API Endpoints

### 6.1 Get Dashboard Stats

**Endpoint:** `GET /students/stats`

**Response:**
```json
{
  "student_id": 10,
  "total_textbooks": 5,
  "total_chapters": 25,
  "total_paragraphs": 150,
  "completed_paragraphs": 45,
  "mastered_paragraphs": 30,
  "struggling_paragraphs": 5,
  "average_mastery_score": 72.5,
  "total_tests_taken": 20,
  "tests_passed": 18,
  "average_test_score": 0.78,
  "total_time_spent_minutes": 1200,
  "current_streak_days": 5,
  "longest_streak_days": 12,
  "last_activity_at": "2024-02-15T14:30:00"
}
```

### 6.2 Get Student Progress

**Endpoint:** `GET /students/progress`

**Response:**
```json
{
  "student_id": 10,
  "overall_progress": 45.5,
  "textbooks": [
    {
      "textbook_id": 1,
      "title": "Алгебра 9",
      "progress_percentage": 60,
      "mastery_score": 75.0,
      "chapters_completed": 3,
      "chapters_total": 5
    }
  ]
}
```

---

## 7. Content API

### 7.1 Get Textbooks

**Endpoint:** `GET /students/textbooks`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max: 100) |
| `subject_id` | int | - | Filter by subject |
| `grade_level` | int | - | Filter by grade (1-11) |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Алгебра 9",
      "subject_id": 1,
      "subject": "Математика",
      "subject_rel": {
        "id": 1,
        "name": "Математика",
        "code": "MATH"
      },
      "grade_level": 9,
      "description": "Учебник по алгебре для 9 класса",
      "is_global": true,
      "progress": {
        "chapters_total": 5,
        "chapters_completed": 3,
        "paragraphs_total": 50,
        "paragraphs_completed": 25,
        "percentage": 50.0
      },
      "mastery_level": "B",
      "last_activity": "2024-02-15T14:30:00",
      "author": "Алимов Ш.А.",
      "chapters_count": 5
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### 7.2 Get Chapters

**Endpoint:** `GET /students/textbooks/{textbook_id}/chapters`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max: 100) |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "textbook_id": 1,
      "title": "Квадратные уравнения",
      "number": 1,
      "order": 1,
      "description": "Основные типы квадратных уравнений",
      "learning_objective": "Научиться решать квадратные уравнения",
      "status": "in_progress",
      "progress": {
        "paragraphs_total": 10,
        "paragraphs_completed": 5,
        "percentage": 50.0
      },
      "mastery_level": "B",
      "mastery_score": 72.0,
      "has_summative_test": true,
      "summative_passed": false
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### 7.3 Get Paragraphs

**Endpoint:** `GET /students/chapters/{chapter_id}/paragraphs`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max: 100) |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "chapter_id": 1,
      "title": "Определение квадратного уравнения",
      "number": 1,
      "order": 1,
      "summary": "Основное определение и форма квадратного уравнения",
      "status": "completed",
      "estimated_time": 15,
      "has_practice": true,
      "practice_score": 85.0,
      "learning_objective": "Понять определение",
      "key_terms": ["квадратное уравнение", "коэффициент"]
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### 7.4 Get Paragraph Content

**Endpoint:** `GET /students/paragraphs/{paragraph_id}`

**Response:**
```json
{
  "id": 1,
  "chapter_id": 1,
  "title": "Определение квадратного уравнения",
  "number": 1,
  "order": 1,
  "content": "<p>Квадратным уравнением называется...</p>",
  "summary": "Основное определение",
  "learning_objective": "Понять определение",
  "lesson_objective": "Научиться распознавать",
  "key_terms": ["квадратное уравнение", "коэффициент"],
  "questions": [
    {
      "order": 1,
      "text": "Что такое квадратное уравнение?"
    }
  ],
  "status": "completed",
  "current_step": "summary",
  "has_audio": true,
  "has_video": true,
  "has_slides": false,
  "has_cards": true,
  "chapter_title": "Квадратные уравнения",
  "textbook_title": "Алгебра 9"
}
```

### 7.5 Get Rich Content

**Endpoint:** `GET /students/paragraphs/{paragraph_id}/content`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `language` | string | "ru" | Content language: "ru" or "kk" |

**Response:**
```json
{
  "paragraph_id": 1,
  "language": "ru",
  "explain_text": "Подробное объяснение темы...",
  "audio_url": "/uploads/audio/paragraph-1.mp3",
  "video_url": "https://youtube.com/watch?v=...",
  "slides_url": "/uploads/slides/paragraph-1.pdf",
  "cards": [
    {
      "id": "card-1",
      "front": "Что такое дискриминант?",
      "back": "D = b² - 4ac"
    }
  ],
  "has_explain": true,
  "has_audio": true,
  "has_video": true,
  "has_slides": true,
  "has_cards": true
}
```

### 7.6 Paragraph Navigation

**Endpoint:** `GET /students/paragraphs/{paragraph_id}/navigation`

**Response:**
```json
{
  "current": {
    "id": 5,
    "title": "Формула дискриминанта",
    "number": 5
  },
  "previous": {
    "id": 4,
    "title": "Неполные квадратные уравнения",
    "number": 4
  },
  "next": {
    "id": 6,
    "title": "Теорема Виета",
    "number": 6
  },
  "chapter": {
    "id": 1,
    "title": "Квадратные уравнения",
    "total_paragraphs": 10
  }
}
```

---

## 8. Tests & Assessments

### 8.1 Get Available Tests

**Endpoint:** `GET /students/tests`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max: 100) |
| `chapter_id` | int | - | Filter by chapter |
| `paragraph_id` | int | - | Filter by paragraph |
| `test_purpose` | string | - | Filter: formative, summative, practice |
| `difficulty` | string | - | Filter: easy, medium, hard |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Тест: Квадратные уравнения",
      "description": "Формативный тест",
      "test_purpose": "formative",
      "difficulty": "medium",
      "time_limit": 45,
      "passing_score": 0.7,
      "is_active": true,
      "chapter_id": 1,
      "paragraph_id": null,
      "school_id": null,
      "question_count": 10,
      "attempts_count": 2,
      "best_score": 0.85,
      "created_at": "2024-01-10T08:00:00",
      "updated_at": "2024-01-10T08:00:00"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### 8.2 Start Test Attempt

**Endpoint:** `POST /students/tests/{test_id}/start`

**Response (201 Created):**
```json
{
  "id": 123,
  "student_id": 10,
  "test_id": 1,
  "school_id": 7,
  "attempt_number": 1,
  "status": "in_progress",
  "started_at": "2024-02-15T10:00:00",
  "completed_at": null,
  "score": null,
  "points_earned": null,
  "total_points": null,
  "passed": null,
  "time_spent": null,
  "test": {
    "id": 1,
    "title": "Тест: Квадратные уравнения",
    "time_limit": 45,
    "questions": [
      {
        "id": 1,
        "question_text": "Какой коэффициент называется старшим?",
        "question_type": "single_choice",
        "points": 1.0,
        "options": [
          {"id": 1, "text": "Коэффициент a", "order": 1},
          {"id": 2, "text": "Коэффициент b", "order": 2},
          {"id": 3, "text": "Коэффициент c", "order": 3}
        ]
      }
    ]
  },
  "answers": []
}
```

### 8.3 Submit Single Answer

**Endpoint:** `POST /students/attempts/{attempt_id}/answer`

**Request:**
```json
{
  "question_id": 1,
  "selected_option_ids": [1]
}
```

**Response:**
```json
{
  "question_id": 1,
  "is_correct": true,
  "correct_option_ids": [1],
  "explanation": "Правильно! Коэффициент при x² называется старшим.",
  "points_earned": 1.0,
  "answered_count": 1,
  "total_questions": 10,
  "is_test_complete": false,
  "test_score": null,
  "test_passed": null
}
```

### 8.4 Submit All Answers

**Endpoint:** `POST /students/attempts/{attempt_id}/submit`

**Request:**
```json
{
  "answers": [
    {
      "question_id": 1,
      "selected_option_ids": [1]
    },
    {
      "question_id": 2,
      "selected_option_ids": [2, 3]
    }
  ]
}
```

**Response:**
```json
{
  "id": 123,
  "status": "completed",
  "score": 0.85,
  "passed": true,
  "points_earned": 8.5,
  "total_points": 10.0,
  "time_spent": 1200,
  "completed_at": "2024-02-15T10:20:00"
}
```

### 8.5 Get Attempt Details

**Endpoint:** `GET /students/attempts/{attempt_id}`

**Response:**
```json
{
  "id": 123,
  "test_id": 1,
  "status": "completed",
  "score": 0.85,
  "passed": true,
  "started_at": "2024-02-15T10:00:00",
  "completed_at": "2024-02-15T10:20:00",
  "time_spent": 1200,
  "answers": [
    {
      "question_id": 1,
      "selected_option_ids": [1],
      "is_correct": true,
      "points_earned": 1.0
    }
  ]
}
```

---

## 9. Homework System

### 9.1 Get Homework List

**Endpoint:** `GET /students/homework`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max: 100) |
| `status` | string | - | Filter: assigned, in_progress, submitted, graded |
| `include_completed` | bool | true | Include completed homework |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Домашнее задание: Квадратные уравнения",
      "description": "Решить задачи по квадратным уравнениям",
      "due_date": "2024-02-20T18:00:00",
      "is_overdue": false,
      "can_submit": true,
      "my_status": "in_progress",
      "my_score": 7.5,
      "max_score": 10,
      "my_percentage": 75.0,
      "is_late": false,
      "late_penalty": 0,
      "show_explanations": true,
      "tasks": [...]
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### 9.2 Get Homework Details

**Endpoint:** `GET /students/homework/{homework_id}`

**Response:**
```json
{
  "id": 1,
  "title": "Домашнее задание: Квадратные уравнения",
  "description": "Решить задачи",
  "due_date": "2024-02-20T18:00:00",
  "is_overdue": false,
  "can_submit": true,
  "my_status": "in_progress",
  "my_score": 7.5,
  "max_score": 10,
  "my_percentage": 75.0,
  "is_late": false,
  "late_penalty": 0,
  "show_explanations": true,
  "tasks": [
    {
      "id": 1,
      "paragraph_id": 1,
      "paragraph_title": "Определение квадратного уравнения",
      "task_type": "quiz",
      "instructions": "Ответьте на вопросы",
      "points": 10,
      "time_limit_minutes": 15,
      "status": "completed",
      "current_attempt": 1,
      "max_attempts": 3,
      "attempts_remaining": 2,
      "questions_count": 5,
      "answered_count": 5
    }
  ]
}
```

### 9.3 Start Homework Task

**Endpoint:** `POST /students/homework/{homework_id}/tasks/{task_id}/start`

**Response (201 Created):**
```json
{
  "id": 1,
  "paragraph_id": 1,
  "paragraph_title": "Определение",
  "task_type": "quiz",
  "instructions": "Ответьте на вопросы",
  "points": 10,
  "time_limit_minutes": 15,
  "status": "in_progress",
  "current_attempt": 1,
  "max_attempts": 3,
  "attempts_remaining": 2,
  "submission_id": 456,
  "questions_count": 5,
  "answered_count": 0
}
```

### 9.4 Get Task Questions

**Endpoint:** `GET /students/homework/{homework_id}/tasks/{task_id}/questions`

**Response:**
```json
[
  {
    "id": 1,
    "question_text": "Решите уравнение: x² - 5x + 6 = 0",
    "question_type": "short_answer",
    "options": null,
    "points": 2,
    "my_answer": null,
    "my_selected_options": null,
    "is_answered": false
  }
]
```

### 9.5 Submit Answer

**Endpoint:** `POST /students/homework/submissions/{submission_id}/answer`

**Request:**
```json
{
  "question_id": 1,
  "answer_text": "x = 2, x = 3"
}
```

**Response:**
```json
{
  "question_id": 1,
  "is_correct": true,
  "points_earned": 2,
  "explanation": "Правильно!",
  "ai_feedback": "Отлично! Ты правильно применил формулу."
}
```

### 9.6 Complete Submission

**Endpoint:** `POST /students/homework/submissions/{submission_id}/complete`

**Response:**
```json
{
  "submission_id": 456,
  "task_id": 1,
  "status": "completed",
  "score": 8,
  "max_score": 10,
  "percentage": 80.0,
  "time_spent_seconds": 600,
  "is_late": false,
  "late_penalty": 0
}
```

---

## 10. Mastery Tracking

### 10.1 Get Chapter Mastery

**Endpoint:** `GET /students/mastery/chapter/{chapter_id}`

**Response:**
```json
{
  "id": 1,
  "student_id": 10,
  "chapter_id": 1,
  "total_paragraphs": 5,
  "completed_paragraphs": 4,
  "mastered_paragraphs": 3,
  "struggling_paragraphs": 0,
  "average_score": 0.80,
  "weighted_score": 0.82,
  "summative_score": 0.88,
  "summative_passed": true,
  "mastery_level": "B",
  "mastery_score": 82.0,
  "progress_percentage": 80,
  "estimated_completion_date": "2024-02-28",
  "last_updated_at": "2024-02-15T14:30:00",
  "chapter_title": "Квадратные уравнения",
  "chapter_order": 1,
  "paragraphs": [
    {
      "id": 1,
      "paragraph_id": 1,
      "paragraph_title": "Определение",
      "status": "mastered",
      "mastery_score": 90.0,
      "attempts_count": 3
    }
  ]
}
```

### 10.2 Get Mastery Overview

**Endpoint:** `GET /students/mastery/overview`

**Response:**
```json
{
  "student_id": 10,
  "chapters": [
    {
      "chapter_id": 1,
      "chapter_title": "Квадратные уравнения",
      "mastery_level": "B",
      "mastery_score": 82.0,
      "progress_percentage": 80
    }
  ],
  "total_chapters": 2,
  "average_mastery_score": 63.5,
  "level_a_count": 0,
  "level_b_count": 1,
  "level_c_count": 1
}
```

### Mastery Levels

| Level | Score Range | Description |
|-------|-------------|-------------|
| **A** | 85-100% | Mastered |
| **B** | 60-84% | Progressing |
| **C** | 0-59% | Struggling |

---

## 11. AI Chat Assistant

### 11.1 Create Chat Session

**Endpoint:** `POST /chat/sessions`

**Request:**
```json
{
  "session_type": "reading_help",
  "paragraph_id": 1,
  "language": "ru"
}
```

**Session Types:**
- `reading_help` - Help while reading content
- `post_paragraph` - Questions after reading
- `test_help` - Help during test
- `general_tutor` - General tutoring

**Response (201 Created):**
```json
{
  "id": 1,
  "session_type": "reading_help",
  "paragraph_id": 1,
  "chapter_id": 1,
  "title": null,
  "mastery_level": "B",
  "language": "ru",
  "message_count": 0,
  "total_tokens_used": 0,
  "created_at": "2024-02-15T10:00:00"
}
```

### 11.2 Send Message

**Endpoint:** `POST /chat/sessions/{session_id}/messages`

**Request:**
```json
{
  "content": "Как решать квадратные уравнения через дискриминант?"
}
```

**Response:**
```json
{
  "id": 2,
  "role": "assistant",
  "content": "Для решения квадратного уравнения ax² + bx + c = 0 через дискриминант:\n\n1. **Вычислить дискриминант:** D = b² - 4ac\n\n2. **Определить количество корней:**\n   - D > 0: два различных корня\n   - D = 0: один корень\n   - D < 0: нет вещественных корней\n\n3. **Найти корни:** x = (-b ± √D) / 2a",
  "citations": [
    {
      "text": "Формула дискриминанта",
      "source": "Параграф 3: Дискриминант",
      "url": "/paragraphs/3"
    }
  ],
  "tokens_used": 150,
  "model_used": "gpt-4",
  "processing_time_ms": 2500,
  "created_at": "2024-02-15T10:05:30"
}
```

### 11.3 Get Chat Sessions

**Endpoint:** `GET /chat/sessions`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 10 | Items per page (max: 50) |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "session_type": "reading_help",
      "paragraph_id": 1,
      "title": "Помощь с квадратными уравнениями",
      "message_count": 5,
      "last_message_at": "2024-02-15T14:30:00",
      "created_at": "2024-02-15T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

### 11.4 Get Session with Messages

**Endpoint:** `GET /chat/sessions/{session_id}`

**Response:**
```json
{
  "id": 1,
  "session_type": "reading_help",
  "paragraph_id": 1,
  "message_count": 2,
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Как решать квадратные уравнения?",
      "created_at": "2024-02-15T10:05:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Для решения квадратного уравнения...",
      "citations": [...],
      "created_at": "2024-02-15T10:05:30"
    }
  ]
}
```

### 11.5 Delete Session

**Endpoint:** `DELETE /chat/sessions/{session_id}`

**Response:** `204 No Content`

---

## 12. Pagination

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | int | 1 | - | Page number (1-indexed) |
| `page_size` | int | 20 | 100 | Items per page |

### Example Request

```
GET /students/textbooks?page=2&page_size=10
GET /students/homework?page=1&page_size=50&status=in_progress
```

### Response Structure

```json
{
  "items": [...],
  "total": 100,
  "page": 2,
  "page_size": 10,
  "total_pages": 10
}
```

### Pagination Logic

- `total_pages = ceil(total / page_size)`
- `has_next_page = page < total_pages`
- `has_prev_page = page > 1`

---

## 13. Rate Limiting

### Current Limits

| Endpoint Category | Limit | Window |
|-------------------|-------|--------|
| `/auth/login` | 5 requests | 1 minute |
| `/auth/refresh` | 10 requests | 1 minute |
| `/chat/sessions/*/messages` | 20 requests | 1 minute |
| All other endpoints | 60 requests | 1 minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1706180000
```

### 429 Response

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "error_code": "RATE_001"
}
```

### Retry Strategy

When receiving 429:
1. Parse `X-RateLimit-Reset` header
2. Wait until reset time
3. Implement exponential backoff for retries

---

## 14. Security Requirements

### Token Storage

| Requirement | Platform |
|-------------|----------|
| Use secure storage | Keychain (iOS), EncryptedSharedPreferences (Android) |
| Clear on logout | Delete all stored tokens |
| Never log tokens | Exclude from crash reports |

### Certificate Pinning (Recommended)

Pin the API certificate to prevent MITM attacks:
- Domain: `api.ai-mentor.kz`
- SHA256 fingerprint provided separately

### Network Security

- HTTPS only (no HTTP fallback)
- TLS 1.2+ required
- Disable cleartext traffic

### Sensitive Data

- Never log passwords or tokens
- Mask email in logs: `s***t@school.com`
- Don't include in error reports

---

## 15. Offline Sync Strategy

### Data Categories

| Category | Sync Strategy | Priority |
|----------|--------------|----------|
| **Textbooks/Chapters/Paragraphs** | Download on first access, cache locally | High |
| **User Profile** | Sync on login, refresh periodically | High |
| **Mastery Progress** | Sync bidirectionally | Medium |
| **Test Attempts** | Queue locally, sync when online | High |
| **Homework Submissions** | Queue locally, sync when online | High |
| **Chat Messages** | Online only (requires AI) | Low |

### Sync Queue

For offline submissions:
1. Store in local database with `is_synced = false`
2. On connectivity restored:
   - Process queue FIFO
   - Retry failed requests (max 3 times)
   - Mark as synced on success

### Conflict Resolution

Strategy: **Server Wins for Scores**

```
IF local_score != server_score:
    USE server_score

IF local_timestamp > server_timestamp:
    WARN user about sync conflict
    KEEP server data
```

### Background Sync

- Every 15 minutes if app active
- On app resume from background
- On network connectivity change

---

## Appendix A: TypeScript Interfaces

```typescript
interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface User {
  id: number;
  email: string;
  role: 'admin' | 'teacher' | 'student' | 'parent';
  school_id: number | null;
  first_name: string;
  last_name: string;
  is_active: boolean;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface Textbook {
  id: number;
  title: string;
  subject_id: number;
  subject: string;
  grade_level: number;
  is_global: boolean;
}

interface Chapter {
  id: number;
  textbook_id: number;
  title: string;
  number: number;
  order: number;
  mastery_level: 'A' | 'B' | 'C' | null;
}

interface Paragraph {
  id: number;
  chapter_id: number;
  title: string;
  number: number;
  content: string;
  status: 'not_started' | 'in_progress' | 'completed';
}

interface APIError {
  detail: string;
  error_code?: string;
}
```

---

## Contact & Support

**API Issues:** api-support@ai-mentor.kz
**Documentation:** https://docs.ai-mentor.kz

---

**Document Version:** 2.0
**Last Updated:** 2026-01-07
