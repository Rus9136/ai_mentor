# Gamification — API для мобильного приложения

Документ для мобильного разработчика. Описывает API геймификации: ежедневные квесты, профиль/XP/уровень, ачивки, лидерборд, история XP. Все экраны реализуются **нативно** в мобильном приложении.

**Base URL:** `https://api.ai-mentor.kz/api/v1`
**Авторизация:** JWT токен в `Authorization: Bearer <token>` (роль STUDENT)
**Формат:** JSON. Даты в ISO 8601.

> Quiz Battle (живые квизы) описан в отдельном документе: [`API_QUIZ_MOBILE.md`](./API_QUIZ_MOBILE.md)

---

## Содержание

1. [Ежедневные квесты](#1-ежедневные-квесты)
2. [Профиль, XP, Уровень](#2-профиль-xp-уровень)
3. [Ачивки](#3-ачивки)
4. [Лидерборд](#4-лидерборд)
5. [История XP](#5-история-xp)
6. [Polling-стратегия](#6-polling-стратегия)
7. [Чеклист](#7-чеклист)

---

## 1. Ежедневные квесты

### 1.1 Получить сегодняшние квесты

```
GET /students/gamification/daily-quests
Authorization: Bearer <token>
```

**Описание:** Возвращает список ежедневных квестов с прогрессом текущего ученика. При первом запросе за день автоматически создаёт записи прогресса (lazy init).

**Ответ:** `200 OK`

```json
[
  {
    "id": 1,
    "code": "complete_3_tests",
    "name_kk": "3 тест тапсыр",
    "name_ru": "Сдай 3 теста",
    "description_kk": "Бүгін 3 тестті тапсыр",
    "description_ru": "Пройди 3 теста сегодня",
    "quest_type": "complete_tests",
    "target_value": 3,
    "xp_reward": 30,
    "current_value": 1,
    "is_completed": false,
    "completed_at": null,
    "subject_name_kk": null,
    "subject_name_ru": null
  },
  {
    "id": 3,
    "code": "master_paragraph",
    "name_kk": "Параграфты меңгер",
    "name_ru": "Освой параграф",
    "description_kk": "1 параграфты меңгеру деңгейіне жеткіз",
    "description_ru": "Доведи 1 параграф до уровня mastered",
    "quest_type": "master_paragraph",
    "target_value": 1,
    "xp_reward": 40,
    "current_value": 0,
    "is_completed": false,
    "completed_at": null,
    "subject_name_kk": null,
    "subject_name_ru": null
  }
]
```

### 1.2 Поля ответа

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | int | ID квеста |
| `code` | string | Уникальный код квеста |
| `name_kk` | string | Название (казахский) |
| `name_ru` | string | Название (русский) |
| `description_kk` | string? | Описание (казахский) |
| `description_ru` | string? | Описание (русский) |
| `quest_type` | string | Тип квеста (см. таблицу ниже) |
| `target_value` | int | Цель (напр. 3 теста) |
| `xp_reward` | int | Награда XP за выполнение |
| `current_value` | int | Текущий прогресс |
| `is_completed` | bool | Выполнен ли |
| `completed_at` | string? | Дата/время выполнения (ISO) |
| `subject_name_kk` | string? | Привязка к предмету (казахский) |
| `subject_name_ru` | string? | Привязка к предмету (русский) |

### 1.3 Типы квестов

| `quest_type` | Описание | Как инкрементируется |
|-------------|----------|---------------------|
| `complete_tests` | Пройти N тестов | Автоматически при прохождении теста |
| `master_paragraph` | Освоить N параграфов | Автоматически при mastery=mastered |
| `study_time` | Учиться N минут | *(пока неактивен)* |
| `review_spaced` | Сделать N повторений | *(пока неактивен)* |

### 1.4 Логика работы

- **Прогресс обновляется автоматически** сервером при обучающих событиях (тест пройден, параграф освоен, квиз-батл завершён)
- Мобильное приложение **не отправляет** запросы на инкремент квестов — только читает
- Квесты обновляются каждый день (UTC)
- Если квест привязан к предмету (`subject_name_kk/ru` != null) — инкрементируется только при действиях по этому предмету
- При выполнении квеста (`current_value >= target_value`) XP начисляется автоматически

### 1.5 Рекомендации для UI

```
┌─────────────────────────────────────────┐
│ 📝 Сдай 3 теста               +30 XP   │
│ ████████░░░░░░  2/3                     │
├─────────────────────────────────────────┤
│ ✅ Освой параграф              +40 XP   │
│ ████████████████  1/1  Выполнено!       │
├─────────────────────────────────────────┤
│ 🎮 Сыграй в квиз  (Алгебра)   +20 XP   │
│ ░░░░░░░░░░░░░░░░  0/1                   │
└─────────────────────────────────────────┘
```

- Progress bar: `current_value / target_value`
- Зелёный цвет + галочка для `is_completed = true`
- `xp_reward` — показать справа ("+30 XP")
- Локализация: `name_kk` / `name_ru` в зависимости от языка приложения
- Опциональный бейдж предмета если `subject_name_kk/ru` не null
- **Polling:** обновлять каждые 30-60 секунд или по возвращению на экран

### 1.6 Пример флоу

```
1. GET /students/gamification/daily-quests
   → [
       { code: "complete_3_tests", target_value: 3, current_value: 1, is_completed: false, xp_reward: 30 },
       { code: "master_paragraph", target_value: 1, current_value: 0, is_completed: false, xp_reward: 40 }
     ]

2. Ученик проходит тест в приложении...

3. GET /students/gamification/daily-quests (обновляем)
   → [{ code: "complete_3_tests", current_value: 2, is_completed: false }, ...]

4. Ученик проходит ещё один тест...

5. GET /students/gamification/daily-quests
   → [{ code: "complete_3_tests", current_value: 3, is_completed: true,
        completed_at: "2026-03-15T11:45:00Z" }, ...]
   Квест выполнен! +30 XP начислены автоматически.

6. GET /students/gamification/profile
   → { total_xp: 1270, level: 5, ... }  // XP увеличился на 30
```

---

## 2. Профиль, XP, Уровень

### 2.1 Получить профиль

```
GET /students/gamification/profile
Authorization: Bearer <token>
```

**Ответ:** `200 OK`

```json
{
  "total_xp": 1240,
  "level": 5,
  "xp_in_current_level": 403,
  "xp_to_next_level": 1837,
  "current_streak": 12,
  "longest_streak": 15,
  "badges_earned_count": 7
}
```

### 2.2 Поля ответа

| Поле | Тип | Описание |
|------|-----|----------|
| `total_xp` | int | Суммарный XP за всё время |
| `level` | int | Текущий уровень (от 1) |
| `xp_in_current_level` | int | XP набранный на текущем уровне |
| `xp_to_next_level` | int | XP нужно для следующего уровня |
| `current_streak` | int | Текущая серия дней подряд |
| `longest_streak` | int | Рекорд серии дней |
| `badges_earned_count` | int | Кол-во полученных ачивок |

### 2.3 Формула уровня

```
XP для перехода с уровня L на L+1 = floor(100 * L^1.5)

Уровень 1→2:   283 XP
Уровень 2→3:   519 XP
Уровень 5→6:   1341 XP
Уровень 10→11: 3317 XP
```

### 2.4 Виджет на главном экране

```
┌──────────────────────────────────────────┐
│  ⭐ Уровень 5        🔥 12 дней подряд  │
│  ████████████░░░░░░░░░  403 / 1,837 XP  │
└──────────────────────────────────────────┘
```

- Прогресс-бар: `xp_in_current_level / xp_to_next_level`
- Показать `current_streak` с иконкой огня
- Кликабельный → переход на полный профиль геймификации

---

## 3. Ачивки

### 3.1 Все ачивки с прогрессом

```
GET /students/gamification/achievements
Authorization: Bearer <token>
```

**Ответ:** `200 OK`

```json
[
  {
    "id": 1,
    "achievement": {
      "id": 10,
      "code": "first_test",
      "name_kk": "Бірінші тест",
      "name_ru": "Первый тест",
      "description_kk": "Бірінші тестті тапсыр",
      "description_ru": "Сдай первый тест",
      "icon": "🏆",
      "category": "tests",
      "rarity": "common",
      "xp_reward": 20
    },
    "progress": 1.0,
    "is_earned": true,
    "earned_at": "2026-03-12T14:30:00Z"
  },
  {
    "id": 2,
    "achievement": {
      "id": 11,
      "code": "test_master_50",
      "name_kk": "50 тест тапсыр",
      "name_ru": "50 тестов",
      "description_kk": "50 тест тапсыр",
      "description_ru": "Сдай 50 тестов",
      "icon": "🎯",
      "category": "tests",
      "rarity": "rare",
      "xp_reward": 100
    },
    "progress": 0.6,
    "is_earned": false,
    "earned_at": null
  }
]
```

### 3.2 Новые ачивки (polling)

```
GET /students/gamification/achievements/recent
Authorization: Bearer <token>
```

**Описание:** Возвращает недавно полученные ачивки, которые ещё не были показаны пользователю. **Автоматически помечает их как показанные** (notified) — повторный запрос вернёт пустой массив, пока не появятся новые.

**Ответ:** `200 OK`

```json
[
  {
    "id": 3,
    "achievement": {
      "id": 12,
      "code": "streak_7",
      "name_kk": "Апталық серия",
      "name_ru": "Недельная серия",
      "description_kk": "7 күн қатарынан оқы",
      "description_ru": "Учись 7 дней подряд",
      "icon": "🔥",
      "category": "streak",
      "rarity": "rare",
      "xp_reward": 50
    },
    "progress": 1.0,
    "is_earned": true,
    "earned_at": "2026-03-15T08:15:00Z"
  }
]
```

### 3.3 Редкость ачивок

| `rarity` | Цвет рамки | Описание |
|-----------|-----------|----------|
| `common` | Серый | Базовые ачивки |
| `rare` | Синий | Средние |
| `epic` | Фиолетовый | Сложные |
| `legendary` | Золотой | Экстра-сложные |

### 3.4 Категории ачивок

| `category` | Описание |
|-----------|----------|
| `tests` | За прохождение тестов |
| `mastery` | За освоение параграфов |
| `streak` | За серию дней |
| `xp` | За набор XP |
| `quiz` | За участие в квизах |

### 3.5 Рекомендации для UI

- **Polling `/achievements/recent`** каждые 30 секунд для показа popup новой ачивки
- Карточка: иконка (emoji `icon`), название (локализованное), прогресс-бар
- Earned: цветная иконка + дата получения
- Locked: серая иконка + прогресс-бар (`progress` = 0.0–1.0, т.е. 0–100%)
- Рамка карточки — цвет по `rarity`
- Popup новой ачивки: modal с анимацией, иконка + название + "+{xp_reward} XP"

---

## 4. Лидерборд

### 4.1 Получить лидерборд

```
GET /students/gamification/leaderboard?scope=school
GET /students/gamification/leaderboard?scope=class&class_id=15
Authorization: Bearer <token>
```

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `scope` | string | Да | `school` или `class` |
| `class_id` | int | Для `scope=class` | ID класса |

**Ответ:** `200 OK`

```json
{
  "entries": [
    {
      "rank": 1,
      "student_id": 101,
      "student_name": "Айдана Б.",
      "total_xp": 2450,
      "level": 8
    },
    {
      "rank": 2,
      "student_id": 102,
      "student_name": "Олжас К.",
      "total_xp": 2180,
      "level": 7
    }
  ],
  "student_rank": 6,
  "student_xp": 1240,
  "student_level": 5,
  "total_students": 128,
  "scope": "school"
}
```

### 4.2 Поля ответа

| Поле | Тип | Описание |
|------|-----|----------|
| `entries` | array | Топ-50 учеников |
| `entries[].rank` | int | Место |
| `entries[].student_id` | int | ID ученика |
| `entries[].student_name` | string | Имя |
| `entries[].total_xp` | int | Суммарный XP |
| `entries[].level` | int | Уровень |
| `student_rank` | int | Место текущего ученика |
| `student_xp` | int | XP текущего ученика |
| `student_level` | int | Уровень текущего ученика |
| `total_students` | int | Всего учеников |
| `scope` | string | `"school"` или `"class"` |

### 4.3 Рекомендации для UI

```
┌─────────────────────────────┐
│  [Школа]  [Класс]          │
│                             │
│  🥇 Айдана    Ур.8  2,450  │
│  🥈 Олжас     Ур.7  2,180  │
│  🥉 Дана      Ур.7  1,950  │
│  ─────────────────────────  │
│  4. Бекзат    Ур.6  1,820  │
│  5. Арман     Ур.5  1,640  │
│ ▸6. Ты        Ур.5  1,240◂ │ ← подсветка
│  7. Камила    Ур.4  1,100  │
└─────────────────────────────┘
```

- Переключатель "Школа" / "Класс"
- Топ-3 с медалями (крупнее)
- Текущий ученик подсвечен в списке
- `student_rank` — место текущего ученика (показать внизу если он не в топ-50)

---

## 5. История XP

### 5.1 Получить историю

```
GET /students/gamification/xp-history?days=7
Authorization: Bearer <token>
```

| Параметр | Тип | Default | Max | Описание |
|----------|-----|---------|-----|----------|
| `days` | int | 7 | 90 | За последние N дней |

**Ответ:** `200 OK`

```json
[
  {
    "id": 456,
    "amount": 30,
    "source_type": "test_passed",
    "source_id": 789,
    "created_at": "2026-03-15T10:30:00Z"
  },
  {
    "id": 455,
    "amount": 40,
    "source_type": "daily_quest",
    "source_id": 3,
    "created_at": "2026-03-15T09:15:00Z"
  }
]
```

### 5.2 Типы источников XP

| `source_type` | Описание |
|--------------|----------|
| `test_passed` | Прохождение теста |
| `mastery_up` | Изменение mastery параграфа |
| `streak_bonus` | Бонус за серию дней |
| `chapter_complete` | Повышение уровня главы |
| `daily_quest` | Выполнение ежедневного квеста |
| `self_assessment` | Самооценка |
| `review_completed` | Интервальное повторение |
| `paragraph_complete` | Завершение параграфа |
| `quiz_battle` | Участие в квиз-батле |

### 5.3 Рекомендации для UI

- Список транзакций с иконками по `source_type`
- Группировка по дням
- Сумма XP за день в заголовке группы
- Опционально: линейный график XP по дням

---

## 6. Polling-стратегия

| Endpoint | Интервал | Когда | Примечание |
|----------|---------|-------|------------|
| `/profile` | 30 сек | Главный экран, экран профиля | Основной виджет |
| `/daily-quests` | 30-60 сек | Экран квестов | Или при возврате на экран |
| `/achievements/recent` | 30 сек | Любой экран (фоново) | Для popup новой ачивки |
| `/achievements` | По запросу | Экран ачивок | Не нужен polling |
| `/leaderboard` | По запросу | Экран лидерборда | Pull-to-refresh |
| `/xp-history` | По запросу | Экран истории | Pull-to-refresh |

---

## 7. Чеклист

### Экраны для реализации

- [ ] **Виджет XP/Уровень** на главном экране (profile endpoint)
  - [ ] Номер уровня, прогресс-бар XP, стрик
  - [ ] Кликабельный → полный профиль
- [ ] **Экран "Профиль геймификации"** (табы или секции)
  - [ ] Профиль: уровень, XP бар, стрик, статистика
  - [ ] Ачивки: сетка карточек (earned/locked, rarity цвета)
  - [ ] Лидерборд: школа/класс, топ-3 с медалями
  - [ ] Ежедневные квесты: карточки с прогрессом
- [ ] **Popup новой ачивки** (polling `/achievements/recent`)
  - [ ] Modal с анимацией
  - [ ] Иконка + название + "+{xp_reward} XP"
- [ ] **Ежедневные квесты** (на главном или в профиле)
  - [ ] Прогресс-бар, XP награда, статус
  - [ ] Зелёная подсветка выполненных

### Технические задачи

- [ ] API клиент для 6 gamification endpoints
- [ ] Polling manager (`/achievements/recent` каждые 30 сек фоново)
- [ ] Локализация: `name_kk`/`name_ru` для квестов и ачивок
- [ ] Кеширование профиля (обновлять при получении XP)

### Локализация

**Русский:**

| Ключ | Текст |
|------|-------|
| level | Уровень |
| xpProgress | {current} / {total} XP |
| streak | {days} дней подряд |
| achievements | Достижения |
| leaderboard | Рейтинг |
| dailyQuests | Ежедневные задания |
| school | Школа |
| class | Класс |
| earned | Получено |
| locked | Заблокировано |
| xpAwarded | +{amount} XP |
| levelUp | Уровень {level}! |
| questComplete | Задание выполнено! |
| yourRank | Твоё место: {rank} |
| noAchievements | Пока нет достижений |
| keepLearning | Продолжай учиться! |

**Казахский:**

| Ключ | Текст |
|------|-------|
| level | Деңгей |
| xpProgress | {current} / {total} XP |
| streak | Қатарынан {days} күн |
| achievements | Жетістіктер |
| leaderboard | Рейтинг |
| dailyQuests | Күнделікті тапсырмалар |
| school | Мектеп |
| class | Сынып |
| earned | Алынды |
| locked | Құлыпталған |
| xpAwarded | +{amount} XP |
| levelUp | {level} деңгей! |
| questComplete | Тапсырма орындалды! |
| yourRank | Сенің орның: {rank} |
| noAchievements | Әзірге жетістіктер жоқ |
| keepLearning | Оқуды жалғастыр! |

### Обработка ошибок

| HTTP | Значение | Действие |
|------|----------|----------|
| 200 | Успех | Показать данные |
| 401 | Токен невалидный | Обновить токен, повторить |
| 500 | Ошибка сервера | Показать кешированные данные |

Формат ошибки:
```json
{
  "detail": "Could not validate credentials"
}
```
