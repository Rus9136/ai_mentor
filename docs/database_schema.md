# Документация по структуре базы данных AI Mentor Platform

## Содержание
- [Обзор](#обзор)
- [Диаграмма связей](#диаграмма-связей)
- [Таблицы базы данных](#таблицы-базы-данных)
- [Enum типы](#enum-типы)
- [Инструкция по работе с миграциями](#инструкция-по-работе-с-миграциями)

---

## Обзор

База данных AI Mentor Platform использует PostgreSQL с расширением **pgvector** для векторного поиска. Система управления миграциями - **Alembic**.

### Основные компоненты системы:
1. **Организационная структура** - школы, пользователи, учителя, ученики, классы
2. **Образовательный контент** - учебники, главы, параграфы, тесты, вопросы
3. **Прогресс обучения** - результаты тестов, история освоения материала, адаптивные группы
4. **Аналитика** - сессии обучения, активности, события

---

## Диаграмма связей

```
schools
  ├── users
  │     ├── students → class_students → school_classes
  │     └── teachers → class_teachers → school_classes
  ├── textbooks
  │     └── chapters
  │           ├── paragraphs
  │           │     ├── paragraph_embeddings (векторное представление)
  │           │     ├── tests
  │           │     ├── student_paragraphs (прогресс)
  │           │     ├── mastery_history (история освоения)
  │           │     └── adaptive_groups (адаптивное обучение)
  │           └── tests
  └── assignments
        ├── assignment_tests
        └── student_assignments

students
  ├── test_attempts → test_attempt_answers
  ├── learning_sessions → learning_activities
  ├── analytics_events
  └── sync_queue (синхронизация офлайн/онлайн)
```

---

## Таблицы базы данных

### 1. schools (Школы)

**Описание:** Основная таблица для хранения информации о школах в системе.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| name | VARCHAR(255) | Да | Название школы |
| code | VARCHAR(50) | Да | Уникальный код школы |
| description | TEXT | Нет | Описание школы |
| is_active | BOOLEAN | Да | Активна ли школа (по умолчанию true) |
| email | VARCHAR(255) | Нет | Email школы |
| phone | VARCHAR(50) | Нет | Телефон школы |
| address | TEXT | Нет | Адрес школы |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления (soft delete) |
| is_deleted | BOOLEAN | Да | Удалена ли запись (по умолчанию false) |

**Индексы:**
- `ix_schools_name` (name)
- `ix_schools_code` (code)

**Связи:**
- → users (school_id)
- → students (school_id)
- → teachers (school_id)
- → school_classes (school_id)
- → textbooks (school_id)
- → assignments (school_id)

---

### 2. users (Пользователи)

**Описание:** Хранит информацию о всех пользователях системы (админы, учителя, ученики, родители).

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| school_id | INTEGER | Да | FK → schools.id |
| email | VARCHAR(255) | Да | Email пользователя |
| password_hash | VARCHAR(255) | Да | Хеш пароля |
| is_active | BOOLEAN | Да | Активен ли аккаунт |
| is_verified | BOOLEAN | Да | Подтвержден ли email |
| first_name | VARCHAR(100) | Да | Имя |
| last_name | VARCHAR(100) | Да | Фамилия |
| middle_name | VARCHAR(100) | Нет | Отчество |
| phone | VARCHAR(50) | Нет | Телефон |
| role | userrole | Да | Роль: admin, teacher, student, parent |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удален ли |

**Индексы:**
- `ix_users_school_id` (school_id)
- `ix_users_email` (email)
- `ix_users_role` (role)

**Связи:**
- ← schools (school_id)
- → students (user_id)
- → teachers (user_id)

---

### 3. students (Ученики)

**Описание:** Профили учеников с дополнительной информацией.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| school_id | INTEGER | Да | FK → schools.id |
| user_id | INTEGER | Да | FK → users.id (UNIQUE) |
| student_code | VARCHAR(50) | Да | Код ученика |
| grade_level | INTEGER | Да | Класс обучения |
| birth_date | DATE | Нет | Дата рождения |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удален ли |

**Индексы:**
- `ix_students_school_id` (school_id)
- `ix_students_user_id` (user_id)
- `ix_students_student_code` (student_code)
- `ix_students_grade_level` (grade_level)

**Связи:**
- ← schools (school_id)
- ← users (user_id)
- → class_students (student_id)
- → test_attempts (student_id)
- → mastery_history (student_id)
- → adaptive_groups (student_id)
- → student_assignments (student_id)
- → student_paragraphs (student_id)
- → learning_sessions (student_id)
- → learning_activities (student_id)
- → analytics_events (student_id)
- → sync_queue (student_id)

---

### 4. teachers (Учителя)

**Описание:** Профили учителей.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| school_id | INTEGER | Да | FK → schools.id |
| user_id | INTEGER | Да | FK → users.id (UNIQUE) |
| teacher_code | VARCHAR(50) | Да | Код учителя |
| subject | VARCHAR(100) | Нет | Предмет |
| bio | TEXT | Нет | Биография |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удален ли |

**Индексы:**
- `ix_teachers_school_id` (school_id)
- `ix_teachers_user_id` (user_id)
- `ix_teachers_teacher_code` (teacher_code)

**Связи:**
- ← schools (school_id)
- ← users (user_id)
- → class_teachers (teacher_id)
- → assignments (teacher_id)

---

### 5. school_classes (Классы)

**Описание:** Учебные классы в школе.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| school_id | INTEGER | Да | FK → schools.id |
| name | VARCHAR(100) | Да | Название класса (например, "10А") |
| code | VARCHAR(50) | Да | Код класса |
| grade_level | INTEGER | Да | Уровень класса (1-11) |
| academic_year | VARCHAR(20) | Да | Учебный год (например, "2024-2025") |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удален ли |

**Индексы:**
- `ix_school_classes_school_id` (school_id)
- `ix_school_classes_code` (code)
- `ix_school_classes_grade_level` (grade_level)
- `ix_school_classes_academic_year` (academic_year)

**Ограничения:**
- UNIQUE (school_id, code)

**Связи:**
- ← schools (school_id)
- → class_students (class_id)
- → class_teachers (class_id)
- → assignments (class_id)

---

### 6. class_students (Ученики в классах)

**Описание:** Связь многие-ко-многим между классами и учениками.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| class_id | INTEGER | Да | FK → school_classes.id |
| student_id | INTEGER | Да | FK → students.id |

**Ограничения:**
- UNIQUE (class_id, student_id)

**Связи:**
- ← school_classes (class_id)
- ← students (student_id)

---

### 7. class_teachers (Учителя в классах)

**Описание:** Связь многие-ко-многим между классами и учителями.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| class_id | INTEGER | Да | FK → school_classes.id |
| teacher_id | INTEGER | Да | FK → teachers.id |

**Ограничения:**
- UNIQUE (class_id, teacher_id)

**Связи:**
- ← school_classes (class_id)
- ← teachers (teacher_id)

---

### 8. textbooks (Учебники)

**Описание:** Учебники, используемые в школе. Поддерживает гибридную модель: глобальные учебники (доступны всем школам) и школьные (созданные или кастомизированные конкретной школой).

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| school_id | INTEGER | Нет | FK → schools.id (NULL = глобальный учебник) |
| global_textbook_id | INTEGER | Нет | FK → textbooks.id (ссылка на глобальный при кастомизации) |
| is_customized | BOOLEAN | Да | Модифицирован ли школой (по умолчанию false) |
| title | VARCHAR(255) | Да | Название учебника |
| subject | VARCHAR(100) | Да | Предмет |
| grade_level | INTEGER | Да | Класс |
| author | VARCHAR(255) | Нет | Автор |
| publisher | VARCHAR(255) | Нет | Издательство |
| year | INTEGER | Нет | Год издания |
| isbn | VARCHAR(50) | Нет | ISBN |
| description | TEXT | Нет | Описание |
| is_active | BOOLEAN | Да | Активен ли |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удален ли |

**Индексы:**
- `ix_textbooks_school_id` (school_id)
- `ix_textbooks_global_textbook_id` (global_textbook_id)
- `ix_textbooks_school_global` (school_id, global_textbook_id)
- `ix_textbooks_title` (title)
- `ix_textbooks_subject` (subject)
- `ix_textbooks_grade_level` (grade_level)

**Связи:**
- ← schools (school_id)
- → chapters (textbook_id)

---

### 9. chapters (Главы)

**Описание:** Главы учебников.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| textbook_id | INTEGER | Да | FK → textbooks.id |
| title | VARCHAR(255) | Да | Название главы |
| number | INTEGER | Да | Номер главы |
| order | INTEGER | Да | Порядок сортировки |
| description | TEXT | Нет | Описание главы |
| **learning_objective** | **TEXT** | **Нет** | **Цель обучения (широкая, долгосрочная)** |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удалена ли |

**Индексы:**
- `ix_chapters_textbook_id` (textbook_id)

**Связи:**
- ← textbooks (textbook_id)
- → paragraphs (chapter_id)
- → tests (chapter_id)

---

### 10. paragraphs (Параграфы)

**Описание:** Параграфы в главах учебника.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| chapter_id | INTEGER | Да | FK → chapters.id |
| title | VARCHAR(255) | Нет | Название параграфа |
| number | INTEGER | Да | Номер параграфа |
| order | INTEGER | Да | Порядок сортировки |
| content | TEXT | Да | Полное содержание параграфа |
| summary | TEXT | Нет | Краткое содержание |
| **learning_objective** | **TEXT** | **Нет** | **Цель обучения для параграфа (широкая)** |
| **lesson_objective** | **TEXT** | **Нет** | **Цель урока (конкретная, краткосрочная)** |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удален ли |

**Индексы:**
- `ix_paragraphs_chapter_id` (chapter_id)

**Связи:**
- ← chapters (chapter_id)
- → paragraph_embeddings (paragraph_id)
- → tests (paragraph_id)
- → mastery_history (paragraph_id)
- → adaptive_groups (paragraph_id)
- → student_paragraphs (paragraph_id)
- → learning_activities (paragraph_id)

---

### 11. paragraph_embeddings (Векторные эмбеддинги параграфов)

**Описание:** Векторные представления текста для RAG (Retrieval-Augmented Generation).

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| paragraph_id | INTEGER | Да | FK → paragraphs.id |
| chunk_index | INTEGER | Да | Индекс части текста |
| chunk_text | TEXT | Да | Текст части |
| embedding | VECTOR(1536) | Да | Векторное представление (OpenAI) |
| model | VARCHAR(100) | Да | Модель эмбеддинга (по умолчанию text-embedding-3-small) |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удален ли |

**Индексы:**
- `ix_paragraph_embeddings_paragraph_id` (paragraph_id)

**Связи:**
- ← paragraphs (paragraph_id)

---

### 12. tests (Тесты)

**Описание:** Тесты для проверки знаний. Поддерживает гибридную модель: глобальные тесты (доступны всем школам) и школьные (созданные конкретной школой).

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| school_id | INTEGER | Нет | FK → schools.id (NULL = глобальный тест) |
| chapter_id | INTEGER | Нет | FK → chapters.id |
| paragraph_id | INTEGER | Нет | FK → paragraphs.id |
| title | VARCHAR(255) | Да | Название теста |
| description | TEXT | Нет | Описание |
| difficulty | difficultylevel | Да | Сложность: easy, medium, hard |
| time_limit | INTEGER | Нет | Ограничение по времени (секунды) |
| passing_score | FLOAT | Да | Проходной балл (0.0-1.0, по умолчанию 0.7) |
| is_active | BOOLEAN | Да | Активен ли |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удален ли |

**Индексы:**
- `ix_tests_school_id` (school_id)
- `ix_tests_chapter_id` (chapter_id)
- `ix_tests_paragraph_id` (paragraph_id)

**Связи:**
- ← chapters (chapter_id)
- ← paragraphs (paragraph_id)
- → questions (test_id)
- → test_attempts (test_id)
- → assignment_tests (test_id)
- → learning_activities (test_id)

---

### 13. questions (Вопросы)

**Описание:** Вопросы в тестах.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| test_id | INTEGER | Да | FK → tests.id |
| order | INTEGER | Да | Порядок в тесте |
| question_type | questiontype | Да | single_choice, multiple_choice, true_false, short_answer |
| question_text | TEXT | Да | Текст вопроса |
| explanation | TEXT | Нет | Объяснение правильного ответа |
| points | FLOAT | Да | Баллы за вопрос (по умолчанию 1.0) |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удален ли |

**Индексы:**
- `ix_questions_test_id` (test_id)

**Связи:**
- ← tests (test_id)
- → question_options (question_id)
- → test_attempt_answers (question_id)

---

### 14. question_options (Варианты ответов)

**Описание:** Варианты ответов на вопросы.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| question_id | INTEGER | Да | FK → questions.id |
| order | INTEGER | Да | Порядок отображения |
| option_text | TEXT | Да | Текст варианта |
| is_correct | BOOLEAN | Да | Правильный ли ответ |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удален ли |

**Индексы:**
- `ix_question_options_question_id` (question_id)

**Связи:**
- ← questions (question_id)

---

### 15. test_attempts (Попытки прохождения тестов)

**Описание:** История попыток прохождения тестов учениками.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| student_id | INTEGER | Да | FK → students.id |
| test_id | INTEGER | Да | FK → tests.id |
| school_id | INTEGER | Да | FK → schools.id (денормализован для производительности) |
| attempt_number | INTEGER | Да | Номер попытки (по умолчанию 1) |
| status | attemptstatus | Да | in_progress, completed, abandoned |
| started_at | TIMESTAMP | Да | Время начала |
| completed_at | TIMESTAMP | Нет | Время завершения |
| score | FLOAT | Нет | Оценка (0.0-1.0) |
| points_earned | FLOAT | Нет | Набранные баллы |
| total_points | FLOAT | Нет | Всего баллов |
| passed | BOOLEAN | Нет | Пройден ли тест |
| time_spent | INTEGER | Нет | Затраченное время (секунды) |
| synced_at | TIMESTAMP | Нет | Время синхронизации |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |

**Индексы:**
- `ix_test_attempts_school_id` (school_id)
- `ix_test_attempts_school_student` (school_id, student_id)
- `ix_test_attempts_school_created` (school_id, created_at)
- `ix_test_attempts_student_id` (student_id)
- `ix_test_attempts_test_id` (test_id)
- `ix_test_attempts_status` (status)

**Связи:**
- ← students (student_id)
- ← tests (test_id)
- → test_attempt_answers (attempt_id)

---

### 16. test_attempt_answers (Ответы на вопросы)

**Описание:** Ответы ученика на вопросы в попытке теста.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| attempt_id | INTEGER | Да | FK → test_attempts.id |
| question_id | INTEGER | Да | FK → questions.id |
| selected_option_ids | JSON | Нет | ID выбранных вариантов (JSON массив) |
| answer_text | TEXT | Нет | Текстовый ответ |
| is_correct | BOOLEAN | Нет | Правильный ли ответ |
| points_earned | FLOAT | Нет | Набранные баллы |
| answered_at | TIMESTAMP | Да | Время ответа |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |

**Индексы:**
- `ix_test_attempt_answers_attempt_id` (attempt_id)
- `ix_test_attempt_answers_question_id` (question_id)

**Связи:**
- ← test_attempts (attempt_id)
- ← questions (question_id)

---

### 17. mastery_history (История освоения материала)

**Описание:** Трекинг прогресса освоения параграфов учениками.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| student_id | INTEGER | Да | FK → students.id |
| paragraph_id | INTEGER | Да | FK → paragraphs.id |
| school_id | INTEGER | Да | FK → schools.id (денормализован для производительности) |
| mastery_score | FLOAT | Да | Оценка освоения (0.0-1.0) |
| attempts_count | INTEGER | Да | Количество попыток |
| success_rate | FLOAT | Да | Процент успеха (по умолчанию 0.0) |
| recorded_at | TIMESTAMP | Да | Время записи |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |

**Индексы:**
- `ix_mastery_history_school_id` (school_id)
- `ix_mastery_history_school_student` (school_id, student_id)
- `ix_mastery_history_school_paragraph` (school_id, paragraph_id)
- `ix_mastery_history_student_id` (student_id)
- `ix_mastery_history_paragraph_id` (paragraph_id)
- `ix_mastery_history_recorded_at` (recorded_at)

**Связи:**
- ← students (student_id)
- ← paragraphs (paragraph_id)

---

### 18. adaptive_groups (Адаптивные группы)

**Описание:** Распределение учеников по группам сложности для адаптивного обучения.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| student_id | INTEGER | Да | FK → students.id |
| paragraph_id | INTEGER | Да | FK → paragraphs.id |
| school_id | INTEGER | Да | FK → schools.id (денормализован для производительности) |
| group_name | VARCHAR(10) | Да | Название группы (A, B, C) |
| assigned_at | TIMESTAMP | Да | Время назначения |
| mastery_score | FLOAT | Да | Оценка освоения |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |

**Индексы:**
- `ix_adaptive_groups_school_id` (school_id)
- `ix_adaptive_groups_school_student` (school_id, student_id)
- `ix_adaptive_groups_student_id` (student_id)
- `ix_adaptive_groups_paragraph_id` (paragraph_id)
- `ix_adaptive_groups_group_name` (group_name)

**Связи:**
- ← students (student_id)
- ← paragraphs (paragraph_id)

---

### 19. assignments (Домашние задания)

**Описание:** Задания, назначенные классам учителями.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| school_id | INTEGER | Да | FK → schools.id |
| class_id | INTEGER | Да | FK → school_classes.id |
| teacher_id | INTEGER | Да | FK → teachers.id |
| title | VARCHAR(255) | Да | Название задания |
| description | TEXT | Нет | Описание |
| due_date | TIMESTAMP | Нет | Срок сдачи |
| is_active | BOOLEAN | Да | Активно ли |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удалено ли |

**Индексы:**
- `ix_assignments_school_id` (school_id)
- `ix_assignments_class_id` (class_id)
- `ix_assignments_teacher_id` (teacher_id)
- `ix_assignments_due_date` (due_date)

**Связи:**
- ← schools (school_id)
- ← school_classes (class_id)
- ← teachers (teacher_id)
- → assignment_tests (assignment_id)
- → student_assignments (assignment_id)

---

### 20. assignment_tests (Тесты в заданиях)

**Описание:** Связь многие-ко-многим между заданиями и тестами.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| assignment_id | INTEGER | Да | FK → assignments.id |
| test_id | INTEGER | Да | FK → tests.id |
| order | INTEGER | Да | Порядок теста в задании (по умолчанию 0) |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления (soft delete) |
| is_deleted | BOOLEAN | Да | Удалена ли запись (по умолчанию false) |

**Индексы:**
- `ix_assignment_tests_is_deleted_created` (is_deleted, created_at)

**Связи:**
- ← assignments (assignment_id)
- ← tests (test_id)

**Примечание:** Поля soft delete добавлены в миграции 007 (исправление ошибки миграции 001)

---

### 21. student_assignments (Задания учеников)

**Описание:** Прогресс выполнения заданий учениками.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| student_id | INTEGER | Да | FK → students.id |
| assignment_id | INTEGER | Да | FK → assignments.id |
| status | assignmentstatus | Да | not_started, in_progress, completed, overdue |
| started_at | TIMESTAMP | Нет | Время начала |
| completed_at | TIMESTAMP | Нет | Время завершения |
| progress_percentage | INTEGER | Да | Процент выполнения (по умолчанию 0) |
| score | FLOAT | Нет | Оценка |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |
| deleted_at | TIMESTAMP | Нет | Дата удаления |
| is_deleted | BOOLEAN | Да | Удалено ли |

**Индексы:**
- `ix_student_assignments_student_id` (student_id)
- `ix_student_assignments_assignment_id` (assignment_id)
- `ix_student_assignments_status` (status)

**Связи:**
- ← students (student_id)
- ← assignments (assignment_id)

---

### 22. student_paragraphs (Прогресс чтения параграфов)

**Описание:** Отслеживание прогресса изучения параграфов учениками.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| student_id | INTEGER | Да | FK → students.id |
| paragraph_id | INTEGER | Да | FK → paragraphs.id |
| school_id | INTEGER | Да | FK → schools.id (денормализован для производительности) |
| is_completed | BOOLEAN | Да | Завершен ли параграф |
| time_spent | INTEGER | Да | Время изучения (секунды, по умолчанию 0) |
| last_accessed_at | TIMESTAMP | Нет | Последнее открытие |
| completed_at | TIMESTAMP | Нет | Время завершения |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |

**Индексы:**
- `ix_student_paragraphs_school_id` (school_id)
- `ix_student_paragraphs_school_student` (school_id, student_id)
- `ix_student_paragraphs_student_id` (student_id)
- `ix_student_paragraphs_paragraph_id` (paragraph_id)

**Связи:**
- ← students (student_id)
- ← paragraphs (paragraph_id)

---

### 23. learning_sessions (Учебные сессии)

**Описание:** Сессии обучения учеников в системе.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| student_id | INTEGER | Да | FK → students.id |
| school_id | INTEGER | Да | FK → schools.id (денормализован для производительности) |
| session_start | TIMESTAMP | Да | Начало сессии |
| session_end | TIMESTAMP | Нет | Конец сессии |
| duration | INTEGER | Нет | Длительность (секунды) |
| device_id | VARCHAR(255) | Нет | ID устройства |
| device_type | VARCHAR(50) | Нет | Тип устройства |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |

**Индексы:**
- `ix_learning_sessions_school_id` (school_id)
- `ix_learning_sessions_school_start` (school_id, session_start)
- `ix_learning_sessions_student_id` (student_id)
- `ix_learning_sessions_session_start` (session_start)

**Связи:**
- ← students (student_id)
- → learning_activities (session_id)

---

### 24. learning_activities (Учебные активности)

**Описание:** Детальная запись активностей ученика во время сессии.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| session_id | INTEGER | Да | FK → learning_sessions.id |
| student_id | INTEGER | Да | FK → students.id |
| school_id | INTEGER | Да | FK → schools.id (денормализован для производительности) |
| activity_type | activitytype | Да | read_paragraph, watch_video, complete_test, ask_question, view_explanation |
| activity_timestamp | TIMESTAMP | Да | Время активности |
| duration | INTEGER | Нет | Длительность (секунды) |
| paragraph_id | INTEGER | Нет | FK → paragraphs.id |
| test_id | INTEGER | Нет | FK → tests.id |
| metadata | JSON | Нет | Дополнительные данные |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |

**Индексы:**
- `ix_learning_activities_school_id` (school_id)
- `ix_learning_activities_school_timestamp` (school_id, activity_timestamp)
- `ix_learning_activities_school_type` (school_id, activity_type)
- `ix_learning_activities_session_id` (session_id)
- `ix_learning_activities_activity_type` (activity_type)
- `ix_learning_activities_activity_timestamp` (activity_timestamp)

**Связи:**
- ← learning_sessions (session_id)
- ← students (student_id)
- ← paragraphs (paragraph_id)
- ← tests (test_id)

---

### 25. analytics_events (Аналитические события)

**Описание:** События для аналитики поведения пользователей.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| student_id | INTEGER | Нет | FK → students.id |
| school_id | INTEGER | Нет | FK → schools.id (nullable для системных событий) |
| event_type | VARCHAR(100) | Да | Тип события |
| event_timestamp | TIMESTAMP | Да | Время события |
| event_data | JSON | Нет | Данные события |
| user_agent | VARCHAR(500) | Нет | User-Agent браузера |
| ip_address | VARCHAR(50) | Нет | IP адрес |
| device_type | VARCHAR(50) | Нет | Тип устройства |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |

**Индексы:**
- `ix_analytics_events_school_id` (school_id)
- `ix_analytics_events_school_timestamp` (school_id, event_timestamp)
- `ix_analytics_events_student_id` (student_id)
- `ix_analytics_events_event_type` (event_type)
- `ix_analytics_events_event_timestamp` (event_timestamp)

**Связи:**
- ← students (student_id)

---

### 26. sync_queue (Очередь синхронизации)

**Описание:** Очередь для синхронизации данных между офлайн и онлайн режимами.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| student_id | INTEGER | Да | FK → students.id |
| school_id | INTEGER | Да | FK → schools.id (денормализован для производительности) |
| entity_type | VARCHAR(100) | Да | Тип сущности |
| entity_id | INTEGER | Нет | ID сущности |
| operation | VARCHAR(20) | Да | Операция (create, update, delete) |
| data | JSON | Да | Данные для синхронизации (JSON объект) |
| status | syncstatus | Да | pending, syncing, completed, failed |
| attempts | INTEGER | Да | Количество попыток (по умолчанию 0) |
| last_attempt_at | TIMESTAMP | Нет | Время последней попытки |
| error_message | TEXT | Нет | Сообщение об ошибке |
| device_id | VARCHAR(255) | Нет | ID устройства |
| created_at_device | TIMESTAMP | Да | Время создания на устройстве |
| created_at | TIMESTAMP | Да | Дата создания на сервере |
| updated_at | TIMESTAMP | Да | Дата обновления |

**Индексы:**
- `ix_sync_queue_school_id` (school_id)
- `ix_sync_queue_school_status` (school_id, status)
- `ix_sync_queue_student_id` (student_id)
- `ix_sync_queue_entity_type` (entity_type)
- `ix_sync_queue_status` (status)

**Связи:**
- ← students (student_id)

---

### 27. system_settings (Системные настройки)

**Описание:** Глобальные настройки системы.

| Колонка | Тип | Обязательно | Описание |
|---------|-----|-------------|----------|
| id | INTEGER | Да | Первичный ключ |
| key | VARCHAR(255) | Да | Ключ настройки (UNIQUE) |
| value | TEXT | Нет | Значение |
| description | TEXT | Нет | Описание настройки |
| is_public | BOOLEAN | Да | Публичная ли настройка (по умолчанию false) |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |

**Индексы:**
- `ix_system_settings_key` (key)

**Связи:**
- Нет

---

## Enum типы

### userrole
Роли пользователей:
- `admin` - Администратор
- `teacher` - Учитель
- `student` - Ученик
- `parent` - Родитель

### difficultylevel
Уровни сложности:
- `easy` - Легкий
- `medium` - Средний
- `hard` - Сложный

### questiontype
Типы вопросов:
- `single_choice` - Один вариант ответа
- `multiple_choice` - Несколько вариантов ответа
- `true_false` - Верно/Неверно
- `short_answer` - Короткий текстовый ответ

### attemptstatus
Статусы попыток теста:
- `in_progress` - В процессе
- `completed` - Завершена
- `abandoned` - Прервана

### assignmentstatus
Статусы заданий:
- `not_started` - Не начато
- `in_progress` - В процессе
- `completed` - Завершено
- `overdue` - Просрочено

### activitytype
Типы активностей:
- `read_paragraph` - Чтение параграфа
- `watch_video` - Просмотр видео
- `complete_test` - Прохождение теста
- `ask_question` - Задать вопрос
- `view_explanation` - Просмотр объяснения

### syncstatus
Статусы синхронизации:
- `pending` - Ожидает
- `syncing` - Синхронизируется
- `completed` - Завершена
- `failed` - Ошибка

---

## Инструкция по работе с миграциями

### Обзор системы миграций

Проект использует **Alembic** для управления миграциями базы данных. Все миграции находятся в директории `backend/alembic/versions/`.

### Текущие миграции

```
001 → Initial schema with all tables
002 → Add learning and lesson objectives
003 → Add learning_objective to paragraphs
004 → Change TEXT to JSON for selected_option_ids and sync_queue.data
005 → Add composite indexes for query optimization
006 → Add soft delete indexes for filtering
007 → Fix assignment_tests soft delete fields
008 → Add school_id to progress tables for data isolation (текущая)
```

**Версия базы данных:** 008

### Оптимизация индексов (миграции 005-006)

В миграциях 005-006 были добавлены индексы для оптимизации производительности:

**Составные индексы (005):**
- `ix_test_attempts_student_created` (student_id, created_at) - для запросов "последние попытки ученика"
- `ix_mastery_history_student_paragraph` (student_id, paragraph_id) - для прогресса по параграфам
- `ix_student_assignments_student_status` (student_id, status) - для фильтрации заданий по статусу
- `ix_paragraph_embeddings_paragraph_chunk` (paragraph_id, chunk_index) - для поиска эмбеддингов

**Индексы для soft delete (006):**
- `ix_*_is_deleted_created` (is_deleted, created_at) - на все таблицы с SoftDeleteModel
- Ускоряет запросы с фильтром `WHERE is_deleted = false ORDER BY created_at`

### Изоляция данных (миграция 008)

Миграция 008 добавляет denormalized `school_id` во все таблицы прогресса для улучшения изоляции данных и производительности:

**Добавлен school_id в таблицы:**
- `test_attempts` - для быстрой выборки попыток по школе
- `mastery_history` - для аналитики освоения материала по школам
- `adaptive_groups` - для группировки учеников внутри школы
- `student_paragraphs` - для отслеживания прогресса чтения
- `learning_sessions` - для аналитики сессий по школам
- `learning_activities` - для детальной аналитики активностей
- `analytics_events` - для событийной аналитики (nullable)
- `sync_queue` - для управления синхронизацией по школам

**Гибридная модель контента:**
- `textbooks.school_id` - теперь nullable (NULL = глобальный учебник)
- `textbooks.global_textbook_id` - ссылка на глобальный учебник при кастомизации
- `textbooks.is_customized` - флаг модификации контента школой
- `tests.school_id` - nullable (NULL = глобальный тест)

**Новые индексы (008):**
- Single: `ix_*_school_id` на всех таблицах с school_id
- Composite: `ix_test_attempts_school_student`, `ix_test_attempts_school_created`
- Composite: `ix_mastery_history_school_student`, `ix_mastery_history_school_paragraph`
- Composite: `ix_learning_activities_school_timestamp`, `ix_learning_activities_school_type`
- Composite: `ix_analytics_events_school_timestamp`, `ix_sync_queue_school_status`
- И другие для оптимизации запросов по school_id

**Преимущества:**
- ✅ Быстрая фильтрация данных по школам без JOIN через students
- ✅ Готовность к партицированию и шардированию по school_id
- ✅ Гибкая модель контента (глобальный + школьный)
- ✅ Улучшенная производительность аналитических запросов

---

### 1. Создание новой миграции

#### Шаг 1: Создать файл миграции

Создайте файл в директории `backend/alembic/versions/` с именем в формате:
```
00X_описание_миграции.py
```

Где X - следующий номер миграции.

#### Шаг 2: Структура файла миграции

```python
"""Описание миграции

Revision ID: 00X
Revises: 00Y  # предыдущая версия
Create Date: YYYY-MM-DD

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '00X'
down_revision: Union[str, None] = '00Y'  # предыдущая версия
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Применение миграции"""
    # Добавьте операции для обновления БД
    pass


def downgrade() -> None:
    """Откат миграции"""
    # Добавьте операции для отката БД
    pass
```

---

### 2. Примеры операций с миграциями

#### Добавление колонки

```python
def upgrade() -> None:
    op.add_column('table_name', sa.Column('column_name', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('table_name', 'column_name')
```

#### Удаление колонки

```python
def upgrade() -> None:
    op.drop_column('table_name', 'column_name')

def downgrade() -> None:
    op.add_column('table_name', sa.Column('column_name', sa.Text(), nullable=True))
```

#### Изменение типа колонки

```python
def upgrade() -> None:
    op.alter_column('table_name', 'column_name',
                    existing_type=sa.VARCHAR(50),
                    type_=sa.VARCHAR(100),
                    existing_nullable=True)

def downgrade() -> None:
    op.alter_column('table_name', 'column_name',
                    existing_type=sa.VARCHAR(100),
                    type_=sa.VARCHAR(50),
                    existing_nullable=True)
```

#### Создание индекса

```python
def upgrade() -> None:
    op.create_index('ix_table_column', 'table_name', ['column_name'])

def downgrade() -> None:
    op.drop_index('ix_table_column', 'table_name')
```

#### Создание новой таблицы

```python
def upgrade() -> None:
    op.create_table(
        'new_table',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_new_table_name', 'new_table', ['name'])

def downgrade() -> None:
    op.drop_index('ix_new_table_name', 'new_table')
    op.drop_table('new_table')
```

---

### 3. Обновление модели SQLAlchemy

После создания миграции обновите соответствующую модель в `backend/app/models/`:

```python
from sqlalchemy import Column, Text

class MyModel(SoftDeleteModel):
    __tablename__ = "my_table"

    # Новая колонка
    new_column = Column(Text, nullable=True)  # Добавьте описание
```

---

### 4. Применение миграции

#### Через Docker (рекомендуется для production)

```bash
# Применить миграцию напрямую через SQL
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "
ALTER TABLE table_name ADD COLUMN column_name TEXT;
"

# Обновить версию миграции в БД
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "
UPDATE alembic_version SET version_num = '00X';
"
```

#### Через Alembic (для development с установленными зависимостями)

```bash
# Активировать виртуальное окружение
source .venv/bin/activate

# Перейти в директорию backend
cd backend

# Применить все миграции
alembic upgrade head

# Применить конкретную миграцию
alembic upgrade 00X

# Откатить одну миграцию
alembic downgrade -1

# Откатить до конкретной версии
alembic downgrade 00X
```

---

### 5. Проверка результатов

#### Проверить текущую версию миграции

```bash
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "
SELECT version_num FROM alembic_version;
"
```

#### Проверить структуру таблицы

```bash
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\d table_name"
```

#### Посмотреть историю миграций

```bash
cd backend
source ../.venv/bin/activate
alembic history
```

---

### 6. Создание SQL версии миграции (опционально)

Для удобства создайте дублирующий SQL файл:

**Файл:** `backend/alembic/versions/00X_описание.sql`

```sql
-- Описание миграции

-- Добавление новой колонки
ALTER TABLE table_name ADD COLUMN column_name TEXT;

-- Создание индекса (если нужно)
CREATE INDEX ix_table_column ON table_name(column_name);
```

---

### 7. Пример: Добавление колонки description в таблицу tests

#### Шаг 1: Создать файл миграции

**Файл:** `backend/alembic/versions/004_add_description_to_tests.py`

```python
"""Add description to tests

Revision ID: 004
Revises: 003
Create Date: 2025-10-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tests', sa.Column('detailed_description', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('tests', 'detailed_description')
```

#### Шаг 2: Обновить модель

**Файл:** `backend/app/models/test.py`

```python
class Test(SoftDeleteModel):
    __tablename__ = "tests"

    # ... существующие поля ...
    description = Column(Text, nullable=True)
    detailed_description = Column(Text, nullable=True)  # Новое поле
```

#### Шаг 3: Применить миграцию

```bash
# Через Docker
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "
ALTER TABLE tests ADD COLUMN detailed_description TEXT;
"

docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "
UPDATE alembic_version SET version_num = '004';
"
```

#### Шаг 4: Проверить

```bash
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\d tests"
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "
SELECT version_num FROM alembic_version;
"
```

---

### 8. Лучшие практики

1. **Всегда создавайте функцию downgrade** - для возможности отката миграции
2. **Тестируйте миграции** на тестовой базе перед применением на production
3. **Делайте маленькие миграции** - лучше несколько маленьких, чем одна большая
4. **Используйте осмысленные имена** - описание должно быть понятным
5. **Не изменяйте существующие миграции** - создавайте новые для исправлений
6. **Документируйте сложные миграции** - добавляйте комментарии в код
7. **Проверяйте индексы** - после добавления колонок может потребоваться индекс
8. **Обновляйте модели** - синхронизируйте модели SQLAlchemy с миграциями

---

### 9. Troubleshooting

#### Проблема: Alembic не находится

```bash
# Установите в виртуальное окружение
source .venv/bin/activate
pip install alembic sqlalchemy psycopg2-binary
```

#### Проблема: Ошибка подключения к БД

```bash
# Проверьте, что PostgreSQL запущен
docker ps | grep ai_mentor_postgres

# Проверьте настройки в alembic.ini
cat backend/alembic.ini | grep sqlalchemy.url
```

#### Проблема: Версия миграции не совпадает

```bash
# Проверьте текущую версию в БД
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "
SELECT version_num FROM alembic_version;
"

# Установите нужную версию вручную
docker exec ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "
UPDATE alembic_version SET version_num = '00X';
"
```

---

### 10. Полезные команды

```bash
# Посмотреть текущую версию миграции
alembic current

# Посмотреть историю миграций
alembic history

# Посмотреть SQL, который будет выполнен (без применения)
alembic upgrade head --sql

# Создать автоматическую миграцию на основе изменений в моделях
alembic revision --autogenerate -m "Описание"

# Откатить все миграции
alembic downgrade base
```

---

## Заключение

Эта документация описывает полную структуру базы данных AI Mentor Platform и процесс работы с миграциями. При добавлении новых функций следуйте описанным практикам для поддержания согласованности схемы базы данных.
