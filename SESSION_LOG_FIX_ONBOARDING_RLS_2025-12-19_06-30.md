# Session Log: Fix Student Onboarding & RLS Policies

**Дата:** 2025-12-19 06:30
**Задача:** Исправить регистрацию студентов через публичные коды и RLS политики

## Контекст

Был реализован новый onboarding flow для студентов:
1. Студент логинится через Google OAuth
2. Выбирает класс (7-11) → автоматически использует публичный код (PUBLIC7-PUBLIC11)
3. Заполняет профиль → завершает регистрацию

## Проблемы и решения

---

### Проблема 1: `code_not_found` при выборе класса

**Симптом:** При выборе класса выходит надпись "code_not_found"

**Причина:** RLS политика на `invitation_codes` требовала `school_id = current_tenant_id`, но студент на onboarding не имеет `school_id` (NULL), поэтому запрос не находил коды.

**Диагностика:**
```sql
SELECT * FROM pg_policies WHERE tablename = 'invitation_codes';
-- Политика: school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id'), ''), '0')::integer
-- При NULL tenant_id это становится school_id = 0, а коды имеют school_id = 3
```

**Решение:**
```sql
DROP POLICY IF EXISTS invitation_codes_select_policy ON invitation_codes;
CREATE POLICY invitation_codes_select_policy ON invitation_codes
    FOR SELECT USING (true);  -- Разрешить SELECT всем
```

---

### Проблема 2: 500 Internal Server Error на validate-code

**Симптом:** CORS ошибка в браузере, 500 на сервере

**Причина:** `invitation_code.school` возвращал `None` потому что RLS на `schools` блокировала доступ.

**Лог ошибки:**
```
AttributeError: 'NoneType' object has no attribute 'id'
File "/app/app/api/v1/auth_oauth.py", line 201, in validate_invitation_code
    "id": invitation_code.school.id,
```

**Решение:** Обновить RLS на `schools` и `school_classes`:
```sql
CREATE POLICY schools_select_policy ON schools FOR SELECT USING (true);
CREATE POLICY school_classes_select_policy ON school_classes FOR SELECT USING (true);
```

---

### Проблема 3: 422 Unprocessable Content на complete-onboarding

**Симптом:** При нажатии "Завершить регистрацию" ошибка 422

**Причина:** Несоответствие между frontend и backend схемами:
- Frontend отправлял: `{ code: "PUBLIC7", ... }`
- Backend ожидал: `{ invitation_code: "PUBLIC7", ... }`

**Файлы:**
- `backend/app/schemas/invitation_code.py`: `invitation_code: str`
- `student-app/src/lib/api/auth.ts`: `code: string`

**Решение:**
```typescript
// student-app/src/lib/api/auth.ts
export interface OnboardingCompleteRequest {
  invitation_code: string;  // Было: code
  first_name: string;
  last_name: string;
  ...
}

// student-app/src/app/[locale]/(auth)/onboarding/page.tsx
await completeOnboarding({
  invitation_code: activeCode,  // Было: code
  ...
});
```

---

### Проблема 4: StaleDataError при UPDATE users

**Симптом:** `UPDATE statement on table 'users' expected to update 1 row(s); 0 were matched`

**Причина:** RLS на `users` не разрешала UPDATE для пользователя без `school_id`

**Решение:**
1. Добавить функцию `set_current_user_id()` в `backend/app/core/tenancy.py`
2. Вызывать её в `get_current_user()` для всех пользователей
3. Обновить RLS политику:

```sql
CREATE POLICY users_update_policy ON users FOR UPDATE
USING (
    (COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
    OR (id = COALESCE(NULLIF(current_setting('app.current_user_id', true), ''), '0')::integer)
    OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer)
);
```

**Изменения в коде:**
```python
# backend/app/core/tenancy.py
async def set_current_user_id(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        text("SELECT set_config('app.current_user_id', :user_id, false)"),
        {"user_id": str(user_id)}
    )

# backend/app/api/dependencies.py
async def get_current_user(...):
    ...
    # Always set current user ID (for self-update RLS policies)
    await set_current_user_id(db, user.id)
    ...
```

---

### Проблема 5: RLS блокирует INSERT в students

**Симптом:** `new row violates row-level security policy for table "students"`

**Причина:** При onboarding студент ещё не имеет `school_id` в токене, но создаёт student record с `school_id` из invitation_code.

**Решение:**
```sql
CREATE POLICY students_insert_policy ON students FOR INSERT
WITH CHECK (
    (COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
    OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer)
    -- Self-registration: user_id должен совпадать с current_user_id
    OR (user_id = COALESCE(NULLIF(current_setting('app.current_user_id', true), ''), '0')::integer)
);
```

---

### Проблема 6: 400 на /students/textbooks

**Симптом:** После успешной регистрации страница не загружается, ошибка 400/403

**Причины:**
1. Student record не был создан (из-за проблемы 5)
2. RLS на `textbooks`, `chapters`, `paragraphs` блокировала глобальный контент

**Решение:**

1. Создать недостающий student record:
```sql
INSERT INTO students (school_id, user_id, student_code, grade_level, is_deleted)
VALUES (3, 6, 'STU-PUB-001', 7, false);
```

2. Обновить RLS для контента - разрешить SELECT для глобального контента (`school_id IS NULL`):

```sql
-- TEXTBOOKS
CREATE POLICY textbooks_select_policy ON textbooks FOR SELECT
USING (
    (COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
    OR (school_id IS NULL)  -- Глобальный контент
    OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer)
);

-- CHAPTERS (через subquery к textbooks)
CREATE POLICY chapters_select_policy ON chapters FOR SELECT
USING (
    (COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
    OR EXISTS (
        SELECT 1 FROM textbooks t WHERE t.id = chapters.textbook_id
        AND (t.school_id IS NULL OR t.school_id = ...)
    )
);

-- PARAGRAPHS (через chapters -> textbooks)
CREATE POLICY paragraphs_select_policy ON paragraphs FOR SELECT
USING (
    (COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
    OR EXISTS (
        SELECT 1 FROM chapters c JOIN textbooks t ON t.id = c.textbook_id
        WHERE c.id = paragraphs.chapter_id
        AND (t.school_id IS NULL OR t.school_id = ...)
    )
);
```

---

## Файлы изменены

| Файл | Изменения |
|------|-----------|
| `backend/app/core/tenancy.py` | Добавлена функция `set_current_user_id()` |
| `backend/app/api/dependencies.py` | Вызов `set_current_user_id()` для всех пользователей |
| `backend/alembic/versions/b2c3d4e5f6a7_fix_invitation_codes_rls_select.py` | Полная миграция с RLS политиками |
| `student-app/src/lib/api/auth.ts` | `code` → `invitation_code` в интерфейсе |
| `student-app/src/app/[locale]/(auth)/onboarding/page.tsx` | `code` → `invitation_code` в вызове API |

---

## Финальное состояние RLS политик

```
tablename         | policyname                      | cmd
------------------+---------------------------------+--------
chapters          | chapters_modify_policy          | ALL
chapters          | chapters_select_policy          | SELECT
invitation_codes  | invitation_codes_select_policy  | SELECT  (OPEN)
paragraphs        | paragraphs_modify_policy        | ALL
paragraphs        | paragraphs_select_policy        | SELECT
school_classes    | school_classes_select_policy    | SELECT  (OPEN)
schools           | schools_select_policy           | SELECT  (OPEN)
students          | students_insert_policy          | INSERT  (self-registration)
students          | students_select_policy          | SELECT
textbooks         | textbooks_select_policy         | SELECT  (global + school)
users             | users_update_policy             | UPDATE  (self-update)
```

---

## Ключевые выводы

1. **RLS и Onboarding конфликтуют** - при onboarding пользователь не имеет `school_id`, но должен иметь доступ к:
   - Валидации кодов приглашения
   - Информации о школе
   - Обновлению своего профиля
   - Созданию student record

2. **Решение** - использовать `app.current_user_id` для разрешения операций над своими данными, независимо от `school_id`

3. **Глобальный контент** (`school_id IS NULL`) должен быть доступен всем аутентифицированным пользователям

4. **Frontend/Backend синхронизация** - критично проверять соответствие имён полей в схемах

---

## Команды для проверки

```bash
# Проверить RLS политики
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -c "
SELECT tablename, policyname, cmd FROM pg_policies ORDER BY tablename;"

# Проверить студентов
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -c "
SELECT u.id, u.email, u.school_id, s.id as student_id FROM users u
LEFT JOIN students s ON s.user_id = u.id WHERE u.role = 'student';"

# Проверить публичные коды
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -c "
SELECT code, school_id, grade_level, is_active FROM invitation_codes WHERE code LIKE 'PUBLIC%';"
```
