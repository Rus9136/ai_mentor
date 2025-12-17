# Admin Panel v2 - Архитектура и Документация

## Обзор

Новая админ панель для AI Mentor платформы. Заменяет старую React Admin панель.

**URL:** https://admin.ai-mentor.kz
**Стек:** Next.js 16 + shadcn/ui + TanStack Query + Tailwind CSS
**Локализация:** Русский (ru) + Казахский (kk)

---

## Структура проекта

```
admin-v2/
├── src/
│   ├── app/                          # Next.js App Router
│   │   └── [locale]/                 # i18n routing (/ru/*, /kk/*)
│   │       ├── (auth)/               # Auth layout (без sidebar)
│   │       │   └── login/page.tsx    # Страница логина
│   │       └── (dashboard)/          # Dashboard layout (с sidebar)
│   │           ├── layout.tsx        # Sidebar + Header
│   │           ├── page.tsx          # Главная страница
│   │           │
│   │           │── # SUPER_ADMIN страницы
│   │           ├── schools/          # CRUD школ
│   │           ├── textbooks/        # Глобальные учебники
│   │           ├── tests/            # Глобальные тесты
│   │           ├── goso/             # ГОСО стандарты (read-only)
│   │           │
│   │           │── # School ADMIN страницы
│   │           ├── students/         # Ученики школы
│   │           ├── teachers/         # Учителя школы
│   │           ├── parents/          # Родители
│   │           ├── classes/          # Классы
│   │           ├── school-textbooks/ # Библиотека учебников
│   │           ├── school-tests/     # Тесты школы
│   │           └── settings/         # Настройки школы
│   │
│   ├── components/
│   │   ├── ui/                       # shadcn/ui компоненты
│   │   ├── layout/                   # Sidebar, Header, Breadcrumbs
│   │   ├── data-table/               # DataTable + columns helpers
│   │   ├── forms/                    # Формы (StudentForm, etc.)
│   │   ├── auth/                     # AuthGuard, RoleGuard
│   │   └── textbooks/                # StructureEditor, ChapterDialog
│   │
│   ├── lib/
│   │   ├── api/                      # API клиенты (axios)
│   │   ├── hooks/                    # React Query hooks
│   │   ├── validations/              # Zod schemas
│   │   └── utils.ts                  # cn() helper
│   │
│   ├── providers/                    # QueryProvider, AuthProvider
│   ├── stores/                       # Zustand (sidebar state)
│   ├── types/                        # TypeScript interfaces
│   └── i18n/                         # next-intl config
│
├── messages/                         # Переводы
│   ├── ru.json                       # Русский
│   └── kk.json                       # Казахский
│
├── Dockerfile.prod                   # Production Docker image
├── next.config.ts                    # Next.js config + API rewrites
└── package.json
```

---

## Роли и доступы

### SUPER_ADMIN (role: 'super_admin')
- Управление школами (`/schools`)
- Глобальные учебники (`/textbooks`)
- Глобальные тесты (`/tests`)
- ГОСО стандарты (`/goso`)
- API endpoints: `/api/v1/admin/global/*`, `/api/v1/admin/schools`

### School ADMIN (role: 'admin')
- Привязан к конкретной школе (school_id из JWT)
- Ученики (`/students`)
- Учителя (`/teachers`)
- Родители (`/parents`)
- Классы (`/classes`)
- Библиотека учебников (`/school-textbooks`) - может форкать глобальные
- Тесты школы (`/school-tests`)
- Настройки (`/settings`)
- API endpoints: `/api/v1/admin/school/*`

---

## Ключевые файлы по функциональности

### Аутентификация
| Файл | Описание |
|------|----------|
| `src/providers/auth-provider.tsx` | AuthContext, login/logout, token refresh |
| `src/components/auth/auth-guard.tsx` | Редирект на /login если не авторизован |
| `src/components/auth/role-guard.tsx` | Проверка роли пользователя |
| `src/lib/api/client.ts` | Axios interceptors, auto-refresh tokens |
| `src/app/[locale]/(auth)/login/page.tsx` | Страница логина |

### Навигация
| Файл | Описание |
|------|----------|
| `src/components/layout/sidebar.tsx` | Боковое меню (роль-зависимое) |
| `src/components/layout/header.tsx` | Шапка с user menu |
| `src/components/layout/nav-config.ts` | Конфигурация меню по ролям |
| `src/stores/sidebar-store.ts` | Zustand store для collapsed state |

### DataTable (списки)
| Файл | Описание |
|------|----------|
| `src/components/data-table/data-table.tsx` | Основной компонент таблицы |
| `src/components/data-table/data-table-column-header.tsx` | Сортировка колонок |
| `src/components/data-table/data-table-pagination.tsx` | Пагинация |
| `src/components/data-table/data-table-toolbar.tsx` | Поиск и фильтры |
| `src/components/data-table/data-table-row-actions.tsx` | View/Edit/Delete кнопки |

### API клиенты (`src/lib/api/`)
| Файл | Endpoints |
|------|-----------|
| `client.ts` | Base axios instance с interceptors |
| `auth.ts` | `/auth/login`, `/auth/refresh`, `/auth/me` |
| `schools.ts` | `/admin/schools/*` (SUPER_ADMIN) |
| `textbooks.ts` | `/admin/global/textbooks/*` (SUPER_ADMIN) |
| `tests.ts` | `/admin/global/tests/*` (SUPER_ADMIN) |
| `goso.ts` | `/goso/*` (read-only) |
| `students.ts` | `/admin/school/students/*` (School ADMIN) |
| `teachers.ts` | `/admin/school/teachers/*` (School ADMIN) |
| `parents.ts` | `/admin/school/parents/*` (School ADMIN) |
| `classes.ts` | `/admin/school/classes/*` (School ADMIN) |
| `school-textbooks.ts` | `/admin/school/textbooks/*` (School ADMIN) |
| `school-tests.ts` | `/admin/school/tests/*` (School ADMIN) |
| `settings.ts` | `/admin/school/settings` (School ADMIN) |

### React Query Hooks (`src/lib/hooks/`)
| Файл | Hooks |
|------|-------|
| `use-auth.ts` | `useLogin`, `useLogout`, `useCurrentUser` |
| `use-schools.ts` | `useSchools`, `useSchool`, `useCreateSchool`, etc. |
| `use-textbooks.ts` | `useTextbooks`, `useChapters`, `useParagraphs`, etc. |
| `use-tests.ts` | `useTests`, `useTest`, `useQuestions`, etc. |
| `use-students.ts` | `useStudents`, `useStudent`, `useCreateStudent`, etc. |
| `use-teachers.ts` | `useTeachers`, `useTeacher`, `useCreateTeacher`, etc. |
| `use-parents.ts` | `useParents`, `useParent`, `useAddChildToParent`, etc. |
| `use-classes.ts` | `useClasses`, `useAddStudentsToClass`, etc. |
| `use-school-textbooks.ts` | `useSchoolTextbooks`, `useCustomizeTextbook` |
| `use-school-tests.ts` | `useSchoolTests`, `useSchoolTest`, etc. |
| `use-settings.ts` | `useSchoolSettings`, `useUpdateSchoolSettings` |

### Zod Validations (`src/lib/validations/`)
| Файл | Schemas |
|------|---------|
| `school.ts` | `schoolCreateSchema`, `schoolUpdateSchema` |
| `textbook.ts` | `textbookSchema`, `chapterSchema`, `paragraphSchema` |
| `test.ts` | `testSchema`, `questionSchema`, `optionSchema` |
| `student.ts` | `studentCreateSchema`, `studentUpdateSchema` |
| `teacher.ts` | `teacherCreateSchema`, `teacherUpdateSchema` |
| `parent.ts` | `parentCreateSchema` |
| `class.ts` | `classCreateSchema` |
| `settings.ts` | `settingsUpdateSchema` |

### Формы (`src/components/forms/`)
| Файл | Описание |
|------|----------|
| `school-form.tsx` | Форма школы (SUPER_ADMIN) |
| `textbook-form.tsx` | Форма учебника |
| `test-form.tsx` | Форма теста |
| `student-form.tsx` | Форма ученика (create/edit) |
| `teacher-form.tsx` | Форма учителя (create/edit) |
| `parent-form.tsx` | Форма родителя |
| `class-form.tsx` | Форма класса |
| `settings-form.tsx` | Форма настроек школы |

---

## Паттерны и конвенции

### 1. Структура страницы CRUD

```
/[entity]/
├── page.tsx           # Список (DataTable)
├── columns.tsx        # Определение колонок таблицы
├── create/
│   └── page.tsx       # Создание
└── [id]/
    ├── page.tsx       # Детальный просмотр
    └── edit/
        └── page.tsx   # Редактирование
```

### 2. Query Keys Factory Pattern

```typescript
// src/lib/hooks/use-students.ts
export const studentKeys = {
  all: ['students'] as const,
  lists: () => [...studentKeys.all, 'list'] as const,
  list: (filters?: StudentFilters) => [...studentKeys.lists(), filters] as const,
  details: () => [...studentKeys.all, 'detail'] as const,
  detail: (id: number) => [...studentKeys.details(), id] as const,
};
```

### 3. RoleGuard для защиты страниц

```tsx
// SUPER_ADMIN only
<RoleGuard allowedRoles={['super_admin']}>
  <SchoolsPage />
</RoleGuard>

// School ADMIN only
<RoleGuard allowedRoles={['admin']}>
  <StudentsPage />
</RoleGuard>
```

### 4. Discriminated Union для форм (create/edit)

```typescript
type StudentFormProps =
  | {
      mode: 'create';
      student?: never;
      onSubmit: (data: StudentCreateInput) => void;
    }
  | {
      mode: 'edit';
      student: Student;
      onSubmit: (data: StudentUpdateInput) => void;
    };
```

### 5. API Client Pattern

```typescript
// src/lib/api/students.ts
export const studentsApi = {
  getAll: () => apiClient.get<Student[]>('/admin/school/students'),
  getById: (id: number) => apiClient.get<Student>(`/admin/school/students/${id}`),
  create: (data: StudentCreateInput) => apiClient.post<Student>('/admin/school/students', data),
  update: (id: number, data: StudentUpdateInput) => apiClient.put<Student>(`/admin/school/students/${id}`, data),
  delete: (id: number) => apiClient.delete(`/admin/school/students/${id}`),
};
```

---

## Специфические фичи

### Textbook Structure Editor
Редактор структуры учебника (главы и параграфы):
- `src/components/textbooks/structure-editor.tsx` - основной компонент
- `src/components/textbooks/chapter-dialog.tsx` - диалог главы
- `src/components/textbooks/paragraph-dialog.tsx` - диалог параграфа
- Collapsible главы, inline редактирование

### School Textbooks Fork (Customize)
Школа может "форкнуть" глобальный учебник:
- `POST /admin/school/textbooks/{global_id}/customize`
- Создаёт копию с `is_customized=true` и `global_textbook_id`
- UI: две вкладки (Глобальные / Наши учебники)

### Class Membership Management
Управление составом класса:
- `useAddStudentsToClass`, `useRemoveStudentFromClass`
- `useAddTeachersToClass`, `useRemoveTeacherFromClass`
- UI: вкладки Ученики/Учителя в детальном просмотре класса

### Parent-Child Relationship
Связь родитель-ребёнок:
- `useAddChildToParent`, `useRemoveChildFromParent`
- UI: выбор детей при создании родителя, управление в детальном просмотре

---

## Deployment

### Docker
```bash
# Build
docker compose -f docker-compose.infra.yml build admin-v2

# Start
docker compose -f docker-compose.infra.yml up -d admin-v2

# Logs
docker logs -f ai_mentor_admin_v2_prod
```

### Конфигурация
| Параметр | Значение |
|----------|----------|
| Container | `ai_mentor_admin_v2_prod` |
| Port | `127.0.0.1:3003 -> 3000` |
| Nginx | `/etc/nginx/sites-enabled/ai-mentor-admin.conf` |
| URL | https://admin.ai-mentor.kz |

### Environment Variables
```env
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api.ai-mentor.kz/api/v1
```

---

## Тестовые учётные данные

| Роль | Email | Password |
|------|-------|----------|
| SUPER_ADMIN | superadmin@aimentor.com | admin123 |
| School ADMIN | school.admin@test.com | admin123 |

---

## Частые задачи

### Добавить новую страницу для School ADMIN

1. Создать API client в `src/lib/api/`
2. Создать hooks в `src/lib/hooks/`
3. Создать validation schema в `src/lib/validations/`
4. Создать форму в `src/components/forms/`
5. Создать страницы в `src/app/[locale]/(dashboard)/[entity]/`
6. Добавить в навигацию `src/components/layout/nav-config.ts`
7. Экспортировать из `index.ts` файлов

### Добавить новый API endpoint

1. Добавить метод в соответствующий API client
2. Создать React Query hook
3. Использовать в компоненте

### Изменить структуру формы

1. Обновить Zod schema в `src/lib/validations/`
2. Обновить форму в `src/components/forms/`
3. TypeScript автоматически покажет ошибки

---

## Зависимости от Backend API

Админ панель полностью зависит от Backend API:
- **Auth:** `/api/v1/auth/*`
- **SUPER_ADMIN:** `/api/v1/admin/global/*`, `/api/v1/admin/schools`
- **School ADMIN:** `/api/v1/admin/school/*`
- **GOSO:** `/api/v1/goso/*`

API документация: https://api.ai-mentor.kz/docs
