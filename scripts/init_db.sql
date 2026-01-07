-- Инициализация базы данных AI Mentor
-- Этот скрипт выполняется при первом запуске PostgreSQL контейнера

-- ==========================================
-- 1. СОЗДАНИЕ РОЛЕЙ PostgreSQL
-- ==========================================
-- Проект использует ДВЕ роли для multi-tenant изоляции через RLS:

-- Роль 1: ai_mentor_user (SUPERUSER) - для миграций
-- СОЗДАЁТСЯ АВТОМАТИЧЕСКИ docker entrypoint из POSTGRES_USER/POSTGRES_PASSWORD
-- Этот блок только проверяет наличие и выдаёт SUPERUSER права если нужно
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ai_mentor_user') THEN
        -- Убедимся что роль имеет SUPERUSER права (для bypass RLS при миграциях)
        ALTER ROLE ai_mentor_user WITH SUPERUSER;
        RAISE NOTICE 'Role ai_mentor_user exists, ensured SUPERUSER privileges';
    ELSE
        -- Fallback: создаём если docker entrypoint не создал (не должно случиться)
        CREATE ROLE ai_mentor_user WITH SUPERUSER LOGIN PASSWORD 'ai_mentor_pass';
        RAISE NOTICE 'Role ai_mentor_user created (SUPERUSER for migrations)';
    END IF;
END
$$;

-- Роль 2: ai_mentor_app (обычный пользователь) - для runtime
-- Используется в: backend/.env (POSTGRES_USER), FastAPI приложение
-- Права: Обычный пользователь, RLS политики активны
-- ВАЖНО: Пароль должен совпадать с POSTGRES_PASSWORD в docker-compose.infra.yml
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ai_mentor_app') THEN
        -- Используем тот же пароль что и для ai_mentor_user (из POSTGRES_PASSWORD env)
        -- ВАЖНО: Пароль должен совпадать с backend/.env POSTGRES_PASSWORD
        CREATE ROLE ai_mentor_app WITH LOGIN PASSWORD 'AiM3nt0r_Pr0d_S3cur3_P@ssw0rd_2025!';
        RAISE NOTICE 'Role ai_mentor_app created (normal user for runtime with RLS)';
    ELSE
        -- Обновляем пароль на случай если он устарел
        ALTER ROLE ai_mentor_app WITH PASSWORD 'AiM3nt0r_Pr0d_S3cur3_P@ssw0rd_2025!';
        RAISE NOTICE 'Role ai_mentor_app password updated';
    END IF;
END
$$;

-- Предоставление прав на базу данных
GRANT ALL PRIVILEGES ON DATABASE ai_mentor_db TO ai_mentor_user;
GRANT CONNECT ON DATABASE ai_mentor_db TO ai_mentor_app;

-- ==========================================
-- 2. РАСШИРЕНИЯ PostgreSQL
-- ==========================================

-- Включаем расширение pgvector для векторного поиска (RAG)
CREATE EXTENSION IF NOT EXISTS vector;

-- Включаем расширение для UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
-- ==========================================

-- Функция для автоматического обновления updated_at
-- Используется в триггерах на всех таблицах с TimestampMixin
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ==========================================
-- 4. ПРАВА ДОСТУПА (будут расширены в миграциях)
-- ==========================================

-- После создания таблиц в миграциях, ai_mentor_app получит:
-- - SELECT, INSERT, UPDATE, DELETE на все таблицы
-- - USAGE, SELECT на все sequences
-- Row Level Security будет настроен в миграции 401bffeccd70_enable_rls_policies.py

-- Информационное сообщение
DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'AI Mentor database initialized successfully';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Roles created:';
    RAISE NOTICE '  - ai_mentor_user (SUPERUSER for migrations)';
    RAISE NOTICE '  - ai_mentor_app (normal user for runtime with RLS)';
    RAISE NOTICE 'Extensions enabled:';
    RAISE NOTICE '  - vector (pgvector for embeddings)';
    RAISE NOTICE '  - uuid-ossp';
    RAISE NOTICE 'Functions created:';
    RAISE NOTICE '  - update_updated_at_column()';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Ready for Alembic migrations!';
    RAISE NOTICE 'Next step: alembic upgrade head';
    RAISE NOTICE '================================================';
END $$;
