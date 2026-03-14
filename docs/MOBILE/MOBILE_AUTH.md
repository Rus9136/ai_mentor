# API: Авторизация для мобильных приложений

Документация для мобильных разработчиков (iOS / Android).

**Base URL:** `https://api.ai-mentor.kz/api/v1`

---

## Способы авторизации

| Способ | Эндпоинт | Статус |
|--------|----------|--------|
| Телефон (регистрация) | `POST /auth/phone/register` | Активен |
| Телефон (вход) | `POST /auth/phone/login` | Активен |
| Google OAuth | `POST /auth/google` | Активен |
| Apple Sign In | `POST /auth/apple` | Активен |

Все способы возвращают одинаковую структуру: `access_token`, `refresh_token`, `user`, `requires_onboarding`.

---

## 1. Авторизация по телефону

### 1.1 Регистрация

```http
POST /auth/phone/register
Content-Type: application/json

{
  "phone": "+77001234567",
  "first_name": "Иван",
  "last_name": "Петров",
  "middle_name": "Сергеевич",  // опционально
  "password": "secret123"       // опционально (на будущее)
}
```

**Валидация phone:** формат `+7XXXXXXXXXX` (казахстанский, 12 символов с `+`).

**Response 200 (успех):**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "requires_onboarding": true,
  "user": {
    "id": 54,
    "email": "phone_+77001234567@phone.local",
    "role": "student",
    "first_name": "Иван",
    "last_name": "Петров",
    "middle_name": "Сергеевич",
    "school_id": null,
    "is_active": true,
    "is_verified": false,
    "avatar_url": null,
    "auth_provider": "phone",
    "phone": "+77001234567"
  }
}
```

**Ошибки:**

| HTTP | Код | Когда |
|------|-----|-------|
| 409 | `RES_002` | Номер уже зарегистрирован |
| 422 | — | Невалидный формат номера |

```json
// 409 — номер занят
{
  "code": "RES_002",
  "message": "Phone number already registered"
}

// 422 — невалидный формат
{
  "detail": [
    {
      "loc": ["body", "phone"],
      "msg": "Value error, Phone must be in +7XXXXXXXXXX format",
      "type": "value_error"
    }
  ]
}
```

### 1.2 Вход

```http
POST /auth/phone/login
Content-Type: application/json

{
  "phone": "+77001234567",
  "password": "secret123"  // опционально (пока не проверяется)
}
```

**Response 200 (успех):**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "requires_onboarding": true,
  "user": {
    "id": 54,
    "role": "student",
    "first_name": "Иван",
    "last_name": "Петров",
    "school_id": null,
    "auth_provider": "phone",
    "phone": "+77001234567"
  }
}
```

**Поле `requires_onboarding`:**
- `true` — пользователь не привязан к школе → показать экран онбординга
- `false` — пользователь уже в школе → перейти на главный экран

**Ошибки:**

| HTTP | Код | Когда |
|------|-----|-------|
| 401 | `AUTH_001` | Номер не зарегистрирован |
| 403 | `ACCESS_004` | Аккаунт деактивирован |

---

## 2. Google OAuth

```http
POST /auth/google
Content-Type: application/json

{
  "id_token": "GOOGLE_ID_TOKEN",
  "client_id": "MOBILE_CLIENT_ID"  // опционально
}
```

**Response:** та же структура (`access_token`, `refresh_token`, `user`, `requires_onboarding`).

Новому пользователю: `requires_onboarding: true`, `school_id: null`.
Существующему: `requires_onboarding: false`, `school_id: 7`.

---

## 3. Apple Sign In

```http
POST /auth/apple
Content-Type: application/json

{
  "identity_token": "APPLE_IDENTITY_TOKEN_JWT",
  "authorization_code": "AUTH_CODE",         // опционально
  "first_name": "Иван",                      // только при первом входе
  "last_name": "Петров",                      // только при первом входе
  "client_id": "BUNDLE_ID_OR_SERVICE_ID"     // опционально
}
```

**Важно:** Apple предоставляет имя пользователя **только при первом входе**. Если `first_name`/`last_name` доступны — обязательно передавайте их.

**Response:** та же структура (`access_token`, `refresh_token`, `user`, `requires_onboarding`).

---

## 4. Онбординг (привязка к школе)

После регистрации/входа, если `requires_onboarding: true`, нужно пройти онбординг.

**Все запросы онбординга требуют авторизации:** `Authorization: Bearer {access_token}`

### 4.1 Валидация кода

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

### 4.2 Завершение онбординга

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
    "id": 54,
    "school_id": 7,
    "first_name": "Иван",
    "last_name": "Петров",
    "role": "student"
  },
  "student": {
    "id": 456,
    "student_code": "STU70724001",
    "grade_level": 7,
    "classes": [],
    "pending_request": {
      "id": 12,
      "class_id": 45,
      "class_name": "7-А",
      "status": "pending"
    }
  }
}
```

**ВАЖНО:** После `complete` нужно **заменить сохранённые токены** на новые! Новые токены содержат обновлённый `school_id`.

### Публичные коды классов

| Класс | Код |
|-------|-----|
| 7 | `PUBLIC7` |
| 8 | `PUBLIC8` |
| 9 | `PUBLIC9` |
| 10 | `PUBLIC10` |
| 11 | `PUBLIC11` |

---

## 5. Refresh Token

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

**Сроки жизни токенов:**
- Access token: **30 минут**
- Refresh token: **7 дней**

---

## 6. Текущий пользователь

```http
GET /auth/me
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": 54,
  "email": "phone_+77001234567@phone.local",
  "role": "student",
  "first_name": "Иван",
  "last_name": "Петров",
  "middle_name": "Сергеевич",
  "school_id": 7,
  "is_active": true,
  "is_verified": true,
  "avatar_url": null,
  "auth_provider": "phone",
  "phone": "+77001234567"
}
```

---

## User Flow (все способы)

```
┌──────────────────────────────────┐
│          Login Screen            │
│                                  │
│  ┌────────────────────────────┐  │
│  │  Номер телефона            │  │
│  │  +7 ___  ___  __  __      │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────────────┐  │
│  │         Войти              │  │  ← POST /auth/phone/login
│  └────────────────────────────┘  │
│                                  │
│  Нет аккаунта? Регистрация →     │  ← POST /auth/phone/register
│                                  │
│  ─── или войти через ───         │
│                                  │
│   [G Google]    [ Apple]        │  ← POST /auth/google | /auth/apple
│                                  │
└──────────────┬───────────────────┘
               │
         ┌─────┴─────┐
         │           │
         ▼           ▼
   requires_     requires_
   onboarding    onboarding
   = true        = false
         │           │
         ▼           ▼
  ┌───────────┐  ┌──────────┐
  │ Onboarding│  │  Home    │
  │  Screen   │  │  Screen  │
  └─────┬─────┘  └──────────┘
        │
        ▼
  ┌─────────────────────────────┐
  │  Выбор класса               │
  │  [7] [8] [9] [10] [11]     │    ← validate-code с PUBLIC{N}
  │                             │
  │  или                        │
  │  [У меня есть код школы]    │    ← validate-code с кодом учителя
  └──────────────┬──────────────┘
                 │
                 ▼
  ┌─────────────────────────────┐
  │  Заполнение профиля         │
  │  - Фамилия *                │
  │  - Имя *                    │
  │  - Отчество                 │
  │  - Дата рождения            │
  │                             │
  │  [Завершить]                │    ← POST /auth/onboarding/complete
  └──────────────┬──────────────┘
                 │ обновить токены!
                 ▼
  ┌─────────────────────────────┐
  │         Home Screen         │
  └─────────────────────────────┘
```

---

## Обработка ошибок

### Формат ошибок API

```json
{
  "code": "AUTH_001",
  "message": "Phone number not registered",
  "detail": "Phone number not registered"
}
```

### Коды ошибок авторизации

| HTTP | Код | Описание |
|------|-----|----------|
| 401 | `AUTH_001` | Неверные учётные данные / номер не зарегистрирован |
| 401 | `AUTH_002` | Токен истёк |
| 401 | `AUTH_003` | Невалидный токен |
| 401 | `AUTH_007` | Невалидный refresh token |
| 403 | `ACCESS_004` | Аккаунт деактивирован |
| 409 | `RES_002` | Номер телефона уже зарегистрирован |
| 422 | — | Ошибка валидации (формат телефона, пропущено поле) |
| 429 | `RATE_001` | Слишком много запросов |

### HTTP 401 — Стратегия обновления токена

```
Любой запрос → 401
       │
       ▼
POST /auth/refresh
       │
  ┌────┴────┐
  ▼         ▼
200 OK    401/другая ошибка
  │         │
  ▼         ▼
Повторить   Очистить токены →
запрос      redirect на Login
```

---

## Хранение токенов

| Платформа | Где хранить | НЕ использовать |
|-----------|-------------|-----------------|
| iOS | **Keychain** | UserDefaults |
| Android | **EncryptedSharedPreferences** | SharedPreferences |

---

## Конфигурация Google Sign-In

### Настроенные Client IDs

| Платформа | Client ID | Статус |
|-----------|-----------|--------|
| Web | `471358699492-2b5jg1dtch12uf0e1lst0dqabf50k51i.apps.googleusercontent.com` | Активен |
| iOS | `471358699492-bk3tf3qabatma3jhe15mf7sp6vqeivd7.apps.googleusercontent.com` | Активен |
| Android | — | Не настроен |

### iOS (GoogleSignIn SDK)

```swift
GIDSignIn.sharedInstance.signIn(withPresenting: self) { result, error in
    guard let idToken = result?.user.idToken?.tokenString else { return }
    // POST /auth/google с { "id_token": idToken }
}
```

### Android (Play Services Auth)

```kotlin
val signInIntent = googleSignInClient.signInIntent
startActivityForResult(signInIntent, RC_SIGN_IN)

// В onActivityResult:
val account = GoogleSignIn.getSignedInAccountFromIntent(data)
val idToken = account.result.idToken
// POST /auth/google с { "id_token": idToken }
```

---

## Checklist для тестирования

### Phone Auth
- [ ] Регистрация с валидным номером +7XXXXXXXXXX
- [ ] Регистрация с невалидным номером → 422
- [ ] Повторная регистрация → 409 "Phone number already registered"
- [ ] Вход с зарегистрированным номером → 200
- [ ] Вход с незарегистрированным номером → 401
- [ ] После регистрации `requires_onboarding: true`

### Onboarding (общий для всех способов)
- [ ] validate-code с PUBLIC7 → valid: true
- [ ] validate-code с невалидным кодом → valid: false
- [ ] complete → новые токены с school_id
- [ ] Повторный вход после complete → `requires_onboarding: false`

### Tokens
- [ ] Refresh token обновляет оба токена
- [ ] Истёкший access token → 401 → refresh → повтор
- [ ] Истёкший refresh token → redirect на Login
