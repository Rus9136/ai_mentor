# AI Mentor - Production Deployment Guide

> Полное руководство по production деплою на сервере 207.180.243.173

**Дата последнего обновления:** 2025-11-08 (добавлен автоматический деплой)
**Статус:** ✅ Production работает стабильно

---

## 📊 Текущий статус Production

**Сервер:** 207.180.243.173 (ai-mentor.kz)
**Деплой:** 2025-11-08 06:54
**Инфраструктура:** Централизованная (`/home/rus/infrastructure/`)

### Работающие сервисы:

- ✅ **Backend API:** https://api.ai-mentor.kz/health
- ✅ **Frontend Portal:** https://ai-mentor.kz (Student/Parent)
- ✅ **Admin Panel:** https://admin.ai-mentor.kz
- ✅ **PostgreSQL:** ai_mentor_postgres_prod (14 migrations applied)
- ✅ **SSL:** Let's Encrypt (expires 2026-02-06)

### Docker контейнеры:

```bash
NAME                      STATUS        PORTS
ai_mentor_backend_prod    Up (healthy)  127.0.0.1:8006->8000/tcp
ai_mentor_postgres_prod   Up (healthy)  5432/tcp (internal only)
```

---

## 🏗️ Архитектура Production

### Как работает деплой:

```
Internet (HTTPS)
    │
    └─── Общий Nginx (207.180.243.173:80/443)
         │
         ├─── ai-mentor.kz ────────────► /var/www/ai-mentor/ (Static Files)
         │
         ├─── admin.ai-mentor.kz ──────► /var/www/ai-mentor/ (Static Files)
         │
         └─── api.ai-mentor.kz ────────► 127.0.0.1:8006 (Backend Docker)
                                                  │
                                                  ▼
                                          PostgreSQL + pgvector
                                          (Docker контейнер)
```

### Интеграция с инфраструктурой сервера:

- **Общий Nginx:** `/home/rus/infrastructure/nginx/`
- **Общий SSL (certbot):** Централизованно управляется
- **Docker сеть:** `infrastructure_network` (связь между проектами)
- **Backend порт:** 127.0.0.1:8006 (только localhost, не доступен извне)

---

## 📁 Что где находится

### На сервере:

```
/home/rus/infrastructure/
├── nginx/
│   └── sites-enabled/
│       ├── ai-mentor-api.conf       # API reverse proxy
│       ├── ai-mentor-frontend.conf  # Frontend static
│       └── ai-mentor-admin.conf     # Admin panel
└── [общие сервисы для всех проектов]

/home/rus/projects/ai_mentor/
├── deploy.sh                 # ✅ Умный деплой скрипт (рекомендуется)
├── .deploy-helpers.sh        # ✅ Вспомогательные функции
├── docker-compose.infra.yml  # ✅ PRODUCTION конфигурация
├── deploy-infra.sh           # ✅ Ручное управление
├── backend/
│   ├── .env                  # ✅ Production secrets (НЕ в Git!)
│   └── Dockerfile.prod       # Production build
├── frontend/
│   ├── .env.production       # Production API URL
│   └── Dockerfile.prod       # Production build
├── nginx/infra/              # Шаблоны конфигураций
│   ├── ai-mentor-api.conf
│   ├── ai-mentor-frontend.conf
│   └── ai-mentor-admin.conf
└── scripts/
    └── init_db.sql           # PostgreSQL init (2 роли)

/var/www/ai-mentor/           # Frontend собранные файлы
└── [index.html, assets/, etc.]

/etc/nginx/sites-enabled/     # Активные Nginx конфигурации
├── ai-mentor-api.conf -> /home/rus/infrastructure/nginx/sites-enabled/ai-mentor-api.conf
├── ai-mentor-frontend.conf -> /home/rus/infrastructure/nginx/sites-enabled/ai-mentor-frontend.conf
└── ai-mentor-admin.conf -> /home/rus/infrastructure/nginx/sites-enabled/ai-mentor-admin.conf

/etc/letsencrypt/live/ai-mentor.kz/  # SSL сертификаты
├── fullchain.pem
└── privkey.pem
```

### Актуальные файлы проекта:

| Файл | Статус | Назначение |
|------|--------|------------|
| `deploy.sh` | ✅ PRODUCTION | **Умный деплой скрипт** (рекомендуется) |
| `.deploy-helpers.sh` | ✅ PRODUCTION | Вспомогательные функции для деплоя |
| `docker-compose.infra.yml` | ✅ PRODUCTION | Основной файл для деплоя |
| `deploy-infra.sh` | ✅ PRODUCTION | Ручное управление инфраструктурой |
| `backend/.env` | ✅ PRODUCTION | Секреты (НЕ в Git!) |
| `frontend/.env.production` | ✅ PRODUCTION | API URL для сборки |
| `nginx/infra/*.conf` | ✅ PRODUCTION | Шаблоны конфигураций |
| `docker-compose.yml` | ⚠️ LOCAL DEV | Только для разработки |

---

## 🚀 Быстрые команды

### Управление сервисами:

```bash
cd /home/rus/projects/ai_mentor

# Запуск
./deploy-infra.sh start

# Статус
./deploy-infra.sh status

# Логи backend
./deploy-infra.sh logs backend

# Перезапуск
./deploy-infra.sh restart

# Остановка
./deploy-infra.sh stop
```

### Работа с БД:

```bash
# Применить миграции
./deploy-infra.sh migrate

# Backup БД
./deploy-infra.sh backup
# Результат: backup_YYYYMMDD_HHMMSS.sql

# Restore БД
./deploy-infra.sh restore backup_20251108_065400.sql

# Подключиться к БД
docker compose -f docker-compose.infra.yml exec postgres psql -U ai_mentor_user -d ai_mentor_db
```

### 🚀 Автоматический деплой (рекомендуется):

```bash
cd /home/rus/projects/ai_mentor

# 1. Pull новый код
git pull origin main

# 2. Умный деплой - автоматически определяет изменения
./deploy.sh
```

**Что делает автоматически:**
- 🔍 Анализирует `git diff` для определения что изменилось
- 📋 Показывает план деплоя (backend/frontend/migrations)
- 🚀 Собирает и деплоит **только** то что изменилось
- ✅ Проверяет healthcheck после деплоя
- 📊 Показывает детальный summary с временем

**Принудительный деплой конкретного компонента:**

```bash
./deploy.sh backend      # Только backend (15-30 сек)
./deploy.sh frontend     # Только frontend (50-90 сек)
./deploy.sh migrations   # Только миграции (5-15 сек)
./deploy.sh full         # Полный деплой всего (1-2 минуты)
```

**Примеры использования:**

```bash
# Изменил backend код
vim backend/app/api/v1/students.py
git add . && git commit -m "feat: новый API endpoint"
git pull && ./deploy.sh
# → Автоматически задеплоит только backend (15 сек)

# Изменил frontend UI
vim frontend/src/pages/Dashboard.tsx
git add . && git commit -m "fix: исправил UI"
git pull && ./deploy.sh
# → Автоматически задеплоит только frontend (50 сек)

# Добавил миграцию
vim backend/alembic/versions/015_add_field.py
git add . && git commit -m "feat: добавил поле в БД"
git pull && ./deploy.sh
# → Применит миграцию + пересоберёт backend
```

### Ручное управление (если нужен детальный контроль):

```bash
cd /home/rus/projects/ai_mentor

# Backend
./deploy-infra.sh build
./deploy-infra.sh restart
./deploy-infra.sh migrate

# Frontend
./deploy-infra.sh build-frontend
./deploy-infra.sh deploy-frontend
```

### Мониторинг:

```bash
# Docker статус
docker ps

# Ресурсы
docker stats ai_mentor_backend_prod ai_mentor_postgres_prod

# Логи Nginx
sudo tail -f /var/log/nginx/ai-mentor-api_access.log
sudo tail -f /var/log/nginx/error.log

# Health check API
curl https://api.ai-mentor.kz/health
```

---

## 📋 Пошаговая инструкция для нового деплоя

### Предварительные требования:

1. **DNS настроен** (A-записи на 207.180.243.173):
   - ai-mentor.kz
   - www.ai-mentor.kz
   - api.ai-mentor.kz
   - admin.ai-mentor.kz

2. **SSH доступ к серверу:** `ssh rus@207.180.243.173`

3. **Централизованная инфраструктура существует:**
   - `/home/rus/infrastructure/nginx/`
   - Docker сеть `infrastructure_network`
   - Общий certbot для SSL

---

### Шаг 1: Проверка инфраструктуры

```bash
# Проверить Docker сеть
docker network ls | grep infrastructure_network

# Проверить свободен ли порт 8006
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep 8006
```

---

### Шаг 2: Клонирование проекта

```bash
cd ~/projects
git clone <repository_url> ai_mentor
cd ai_mentor
```

---

### Шаг 3: Настройка переменных окружения

```bash
# Копировать шаблон
cp .env.production backend/.env

# Сгенерировать SECRET_KEY
openssl rand -hex 32

# Редактировать backend/.env
nano backend/.env
```

**Обязательно заполнить:**

```env
# Security
SECRET_KEY=<результат openssl rand -hex 32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=ai_mentor_db
POSTGRES_USER=ai_mentor_app
POSTGRES_PASSWORD=<минимум_32_символа>

# Application
ENVIRONMENT=production
DEBUG=False

# CORS (production domains)
BACKEND_CORS_ORIGINS=["https://ai-mentor.kz","https://www.ai-mentor.kz","https://admin.ai-mentor.kz","https://api.ai-mentor.kz"]

# OpenAI (опционально)
OPENAI_API_KEY=<ваш_ключ_если_нужен_RAG>
```

**Установить пароль БД в переменную окружения:**

```bash
export POSTGRES_PASSWORD="<тот_же_пароль>"
```

---

### Шаг 4: Получение SSL сертификатов

```bash
# Через общий certbot сервера
sudo certbot certonly --webroot \
    -w /var/www/certbot \
    -d ai-mentor.kz \
    -d www.ai-mentor.kz \
    -d api.ai-mentor.kz \
    -d admin.ai-mentor.kz \
    --email admin@ai-mentor.kz \
    --agree-tos \
    --no-eff-email
```

**Если `/var/www/certbot` не существует:**

```bash
sudo mkdir -p /var/www/certbot
sudo chown www-data:www-data /var/www/certbot
```

**Проверка сертификатов:**

```bash
sudo certbot certificates
```

---

### Шаг 5: Установка Nginx конфигураций

```bash
cd ~/projects/ai_mentor

# Вариант A: Через скрипт
./deploy-infra.sh install-nginx

# Вариант B: Вручную
sudo cp nginx/infra/ai-mentor-api.conf /home/rus/infrastructure/nginx/sites-enabled/
sudo cp nginx/infra/ai-mentor-frontend.conf /home/rus/infrastructure/nginx/sites-enabled/
sudo cp nginx/infra/ai-mentor-admin.conf /home/rus/infrastructure/nginx/sites-enabled/

# Активация конфигураций
sudo ln -sf /home/rus/infrastructure/nginx/sites-enabled/ai-mentor-api.conf /etc/nginx/sites-enabled/
sudo ln -sf /home/rus/infrastructure/nginx/sites-enabled/ai-mentor-frontend.conf /etc/nginx/sites-enabled/
sudo ln -sf /home/rus/infrastructure/nginx/sites-enabled/ai-mentor-admin.conf /etc/nginx/sites-enabled/

# Проверка и перезагрузка
sudo nginx -t
sudo systemctl reload nginx
```

---

### Шаг 6: Первоначальный деплой

```bash
cd ~/projects/ai_mentor

# Полный деплой (все в одном)
./deploy-infra.sh deploy
```

**Или пошагово:**

```bash
# 1. Сборка Docker образов
./deploy-infra.sh build

# 2. Запуск сервисов (PostgreSQL + Backend)
./deploy-infra.sh start

# 3. Ожидание запуска PostgreSQL
sleep 10

# 4. Применение миграций
./deploy-infra.sh migrate

# 5. Сборка frontend
./deploy-infra.sh build-frontend

# 6. Деплой frontend в /var/www/ai-mentor/
./deploy-infra.sh deploy-frontend
```

---

### Шаг 7: Проверка работоспособности

```bash
# Health check API
curl https://api.ai-mentor.kz/health
# Ожидаемый результат: {"status":"healthy","version":"0.1.0","project":"AI Mentor"}

# Проверка SSL
curl -I https://api.ai-mentor.kz
# Ожидаемый результат: HTTP/2 200

# Статус контейнеров
./deploy-infra.sh status
```

**Открыть в браузере:**

- https://api.ai-mentor.kz/docs (Swagger UI)
- https://ai-mentor.kz (Frontend Portal)
- https://admin.ai-mentor.kz (Admin Panel)

---

### Шаг 8: Тестовые пользователи

**Credentials (ИЗМЕНИТЬ ПОСЛЕ ДЕПЛОЯ!):**

- **SUPER_ADMIN:** superadmin@aimentor.com / admin123
- **School ADMIN:** school.admin@test.com / admin123

**Тест login через API:**

```bash
curl -X POST https://api.ai-mentor.kz/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@aimentor.com","password":"admin123"}'
```

---

## 🔧 Troubleshooting

### 1. Backend не работает (502 Bad Gateway)

```bash
# Проверить статус
./deploy-infra.sh status

# Проверить логи
./deploy-infra.sh logs backend

# Проверить порт 8006
netstat -tlnp | grep 8006

# Проверить health
curl http://127.0.0.1:8006/health

# Перезапустить
./deploy-infra.sh restart
```

### 2. Frontend не обновляется

```bash
# Пересобрать и развернуть
./deploy-infra.sh build-frontend
./deploy-infra.sh deploy-frontend

# Проверить права
ls -la /var/www/ai-mentor/

# Проверить Nginx конфигурацию
sudo nginx -t
sudo tail -f /var/log/nginx/ai-mentor-frontend_error.log

# Очистить cache браузера: Ctrl+Shift+R
```

### 3. Миграции не применяются

```bash
# Проверить подключение к БД
docker compose -f docker-compose.infra.yml exec postgres psql -U ai_mentor_user -d ai_mentor_db -c "\dt"

# Проверить текущую версию миграций
docker compose -f docker-compose.infra.yml exec backend alembic current

# Применить миграции вручную
docker compose -f docker-compose.infra.yml exec backend alembic upgrade head

# Проверить логи БД
docker compose -f docker-compose.infra.yml logs postgres
```

### 4. SSL не работает

```bash
# Проверить сертификаты
sudo certbot certificates

# Переполучить сертификат
sudo certbot certonly --webroot \
    -w /var/www/certbot \
    -d ai-mentor.kz \
    -d www.ai-mentor.kz \
    -d api.ai-mentor.kz \
    -d admin.ai-mentor.kz \
    --force-renewal

# Перезагрузить Nginx
sudo systemctl reload nginx
```

### 5. CORS ошибки

**Проблема:** Frontend не может подключиться к API

```bash
# Проверить backend/.env
cat backend/.env | grep BACKEND_CORS_ORIGINS
# Должно содержать все production домены

# Проверить Nginx (CORS должен управляться FastAPI, не Nginx)
sudo grep -n "add_header.*Access-Control" /etc/nginx/sites-enabled/ai-mentor-api.conf
# НЕ должно быть CORS headers в Nginx для API

# Перезапустить backend после изменения .env
./deploy-infra.sh restart
```

### 6. Docker контейнер падает

```bash
# Проверить логи
docker compose -f docker-compose.infra.yml logs backend

# Проверить ресурсы
docker stats

# Пересоздать контейнер
docker compose -f docker-compose.infra.yml up -d --force-recreate backend
```

---

## ⚙️ Важные технические детали

### PostgreSQL - ДВЕ роли:

1. **ai_mentor_user** (SUPERUSER)
   - Для миграций (alembic)
   - Может bypass RLS политики
   - Используется в `alembic.ini`

2. **ai_mentor_app** (обычный пользователь)
   - Для runtime приложения
   - RLS политики активны
   - Используется в `backend/.env` (POSTGRES_USER)

### Backend конфигурация:

- **Gunicorn:** 4 workers (Uvicorn workers)
- **Порт:** 127.0.0.1:8006 (только localhost)
- **Health check:** http://127.0.0.1:8006/health
- **Timeout:** 120 секунд

### Frontend:

- **Build tool:** Vite
- **Static files:** /var/www/ai-mentor/
- **SPA routing:** Nginx fallback to index.html
- **Cache:** 1 year для assets

### Nginx rate limiting:

- **API:** 60 req/min
- **Admin:** 30 req/min
- **Login endpoints:** Stricter (5 req/min)

---

## 🔒 Секреты и безопасность

### Критические переменные (backend/.env):

```env
SECRET_KEY=<32-byte hex>         # Для JWT токенов
POSTGRES_PASSWORD=<strong pass>  # БД пароль (минимум 32 символа)
OPENAI_API_KEY=<optional>        # Для RAG (опционально)
```

### Важные замечания:

1. **НЕ коммитить `backend/.env`** - должен быть в .gitignore
2. **Использовать сильные пароли** (32+ символов)
3. **Сменить тестовые пароли** сразу после деплоя
4. **SSL сертификаты** обновляются автоматически (certbot cron)
5. **Backend доступен ТОЛЬКО на localhost:8006** - не извне

---

## 📦 Backup стратегия

### Ручной backup:

```bash
cd ~/projects/ai_mentor

# Создать backup
./deploy-infra.sh backup
# Результат: backup_20251108_065400.sql

# Восстановить
./deploy-infra.sh restore backup_20251108_065400.sql
```

### Автоматический daily backup (настроить):

```bash
# Добавить в crontab
crontab -e

# Добавить строку (2:00 AM каждый день)
0 2 * * * cd /home/rus/projects/ai_mentor && ./deploy-infra.sh backup

# Или расширить общий скрипт инфраструктуры
nano /home/rus/infrastructure/backup.sh
```

---

## 📝 Чеклист после деплоя

- [ ] DNS настроен для всех доменов
- [ ] SSL сертификаты получены и активны
- [ ] PostgreSQL запущен и здоров
- [ ] Backend запущен на 127.0.0.1:8006
- [ ] Миграции применены (14/14)
- [ ] Frontend собран и задеплоен в /var/www/ai-mentor/
- [ ] Nginx конфигурации установлены
- [ ] API доступен (https://api.ai-mentor.kz/health)
- [ ] Frontend доступен (https://ai-mentor.kz)
- [ ] Admin panel доступен (https://admin.ai-mentor.kz)
- [ ] Login через API работает
- [ ] Тестовые пароли изменены
- [ ] Логи проверены на ошибки
- [ ] Backup настроен

---

## 🔗 Полезные ссылки

### Production URLs:

- **Frontend:** https://ai-mentor.kz
- **Admin Panel:** https://admin.ai-mentor.kz
- **API:** https://api.ai-mentor.kz
- **API Docs:** https://api.ai-mentor.kz/docs
- **Health Check:** https://api.ai-mentor.kz/health

### Документация проекта:

- [CLAUDE.md](CLAUDE.md) - Техническая документация, архитектура
- [SESSION_LOG_Production_Deploy_AI_Mentor_2025-11-08_06-54.md](SESSION_LOG_Production_Deploy_AI_Mentor_2025-11-08_06-54.md) - Полный лог деплоя

---

## 📞 Поддержка

### Логи для диагностики:

```bash
# Backend
./deploy-infra.sh logs backend

# PostgreSQL
docker compose -f docker-compose.infra.yml logs postgres

# Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/ai-mentor-api_access.log

# Docker stats
docker stats
```

### Команды для проверки:

```bash
# Проверка DNS
dig ai-mentor.kz +short

# Проверка SSL
curl -I https://api.ai-mentor.kz

# Проверка health
curl https://api.ai-mentor.kz/health

# Проверка контейнеров
docker compose -f docker-compose.infra.yml ps

# Проверка Nginx
sudo nginx -t
sudo systemctl status nginx
```

---

**Платформа AI Mentor работает в production!** 🚀

**Версия документа:** 1.1 (добавлен автоматический деплой ./deploy.sh)
**Последнее обновление:** 2025-11-08
