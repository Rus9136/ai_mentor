# Mobile API Guide for AI Mentor

**Version:** 1.0
**Last Updated:** 2026-01-05
**Target Platforms:** iOS (Swift/SwiftUI), Android (Kotlin), React Native, Flutter

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
13. [Offline Sync Strategy](#13-offline-sync-strategy)
14. [Security Best Practices](#14-security-best-practices)
15. [Rate Limiting](#15-rate-limiting)
16. [SDK Examples](#16-sdk-examples)

---

## 1. Quick Start

### Minimum Requirements

```
iOS: 15.0+
Android: API 26+ (Android 8.0)
```

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

| Environment | Base URL | Description |
|-------------|----------|-------------|
| **Production** | `https://api.ai-mentor.kz/api/v1` | Live environment |
| **Staging** | `https://staging-api.ai-mentor.kz/api/v1` | Testing environment |
| **Local** | `http://localhost:8000/api/v1` | Development |

### API Version

Current version: **v1**

All endpoints are prefixed with `/api/v1/`. Version is included in the URL path.

```
https://api.ai-mentor.kz/api/v1/students/textbooks
                          ^^^^^^
                          Version prefix
```

### Content-Type

All requests must use:
```
Content-Type: application/json
Accept: application/json
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
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6InN0dWRlbnQiLCJzY2hvb2xfaWQiOjcsImV4cCI6MTcwNjE4MDAwMH0.xxx",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidHlwZSI6InJlZnJlc2giLCJleHAiOjE3MDY3ODQ4MDB9.yyy",
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

### 3.5 Using Authorization Header

Add to all authenticated requests:

```
Authorization: Bearer <access_token>
```

### 3.6 Token Storage

| Platform | Recommended Storage |
|----------|-------------------|
| iOS | Keychain Services |
| Android | EncryptedSharedPreferences |
| React Native | react-native-keychain |
| Flutter | flutter_secure_storage |

**Example (iOS Swift):**
```swift
import Security

func saveToken(_ token: String, forKey key: String) {
    let data = token.data(using: .utf8)!
    let query: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrAccount as String: key,
        kSecValueData as String: data
    ]
    SecItemAdd(query as CFDictionary, nil)
}
```

**Example (Android Kotlin):**
```kotlin
val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build()

val sharedPreferences = EncryptedSharedPreferences.create(
    context,
    "secret_prefs",
    masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)

sharedPreferences.edit().putString("access_token", token).apply()
```

---

## 4. Common Response Format

### Success Response

```json
{
  "field1": "value1",
  "field2": "value2",
  ...
}
```

All successful responses return the data directly (no wrapper).

### List Response

```json
[
  { "id": 1, "title": "Item 1" },
  { "id": 2, "title": "Item 2" }
]
```

### Paginated List Response

```json
{
  "items": [
    { "id": 1, "title": "Item 1" },
    { "id": 2, "title": "Item 2" }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
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

```json
{
  "detail": "Error message description"
}
```

Or with validation errors:
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
| `409` | Conflict | Duplicate entry (email, code) |
| `422` | Unprocessable Entity | Validation failed |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |

### Error Handling Strategy

```swift
// iOS Swift Example
func handleResponse<T: Decodable>(_ response: HTTPURLResponse, data: Data) throws -> T {
    switch response.statusCode {
    case 200...299:
        return try JSONDecoder().decode(T.self, from: data)
    case 401:
        // Token expired - refresh and retry
        throw APIError.unauthorized
    case 403:
        throw APIError.forbidden
    case 404:
        throw APIError.notFound
    case 422:
        let error = try JSONDecoder().decode(ValidationError.self, from: data)
        throw APIError.validation(error)
    case 429:
        throw APIError.rateLimited
    default:
        throw APIError.serverError(response.statusCode)
    }
}
```

```kotlin
// Android Kotlin Example
sealed class ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class Error(val code: Int, val message: String) : ApiResult<Nothing>()
}

suspend fun <T> handleResponse(response: Response<T>): ApiResult<T> {
    return when {
        response.isSuccessful -> ApiResult.Success(response.body()!!)
        response.code() == 401 -> {
            // Refresh token and retry
            ApiResult.Error(401, "Unauthorized")
        }
        response.code() == 429 -> ApiResult.Error(429, "Rate limited")
        else -> ApiResult.Error(response.code(), response.message())
    }
}
```

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

**Response:**
```json
[
  {
    "id": 1,
    "school_id": null,
    "title": "Алгебра 9",
    "subject_id": 1,
    "subject": "Математика",
    "subject_rel": {
      "id": 1,
      "name": "Математика",
      "code": "MATH"
    },
    "grade_level": 9,
    "author": "Алимов Ш.А.",
    "publisher": "Просвещение",
    "year": 2024,
    "description": "Учебник по алгебре для 9 класса",
    "is_active": true,
    "is_customized": false,
    "version": 1,
    "created_at": "2024-01-10T08:00:00"
  }
]
```

### 7.2 Get Chapters

**Endpoint:** `GET /students/textbooks/{textbook_id}/chapters`

**Response:**
```json
[
  {
    "id": 1,
    "textbook_id": 1,
    "title": "Квадратные уравнения",
    "number": 1,
    "order": 1,
    "description": "Основные типы квадратных уравнений",
    "learning_objective": "Научиться решать квадратные уравнения",
    "created_at": "2024-01-10T08:00:00"
  }
]
```

### 7.3 Get Paragraphs

**Endpoint:** `GET /students/chapters/{chapter_id}/paragraphs`

**Response:**
```json
[
  {
    "id": 1,
    "chapter_id": 1,
    "title": "Определение квадратного уравнения",
    "number": 1,
    "order": 1,
    "summary": "Основное определение и форма квадратного уравнения",
    "key_terms": ["квадратное уравнение", "коэффициент", "дискриминант"],
    "created_at": "2024-01-10T08:00:00"
  }
]
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
  "content": "<p>Квадратным уравнением называется уравнение вида ax² + bx + c = 0...</p>",
  "summary": "Основное определение и форма квадратного уравнения",
  "learning_objective": "Понять определение квадратного уравнения",
  "lesson_objective": "Научиться распознавать квадратные уравнения",
  "key_terms": ["квадратное уравнение", "коэффициент", "дискриминант"],
  "questions": [
    {
      "order": 1,
      "text": "Что такое квадратное уравнение?"
    }
  ],
  "created_at": "2024-01-10T08:00:00",
  "updated_at": "2024-01-20T14:45:00"
}
```

### 7.5 Get Rich Content

**Endpoint:** `GET /students/paragraphs/{paragraph_id}/content`

**Response:**
```json
{
  "paragraph_id": 1,
  "title": "Определение квадратного уравнения",
  "language": "ru",
  "content_cards": [
    {
      "id": "card-1",
      "type": "text",
      "order": 1,
      "data": {
        "text": "Квадратным уравнением называется уравнение вида ax² + bx + c = 0"
      }
    },
    {
      "id": "card-2",
      "type": "image",
      "order": 2,
      "data": {
        "url": "/uploads/images/quadratic-formula.png",
        "caption": "Формула дискриминанта"
      }
    },
    {
      "id": "card-3",
      "type": "video",
      "order": 3,
      "data": {
        "url": "https://youtube.com/watch?v=...",
        "title": "Решение квадратных уравнений"
      }
    }
  ],
  "audio_url": "/uploads/audio/paragraph-1.mp3",
  "slides_url": "/uploads/slides/paragraph-1.pdf"
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
- `chapter_id` (optional): Filter by chapter
- `paragraph_id` (optional): Filter by paragraph

**Response:**
```json
[
  {
    "id": 1,
    "textbook_id": 1,
    "chapter_id": 1,
    "paragraph_id": null,
    "title": "Тест: Квадратные уравнения",
    "description": "Формативный тест",
    "test_purpose": "formative",
    "difficulty": "medium",
    "time_limit": 45,
    "passing_score": 0.7,
    "is_active": true,
    "questions_count": 10,
    "created_at": "2024-01-10T08:00:00"
  }
]
```

### 8.2 Start Test Attempt

**Endpoint:** `POST /students/tests/{test_id}/start`

**Response (201 Created):**
```json
{
  "attempt_id": 123,
  "test_id": 1,
  "test_title": "Тест: Квадратные уравнения",
  "time_limit": 45,
  "started_at": "2024-02-15T10:00:00",
  "expires_at": "2024-02-15T10:45:00",
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
}
```

### 8.3 Submit Answer

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

### 8.4 Submit Test

**Endpoint:** `POST /students/attempts/{attempt_id}/submit`

**Response:**
```json
{
  "attempt_id": 123,
  "test_id": 1,
  "score": 0.85,
  "passed": true,
  "passing_score": 0.7,
  "correct_answers": 8,
  "total_questions": 10,
  "time_spent_seconds": 1200,
  "completed_at": "2024-02-15T10:20:00",
  "mastery_level_before": "B",
  "mastery_level_after": "A"
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
  "time_spent_seconds": 1200,
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

**Response:**
```json
[
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
    "tasks_count": 3
  }
]
```

### 9.2 Get Homework Details

**Endpoint:** `GET /students/homework/{homework_id}`

**Response:**
```json
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
  "tasks": [
    {
      "id": 1,
      "paragraph_id": 1,
      "paragraph_title": "Определение квадратного уравнения",
      "task_type": "quiz",
      "sort_order": 0,
      "is_required": true,
      "points": 10,
      "time_limit_minutes": 15,
      "max_attempts": 3,
      "my_attempts_used": 1,
      "my_best_score": 8,
      "status": "completed"
    }
  ]
}
```

### 9.3 Start Homework Task

**Endpoint:** `POST /students/homework/{homework_id}/tasks/{task_id}/start`

**Response (201 Created):**
```json
{
  "submission_id": 456,
  "task_id": 1,
  "attempt_number": 1,
  "max_attempts": 3,
  "started_at": "2024-02-15T10:00:00",
  "questions": [
    {
      "id": 1,
      "question_text": "Решите уравнение: x² - 5x + 6 = 0",
      "question_type": "short_answer",
      "points": 2
    }
  ]
}
```

### 9.4 Submit Answer

**Endpoint:** `POST /students/homework/{homework_id}/tasks/{task_id}/questions/{question_id}/answer`

**Request:**
```json
{
  "answer_text": "x = 2, x = 3"
}
```

**Response:**
```json
{
  "question_id": 1,
  "is_correct": true,
  "points_earned": 2,
  "explanation": "Правильно! Корни уравнения: x₁ = 2, x₂ = 3",
  "ai_feedback": "Отлично! Ты правильно применил формулу дискриминанта."
}
```

### 9.5 Submit Homework

**Endpoint:** `POST /students/homework/{homework_id}/submit`

**Response:**
```json
{
  "homework_id": 1,
  "status": "submitted",
  "submitted_at": "2024-02-15T14:30:00",
  "is_late": false,
  "total_score": 18,
  "max_score": 20,
  "percentage": 90.0,
  "late_penalty_applied": 0
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
    },
    {
      "chapter_id": 2,
      "chapter_title": "Неравенства",
      "mastery_level": "C",
      "mastery_score": 45.0,
      "progress_percentage": 30
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
| **A** | 85-100% | Mastered - excellent understanding |
| **B** | 60-84% | Progressing - good understanding |
| **C** | 0-59% | Struggling - needs more practice |

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
  "content": "Для решения квадратного уравнения ax² + bx + c = 0 через дискриминант:\n\n1. **Вычислить дискриминант:** D = b² - 4ac\n\n2. **Определить количество корней:**\n   - D > 0: два различных корня\n   - D = 0: один корень (два равных)\n   - D < 0: нет вещественных корней\n\n3. **Найти корни:** x = (-b ± √D) / 2a",
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
- `page` (default: 1)
- `page_size` (default: 10, max: 50)

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
  "page_size": 10
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

| Parameter | Default | Max | Description |
|-----------|---------|-----|-------------|
| `skip` | 0 | - | Number of items to skip |
| `limit` | 20 | 100 | Number of items to return |
| `page` | 1 | - | Page number (alternative to skip) |
| `page_size` | 20 | 50 | Items per page |

### Example

```
GET /students/homework?skip=20&limit=10
GET /chat/sessions?page=2&page_size=10
```

### Pagination Response

```json
{
  "items": [...],
  "total": 100,
  "page": 2,
  "page_size": 10
}
```

### Mobile Implementation

```swift
// iOS Swift
struct PaginatedResponse<T: Decodable>: Decodable {
    let items: [T]
    let total: Int
    let page: Int
    let pageSize: Int

    var hasNextPage: Bool {
        return page * pageSize < total
    }
}
```

```kotlin
// Android Kotlin
data class PaginatedResponse<T>(
    val items: List<T>,
    val total: Int,
    val page: Int,
    @SerializedName("page_size") val pageSize: Int
) {
    fun hasNextPage(): Boolean = page * pageSize < total
}
```

---

## 13. Offline Sync Strategy

### 13.1 Data Categories

| Category | Sync Strategy | Priority |
|----------|--------------|----------|
| **Textbooks/Chapters/Paragraphs** | Download on first access, cache locally | High |
| **User Profile** | Sync on login, refresh periodically | High |
| **Mastery Progress** | Sync bidirectionally | Medium |
| **Test Attempts** | Queue locally, sync when online | High |
| **Homework Submissions** | Queue locally, sync when online | High |
| **Chat Messages** | Online only (requires AI) | Low |

### 13.2 Local Storage Schema

```sql
-- SQLite/Realm schema for mobile

CREATE TABLE textbooks (
    id INTEGER PRIMARY KEY,
    title TEXT,
    subject TEXT,
    grade_level INTEGER,
    data JSON,  -- Full response
    synced_at DATETIME,
    is_dirty BOOLEAN DEFAULT 0
);

CREATE TABLE paragraphs (
    id INTEGER PRIMARY KEY,
    chapter_id INTEGER,
    title TEXT,
    content TEXT,
    data JSON,
    synced_at DATETIME
);

CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT,
    method TEXT,
    body JSON,
    created_at DATETIME,
    retry_count INTEGER DEFAULT 0,
    last_error TEXT
);
```

### 13.3 Sync Algorithm

```
1. App Launch:
   - Check network connectivity
   - If online: process sync queue
   - Fetch updated content (use Last-Modified header)
   - Refresh mastery progress

2. User Action (test answer, homework):
   - Save locally immediately
   - If online: send to server
   - If offline: add to sync queue

3. Coming Online:
   - Process sync queue (FIFO)
   - Retry failed requests (max 3 times)
   - Resolve conflicts (server wins for scores)

4. Background Sync:
   - Every 15 minutes if app active
   - On app resume from background
```

### 13.4 Conflict Resolution

```
Strategy: Server Wins for Scores

IF local_score != server_score:
    USE server_score

IF local_timestamp > server_timestamp:
    WARN user about sync conflict
    KEEP server data
```

### 13.5 Example Implementation

```swift
// iOS Swift - Sync Manager
class SyncManager {
    private let syncQueue: SyncQueue
    private let api: APIClient

    func processQueue() async {
        while let item = syncQueue.next() {
            do {
                try await api.send(item)
                syncQueue.remove(item)
            } catch {
                if item.retryCount < 3 {
                    syncQueue.retry(item, error: error)
                } else {
                    syncQueue.fail(item, error: error)
                    notifyUser(about: item)
                }
            }
        }
    }

    func queueAction(_ action: SyncAction) {
        syncQueue.add(action)
        if NetworkMonitor.shared.isConnected {
            Task { await processQueue() }
        }
    }
}
```

---

## 14. Security Best Practices

### 14.1 Token Storage

**DO:**
- Use Keychain (iOS) / EncryptedSharedPreferences (Android)
- Never store tokens in plain text
- Clear tokens on logout

**DON'T:**
- Store tokens in UserDefaults/SharedPreferences
- Log tokens to console
- Include tokens in crash reports

### 14.2 Certificate Pinning (Recommended)

```swift
// iOS Swift - Certificate Pinning
let serverTrustManager = ServerTrustManager(evaluators: [
    "api.ai-mentor.kz": PinnedCertificatesTrustEvaluator(
        certificates: [certificate],
        acceptSelfSignedCertificates: false,
        performDefaultValidation: true
    )
])
```

```kotlin
// Android Kotlin - Certificate Pinning
val certificatePinner = CertificatePinner.Builder()
    .add("api.ai-mentor.kz", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    .build()

val client = OkHttpClient.Builder()
    .certificatePinner(certificatePinner)
    .build()
```

### 14.3 Sensitive Data

- Never log user passwords
- Mask email in logs: `s***t@school.com`
- Don't include sensitive data in error reports

### 14.4 Network Security

```xml
<!-- Android: network_security_config.xml -->
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">ai-mentor.kz</domain>
    </domain-config>
</network-security-config>
```

```swift
// iOS: Info.plist - App Transport Security
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
</dict>
```

---

## 15. Rate Limiting

### Current Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
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

### Handling 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```

**Retry Strategy:**
```swift
func handleRateLimit(retryAfter: Int) {
    // Wait for specified time
    DispatchQueue.main.asyncAfter(deadline: .now() + .seconds(retryAfter)) {
        retryRequest()
    }
}
```

---

## 16. SDK Examples

### 16.1 iOS Swift

```swift
import Foundation

class AIMentorAPI {
    private let baseURL = "https://api.ai-mentor.kz/api/v1"
    private var accessToken: String?

    // Login
    func login(email: String, password: String) async throws -> TokenResponse {
        let url = URL(string: "\(baseURL)/auth/login")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(LoginRequest(email: email, password: password))

        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(TokenResponse.self, from: data)
        self.accessToken = response.accessToken
        return response
    }

    // Get textbooks
    func getTextbooks() async throws -> [Textbook] {
        return try await get("/students/textbooks")
    }

    // Generic GET
    private func get<T: Decodable>(_ path: String) async throws -> T {
        let url = URL(string: "\(baseURL)\(path)")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(accessToken ?? "")", forHTTPHeaderField: "Authorization")

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(T.self, from: data)
    }
}
```

### 16.2 Android Kotlin

```kotlin
import retrofit2.Retrofit
import retrofit2.http.*

interface AIMentorAPI {
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): TokenResponse

    @GET("students/textbooks")
    suspend fun getTextbooks(): List<Textbook>

    @GET("students/chapters/{chapter_id}/paragraphs")
    suspend fun getParagraphs(@Path("chapter_id") chapterId: Int): List<Paragraph>

    @POST("students/tests/{test_id}/start")
    suspend fun startTest(@Path("test_id") testId: Int): TestAttempt

    @POST("students/attempts/{attempt_id}/answer")
    suspend fun submitAnswer(
        @Path("attempt_id") attemptId: Int,
        @Body answer: AnswerRequest
    ): AnswerResponse
}

// Repository
class StudentRepository(private val api: AIMentorAPI) {
    suspend fun getTextbooks(): Result<List<Textbook>> {
        return try {
            Result.success(api.getTextbooks())
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

### 16.3 React Native

```typescript
import axios from 'axios';
import * as Keychain from 'react-native-keychain';

const api = axios.create({
  baseURL: 'https://api.ai-mentor.kz/api/v1',
});

// Add auth interceptor
api.interceptors.request.use(async (config) => {
  const credentials = await Keychain.getGenericPassword();
  if (credentials) {
    config.headers.Authorization = `Bearer ${credentials.password}`;
  }
  return config;
});

// API functions
export const login = async (email: string, password: string) => {
  const { data } = await api.post('/auth/login', { email, password });
  await Keychain.setGenericPassword('token', data.access_token);
  return data;
};

export const getTextbooks = async () => {
  const { data } = await api.get('/students/textbooks');
  return data;
};

export const startTest = async (testId: number) => {
  const { data } = await api.post(`/students/tests/${testId}/start`);
  return data;
};
```

### 16.4 Flutter/Dart

```dart
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AIMentorAPI {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: 'https://api.ai-mentor.kz/api/v1',
  ));
  final _storage = FlutterSecureStorage();

  AIMentorAPI() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'access_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
    ));
  }

  Future<TokenResponse> login(String email, String password) async {
    final response = await _dio.post('/auth/login', data: {
      'email': email,
      'password': password,
    });
    final token = TokenResponse.fromJson(response.data);
    await _storage.write(key: 'access_token', value: token.accessToken);
    return token;
  }

  Future<List<Textbook>> getTextbooks() async {
    final response = await _dio.get('/students/textbooks');
    return (response.data as List)
        .map((json) => Textbook.fromJson(json))
        .toList();
  }
}
```

---

## Appendix A: Data Models

### TypeScript Interfaces

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
  middle_name: string | null;
  phone: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

interface Textbook {
  id: number;
  school_id: number | null;
  title: string;
  subject: string;
  grade_level: number;
  author: string | null;
  is_active: boolean;
  created_at: string;
}

interface Chapter {
  id: number;
  textbook_id: number;
  title: string;
  number: number;
  order: number;
  description: string | null;
  created_at: string;
}

interface Paragraph {
  id: number;
  chapter_id: number;
  title: string;
  number: number;
  order: number;
  content: string;
  summary: string | null;
  key_terms: string[];
  created_at: string;
}

interface MasteryLevel {
  level: 'A' | 'B' | 'C';
  score: number;
  progress_percentage: number;
}
```

---

## Appendix B: Common Issues

### 1. Token Expired

**Problem:** 401 Unauthorized on all requests

**Solution:**
```swift
if response.statusCode == 401 {
    let newToken = try await refreshToken()
    // Retry original request with new token
}
```

### 2. Network Timeout

**Problem:** Request times out

**Solution:**
- Set appropriate timeout (30 seconds for normal, 60 for file upload)
- Implement retry logic with exponential backoff

### 3. Large Content

**Problem:** Paragraph content too large

**Solution:**
- Use pagination for lists
- Implement lazy loading for content
- Cache content locally

---

## Contact & Support

**API Issues:** api-support@ai-mentor.kz
**Documentation:** https://docs.ai-mentor.kz
**GitHub:** https://github.com/ai-mentor/mobile-sdk

---

**Document Version:** 1.0
**Last Updated:** 2026-01-05
