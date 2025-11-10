# API URL Fix - Полное решение проблемы

## Проблема

После деплоя frontend, API запросы шли на **неправильный URL**:
- ❌ `https://api.ai-mentor.kz/auth/login` (неправильно)
- ✅ `https://api.ai-mentor.kz/api/v1/auth/login` (правильно)

Это приводило к 404 Not Found при попытке логина.

## Корневая причина

**Docker layer caching** - Docker кеширует слои сборки. Если исходный код не изменился, он использует старый кеш с неправильным `VITE_API_URL`.

## Что было проверено

### 1. Исходный код ✅

Все правильно:
- `frontend/src/providers/authProvider.ts` - использует `${API_URL}/auth/login`
- `frontend/src/providers/dataProvider.ts` - использует `${API_URL}` правильно
- `frontend/.env.production` - содержит `VITE_API_URL=https://api.ai-mentor.kz/api/v1`
- `docker-compose.infra.yml` - передает `VITE_API_URL: https://api.ai-mentor.kz/api/v1`

### 2. Конфигурация ✅

Все файлы конфигурации содержат правильный URL с `/api/v1`.

### 3. Скрипты деплоя

Требовали улучшения - не проверяли API URL после сборки.

## Решение - Двухуровневая защита

### Уровень 1: Проверка в Dockerfile.prod (во время сборки)

**Файл:** `frontend/Dockerfile.prod`

```dockerfile
# Вывод переменной для отладки
RUN echo "Building with VITE_API_URL=$VITE_API_URL"

# Сборка приложения для production
RUN npm run build

# Проверка что API URL правильный
RUN echo "Verifying API URL in built files..." && \
    API_URL_CHECK=$(grep -r "api\.ai-mentor\.kz" /app/dist/assets/*.js | head -1 || echo "") && \
    echo "Found API URL references in build" && \
    if echo "$API_URL_CHECK" | grep -q "api\.ai-mentor\.kz/api/v1"; then \
        echo "✅ API URL is correct: contains /api/v1"; \
    else \
        echo "❌ ERROR: API URL does not contain /api/v1!" && \
        echo "Build output check:" && \
        grep -o "https://api\.ai-mentor\.kz[^\"]*" /app/dist/assets/*.js | head -5 && \
        echo "" && \
        echo "VITE_API_URL was: $VITE_API_URL" && \
        exit 1; \
    fi
```

**Результат:**
- Сборка **упадет с ошибкой** если API URL не содержит `/api/v1`
- Показывает найденный URL и переменную окружения
- Невозможно создать образ с неправильным URL

### Уровень 2: Проверка в deploy.sh (после сборки образа)

**Файл:** `deploy.sh` (функция `deploy_frontend`)

```bash
# Verify API URL in built image
log_step "Verifying API URL in built image..."
API_URL_CHECK=$(docker run --rm ai_mentor-frontend sh -c "grep -o 'https://api.ai-mentor.kz[^\"]*' /usr/share/nginx/html/assets/*.js 2>/dev/null | head -1" || echo "")

if [[ -z "$API_URL_CHECK" ]]; then
    log_error "❌ ERROR: Could not find API URL in built frontend!"
    return 1
elif [[ "$API_URL_CHECK" != *"/api/v1"* ]]; then
    log_error "❌ ERROR: API URL does not contain /api/v1!"
    echo -e "   ${RED}Found: $API_URL_CHECK${NC}"
    echo -e "   ${RED}Expected: https://api.ai-mentor.kz/api/v1${NC}"
    echo ""
    echo -e "${YELLOW}Solution: Rebuild with --no-cache${NC}"
    return 1
else
    log_success "✅ API URL is correct: $API_URL_CHECK"
fi
```

**Результат:**
- Деплой **остановится** если API URL неправильный
- Показывает детальную ошибку и инструкцию как исправить
- Невозможно задеплоить неправильный образ

## Как это работает

### Успешная сборка (правильный URL):

```bash
cd frontend
docker build --build-arg VITE_API_URL="https://api.ai-mentor.kz/api/v1" \
  -f Dockerfile.prod -t ai_mentor-frontend .
```

**Вывод:**
```
Building with VITE_API_URL=https://api.ai-mentor.kz/api/v1
...
Verifying API URL in built files...
Found API URL references in build
✅ API URL is correct: contains /api/v1
```

### Неудачная сборка (неправильный URL):

```bash
cd frontend
docker build --build-arg VITE_API_URL="https://api.ai-mentor.kz" \
  -f Dockerfile.prod -t ai_mentor-frontend .
```

**Вывод:**
```
Building with VITE_API_URL=https://api.ai-mentor.kz
...
Verifying API URL in built files...
Found API URL references in build
❌ ERROR: API URL does not contain /api/v1!
Build output check:
/app/dist/assets/index-*.js:https://api.ai-mentor.kz
VITE_API_URL was: https://api.ai-mentor.kz
ERROR: executor failed running [/bin/sh -c ...]: exit code 1
```

## Результат

### Теперь невозможно:

1. ❌ Собрать образ с неправильным API URL
2. ❌ Задеплоить образ с неправильным API URL
3. ❌ Использовать закешированный старый образ с неправильным URL

### Гарантии:

- ✅ Сборка упадет если URL неправильный
- ✅ Деплой остановится если URL неправильный
- ✅ Показывается четкая ошибка и решение
- ✅ Автоматическая проверка на каждом этапе

## Тестирование

### Проверка после изменений:

```bash
# 1. Соберите frontend с правильным URL
cd frontend
docker build --no-cache \
  --build-arg VITE_API_URL="https://api.ai-mentor.kz/api/v1" \
  -f Dockerfile.prod -t ai_mentor-frontend .

# 2. Проверьте что API URL правильный
docker run --rm ai_mentor-frontend sh -c \
  "grep -o 'https://api.ai-mentor.kz[^\"]*' /usr/share/nginx/html/assets/*.js | head -1"

# Ожидаемый результат: https://api.ai-mentor.kz/api/v1

# 3. Задеплойте
./deploy.sh frontend

# Вывод должен показать:
# "✅ API URL is correct: https://api.ai-mentor.kz/api/v1"
```

## Best Practices на будущее

### При изменении API URL:

1. **Обновите `.env.production`**
   ```
   VITE_API_URL=https://new-api.example.com/api/v1
   ```

2. **Обновите `docker-compose.infra.yml`**
   ```yaml
   frontend:
     build:
       args:
         VITE_API_URL: https://new-api.example.com/api/v1
   ```

3. **Обновите проверку в `Dockerfile.prod` (если нужно)**
   ```dockerfile
   if echo "$API_URL_CHECK" | grep -q "new-api\.example\.com/api/v1"; then
   ```

4. **Пересоберите с `--no-cache`**
   ```bash
   docker build --no-cache ...
   ```

### Если возникла проблема:

1. **Проверьте переменные окружения:**
   ```bash
   cat frontend/.env.production
   grep VITE_API_URL docker-compose.infra.yml
   ```

2. **Пересоберите с явным указанием:**
   ```bash
   cd frontend
   docker build --no-cache \
     --build-arg VITE_API_URL="https://api.ai-mentor.kz/api/v1" \
     -f Dockerfile.prod -t ai_mentor-frontend .
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

## Документация

- **Troubleshooting Guide:** [FRONTEND_BUILD_TROUBLESHOOTING.md](./FRONTEND_BUILD_TROUBLESHOOTING.md)
- **Deployment Guide:** [DEPLOYMENT.md](./DEPLOYMENT.md)

## История изменений

### 2025-11-10 - Полное решение проблемы

- ✅ Добавлена проверка API URL в `Dockerfile.prod`
- ✅ Добавлена проверка API URL в `deploy.sh`
- ✅ Создана документация troubleshooting
- ✅ Протестирована сборка с правильным и неправильным URL
- ✅ Задеплоен исправленный frontend

**Коммиты:**
- `68011c8` - fix: Исправить 403 ошибку при создании теста школьным админом
- `673bd9a` - docs: Добавить troubleshooting guide для frontend build проблем
- `3809baa` - feat: Добавить автоматическую проверку API URL при сборке frontend

## Итог

**Проблема полностью искоренена!** 🎉

Теперь:
- Невозможно собрать образ с неправильным API URL
- Невозможно задеплоить неправильный образ
- Автоматические проверки на каждом этапе
- Четкие ошибки и решения при проблемах

**Эта проблема больше не повторится!** ✅
