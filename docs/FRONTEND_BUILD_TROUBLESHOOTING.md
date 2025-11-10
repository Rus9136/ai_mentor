# Frontend Build Troubleshooting

## Проблема: Неправильный API URL в production build

### Симптомы
- Frontend запросы идут на `https://api.ai-mentor.kz/auth/login` вместо `https://api.ai-mentor.kz/api/v1/auth/login`
- Ошибка 404 Not Found при попытке логина
- В собранных JS файлах API_URL = `"https://api.ai-mentor.kz"` вместо `"https://api.ai-mentor.kz/api/v1"`

### Причина

**Docker layer caching** - Docker кеширует слои сборки и если исходный код не изменился, использует закешированный слой с неправильными переменными окружения.

Процесс сборки в Dockerfile.prod:
```dockerfile
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build
```

Если `COPY . .` не изменился, Docker использует старый кеш для слоя `RUN npm run build`, который был собран с другим (или без) VITE_API_URL.

### Решение

#### Вариант 1: Принудительная пересборка с явным указанием переменной

```bash
cd frontend
docker build --no-cache \
  --build-arg VITE_API_URL="https://api.ai-mentor.kz/api/v1" \
  -f Dockerfile.prod \
  -t ai_mentor-frontend .
```

**Важно:**
- `--no-cache` сбрасывает ВСЕ слои
- `--build-arg` явно передает переменную окружения

#### Вариант 2: Использовать deploy.sh frontend

Скрипт `./deploy.sh frontend` автоматически пересобирает с правильными переменными из docker-compose.infra.yml.

#### Вариант 3: Убедиться что docker-compose.infra.yml передает переменные

Проверьте в docker-compose.infra.yml:

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile.prod
    args:
      # Production API URL - ВАЖНО: должен включать /api/v1
      VITE_API_URL: https://api.ai-mentor.kz/api/v1
```

### Проверка после сборки

#### 1. Проверить API URL в Docker образе

```bash
docker run --rm ai_mentor-frontend sh -c \
  "grep -o 'https://api.ai-mentor.kz[^\"]*' /usr/share/nginx/html/assets/*.js | head -5"
```

**Ожидаемый результат:**
```
/usr/share/nginx/html/assets/index-*.js:https://api.ai-mentor.kz/api/v1
/usr/share/nginx/html/assets/index-*.js:https://api.ai-mentor.kz/api/v1
```

**Неправильный результат (БАГ!):**
```
/usr/share/nginx/html/assets/index-*.js:https://api.ai-mentor.kz
```

#### 2. Проверить API URL в развернутых файлах

```bash
grep -o "https://api.ai-mentor.kz[^\"]*" /var/www/ai-mentor-admin/assets/*.js | head -5
```

#### 3. Проверить что API endpoint работает

```bash
curl -s "https://api.ai-mentor.kz/api/v1/health"
# Должен вернуть: {"status":"healthy"}
```

### Почему это происходит периодически?

1. **Изменили только код без пересборки образа** - Docker использует старый кеш
2. **Забыли передать build args** - Docker использует fallback значение из кода
3. **Изменили .env.production но не пересобрали** - Vite не видит новые переменные
4. **Использовали deploy.sh с кешем** - Скрипт не всегда делает --no-cache

### Best Practices

#### При деплое frontend всегда делайте:

1. **Проверьте переменные окружения:**
   ```bash
   cat frontend/.env.production
   # VITE_API_URL=https://api.ai-mentor.kz/api/v1
   ```

2. **Пересоберите с --no-cache если сомневаетесь:**
   ```bash
   cd frontend
   docker build --no-cache \
     --build-arg VITE_API_URL="https://api.ai-mentor.kz/api/v1" \
     -f Dockerfile.prod \
     -t ai_mentor-frontend .
   ```

3. **Проверьте собранный образ:**
   ```bash
   docker run --rm ai_mentor-frontend sh -c \
     "grep -o 'https://api.ai-mentor.kz[^\"]*' /usr/share/nginx/html/assets/*.js | head -1"
   ```

4. **Задеплойте:**
   ```bash
   ./deploy.sh frontend
   ```

5. **Проверьте развернутую версию:**
   ```bash
   grep -o "https://api.ai-mentor.kz[^\"]*" /var/www/ai-mentor-admin/assets/*.js | head -1
   ```

6. **Проверьте логин:**
   ```bash
   curl -s -X POST "https://api.ai-mentor.kz/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email":"superadmin@aimentor.com","password":"admin123"}'
   # Должен вернуть: {"access_token": "...", "refresh_token": "..."}
   ```

### Как предотвратить в будущем

#### Улучшение Dockerfile.prod

Добавьте проверку во время сборки:

```dockerfile
RUN npm run build

# Проверяем что API URL правильный
RUN if ! grep -q "https://api.ai-mentor.kz/api/v1" /app/dist/assets/*.js; then \
      echo "ERROR: API URL не содержит /api/v1!" && \
      echo "Найдено:" && \
      grep -o "https://api.ai-mentor.kz[^\"]*" /app/dist/assets/*.js | head -5 && \
      exit 1; \
    fi
```

Это сломает сборку если API URL неправильный.

#### Улучшение deploy.sh

Добавить автоматическую проверку после сборки:

```bash
# После сборки образа
echo "🔍 Проверка API URL в собранном образе..."
API_URL=$(docker run --rm ai_mentor-frontend sh -c \
  "grep -o 'https://api.ai-mentor.kz[^\"]*' /usr/share/nginx/html/assets/*.js | head -1")

if [[ "$API_URL" != *"/api/v1"* ]]; then
  echo "❌ ОШИБКА: API URL не содержит /api/v1!"
  echo "Найдено: $API_URL"
  exit 1
fi

echo "✅ API URL корректный: $API_URL"
```

### История инцидента (2025-11-10)

**Проблема:** После деплоя frontend, логин возвращал 404 ошибку.

**Причина:** Docker использовал закешированный слой сборки с API_URL без `/api/v1`.

**Решение:**
1. Пересобрали с `--no-cache` и явным `--build-arg`
2. Проверили что API URL правильный в образе
3. Задеплоили обновленные файлы
4. Подтвердили что логин работает

**Время решения:** ~30 минут

**Предотвращение:** Добавлен этот документ и улучшены процессы сборки.
