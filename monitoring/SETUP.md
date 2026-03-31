# AI Mentor Monitoring Setup

## 1. UptimeRobot (внешний мониторинг + Telegram алерты)

### Регистрация
1. Зайти на https://uptimerobot.com и создать бесплатный аккаунт
2. Free план: 50 мониторов, проверка каждые 5 минут

### Создать мониторы

| Monitor Name | Type | URL | Expected |
|-------------|------|-----|----------|
| AI Mentor API Health | HTTP(s) - Keyword | `https://api.ai-mentor.kz/health/ready` | Keyword: `"healthy"` |
| AI Mentor Student App | HTTP(s) | `https://ai-mentor.kz` | Status 200 |
| AI Mentor Admin Panel | HTTP(s) | `https://admin.ai-mentor.kz` | Status 200 |
| AI Mentor Teacher App | HTTP(s) | `https://teacher.ai-mentor.kz` | Status 200 |
| AI Mentor Lab App | HTTP(s) | `https://lab.ai-mentor.kz` | Status 200 |

**Важно для API Health:** использовать тип "Keyword" и искать `"healthy"` в ответе. Если БД упадёт — ответ будет `"unhealthy"` → алерт.

### Telegram алерты
1. В Telegram: найти бота `@BotFather` → `/newbot` → получить токен
2. Создать группу/канал для алертов, добавить бота
3. Узнать chat_id: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. В UptimeRobot: My Settings → Alert Contacts → Add → Telegram
5. Привязать алерт контакт ко всем мониторам

### Результат
- Если любой сервис упадёт — уведомление в Telegram за 5 минут
- Dashboard со статусом всех сервисов: https://stats.uptimerobot.com/

---

## 2. Deep Health Endpoint (уже реализован)

Endpoint: `GET /health/ready`

Проверяет:
- **database** — PostgreSQL connectivity + latency
- **db_pool** — состояние connection pool (size, checked_in/out, overflow)
- **disk** — свободное место (warning >85%, critical >95%)
- **llm** — настроен ли LLM провайдер (API key)
- **uploads** — директория загрузок существует

Статусы ответа:
- `200` + `"healthy"` — всё ок
- `200` + `"degraded"` — работает, но есть проблемы (нет API key)
- `503` + `"unhealthy"` — критическая проблема (БД недоступна, диск полный)

---

## 3. Grafana Cloud (логи)

### Регистрация
1. Зайти на https://grafana.com/auth/sign-up (бесплатно)
2. Free tier: 50GB логов/месяц, 10k metrics, 14 дней retention

### Получить credentials
1. My Account → Grafana Cloud Portal
2. Выбрать Loki (Logs) → Details
3. Скопировать:
   - **URL**: `https://logs-prod-XXX.grafana.net/loki/api/v1/push`
   - **User**: числовой ID
   - **Password**: сгенерировать API key (Create API Key → Role: MetricsPublisher)

### Настройка на сервере
```bash
cd /home/rus/projects/ai_mentor/monitoring

# Создать файл с credentials
cp .env.monitoring.example .env.monitoring
nano .env.monitoring  # вставить реальные credentials

# Запустить Promtail
docker compose -f docker-compose.monitoring.yml up -d

# Проверить логи Promtail
docker logs ai_mentor_promtail --tail 20
```

### Проверка в Grafana Cloud
1. Зайти в Grafana Cloud → Explore → выбрать Loki
2. Query: `{job="ai_mentor"}`
3. Должны появиться логи всех контейнеров

### Полезные Loki запросы
```logql
# Все ошибки за последний час
{job="ai_mentor"} |= "ERROR"

# 500 ошибки
{job="ai_mentor"} |= "500"

# Логи конкретного контейнера
{job="ai_mentor", container_id=~".*backend.*"}

# Login attempts
{job="ai_mentor"} |= "auth/login"
```

### Алерты в Grafana
1. Alerting → Alert Rules → New Alert Rule
2. Query: `count_over_time({job="ai_mentor"} |= "ERROR" [5m]) > 10`
3. Contact point: Telegram (Grafana Alerting → Contact Points → Telegram)

---

## Проверка что всё работает

```bash
# 1. Deep health check
curl -s https://api.ai-mentor.kz/health/ready | python3 -m json.tool

# 2. UptimeRobot — проверить dashboard на uptimerobot.com

# 3. Promtail status
docker logs ai_mentor_promtail --tail 10
curl -s http://localhost:9080/ready  # должен вернуть "Ready"
```
