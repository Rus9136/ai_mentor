# Техническое задание: Профиль студента в мобильном приложении

## Обзор

Документация API для экрана профиля студента в мобильном приложении. Описывает все эндпоинты необходимые для реализации функционала идентичного веб-версии ai-mentor.kz.

**Base URL:** `https://api.ai-mentor.kz/api/v1`

---

## Содержание

1. [Структура экрана профиля](#структура-экрана-профиля)
2. [API Endpoints](#api-endpoints)
   - [Данные пользователя](#1-данные-текущего-пользователя)
   - [Профиль студента](#2-профиль-студента)
   - [Статистика](#3-статистика-студента)
   - [Уровень освоения (Mastery)](#4-обзор-уровня-освоения-mastery)
   - [Заявка на вступление в класс](#5-заявка-на-вступление-в-класс)
   - [Удаление аккаунта](#6-удаление-аккаунта)
3. [UI спецификация](#ui-спецификация)
4. [Обработка ошибок](#обработка-ошибок)

---

## Структура экрана профиля

Экран профиля состоит из следующих секций:

```
┌────────────────────────────────┐
│                                │
│   [Avatar]  Имя Фамилия        │  ← ProfileHeader
│             Школа              │
│             Класс              │
│             email@example.com  │
│                                │
├────────────────────────────────┤
│                                │
│   📊 Моя статистика            │  ← StatsCards
│   ┌────┐ ┌────┐ ┌────┐ ┌────┐ │
│   │ 🔥 │ │ 📖 │ │ ✓  │ │ ⏱  │ │
│   │ 5  │ │ 12 │ │ 48 │ │ 2ч │ │
│   │дней│ │пар.│ │зад.│ │    │ │
│   └────┘ └────┘ └────┘ └────┘ │
│                                │
├────────────────────────────────┤
│                                │
│   📈 Мой уровень               │  ← MasteryOverview
│   ┌──────────────────────────┐ │
│   │ Всего: A:2 B:3 C:1       │ │
│   ├──────────────────────────┤ │
│   │ Глава 1    ████████░ 85% A│ │
│   │ Глава 2    ██████░░░ 62% B│ │
│   │ Глава 3    ████░░░░░ 45% C│ │
│   └──────────────────────────┘ │
│                                │
├────────────────────────────────┤
│                                │
│   ⚙️ Настройки                 │  ← SettingsSection
│   ┌──────────────────────────┐ │
│   │ 👥 Вступить в класс    → │ │
│   └──────────────────────────┘ │
│   ┌──────────────────────────┐ │
│   │ 🌐 Язык     [RU] [KZ]    │ │
│   └──────────────────────────┘ │
│   ┌──────────────────────────┐ │
│   │ 🚪 Выйти               → │ │
│   └──────────────────────────┘ │
│   ┌──────────────────────────┐ │
│   │ 🗑️ Удалить аккаунт     → │ │
│   └──────────────────────────┘ │
│                                │
└────────────────────────────────┘
```

---

## API Endpoints

### 1. Данные текущего пользователя

Получение базовых данных пользователя (имя, email, аватар).

```http
GET /auth/me
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": 123,
  "email": "student@gmail.com",
  "first_name": "Иван",
  "last_name": "Петров",
  "middle_name": "Сергеевич",
  "role": "student",
  "school_id": 7,
  "avatar_url": "https://lh3.googleusercontent.com/...",
  "auth_provider": "google",
  "is_active": true,
  "is_verified": true
}
```

**TypeScript Interface:**
```typescript
interface UserResponse {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  middle_name: string | null;
  role: string;
  school_id: number | null;
  avatar_url: string | null;
  auth_provider: string;
  is_active: boolean;
  is_verified: boolean;
}
```

---

### 2. Профиль студента

Получение данных профиля студента с информацией о школе и классах.

```http
GET /students/profile
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": 456,
  "student_code": "STU70724001",
  "grade_level": 7,
  "birth_date": "2012-05-15",
  "school_name": "AI Mentor School",
  "classes": [
    {
      "id": 45,
      "name": "7-А",
      "grade_level": 7
    }
  ]
}
```

**TypeScript Interface:**
```typescript
interface ClassInfo {
  id: number;
  name: string;
  grade_level: number;
}

interface StudentProfile {
  id: number;
  student_code: string;
  grade_level: number;
  birth_date: string | null;  // ISO 8601 format: "2012-05-15"
  school_name: string | null;
  classes: ClassInfo[];
}
```

**Примечания:**
- `school_name` может быть `null` если студент ещё не привязан к школе
- `classes` — массив классов, в которых состоит студент (обычно 1)
- `birth_date` — дата в формате ISO 8601

---

### 3. Статистика студента

Получение статистики обучения: серия дней, завершённые параграфы, задания, время.

```http
GET /students/stats
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "streak_days": 5,
  "total_paragraphs_completed": 12,
  "total_tasks_completed": 48,
  "total_time_spent_minutes": 145
}
```

**TypeScript Interface:**
```typescript
interface StudentStats {
  streak_days: number;              // Серия дней подряд (≥10 мин/день)
  total_paragraphs_completed: number; // Завершённых параграфов
  total_tasks_completed: number;     // Выполненных заданий
  total_time_spent_minutes: number;  // Общее время в минутах
}
```

**Логика отображения времени:**
```typescript
function formatTime(minutes: number): { value: number; unit: string } {
  if (minutes < 60) {
    return { value: minutes, unit: 'мин' };
  }
  const hours = Math.floor(minutes / 60);
  return { value: hours, unit: 'ч' };
}
```

**Карточки статистики:**

| Иконка | Значение | Подпись | Цвет фона |
|--------|----------|---------|-----------|
| 🔥 Flame | `streak_days` | "дней подряд" | Orange |
| 📖 BookOpen | `total_paragraphs_completed` | "параграфов" | Green |
| ✓ CheckCircle | `total_tasks_completed` | "заданий" | Blue |
| ⏱ Clock | formatted time | "мин" / "ч" | Purple |

---

### 4. Обзор уровня освоения (Mastery)

Получение данных об уровне освоения по всем главам с A/B/C грейдингом.

```http
GET /students/mastery/overview
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "student_id": 456,
  "chapters": [
    {
      "id": 1,
      "student_id": 456,
      "chapter_id": 101,
      "total_paragraphs": 10,
      "completed_paragraphs": 8,
      "mastered_paragraphs": 6,
      "struggling_paragraphs": 1,
      "mastery_level": "A",
      "mastery_score": 85.5,
      "progress_percentage": 80,
      "summative_score": 0.92,
      "summative_passed": true,
      "last_updated_at": "2024-01-20T15:30:00Z",
      "chapter_title": "Введение в алгебру",
      "chapter_order": 1
    },
    {
      "id": 2,
      "student_id": 456,
      "chapter_id": 102,
      "total_paragraphs": 8,
      "completed_paragraphs": 5,
      "mastered_paragraphs": 3,
      "struggling_paragraphs": 0,
      "mastery_level": "B",
      "mastery_score": 62.0,
      "progress_percentage": 62,
      "summative_score": null,
      "summative_passed": null,
      "last_updated_at": "2024-01-19T10:15:00Z",
      "chapter_title": "Линейные уравнения",
      "chapter_order": 2
    }
  ],
  "total_chapters": 6,
  "average_mastery_score": 68.5,
  "level_a_count": 2,
  "level_b_count": 3,
  "level_c_count": 1
}
```

**TypeScript Interfaces:**
```typescript
interface ChapterMasteryDetail {
  id: number;
  student_id: number;
  chapter_id: number;
  total_paragraphs: number;
  completed_paragraphs: number;
  mastered_paragraphs: number;      // Оценка ≥ 85%
  struggling_paragraphs: number;     // Оценка < 60%
  mastery_level: 'A' | 'B' | 'C';
  mastery_score: number;             // 0-100
  progress_percentage: number;        // 0-100
  summative_score: number | null;    // 0.0-1.0, итоговый тест
  summative_passed: boolean | null;
  last_updated_at: string;           // ISO 8601
  chapter_title: string | null;
  chapter_order: number | null;
}

interface MasteryOverview {
  student_id: number;
  chapters: ChapterMasteryDetail[];
  total_chapters: number;
  average_mastery_score: number;
  level_a_count: number;
  level_b_count: number;
  level_c_count: number;
}
```

**Уровни освоения (A/B/C):**

| Уровень | Описание | Цвет | Порог |
|---------|----------|------|-------|
| A | Отлично | Green (#22c55e) | mastery_score ≥ 80 |
| B | Хорошо | Blue (#3b82f6) | mastery_score ≥ 60 |
| C | Требует внимания | Orange (#f97316) | mastery_score < 60 |

**Отображение progress bar:**
```typescript
const LEVEL_COLORS = {
  A: { bg: 'bg-green-100', text: 'text-green-700', bar: 'bg-green-500' },
  B: { bg: 'bg-blue-100', text: 'text-blue-700', bar: 'bg-blue-500' },
  C: { bg: 'bg-orange-100', text: 'text-orange-700', bar: 'bg-orange-500' },
};
```

---

### 5. Заявка на вступление в класс

#### 5.1 Создание заявки

Студент может подать заявку на вступление в класс по коду приглашения от учителя.

```http
POST /students/join-request
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "invitation_code": "7A-ABC12",
  "first_name": "Иван",
  "last_name": "Петров",
  "middle_name": "Сергеевич"
}
```

**Request Body:**
```typescript
interface JoinRequestCreateData {
  invitation_code: string;  // 4-20 символов
  first_name: string;       // 1-100 символов, обязательное
  last_name: string;        // 1-100 символов, обязательное
  middle_name?: string;     // 0-100 символов, опционально
}
```

**Response (успех):**
```json
{
  "id": 789,
  "student_id": 456,
  "class_id": 45,
  "school_id": 7,
  "status": "pending",
  "created_at": "2024-01-20T15:30:00Z"
}
```

**TypeScript Interface:**
```typescript
interface JoinRequestResponse {
  id: number;
  student_id: number;
  class_id: number;
  school_id: number;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
}
```

**Возможные ошибки (HTTP 400):**

| Код ошибки | Сообщение на русском |
|------------|---------------------|
| `code_not_found` | Код приглашения не найден |
| `code_expired` | Срок действия кода истёк |
| `code_exhausted` | Код использован максимальное количество раз |
| `code_inactive` | Код приглашения неактивен |
| `request_pending` | У вас уже есть активная заявка на рассмотрении |
| `already_in_class` | Вы уже состоите в этом классе |
| `no_class` | Код не привязан к классу |

---

#### 5.2 Статус заявки

Получение статуса текущей заявки студента.

```http
GET /students/join-request/status
Authorization: Bearer {access_token}
```

**Response (есть заявка):**
```json
{
  "id": 789,
  "status": "pending",
  "class_name": "7-А",
  "school_name": "Школа №15",
  "created_at": "2024-01-20T15:30:00Z",
  "rejection_reason": null,
  "has_request": true
}
```

**Response (нет заявки):**
```json
{
  "has_request": false
}
```

**Response (отклонённая заявка):**
```json
{
  "id": 789,
  "status": "rejected",
  "class_name": "7-А",
  "school_name": "Школа №15",
  "created_at": "2024-01-20T15:30:00Z",
  "rejection_reason": "Ученик не найден в списках школы",
  "has_request": true
}
```

**TypeScript Interface:**
```typescript
interface JoinRequestStatus {
  id: number | null;
  status: 'pending' | 'approved' | 'rejected' | null;
  class_name: string | null;
  school_name: string | null;
  created_at: string | null;
  rejection_reason: string | null;
  has_request: boolean;
}
```

---

### 6. Удаление аккаунта

Полное удаление аккаунта пользователя и всех связанных данных.

```http
DELETE /auth/me
Authorization: Bearer {access_token}
```

**Response:** `204 No Content`

**Важно:**
- После успешного удаления очистить все локальные токены
- Перенаправить пользователя на экран входа
- Показать подтверждение перед удалением

---

## UI спецификация

### ProfileHeader

Отображает аватар, имя, школу, класс и email.

```
┌─────────────────────────────────────────┐
│ ┌────────┐                              │
│ │        │  Иван Петров                 │
│ │   ИП   │  Сергеевич                   │
│ │        │  AI Mentor School            │
│ └────────┘  7-А                         │
│             student@gmail.com           │
└─────────────────────────────────────────┘
```

**Логика аватара:**
- Если `avatar_url` есть → показать изображение
- Если нет → показать инициалы (первые буквы имени и фамилии)

**Логика отображения класса:**
- Если `classes.length > 0` → показать имена классов через запятую
- Иначе если `grade_level` есть → показать "{grade_level} класс"
- Иначе → не показывать

---

### StatsCards

4 карточки в 2x2 или 4x1 grid.

```
┌────────────────┐  ┌────────────────┐
│      🔥        │  │      📖        │
│      5         │  │      12        │
│  дней подряд   │  │   параграфов   │
└────────────────┘  └────────────────┘
┌────────────────┐  ┌────────────────┐
│      ✓         │  │      ⏱        │
│      48        │  │      2         │
│    заданий     │  │       ч        │
└────────────────┘  └────────────────┘
```

---

### MasteryOverview

Summary + список глав с progress bars.

**Пустое состояние:**
```
┌─────────────────────────────────────────┐
│                  ⚠️                      │
│      Данные об уровне освоения          │
│        пока недоступны                  │
└─────────────────────────────────────────┘
```

**С данными:**
```
┌─────────────────────────────────────────┐
│  📈 Общий уровень      A:2  B:3  C:1    │
├─────────────────────────────────────────┤
│  Введение в алгебру                     │
│  ████████████████░░░░  85%         [A]  │
├─────────────────────────────────────────┤
│  Линейные уравнения                     │
│  ████████████░░░░░░░░  62%         [B]  │
└─────────────────────────────────────────┘
```

**Сортировка:** по `chapter_order` (возрастание)

---

### JoinClassModal

Модальное окно для подачи заявки в класс.

```
┌─────────────────────────────────────────┐
│  Вступить в класс                   [X] │
├─────────────────────────────────────────┤
│                                         │
│  Код приглашения                        │
│  ┌─────────────────────────────────┐    │
│  │ 7A-ABC12                        │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ─────── Введите свои данные ────────   │
│                                         │
│  Фамилия *                              │
│  ┌─────────────────────────────────┐    │
│  │ Петров                          │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Имя *                                  │
│  ┌─────────────────────────────────┐    │
│  │ Иван                            │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Отчество                               │
│  ┌─────────────────────────────────┐    │
│  │ Сергеевич                       │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │         Отправить заявку        │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

**Валидация:**
- `invitation_code`: обязательное, min 4, max 20 символов
- `first_name`: обязательное, min 1, max 100 символов
- `last_name`: обязательное, min 1, max 100 символов
- `middle_name`: опционально, max 100 символов

**При ошибке:** показать сообщение из `detail` в красном блоке

---

### JoinRequestStatus

Отображение статуса заявки вместо кнопки "Вступить в класс".

**Pending (ожидает):**
```
┌─────────────────────────────────────────┐
│ ┌────┐                                  │
│ │ ⏳ │  Заявка на рассмотрении          │
│ └────┘  Ожидаем ответа от учителя       │
│         класса 7-А                      │
│         Школа №15                       │
└─────────────────────────────────────────┘
```
Цвет: Yellow background, yellow border-left

**Rejected (отклонена):**
```
┌─────────────────────────────────────────┐
│ ┌────┐                                  │
│ │ ❌ │  Заявка отклонена                │
│ └────┘  Причина: Ученик не найден       │
│         7-А                             │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │       Попробовать снова         │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```
Цвет: Red background, red border-left

---

### SettingsSection

Список настроек с действиями.

```
┌─────────────────────────────────────────┐
│ 👥  Вступить в класс                  → │
│     У вас есть код от учителя?          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 🌐  Язык                    [RU] [KZ]   │
│     Русский                             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 🚪  Выйти                             → │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 🗑️  Удалить аккаунт                   → │
└─────────────────────────────────────────┘
```

**Подтверждение выхода:**
```
┌─────────────────────────────────────────┐
│      Вы уверены, что хотите выйти?      │
│                                         │
│   [  Отмена  ]     [  Выйти  ]          │
└─────────────────────────────────────────┘
```

**Подтверждение удаления:**
```
┌─────────────────────────────────────────┐
│      Удалить аккаунт?                   │
│                                         │
│   Все ваши данные будут удалены         │
│   без возможности восстановления        │
│                                         │
│   [  Отмена  ]     [ Удалить ]          │
└─────────────────────────────────────────┘
```

---

## Обработка ошибок

### HTTP 401 Unauthorized

1. Попробовать refresh token: `POST /auth/refresh`
2. Если успешно → повторить оригинальный запрос с новым токеном
3. Если неуспешно → очистить токены и redirect на Login

### HTTP 400 Bad Request

```json
{
  "detail": "Сообщение об ошибке"
}
```

Показать `detail` пользователю в toast/alert.

### HTTP 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "first_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

Показать ошибки валидации у соответствующих полей формы.

---

## Порядок загрузки данных

При открытии экрана профиля загружать **параллельно**:

1. `GET /auth/me` — данные пользователя
2. `GET /students/profile` — профиль студента
3. `GET /students/stats` — статистика
4. `GET /students/mastery/overview` — уровни освоения
5. `GET /students/join-request/status` — статус заявки

**Рекомендуемый cache time:**
- `/auth/me` — 10 минут
- `/students/profile` — 10 минут
- `/students/stats` — 5 минут
- `/students/mastery/overview` — 5 минут
- `/students/join-request/status` — 1 минута (может часто меняться)

---

## Локализация

Приложение поддерживает два языка:
- `ru` — Русский
- `kz` — Казахский

Тексты для профиля:

| Ключ | Русский | Казахский |
|------|---------|-----------|
| profile.myStats | Моя статистика | Менің статистикам |
| profile.myLevel | Мой уровень | Менің деңгейім |
| profile.settings | Настройки | Баптаулар |
| profile.stats.streak | дней подряд | күн қатарынан |
| profile.stats.paragraphs | параграфов | параграфтар |
| profile.stats.tasks | заданий | тапсырмалар |
| profile.stats.time | мин | мин |
| profile.stats.hours | ч | сағ |
| profile.mastery.overall | Общий уровень | Жалпы деңгей |
| profile.mastery.noData | Данные пока недоступны | Деректер әлі жоқ |
| profile.joinClass.button | Вступить в класс | Сыныпқа қосылу |
| profile.joinClass.description | У вас есть код от учителя? | Мұғалімнен код бар ма? |
| profile.joinClass.title | Вступить в класс | Сыныпқа қосылу |
| profile.joinClass.invitationCode | Код приглашения | Шақыру коды |
| profile.joinClass.lastName | Фамилия | Тегі |
| profile.joinClass.firstName | Имя | Аты |
| profile.joinClass.middleName | Отчество | Әкесінің аты |
| profile.joinClass.submit | Отправить заявку | Өтінішті жіберу |
| profile.joinClass.pendingStatus | Заявка на рассмотрении | Өтініш қаралуда |
| profile.joinClass.rejectedStatus | Заявка отклонена | Өтініш қабылданбады |
| profile.joinClass.tryAgain | Попробовать снова | Қайта көру |
| profile.language.title | Язык | Тіл |
| profile.language.ru | Русский | Орысша |
| profile.language.kz | Казахский | Қазақша |
| profile.logout | Выйти | Шығу |
| profile.confirmLogout | Вы уверены? | Сенімдісіз бе? |
| profile.deleteAccount | Удалить аккаунт | Аккаунтты жою |
| profile.confirmDelete | Удалить аккаунт? | Аккаунтты жою? |
| profile.deleteWarning | Все данные будут удалены | Барлық деректер жойылады |
| profile.cancel | Отмена | Болдырмау |
| profile.gradeLabel | класс | сынып |

---

## Checklist для тестирования

- [ ] ProfileHeader отображает аватар (URL или инициалы)
- [ ] ProfileHeader показывает школу и классы
- [ ] StatsCards отображают 4 карточки со статистикой
- [ ] Время корректно форматируется (мин → ч)
- [ ] MasteryOverview показывает пустое состояние когда нет данных
- [ ] MasteryOverview отображает список глав с progress bars
- [ ] Уровни A/B/C отображаются правильными цветами
- [ ] Кнопка "Вступить в класс" открывает модальное окно
- [ ] Форма заявки валидирует обязательные поля
- [ ] Ошибки API отображаются пользователю
- [ ] После успешной заявки показывается статус "Pending"
- [ ] Отклонённая заявка показывает причину и кнопку "Попробовать снова"
- [ ] Переключение языка работает корректно
- [ ] Выход из аккаунта требует подтверждения
- [ ] Удаление аккаунта требует подтверждения
- [ ] После удаления аккаунта redirect на Login
- [ ] Pull-to-refresh обновляет все данные
- [ ] Skeleton/loading states во время загрузки
