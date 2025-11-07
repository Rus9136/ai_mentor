# Quick Deploy Guide - AI Mentor

Быстрая инструкция для деплоя на production сервер (Ubuntu 22.04).

---

## Предварительные требования

1. **DNS настроен** (A-записи на IP сервера):
   - ai-mentor.kz
   - www.ai-mentor.kz
   - api.ai-mentor.kz
   - admin.ai-mentor.kz

2. **SSH доступ к серверу**

---

## На сервере (Ubuntu 22.04)

### 1. Установка Docker

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose
sudo apt install -y docker-compose-plugin

# Firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Клонирование проекта

```bash
cd /opt
sudo git clone https://github.com/your-username/ai_mentor.git
cd ai_mentor
sudo chown -R $USER:$USER /opt/ai_mentor
```

### 3. Настройка переменных окружения

```bash
# Копируем шаблон
cp .env.production backend/.env

# Генерируем SECRET_KEY
openssl rand -hex 32

# Редактируем backend/.env
nano backend/.env
```

**Обязательно изменить:**
```env
SECRET_KEY=<результат_openssl_rand_hex_32>
POSTGRES_PASSWORD=<минимум_32_символа>
DATABASE_URL=postgresql+asyncpg://ai_mentor_app:<ваш_пароль>@postgres:5432/ai_mentor_db
OPENAI_API_KEY=sk-<ваш_ключ>
```

Сохранить: `Ctrl+O`, `Enter`, `Ctrl+X`

### 4. Первоначальный деплой

```bash
sudo chmod +x scripts/deploy.sh scripts/ssl-setup.sh
sudo ./scripts/deploy.sh initial
```

**Ожидаемый вывод:**
```
[INFO] Проверка зависимостей...
[INFO] ✓ Все зависимости установлены
[INFO] Проверка .env файла...
[INFO] ✓ .env файл корректен
[INFO] Собираем Docker образы...
[INFO] Запускаем контейнеры...
[INFO] Применяем миграции базы данных...
[INFO] === DEPLOYMENT ЗАВЕРШЕН ===
```

### 5. Настройка SSL

```bash
# Редактируем email (для уведомлений Let's Encrypt)
nano scripts/ssl-setup.sh
# Измените: EMAIL="admin@ai-mentor.kz"

# Запускаем получение сертификатов
sudo ./scripts/ssl-setup.sh
```

**На вопрос "Продолжить?" ответить:** `y`

### 6. Проверка

Откройте в браузере:

- https://api.ai-mentor.kz/docs
- https://ai-mentor.kz
- https://admin.ai-mentor.kz

---

## Тестовый логин

**SUPER_ADMIN:**
- Email: superadmin@aimentor.com
- Password: admin123

**School ADMIN:**
- Email: school.admin@test.com
- Password: admin123

**⚠️ ВАЖНО:** Смените пароли сразу после первого входа!

---

## Полезные команды

```bash
# Статус сервисов
docker compose -f docker-compose.prod.yml ps

# Логи
docker compose -f docker-compose.prod.yml logs -f

# Логи только backend
docker compose -f docker-compose.prod.yml logs -f backend

# Перезапуск
sudo ./scripts/deploy.sh restart

# Обновление (после git pull)
sudo ./scripts/deploy.sh update
```

---

## Backup базы данных

```bash
# Создать backup
docker compose -f docker-compose.prod.yml exec postgres pg_dump \
  -U ai_mentor_user ai_mentor_db > backup_$(date +%Y%m%d).sql

# Восстановить backup
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U ai_mentor_user -d ai_mentor_db
```

---

## Troubleshooting

### Контейнер не работает

```bash
# Смотрим логи
docker compose -f docker-compose.prod.yml logs <service_name>

# Пересоздаем
docker compose -f docker-compose.prod.yml up -d --force-recreate <service_name>
```

### SSL не работает

```bash
# Проверяем сертификаты
docker compose -f docker-compose.prod.yml exec certbot certbot certificates

# Переполучаем
sudo ./scripts/ssl-setup.sh
```

### 502 Bad Gateway

```bash
# Проверяем backend
docker compose -f docker-compose.prod.yml ps backend
docker compose -f docker-compose.prod.yml logs backend

# Перезапускаем
docker compose -f docker-compose.prod.yml restart backend
```

---

## Полная документация

Для детальной информации читайте:
- [DEPLOYMENT.md](DEPLOYMENT.md) - полное руководство
- [PRODUCTION_SETUP_SUMMARY.md](PRODUCTION_SETUP_SUMMARY.md) - список созданных файлов

---

## Что дальше?

1. Настроить автоматический backup (cron)
2. Настроить мониторинг (опционально)
3. Сменить тестовые пароли
4. Добавить реальных пользователей через Admin Panel

**Готово! Проект в production.** 🚀
