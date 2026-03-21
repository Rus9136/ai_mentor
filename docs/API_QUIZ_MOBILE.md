# Quiz Battle — Интеграция для мобильного приложения

Документ для мобильного разработчика. Квиз-баттл работает через **WebView** — все экраны игры (лобби, вопросы, таймер, результаты) реализованы на веб-фронтенде. Мобильное приложение реализует только **нативный виджет "Мои квизы"** на главном экране и открывает WebView для самой игры.

**Base URL:** `https://api.ai-mentor.kz/api/v1`
**WebView URL:** `https://ai-mentor.kz/{locale}/webview/quiz`
**Авторизация:** JWT токен в `Authorization: Bearer <token>` (роль STUDENT)

---

## Содержание

1. [Архитектура](#1-архитектура)
2. [Виджет "Мои квизы" (нативный)](#2-виджет-мои-квизы)
3. [Открытие WebView](#3-открытие-webview)
4. [Ввод кода вручную](#4-ввод-кода-вручную)
5. [Обработка ошибок](#5-обработка-ошибок)
6. [Чеклист](#6-чеклист)

---

## 1. Архитектура

```
┌──────────────────────────────────────────────────┐
│                МОБИЛЬНОЕ ПРИЛОЖЕНИЕ               │
│                                                   │
│  ┌─────────────────────────────────────────────┐  │
│  │  Главный экран (нативный)                   │  │
│  │                                             │  │
│  │  ┌───────────────────────────────────────┐  │  │
│  │  │  Виджет "Мои квизы"                  │  │  │
│  │  │  GET /students/quiz-sessions/my-quizzes│  │  │
│  │  │                                       │  │  │
│  │  │  [Алгебра — §5]  ● Доступен  [Войти] │  │  │
│  │  │  [Тарих — Тест]  ● В процессе  ████  │  │  │
│  │  │  [Информатика]   ○ Завершён  #3 +85XP│  │  │
│  │  └───────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────┘  │
│                        │                          │
│                  нажатие на квиз                   │
│                        ▼                          │
│  ┌─────────────────────────────────────────────┐  │
│  │  WebView (полноэкранный)                    │  │
│  │  URL: ai-mentor.kz/ru/webview/quiz          │  │
│  │       ?token={jwt}&code={join_code}         │  │
│  │                                             │  │
│  │  ┌───────────────────────────────────────┐  │  │
│  │  │  Все экраны квиза (веб-фронтенд):    │  │  │
│  │  │  • Ввод кода / авто-join             │  │  │
│  │  │  • Лобби (ожидание старта)           │  │  │
│  │  │  • Вопросы + таймер                  │  │  │
│  │  │  • Результаты + лидерборд            │  │  │
│  │  │  • Подиум + XP                       │  │  │
│  │  └───────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

**Что делает мобильное приложение:**
1. Показывает нативный виджет "Мои квизы" (REST API)
2. Открывает WebView с URL и передаёт JWT токен
3. Всё остальное — веб-фронтенд

**Что НЕ нужно делать мобильному:**
- WebSocket подключение — делает веб-фронтенд
- Экраны вопросов/ответов/таймера — делает веб-фронтенд
- State machine — делает веб-фронтенд
- Звуки — делает веб-фронтенд (Web Audio API)

---

## 2. Виджет "Мои квизы"

Нативный виджет на главном экране. Показывает квизы для класса(ов) ученика.

### `GET /students/quiz-sessions/my-quizzes`

**Заголовки:**
```
Authorization: Bearer {access_token}
```

**Ответ:** `200 OK`
```json
[
  {
    "id": 42,
    "test_title": "Алгебра — §5 Квадрат теңдеу",
    "class_name": "7А",
    "join_code": "X4K9P2",
    "status": "lobby",
    "mode": "classic",
    "question_count": 10,
    "participant_count": 5,
    "has_joined": false,
    "answered_count": 0,
    "total_score": null,
    "correct_answers": null,
    "rank": null,
    "xp_earned": null,
    "created_at": "2026-03-15T10:30:00Z"
  },
  {
    "id": 38,
    "test_title": "Тарих — Тест 3",
    "class_name": "7А",
    "join_code": "M7N2Q5",
    "status": "in_progress",
    "mode": "self_paced",
    "question_count": 15,
    "participant_count": 12,
    "has_joined": true,
    "answered_count": 7,
    "total_score": 5200,
    "correct_answers": 6,
    "rank": null,
    "xp_earned": null,
    "created_at": "2026-03-14T14:00:00Z"
  },
  {
    "id": 35,
    "test_title": "Информатика — Итоговый",
    "class_name": "7А",
    "join_code": "P3R8W1",
    "status": "finished",
    "mode": "team",
    "question_count": 20,
    "participant_count": 24,
    "has_joined": true,
    "answered_count": 20,
    "total_score": 14500,
    "correct_answers": 16,
    "rank": 3,
    "xp_earned": 85,
    "created_at": "2026-03-13T09:00:00Z"
  }
]
```

### Поля ответа

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | int | ID сессии квиза |
| `test_title` | string | Название теста |
| `class_name` | string | Название класса (7А, 8Б, ...) |
| `join_code` | string | 6-значный код для входа |
| `status` | string | `"lobby"` / `"in_progress"` / `"finished"` |
| `mode` | string | `"classic"` / `"team"` / `"self_paced"` / `"quick_question"` |
| `question_count` | int | Всего вопросов |
| `participant_count` | int | Количество участников |
| `has_joined` | bool | Ученик уже присоединился |
| `answered_count` | int | Сколько вопросов ответил (для self-paced прогресса) |
| `total_score` | int? | Общий счёт (null если не участвует) |
| `correct_answers` | int? | Правильных ответов |
| `rank` | int? | Место (только для finished) |
| `xp_earned` | int? | Заработано XP (только для finished) |
| `created_at` | string | ISO дата создания |

### Логика отображения виджета

**Когда показывать:** только если список не пустой. Если пустой — виджет скрыт.

**Polling:** обновлять каждые **60 секунд**.

**Для каждого элемента:**

| status | Бейдж | Доп. инфо | Кнопка | Действие |
|--------|-------|-----------|--------|----------|
| `lobby` | Зелёный "Доступен" (с пульсирующей точкой) | Участников: {participant_count} | "Войти" | Открыть WebView с `code` |
| `in_progress` + `self_paced` + `has_joined` | Синий "В процессе" | Прогресс-бар {answered_count}/{question_count} | "Продолжить" | Открыть WebView с `code` |
| `in_progress` + `self_paced` + `!has_joined` | Синий "В процессе" | Участников: {participant_count} | "Войти" | Открыть WebView с `code` |
| `in_progress` + другой mode | Синий "В процессе" | Участников: {participant_count} | "Войти" | Открыть WebView с `code` |
| `finished` + `has_joined` | Серый "Завершён" | Место #{rank}, +{xp_earned} XP, {correct_answers}/{question_count} | — | Опционально: WebView для результатов |
| `finished` + `!has_joined` | Серый "Завершён" | — | — | Нет действия |

**Иконки по mode:**
- `classic` — молния (Zap)
- `team` — группа (Users)
- `self_paced` — часы (Clock)

**Особенности:**
- `quick_question` квизы **не** попадают в этот список (они эфемерные)
- Finished квизы старше **7 дней** автоматически не возвращаются API
- Сортировка сервером: `in_progress` → `lobby` → `finished`, внутри по дате

---

## 3. Открытие WebView

При нажатии на квиз из виджета — открыть **полноэкранный WebView**.

### URL формат

```
https://ai-mentor.kz/{locale}/webview/quiz?token={access_token}&code={join_code}
```

**Параметры:**

| Параметр | Обязательный | Описание |
|----------|-------------|----------|
| `token` | Да | JWT access_token студента |
| `code` | Нет | 6-значный код квиза (если передан — авто-join) |
| `{locale}` | Да | Язык: `ru` или `kk` |

### Примеры

**С кодом (из виджета "Мои квизы"):**
```
https://ai-mentor.kz/ru/webview/quiz?token=eyJhbG...&code=X4K9P2
```
Веб-фронтенд автоматически вызовет join и перейдёт в лобби.

**Без кода (ручной ввод):**
```
https://ai-mentor.kz/ru/webview/quiz?token=eyJhbG...
```
Веб-фронтенд покажет экран ввода 6-значного кода.

### Как работает авторизация в WebView

1. Мобилка открывает URL с `?token=...`
2. WebView layout (`/webview/layout.tsx`) извлекает token из URL
3. Сохраняет в `localStorage.setItem('ai_mentor_access_token', token)`
4. Все дальнейшие API запросы и WebSocket подключения используют этот токен
5. **Мобилке больше ничего делать не нужно**

### Настройки WebView

```
// iOS (WKWebView)
webView.configuration.preferences.javaScriptEnabled = true
webView.configuration.websiteDataStore = .default  // нужен localStorage
webView.scrollView.bounces = false

// Android (WebView)
webView.settings.javaScriptEnabled = true
webView.settings.domStorageEnabled = true  // ВАЖНО: нужен для localStorage
webView.settings.mediaPlaybackRequiresUserGesture = false  // для звуков
```

**Важно:**
- `domStorageEnabled = true` — **обязательно**, иначе localStorage не работает и авторизация сломается
- `mediaPlaybackRequiresUserGesture = false` — для звуков квиза (Web Audio API)
- WebSocket работает внутри WebView без дополнительных настроек

### Закрытие WebView

Веб-фронтенд **не** отправляет сигнал о завершении. Варианты:

**Вариант А (простой):** Пользователь закрывает сам (кнопка "Назад" / свайп).

**Вариант Б (с обратной связью):** Добавить JavaScript bridge:
```javascript
// На веб-фронтенде (будущее):
window.AIMentor?.onQuizFinished({ rank: 2, xp: 70 });

// В мобильном приложении перехватить:
webView.addJavascriptInterface(object : QuizBridge {
    @JavascriptInterface
    fun onQuizFinished(data: String) {
        // Закрыть WebView, обновить XP на главном экране
    }
}, "AIMentor")
```
Этот bridge пока **не реализован** на фронтенде. На первом этапе используйте Вариант А.

---

## 4. Ввод кода вручную

Помимо виджета, студент может ввести код вручную. Для этого на главном экране мобильного приложения можно добавить кнопку "Ввести код квиза", которая открывает WebView **без параметра code**:

```
https://ai-mentor.kz/ru/webview/quiz?token={access_token}
```

Веб-фронтенд покажет экран ввода кода с клавиатурой.

---

## 5. Обработка ошибок

### REST API (виджет)

| HTTP | Значение | Действие |
|------|----------|----------|
| 200 | Успех | Показать виджет |
| 200 + `[]` | Пустой список | Скрыть виджет |
| 401 | Токен невалидный | Обновить токен, повторить |
| 500 | Ошибка сервера | Скрыть виджет, не блокировать UI |

Формат ошибки:
```json
{
  "detail": "Could not validate credentials"
}
```

### WebView

Ошибки внутри WebView (неверный код, квиз не найден) обрабатываются **веб-фронтендом**. Мобильное приложение не должно их перехватывать.

---

## 6. Чеклист

### Нативная реализация

- [ ] **API клиент** — `GET /students/quiz-sessions/my-quizzes` с Bearer token
- [ ] **Виджет "Мои квизы"** на главном экране
  - [ ] Условный рендер (скрывать если пусто)
  - [ ] Polling каждые 60 секунд
  - [ ] Статус-бейджи: зелёный (lobby), синий (in_progress), серый (finished)
  - [ ] Прогресс-бар для self-paced (answered_count / question_count)
  - [ ] Результаты для finished (rank, xp_earned, correct/total)
  - [ ] Кнопка "Войти" / "Продолжить" → открытие WebView
- [ ] **Кнопка "Ввести код"** — открывает WebView без code
- [ ] **WebView контейнер**
  - [ ] Полноэкранный
  - [ ] JavaScript enabled
  - [ ] DOM Storage enabled (localStorage!)
  - [ ] Media autoplay allowed (звуки)
  - [ ] Формирование URL: `ai-mentor.kz/{locale}/webview/quiz?token={jwt}&code={code}`
  - [ ] Кнопка "Назад" для закрытия

### Не нужно реализовывать

- ~~WebSocket клиент~~ — делает веб-фронтенд
- ~~Экраны вопросов/ответов~~ — делает веб-фронтенд
- ~~Таймер~~ — делает веб-фронтенд
- ~~State machine~~ — делает веб-фронтенд
- ~~Звуки~~ — делает веб-фронтенд
- ~~Лидерборд/подиум~~ — делает веб-фронтенд

### Локализация (нативный виджет)

**Русский:**
| Ключ | Текст |
|------|-------|
| title | Мои квизы |
| available | Доступен |
| inProgress | В процессе |
| completed | Завершён |
| join | Войти |
| continue | Продолжить |
| enterCode | Ввести код |
| untitled | Квиз |
| live | Live |
| team | Команды |
| selfPaced | Самост. |

**Казахский:**
| Ключ | Текст |
|------|-------|
| title | Менің квиздерім |
| available | Қол жетімді |
| inProgress | Жүріп жатыр |
| completed | Аяқталды |
| join | Кіру |
| continue | Жалғастыру |
| enterCode | Кодты енгізу |
| untitled | Квиз |
| live | Live |
| team | Командалар |
| selfPaced | Өздігінен |
