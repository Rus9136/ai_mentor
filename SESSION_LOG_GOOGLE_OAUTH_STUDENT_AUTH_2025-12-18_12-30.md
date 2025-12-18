# Session Log: Google OAuth + Student Authentication

**Дата:** 2025-12-18 12:30 - 14:05
**Задача:** Реализация Google OAuth авторизации для студентов с системой кодов приглашения

---

## Решения пользователя

| Вопрос | Выбор |
|--------|-------|
| OAuth метод | Google Identity Services (GIS) |
| URL студенческого приложения | ai-mentor.kz (заменить старый frontend) |
| Привязка к школе | Код приглашения от школьного админа |
| Индивидуальные ученики | Кнопка "Продолжить без школы" |

---

## Статус: ЗАДЕПЛОЕНО В PRODUCTION ✅

**Production URLs:**
- Student App: https://ai-mentor.kz/ru/login
- API: https://api.ai-mentor.kz

**Контейнер:** `ai_mentor_student_app_prod` на порту `127.0.0.1:3006`

---

## Выполненные задачи (Backend)

### 1. ✅ Миграция БД (015_add_oauth_and_invitation_codes.py)

**Файл:** `backend/alembic/versions/015_add_oauth_and_invitation_codes.py`

**Изменения в таблице `users`:**
- `auth_provider` (enum: local/google, default: local)
- `google_id` (varchar 255, unique, indexed)
- `avatar_url` (varchar 500)
- `password_hash` теперь nullable (для OAuth пользователей)

**Новая таблица `invitation_codes`:**
- id, code (unique), school_id, class_id
- grade_level (1-11), expires_at, max_uses, uses_count
- created_by, is_active, created_at, updated_at
- RLS policies для изоляции по школе

**Новая таблица `invitation_code_uses`:**
- id, invitation_code_id, student_id, created_at
- Аудит использования кодов

### 2. ✅ RLS Policy Fix для OAuth

**Проблема:** При Google OAuth регистрации пользователь создаётся с `school_id = NULL`, но RLS политика блокировала INSERT.

**Решение:** Обновлена политика `tenant_insert_policy` на таблице `users`:
```sql
CREATE POLICY tenant_insert_policy ON users
FOR INSERT
WITH CHECK (
    COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
    OR school_id IS NULL  -- Разрешить NULL для OAuth
    OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer
);
```

### 3. ✅ Модели, схемы, репозитории

- `backend/app/models/user.py` - OAuth поля
- `backend/app/models/invitation_code.py` - InvitationCode, InvitationCodeUse
- `backend/app/schemas/invitation_code.py` - все схемы
- `backend/app/repositories/invitation_code_repo.py` - CRUD + валидация
- `backend/app/repositories/user_repo.py` - get_by_google_id
- `backend/app/repositories/student_repo.py` - get_by_user_id, generate_student_code

### 4. ✅ Сервисы и Endpoints

- `backend/app/services/google_auth_service.py` - верификация Google ID token
- `backend/app/api/v1/auth_oauth.py` - OAuth endpoints
- `backend/app/api/v1/invitation_codes.py` - Admin CRUD для кодов

**OAuth Endpoints:**
| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/auth/google` | Google OAuth login/register |
| POST | `/auth/onboarding/validate-code` | Проверить код приглашения |
| POST | `/auth/onboarding/complete` | Завершить онбординг |

**Admin Endpoints:**
| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/admin/school/invitation-codes` | Список кодов школы |
| POST | `/admin/school/invitation-codes` | Создать код |
| GET | `/admin/school/invitation-codes/{id}` | Получить код |
| PATCH | `/admin/school/invitation-codes/{id}` | Обновить код |
| DELETE | `/admin/school/invitation-codes/{id}` | Деактивировать код |
| GET | `/admin/school/invitation-codes/{id}/uses` | История использования |

---

## Выполненные задачи (Frontend)

### 5. ✅ Student App (Next.js 16)

**Директория:** `student-app/`

**Структура:**
```
student-app/
├── package.json
├── next.config.ts
├── tailwind.config.ts
├── Dockerfile.prod
├── .env.local
├── messages/
│   ├── ru.json
│   └── kk.json
└── src/
    ├── app/[locale]/
    │   ├── layout.tsx
    │   ├── (auth)/login/page.tsx         # Google Sign-In
    │   ├── (auth)/onboarding/page.tsx    # Код + профиль + Skip
    │   └── (app)/page.tsx                # Dashboard
    ├── components/
    │   ├── ui/button.tsx, input.tsx, card.tsx
    │   └── auth/google-signin-button.tsx
    ├── lib/
    │   ├── api/client.ts                 # Axios + JWT interceptors
    │   ├── api/auth.ts                   # Auth API
    │   └── utils.ts
    ├── providers/
    │   └── auth-provider.tsx             # Auth context + skip logic
    └── i18n/
        ├── request.ts
        └── routing.ts
```

### 6. ✅ GoogleSignInButton Fix

**Проблема:** `buttonRef` был `null` когда скрипт загружался, т.к. показывался loading spinner вместо div.

**Решение:** Всегда рендерить div с ref, скрывать через CSS:
```tsx
return (
  <div className="flex justify-center">
    {isLoading && <LoadingSpinner />}
    <div ref={buttonRef} className={isLoading ? 'hidden' : ''} />
  </div>
);
```

### 7. ✅ Skip Onboarding Feature

**Для индивидуальных учеников без школы:**
- Кнопка "Продолжить без школы" на странице онбординга
- Сохранение флага в localStorage: `ai_mentor_skipped_onboarding`
- AuthProvider проверяет флаг и не редиректит на onboarding

---

## Выполненные задачи (Инфраструктура)

### 8. ✅ Docker Compose

**Файл:** `docker-compose.infra.yml`

Добавлен сервис `student-app`:
- **Порт:** `127.0.0.1:3006:3000` (изменён с 3004/3005 из-за конфликтов)
- Build args: NEXT_PUBLIC_API_URL, NEXT_PUBLIC_GOOGLE_CLIENT_ID

### 9. ✅ Nginx конфигурация

**Файл:** `nginx/ai-mentor.kz.conf` → `/etc/nginx/sites-enabled/ai-mentor-frontend.conf`

- Проксирование к student-app на порту 3006
- SSL настройки (Let's Encrypt)
- CSP для Google OAuth + Google Fonts
- Rate limiting

**CSP Header (финальный):**
```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://apis.google.com;
style-src 'self' 'unsafe-inline' https://accounts.google.com https://fonts.googleapis.com;
style-src-elem 'self' 'unsafe-inline' https://accounts.google.com https://fonts.googleapis.com;
img-src 'self' data: https: blob:;
font-src 'self' data: https://fonts.gstatic.com;
connect-src 'self' https://api.ai-mentor.kz https://accounts.google.com wss:;
frame-src https://accounts.google.com;
frame-ancestors 'self';
```

### 10. ✅ Google OAuth Credentials

**Google Cloud Console:**
- Project: AI Mentor
- OAuth 2.0 Client ID: `471358699492-2b5jg1dtch12uf0e1lst0dqabf50k51i.apps.googleusercontent.com`
- Authorized JavaScript origins: `https://ai-mentor.kz`

**Сохранено в:**
- `backend/.env`: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
- `student-app/.env.local`: NEXT_PUBLIC_GOOGLE_CLIENT_ID

---

## Исправленные проблемы

| Проблема | Решение |
|----------|---------|
| Порт 3004 занят (businessqoldau) | Изменён на 3005 |
| Порт 3005 занят (tco_admin) | Изменён на 3006 |
| CSP блокирует Google Fonts | Добавлен `fonts.googleapis.com` в style-src |
| CSP блокирует Google styles | Добавлен `accounts.google.com` в style-src-elem |
| buttonRef = null при загрузке | Всегда рендерить div, скрывать через CSS |
| RLS блокирует INSERT с NULL school_id | Обновлена политика: `OR school_id IS NULL` |
| Нет входа без школы | Добавлена кнопка "Продолжить без школы" |

---

## Auth Flow (финальный)

```
1. Пользователь открывает https://ai-mentor.kz/ru/login
2. Нажимает "Войти через Google"
3. GIS показывает popup → возвращает ID token
4. Frontend: POST /auth/google { id_token }
5. Backend:
   - Верифицирует токен через Google
   - Ищет user по google_id или email
   - Если нет → создаёт User (role=STUDENT, school_id=NULL)
   - Возвращает JWT + requires_onboarding=true
6. Frontend: redirect /onboarding
7. Пользователь выбирает:
   A) Ввести код приглашения → привязка к школе
   B) "Продолжить без школы" → индивидуальный ученик
8. Redirect на главную страницу /
```

---

## Файлы созданы/изменены

### Backend:
```
backend/alembic/versions/015_add_oauth_and_invitation_codes.py (создан)
backend/alembic/versions/016_fix_users_rls_for_oauth.py (создан)
backend/app/models/invitation_code.py (создан)
backend/app/schemas/invitation_code.py (создан)
backend/app/repositories/invitation_code_repo.py (создан)
backend/app/services/google_auth_service.py (создан)
backend/app/api/v1/auth_oauth.py (создан)
backend/app/api/v1/invitation_codes.py (создан)
backend/app/models/user.py (изменён)
backend/app/repositories/user_repo.py (изменён)
backend/app/repositories/student_repo.py (изменён)
backend/app/core/config.py (изменён)
backend/app/main.py (изменён)
backend/.env (изменён - добавлены Google credentials)
```

### Frontend:
```
student-app/ (весь проект создан)
student-app/.env.local (создан)
student-app/src/components/auth/google-signin-button.tsx (исправлен buttonRef)
student-app/src/app/[locale]/(auth)/onboarding/page.tsx (добавлен skip)
student-app/src/providers/auth-provider.tsx (добавлена логика skip)
student-app/messages/ru.json (добавлены переводы skip)
student-app/messages/kk.json (добавлены переводы skip)
```

### Инфраструктура:
```
docker-compose.infra.yml (добавлен student-app, порт 3006)
nginx/ai-mentor.kz.conf (создан, обновлён CSP)
/etc/nginx/sites-enabled/ai-mentor-frontend.conf (обновлён)
```

---

## Команды деплоя

```bash
# Сборка и запуск
GOOGLE_CLIENT_ID=471358699492-2b5jg1dtch12uf0e1lst0dqabf50k51i.apps.googleusercontent.com \
docker compose -f docker-compose.infra.yml build student-app

docker compose -f docker-compose.infra.yml up -d student-app

# Nginx
sudo cp nginx/ai-mentor.kz.conf /etc/nginx/sites-enabled/ai-mentor-frontend.conf
sudo nginx -t && sudo systemctl reload nginx

# Логи
docker logs ai_mentor_student_app_prod --tail 50
```

---

*Session by Claude Code*
