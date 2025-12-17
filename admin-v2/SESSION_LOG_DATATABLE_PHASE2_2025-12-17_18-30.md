# SESSION LOG: Admin Panel v2 - Phase 2 DataTable & Forms

**Дата:** 2025-12-17 18:30
**Задача:** Реализация Фазы 2 - DataTable компоненты, Query Hooks, Zod валидации
**Статус:** Завершено

---

## Контекст

Продолжение разработки admin-v2 после Фазы 1 (Foundation). Цель - создать переиспользуемый DataTable компонент и интегрировать его с реальными данными из API.

### План работы:
```
День 1:
├── 1. Query Hooks (use-schools.ts)     # Сначала данные
├── 2. Zod schemas (school.ts)          # Типы валидации
└── 3. DataTable base                   # Потом UI
```

---

## Выполненная работа

### 1. Query Hooks (`src/lib/hooks/use-schools.ts`)

Создано 9 хуков с TanStack Query:

```typescript
// Query keys factory
export const schoolKeys = {
  all: ['schools'] as const,
  lists: () => [...schoolKeys.all, 'list'] as const,
  list: (filters?) => [...schoolKeys.lists(), filters] as const,
  details: () => [...schoolKeys.all, 'detail'] as const,
  detail: (id: number) => [...schoolKeys.details(), id] as const,
};

// Хуки:
useSchools()            // GET список школ
useSchool(id)           // GET одна школа
useCreateSchool()       // POST создание
useUpdateSchool()       // PUT обновление
useDeleteSchool()       // DELETE удаление
useBlockSchool()        // PATCH блокировка
useUnblockSchool()      // PATCH разблокировка
useBulkBlockSchools()   // Bulk block
useBulkUnblockSchools() // Bulk unblock
```

**Особенности:**
- Автоматическая инвалидация кэша при мутациях
- Toast уведомления через `sonner`
- Типизация через существующие типы из `@/types`

### 2. Zod Schemas (`src/lib/validations/school.ts`)

```typescript
export const schoolCreateSchema = z.object({
  name: z.string().min(1).max(255),
  code: z.string().min(2).max(50).regex(/^[a-z0-9_-]+$/),
  email: z.string().email().optional().or(z.literal('')),
  phone: z.string().max(50).optional(),
  address: z.string().optional(),
  description: z.string().optional(),
});

export const schoolUpdateSchema = schoolCreateSchema.partial();
export type SchoolCreateInput = z.infer<typeof schoolCreateSchema>;
export const schoolCreateDefaults: SchoolCreateInput = {...};
```

### 3. DataTable компоненты (`src/components/data-table/`)

| Файл | Описание |
|------|----------|
| `data-table.tsx` | Главный компонент с TanStack Table |
| `data-table-pagination.tsx` | Пагинация с выбором размера страницы |
| `data-table-toolbar.tsx` | Toolbar с поиском и фильтрами |
| `data-table-column-header.tsx` | Сортируемые заголовки колонок |
| `data-table-faceted-filter.tsx` | Фильтры с множественным выбором |
| `data-table-row-actions.tsx` | Dropdown меню действий для строки |
| `index.ts` | Экспорты |

**Функционал DataTable:**
- Sorting по колонкам (asc/desc)
- Client-side pagination
- Search фильтрация
- Faceted filters (по статусу и т.д.)
- Row selection (checkboxes)
- Row actions (view/edit/delete dropdown)
- Loading skeleton
- Empty state
- Скрытие колонок

### 4. Страница Schools (`src/app/[locale]/(dashboard)/schools/`)

| Файл | Описание |
|------|----------|
| `columns.tsx` | Определение колонок таблицы |
| `page.tsx` | Страница со списком школ |

**Колонки:**
- Checkbox для выбора
- ID (sortable)
- Название (sortable, searchable)
- Код (с `<code>` стилем)
- Email (кликабельный mailto)
- Статус (badge: Активна/Заблокирована)
- Дата создания (форматирование date-fns)
- Actions (view/edit/delete/block/unblock)

**Функционал страницы:**
- Загрузка данных из API через `useSchools()`
- Поиск по названию
- Фильтр по статусу
- Диалог подтверждения удаления
- RoleGuard (только super_admin)
- Toast уведомления при действиях

### 5. Установленные компоненты

```bash
npx shadcn@latest add alert-dialog
```

### 6. Исправление CORS

**Проблема:** Браузер блокировал запросы с `localhost:3003` к `api.ai-mentor.kz`

**Решение:** Next.js rewrites для проксирования API:

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://api.ai-mentor.kz/api/:path*',
      },
    ];
  },
};
```

```typescript
// src/lib/api/client.ts
const API_URL = typeof window !== 'undefined'
  ? '/api/v1'  // Browser: proxied through Next.js
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1');
```

---

## Структура файлов (новые)

```
admin-v2/src/
├── lib/
│   ├── hooks/
│   │   ├── index.ts
│   │   └── use-schools.ts          # NEW
│   └── validations/
│       ├── index.ts
│       └── school.ts               # NEW
├── components/
│   └── data-table/
│       ├── index.ts                # NEW
│       ├── data-table.tsx          # NEW
│       ├── data-table-pagination.tsx    # NEW
│       ├── data-table-toolbar.tsx       # NEW
│       ├── data-table-column-header.tsx # NEW
│       ├── data-table-faceted-filter.tsx # NEW
│       └── data-table-row-actions.tsx   # NEW
└── app/[locale]/(dashboard)/schools/
    ├── columns.tsx                 # NEW
    └── page.tsx                    # NEW
```

---

## Тестирование

### Результаты:
| Тест | Статус |
|------|--------|
| `npm run build` | ✅ Успешно |
| Dev server | ✅ http://localhost:3003 |
| API proxy | ✅ Работает |
| Login | ✅ Успешно |
| /schools page | ✅ Загружается |
| Данные из API | ✅ 1 школа отображается |

### Как тестировать:
```bash
cd admin-v2
npm run dev
# http://localhost:3003/ru/login
# Email: superadmin@aimentor.com
# Password: admin123
# -> http://localhost:3003/ru/schools
```

---

## API данные

```json
// GET /api/v1/admin/schools
[
  {
    "id": 1,
    "name": "Школа №1",
    "code": "11",
    "is_active": true,
    "email": null,
    "created_at": "2025-12-16T10:06:33.782632Z"
  }
]
```

---

## Следующие шаги (Фаза 3)

### SUPER_ADMIN CRUD:
- [ ] Schools: Create, Edit, Show pages
- [ ] Textbooks: List, Create, Edit, Show + Structure Editor
- [ ] Tests: List, Create, Edit, Show + Questions Editor
- [ ] GOSO: Frameworks viewer, Outcomes list

### Улучшения DataTable:
- [ ] Bulk actions с выбранными строками
- [ ] Column visibility toggle
- [ ] Export to CSV
- [ ] Server-side pagination (если нужно)

---

## Команды

```bash
# Разработка
cd admin-v2
npm run dev

# Сборка
npm run build

# Тест API через прокси
curl -s http://localhost:3003/api/v1/admin/schools \
  -H "Authorization: Bearer <token>"
```

---

## Заметки

1. CORS обходится через Next.js rewrites - все `/api/*` запросы проксируются
2. DataTable использует client-side pagination (достаточно для MVP)
3. Query hooks включают toast уведомления из коробки
4. Zod схемы готовы для интеграции с react-hook-form

---

**Время выполнения:** ~40 минут
**Автор:** Claude Code
