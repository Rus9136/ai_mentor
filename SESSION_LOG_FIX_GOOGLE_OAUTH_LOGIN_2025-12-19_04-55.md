# Session Log: Fix Google OAuth Login Button

**Дата:** 2025-12-19 04:55
**Задача:** Исправить ошибку "Google Client ID not configured" на странице логина

## Проблема

На странице https://ai-mentor.kz/ru/login вместо кнопки Google отображалась ошибка:
```
Google Client ID not configured
```

## Анализ

1. **Компонент GoogleSignInButton** (`student-app/src/components/auth/google-signin-button.tsx`):
   - Использует `process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID`
   - Если переменная пустая, выводит ошибку "Google Client ID not configured"

2. **Dockerfile.prod** (`student-app/Dockerfile.prod`):
   - Принимает `NEXT_PUBLIC_GOOGLE_CLIENT_ID` как build ARG
   - Переменная должна быть передана во время сборки

3. **docker-compose.infra.yml**:
   ```yaml
   student-app:
     build:
       args:
         NEXT_PUBLIC_GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:-}
   ```
   - Ожидает `GOOGLE_CLIENT_ID` из окружения хоста

4. **Проверка контейнера**:
   ```bash
   docker inspect ai_mentor_student_app_prod | jq '.[0].Config.Env' | grep -i google
   # Результат: "NEXT_PUBLIC_GOOGLE_CLIENT_ID=",
   ```
   - Переменная была пустой!

5. **Google Client ID** найден в `backend/.env`:
   ```
   GOOGLE_CLIENT_ID=471358699492-2b5jg1dtch12uf0e1lst0dqabf50k51i.apps.googleusercontent.com
   ```

## Решение

### 1. Пересборка контейнера с передачей переменной

```bash
GOOGLE_CLIENT_ID=471358699492-2b5jg1dtch12uf0e1lst0dqabf50k51i.apps.googleusercontent.com \
  docker compose -f docker-compose.infra.yml build student-app

GOOGLE_CLIENT_ID=471358699492-2b5jg1dtch12uf0e1lst0dqabf50k51i.apps.googleusercontent.com \
  docker compose -f docker-compose.infra.yml up -d student-app
```

### 2. Создание корневого .env файла

Чтобы не передавать переменную вручную при каждом деплое, создан `.env` в корне проекта:

```bash
# /home/rus/projects/ai_mentor/.env
GOOGLE_CLIENT_ID=471358699492-2b5jg1dtch12uf0e1lst0dqabf50k51i.apps.googleusercontent.com
POSTGRES_PASSWORD=AiM3nt0r_Pr0d_S3cur3_P@ssw0rd_2025!
```

Docker-compose автоматически читает этот файл.

### 3. Проверка .gitignore

Файл `.env` уже был в `.gitignore` - секреты не попадут в git.

## Проверка

```bash
# Переменная в контейнере
docker inspect ai_mentor_student_app_prod | jq '.[0].Config.Env' | grep -i google
# "NEXT_PUBLIC_GOOGLE_CLIENT_ID=471358699492-2b5jg1dtch12uf0e1lst0dqabf50k51i.apps.googleusercontent.com"

# Страница логина работает
curl -s https://ai-mentor.kz/ru/login | grep -o "not configured" || echo "OK"
# OK
```

## Файлы

| Файл | Действие |
|------|----------|
| `/home/rus/projects/ai_mentor/.env` | Создан (docker-compose env vars) |
| `.gitignore` | Проверен (`.env` уже включён) |

## Результат

- Кнопка Google OAuth отображается корректно на странице логина
- Будущие деплои автоматически подхватят `GOOGLE_CLIENT_ID` из корневого `.env`

## Связанные файлы

- `student-app/src/components/auth/google-signin-button.tsx` - компонент кнопки
- `student-app/Dockerfile.prod` - сборка с ARG
- `docker-compose.infra.yml` - конфигурация сервисов
- `backend/.env` - исходное хранение Google Client ID
