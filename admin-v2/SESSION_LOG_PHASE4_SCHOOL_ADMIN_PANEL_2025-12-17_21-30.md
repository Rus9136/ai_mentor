# Session Log: Phase 4 - School ADMIN Panel

**Date:** 2025-12-17 21:30
**Task:** Implement School ADMIN panel for admin-v2 (Phase 4)

## Overview

Phase 4 implementation of School ADMIN panel - interface for school administrators (role='admin') who are tied to a specific school_id and can only manage their own school's data.

## Key Difference from SUPER_ADMIN

- School ADMIN is tied to `school_id` from JWT token
- Cannot see other schools' data
- Can only READ global content (textbooks, tests)
- Can EDIT only their own school's data
- Uses `/api/v1/admin/school/*` endpoints (not `/admin/global/*`)

## Completed Tasks

### 1. API Clients Created (`/src/lib/api/`)

| File | Description |
|------|-------------|
| `students.ts` | CRUD for `/admin/school/students` |
| `teachers.ts` | CRUD for `/admin/school/teachers` |
| `parents.ts` | CRUD + children management for `/admin/school/parents` |
| `classes.ts` | CRUD + students/teachers management for `/admin/school/classes` |
| `school-textbooks.ts` | CRUD + customize/fork endpoint |
| `school-tests.ts` | CRUD + questions management |
| `settings.ts` | GET/PUT for school settings |

### 2. React Query Hooks (`/src/lib/hooks/`)

| File | Key Hooks |
|------|-----------|
| `use-students.ts` | `useStudents`, `useStudent`, `useCreateStudent`, `useUpdateStudent`, `useDeleteStudent` |
| `use-teachers.ts` | `useTeachers`, `useTeacher`, `useCreateTeacher`, `useUpdateTeacher`, `useDeleteTeacher` |
| `use-parents.ts` | `useParents`, `useParent`, `useCreateParent`, `useDeleteParent`, `useAddChildToParent`, `useRemoveChildFromParent` |
| `use-classes.ts` | `useClasses`, `useClass`, `useCreateClass`, `useUpdateClass`, `useDeleteClass`, `useAddStudentsToClass`, `useRemoveStudentFromClass`, `useAddTeachersToClass`, `useRemoveTeacherFromClass` |
| `use-school-textbooks.ts` | `useSchoolTextbooks`, `useCustomizeTextbook`, `useDeleteSchoolTextbook` |
| `use-school-tests.ts` | `useSchoolTests`, `useSchoolTest`, `useCreateSchoolTest`, `useUpdateSchoolTest`, `useDeleteSchoolTest` |
| `use-settings.ts` | `useSchoolSettings`, `useUpdateSchoolSettings` |

### 3. Zod Validations (`/src/lib/validations/`)

| File | Schemas |
|------|---------|
| `student.ts` | `studentCreateSchema`, `studentUpdateSchema` |
| `teacher.ts` | `teacherCreateSchema`, `teacherUpdateSchema` |
| `parent.ts` | `parentCreateSchema` |
| `class.ts` | `classCreateSchema` |
| `settings.ts` | `settingsUpdateSchema` |

### 4. Forms (`/src/components/forms/`)

| File | Features |
|------|----------|
| `student-form.tsx` | Discriminated union props for create/edit modes, grade selector |
| `teacher-form.tsx` | Discriminated union props for create/edit modes, subject field, bio textarea |
| `parent-form.tsx` | Children selection with checkboxes |
| `class-form.tsx` | Name, code, grade level, academic year |
| `settings-form.tsx` | School name, address, phone, email |

### 5. Pages Created

#### Students (`/src/app/[locale]/(dashboard)/students/`)
- `page.tsx` - List with DataTable
- `columns.tsx` - Table columns definition
- `create/page.tsx` - Create new student
- `[id]/page.tsx` - Student detail view
- `[id]/edit/page.tsx` - Edit student

#### Teachers (`/src/app/[locale]/(dashboard)/teachers/`)
- `page.tsx` - List with DataTable
- `columns.tsx` - Table columns definition
- `create/page.tsx` - Create new teacher
- `[id]/page.tsx` - Teacher detail view
- `[id]/edit/page.tsx` - Edit teacher

#### Parents (`/src/app/[locale]/(dashboard)/parents/`)
- `page.tsx` - List with DataTable
- `columns.tsx` - Table columns definition
- `create/page.tsx` - Create new parent with children selection
- `[id]/page.tsx` - Parent detail with children management (add/remove)

#### Classes (`/src/app/[locale]/(dashboard)/classes/`)
- `page.tsx` - List with DataTable
- `columns.tsx` - Table columns definition
- `create/page.tsx` - Create new class
- `[id]/page.tsx` - Class detail with tabs (Students/Teachers), add/remove members
- `[id]/edit/page.tsx` - Edit class

#### School Textbooks (`/src/app/[locale]/(dashboard)/school-textbooks/`)
- `page.tsx` - Two tabs interface:
  - **Global tab**: Read-only list of global textbooks with "Customize" button
  - **School tab**: School's own textbooks (forked or custom)

#### School Tests (`/src/app/[locale]/(dashboard)/school-tests/`)
- `page.tsx` - List with DataTable, CRUD actions

#### Settings (`/src/app/[locale]/(dashboard)/settings/`)
- `page.tsx` - School settings form with statistics cards

## Technical Patterns Used

### 1. RoleGuard with 'admin' role
```tsx
<RoleGuard allowedRoles={['admin']}>
  {/* School admin content */}
</RoleGuard>
```

### 2. Discriminated Union Props for Forms
```typescript
type StudentFormProps =
  | {
      mode: 'create';
      student?: never;
      onSubmit: (data: StudentCreateInput) => void;
      isLoading?: boolean;
    }
  | {
      mode: 'edit';
      student: Student;
      onSubmit: (data: StudentUpdateInput) => void;
      isLoading?: boolean;
    };
```

### 3. Fork/Customize Pattern for Textbooks
```tsx
const handleCustomize = (textbook: Textbook) => {
  customizeTextbook.mutate(textbook.id, {
    onSuccess: () => {
      // Refresh list, show school tab
    },
  });
};

// Check if already customized
const isAlreadyCustomized = globalTextbooks.some(
  (t) => t.global_textbook_id === textbook.id
);
```

### 4. Query Keys Factory Pattern
```typescript
export const studentKeys = {
  all: ['students'] as const,
  lists: () => [...studentKeys.all, 'list'] as const,
  list: (filters?: StudentFilters) => [...studentKeys.lists(), filters] as const,
  details: () => [...studentKeys.all, 'detail'] as const,
  detail: (id: number) => [...studentKeys.details(), id] as const,
};
```

## Build Verification

Build passed successfully with all 45 pages generated:
- Static pages (SSG): Lists, create forms
- Dynamic pages: Detail views, edit forms

## Files Summary

| Category | Count |
|----------|-------|
| API clients | 7 |
| Hooks | 7 |
| Validations | 5 |
| Forms | 5 |
| Pages | ~20 |
| **Total new files** | **~44** |

## Next Steps (Phase 5+)

1. Add detail pages for school-textbooks (`/school-textbooks/[id]`)
2. Add create/edit/detail pages for school-tests
3. Add questions editor for school tests
4. Integration testing with real API

---

## Production Deployment (добавлено позже)

### Что было сделано:

1. **Dockerfile.prod** - Multi-stage build для Next.js
2. **docker-compose.infra.yml** - Добавлен сервис `admin-v2` на порту 3003
3. **nginx config** - Проксирование к Next.js серверу
4. **ARCHITECTURE.md** - Полная документация для AI агентов

### Deployment Info:

| Параметр | Значение |
|----------|----------|
| Container | `ai_mentor_admin_v2_prod` |
| Port | `127.0.0.1:3003 -> 3000` |
| URL | https://admin.ai-mentor.kz |
| Status | Running (healthy) |

### Команды деплоя:

```bash
# Build
docker compose -f docker-compose.infra.yml build admin-v2

# Start
docker compose -f docker-compose.infra.yml up -d admin-v2

# Logs
docker logs -f ai_mentor_admin_v2_prod
```

---

*Session completed successfully. Build passes without errors. Deployed to production.*
