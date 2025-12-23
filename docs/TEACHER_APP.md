# Teacher App (teacher.ai-mentor.kz)

Приложение для учителей — панель мониторинга успеваемости учеников и аналитики классов.

**URL:** https://teacher.ai-mentor.kz
**Порт:** 3007
**Папка:** `teacher-app/`

---

## Содержание

- [Архитектура](#архитектура)
- [Технологии](#технологии)
- [Структура проекта](#структура-проекта)
- [Страницы](#страницы)
- [API Endpoints](#api-endpoints)
- [Компоненты](#компоненты)
- [Авторизация](#авторизация)
- [Mastery Levels](#mastery-levels)
- [Локализация](#локализация)
- [Развёртывание](#развёртывание)
- [Разработка](#разработка)

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                     teacher.ai-mentor.kz                        │
│                        (Next.js 15)                             │
├─────────────────────────────────────────────────────────────────┤
│  Nginx (443)  →  Docker (3007)  →  Next.js Standalone           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │  Dashboard  │    │   Classes   │    │  Analytics  │        │
│   └─────────────┘    └─────────────┘    └─────────────┘        │
│          │                  │                  │                │
│          └──────────────────┼──────────────────┘                │
│                             ▼                                   │
│                    TanStack Query                               │
│                             │                                   │
│                             ▼                                   │
│                   api.ai-mentor.kz                              │
│                   /api/v1/teachers/*                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Технологии

| Технология | Версия | Назначение |
|------------|--------|------------|
| Next.js | 15.5 | App Router, SSR, standalone output |
| React | 19.0 | UI библиотека |
| TypeScript | 5.7 | Типизация |
| Tailwind CSS | 3.4 | Стилизация |
| TanStack Query | 5.64 | Data fetching, caching |
| Radix UI | - | Tabs, Progress, Dialog, Dropdown |
| next-intl | 4.0 | Локализация (RU/KZ) |
| Axios | 1.7 | HTTP клиент |
| Zustand | 5.0 | State management |
| Recharts | 2.15 | Графики |
| lucide-react | - | Иконки |

---

## Структура проекта

```
teacher-app/
├── src/
│   ├── app/
│   │   └── [locale]/
│   │       ├── layout.tsx              # Root layout
│   │       ├── (auth)/
│   │       │   └── login/
│   │       │       └── page.tsx        # Страница входа
│   │       └── (dashboard)/
│   │           ├── layout.tsx          # Dashboard layout (sidebar)
│   │           ├── page.tsx            # Главная (dashboard)
│   │           ├── classes/
│   │           │   ├── page.tsx        # Список классов
│   │           │   └── [id]/
│   │           │       ├── page.tsx    # Детали класса
│   │           │       └── students/
│   │           │           └── [sid]/
│   │           │               └── page.tsx  # Прогресс ученика
│   │           └── analytics/
│   │               └── page.tsx        # Аналитика
│   │
│   ├── components/
│   │   ├── dashboard/
│   │   │   ├── StatCard.tsx            # Карточка статистики
│   │   │   ├── MasteryBadge.tsx        # Бейдж уровня A/B/C
│   │   │   └── MasteryDistributionChart.tsx  # Stacked bar chart
│   │   └── ui/
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── tabs.tsx
│   │       ├── progress.tsx
│   │       ├── input.tsx
│   │       ├── label.tsx
│   │       └── alert.tsx
│   │
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts               # Axios instance + interceptors
│   │   │   ├── auth.ts                 # Email/Password auth
│   │   │   └── teachers.ts             # Teacher API functions
│   │   ├── hooks/
│   │   │   └── use-teacher-data.ts     # TanStack Query hooks
│   │   └── utils.ts                    # cn() utility
│   │
│   ├── providers/
│   │   ├── auth-provider.tsx           # Auth context
│   │   └── query-provider.tsx          # TanStack Query provider
│   │
│   ├── i18n/
│   │   ├── routing.ts                  # Locale routing config
│   │   └── request.ts                  # next-intl config
│   │
│   ├── messages/
│   │   ├── ru/index.json               # Русский
│   │   └── kz/index.json               # Казахский
│   │
│   └── middleware.ts                   # Locale redirect middleware
│
├── public/
│   └── .gitkeep
│
├── Dockerfile.prod                     # Production Dockerfile
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## Страницы

### 1. Login (`/[locale]/login`)

Страница входа для учителей.

```
┌─────────────────────────────────────────┐
│         🎓 AI Mentor                     │
│        Teacher Dashboard                 │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │ Вход для учителей                 │  │
│  │                                   │  │
│  │ Введите учётные данные,           │  │
│  │ полученные от администратора школы│  │
│  │                                   │  │
│  │ Email: [________________]         │  │
│  │ Пароль: [________________]        │  │
│  │                                   │  │
│  │        [ Войти ]                  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Особенности:**
- Email/Password авторизация (не Google OAuth)
- Учётные данные выдаёт School ADMIN
- Проверка роли: только `teacher` допускается

### 2. Dashboard (`/[locale]`)

Главная страница с обзором.

**Отображает:**
- Количество классов
- Общее количество учеников
- Средний балл
- Ученики, нуждающиеся в помощи (уровень C)
- Распределение по уровням (A/B/C chart)
- Последняя активность учеников

### 3. Classes (`/[locale]/classes`)

Список классов учителя.

**Карточка класса содержит:**
- Название и код класса
- Количество учеников
- Распределение A/B/C (визуализация)
- Средний прогресс
- Кнопка "Открыть класс"

### 4. Class Detail (`/[locale]/classes/[id]`)

Детальная информация о классе.

**Содержит:**
- Информация о классе
- Распределение по уровням
- Таблица учеников:
  - Имя
  - Mastery Level (бейдж A/B/C)
  - Прогресс (%)
  - Последняя активность
  - Ссылка на детали

### 5. Student Progress (`/[locale]/classes/[id]/students/[sid]`)

Детальный прогресс ученика.

**Tabs:**
1. **Прогресс по главам** — список глав с % прохождения
2. **Тесты** — последние попытки тестов
3. **История изменений** — timeline mastery changes

### 6. Analytics (`/[locale]/analytics`)

Аналитика по всем классам.

**Разделы:**
1. **Сложные темы** — параграфы с >30% учеников в уровне C
2. **Тренды** — weekly/monthly изменения mastery по классам

---

## API Endpoints

### Backend: `/api/v1/teachers/*`

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/teachers/dashboard` | Обзор dashboard |
| GET | `/teachers/classes` | Список классов |
| GET | `/teachers/classes/{id}` | Детали класса |
| GET | `/teachers/classes/{id}/overview` | Аналитика класса |
| GET | `/teachers/classes/{id}/mastery-distribution` | A/B/C распределение |
| GET | `/teachers/classes/{id}/students/{sid}/progress` | Прогресс ученика |
| GET | `/teachers/students/{id}/mastery-history` | История mastery |
| GET | `/teachers/analytics/struggling-topics` | Сложные темы |
| GET | `/teachers/analytics/mastery-trends` | Тренды (weekly/monthly) |

### Assignments (stubs, не реализованы)

| Метод | Endpoint | Статус |
|-------|----------|--------|
| GET | `/teachers/assignments` | Returns [] |
| POST | `/teachers/assignments` | 501 Not Implemented |
| GET | `/teachers/assignments/{id}` | 404 |
| PUT | `/teachers/assignments/{id}` | 404 |
| DELETE | `/teachers/assignments/{id}` | 404 |

### TypeScript Types

```typescript
// lib/api/teachers.ts

interface MasteryDistribution {
  level_a: number;   // >= 85%
  level_b: number;   // 60-84%
  level_c: number;   // < 60%
  not_started: number;
}

interface TeacherDashboardResponse {
  classes_count: number;
  total_students: number;
  students_by_level: MasteryDistribution;
  average_class_score: number;
  students_needing_help: number;
  recent_activity: RecentActivityItem[];
}

interface TeacherClassResponse {
  id: number;
  name: string;
  code: string;
  grade_level: number;
  academic_year: string;
  students_count: number;
  mastery_distribution: MasteryDistribution;
  average_score: number;
  progress_percentage: number;
}

interface StudentWithMastery {
  id: number;
  student_code: string;
  first_name: string;
  last_name: string;
  mastery_level: 'A' | 'B' | 'C' | null;
  mastery_score: number | null;
  progress_percentage: number;
  last_activity: string | null;
}
```

---

## Компоненты

### StatCard

Карточка статистики на dashboard.

```tsx
<StatCard
  title="Учеников"
  value={125}
  icon={Users}
  trend={{ value: 5, direction: 'up' }}
/>
```

### MasteryBadge

Бейдж уровня владения.

```tsx
<MasteryBadge level="A" />  // Зелёный
<MasteryBadge level="B" />  // Жёлтый
<MasteryBadge level="C" />  // Красный
```

### MasteryDistributionChart

Горизонтальный stacked bar chart.

```tsx
<MasteryDistributionChart
  distribution={{
    level_a: 15,
    level_b: 20,
    level_c: 5,
    not_started: 3
  }}
/>
```

---

## Авторизация

### Flow

```
1. School ADMIN создаёт учителя в Admin Panel
   POST /admin/school/teachers {email, password, name, subject}

2. Учитель получает учётные данные от админа

3. Учитель заходит на teacher.ai-mentor.kz/login

4. Вводит email + password

5. POST /auth/login → JWT токен

6. Frontend проверяет role === 'teacher'

7. Доступ к Teacher Dashboard
```

### Token Storage

```typescript
// Отдельные ключи от student-app
const ACCESS_TOKEN_KEY = 'ai_mentor_teacher_access_token';
const REFRESH_TOKEN_KEY = 'ai_mentor_teacher_refresh_token';
```

### Auto-refresh

API client автоматически обновляет токен при 401 ответе:

```typescript
// lib/api/client.ts
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Refresh token logic
      const response = await axios.post('/auth/refresh', {
        refresh_token: getRefreshToken(),
      });
      setTokens(response.data.access_token, response.data.refresh_token);
      // Retry original request
    }
  }
);
```

---

## Mastery Levels

Система уровней владения материалом:

| Уровень | Диапазон | Цвет | Описание |
|---------|----------|------|----------|
| **A** | >= 85% | Зелёный | Отличное владение |
| **B** | 60-84% | Жёлтый (Amber) | Хорошее владение |
| **C** | < 60% | Красный | Требуется помощь |
| **-** | 0% | Серый | Не начал |

### CSS Variables

```css
/* globals.css */
--mastery-a: 142 76% 36%;   /* hsl(142, 76%, 36%) - Green */
--mastery-b: 38 92% 50%;    /* hsl(38, 92%, 50%) - Amber */
--mastery-c: 0 84% 60%;     /* hsl(0, 84%, 60%) - Red */
```

---

## Локализация

### Поддерживаемые языки

- **ru** — Русский (по умолчанию)
- **kz** — Казахский

### Структура файлов

```
messages/
├── ru/index.json
└── kz/index.json
```

### Использование

```tsx
import { useTranslations } from 'next-intl';

function MyComponent() {
  const t = useTranslations('dashboard');
  return <h1>{t('welcome')}</h1>;
}
```

### Ключевые секции

| Секция | Назначение |
|--------|------------|
| `common` | Общие (loading, error, save, cancel) |
| `navigation` | Навигация (dashboard, classes, analytics) |
| `auth` | Авторизация (login, email, password) |
| `dashboard` | Dashboard (welcome, classesCount, etc.) |
| `classes` | Классы (title, students, progress) |
| `student` | Ученик (progress, chaptersProgress) |
| `analytics` | Аналитика (strugglingTopics, trends) |
| `mastery` | Уровни (levelA, levelB, levelC) |

---

## Развёртывание

### Nginx

Конфигурация: `nginx/ai-mentor-teacher.conf`

```nginx
upstream teacher_app_nextjs {
    server 127.0.0.1:3007;
    keepalive 64;
}

server {
    listen 443 ssl http2;
    server_name teacher.ai-mentor.kz;

    ssl_certificate /etc/letsencrypt/live/ai-mentor.kz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ai-mentor.kz/privkey.pem;

    location / {
        proxy_pass http://teacher_app_nextjs;
        # ... headers
    }
}
```

### Docker

```dockerfile
# Dockerfile.prod
FROM node:20-alpine AS base

# Dependencies
FROM base AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_GOOGLE_CLIENT_ID
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_GOOGLE_CLIENT_ID=$NEXT_PUBLIC_GOOGLE_CLIENT_ID
RUN npm run build

# Runner
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3007
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3007
CMD ["node", "server.js"]
```

### docker-compose.infra.yml

```yaml
teacher-app:
  build:
    context: ./teacher-app
    dockerfile: Dockerfile.prod
    args:
      NEXT_PUBLIC_API_URL: https://api.ai-mentor.kz/api/v1
      NEXT_PUBLIC_GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
  container_name: ai_mentor_teacher_app_prod
  restart: unless-stopped
  ports:
    - "127.0.0.1:3007:3007"
  environment:
    - NODE_ENV=production
  networks:
    - ai_mentor_network
```

### Деплой

```bash
# Полный деплой (через deploy.sh)
./deploy.sh

# Только teacher-app
docker compose -f docker-compose.infra.yml build teacher-app
docker compose -f docker-compose.infra.yml up -d teacher-app
```

---

## Разработка

### Локальный запуск

```bash
cd teacher-app

# Установка зависимостей
npm install

# Development server (порт 3005)
npm run dev

# Open: http://localhost:3005/ru
```

### Environment Variables

```env
# .env.local
NEXT_PUBLIC_API_URL=https://api.ai-mentor.kz/api/v1
# или для локальной разработки:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Build

```bash
npm run build
npm run start  # Production mode на порту 3005
```

### Lint

```bash
npm run lint
```

---

## Тестовые учётные записи

```
Email: teacher.math@school001.com
Password: teacher123
School: School #7
```

---

## Связанные файлы

| Файл | Описание |
|------|----------|
| `backend/app/api/v1/teachers.py` | API endpoints (486 строк) |
| `backend/app/services/teacher_analytics_service.py` | Бизнес-логика (480 строк) |
| `backend/app/schemas/teacher_dashboard.py` | Pydantic schemas (400 строк) |
| `nginx/ai-mentor-teacher.conf` | Nginx конфигурация |
| `docker-compose.infra.yml` | Docker compose |

---

## Следующие шаги (TODO)

1. **Assignments** — полная реализация (сейчас stubs)
2. **Turborepo** — shared packages с student-app
3. **Тесты** — unit/integration tests
4. **Dark mode** — тема оформления
5. **PWA** — offline support

---

## История изменений

| Дата | Версия | Изменения |
|------|--------|-----------|
| 2025-12-23 | 1.0.0 | Первоначальная реализация (Итерация 11) |
| 2025-12-23 | 1.0.1 | Google OAuth → Email/Password |
