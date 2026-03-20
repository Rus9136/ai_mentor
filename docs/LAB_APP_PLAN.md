# Лаборатория — интерактивный режим обучения

## Идея

AI Mentor сегодня обучает через текст, тесты и чат с ИИ-репетитором. Но многие школьные предметы по своей природе визуальны и пространственны — история разворачивается на карте, химия живёт в трёхмерных молекулах, физика описывает движение тел. Текстовый формат не раскрывает эти предметы полностью.

**Лаборатория** — новый режим урока, где вместо чтения параграфа студент взаимодействует с предметом напрямую:

- **История Казахстана** — интерактивная карта с таймлайном эпох. Студент перематывает время и видит, как менялись территории ханств, где проходили торговые пути, где случались ключевые битвы. Каждая эпоха привязана к параграфу учебника.
- **Химия** — 3D-модели молекул. Можно вращать, приближать, изучать типы связей, запускать визуализацию реакций.
- **Физика** — симуляции: маятник, электрические цепи, оптика. Студент меняет параметры и видит результат.
- **Биология** — интерактивная анатомия: слои тканей, органеллы клетки, системы органов.
- **География** — рельеф и климатические зоны Казахстана с наложением данных.

Лаборатория не заменяет учебник — она дополняет его. После изучения параграфа студент переходит в лабораторию и «трогает руками» то, о чём читал. Внутри лаборатории встроены интерактивные задания (найди на карте, собери молекулу, настрой параметры), за которые начисляется XP.

### Техническая реализация

Лаборатория — отдельный фронтенд-сервис внутри монорепо, по аналогии с `student-app`, `teacher-app` и `admin-v2`. Деплоится на поддомен `lab.ai-mentor.kz`. Открывается из Flutter-приложения через WebView с передачей JWT-токена. Общается с существующим FastAPI-бэкендом.

### Почему отдельный фронтенд, а не раздел в student-app

1. **Тяжёлые зависимости** — Leaflet, 3Dmol.js, Matter.js значительно увеличат бандл student-app для всех студентов, даже тех, кто не пользуется лабораторией.
2. **Независимый деплой** — можно обновлять лабораторию без пересборки основного приложения.
3. **Разные паттерны UI** — лаборатория это полноэкранный canvas/карта, а не список карточек. Другая навигация, другой layout.
4. **Изоляция рисков** — баг в WebGL-рендеринге молекул не сломает домашние задания.

---

## Архитектура

### Место в монорепо

```
ai_mentor/
├── student-app/     # ai-mentor.kz        → порт 3006
├── teacher-app/     # teacher.ai-mentor.kz → порт 3007
├── admin-v2/        # admin.ai-mentor.kz   → порт 3003
├── lab-app/         # lab.ai-mentor.kz     → порт 3008  ← НОВЫЙ
├── backend/
└── docker-compose.infra.yml
```

### Стек технологий

| Слой | Технология | Обоснование |
|------|-----------|-------------|
| Framework | Next.js 15 (standalone) | Единый стек с остальными фронтендами, единый Dockerfile |
| React | React 19 | Та же версия что в student-app |
| Styling | Tailwind CSS + Radix UI | Те же UI-компоненты |
| State (серверный) | TanStack Query | Кеширование, дедупликация запросов |
| State (клиентский) | Zustand | Текущая эпоха, zoom, выбранный объект |
| i18n | next-intl (ru, kz) | Единообразие |
| Auth | JWT из localStorage | Тот же паттерн client.ts с interceptors |
| HTTP | Axios | Копия из student-app |

**Предметные библиотеки:**

| Предмет | Библиотека | Размер | Назначение |
|---------|-----------|--------|------------|
| История, География | Leaflet + react-leaflet | ~40 КБ | Интерактивная карта |
| Химия | 3Dmol.js | ~500 КБ | WebGL рендеринг молекул |
| Физика | Matter.js | ~80 КБ | 2D физический движок |
| Биология | Custom SVG (React) | — | Интерактивная анатомия |

### Файловая структура lab-app

```
lab-app/
├── package.json
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── Dockerfile.prod
│
├── public/
│   └── data/                         # Статический контент лабораторий
│       ├── history/
│       │   ├── epochs.json           # Список эпох с датами и описаниями
│       │   ├── golden_horde.geojson  # Территория Золотой Орды
│       │   ├── kazakh_khanate.geojson
│       │   ├── kokand_khanate.geojson
│       │   └── markers/              # Города, битвы, пути
│       │       ├── cities.json
│       │       ├── battles.json
│       │       └── trade_routes.json
│       ├── chemistry/
│       │   ├── molecules/            # MOL/PDB файлы
│       │   └── reactions/            # Конфигурации реакций
│       └── physics/
│           └── simulations.json      # Параметры симуляций
│
├── src/
│   ├── app/
│   │   └── [locale]/
│   │       ├── layout.tsx            # Root layout с провайдерами
│   │       ├── page.tsx              # Каталог лабораторий
│   │       ├── (auth)/
│   │       │   └── login/page.tsx    # Логин (или редирект в student-app)
│   │       └── lab/
│   │           └── [labId]/
│   │               ├── page.tsx      # Роутер по lab_type → нужный компонент
│   │               └── loading.tsx   # Skeleton загрузки
│   │
│   ├── components/
│   │   ├── ui/                       # Shadcn/ui компоненты
│   │   ├── lab/                      # Общие компоненты лаборатории
│   │   │   ├── LabCard.tsx           # Карточка в каталоге
│   │   │   ├── LabShell.tsx          # Общий layout (toolbar, sidebar)
│   │   │   ├── LabTaskDialog.tsx     # Модалка интерактивного задания
│   │   │   └── XPNotification.tsx    # Уведомление о полученном XP
│   │   │
│   │   ├── history/                  # Модуль «История»
│   │   │   ├── HistoryMap.tsx        # Leaflet карта Казахстана
│   │   │   ├── Timeline.tsx          # Слайдер эпох (перемотка времени)
│   │   │   ├── EpochInfo.tsx         # Боковая панель с описанием эпохи
│   │   │   ├── TerritoryLayer.tsx    # GeoJSON полигоны территорий
│   │   │   └── MapMarkers.tsx        # Маркеры городов, битв, путей
│   │   │
│   │   ├── chemistry/               # Модуль «Химия» (фаза 2)
│   │   │   ├── MoleculeViewer.tsx    # 3Dmol.js рендер
│   │   │   ├── BondInfo.tsx          # Информация о связях
│   │   │   └── ReactionSimulator.tsx # Визуализация реакции
│   │   │
│   │   ├── physics/                  # Модуль «Физика» (фаза 3)
│   │   │   ├── PendulumSim.tsx       # Маятник
│   │   │   ├── CircuitBuilder.tsx    # Электрические цепи
│   │   │   └── OpticsLab.tsx         # Линзы и зеркала
│   │   │
│   │   └── biology/                  # Модуль «Биология» (фаза 4)
│   │       ├── AnatomyViewer.tsx     # SVG-анатомия
│   │       └── CellExplorer.tsx      # Интерактивная клетка
│   │
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts            # Axios + JWT interceptors
│   │   │   └── lab.ts               # API функции лаборатории
│   │   └── utils/
│   │       ├── geojson.ts           # Работа с GeoJSON
│   │       └── coordinates.ts       # Преобразование координат
│   │
│   ├── providers/
│   │   ├── auth-provider.tsx        # JWT auth context
│   │   └── query-provider.tsx       # TanStack Query
│   │
│   ├── stores/
│   │   └── lab-store.ts             # Zustand: эпоха, zoom, selected object
│   │
│   ├── types/
│   │   └── lab.ts                   # TypeScript интерфейсы
│   │
│   ├── messages/
│   │   ├── ru.json                  # Русские переводы
│   │   └── kk.json                  # Казахские переводы
│   │
│   └── i18n/
│       ├── request.ts
│       └── routing.ts
│
└── middleware.ts                     # Locale routing + auth redirect
```

### Хранение контента

| Тип данных | Хранилище | Обоснование |
|-----------|-----------|-------------|
| GeoJSON карты (территории по эпохам) | `lab-app/public/data/history/` — статика в репо | JSON, удобно версионировать, ~1-5 МБ на эпоху |
| 3D молекулы (PDB/MOL) | `lab-app/public/data/chemistry/` — статика в репо | Стандартные форматы, 5-50 КБ на молекулу |
| Изображения анатомии | `uploads/lab-content/` на сервере | По аналогии с `uploads/textbook-images/` |
| Конфигурация симуляций | `labs.config` (JSONB в БД) | Малый объём, нужен CRUD через админку |
| Метаданные эпох (даты, описания) | `lab_epochs` таблица или JSONB | Привязка к `paragraph_id` учебника |

### Новые таблицы в БД

```sql
-- Лаборатории (создаёт SUPER_ADMIN)
CREATE TABLE labs (
    id SERIAL PRIMARY KEY,
    subject_id INT REFERENCES subjects(id),
    textbook_id INT REFERENCES textbooks(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    lab_type VARCHAR(50) NOT NULL,       -- 'map', 'molecule_3d', 'simulation', 'anatomy'
    config JSONB DEFAULT '{}',           -- конфигурация, специфичная для типа
    content_path VARCHAR(500),           -- путь к статическим данным
    is_active BOOLEAN DEFAULT true,
    school_id INT REFERENCES schools(id),-- NULL = глобальный контент
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Прогресс студента в лаборатории
CREATE TABLE lab_progress (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(id),
    lab_id INT REFERENCES labs(id),
    progress_data JSONB DEFAULT '{}',    -- explored items, scores по разделам
    xp_earned INT DEFAULT 0,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, lab_id)
);

-- Задания внутри лаборатории
CREATE TABLE lab_tasks (
    id SERIAL PRIMARY KEY,
    lab_id INT REFERENCES labs(id),
    title VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL,      -- 'find_on_map', 'order_events', 'build_molecule'
    task_data JSONB NOT NULL,            -- вопрос, варианты, правильный ответ
    xp_reward INT DEFAULT 10,
    order_index INT DEFAULT 0,
    paragraph_id INT REFERENCES paragraphs(id),  -- привязка к параграфу учебника
    created_at TIMESTAMP DEFAULT NOW()
);

-- Ответы студента на задания лаборатории
CREATE TABLE lab_task_answers (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(id),
    lab_task_id INT REFERENCES lab_tasks(id),
    answer_data JSONB NOT NULL,
    is_correct BOOLEAN NOT NULL,
    xp_earned INT DEFAULT 0,
    answered_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, lab_task_id)      -- одна попытка на задание
);
```

### API эндпоинты (FastAPI)

```
Префикс: /api/v1/students/lab/
Auth: STUDENT role (JWT)
```

| Метод | Эндпоинт | Описание |
|-------|---------|----------|
| `GET` | `/available` | Каталог доступных лабораторий (по textbook_id студента) |
| `GET` | `/{lab_id}` | Метаданные лаборатории + конфигурация |
| `GET` | `/{lab_id}/content` | Контент (GeoJSON, маркеры). Query: `?epoch=golden_horde` |
| `GET` | `/{lab_id}/progress` | Прогресс текущего студента |
| `POST` | `/{lab_id}/progress` | Обновить прогресс (explored epochs и т.д.) |
| `GET` | `/{lab_id}/tasks` | Список заданий лаборатории |
| `POST` | `/{lab_id}/tasks/{task_id}/answer` | Ответить на задание → is_correct + xp_earned |

**Бэкенд структура:**

```
backend/app/
├── api/v1/students/
│   └── lab.py                     # Router
├── services/
│   └── lab_service.py             # Бизнес-логика, проверка ответов, XP
├── repositories/
│   └── lab_repo.py                # CRUD
├── models/
│   └── lab.py                     # SQLAlchemy: Lab, LabProgress, LabTask, LabTaskAnswer
└── schemas/
    └── lab.py                     # Pydantic: LabResponse, LabTaskAnswer, ProgressUpdate
```

### Инфраструктура

**docker-compose.infra.yml** — новый сервис:

```yaml
lab-app:
  container_name: ai_mentor_lab_app_prod
  build:
    context: ./lab-app
    dockerfile: Dockerfile.prod
    args:
      - NEXT_PUBLIC_API_URL=https://api.ai-mentor.kz/api/v1
  ports:
    - "3008:3000"
  environment:
    - NODE_ENV=production
  networks:
    - infrastructure_network
  restart: unless-stopped
```

**Nginx** — новый server block:

```nginx
server {
    server_name lab.ai-mentor.kz;
    location / {
        proxy_pass http://127.0.0.1:3008;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }
    # SSL через certbot
}
```

**deploy.sh** — добавить секцию `lab-app`:

```bash
if [[ "$DEPLOY_TARGET" == "lab-app" ]] || changed_in "lab-app/"; then
    deploy_frontend "lab-app" "ai_mentor_lab_app_prod" 3008 "/ru"
fi
```

---

## План реализации по фазам

### Фаза 1. Скелет фронтенда — ВЫПОЛНЕНО (19.03.2026)

**Цель:** рабочий Next.js проект, который билдится, деплоится и открывается по адресу `lab.ai-mentor.kz`.

**Что сделано:**

1. Создан `lab-app/` (32 файла) на основе паттернов `student-app/`:
   - `package.json` — Next.js 15, React 19, Leaflet, react-leaflet, TanStack Query, Zustand
   - `next.config.ts` (standalone + next-intl), `tailwind.config.ts` (цвета AI Mentor)
   - `tsconfig.json`, `postcss.config.mjs`, `.gitignore`
   - `Dockerfile.prod` (multi-stage, node:20-alpine)
   - `middleware.ts` (locale routing, /kk → /kz редирект)

2. Страницы:
   - `/[locale]/page.tsx` — каталог лабораторий (4 карточки: История, Химия, Физика, Биология)
   - `/[locale]/lab/[labId]/page.tsx` — страница лаборатории с dynamic import карты
   - `/[locale]/(auth)/login/page.tsx` — логин
   - `/[locale]/webview/lab/[labId]/page.tsx` — WebView-версия без навигации (для Flutter)

3. Auth:
   - `auth-provider.tsx` с поддержкой `?token=xxx` из URL (WebView)
   - `client.ts` — JWT interceptors, fallback на student-app токены (shared session)
   - Токены: `ai_mentor_lab_access_token` / `ai_mentor_lab_refresh_token`

4. i18n: `ru.json` и `kk.json` с ключами для лаборатории, истории, логина

5. Компоненты истории (заготовки):
   - `HistoryLab.tsx` — главный компонент (карта + таймлайн + сайдбар)
   - `HistoryMap.tsx` — Leaflet карта Казахстана (CartoDB tiles)
   - `Timeline.tsx` — слайдер эпох с цветовыми точками
   - `EpochInfo.tsx` — боковая панель с описанием эпохи
   - `epochs-data.ts` — 7 исторических эпох (от саков до независимости)

6. Инфраструктура:
   - `docker-compose.infra.yml` — добавлен сервис `lab-app` (порт 3008), CORS для `lab.ai-mentor.kz`
   - `deploy.sh` — режим `./deploy.sh lab-app`, авто-детекция изменений, health check, usage

7. `next build` компилируется успешно — 7 страниц, 145 КБ First Load JS

**Осталось для продакшена:** Nginx конфиг (`lab.ai-mentor.kz → localhost:3008`) + SSL через certbot.

---

### Фаза 2. Бэкенд API — ВЫПОЛНЕНО (19.03.2026)

**Цель:** API для лабораторий готов, данные можно создавать и получать.

**Что сделано:**

1. Миграция БД `064_labs.py`:
   - 4 таблицы: `labs`, `lab_progress`, `lab_tasks`, `lab_task_answers`
   - GRANT для `ai_mentor_app` (SELECT, INSERT, UPDATE, DELETE + sequences)
   - Unique constraints: `(student_id, lab_id)` в progress, `(student_id, lab_task_id)` в answers
   - Применена к продакшен БД, alembic version = `064_labs`

2. SQLAlchemy модели — `backend/app/models/lab.py`:
   - `Lab` (subject_id, textbook_id, lab_type, config JSONB, school_id)
   - `LabProgress` (student_id, lab_id, progress_data JSONB, xp_earned)
   - `LabTask` (lab_id, task_type, task_data JSONB, xp_reward, paragraph_id)
   - `LabTaskAnswer` (student_id, lab_task_id, answer_data JSONB, is_correct, xp_earned)

3. Pydantic schemas — `backend/app/schemas/lab.py`:
   - `LabResponse`, `LabProgressResponse`, `LabTaskResponse`, `LabTaskAnswerResult`
   - `ProgressUpdateRequest`, `TaskAnswerRequest`

4. Repository — `backend/app/repositories/lab_repo.py`:
   - CRUD для labs, progress (upsert), tasks, answers
   - `selectinload` для eager loading

5. Service — `backend/app/services/lab_service.py`:
   - Бизнес-логика с проверкой 4 типов ответов: `quiz`, `choose_epoch`, `order_events`, `find_on_map`
   - Идемпотентность ответов (повторный ответ возвращает результат без XP)
   - Автоматическое обновление XP в progress

6. API Router — `backend/app/api/v1/students/lab.py` (6 эндпоинтов):
   - Зарегистрирован в `students/__init__.py`

7. Тестовые данные:
   - Lab id=1: «Қазақстан тарихы — интерактивті карта» (subject_id=1, textbook_id=25)

**Проверено:** все 6 эндпоинтов отвечают корректно с реальным JWT токеном студента.

**Не реализовано (отложено):** SUPER_ADMIN API для CRUD лабораторий — пока лабы создаются через SQL.

---

### Фаза 2.5. Деплой фронтенда lab.ai-mentor.kz — ВЫПОЛНЕНО (20.03.2026)

**Цель:** lab-app доступен по адресу `https://lab.ai-mentor.kz` с валидным SSL.

**Что сделано:**

1. SSL-сертификат:
   - DNS `lab.ai-mentor.kz` резолвится на `207.180.243.173`
   - Расширен существующий сертификат `ai-mentor.kz` через `certbot --expand` (добавлен `lab.ai-mentor.kz`)
   - Сертификат: `/etc/letsencrypt/live/ai-mentor.kz/fullchain.pem` (истекает 2026-06-18)

2. Nginx конфигурация:
   - Конфиг: `nginx/lab.ai-mentor.kz.conf` (в репо)
   - Симлинк: `/etc/nginx/sites-enabled/ai-mentor-lab.conf` → `nginx/lab.ai-mentor.kz.conf`
   - HTTP→HTTPS редирект, SSL, gzip, rate limiting, CSP (CartoDB tiles, unpkg CDN для Leaflet)
   - Upstream: `127.0.0.1:3012` (порт 3008 был занят `sbcheck_frontend`)

3. Docker контейнер:
   - Контейнер: `ai_mentor_lab_app_prod` (порт `127.0.0.1:3012:3000`)
   - Деплой: `./deploy.sh lab-app`

4. Проверено:
   - `curl -s https://lab.ai-mentor.kz/ru` → 200 OK, HTTP/2
   - `curl -s http://127.0.0.1:3012/ru` → 200 OK
   - i18n: `/ru` и `/kz` работают

---

### Фаза 3. Карта истории Казахстана — MVP модуль (3-5 дней)

**Цель:** полноценная интерактивная карта с 5-7 историческими эпохами.

**Задачи:**

1. Подготовка GeoJSON данных (исследование + создание):
   - Собрать/нарисовать территории для ключевых эпох:
     - Саки и Усуни (VII в. до н.э. — V в. н.э.)
     - Тюркский каганат (VI—VIII вв.)
     - Золотая Орда (XIII—XV вв.)
     - Казахское ханство (XV—XVIII вв.)
     - Кокандское/Хивинское ханство (XVIII—XIX вв.)
     - Российская империя — Казахская степь (XIX в.)
     - Казахская ССР (1936—1991)
   - Маркеры: столицы, ключевые города, битвы
   - Торговые пути: Великий Шёлковый путь

2. Компоненты карты:
   - `HistoryMap.tsx` — Leaflet карта с центром на Казахстане
   - `Timeline.tsx` — горизонтальный слайдер внизу экрана, перемотка по эпохам
   - `TerritoryLayer.tsx` — GeoJSON полигоны с цветовой кодировкой и анимацией перехода
   - `MapMarkers.tsx` — кликабельные маркеры (город → popup с описанием и фото)
   - `EpochInfo.tsx` — боковая панель: название эпохи, даты, ключевые события, ссылка на параграф учебника

3. UX:
   - Плавная анимация смены территорий при перемотке Timeline
   - Zoom к ключевым точкам при клике на событие
   - Мобильная адаптация (touch-жесты для карты)
   - Полноэкранный режим

4. Привязка к учебнику:
   - Каждая эпоха содержит `paragraph_id` → ссылка «Читать в учебнике»
   - Лаборатория открывается из параграфа учебника через deep link

**Результат:** студент открывает карту, перематывает время слайдером, видит как менялись территории, кликает на города и битвы, читает описания.

---

### Фаза 4. Интерактивные задания (2-3 дня)

**Цель:** встроенные задания на карте с начислением XP.

**Задачи:**

1. Типы заданий:
   - **«Найди на карте»** — задание: «Покажи столицу Казахского ханства». Студент кликает на карту, проверяется расстояние до правильной точки.
   - **«Хронология»** — задание: «Расположи события в правильном порядке». Drag-and-drop список.
   - **«Выбери эпоху»** — показана территория, нужно выбрать к какой эпохе она относится.
   - **«Викторина»** — текстовый вопрос с вариантами ответа, привязан к точке на карте.

2. Компоненты:
   - `LabTaskDialog.tsx` — модальное окно задания (адаптивное под тип)
   - `XPNotification.tsx` — анимированное уведомление «+10 XP»
   - Маркеры заданий на карте (иконка задания → клик → открывается диалог)

3. Интеграция с gamification:
   - `POST /lab/{lab_id}/tasks/{task_id}/answer` → начисление XP
   - Синхронизация с `gamification_profiles` (общий XP студента)
   - Показ streak / уровня если применимо

4. Прогресс:
   - Трекинг explored_epochs (какие эпохи студент просмотрел)
   - Трекинг выполненных заданий
   - Прогресс-бар на странице каталога

**Результат:** на карте появляются маркеры заданий, студент отвечает, получает XP, видит свой прогресс.

---

### Фаза 5. WebView интеграция + деплой (1 день)

**Цель:** лаборатория работает из Flutter-приложения и задеплоена в прод.

**Задачи:**

1. WebView маршрут:
   - `/[locale]/webview/lab/[labId]/page.tsx` — без шапки/навигации, только контент
   - JWT передаётся через URL query: `?token=xxx`
   - Парсинг токена из URL, сохранение в localStorage

2. Flutter deep link:
   - Формат URL: `https://lab.ai-mentor.kz/ru/webview/lab/{labId}?token={jwt}`
   - Передача из Flutter: `WebView(url: labUrl, headers: {'Authorization': 'Bearer $token'})`

3. Тестирование:
   - Проверить touch-жесты карты в WebView (pinch-to-zoom, pan)
   - Проверить производительность на Android (low-end устройства)
   - Проверить что JWT refresh работает в WebView контексте

4. Продакшен деплой:
   - DNS запись `lab.ai-mentor.kz` → сервер
   - Nginx конфиг + SSL (certbot)
   - `docker compose build lab-app && docker compose up -d lab-app`
   - Health check: `curl https://lab.ai-mentor.kz/ru`

**Результат:** лаборатория доступна по `lab.ai-mentor.kz` в браузере и через WebView в Flutter-приложении.

---

### Фаза 6. Химия — 3D молекулы (будущее)

**Цель:** второй предметный модуль — интерактивные 3D-модели молекул.

**Задачи:**

1. Интеграция 3Dmol.js:
   - `MoleculeViewer.tsx` — WebGL рендер молекулы из MOL/PDB файла
   - Вращение, zoom, выделение атомов
   - Подсветка типов связей (ковалентная, ионная, водородная)
   - Переключение стилей отображения (шарики, палочки, van der Waals)

2. Контент:
   - Загрузить MOL файлы базовых молекул из PubChem (H₂O, CO₂, C₆H₁₂O₆, NaCl, ...)
   - Привязать к параграфам учебника химии

3. Задания:
   - «Найди атом» — кликни на атом кислорода в молекуле глюкозы
   - «Посчитай связи» — сколько ковалентных связей в молекуле?
   - «Собери молекулу» — drag-and-drop атомов (расширенный режим)

---

### Фаза 7. Физика — симуляции (будущее)

**Цель:** третий модуль — интерактивные физические симуляции.

**Задачи:**

1. Matter.js симуляции:
   - `PendulumSim.tsx` — маятник с настройкой длины, массы, угла. Графики T(l), E(t).
   - `CircuitBuilder.tsx` — drag-and-drop элементы цепи (батарея, резистор, лампочка). Закон Ома в реальном времени.
   - `OpticsLab.tsx` — линзы, зеркала, преломление. Лучи строятся в реальном времени.

2. Параметрический UI:
   - Слайдеры для изменения параметров (масса, длина, напряжение)
   - Графики в реальном времени (recharts)
   - Кнопки play/pause/reset

3. Задания:
   - «Настрой маятник с периодом 2 секунды»
   - «Собери цепь, чтобы лампочка горела»
   - «Где будет фокус линзы?»

---

## MVP-предмет: почему История Казахстана

| Критерий | История | Химия | Физика |
|----------|---------|-------|--------|
| Контент в БД | 8 учебников (5-11 класс) | Нет учебника | Нет учебника |
| Визуальный wow-эффект | Карта с анимацией эпох | 3D молекулы | Симуляции |
| Техническая сложность | 2D (Leaflet) — проще | 3D (WebGL) — сложнее | 2D (Matter.js) — средне |
| Мобильная совместимость | Отличная (Leaflet touch) | Средняя (WebGL) | Хорошая |
| Уникальность | Интерактивных карт истории КЗ нет | Есть аналоги | Есть PhET |
| Время до MVP | 1-2 недели | 2-3 недели | 2-3 недели |

**Вывод:** История Казахстана — оптимальный старт. Быстрый MVP, максимальный эффект, привязка к уже загруженному контенту.
