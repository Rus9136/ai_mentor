# Chat Service - RAG-based Conversations

Multi-turn чат с ИИ для студентов с поддержкой RAG контекста из учебника и A/B/C персонализацией.

## Оглавление

- [Обзор](#обзор)
- [API Endpoints](#api-endpoints)
- [Типы сессий](#типы-сессий)
- [Персонализация A/B/C](#персонализация-abc)
- [Системные промпты](#системные-промпты)
- [Примеры использования](#примеры-использования)
- [Архитектура](#архитектура)
- [База данных](#база-данных)

---

## Обзор

Chat Service предоставляет:

- **Multi-turn диалоги** - история сохраняется в PostgreSQL
- **RAG контекст** - автоматический поиск релевантных параграфов из учебника
- **A/B/C персонализация** - адаптация ответов под уровень мастерства ученика
- **Редактируемые промпты** - админ может менять системные инструкции
- **Цитаты** - AI ссылается на конкретные параграфы учебника
- **Multi-tenant изоляция** - RLS политики по school_id

**Стек:**
- LLM: Cerebras (llama-3.3-70b)
- Embeddings: Jina AI (jina-embeddings-v3)
- Vector Search: pgvector (IVFFlat)
- Database: PostgreSQL с RLS

---

## API Endpoints

### Student Endpoints

Все endpoints требуют JWT токен студента.

#### Создать сессию

```http
POST /api/v1/chat/sessions
Authorization: Bearer <student_token>
Content-Type: application/json

{
  "session_type": "reading_help",
  "chapter_id": 40,
  "paragraph_id": null,
  "test_id": null,
  "title": "Вопросы по главе",
  "language": "ru"
}
```

**Response:**
```json
{
  "id": 5,
  "session_type": "reading_help",
  "chapter_id": 40,
  "paragraph_id": null,
  "test_id": null,
  "title": "Помощь с чтением - 22.12.2025 14:47",
  "mastery_level": "B",
  "language": "ru",
  "message_count": 0,
  "total_tokens_used": 0,
  "last_message_at": null,
  "created_at": "2025-12-22T14:47:47.106637Z"
}
```

#### Список сессий

```http
GET /api/v1/chat/sessions?page=1&page_size=20&session_type=reading_help
Authorization: Bearer <student_token>
```

**Response:**
```json
{
  "items": [...],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

#### Получить сессию с историей

```http
GET /api/v1/chat/sessions/{session_id}
Authorization: Bearer <student_token>
```

**Response:**
```json
{
  "id": 5,
  "session_type": "reading_help",
  "chapter_id": 40,
  "mastery_level": "B",
  "message_count": 2,
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Кто такой Тауке хан?",
      "citations": null,
      "created_at": "2025-12-22T14:48:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Тауке хан был правителем...",
      "citations": [
        {
          "paragraph_id": 279,
          "paragraph_title": "Внутреннее положение...",
          "chapter_title": "Казахско-джунгарские войны",
          "chunk_text": "...",
          "relevance_score": 0.539
        }
      ],
      "tokens_used": 1996,
      "model_used": "llama-3.3-70b",
      "processing_time_ms": 2887,
      "created_at": "2025-12-22T14:48:03Z"
    }
  ]
}
```

#### Отправить сообщение

```http
POST /api/v1/chat/sessions/{session_id}/messages
Authorization: Bearer <student_token>
Content-Type: application/json

{
  "content": "Кто такой Тауке хан?"
}
```

**Response:**
```json
{
  "user_message": {
    "id": 1,
    "role": "user",
    "content": "Кто такой Тауке хан?",
    "citations": null,
    "tokens_used": null,
    "created_at": "2025-12-22T14:48:00Z"
  },
  "assistant_message": {
    "id": 2,
    "role": "assistant",
    "content": "Тауке хан был правителем Казахского ханства...",
    "citations": [
      {
        "paragraph_id": 279,
        "paragraph_title": "Внутреннее и внешнее политическое положение...",
        "chapter_title": "Казахско-джунгарские войны",
        "chunk_text": "Тауке хан считается основоположником...",
        "relevance_score": 0.539
      }
    ],
    "tokens_used": 1996,
    "model_used": "llama-3.3-70b",
    "processing_time_ms": 2887,
    "created_at": "2025-12-22T14:48:03Z"
  },
  "session": {
    "id": 5,
    "message_count": 2,
    "total_tokens_used": 1996,
    "last_message_at": "2025-12-22T14:48:03Z"
  }
}
```

#### Удалить сессию

```http
DELETE /api/v1/chat/sessions/{session_id}
Authorization: Bearer <student_token>
```

**Response:** `204 No Content`

---

### Admin Endpoints (SUPER_ADMIN)

#### Список промптов

```http
GET /api/v1/chat/admin/prompts?prompt_type=reading_help&mastery_level=B
Authorization: Bearer <super_admin_token>
```

#### Создать промпт

```http
POST /api/v1/chat/admin/prompts
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "prompt_type": "reading_help",
  "mastery_level": "A",
  "language": "ru",
  "name": "Помощь при чтении - Уровень A",
  "description": "Промпт для продвинутых учеников",
  "prompt_text": "Ты — продвинутый репетитор...",
  "is_active": true
}
```

#### Обновить промпт

```http
PUT /api/v1/chat/admin/prompts/{prompt_id}
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "prompt_text": "Обновлённый текст промпта...",
  "is_active": true
}
```

#### Удалить промпт

```http
DELETE /api/v1/chat/admin/prompts/{prompt_id}
Authorization: Bearer <super_admin_token>
```

---

## Типы сессий

| Тип | Описание | Обязательный контекст |
|-----|----------|----------------------|
| `reading_help` | Помощь при чтении параграфа | `paragraph_id` или `chapter_id` |
| `post_paragraph` | Обсуждение после прочтения | `paragraph_id` |
| `test_help` | Помощь с тестом | `test_id` |
| `general_tutor` | Общие вопросы | `chapter_id` (опционально) |

**Пример использования типов:**

```javascript
// При чтении параграфа - кнопка "Помощь"
createSession({
  session_type: "reading_help",
  paragraph_id: 279,
  chapter_id: 40
});

// После прочтения параграфа - кнопка "Обсудить"
createSession({
  session_type: "post_paragraph",
  paragraph_id: 279
});

// В тесте - кнопка "Подсказка"
createSession({
  session_type: "test_help",
  test_id: 15
});

// На главной странице - кнопка "Задать вопрос"
createSession({
  session_type: "general_tutor",
  chapter_id: 40  // опционально
});
```

---

## Персонализация A/B/C

Система автоматически определяет уровень мастерства ученика и адаптирует:
- Сложность языка
- Глубину объяснений
- Количество примеров

### Уровни мастерства

| Уровень | Критерий | Стиль ответа |
|---------|----------|--------------|
| **A** | ≥85% правильных ответов | Краткий, сложная терминология, углублённые концепции |
| **B** | 60-84% правильных ответов | Чёткие объяснения с примерами |
| **C** | <60% правильных ответов | Простой язык, много примеров, пошаговые объяснения |

### Как определяется уровень

1. При создании сессии вызывается `RAGService.get_student_mastery_level()`
2. Берутся последние 5 попыток тестов по главе
3. Рассчитывается взвешенный средний балл
4. Уровень сохраняется в сессии (`mastery_level`)

---

## Системные промпты

### Предустановленные промпты

Миграция создаёт 12 базовых промптов (4 типа × 3 уровня):

| prompt_type | mastery_level | language | name |
|-------------|---------------|----------|------|
| reading_help | A | ru | Помощь при чтении - Уровень A |
| reading_help | B | ru | Помощь при чтении - Уровень B |
| reading_help | C | ru | Помощь при чтении - Уровень C |
| post_paragraph | A | ru | Обсуждение после параграфа - Уровень A |
| ... | ... | ... | ... |

### Структура промпта

```
Ты — репетитор для ученика уровня {level}.
{Описание стиля ответов}
Язык: {language}.
{Дополнительные инструкции}
```

### Fallback промпты

Если в БД нет подходящего промпта, используются fallback из кода:

```python
DEFAULT_PROMPTS = {
    ("reading_help", "A", "ru"): "Ты — продвинутый репетитор...",
    ("reading_help", "B", "ru"): "Ты — репетитор...",
    ("general_tutor", "B", "ru"): "Ты — репетитор для ученика..."
}
```

---

## Примеры использования

### Frontend (React)

```typescript
// hooks/useChat.ts
import { useMutation, useQuery } from '@tanstack/react-query';
import { chatApi } from '@/lib/api/chat';

export function useCreateSession() {
  return useMutation({
    mutationFn: (data: CreateSessionRequest) =>
      chatApi.createSession(data)
  });
}

export function useSendMessage(sessionId: number) {
  return useMutation({
    mutationFn: (content: string) =>
      chatApi.sendMessage(sessionId, { content })
  });
}

export function useSessionHistory(sessionId: number) {
  return useQuery({
    queryKey: ['chat', 'session', sessionId],
    queryFn: () => chatApi.getSession(sessionId)
  });
}
```

```tsx
// components/ChatWindow.tsx
function ChatWindow({ sessionId }: { sessionId: number }) {
  const { data: session } = useSessionHistory(sessionId);
  const sendMessage = useSendMessage(sessionId);
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;

    await sendMessage.mutateAsync(input);
    setInput('');
  };

  return (
    <div className="chat-window">
      <div className="messages">
        {session?.messages.map(msg => (
          <Message key={msg.id} message={msg} />
        ))}
      </div>

      <div className="input-area">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Задайте вопрос..."
        />
        <button
          onClick={handleSend}
          disabled={sendMessage.isPending}
        >
          {sendMessage.isPending ? 'Отправка...' : 'Отправить'}
        </button>
      </div>
    </div>
  );
}
```

### cURL

```bash
# 1. Получить токен студента
TOKEN=$(curl -s -X POST "https://api.ai-mentor.kz/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "student@school.com", "password": "password"}' \
  | jq -r '.access_token')

# 2. Создать сессию
SESSION=$(curl -s -X POST "https://api.ai-mentor.kz/api/v1/chat/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_type": "reading_help", "chapter_id": 40}' \
  | jq -r '.id')

echo "Session ID: $SESSION"

# 3. Отправить сообщение
curl -s -X POST "https://api.ai-mentor.kz/api/v1/chat/sessions/$SESSION/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Кто такой Тауке хан?"}' | jq .
```

---

## Архитектура

### Flow отправки сообщения

```
POST /chat/sessions/{id}/messages
         │
         ▼
┌─────────────────────────────────┐
│ 1. Загрузить сессию с историей  │
│    (ChatSession + messages)     │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 2. Сохранить user message       │
│    (ChatMessage role=user)      │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 3. Построить messages для LLM:  │
│    - System prompt (из БД)      │
│    - История (last 10 msgs)     │
│    - Текущий вопрос             │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 4. RAG: найти контекст          │
│    → Jina embedding             │
│    → pgvector cosine search     │
│    → top 5 chunks               │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 5. Добавить контекст к вопросу  │
│    "Контекст из учебника:..."   │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 6. LLM генерация (Cerebras)     │
│    llama-3.3-70b                │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 7. Сохранить assistant message  │
│    + citations, tokens, time    │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 8. Обновить статистику сессии   │
│    message_count, tokens        │
└─────────────────────────────────┘
         │
         ▼
      Response
```

### Компоненты

```
┌─────────────────────────────────────────────────────┐
│                   API Layer                          │
│  backend/app/api/v1/chat.py                         │
│  - POST /sessions                                    │
│  - GET /sessions                                     │
│  - POST /sessions/{id}/messages                      │
│  - Admin endpoints                                   │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                   ChatService                        │
│  backend/app/services/chat_service.py               │
│  - Session CRUD                                      │
│  - Message handling                                  │
│  - Prompt management                                 │
└─────────────────────────────────────────────────────┘
            │                   │
            ▼                   ▼
┌───────────────────┐  ┌───────────────────┐
│    RAGService     │  │    LLMService     │
│  - Embeddings     │  │  - Cerebras API   │
│  - Vector search  │  │  - llama-3.3-70b  │
│  - Citations      │  │                   │
└───────────────────┘  └───────────────────┘
            │
            ▼
┌───────────────────────────────────────────┐
│           EmbeddingRepository             │
│  - pgvector cosine similarity             │
│  - IVFFlat index (lists=100)              │
└───────────────────────────────────────────┘
```

---

## База данных

### Таблицы

#### chat_sessions

```sql
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    school_id INTEGER NOT NULL REFERENCES schools(id),
    session_type VARCHAR(30) NOT NULL DEFAULT 'general_tutor',
    paragraph_id INTEGER REFERENCES paragraphs(id),
    chapter_id INTEGER REFERENCES chapters(id),
    test_id INTEGER REFERENCES tests(id),
    title VARCHAR(255),
    mastery_level VARCHAR(1),  -- A, B, or C
    language VARCHAR(5) DEFAULT 'ru',
    last_message_at TIMESTAMPTZ,
    message_count INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX ix_chat_sessions_student_id ON chat_sessions(student_id);
CREATE INDEX ix_chat_sessions_school_id ON chat_sessions(school_id);
CREATE INDEX ix_chat_sessions_session_type ON chat_sessions(session_type);

-- RLS
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY chat_sessions_tenant_policy ON chat_sessions
    FOR ALL USING (
        current_setting('app.is_super_admin', true) = 'true'
        OR current_setting('app.current_tenant_id', true)::integer = school_id
    );
```

#### chat_messages

```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    school_id INTEGER NOT NULL REFERENCES schools(id),
    role VARCHAR(20) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    citations_json TEXT,        -- JSON array of citations
    context_chunks_used INTEGER,
    tokens_used INTEGER,
    model_used VARCHAR(100),
    processing_time_ms INTEGER,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX ix_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX ix_chat_messages_school_id ON chat_messages(school_id);

-- RLS
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY chat_messages_tenant_policy ON chat_messages
    FOR ALL USING (
        current_setting('app.is_super_admin', true) = 'true'
        OR current_setting('app.current_tenant_id', true)::integer = school_id
    );
```

#### system_prompt_templates

```sql
CREATE TABLE system_prompt_templates (
    id SERIAL PRIMARY KEY,
    prompt_type VARCHAR(30) NOT NULL,   -- reading_help, post_paragraph, test_help, general_tutor
    mastery_level VARCHAR(1) NOT NULL,  -- A, B, C
    language VARCHAR(5) DEFAULT 'ru',
    name VARCHAR(255) NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Unique constraint for active prompts
CREATE UNIQUE INDEX uq_system_prompts_active
ON system_prompt_templates(prompt_type, mastery_level, language)
WHERE is_active = true;
```

### Миграция

```bash
# Применить миграцию
cd backend && alembic upgrade head

# Откатить
cd backend && alembic downgrade -1
```

---

## Конфигурация

### Environment Variables

```bash
# LLM (Cerebras)
CEREBRAS_API_KEY=your_api_key
CEREBRAS_MODEL=llama-3.3-70b

# Embeddings (Jina AI)
JINA_API_KEY=your_api_key

# RAG Settings
RAG_SIMILARITY_THRESHOLD=0.4
RAG_MAX_CHUNKS=5
```

### Лимиты

| Параметр | Значение |
|----------|----------|
| Max message length | 4000 символов |
| History in context | 10 последних сообщений |
| Max tokens per response | 1500 |
| RAG chunks | 5 |
| Similarity threshold | 0.4 |

---

## Мониторинг

### Метрики в ответе

Каждый ответ AI содержит:
- `tokens_used` - потреблённые токены
- `model_used` - использованная модель
- `processing_time_ms` - время обработки
- `context_chunks_used` - количество RAG чанков

### Агрегированные метрики сессии

- `message_count` - общее количество сообщений
- `total_tokens_used` - суммарное потребление токенов
- `last_message_at` - время последнего сообщения

### Логирование

```python
logger.info(
    f"Chat response: session={session_id}, tokens={tokens}, "
    f"chunks={chunks}, time={time}ms"
)
```

---

## Troubleshooting

### RLS ошибки

```
InsufficientPrivilegeError: new row violates row-level security policy
```

**Решение:** Проверить что `app.current_tenant_id` установлен в сессии БД.

### Пустой RAG контекст

```
citations: []
```

**Причины:**
1. Нет embeddings для параграфов главы
2. Similarity threshold слишком высокий
3. Вопрос не связан с контентом учебника

**Решение:**
```bash
# Проверить embeddings
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db \
  -c "SELECT COUNT(*) FROM paragraph_embeddings WHERE chapter_id = 40;"

# Сгенерировать embeddings
POST /api/v1/rag/generate-embeddings
{"textbook_id": 11}
```

### Медленные ответы

**Причины:**
1. Большая история (>10 сообщений)
2. Много RAG чанков
3. Медленный LLM API

**Метрики для диагностики:**
- `processing_time_ms` > 5000 - проблема
- `tokens_used` > 3000 - большой контекст

---

## Changelog

### v1.0.0 (2025-12-22)

- Initial release
- Session CRUD
- RAG-based responses with citations
- A/B/C personalization
- Admin prompt management
- RLS multi-tenant isolation
