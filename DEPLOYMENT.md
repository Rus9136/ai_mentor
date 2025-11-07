# AI Mentor - Production Deployment Guide

Полное руководство по развертыванию проекта AI Mentor на production сервере.

---

## Архитектура Production

```
┌─────────────────────────────────────────────────────────┐
│                    Internet                              │
└───────────────────┬─────────────────────────────────────┘
                    │ 80/443
                    ▼
         ┌──────────────────────┐
         │   Nginx (Reverse     │
         │   Proxy + SSL)       │
         └─────┬────────┬───────┘
               │        │
    ┌──────────┘        └───────────┐
    │                                │
    ▼                                ▼
┌─────────────┐              ┌─────────────┐
│  Frontend   │              │  Backend    │
│  (React)    │              │  (FastAPI)  │
│  Port: -    │              │  Port: 8000 │
└─────────────┘              └──────┬──────┘
                                    │
                                    ▼
                            ┌──────────────┐
                            │  PostgreSQL  │
                            │  + pgvector  │
                            │  Port: 5432  │
                            └──────────────┘
```

## Домены

- **ai-mentor.kz** - Student/Parent Portal
- **admin.ai-mentor.kz** - Admin Panel (SUPER_ADMIN & School ADMIN)
- **api.ai-mentor.kz** - Backend API + Docs

---

## Требования к серверу

### Минимальные характеристики:
- **OS:** Ubuntu 22.04 LTS или новее
- **CPU:** 4 cores (рекомендуется 8)
- **RAM:** 8 GB (рекомендуется 16 GB)
- **Диск:** 100 GB SSD
- **Сеть:** Статический IP адрес

### Установленное ПО:
- Docker 24.0+
- Docker Compose 2.0+
- Git
- OpenSSL

---

## Шаг 1: Настройка DNS

Создайте A-записи для всех доменов, указывающие на IP вашего сервера:

```
A    ai-mentor.kz           →  YOUR_SERVER_IP
A    www.ai-mentor.kz       →  YOUR_SERVER_IP
A    api.ai-mentor.kz       →  YOUR_SERVER_IP
A    admin.ai-mentor.kz     →  YOUR_SERVER_IP
```

Проверка:
```bash
nslookup ai-mentor.kz
nslookup api.ai-mentor.kz
nslookup admin.ai-mentor.kz
```

---

## Шаг 2: Подготовка сервера

### 2.1 Установка Docker

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo apt install docker-compose-plugin -y

# Проверка
docker --version
docker compose version
```

### 2.2 Настройка Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Проверка
sudo ufw status
```

### 2.3 Установка дополнительных утилит

```bash
sudo apt install -y git curl htop postgresql-client
```

---

## Шаг 3: Клонирование проекта

```bash
# Переход в рабочую директорию
cd /opt

# Клонирование репозитория
sudo git clone https://github.com/your-username/ai_mentor.git
cd ai_mentor

# Установка прав
sudo chown -R $USER:$USER /opt/ai_mentor
```

---

## Шаг 4: Настройка переменных окружения

### 4.1 Копирование шаблона

```bash
cp .env.production backend/.env
```

### 4.2 Редактирование backend/.env

```bash
nano backend/.env
```

**Обязательные изменения:**

```bash
# 1. SECRET_KEY - генерируем новый
openssl rand -hex 32
# Вставляем полученное значение:
SECRET_KEY=<сгенерированный_ключ>

# 2. POSTGRES_PASSWORD - сильный пароль
POSTGRES_PASSWORD=<минимум_32_символа>

# 3. DATABASE_URL - обновляем с новым паролем
DATABASE_URL=postgresql+asyncpg://ai_mentor_app:<ваш_пароль>@postgres:5432/ai_mentor_db

# 4. OPENAI_API_KEY
OPENAI_API_KEY=sk-<ваш_ключ>

# 5. CORS_ORIGINS - проверяем домены
CORS_ORIGINS=["https://ai-mentor.kz","https://admin.ai-mentor.kz","https://api.ai-mentor.kz"]
```

**Сохраните файл:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Шаг 5: Первоначальный деплой

### 5.1 Запуск скрипта деплоя

```bash
sudo chmod +x scripts/deploy.sh
sudo ./scripts/deploy.sh initial
```

Скрипт выполнит:
1. Проверку зависимостей
2. Проверку .env файла
3. Сборку Docker образов
4. Запуск PostgreSQL
5. Применение миграций
6. Запуск backend и frontend

### 5.2 Проверка статуса

```bash
# Проверка контейнеров
docker compose -f docker-compose.prod.yml ps

# Ожидаемый вывод:
# NAME                        STATUS
# ai_mentor_postgres_prod     Up (healthy)
# ai_mentor_backend_prod      Up
# ai_mentor_frontend_prod     Exited (0)
# ai_mentor_nginx_prod        Up

# Проверка логов
docker compose -f docker-compose.prod.yml logs backend
```

---

## Шаг 6: Настройка SSL сертификатов

### 6.1 Редактирование email в скрипте

```bash
nano scripts/ssl-setup.sh

# Измените строку:
EMAIL="admin@ai-mentor.kz"  # ваш реальный email
```

### 6.2 Запуск получения сертификатов

```bash
sudo chmod +x scripts/ssl-setup.sh
sudo ./scripts/ssl-setup.sh
```

Скрипт:
1. Проверит DNS записи
2. Запустит временный nginx
3. Получит SSL сертификаты через Let's Encrypt
4. Запустит production nginx с SSL

### 6.3 Проверка SSL

```bash
# Проверка сертификатов
curl -I https://api.ai-mentor.kz

# Должны увидеть: HTTP/2 200
```

---

## Шаг 7: Проверка работоспособности

### 7.1 Проверка доменов

Откройте в браузере:

- **https://api.ai-mentor.kz/docs** - Swagger документация API
- **https://api.ai-mentor.kz/health** - Health check
- **https://ai-mentor.kz** - Frontend (Student Portal)
- **https://admin.ai-mentor.kz** - Admin Panel

### 7.2 Тестовый логин

```bash
# API Test
curl -X POST https://api.ai-mentor.kz/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "superadmin@aimentor.com",
    "password": "admin123"
  }'

# Должен вернуть access_token
```

### 7.3 Проверка базы данных

```bash
# Подключение к PostgreSQL
docker compose -f docker-compose.prod.yml exec postgres psql -U ai_mentor_user -d ai_mentor_db

# Проверка таблиц
\dt

# Проверка пользователей
SELECT id, email, role FROM users LIMIT 5;

# Выход
\q
```

---

## Обновление проекта (Update)

Для обновления существующего деплоя:

```bash
# Pull последних изменений
cd /opt/ai_mentor
git pull origin main

# Запуск обновления
sudo ./scripts/deploy.sh update
```

Скрипт обновления:
1. Остановит сервисы (кроме БД)
2. Пересоберет образы
3. Применит новые миграции
4. Запустит обновленные сервисы

---

## Мониторинг и обслуживание

### Просмотр логов

```bash
# Все логи
docker compose -f docker-compose.prod.yml logs -f

# Только backend
docker compose -f docker-compose.prod.yml logs -f backend

# Только nginx
docker compose -f docker-compose.prod.yml logs -f nginx

# Последние 100 строк
docker compose -f docker-compose.prod.yml logs --tail=100
```

### Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Использование диска
df -h
docker system df
```

### Перезапуск сервисов

```bash
# Все сервисы
sudo ./scripts/deploy.sh restart

# Только backend
docker compose -f docker-compose.prod.yml restart backend

# Только nginx
docker compose -f docker-compose.prod.yml restart nginx
```

---

## Backup базы данных

### Создание backup

```bash
# Ручной backup
docker compose -f docker-compose.prod.yml exec postgres pg_dump \
  -U ai_mentor_user ai_mentor_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Сжатый backup
docker compose -f docker-compose.prod.yml exec postgres pg_dump \
  -U ai_mentor_user ai_mentor_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Восстановление backup

```bash
# Из несжатого backup
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U ai_mentor_user -d ai_mentor_db

# Из сжатого backup
gunzip -c backup.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U ai_mentor_user -d ai_mentor_db
```

### Автоматический backup (cron)

```bash
# Создаем скрипт backup
sudo nano /opt/ai_mentor/scripts/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/ai_mentor/backups"
mkdir -p $BACKUP_DIR

# Backup
cd /opt/ai_mentor
docker compose -f docker-compose.prod.yml exec -T postgres pg_dump \
  -U ai_mentor_user ai_mentor_db | \
  gzip > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Удаление старых backups (старше 30 дней)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

```bash
# Делаем скрипт исполняемым
sudo chmod +x /opt/ai_mentor/scripts/backup.sh

# Добавляем в cron (каждый день в 2:00 AM)
sudo crontab -e

# Добавляем строку:
0 2 * * * /opt/ai_mentor/scripts/backup.sh >> /var/log/ai_mentor_backup.log 2>&1
```

---

## Troubleshooting

### Контейнер не запускается

```bash
# Проверяем логи
docker compose -f docker-compose.prod.yml logs <service_name>

# Пересоздаем контейнер
docker compose -f docker-compose.prod.yml up -d --force-recreate <service_name>
```

### SSL сертификаты не работают

```bash
# Проверяем сертификаты
docker compose -f docker-compose.prod.yml exec certbot certbot certificates

# Пересоздаем сертификаты
sudo ./scripts/ssl-setup.sh
```

### База данных недоступна

```bash
# Проверяем состояние PostgreSQL
docker compose -f docker-compose.prod.yml ps postgres

# Проверяем логи
docker compose -f docker-compose.prod.yml logs postgres

# Перезапускаем
docker compose -f docker-compose.prod.yml restart postgres
```

### Nginx 502 Bad Gateway

```bash
# Проверяем, что backend работает
docker compose -f docker-compose.prod.yml ps backend

# Проверяем логи backend
docker compose -f docker-compose.prod.yml logs backend

# Тестируем backend напрямую (внутри сети)
docker compose -f docker-compose.prod.yml exec nginx curl http://backend:8000/health
```

---

## Security Checklist

- [ ] Все пароли изменены с дефолтных
- [ ] SECRET_KEY уникальный (минимум 32 символа)
- [ ] SSH доступ только по ключу (отключен пароль)
- [ ] Firewall настроен (только 22, 80, 443)
- [ ] SSL сертификаты установлены
- [ ] Автоматический backup настроен
- [ ] Логи мониторятся
- [ ] .env файлы не в Git
- [ ] Обновления системы применяются регулярно

---

## Полезные команды

```bash
# Полная очистка и перезапуск
docker compose -f docker-compose.prod.yml down -v
sudo ./scripts/deploy.sh initial

# Подключение к контейнеру
docker compose -f docker-compose.prod.yml exec backend bash
docker compose -f docker-compose.prod.yml exec postgres bash

# Копирование файлов из контейнера
docker compose -f docker-compose.prod.yml cp backend:/app/logs/app.log ./local_logs/

# Применение новых миграций вручную
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Откат миграции
docker compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```

---

## Контакты и поддержка

При возникновении проблем:
1. Проверьте логи: `docker compose -f docker-compose.prod.yml logs`
2. Проверьте секцию Troubleshooting
3. Создайте issue на GitHub

**Документация проекта:**
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Техническая архитектура
- [ADMIN_PANEL.md](docs/ADMIN_PANEL.md) - Админ панель
- [database_schema.md](docs/database_schema.md) - Схема БД
- [migrations_quick_guide.md](docs/migrations_quick_guide.md) - Миграции

---

## Changelog

- **2025-01-07** - Initial production deployment guide created
