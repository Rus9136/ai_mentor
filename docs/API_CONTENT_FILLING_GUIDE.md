# Руководство по программному заполнению контента через API

**Полная инструкция** по созданию учебников, глав и параграфов через REST API платформы AI Mentor.

---

## Содержание

1. [Авторизация и получение токена](#1-авторизация-и-получение-токена)
2. [Создание учебника](#2-создание-учебника)
3. [Создание глав](#3-создание-глав)
4. [Создание параграфов](#4-создание-параграфов)
5. [Полный пример на Python](#5-полный-пример-на-python)
6. [Полный пример на bash/cURL](#6-полный-пример-на-bashcurl)

---

## 1. Авторизация и получение токена

### Шаг 1.1: Login (получение access token)

**Endpoint:** `POST /api/v1/auth/login`

**Для SUPER_ADMIN (глобальный контент):**
```bash
curl -X POST https://api.ai-mentor.kz/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "superadmin@aimentor.com",
    "password": "admin123"
  }'
```

**Для School ADMIN (школьный контент):**
```bash
curl -X POST https://api.ai-mentor.kz/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "school.admin@test.com",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Сохраните `access_token`** - он нужен для всех последующих запросов.

---

## 2. Создание учебника

### Шаг 2.1: Создать новый учебник

**Для SUPER_ADMIN (глобальный учебник):**

**Endpoint:** `POST /api/v1/admin/global/textbooks`

```bash
curl -X POST https://api.ai-mentor.kz/api/v1/admin/global/textbooks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Алгебра 7 класс",
    "subject": "Математика",
    "grade_level": 7,
    "author": "А. Абылкасымова",
    "publisher": "Мектеп",
    "year": 2023,
    "isbn": "978-601-293-456-7",
    "description": "Учебник алгебры для 7 класса средней школы",
    "is_active": true
  }'
```

**Для School ADMIN (школьный учебник):**

**Endpoint:** `POST /api/v1/admin/school/textbooks`

```bash
curl -X POST https://api.ai-mentor.kz/api/v1/admin/school/textbooks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "История Казахстана 8 класс (Школа №1)",
    "subject": "История",
    "grade_level": 8,
    "author": "Школьный методист",
    "description": "Адаптированный учебник для нашей школы",
    "is_active": true
  }'
```

**Response:**
```json
{
  "id": 15,
  "school_id": null,
  "global_textbook_id": null,
  "is_customized": false,
  "version": 1,
  "source_version": null,
  "title": "Алгебра 7 класс",
  "subject": "Математика",
  "grade_level": 7,
  "author": "А. Абылкасымова",
  "publisher": "Мектеп",
  "year": 2023,
  "isbn": "978-601-293-456-7",
  "description": "Учебник алгебры для 7 класса средней школы",
  "is_active": true,
  "created_at": "2025-11-11T08:00:00Z",
  "updated_at": "2025-11-11T08:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

**Сохраните `id` учебника** (в примере: 15) - он нужен для создания глав.

### Шаг 2.2: Получить список учебников (опционально)

**SUPER_ADMIN:**
```bash
curl -X GET https://api.ai-mentor.kz/api/v1/admin/global/textbooks \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**School ADMIN:**
```bash
curl -X GET https://api.ai-mentor.kz/api/v1/admin/school/textbooks \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 3. Создание глав

### Шаг 3.1: Создать главу учебника

**Для SUPER_ADMIN:**

**Endpoint:** `POST /api/v1/admin/global/chapters`

```bash
curl -X POST https://api.ai-mentor.kz/api/v1/admin/global/chapters \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "textbook_id": 15,
    "title": "Линейные уравнения",
    "number": 1,
    "order": 1,
    "description": "Введение в линейные уравнения с одной переменной",
    "learning_objective": "Изучить методы решения линейных уравнений"
  }'
```

**Для School ADMIN:**

**Endpoint:** `POST /api/v1/admin/school/chapters`

```bash
curl -X POST https://api.ai-mentor.kz/api/v1/admin/school/chapters \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "textbook_id": 15,
    "title": "Жоңғар шапқыншылығы",
    "number": 1,
    "order": 1,
    "description": "XVIII ғасырдағы Жоңғар шапқыншылығы",
    "learning_objective": "Жоңғар шапқыншылығының тарихын зерттеу"
  }'
```

**Response:**
```json
{
  "id": 42,
  "textbook_id": 15,
  "title": "Линейные уравнения",
  "number": 1,
  "order": 1,
  "description": "Введение в линейные уравнения с одной переменной",
  "learning_objective": "Изучить методы решения линейных уравнений",
  "created_at": "2025-11-11T08:05:00Z",
  "updated_at": "2025-11-11T08:05:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

**Сохраните `id` главы** (в примере: 42) - он нужен для создания параграфов.

### Шаг 3.2: Получить главы учебника (опционально)

```bash
curl -X GET "https://api.ai-mentor.kz/api/v1/admin/global/textbooks/15/chapters" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 4. Создание параграфов

### Шаг 4.1: Создать параграф с полным набором полей

**Для SUPER_ADMIN:**

**Endpoint:** `POST /api/v1/admin/global/paragraphs`

```bash
curl -X POST https://api.ai-mentor.kz/api/v1/admin/global/paragraphs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "chapter_id": 42,
    "title": "Решение уравнений методом переноса",
    "number": 1,
    "order": 1,
    "content": "<h2>Метод переноса слагаемых</h2><p>При решении уравнений часто используется метод переноса слагаемых из одной части уравнения в другую...</p>",
    "summary": "Основы метода переноса слагаемых при решении линейных уравнений",
    "learning_objective": "Освоить метод переноса слагаемых",
    "lesson_objective": "Решить 10 уравнений методом переноса",
    "key_terms": [
      "уравнение",
      "переменная",
      "перенос слагаемых",
      "знак меняется"
    ],
    "questions": [
      {
        "order": 1,
        "text": "Что происходит со знаком слагаемого при переносе через знак равенства?"
      },
      {
        "order": 2,
        "text": "Решите уравнение: x + 5 = 12"
      },
      {
        "order": 3,
        "text": "Как проверить правильность решения уравнения?"
      }
    ]
  }'
```

**Для School ADMIN:**

**Endpoint:** `POST /api/v1/admin/school/paragraphs`

```bash
curl -X POST https://api.ai-mentor.kz/api/v1/admin/school/paragraphs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "chapter_id": 42,
    "title": "Ақтабан шұбырынды",
    "number": 1,
    "order": 1,
    "content": "<h2>Ақтабан шұбырынды оқиғасы</h2><p>XVIII ғасырдың басында қазақ халқы ауыр сынақтан өтті...</p>",
    "summary": "Жоңғар шапқыншылығының қазақ халқына әсері",
    "learning_objective": "Тарихи оқиғалардың себептері мен салдарын талдау",
    "lesson_objective": "Ақтабан шұбырынды оқиғасының хронологиясын білу",
    "key_terms": [
      "Жоңғар хандығы",
      "Ақтабан шұбырынды",
      "Аңырақай шайқасы",
      "Батыр"
    ],
    "questions": [
      {
        "order": 1,
        "text": "Ақтабан шұбырынды оқиғасы қай жылы болды?"
      },
      {
        "order": 2,
        "text": "Жоңғар шапқыншылығына қарсы күреске кімдер қатысты?"
      },
      {
        "order": 3,
        "text": "Аңырақай шайқасының маңызы неде?"
      }
    ]
  }'
```

**Response:**
```json
{
  "id": 128,
  "chapter_id": 42,
  "title": "Решение уравнений методом переноса",
  "number": 1,
  "order": 1,
  "content": "<h2>Метод переноса слагаемых</h2><p>При решении уравнений...</p>",
  "summary": "Основы метода переноса слагаемых при решении линейных уравнений",
  "learning_objective": "Освоить метод переноса слагаемых",
  "lesson_objective": "Решить 10 уравнений методом переноса",
  "key_terms": [
    "уравнение",
    "переменная",
    "перенос слагаемых",
    "знак меняется"
  ],
  "questions": [
    {
      "order": 1,
      "text": "Что происходит со знаком слагаемого при переносе через знак равенства?"
    },
    {
      "order": 2,
      "text": "Решите уравнение: x + 5 = 12"
    },
    {
      "order": 3,
      "text": "Как проверить правильность решения уравнения?"
    }
  ],
  "created_at": "2025-11-11T08:10:00Z",
  "updated_at": "2025-11-11T08:10:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

### Шаг 4.2: Получить параграфы главы (опционально)

```bash
curl -X GET "https://api.ai-mentor.kz/api/v1/admin/global/chapters/42/paragraphs" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 5. Полный пример на Python

### Установка зависимостей

```bash
pip install requests
```

### Python скрипт `fill_textbook.py`

```python
#!/usr/bin/env python3
"""
Скрипт для программного заполнения учебника через API AI Mentor.
"""
import requests
import json
from typing import Dict, List, Optional

# Конфигурация
API_URL = "https://api.ai-mentor.kz/api/v1"
# Выберите нужный тип админа:
IS_SUPER_ADMIN = True  # False для школьного админа

# Credentials
if IS_SUPER_ADMIN:
    EMAIL = "superadmin@aimentor.com"
    PASSWORD = "admin123"
else:
    EMAIL = "school.admin@test.com"
    PASSWORD = "admin123"


class ContentAPI:
    """Класс для работы с API контента."""

    def __init__(self, api_url: str, is_super_admin: bool = True):
        self.api_url = api_url
        self.is_super_admin = is_super_admin
        self.token: Optional[str] = None
        self.prefix = "admin/global" if is_super_admin else "admin/school"

    def login(self, email: str, password: str) -> str:
        """Авторизация и получение токена."""
        url = f"{self.api_url}/auth/login"
        response = requests.post(url, json={
            "email": email,
            "password": password
        })
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        print(f"✓ Авторизация успешна. Token получен.")
        return self.token

    def _headers(self) -> Dict[str, str]:
        """Заголовки с токеном."""
        if not self.token:
            raise ValueError("Сначала выполните login()")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def create_textbook(self, data: Dict) -> Dict:
        """Создать учебник."""
        url = f"{self.api_url}/{self.prefix}/textbooks"
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        result = response.json()
        print(f"✓ Учебник создан: ID={result['id']}, Title='{result['title']}'")
        return result

    def create_chapter(self, data: Dict) -> Dict:
        """Создать главу."""
        url = f"{self.api_url}/{self.prefix}/chapters"
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        result = response.json()
        print(f"  ✓ Глава создана: ID={result['id']}, Title='{result['title']}'")
        return result

    def create_paragraph(self, data: Dict) -> Dict:
        """Создать параграф."""
        url = f"{self.api_url}/{self.prefix}/paragraphs"
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        result = response.json()
        print(f"    ✓ Параграф создан: ID={result['id']}, Title='{result['title']}'")
        return result


def main():
    """Основная функция."""

    # Инициализация API
    api = ContentAPI(API_URL, is_super_admin=IS_SUPER_ADMIN)

    # 1. Авторизация
    print("\n=== ШАГ 1: Авторизация ===")
    api.login(EMAIL, PASSWORD)

    # 2. Создание учебника
    print("\n=== ШАГ 2: Создание учебника ===")
    textbook = api.create_textbook({
        "title": "История Казахстана 8 класс",
        "subject": "История",
        "grade_level": 8,
        "author": "К. Жумагулов",
        "publisher": "Атамура",
        "year": 2024,
        "description": "Учебник по истории Казахстана для 8 класса",
        "is_active": True
    })
    textbook_id = textbook["id"]

    # 3. Создание глав
    print("\n=== ШАГ 3: Создание глав ===")

    chapters_data = [
        {
            "textbook_id": textbook_id,
            "title": "Жоңғар шапқыншылығы",
            "number": 1,
            "order": 1,
            "description": "XVIII ғасырдағы Жоңғар шапқыншылығы және қазақ халқының қарсылық көрсетуі",
            "learning_objective": "Жоңғар шапқыншылығының тарихын және оның салдарларын зерттеу"
        },
        {
            "textbook_id": textbook_id,
            "title": "Қазақ хандығының нығаюы",
            "number": 2,
            "order": 2,
            "description": "XVIII ғасырдың екінші жартысында қазақ хандығының қалыптасуы",
            "learning_objective": "Қазақ хандығының дамуын талдау"
        }
    ]

    chapters = []
    for ch_data in chapters_data:
        chapter = api.create_chapter(ch_data)
        chapters.append(chapter)

    # 4. Создание параграфов для первой главы
    print("\n=== ШАГ 4: Создание параграфов ===")

    chapter_1_id = chapters[0]["id"]

    paragraphs_data = [
        {
            "chapter_id": chapter_1_id,
            "title": "Ақтабан шұбырынды оқиғасы",
            "number": 1,
            "order": 1,
            "content": """
<h2>Ақтабан шұбырынды оқиғасы</h2>

<p>XVIII ғасырдың басында (1723-1727 жылдары) қазақ халқы тарихындағы
ең қиын кезеңдердің бірі - "Ақтабан шұбырынды, Алқакөл сұлама" оқиғасы болды.</p>

<h3>Себептері</h3>
<ul>
<li>Жоңғар хандығының агрессивті саясаты</li>
<li>Қазақ хандығының ішкі бірліксіздігі</li>
<li>Қару-жарақ жағынан артта қалу</li>
</ul>

<h3>Салдары</h3>
<p>Бұл оқиға қазақ халқының ұлт-азаттық күресінің басталуына әкелді.</p>
            """,
            "summary": "Жоңғар шапқыншылығының қазақ халқына тигізген зардаптары",
            "learning_objective": "Тарихи оқиғалардың себептері мен салдарын талдау",
            "lesson_objective": "Ақтабан шұбырынды оқиғасының хронологиясын білу",
            "key_terms": [
                "Жоңғар хандығы",
                "Ақтабан шұбырынды",
                "Алқакөл сұлама",
                "ұлт-азаттық күрес"
            ],
            "questions": [
                {
                    "order": 1,
                    "text": "Ақтабан шұбырынды оқиғасы қай жылдары болды?"
                },
                {
                    "order": 2,
                    "text": "Жоңғар шапқыншылығының басты себептерін атаңыз."
                },
                {
                    "order": 3,
                    "text": "Бұл оқиғаның қазақ халқына тигізген әсері қандай болды?"
                }
            ]
        },
        {
            "chapter_id": chapter_1_id,
            "title": "Аңырақай шайқасы",
            "number": 2,
            "order": 2,
            "content": """
<h2>Аңырақай шайқасы (1730)</h2>

<p>1730 жылы өткен Аңырақай шайқасы қазақ халқының Жоңғарға қарсы
ұлт-азаттық күресінде шешуші рөл атқарды.</p>

<h3>Басты тұлғалар</h3>
<ul>
<li>Әбілқайыр хан - қазақ әскерінің басшысы</li>
<li>Бөгенбай батыр - батырлар басшысы</li>
<li>Қабанбай батыр</li>
<li>Жәнібек батыр</li>
</ul>
            """,
            "summary": "Аңырақай шайқасының жеңісі және оның маңызы",
            "learning_objective": "Тарихи шайқастардың стратегиялық маңызын түсіну",
            "lesson_objective": "Аңырақай шайқасының қатысушыларын білу",
            "key_terms": [
                "Аңырақай шайқасы",
                "Әбілқайыр хан",
                "Бөгенбай батыр",
                "жеңіс"
            ],
            "questions": [
                {
                    "order": 1,
                    "text": "Аңырақай шайқасы қай жылы болды?"
                },
                {
                    "order": 2,
                    "text": "Қазақ әскерінің басшысы кім болды?"
                },
                {
                    "order": 3,
                    "text": "Шайқаста қатысқан атақты батырларды атаңыз."
                }
            ]
        }
    ]

    for para_data in paragraphs_data:
        api.create_paragraph(para_data)

    print("\n" + "="*50)
    print("✓ Барлық контент сәтті жүктелді!")
    print(f"  Учебник ID: {textbook_id}")
    print(f"  Главы: {len(chapters)}")
    print(f"  Параграфы: {len(paragraphs_data)}")
    print("="*50)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
```

### Запуск скрипта

```bash
python3 fill_textbook.py
```

---

## 6. Полный пример на bash/cURL

### Bash скрипт `fill_textbook.sh`

```bash
#!/bin/bash
#
# Скрипт для заполнения учебника через API
#

set -e  # Exit on error

# Конфигурация
API_URL="https://api.ai-mentor.kz/api/v1"
EMAIL="superadmin@aimentor.com"
PASSWORD="admin123"
IS_SUPER_ADMIN=true  # false для школьного админа

if [ "$IS_SUPER_ADMIN" = true ]; then
    PREFIX="admin/global"
else
    PREFIX="admin/school"
fi

echo "========================================"
echo "  Заполнение учебника через API"
echo "========================================"

# ШАГ 1: Авторизация
echo -e "\n[1/4] Авторизация..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Ошибка авторизации!"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

echo "✓ Токен получен"

# ШАГ 2: Создание учебника
echo -e "\n[2/4] Создание учебника..."
TEXTBOOK_RESPONSE=$(curl -s -X POST "${API_URL}/${PREFIX}/textbooks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "title": "История Казахстана 8 класс",
    "subject": "История",
    "grade_level": 8,
    "author": "К. Жумагулов",
    "publisher": "Атамура",
    "year": 2024,
    "description": "Учебник по истории Казахстана",
    "is_active": true
  }')

TEXTBOOK_ID=$(echo "$TEXTBOOK_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$TEXTBOOK_ID" ]; then
    echo "❌ Ошибка создания учебника!"
    echo "$TEXTBOOK_RESPONSE"
    exit 1
fi

echo "✓ Учебник создан (ID: $TEXTBOOK_ID)"

# ШАГ 3: Создание главы
echo -e "\n[3/4] Создание главы..."
CHAPTER_RESPONSE=$(curl -s -X POST "${API_URL}/${PREFIX}/chapters" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d "{
    \"textbook_id\": ${TEXTBOOK_ID},
    \"title\": \"Жоңғар шапқыншылығы\",
    \"number\": 1,
    \"order\": 1,
    \"description\": \"XVIII ғасырдағы Жоңғар шапқыншылығы\",
    \"learning_objective\": \"Жоңғар шапқыншылығының тарихын зерттеу\"
  }")

CHAPTER_ID=$(echo "$CHAPTER_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$CHAPTER_ID" ]; then
    echo "❌ Ошибка создания главы!"
    echo "$CHAPTER_RESPONSE"
    exit 1
fi

echo "✓ Глава создана (ID: $CHAPTER_ID)"

# ШАГ 4: Создание параграфа
echo -e "\n[4/4] Создание параграфа..."
PARAGRAPH_RESPONSE=$(curl -s -X POST "${API_URL}/${PREFIX}/paragraphs" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d "{
    \"chapter_id\": ${CHAPTER_ID},
    \"title\": \"Ақтабан шұбырынды оқиғасы\",
    \"number\": 1,
    \"order\": 1,
    \"content\": \"<h2>Ақтабан шұбырынды оқиғасы</h2><p>XVIII ғасырдың басында...</p>\",
    \"summary\": \"Жоңғар шапқыншылығының қазақ халқына әсері\",
    \"learning_objective\": \"Тарихи оқиғалардың себептері мен салдарын талдау\",
    \"lesson_objective\": \"Оқиғаның хронологиясын білу\",
    \"key_terms\": [\"Жоңғар хандығы\", \"Ақтабан шұбырынды\", \"Батыр\"],
    \"questions\": [
      {\"order\": 1, \"text\": \"Ақтабан шұбырынды оқиғасы қай жылы болды?\"},
      {\"order\": 2, \"text\": \"Жоңғар шапқыншылығына қарсы күреске кімдер қатысты?\"}
    ]
  }")

PARAGRAPH_ID=$(echo "$PARAGRAPH_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$PARAGRAPH_ID" ]; then
    echo "❌ Ошибка создания параграфа!"
    echo "$PARAGRAPH_RESPONSE"
    exit 1
fi

echo "✓ Параграф создан (ID: $PARAGRAPH_ID)"

echo -e "\n========================================"
echo "  ✓ Контент успешно загружен!"
echo "========================================"
echo "  Учебник ID: $TEXTBOOK_ID"
echo "  Глава ID:   $CHAPTER_ID"
echo "  Параграф ID: $PARAGRAPH_ID"
echo "========================================"
```

### Запуск скрипта

```bash
chmod +x fill_textbook.sh
./fill_textbook.sh
```

---

## Итоговые endpoints

### Для SUPER_ADMIN (глобальный контент)

```
POST /api/v1/admin/global/textbooks      - Создать учебник
POST /api/v1/admin/global/chapters       - Создать главу
POST /api/v1/admin/global/paragraphs     - Создать параграф
GET  /api/v1/admin/global/textbooks      - Список учебников
GET  /api/v1/admin/global/textbooks/{id}/chapters  - Главы учебника
GET  /api/v1/admin/global/chapters/{id}/paragraphs - Параграфы главы
```

### Для School ADMIN (школьный контент)

```
POST /api/v1/admin/school/textbooks      - Создать учебник
POST /api/v1/admin/school/chapters       - Создать главу
POST /api/v1/admin/school/paragraphs     - Создать параграф
GET  /api/v1/admin/school/textbooks      - Список учебников
GET  /api/v1/admin/school/textbooks/{id}/chapters  - Главы учебника
GET  /api/v1/admin/school/chapters/{id}/paragraphs - Параграфы главы
```

---

## Полезные советы

### 1. Проверка токена

Если токен истек (обычно 30 минут), получите новый через `/auth/login`.

### 2. Формат content

Поле `content` в параграфе принимает HTML или Markdown:
- Используйте `<h2>`, `<p>`, `<ul>`, `<li>` для структуры
- Или Markdown: `## Заголовок`, `- Список`

### 3. key_terms и questions

- `key_terms` - простой массив строк
- `questions` - массив объектов с `order` и `text`
- Оба поля опциональны, можно не указывать

### 4. Batch операции

Для массовой загрузки создайте цикл в скрипте:
```python
for paragraph_data in bulk_paragraphs:
    api.create_paragraph(paragraph_data)
    time.sleep(0.1)  # Небольшая задержка
```

### 5. Swagger документация

Полная документация API доступна по адресу:
```
https://api.ai-mentor.kz/docs
```

---

**Готово!** Теперь вы можете программно заполнять учебники через API.
