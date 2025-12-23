# RAG Service Documentation

**Версия:** 1.0
**Дата:** 2025-12-19
**Статус:** Production Ready

## Обзор

RAG (Retrieval-Augmented Generation) сервис предоставляет персонализированные объяснения учебного материала на основе:

- **Векторного поиска** по контенту параграфов (pgvector)
- **Уровня мастерства студента** (A/B/C группировка)
- **LLM генерации** через Cerebras (llama-3.3-70b)

### Ключевые особенности

| Функция | Описание |
|---------|----------|
| Персонализация | Адаптация сложности объяснений под уровень студента |
| Цитирование | Ссылки на источники в учебнике |
| Мультиязычность | Поддержка русского (ru) и казахского (kk) языков |
| Быстрый inference | Cerebras обеспечивает ответ за 2-4 секунды |

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│  Student Request: "Объясни что такое Золотая Орда"          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  1. RAGService.explain()                                     │
│     - Get mastery_level from ChapterMastery (A/B/C)         │
│     - school_id from JWT for tenant isolation               │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  2. Jina AI Embeddings                                       │
│     - Model: jina-embeddings-v3                             │
│     - Dimensions: 1024                                       │
│     - Task: retrieval.query                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  3. pgvector Similarity Search                               │
│     - Operator: <=> (cosine distance)                       │
│     - Index: IVFFlat (lists=100)                            │
│     - TOP_K=5, MIN_SIMILARITY=0.5                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  4. Context Building + Prompt Selection                      │
│     Level A: Concise, advanced, connections                 │
│     Level B: Standard, examples, tips                       │
│     Level C: Simple, step-by-step, encouraging              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  5. Cerebras LLM Generation                                  │
│     - Model: llama-3.3-70b                                  │
│     - API: https://api.cerebras.ai/v1                       │
│     - Temperature: 0.7, Max tokens: 1500                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  6. ExplanationResponse                                      │
│     - answer: "Золотая Орда — государство..."               │
│     - citations: [{paragraph_id, quote, relevance}]         │
│     - mastery_level: "B"                                    │
│     - tokens_used: 1431                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### Student Endpoints

#### POST /api/v1/rag/explain

Объяснить вопрос или концепцию.

**Request:**
```json
{
  "question_text": "Кто такой Тауке хан?",
  "paragraph_id": null,
  "chapter_id": null,
  "language": "ru"
}
```

**Response:**
```json
{
  "answer": "Тауке хан — значимая фигура в истории Казахского ханства...",
  "citations": [
    {
      "paragraph_id": 279,
      "paragraph_title": "Внутреннее и внешнее политическое положение...",
      "chapter_title": "Казахско-джунгарские войны",
      "chunk_text": "Тауке хан считается основоположником...",
      "relevance_score": 0.539
    }
  ],
  "mastery_level": "B",
  "model_used": "llama-3.3-70b",
  "tokens_used": 1431,
  "processing_time_ms": 3287
}
```

**Параметры запроса:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| question_text | string | Да | Вопрос (1-2000 символов) |
| paragraph_id | int | Нет | ID параграфа для контекста |
| chapter_id | int | Нет | ID главы для фильтрации поиска |
| language | string | Нет | Язык ответа: "ru" или "kk" (по умолчанию "ru") |

---

#### POST /api/v1/rag/paragraphs/{paragraph_id}/explain

Объяснить содержание параграфа.

**Request:**
```json
{
  "user_question": "Что означает Жеты жаргы?",
  "language": "ru"
}
```

**Response:** Аналогичен `/explain`

---

### Admin Endpoints (SUPER_ADMIN only)

#### POST /api/v1/rag/admin/global/paragraphs/{paragraph_id}/embeddings

Сгенерировать embeddings для параграфа.

**Request:**
```json
{
  "force": false
}
```

**Response:**
```json
{
  "paragraph_id": 279,
  "chunks_created": 8,
  "model": "jina-embeddings-v3",
  "total_tokens": 1500,
  "processing_time_ms": 2120
}
```

---

#### GET /api/v1/rag/admin/global/paragraphs/{paragraph_id}/embeddings

Получить статус embeddings параграфа.

**Response:**
```json
{
  "paragraph_id": 279,
  "paragraph_title": "Внутреннее и внешнее политическое положение...",
  "chunks_count": 8,
  "model": "jina-embeddings-v3",
  "created_at": "2025-12-19T10:40:33.887087Z",
  "updated_at": "2025-12-19T10:40:33.887087Z",
  "chunks": [
    {
      "id": 2,
      "paragraph_id": 279,
      "chunk_index": 0,
      "chunk_text": "# Внутреннее и внешнее политическое положение...",
      "model": "jina-embeddings-v3"
    }
  ]
}
```

---

#### DELETE /api/v1/rag/admin/global/paragraphs/{paragraph_id}/embeddings

Удалить embeddings параграфа (hard delete).

**Response:**
```json
{
  "deleted_count": 8
}
```

---

#### POST /api/v1/rag/admin/global/textbooks/{textbook_id}/embeddings

Batch генерация embeddings для всех параграфов учебника.

**Request:**
```json
{
  "force": false
}
```

**Response:**
```json
{
  "textbook_id": 11,
  "textbook_title": "История Казахстана 7 класс",
  "total_paragraphs": 45,
  "processed_paragraphs": 45,
  "skipped_paragraphs": 0,
  "total_chunks_created": 320,
  "total_tokens": 48000,
  "processing_time_ms": 95000,
  "errors": []
}
```

---

## Конфигурация

### Environment Variables

```bash
# Jina AI Embeddings (бесплатно 1M токенов/месяц)
JINA_API_KEY=jina_xxx
JINA_EMBEDDING_MODEL=jina-embeddings-v3
EMBEDDING_PROVIDER=jina
EMBEDDING_DIMENSIONS=1024

# Cerebras LLM (бесплатный API с лимитами)
OPENROUTER_API_KEY=csk-xxx  # Cerebras API key
LLM_PROVIDER=cerebras
CEREBRAS_MODEL=llama-3.3-70b

# RAG Settings
RAG_TOP_K=5                    # Количество чанков для контекста
RAG_SIMILARITY_THRESHOLD=0.7   # Минимальный порог релевантности
CHUNK_SIZE=1000                # Размер чанка в символах
CHUNK_OVERLAP=200              # Перекрытие между чанками
```

### Получение API ключей

#### Jina AI
1. Перейти на https://jina.ai/
2. Зарегистрироваться
3. API Keys → Create New Key
4. Бесплатно: 1M токенов/месяц

#### Cerebras
1. Перейти на https://cloud.cerebras.ai/
2. Зарегистрироваться
3. API Keys → Create New Key
4. Бесплатный tier с rate limits

---

## Персонализация A/B/C

### Уровни мастерства

| Уровень | Критерии | Стиль объяснения |
|---------|----------|------------------|
| **A** | ≥85% правильных ответов, стабильные результаты | Краткий, продвинутый, глубокие связи |
| **B** | 60-84% правильных ответов | Сбалансированный, примеры, практические советы |
| **C** | <60% или нестабильные результаты | Простой язык, пошаговый, подбадривающий |

### Промпты по уровням

**Level A:**
```
Ты — продвинутый репетитор для сильных учеников.
- Будь кратким и интеллектуально стимулирующим
- Используй сложную терминологию
- Давай глубокие инсайты и связи с другими темами
- Пропускай базовые объяснения
```

**Level B:**
```
Ты — поддерживающий репетитор для учеников со средним уровнем.
- Давай чёткие, структурированные объяснения
- Включай примеры для иллюстрации
- Выделяй ключевые моменты для запоминания
```

**Level C:**
```
Ты — терпеливый, подбадривающий репетитор.
- Используй простой, повседневный язык
- Разбивай на маленькие, понятные шаги
- Приводи несколько примеров
- Будь подбадривающим
```

### Алгоритм определения уровня

```python
# 1. Проверяем mastery по конкретной главе
mastery = await mastery_repo.get_by_student_chapter(student_id, chapter_id)
if mastery:
    return mastery.mastery_level  # A, B, or C

# 2. Если нет - считаем средний по всем главам
masteries = await mastery_repo.get_by_student(student_id)
if masteries:
    avg_score = mean([m.mastery_score for m in masteries])
    if avg_score >= 85: return 'A'
    elif avg_score >= 60: return 'B'
    else: return 'C'

# 3. По умолчанию - уровень B
return 'B'
```

---

## Embeddings Pipeline

### Chunking Strategy

```python
# Параметры
CHUNK_SIZE = 1000      # символов
CHUNK_OVERLAP = 200    # перекрытие

# Пример
paragraph_content = "Длинный текст параграфа..."  # 3500 символов

# Результат: 4 чанка
# Chunk 0: [0:1000]
# Chunk 1: [800:1800]
# Chunk 2: [1600:2600]
# Chunk 3: [2400:3500]
```

### Jina AI Request

```python
{
    "model": "jina-embeddings-v3",
    "task": "retrieval.passage",  # или "retrieval.query" для запросов
    "dimensions": 1024,
    "input": ["Текст чанка 1", "Текст чанка 2"],
    "late_chunking": false
}
```

### Vector Search Query

```sql
SELECT
    pe.id,
    pe.chunk_text,
    (1 - (pe.embedding <=> '{query_vector}'::vector)) AS similarity
FROM paragraph_embeddings pe
JOIN paragraphs p ON pe.paragraph_id = p.id
WHERE pe.is_deleted = false
AND (1 - (pe.embedding <=> '{query_vector}'::vector)) >= 0.5
ORDER BY similarity DESC
LIMIT 5;
```

---

## Database Schema

### paragraph_embeddings

```sql
CREATE TABLE paragraph_embeddings (
    id SERIAL PRIMARY KEY,
    paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id),
    chunk_index INTEGER NOT NULL DEFAULT 0,
    chunk_text TEXT NOT NULL,
    embedding vector(1024) NOT NULL,  -- Jina: 1024 dims
    model VARCHAR(100) DEFAULT 'jina-embeddings-v3',
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- IVFFlat index для быстрого поиска
CREATE INDEX ix_paragraph_embeddings_embedding_ivfflat
ON paragraph_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## Примеры использования

### cURL: Объяснить вопрос

```bash
curl -X POST "https://api.ai-mentor.kz/api/v1/rag/explain" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "Что такое Жеты жаргы?",
    "language": "ru"
  }'
```

### cURL: Сгенерировать embeddings

```bash
# Для одного параграфа
curl -X POST "https://api.ai-mentor.kz/api/v1/rag/admin/global/paragraphs/279/embeddings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false}'

# Для всего учебника
curl -X POST "https://api.ai-mentor.kz/api/v1/rag/admin/global/textbooks/11/embeddings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

### Python SDK (пример)

```python
import httpx

async def ask_rag(question: str, token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.ai-mentor.kz/api/v1/rag/explain",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "question_text": question,
                "language": "ru"
            }
        )
        return response.json()

# Использование
result = await ask_rag("Кто такой Тауке хан?", student_token)
print(result["answer"])
print(f"Источники: {[c['paragraph_title'] for c in result['citations']]}")
```

---

## Стоимость и лимиты

### Jina AI (Embeddings)

| Tier | Токены/месяц | Стоимость |
|------|--------------|-----------|
| Free | 1,000,000 | $0 |
| Paid | Unlimited | $0.02/1M tokens |

### Cerebras (LLM)

| Tier | Requests/min | Стоимость |
|------|--------------|-----------|
| Free | 30 | $0 |
| Paid | Unlimited | ~$0.01/1M input tokens |

### Примерный расход на 1000 вопросов

```
Embeddings (query): 1000 * 50 tokens = 50K tokens
LLM (input):        1000 * 2000 tokens = 2M tokens
LLM (output):       1000 * 500 tokens = 500K tokens

Итого: ~$0 (в рамках free tier)
```

---

## Troubleshooting

### Ошибка: "No similar chunks found"

**Причина:** Embeddings не сгенерированы для параграфов.

**Решение:**
```bash
# Сгенерировать для учебника
curl -X POST ".../admin/global/textbooks/{id}/embeddings" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"force": false}'
```

### Ошибка: "JINA_API_KEY is not configured"

**Причина:** Отсутствует API ключ Jina.

**Решение:**
1. Получить ключ на https://jina.ai/
2. Добавить в `.env`: `JINA_API_KEY=jina_xxx`
3. Перезапустить backend

### Ошибка: "Cerebras API error: 429"

**Причина:** Превышен rate limit.

**Решение:**
- Подождать 1 минуту
- Или перейти на платный tier

### Низкая релевантность ответов

**Причины:**
1. Мало embeddings сгенерировано
2. Низкий порог similarity

**Решение:**
1. Сгенерировать embeddings для всех параграфов
2. Уменьшить `RAG_SIMILARITY_THRESHOLD` до 0.3-0.4

---

## Файловая структура

```
backend/app/
├── api/v1/
│   └── rag.py                    # API endpoints
├── services/
│   ├── rag_service.py            # RAG orchestration
│   ├── embedding_service.py      # Jina/OpenAI embeddings
│   └── llm_service.py            # Cerebras/OpenRouter LLM
├── repositories/
│   └── embedding_repo.py         # Vector search queries
├── schemas/
│   └── rag.py                    # Pydantic models
└── models/
    └── paragraph.py              # ParagraphEmbedding model
```

---

## Roadmap

- [ ] Кэширование частых запросов (Redis)
- [ ] Streaming responses для длинных ответов
- [ ] Автоматическая генерация embeddings при создании параграфа
- [ ] Поддержка изображений в контексте
- [ ] A/B тестирование промптов
- [ ] Analytics: топ вопросов, качество ответов
