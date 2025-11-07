# Production Setup - Summary

## Созданные файлы для production деплоя

### Docker конфигурация

1. **docker-compose.prod.yml**
   - Production Docker Compose конфигурация
   - Сервисы: postgres, backend, frontend, nginx, certbot
   - Volumes для данных, SSL сертификатов, логов
   - Health checks и restart policies

2. **backend/Dockerfile.prod**
   - Multi-stage build для оптимизации
   - Production зависимости (без dev packages)
   - Gunicorn + Uvicorn workers (4 workers)
   - Non-root пользователь для безопасности
   - Healthcheck встроен

3. **frontend/Dockerfile.prod**
   - Multi-stage build
   - npm ci для reproducible builds
   - Vite build для production
   - Минифицированные статические файлы

---

## Nginx конфигурация

4. **nginx/nginx.conf**
   - Главный nginx конфиг
   - Gzip compression
   - Security headers
   - Rate limiting zones
   - Worker processes optimization

5. **nginx/conf.d/api.conf**
   - Поддомен: **api.ai-mentor.kz**
   - Reverse proxy к backend:8000
   - SSL configuration
   - Rate limiting для API (10 req/s)
   - Stricter rate limiting для login (5 req/m)
   - CORS headers

6. **nginx/conf.d/frontend.conf**
   - Домен: **ai-mentor.kz** + www
   - Student/Parent Portal
   - SPA routing (React Router)
   - Static file caching (1 year)
   - CSP headers

7. **nginx/conf.d/admin.conf**
   - Поддомен: **admin.ai-mentor.kz**
   - Admin Panel (SUPER_ADMIN & School ADMIN)
   - Stricter security headers
   - Rate limiting
   - Опциональный IP whitelist

---

## Переменные окружения

8. **.env.production**
   - Шаблон production переменных окружения
   - Все обязательные настройки с комментариями
   - ВАЖНО: НЕ коммитить с реальными секретами!
   - Копировать в `backend/.env` на сервере

Критические переменные для изменения:
```bash
SECRET_KEY=<openssl rand -hex 32>
POSTGRES_PASSWORD=<минимум 32 символа>
OPENAI_API_KEY=<ваш ключ>
CORS_ORIGINS=["https://ai-mentor.kz",...]
```

---

## Скрипты деплоя

9. **scripts/deploy.sh**
   - Автоматизация деплоя
   - Режимы: initial, update, restart
   - Проверка зависимостей и .env
   - Сборка образов
   - Применение миграций
   - Мониторинг статуса

Использование:
```bash
# Первый деплой
sudo ./scripts/deploy.sh initial

# Обновление
sudo ./scripts/deploy.sh update

# Перезапуск
sudo ./scripts/deploy.sh restart
```

10. **scripts/ssl-setup.sh**
    - Получение SSL сертификатов через Let's Encrypt
    - Для всех доменов (ai-mentor.kz, api.ai-mentor.kz, admin.ai-mentor.kz)
    - Проверка DNS записей
    - Автоматическое обновление сертификатов (через certbot контейнер)

Использование:
```bash
sudo ./scripts/ssl-setup.sh
```

---

## Документация

11. **DEPLOYMENT.md**
    - Полное руководство по production деплою
    - Шаг за шагом инструкции
    - Требования к серверу
    - Настройка DNS, firewall, Docker
    - Backup и восстановление БД
    - Troubleshooting
    - Security checklist

---

## Git конфигурация

12. **.gitignore** (обновлен)
    - Добавлены production-специфичные исключения:
      - `backend/.env` (реальные секреты)
      - `nginx/ssl/*` (SSL сертификаты)
      - `nginx/logs/*` (логи)
      - `postgres_data/` (данные БД)
      - `*.pem`, `*.key`, `*.crt` (приватные ключи)
      - `backups/`, `*.sql` (backup файлы)

13. **.gitkeep файлы**
    - `nginx/ssl/.gitkeep`
    - `nginx/logs/.gitkeep`
    - `uploads/.gitkeep`
    - Сохраняют структуру директорий в Git

---

## Архитектура Production

```
Internet (HTTPS)
    │
    ├─── ai-mentor.kz ───────────► Nginx ─► Frontend (React SPA)
    │
    ├─── admin.ai-mentor.kz ─────► Nginx ─► Frontend (React Admin)
    │
    └─── api.ai-mentor.kz ───────► Nginx ─► Backend (FastAPI)
                                                    │
                                                    ▼
                                            PostgreSQL + pgvector
```

### Безопасность:
- ✅ SSL/TLS (Let's Encrypt)
- ✅ HTTPS редиректы
- ✅ Security headers (CSP, HSTS, X-Frame-Options)
- ✅ Rate limiting (API, Login endpoints)
- ✅ Non-root containers
- ✅ CORS ограничения

### Production ready features:
- ✅ Multi-stage Docker builds (оптимизация размера)
- ✅ Gunicorn + Uvicorn workers (4 workers)
- ✅ Health checks
- ✅ Auto-restart policies
- ✅ Gzip compression
- ✅ Static file caching
- ✅ SSL auto-renewal (certbot)
- ✅ Централизованное логирование

---

## Следующие шаги на сервере

### 1. Настройка DNS (перед деплоем)
```bash
# Создать A-записи:
ai-mentor.kz        → YOUR_SERVER_IP
www.ai-mentor.kz    → YOUR_SERVER_IP
api.ai-mentor.kz    → YOUR_SERVER_IP
admin.ai-mentor.kz  → YOUR_SERVER_IP
```

### 2. Клонирование и настройка
```bash
cd /opt
git clone https://github.com/your-username/ai_mentor.git
cd ai_mentor

# Настройка .env
cp .env.production backend/.env
nano backend/.env  # Заполнить SECRET_KEY, POSTGRES_PASSWORD, OPENAI_API_KEY
```

### 3. Первоначальный деплой
```bash
sudo ./scripts/deploy.sh initial
```

### 4. Настройка SSL
```bash
# Редактировать email в скрипте
nano scripts/ssl-setup.sh

sudo ./scripts/ssl-setup.sh
```

### 5. Проверка
```bash
# Открыть в браузере:
https://api.ai-mentor.kz/docs
https://ai-mentor.kz
https://admin.ai-mentor.kz
```

---

## Мониторинг после деплоя

```bash
# Статус контейнеров
docker compose -f docker-compose.prod.yml ps

# Логи
docker compose -f docker-compose.prod.yml logs -f

# Ресурсы
docker stats

# Проверка SSL
curl -I https://api.ai-mentor.kz
```

---

## Backup стратегия

### Автоматический daily backup
```bash
# Создать скрипт
nano scripts/backup.sh

# Добавить в cron (2:00 AM)
0 2 * * * /opt/ai_mentor/scripts/backup.sh
```

### Ручной backup
```bash
docker compose -f docker-compose.prod.yml exec postgres pg_dump \
  -U ai_mentor_user ai_mentor_db > backup.sql
```

---

## Важные замечания

1. **Секреты:**
   - НИКОГДА не коммитить `backend/.env` с реальными паролями
   - `.env.production` - только шаблон, НЕ реальные секреты
   - Использовать сильные пароли (32+ символов)

2. **SSL:**
   - Let's Encrypt сертификаты действительны 90 дней
   - Автоматическое обновление через certbot контейнер (каждые 12 часов)
   - Email для уведомлений: изменить в `scripts/ssl-setup.sh`

3. **База данных:**
   - ДВЕ роли: `ai_mentor_user` (миграции), `ai_mentor_app` (runtime)
   - Настроить регулярные backups
   - Мониторить размер БД: `docker system df`

4. **Обновления:**
   - `git pull` + `./scripts/deploy.sh update`
   - Миграции применяются автоматически
   - Zero-downtime: БД не останавливается

5. **Логи:**
   - Backend логи: `nginx/logs/api_access.log`
   - Nginx логи: `nginx/logs/frontend_access.log`, `admin_access.log`
   - Docker логи: `docker compose -f docker-compose.prod.yml logs`

---

## Тестовые credentials (Production)

**ВАЖНО:** После первого деплоя СРАЗУ поменять пароли для:

- SUPER_ADMIN: superadmin@aimentor.com / admin123
- School ADMIN: school.admin@test.com / admin123

```bash
# Или удалить тестовых пользователей и создать новых через API
```

---

## Чек-лист перед запуском

- [ ] DNS записи настроены
- [ ] `backend/.env` заполнен (SECRET_KEY, пароли, API ключи)
- [ ] Firewall настроен (80, 443, 22)
- [ ] Docker и Docker Compose установлены
- [ ] Email в `scripts/ssl-setup.sh` изменен
- [ ] Backup стратегия настроена
- [ ] Мониторинг настроен (опционально)

---

**Готово к production deployment!** 🚀

Следуйте инструкциям в [DEPLOYMENT.md](DEPLOYMENT.md) для полного руководства.
