# SMS Интеграция — SMSC.kz

Документация для интеграции SMS-верификации при регистрации через провайдер [smsc.kz](https://smsc.kz).

---

## Содержание

1. [Обзор провайдера](#обзор-провайдера)
2. [Аутентификация](#аутентификация)
3. [API Endpoints](#api-endpoints)
4. [Отправка SMS](#отправка-sms)
5. [REST API (JSON)](#rest-api-json)
6. [Проверка статуса доставки](#проверка-статуса-доставки)
7. [Проверка баланса](#проверка-баланса)
8. [Callback (Webhook)](#callback-webhook)
9. [Коды ошибок](#коды-ошибок)
10. [Статусы доставки](#статусы-доставки)
11. [Лимиты и ограничения](#лимиты-и-ограничения)
12. [Имя отправителя (Sender ID)](#имя-отправителя-sender-id)
13. [Python клиент](#python-клиент)
14. [Архитектура для AI Mentor](#архитектура-для-ai-mentor)

---

## Обзор провайдера

| Параметр | Значение |
|----------|----------|
| Провайдер | SMSC.kz |
| Сайт | https://smsc.kz |
| Протоколы | HTTP/HTTPS, REST (JSON), SMTP, SMPP |
| Кодировка по умолчанию | windows-1251 (рекомендуем `charset=utf-8`) |
| Формат ответа | Text, CSV, XML, JSON (`fmt=3`) |

---

## Аутентификация

Два способа:

### 1. Login + Password
```
login=<логин>&psw=<пароль>
```

### 2. API Key (рекомендуется)
```
apikey=<ключ>
```

API-ключ генерируется в личном кабинете smsc.kz → Настройки → API.
Заменяет пару login+password — **предпочтительный способ для production**.

---

## API Endpoints

| Назначение | URL |
|------------|-----|
| Отправка SMS | `https://smsc.kz/sys/send.php` |
| REST отправка | `https://smsc.kz/rest/send/` |
| Статус доставки | `https://smsc.kz/sys/status.php` |
| Баланс | `https://smsc.kz/sys/balance.php` |
| Шаблоны | `https://smsc.kz/sys/templates.php` |
| Резервный хост | `https://www2.smsc.kz/sys/send.php` |

---

## Отправка SMS

### HTTP GET/POST

```
GET https://smsc.kz/sys/send.php?login=<login>&psw=<password>&phones=<phone>&mes=<message>&charset=utf-8&fmt=3
```

### Обязательные параметры

| Параметр | Описание |
|----------|----------|
| `login` | Логин аккаунта |
| `psw` | Пароль (или `apikey` вместо login+psw) |
| `phones` | Номер(а) телефона через запятую, формат: `77001234567` |
| `mes` | Текст сообщения (макс. 1000 символов) |

### Основные опциональные параметры

| Параметр | Значения | Описание |
|----------|----------|----------|
| `fmt` | 0,1,2,3 | Формат ответа: 0=text, 1=csv, 2=xml, **3=json** |
| `charset` | utf-8, windows-1251, koi8-r | Кодировка сообщения |
| `sender` | строка | Имя отправителя (до 11 латинских символов или 15 цифр) |
| `cost` | 0,1,2,3 | 0=без стоимости, 1=только стоимость, 2=+ID, 3=+баланс |
| `valid` | 1-24 | Время жизни SMS в часах |
| `time` | DDMMYYhhmm | Отложенная отправка |
| `id` | число | Пользовательский ID сообщения (1–2147483647) |
| `translit` | 0,1,2 | Транслитерация: 0=выкл, 1=латиница, 2=альт. |
| `flash` | 0,1 | Flash SMS (показывается сразу на экране) |
| `tinyurl` | 0,1 | Сокращение URL в тексте |
| `maxsms` | число | Максимум частей длинного SMS |
| `op` | 0,1 | Вернуть информацию об операторе |

### Пример запроса (JSON)

```bash
curl "https://smsc.kz/sys/send.php?apikey=YOUR_KEY&phones=77001234567&mes=Kod:1234&charset=utf-8&fmt=3&cost=3"
```

### Успешный ответ (fmt=3)

```json
{
  "id": 1234,
  "cnt": 1,
  "cost": "1.40",
  "balance": "100.50"
}
```

### Ответ с ошибкой

```json
{
  "error": "invalid login/password",
  "error_code": 2
}
```

---

## REST API (JSON)

### POST запрос

```
POST https://smsc.kz/rest/send/
Content-Type: application/json
```

### Тело запроса

```json
{
  "login": "<login>",
  "psw": "<password>",
  "phones": "77001234567",
  "mes": "Ваш код: 1234",
  "charset": "utf-8",
  "fmt": 3,
  "cost": 3,
  "sender": "AIMentor"
}
```

Или с API-ключом:

```json
{
  "apikey": "<api_key>",
  "phones": "77001234567",
  "mes": "Ваш код: 1234",
  "fmt": 3
}
```

### Успешный ответ

```json
{
  "id": 5678,
  "cnt": 1,
  "cost": "1.40",
  "balance": "98.60"
}
```

---

## Проверка статуса доставки

```
GET https://smsc.kz/sys/status.php?login=<login>&psw=<password>&phone=<phone>&id=<sms_id>&fmt=3&all=1
```

| Параметр | Описание |
|----------|----------|
| `phone` | Номер телефона получателя |
| `id` | ID сообщения (из ответа send) |
| `all` | 0=статус, 1=детали, 2=+оператор |
| `fmt` | Формат ответа |
| `del` | 1=удалить сообщение после проверки |

### Ответ (fmt=3, all=1)

```json
{
  "status": 1,
  "last_date": "14.03.2026 12:30:00",
  "err": 0
}
```

---

## Проверка баланса

```
GET https://smsc.kz/sys/balance.php?login=<login>&psw=<password>&fmt=3
```

### Ответ

```json
{
  "balance": "150.00",
  "currency": "KZT"
}
```

---

## Callback (Webhook)

Настраивается в личном кабинете → Настройки API → URL обработчика.

SMSC.kz отправляет POST/GET на указанный URL при смене статуса сообщения.

### Параметры callback-запроса

| Параметр | Описание |
|----------|----------|
| `phone` | Номер получателя |
| `id` | ID сообщения |
| `status` | Код статуса доставки |
| `time` | Время изменения статуса |
| `err` | Код ошибки (если есть) |
| `cost` | Стоимость сообщения |
| `sender` | Имя отправителя |

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 1 | Ошибка аутентификации (неверный формат запроса) |
| 2 | Неверный логин/пароль или IP заблокирован |
| 3 | Некорректный параметр запроса |
| 4 | IP-адрес заблокирован |
| 5 | Неверный формат сообщения |
| 6 | Сообщение отклонено (неверный номер/получатель) |
| 7 | Некорректный номер получателя |
| 8 | Недостаточно средств на балансе |
| 9 | Слишком много одновременных запросов (rate limit) |

---

## Статусы доставки

| Код | Статус | Описание |
|-----|--------|----------|
| 0 | Unknown | Неизвестен |
| 1 | Accepted | Принято оператором |
| 2 | Buffered | В буфере (ожидает доставки) |
| 3 | Sent | Отправлено |
| 4 | Delivered | **Доставлено** |
| 5 | Undelivered | Не доставлено |
| 6 | Rejected | Отклонено оператором |
| 7 | Failed | Ошибка доставки |

---

## Лимиты и ограничения

| Параметр | Значение |
|----------|----------|
| Макс. длина сообщения | 1000 символов |
| SMS латиница | 160 символов / 1 SMS |
| SMS кириллица | 70 символов / 1 SMS |
| Мультичасть (латиница) | 153 символа / часть |
| Мультичасть (кириллица) | 67 символов / часть |
| Одновременные запросы | Ограничено (ошибка 9 при превышении) |
| Sender ID (буквы) | до 11 символов |
| Sender ID (цифры) | до 15 цифр |

**Для OTP-кода** (`Ваш код: 1234` = 14 символов кириллицей) — всегда 1 SMS.

---

## Имя отправителя (Sender ID)

- Регистрируется в личном кабинете smsc.kz
- Требует одобрения (модерация)
- Только латинские буквы, цифры, пробелы, спецсимволы
- Для Казахстана нужна предварительная регистрация имени
- Рекомендуемое имя: **`AIMentor`** (8 символов, укладывается в лимит)

---

## Python клиент

SMSC.kz предоставляет готовый Python-класс (`smsc_api.py`).

### Основные методы

```python
class SMSC:
    def send_sms(self, phones, message, translit=0, time="", id=0, format=0, sender=False, query="")
    def get_sms_cost(self, phones, message, translit=0, format=0, sender=False, query="")
    def get_status(self, id, phone, all=0)
    def get_balance(self)
```

### Конфигурация

```python
SMSC_LOGIN = ""          # Логин
SMSC_PASSWORD = ""       # Пароль или API-ключ
SMSC_POST = False        # Использовать POST
SMSC_HTTPS = True        # Использовать HTTPS
SMSC_CHARSET = "utf-8"   # Кодировка
```

### Пример использования

```python
smsc = SMSC()
# Отправить SMS
result = smsc.send_sms("77001234567", "Ваш код: 1234", sender="AIMentor")
# Проверить баланс
balance = smsc.get_balance()
# Получить стоимость
cost = smsc.get_sms_cost("77001234567", "Ваш код: 1234")
# Проверить статус
status = smsc.get_status(sms_id, "77001234567")
```

> **Примечание:** Для нашего проекта лучше написать собственный async-клиент на `httpx`, т.к. готовая библиотека синхронная.

---

## Архитектура для AI Mentor

### Переменные окружения (.env)

```env
# SMSC.kz
SMSC_API_KEY=your_api_key_here
SMSC_SENDER=AIMentor
SMSC_BASE_URL=https://smsc.kz
```

### Конфигурация (backend/app/core/config.py)

```python
# SMS Provider
SMSC_API_KEY: str = ""
SMSC_SENDER: str = "AIMentor"
SMSC_BASE_URL: str = "https://smsc.kz"
SMS_CODE_LENGTH: int = 4
SMS_CODE_TTL_SECONDS: int = 300  # 5 минут
SMS_MAX_ATTEMPTS: int = 3
SMS_RATE_LIMIT_SECONDS: int = 60  # 1 запрос в минуту на номер
```

### Структура файлов

```
backend/app/
├── services/
│   └── sms_service.py          # Клиент SMSC.kz (async httpx)
├── api/v1/
│   └── auth_sms.py             # Endpoints: send_code, verify_code
├── schemas/
│   └── sms.py                  # Pydantic: SendCodeRequest, VerifyCodeRequest
└── models/
    └── sms_verification.py     # Модель: phone, code, expires_at, attempts
```

### Флоу верификации

```
1. POST /api/v1/auth/send-code  { phone: "77001234567" }
   → Генерация 4-значного кода
   → Сохранение в БД (phone, code_hash, expires_at, attempts=0)
   → Отправка SMS через SMSC.kz REST API
   → Ответ: { success: true, retry_after: 60 }

2. POST /api/v1/auth/verify-code  { phone: "77001234567", code: "1234" }
   → Проверка code_hash, expires_at, attempts < max
   → При успехе: создание/вход пользователя, JWT токен
   → При неудаче: attempts++, ответ с ошибкой
```

### Безопасность

- **Хэширование кода** — хранить `bcrypt(code)`, не plain text
- **Rate limiting** — 1 SMS в 60 секунд на номер
- **Макс. попыток** — 3 попытки ввода кода, затем блокировка
- **TTL** — код живёт 5 минут
- **Защита от перебора** — экспоненциальная задержка после ошибок
- **IP rate limit** — ограничение на уровне IP (через middleware)

### Пример async-клиента

```python
import httpx
from app.core.config import settings

class SMSCClient:
    """Async клиент для SMSC.kz API."""

    BASE_URL = "https://smsc.kz/rest/send/"

    async def send_sms(self, phone: str, message: str) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.BASE_URL,
                json={
                    "apikey": settings.SMSC_API_KEY,
                    "phones": phone,
                    "mes": message,
                    "fmt": 3,
                    "charset": "utf-8",
                    "sender": settings.SMSC_SENDER,
                    "cost": 3,
                },
            )
            data = response.json()
            if "error" in data:
                raise SMSCError(data["error"], data.get("error_code"))
            return data

    async def check_balance(self) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://smsc.kz/sys/balance.php",
                params={
                    "apikey": settings.SMSC_API_KEY,
                    "fmt": 3,
                },
            )
            return response.json().get("balance", "0")
```

---

## Что нужно сделать для запуска

1. **Регистрация** на [smsc.kz](https://smsc.kz) — создать аккаунт
2. **Пополнить баланс** — для отправки SMS в Казахстане
3. **Зарегистрировать Sender ID** — `AIMentor` (в личном кабинете)
4. **Сгенерировать API Key** — Настройки → API → Создать ключ
5. **Добавить в .env** — `SMSC_API_KEY=...`
6. **Whitelist IP** (опционально) — для доп. безопасности в настройках API
7. **Настроить callback URL** (опционально) — для отслеживания доставки
