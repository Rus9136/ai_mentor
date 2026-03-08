# AI Chat API — Документация для мобильного приложения

Base URL: `https://api.ai-mentor.kz`

Все endpoints требуют JWT токен студента в заголовке:
```
Authorization: Bearer {access_token}
```

---

## Содержание

1. [Создать сессию](#1-создать-сессию)
2. [Список сессий](#2-список-сессий)
3. [Получить сессию с историей](#3-получить-сессию-с-историей)
4. [Отправить сообщение](#4-отправить-сообщение)
5. [Отправить сообщение (стриминг)](#5-отправить-сообщение-стриминг)
6. [Удалить сессию](#6-удалить-сессию)
7. [Типы сессий](#типы-сессий)
8. [Персонализация A/B/C](#персонализация)
9. [Обработка ошибок](#обработка-ошибок)
10. [Лимиты](#лимиты)

---

## 1. Создать сессию

```
POST /api/v1/chat/sessions
```

**Request Body:**

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `session_type` | string | да | `reading_help` / `post_paragraph` / `test_help` / `general_tutor` |
| `paragraph_id` | integer | нет | ID параграфа (для `reading_help`, `post_paragraph`) |
| `chapter_id` | integer | нет | ID главы |
| `test_id` | integer | нет | ID теста (для `test_help`) |
| `title` | string | нет | Заголовок сессии (авто-генерация если не указан) |
| `language` | string | нет | `ru` (по умолчанию) или `kk` |

**Пример запроса:**
```json
{
  "session_type": "reading_help",
  "paragraph_id": 279,
  "chapter_id": 40,
  "language": "ru"
}
```

**Ответ: `201 Created`**
```json
{
  "id": 5,
  "session_type": "reading_help",
  "paragraph_id": 279,
  "chapter_id": 40,
  "test_id": null,
  "title": "Помощь с чтением - 08.03.2026 14:30",
  "mastery_level": "B",
  "language": "ru",
  "message_count": 0,
  "total_tokens_used": 0,
  "last_message_at": null,
  "created_at": "2026-03-08T14:30:00Z"
}
```

---

## 2. Список сессий

```
GET /api/v1/chat/sessions
```

**Query Parameters:**

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `page` | integer | 1 | Номер страницы (от 1) |
| `page_size` | integer | 20 | Элементов на странице (1-100) |
| `session_type` | string | — | Фильтр по типу сессии |

**Ответ: `200 OK`**
```json
{
  "items": [
    {
      "id": 5,
      "session_type": "reading_help",
      "paragraph_id": 279,
      "chapter_id": 40,
      "test_id": null,
      "title": "Помощь с чтением - 08.03.2026 14:30",
      "mastery_level": "B",
      "language": "ru",
      "message_count": 4,
      "total_tokens_used": 3200,
      "last_message_at": "2026-03-08T15:00:00Z",
      "created_at": "2026-03-08T14:30:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

---

## 3. Получить сессию с историей

```
GET /api/v1/chat/sessions/{session_id}
```

**Ответ: `200 OK`**
```json
{
  "id": 5,
  "session_type": "reading_help",
  "paragraph_id": 279,
  "chapter_id": 40,
  "test_id": null,
  "title": "Помощь с чтением",
  "mastery_level": "B",
  "language": "ru",
  "message_count": 2,
  "total_tokens_used": 1996,
  "last_message_at": "2026-03-08T14:48:03Z",
  "created_at": "2026-03-08T14:30:00Z",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Кто такой Тауке хан?",
      "citations": null,
      "tokens_used": null,
      "model_used": null,
      "processing_time_ms": null,
      "created_at": "2026-03-08T14:48:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Тауке хан был правителем Казахского ханства...",
      "citations": [
        {
          "paragraph_id": 279,
          "paragraph_title": "Внутреннее положение Казахского ханства",
          "chapter_title": "Казахско-джунгарские войны",
          "chunk_text": "Тауке хан считается основоположником...",
          "relevance_score": 0.539
        }
      ],
      "tokens_used": 1996,
      "model_used": "llama-3.3-70b",
      "processing_time_ms": 2887,
      "created_at": "2026-03-08T14:48:03Z"
    }
  ]
}
```

**Ошибки:** `404` — сессия не найдена или принадлежит другому студенту.

---

## 4. Отправить сообщение

```
POST /api/v1/chat/sessions/{session_id}/messages
```

**Request Body:**

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `content` | string | да | Текст сообщения (1-4000 символов) |

**Пример запроса:**
```json
{
  "content": "Кто такой Тауке хан?"
}
```

**Ответ: `200 OK`**
```json
{
  "user_message": {
    "id": 10,
    "role": "user",
    "content": "Кто такой Тауке хан?",
    "citations": null,
    "tokens_used": null,
    "model_used": null,
    "processing_time_ms": null,
    "created_at": "2026-03-08T15:05:00Z"
  },
  "assistant_message": {
    "id": 11,
    "role": "assistant",
    "content": "Тауке хан был правителем Казахского ханства...",
    "citations": [
      {
        "paragraph_id": 279,
        "paragraph_title": "Внутреннее положение Казахского ханства",
        "chapter_title": "Казахско-джунгарские войны",
        "chunk_text": "Тауке хан считается основоположником...",
        "relevance_score": 0.539
      }
    ],
    "tokens_used": 1996,
    "model_used": "llama-3.3-70b",
    "processing_time_ms": 2887,
    "created_at": "2026-03-08T15:05:05Z"
  },
  "session": {
    "id": 5,
    "session_type": "reading_help",
    "paragraph_id": 279,
    "chapter_id": 40,
    "test_id": null,
    "title": "Помощь с чтением",
    "mastery_level": "B",
    "language": "ru",
    "message_count": 2,
    "total_tokens_used": 1996,
    "last_message_at": "2026-03-08T15:05:05Z",
    "created_at": "2026-03-08T14:30:00Z"
  }
}
```

> **Примечание:** Этот endpoint ждёт полный ответ от ИИ. Время ответа — 2-10 секунд. Для лучшего UX используйте стриминг (endpoint 5).

---

## 5. Отправить сообщение (стриминг)

```
POST /api/v1/chat/sessions/{session_id}/messages/stream
```

**Request Body:** аналогично endpoint 4.

**Response Headers:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Формат: Server-Sent Events (SSE)**

Каждое событие — строка `data: {json}\n\n`:

### Событие 1 — сообщение пользователя сохранено
```
data: {"type": "user_message", "message": {"id": 10, "role": "user", "content": "Кто такой Тауке хан?", "created_at": "2026-03-08T15:05:00Z"}}
```

### Событие 2..N — текст от ИИ (чанками)
```
data: {"type": "delta", "content": "Тауке хан "}
data: {"type": "delta", "content": "был правителем "}
data: {"type": "delta", "content": "Казахского ханства..."}
```

### Последнее событие — финальный результат
```
data: {"type": "done", "message": {"id": 11, "role": "assistant", "content": "Тауке хан был правителем Казахского ханства...", "tokens_used": 1996, "model_used": "llama-3.3-70b", "processing_time_ms": 2887, "created_at": "2026-03-08T15:05:05Z"}, "session": {...}, "citations": [...]}
```

### Событие ошибки (если произошла)
```
data: {"type": "error", "error": "LLM service unavailable"}
```

### Реализация на мобильных

**Kotlin (Android):**
```kotlin
val client = OkHttpClient()
val request = Request.Builder()
    .url("https://api.ai-mentor.kz/api/v1/chat/sessions/$sessionId/messages/stream")
    .post("""{"content": "$message"}""".toRequestBody("application/json".toMediaType()))
    .addHeader("Authorization", "Bearer $token")
    .build()

client.newCall(request).enqueue(object : Callback {
    override fun onResponse(call: Call, response: Response) {
        val reader = response.body?.source() ?: return
        while (!reader.exhausted()) {
            val line = reader.readUtf8Line() ?: break
            if (line.startsWith("data: ")) {
                val json = JSONObject(line.removePrefix("data: "))
                when (json.getString("type")) {
                    "delta" -> appendText(json.getString("content"))
                    "done" -> onComplete(json)
                    "error" -> onError(json.getString("error"))
                }
            }
        }
    }
})
```

**Swift (iOS):**
```swift
var request = URLRequest(url: URL(string: "https://api.ai-mentor.kz/api/v1/chat/sessions/\(sessionId)/messages/stream")!)
request.httpMethod = "POST"
request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
request.setValue("application/json", forHTTPHeaderField: "Content-Type")
request.httpBody = try? JSONEncoder().encode(["content": message])

let (bytes, _) = try await URLSession.shared.bytes(for: request)
for try await line in bytes.lines {
    guard line.hasPrefix("data: ") else { continue }
    let jsonStr = String(line.dropFirst(6))
    guard let data = jsonStr.data(using: .utf8),
          let event = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { continue }

    switch event["type"] as? String {
    case "delta":
        appendText(event["content"] as? String ?? "")
    case "done":
        onComplete(event)
    case "error":
        onError(event["error"] as? String ?? "Unknown error")
    default: break
    }
}
```

**Flutter (Dart):**
```dart
final request = http.Request('POST',
  Uri.parse('https://api.ai-mentor.kz/api/v1/chat/sessions/$sessionId/messages/stream'));
request.headers['Authorization'] = 'Bearer $token';
request.headers['Content-Type'] = 'application/json';
request.body = jsonEncode({'content': message});

final response = await http.Client().send(request);
await for (final chunk in response.stream.transform(utf8.decoder).transform(const LineSplitter())) {
  if (!chunk.startsWith('data: ')) continue;
  final event = jsonDecode(chunk.substring(6));
  switch (event['type']) {
    case 'delta':
      appendText(event['content']);
    case 'done':
      onComplete(event);
    case 'error':
      onError(event['error']);
  }
}
```

---

## 6. Удалить сессию

```
DELETE /api/v1/chat/sessions/{session_id}
```

**Ответ: `204 No Content`** (пустое тело)

Мягкое удаление — сессия помечается как удалённая.

---

## Типы сессий

| Тип | Когда использовать | Контекст |
|-----|-------------------|----------|
| `reading_help` | Кнопка "Помощь" при чтении параграфа | `paragraph_id` + `chapter_id` |
| `post_paragraph` | Кнопка "Обсудить" после прочтения | `paragraph_id` |
| `test_help` | Кнопка "Подсказка" в тесте | `test_id` |
| `general_tutor` | Кнопка "Задать вопрос" на главной | `chapter_id` (опционально) |

### Сценарии использования

```
// Ученик читает параграф → нажимает "Спросить у ИИ"
POST /api/v1/chat/sessions
{ "session_type": "reading_help", "paragraph_id": 279, "chapter_id": 40 }

// Ученик прочитал параграф → нажимает "Обсудить с ИИ"
POST /api/v1/chat/sessions
{ "session_type": "post_paragraph", "paragraph_id": 279 }

// Ученик проходит тест → нужна подсказка
POST /api/v1/chat/sessions
{ "session_type": "test_help", "test_id": 15 }

// На главном экране → "Задай любой вопрос"
POST /api/v1/chat/sessions
{ "session_type": "general_tutor" }
```

---

## Персонализация

Система автоматически определяет уровень ученика при создании сессии:

| Уровень | Критерий | Стиль ответов ИИ |
|---------|----------|-------------------|
| **A** | ≥85% правильных ответов | Краткий, сложная терминология |
| **B** | 60-84% правильных ответов | Чёткие объяснения с примерами |
| **C** | <60% правильных ответов | Простой язык, пошаговые объяснения |

Уровень сохраняется в поле `mastery_level` сессии.

---

## Схема Citation

```json
{
  "paragraph_id": 279,
  "paragraph_title": "Внутреннее положение Казахского ханства",
  "chapter_title": "Казахско-джунгарские войны",
  "chunk_text": "Тауке хан считается основоположником...",
  "relevance_score": 0.539
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `paragraph_id` | integer | ID параграфа-источника (для навигации в UI) |
| `paragraph_title` | string | Название параграфа |
| `chapter_title` | string | Название главы |
| `chunk_text` | string | Цитируемый текст |
| `relevance_score` | float | Релевантность 0.0-1.0 (выше = точнее) |

---

## Обработка ошибок

**Формат ошибки:**
```json
{
  "detail": "Chat session not found"
}
```

| Код | Описание |
|-----|----------|
| `400` | Неверный формат запроса, неверный `session_type` |
| `401` | Невалидный или отсутствующий токен |
| `403` | Нет доступа (не роль STUDENT) |
| `404` | Сессия не найдена или принадлежит другому студенту |
| `422` | Ошибка валидации (текст слишком длинный и т.д.) |
| `500` | Ошибка сервера (LLM недоступен и т.д.) |

---

## Лимиты

| Параметр | Значение |
|----------|----------|
| Максимальная длина сообщения | 4000 символов |
| История в контексте ИИ | 10 последних сообщений |
| RAG контекст | до 5 чанков |
| Время ответа (без стриминга) | 2-10 секунд |
| Время первого чанка (стриминг) | ~1 секунда |

---

## Полный Flow для мобильного приложения

```
1. Авторизация
   POST /api/v1/auth/login → получить access_token

2. Создать сессию чата
   POST /api/v1/chat/sessions
   → получить session_id

3. Отправить сообщение (рекомендуется стриминг)
   POST /api/v1/chat/sessions/{session_id}/messages/stream
   → читать SSE события, показывать текст по мере поступления

4. Продолжить диалог
   → повторять шаг 3 для каждого нового сообщения

5. Показать список предыдущих чатов
   GET /api/v1/chat/sessions?page=1&page_size=20

6. Открыть предыдущий чат
   GET /api/v1/chat/sessions/{session_id}
   → загрузить полную историю messages[]

7. Удалить чат
   DELETE /api/v1/chat/sessions/{session_id}
```
