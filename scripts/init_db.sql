-- Инициализация базы данных AI Mentor

-- Включаем расширение pgvector для векторного поиска
CREATE EXTENSION IF NOT EXISTS vector;

-- Включаем расширение для UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Включаем Row Level Security для всех таблиц (будет настроено в миграциях)
-- ALTER TABLE ... ENABLE ROW LEVEL SECURITY;

-- Создаем функцию для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Информационное сообщение
DO $$
BEGIN
    RAISE NOTICE 'AI Mentor database initialized successfully';
    RAISE NOTICE 'Extensions enabled: vector, uuid-ossp';
    RAISE NOTICE 'Ready for Alembic migrations';
END $$;
