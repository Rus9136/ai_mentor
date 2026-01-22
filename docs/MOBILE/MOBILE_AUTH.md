# Техническое задание: Google OAuth и выбор класса в мобильном приложении

## Обзор задачи

После авторизации через Google новому пользователю необходимо предложить выбор класса (7-11), аналогично веб-версии на ai-mentor.kz.

---

## API Endpoints

**Base URL:** `https://api.ai-mentor.kz/api/v1`

### 1. Google OAuth Login

```http
POST /auth/google
Content-Type: application/json

{
  "id_token": "GOOGLE_ID_TOKEN",
  "client_id": "MOBILE_GOOGLE_CLIENT_ID"  // опционально, для верификации
}
```

**Response (новый пользователь):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "requires_onboarding": true,
  "user": {
    "id": 123,
    "email": "student@gmail.com",
    "first_name": "Иван",
    "last_name": "Петров",
    "avatar_url": "https://lh3.googleusercontent.com/...",
    "role": "student",
    "school_id": null,
    "is_active": true
  }
}
```

**Response (существующий пользователь):**
```json
{
  "requires_onboarding": false,
  "user": {
    "school_id": 7  // Уже привязан к школе
  }
  // ... остальные поля
}
```

**Ключевое поле:** `requires_onboarding`
- `true` → показать экран выбора класса
- `false` → перейти на главный экран

---

### 2. Валидация кода класса

```http
POST /auth/onboarding/validate-code
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "code": "PUBLIC7"
}
```

**Response (успех):**
```json
{
  "valid": true,
  "school": {
    "id": 7,
    "name": "AI Mentor School",
    "code": "school001"
  },
  "school_class": {
    "id": 45,
    "name": "7-А",
    "grade_level": 7
  },
  "grade_level": 7
}
```

**Response (ошибка):**
```json
{
  "valid": false,
  "error": "Invitation code not found"
}
```

**Возможные ошибки:**
- `"Invitation code not found"`
- `"Invitation code has expired"`
- `"Invitation code has reached its usage limit"`
- `"Invitation code is inactive"`

---

### 3. Завершение регистрации

```http
POST /auth/onboarding/complete
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "invitation_code": "PUBLIC7",
  "first_name": "Иван",
  "last_name": "Петров",
  "middle_name": "Сергеевич",   // опционально
  "birth_date": "2010-05-15"    // опционально, ISO 8601
}
```

**Response:**
```json
{
  "access_token": "NEW_JWT_TOKEN",
  "refresh_token": "NEW_REFRESH_TOKEN",
  "token_type": "bearer",
  "user": {
    "id": 123,
    "school_id": 7,
    "first_name": "Иван",
    "last_name": "Петров"
    // ...
  },
  "student": {
    "id": 456,
    "student_code": "STU70724001",
    "grade_level": 7,
    "classes": [{"id": 45, "name": "7-А"}]
  }
}
```

**Важно:** После этого запроса нужно обновить сохранённые токены на новые!

---

### 4. Refresh Token

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "REFRESH_TOKEN"
}
```

**Response:**
```json
{
  "access_token": "NEW_ACCESS_TOKEN",
  "refresh_token": "NEW_REFRESH_TOKEN",
  "token_type": "bearer"
}
```

---

## User Flow

```
┌─────────────────────┐
│   Splash Screen     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    Login Screen     │
│  [Sign in with      │
│   Google] button    │
└──────────┬──────────┘
           │ Google SDK returns ID token
           ▼
┌─────────────────────┐
│  POST /auth/google  │
│  { id_token: "..." }│
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
requires_     requires_
onboarding    onboarding
= true        = false
     │           │
     ▼           ▼
┌─────────┐  ┌─────────┐
│Onboarding│  │  Home   │
│ Screen  │  │ Screen  │
└────┬────┘  └─────────┘
     │
     ▼
┌─────────────────────┐
│  Выбор класса       │
│  [7] [8] [9] [10] [11] │
│                     │
│  или                │
│  [У меня есть код]  │
└──────────┬──────────┘
           │ validate-code
           ▼
┌─────────────────────┐
│  Заполнение профиля │
│  - Фамилия *        │
│  - Имя *            │
│  - Отчество         │
│  - Дата рождения    │
│                     │
│  [Завершить]        │
└──────────┬──────────┘
           │ complete
           ▼
┌─────────────────────┐
│     Home Screen     │
└─────────────────────┘
```

---

## Коды для классов

| Класс | Код |
|-------|-----|
| 7 | `PUBLIC7` |
| 8 | `PUBLIC8` |
| 9 | `PUBLIC9` |
| 10 | `PUBLIC10` |
| 11 | `PUBLIC11` |

Эти коды публичные и не имеют ограничений по использованию.

---

## UI спецификация: Onboarding Screen

### Шаг 1: Выбор класса

```
┌────────────────────────────────┐
│                                │
│      Выберите ваш класс        │
│                                │
│   ┌─────┐  ┌─────┐  ┌─────┐   │
│   │  7  │  │  8  │  │  9  │   │
│   └─────┘  └─────┘  └─────┘   │
│                                │
│      ┌─────┐  ┌─────┐         │
│      │ 10  │  │ 11  │         │
│      └─────┘  └─────┘         │
│                                │
│   ─────────────────────────   │
│                                │
│   У меня есть код школы →     │
│                                │
└────────────────────────────────┘
```

**Действия:**
- Клик на кнопку класса → `POST /auth/onboarding/validate-code` с `PUBLIC{grade}`
- При успехе → Шаг 3
- При ошибке → показать alert

### Шаг 2: Ввод кода школы (опционально)

```
┌────────────────────────────────┐
│                                │
│   ←  Введите код школы         │
│                                │
│   ┌──────────────────────────┐ │
│   │                          │ │
│   └──────────────────────────┘ │
│                                │
│   Код выдаёт ваш учитель или   │
│   администратор школы          │
│                                │
│   ┌──────────────────────────┐ │
│   │       Продолжить         │ │
│   └──────────────────────────┘ │
│                                │
└────────────────────────────────┘
```

**Валидация:**
- Макс. длина: 12 символов
- При отправке → `POST /auth/onboarding/validate-code`
- При `valid: false` → показать `error` из response

### Шаг 3: Заполнение профиля

```
┌────────────────────────────────┐
│                                │
│   ←  Заполните профиль         │
│                                │
│   Фамилия *                    │
│   ┌──────────────────────────┐ │
│   │ Петров                   │ │
│   └──────────────────────────┘ │
│                                │
│   Имя *                        │
│   ┌──────────────────────────┐ │
│   │ Иван                     │ │
│   └──────────────────────────┘ │
│                                │
│   Отчество                     │
│   ┌──────────────────────────┐ │
│   │                          │ │
│   └──────────────────────────┘ │
│                                │
│   Дата рождения                │
│   ┌──────────────────────────┐ │
│   │ 15.05.2010               │ │
│   └──────────────────────────┘ │
│                                │
│   ┌──────────────────────────┐ │
│   │       Завершить          │ │
│   └──────────────────────────┘ │
│                                │
└────────────────────────────────┘
```

**Поля:**
- Фамилия — обязательное
- Имя — обязательное
- Отчество — опционально
- Дата рождения — опционально, date picker

**При отправке:**
- `POST /auth/onboarding/complete`
- Обновить токены
- Навигация на Home

---

## Хранение токенов

| Платформа | Где хранить |
|-----------|-------------|
| iOS | Keychain |
| Android | EncryptedSharedPreferences |

**Не использовать:** UserDefaults, SharedPreferences (незащищённые)

---

## Обработка ошибок

### HTTP 401 Unauthorized
1. Попробовать `POST /auth/refresh`
2. Если refresh успешен → повторить оригинальный запрос
3. Если refresh не успешен → очистить токены, redirect на Login

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

### HTTP 400 Business Error
```json
{
  "detail": "User already belongs to a school"
}
```

---

## Google Sign-In Integration

### iOS (GoogleSignIn)
```swift
// Pod: GoogleSignIn

GIDSignIn.sharedInstance.signIn(withPresenting: self) { result, error in
    guard let idToken = result?.user.idToken?.tokenString else { return }
    // Отправить idToken на backend
}
```

### Android (Play Services Auth)
```kotlin
// implementation 'com.google.android.gms:play-services-auth:20.7.0'

val signInIntent = googleSignInClient.signInIntent
startActivityForResult(signInIntent, RC_SIGN_IN)

// В onActivityResult:
val account = GoogleSignIn.getSignedInAccountFromIntent(data)
val idToken = account.result.idToken
// Отправить idToken на backend
```

---

## Конфигурация

### Настроенные Google Client IDs

| Платформа | Client ID | Статус |
|-----------|-----------|--------|
| Web | `471358699492-2b5jg1dtch12uf0e1lst0dqabf50k51i.apps.googleusercontent.com` | Активен |
| iOS | `471358699492-bk3tf3qabatma3jhe15mf7sp6vqeivd7.apps.googleusercontent.com` | Активен |
| Android | — | Не настроен |

Backend автоматически принимает токены от любого из настроенных Client ID.

### Добавление нового Client ID

1. Создать OAuth Client ID в [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Добавить в `backend/.env`:
   ```
   GOOGLE_CLIENT_ID_ANDROID=новый_client_id.apps.googleusercontent.com
   ```
3. Перезапустить backend:
   ```bash
   docker compose -f docker-compose.infra.yml up -d backend --force-recreate
   ```

---

## Checklist для тестирования

- [ ] Первый вход через Google → показывается выбор класса
- [ ] Повторный вход → сразу на главную (без onboarding)
- [ ] Выбор класса 7-11 работает корректно
- [ ] Ввод пользовательского кода работает
- [ ] Невалидный код показывает ошибку
- [ ] Профиль сохраняется корректно
- [ ] Токены обновляются после complete
- [ ] Refresh token работает при истечении access token
- [ ] Logout очищает токены
