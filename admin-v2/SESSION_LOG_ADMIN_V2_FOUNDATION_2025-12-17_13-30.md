# SESSION LOG: Admin Panel v2 - Foundation Setup

**Дата:** 2025-12-17 13:30
**Задача:** Создание новой админ панели с 100% контролем над дизайном
**Статус:** Фаза 1 завершена

---

## Контекст

Пользователь запросил полную замену текущей админ панели (React Admin v5 + Material UI) на кастомное решение с полным контролем над дизайном.

### Выбранные решения:
- **Подход:** Параллельная разработка в `admin-v2/`
- **Стек:** Next.js 14 + shadcn/ui + Tailwind
- **Дизайн:** Minimal & Clean
- **Языки:** Русский + Казахский (i18n)

---

## Выполненная работа

### 1. Инициализация проекта
```bash
npx create-next-app@latest admin-v2 --typescript --tailwind --eslint --app --src-dir
```

### 2. Настройка shadcn/ui
- Установлено 27 UI компонентов
- Цветовая схема: Zinc (нейтральная)
- Стиль: New York

### 3. Установленные зависимости
```json
{
  "@tanstack/react-query": "^5.x",
  "@tanstack/react-table": "^8.x",
  "axios": "^1.x",
  "zustand": "^4.x",
  "next-intl": "^3.x",
  "date-fns": "^3.x"
}
```

### 4. Структура i18n (next-intl)
- `src/i18n/config.ts` - конфигурация локалей (ru, kk)
- `src/i18n/request.ts` - серверная загрузка переводов
- `src/i18n/navigation.ts` - типизированная навигация
- `src/middleware.ts` - роутинг по локалям
- `messages/ru.json` - русский перевод (~150 ключей)
- `messages/kk.json` - казахский перевод

### 5. API Layer
- `src/lib/api/client.ts` - Axios с interceptors:
  - Автоматическое добавление Bearer token
  - Auto-refresh при 401
  - Redirect на login при истечении токена
- `src/lib/api/auth.ts` - login, refresh, getMe
- `src/lib/api/schools.ts` - CRUD + block/unblock
- `src/lib/api/textbooks.ts` - полный CRUD + chapters/paragraphs

### 6. Auth система
- `src/providers/auth-provider.tsx`:
  - AuthContext с user, login, logout
  - isSuperAdmin, isSchoolAdmin helpers
  - Автоматический redirect на login
- `src/components/auth/auth-guard.tsx` - защита роутов
- `src/components/auth/role-guard.tsx` - проверка ролей

### 7. Layout компоненты
- `src/components/layout/app-sidebar.tsx`:
  - Role-based меню (SUPER_ADMIN vs ADMIN)
  - Использует shadcn/ui Sidebar
  - Активные пункты подсвечиваются
- `src/components/layout/header.tsx`:
  - User dropdown с logout
  - Language switcher (RU/KK)
  - Роль пользователя в badge

### 8. Страницы
- `src/app/[locale]/(auth)/login/page.tsx` - форма логина
- `src/app/[locale]/(dashboard)/page.tsx` - Dashboard с метриками
- `src/app/[locale]/(dashboard)/layout.tsx` - layout с sidebar

### 9. TypeScript типы
- `src/types/index.ts` - все типы (~400 строк):
  - User, UserRole, TokenResponse
  - School, Textbook, Chapter, Paragraph
  - Test, Question, QuestionOption
  - Student, Teacher, Parent, SchoolClass
  - GOSO: Subject, Framework, Section, Subsection, LearningOutcome

---

## Структура проекта

```
admin-v2/
├── src/
│   ├── app/
│   │   ├── [locale]/
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── layout.tsx
│   │   │   ├── (dashboard)/
│   │   │   │   ├── page.tsx
│   │   │   │   └── layout.tsx
│   │   │   └── layout.tsx
│   │   ├── globals.css
│   │   └── layout.tsx
│   │
│   ├── components/
│   │   ├── ui/              # 27 shadcn/ui компонентов
│   │   ├── layout/          # app-sidebar, header
│   │   └── auth/            # auth-guard, role-guard
│   │
│   ├── lib/
│   │   ├── api/             # client, auth, schools, textbooks
│   │   └── utils.ts
│   │
│   ├── providers/           # auth-provider, query-provider
│   ├── i18n/                # config, request, navigation
│   ├── types/               # TypeScript interfaces
│   └── middleware.ts        # i18n routing
│
├── messages/
│   ├── ru.json
│   └── kk.json
│
├── .env.local
├── next.config.ts
├── tailwind.config.ts
└── package.json
```

---

## Проверка

```bash
npm run build
# ✓ Compiled successfully
# Routes:
#   /[locale]        - Dashboard
#   /[locale]/login  - Login page
```

---

## Следующие шаги (Фаза 2-5)

### Фаза 2: Data Table & Forms (2-3 дня)
- [ ] DataTable компонент (TanStack Table)
- [ ] Column definitions pattern
- [ ] Pagination, sorting, filters
- [ ] Form компоненты с Zod валидацией

### Фаза 3: SUPER_ADMIN CRUD (4-5 дней)
- [ ] Schools: List, Create, Edit, Show
- [ ] Textbooks: CRUD + Structure Editor
- [ ] Tests: CRUD + Questions Editor
- [ ] GOSO: Frameworks viewer, Outcomes list

### Фаза 4: School ADMIN CRUD (4-5 дней)
- [ ] Students, Teachers, Parents CRUD
- [ ] Classes с управлением членами
- [ ] School textbooks (с fork)
- [ ] School tests, Settings

### Фаза 5: Polish (2-3 дня)
- [ ] Rich text editor (TipTap)
- [ ] Dark mode
- [ ] Responsive design
- [ ] Dockerfile для деплоя

---

## Команды

```bash
# Разработка
cd admin-v2
npm run dev
# http://localhost:3000/ru/login

# Сборка
npm run build

# Production preview
npm run start
```

---

## Файлы конфигурации

### .env.local
```
NEXT_PUBLIC_API_URL=https://api.ai-mentor.kz/api/v1
```

### next.config.ts
```typescript
import createNextIntlPlugin from 'next-intl/plugin';
const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');
export default withNextIntl(nextConfig);
```

---

## План документ

Детальный план сохранен в:
`/home/rus/.claude/plans/swift-twirling-cookie.md`

---

## Заметки

1. Next.js 16 показывает warning о deprecated middleware - это связано с новой архитектурой proxy, но middleware продолжает работать
2. Dashboard страницы не генерируются статически т.к. они клиентские (требуют AuthProvider)
3. API подключен к production: `api.ai-mentor.kz`

---

**Время выполнения:** ~45 минут
**Автор:** Claude Code
