# Session Log: GOCO MVP + Fix Alembic migration graph (safe merge)
  
**Дата:** 2025-12-12  
**Время:** 16:30  
**Задача:** Подготовить безопасный merge: исправить Alembic-цепочку (duplicate revision + multi-head), добавить минимальный GOCO MVP (global справочники + `paragraph_outcomes`) с RLS, и закрыть дырку в `fork_textbook()` (копирование `key_terms/questions`).
  
---
  
## Контекст
  
- В репозитории была **проблема Alembic графа**: дублирующийся `revision='010'` и несколько heads.
- В production ранее поля `paragraphs.key_terms/questions` добавлялись вручную (см. `SESSION_LOG_ADD_PARAGRAPH_FIELDS_2025-11-11_07-02.md`), что требует **идемпотентности** миграций.
- Платформа multi-tenant: изоляция через `school_id` + RLS с tenant-context через session vars:
  - `app.current_tenant_id`
  - `app.is_super_admin`
  
---
  
## Выполнено
  
### 1) Fix Alembic graph (без удаления истории миграций)
  
- **`backend/alembic/versions/010_rename_order_to_sort_order.py`**
  - сохранён файл (история не удаляется),
  - исправлен конфликт revision id: `revision="b7e1f9a3c2d4"`, `down_revision="d6cfba8cd6fd"`,
  - сама миграция сделана **идемпотентной** (переименование колонок выполняется только если нужно).
  
- **`backend/alembic/versions/011_add_key_terms_and_questions_to_paragraphs.py`**
  - сделана **идемпотентной**:
    - `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...`
    - `ALTER TABLE ... DROP COLUMN IF EXISTS ...`
  
- Добавлена merge-миграция:
  - **`backend/alembic/versions/c3a8d9e1f0b2_merge_heads_011_and_sort_order.py`**
  - `down_revision = ("b7e1f9a3c2d4", "011")`
  - без schema changes, только сводит граф к single-head.
  
### 2) GOCO MVP миграции (global + mapping)
  
- **`backend/alembic/versions/012_add_goso_core_tables.py`** (revision `012`)
  - таблицы: `subjects`, `frameworks`, `goso_sections`, `goso_subsections`, `learning_outcomes`
  - RLS:
    - `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY`
    - `SELECT`: разрешён всем (global read)
    - `ALL`: только при `app.is_super_admin = 'true'` (global write restricted)
  
- **`backend/alembic/versions/013_add_paragraph_outcomes.py`** (revision `013`)
  - таблица: `paragraph_outcomes` (параграф ↔ цель обучения)
  - RLS:
    - `SELECT`: разрешён для параграфов, доступных текущему тенанту (школьный учебник) **или** global-контента (`textbooks.school_id IS NULL`), либо SUPER_ADMIN
    - `ALL`: разрешён только для параграфов текущего тенанта (школьный контент), либо SUPER_ADMIN  
      (запрещает школе менять связи для global параграфов)
  
### 3) Fix: `fork_textbook()` копирует `key_terms/questions`
  
- **`backend/app/repositories/textbook_repo.py`**
  - при кастомизации (fork) параграфа добавлено копирование:
    - `key_terms=source_paragraph.key_terms`
    - `questions=source_paragraph.questions`
  
---
  
## Список изменённых файлов
  
- `SESSION_LOG_GOSO_MVP_ALEMBIC_GRAPH_FIX_2025-12-12_16-30.md`
- `backend/alembic/versions/010_rename_order_to_sort_order.py`
- `backend/alembic/versions/011_add_key_terms_and_questions_to_paragraphs.py`
- `backend/alembic/versions/c3a8d9e1f0b2_merge_heads_011_and_sort_order.py`
- `backend/alembic/versions/012_add_goso_core_tables.py`
- `backend/alembic/versions/013_add_paragraph_outcomes.py`
- `backend/app/repositories/textbook_repo.py`
- `docs/GOSO_INTEGRATION_PLAN.md`
  
---
  
## Фактический вывод Alembic команд
  
Команда:
  
```bash
cd /home/rus/projects/ai_mentor/backend
../.venv/bin/alembic heads
../.venv/bin/alembic branches
../.venv/bin/alembic history --verbose
```
  
Вывод:
  
```text
### alembic heads
013 (head)

### alembic branches
010 (branchpoint)
    -> 9fe5023de6ad
    -> 011

### alembic history --verbose
Rev: 013 (head)
Parent: 012
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/013_add_paragraph_outcomes.py

    add paragraph_outcomes (paragraph ↔ goso learning outcomes mapping)
    
    Creates `paragraph_outcomes` which links textbook paragraphs to ГОСО learning outcomes.
    
    RLS strategy (critical for multi-tenant safety):
    - SELECT: allowed if the linked paragraph is visible for current tenant
      (tenant textbook OR global textbook) OR if app.is_super_admin=true.
    - INSERT/UPDATE/DELETE: allowed only for paragraphs that belong to the current tenant
      (textbooks.school_id = current_tenant_id) OR if app.is_super_admin=true.
      This prevents School ADMIN from modifying mappings for GLOBAL content.
    
    Revision ID: 013
    Revises: 012
    Create Date: 2025-12-12

Rev: 012
Parent: c3a8d9e1f0b2
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/012_add_goso_core_tables.py

    add goso core reference tables (global)
    
    Creates global reference tables for ГОСО:
    - subjects
    - frameworks
    - goso_sections
    - goso_subsections
    - learning_outcomes
    
    MVP scope:
    - No per-school overrides for curriculum_* here (those are Target).
    - Tables are GLOBAL (no school_id) and readable by all authenticated users.
    - Write access is restricted at DB level to SUPER_ADMIN via session variable:
      `app.is_super_admin = 'true'`.
    
    Revision ID: 012
    Revises: c3a8d9e1f0b2
    Create Date: 2025-12-12

Rev: c3a8d9e1f0b2 (mergepoint)
Merges: b7e1f9a3c2d4, 011
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/c3a8d9e1f0b2_merge_heads_011_and_sort_order.py

    merge heads: 011 (paragraph key_terms/questions) + sort_order rename
    
    This is a pure Alembic merge revision to make the migration graph single-head.
    
    Revision ID: c3a8d9e1f0b2
    Revises: b7e1f9a3c2d4, 011
    Create Date: 2025-12-12

Rev: b7e1f9a3c2d4
Parent: d6cfba8cd6fd
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/010_rename_order_to_sort_order.py

    rename order to sort_order (idempotent)
    
    NOTE: This file originally existed in the repo with a duplicate Alembic revision id ('010'),
    which conflicted with `010_add_textbook_versioning.py`. Duplicate revision ids break the
    Alembic graph.
    
    For a safe forward-only fix, we keep the file path for audit/history, but we correct the
    revision id and place it after the current mainline head. The rename itself is idempotent:
    it will only run if the source column exists and the target column does not.
    
    Revision ID: b7e1f9a3c2d4
    Revises: d6cfba8cd6fd
    Create Date: 2025-12-12

Rev: d6cfba8cd6fd
Parent: ea1742b576f3
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/d6cfba8cd6fd_create_mastery_tables.py

    create_mastery_tables
    
    Creates paragraph_mastery and chapter_mastery tables for two-level mastery tracking.
    
    Architecture:
    - paragraph_mastery: Fine-grained tracking per lesson/paragraph
    - chapter_mastery: Aggregated tracking for A/B/C grouping
    - mastery_history: Updated to support both paragraph and chapter changes (polymorphic)
    
    Revision ID: d6cfba8cd6fd
    Revises: ea1742b576f3
    Create Date: 2025-11-07 08:42:32.900052

Rev: ea1742b576f3
Parent: 401bffeccd70
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/ea1742b576f3_add_test_purpose_enum.py

    add_test_purpose_enum
    
    Adds TestPurpose enum to support different test types in the learning workflow.
    
    Test purposes:
    - diagnostic: Pre-chapter assessment to determine starting point
    - formative: Post-paragraph tests for ongoing assessment (default)
    - summative: Post-chapter comprehensive tests (highest weight for mastery)
    - practice: Self-study tests that don't affect mastery level
    
    Revision ID: ea1742b576f3
    Revises: 401bffeccd70
    Create Date: 2025-11-07 08:41:00.940734

Rev: 401bffeccd70
Parent: 9fe5023de6ad
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/401bffeccd70_enable_rls_policies.py

    enable_rls_policies
    
    This migration enables Row Level Security (RLS) for all tables with school_id.
    RLS provides automatic data isolation at the database level using PostgreSQL session variables.
    
    Key features:
    - Tenant isolation: Users only see data from their school (school_id)
    - Global content: Content with school_id = NULL is visible to all schools
    - SUPER_ADMIN bypass: Database role with BYPASSRLS privilege sees all data
    
    Revision ID: 401bffeccd70
    Revises: 9fe5023de6ad
    Create Date: 2025-11-06 18:42:57.905869

Rev: 9fe5023de6ad
Parent: 010
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/9fe5023de6ad_add_parent_model_and_parent_students_.py

    add parent model and parent_students table
    
    Revision ID: 9fe5023de6ad
    Revises: 010
    Create Date: 2025-11-05 08:25:40.393135

Rev: 011
Parent: 010
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/011_add_key_terms_and_questions_to_paragraphs.py

    add key_terms and questions to paragraphs
    
    Revision ID: 011
    Revises: 010
    Create Date: 2025-11-11
    
    Add key_terms (JSON array of strings) and questions (JSON array of objects)
    columns to the paragraphs table for enhanced content metadata.

Rev: 010 (branchpoint)
Parent: 009
Branches into: 011, 9fe5023de6ad
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/010_add_textbook_versioning.py

    Add versioning support to textbooks
    
    Revision ID: 010
    Revises: 009
    Create Date: 2025-10-30
    
    This migration adds version tracking to textbooks to support:
    - Version management for global textbooks
    - Tracking source version when customizing (forking) a global textbook
    - Future content update synchronization

Rev: 009
Parent: 008
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/009_add_super_admin_role.py

    Add SUPER_ADMIN role to UserRole enum
    
    Revision ID: 009
    Revises: 008
    Create Date: 2025-10-29
    
    This migration adds the SUPER_ADMIN role to the UserRole enum and makes
    school_id nullable for users to support SUPER_ADMIN users who are not
    tied to a specific school.

Rev: 008
Parent: 007
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/008_add_school_id_isolation.py

    Add school_id to progress tables for data isolation
    
    Revision ID: 008
    Revises: 007
    Create Date: 2025-10-29

Rev: 007
Parent: 006
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/007_fix_assignment_tests_soft_delete.py

    Fix assignment_tests table - add soft delete fields
    
    Revision ID: 007
    Revises: 006
    Create Date: 2025-10-29
    
    This migration fixes an error in migration 001 where assignment_tests table
    was created without soft delete fields (created_at, updated_at, deleted_at, is_deleted)
    despite the model inheriting from SoftDeleteModel.

Rev: 006
Parent: 005
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/006_add_soft_delete_indexes.py

    Add indexes for soft delete filtering
    
    Revision ID: 006
    Revises: 005
    Create Date: 2025-10-29

Rev: 005
Parent: 004
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/005_add_composite_indexes.py

    Add composite indexes for query optimization
    
    Revision ID: 005
    Revises: 004
    Create Date: 2025-10-29

Rev: 004
Parent: 003
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/004_change_text_to_json.py

    Change TEXT to JSON for selected_option_ids and sync data
    
    Revision ID: 004
    Revises: 003
    Create Date: 2025-10-29

Rev: 003
Parent: 002
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/003_add_learning_objective_to_paragraphs.py

    Add learning_objective to paragraphs
    
    Revision ID: 003
    Revises: 002
    Create Date: 2025-10-29

Rev: 002
Parent: 001
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/002_add_learning_objectives.py

    Add learning and lesson objectives
    
    Revision ID: 002
    Revises: 001
    Create Date: 2025-10-29

Rev: 001
Parent: <base>
Path: /home/rus/projects/ai_mentor/backend/alembic/versions/001_initial_schema.py

    Initial schema with all tables
    
    Revision ID: 001
    Revises:
    Create Date: 2025-10-28
```
  
---
  
## План проверки
  
### A) Чистая БД (локально)
  
1) Сбросить и поднять PostgreSQL:
  
```bash
cd /home/rus/projects/ai_mentor
docker compose down -v
docker compose up -d postgres
```
  
2) Применить миграции:
  
```bash
cd /home/rus/projects/ai_mentor/backend
# пример через локальный alembic + временный ini (не коммитить)
../.venv/bin/alembic -c alembic.local.ini upgrade head
```
  
3) Проверки:
  
```bash
docker exec -it ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "SELECT version_num FROM alembic_version;"
docker exec -it ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\\dt subjects frameworks goso_sections goso_subsections learning_outcomes paragraph_outcomes"
docker exec -it ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\\dp paragraph_outcomes"
```
  
Ожидаемо:
  - версия `013`
  - таблицы GOCO созданы
  - policies на месте (видны в `\\dp`)
  
### B) “Живая” БД (stage/prod)
  
1) Backup:
  
```bash
docker compose -f docker-compose.infra.yml exec postgres pg_dump -U ai_mentor_user ai_mentor_db > backup_$(date +%Y%m%d).sql
```
  
2) Зафиксировать текущую версию и схему:
  
```bash
docker exec -it ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "SELECT version_num FROM alembic_version;"
docker exec -it ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\\d questions"
docker exec -it ai_mentor_postgres psql -U ai_mentor_user -d ai_mentor_db -c "\\d paragraphs"
```
  
3) Применение:
  
```bash
./deploy-infra.sh migrate
```
  
Ожидаемо:
  - накатывается до `013`,
  - rename-миграция по `order/sort_order` не падает (идемпотентна),
  - GOCO таблицы + RLS появляются.
  

