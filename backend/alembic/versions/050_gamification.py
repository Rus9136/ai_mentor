"""Add gamification tables: xp_transactions, achievements, student_achievements,
daily_quests, student_daily_quests + extend students with XP/level/streak columns.

Revision ID: 050_gamification
Revises: 049_fix_students_update_rls
"""

from alembic import op

revision = '050_gamification'
down_revision = '049_fix_students_update_rls'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extend students table ──
    op.execute("""
        ALTER TABLE students
            ADD COLUMN total_xp INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN level INTEGER NOT NULL DEFAULT 1,
            ADD COLUMN current_streak INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN longest_streak INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN last_activity_date DATE;
    """)
    op.execute("""
        CREATE INDEX ix_students_leaderboard ON students(school_id, total_xp DESC);
    """)

    # ── xp_transactions (append-only XP log) ──
    op.execute("""
        CREATE TYPE xp_source_type AS ENUM (
            'test_passed', 'mastery_up', 'streak_bonus', 'chapter_complete',
            'daily_quest', 'self_assessment', 'review_completed', 'paragraph_complete'
        );
    """)
    op.execute("""
        CREATE TABLE xp_transactions (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            amount INTEGER NOT NULL,
            source_type xp_source_type NOT NULL,
            source_id INTEGER,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX ix_xp_transactions_student ON xp_transactions(student_id, created_at DESC);")
    op.execute("CREATE INDEX ix_xp_transactions_school ON xp_transactions(school_id);")

    # ── achievements (global badge definitions) ──
    op.execute("""
        CREATE TYPE achievement_category AS ENUM (
            'learning', 'streak', 'mastery', 'social', 'milestone'
        );
    """)
    op.execute("""
        CREATE TYPE achievement_rarity AS ENUM (
            'common', 'rare', 'epic', 'legendary'
        );
    """)
    op.execute("""
        CREATE TABLE achievements (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) NOT NULL UNIQUE,
            name_kk VARCHAR(200) NOT NULL,
            name_ru VARCHAR(200) NOT NULL,
            description_kk TEXT,
            description_ru TEXT,
            icon VARCHAR(100) NOT NULL DEFAULT 'star',
            category achievement_category NOT NULL,
            criteria JSONB NOT NULL DEFAULT '{}',
            xp_reward INTEGER NOT NULL DEFAULT 0,
            rarity achievement_rarity NOT NULL DEFAULT 'common',
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    # ── student_achievements (per-student progress) ──
    op.execute("""
        CREATE TABLE student_achievements (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            achievement_id INTEGER NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            progress FLOAT NOT NULL DEFAULT 0.0,
            is_earned BOOLEAN NOT NULL DEFAULT false,
            earned_at TIMESTAMPTZ,
            notified BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE UNIQUE INDEX uix_student_achievement ON student_achievements(student_id, achievement_id);")
    op.execute("CREATE INDEX ix_student_achievements_school ON student_achievements(school_id);")
    op.execute("CREATE INDEX ix_student_achievements_unnotified ON student_achievements(student_id) WHERE is_earned = true AND notified = false;")

    # ── daily_quests (global quest templates) ──
    op.execute("""
        CREATE TYPE quest_type AS ENUM (
            'complete_tests', 'study_time', 'master_paragraph', 'review_spaced'
        );
    """)
    op.execute("""
        CREATE TABLE daily_quests (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) NOT NULL UNIQUE,
            name_kk VARCHAR(200) NOT NULL,
            name_ru VARCHAR(200) NOT NULL,
            description_kk TEXT,
            description_ru TEXT,
            quest_type quest_type NOT NULL,
            target_value INTEGER NOT NULL,
            xp_reward INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    # ── student_daily_quests (assigned quests per day) ──
    op.execute("""
        CREATE TABLE student_daily_quests (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            quest_id INTEGER NOT NULL REFERENCES daily_quests(id) ON DELETE CASCADE,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            quest_date DATE NOT NULL DEFAULT CURRENT_DATE,
            current_value INTEGER NOT NULL DEFAULT 0,
            is_completed BOOLEAN NOT NULL DEFAULT false,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE UNIQUE INDEX uix_student_daily_quest ON student_daily_quests(student_id, quest_id, quest_date);")
    op.execute("CREATE INDEX ix_student_daily_quests_school ON student_daily_quests(school_id);")
    op.execute("CREATE INDEX ix_student_daily_quests_date ON student_daily_quests(student_id, quest_date);")

    # ── Grants for ai_mentor_app ──
    for table in ['xp_transactions', 'student_achievements', 'student_daily_quests']:
        op.execute(f"GRANT SELECT, INSERT, UPDATE ON {table} TO ai_mentor_app;")
        op.execute(f"GRANT USAGE, SELECT ON SEQUENCE {table}_id_seq TO ai_mentor_app;")

    for table in ['achievements', 'daily_quests']:
        op.execute(f"GRANT SELECT ON {table} TO ai_mentor_app;")
        op.execute(f"GRANT USAGE, SELECT ON SEQUENCE {table}_id_seq TO ai_mentor_app;")

    # ── RLS policies ──

    # xp_transactions: tenant isolation
    op.execute("ALTER TABLE xp_transactions ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY xp_transactions_tenant_isolation ON xp_transactions
        FOR ALL USING (
            COALESCE(NULLIF(current_setting('app.is_super_admin', true), ''), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)

    # achievements: public read (global definitions)
    op.execute("ALTER TABLE achievements ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY achievements_public_read ON achievements
        FOR SELECT USING (true);
    """)

    # student_achievements: tenant isolation
    op.execute("ALTER TABLE student_achievements ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY student_achievements_tenant_isolation ON student_achievements
        FOR ALL USING (
            COALESCE(NULLIF(current_setting('app.is_super_admin', true), ''), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)

    # daily_quests: public read (global definitions)
    op.execute("ALTER TABLE daily_quests ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY daily_quests_public_read ON daily_quests
        FOR SELECT USING (true);
    """)

    # student_daily_quests: tenant isolation
    op.execute("ALTER TABLE student_daily_quests ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY student_daily_quests_tenant_isolation ON student_daily_quests
        FOR ALL USING (
            COALESCE(NULLIF(current_setting('app.is_super_admin', true), ''), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)

    # ── Seed achievements ──
    op.execute("""
        INSERT INTO achievements (code, name_kk, name_ru, description_kk, description_ru, icon, category, criteria, xp_reward, rarity, sort_order) VALUES
        ('first_test', 'Бірінші тест', 'Первый тест', 'Бірінші тестті тапсыр', 'Сдай первый тест', 'rocket', 'milestone', '{"type":"tests_passed","threshold":1}', 20, 'common', 1),
        ('test_master_10', '10 тест', '10 тестов', '10 тестті сәтті тапсыр', 'Сдай 10 тестов успешно', 'target', 'milestone', '{"type":"tests_passed","threshold":10}', 50, 'common', 2),
        ('test_master_50', '50 тест', '50 тестов', '50 тестті сәтті тапсыр', 'Сдай 50 тестов успешно', 'trophy', 'milestone', '{"type":"tests_passed","threshold":50}', 150, 'rare', 3),
        ('perfect_score', 'Мінсіз нәтиже', 'Идеальный результат', 'Тестте 100% ал', 'Получи 100% на тесте', 'star', 'learning', '{"type":"perfect_test","threshold":1}', 50, 'rare', 4),
        ('streak_3', '3 күн қатарынан', '3 дня подряд', '3 күн қатарынан оқы', 'Учись 3 дня подряд', 'flame', 'streak', '{"type":"streak_days","threshold":3}', 30, 'common', 10),
        ('streak_7', 'Апталық серия', 'Недельная серия', '7 күн қатарынан оқы', 'Учись 7 дней подряд', 'flame', 'streak', '{"type":"streak_days","threshold":7}', 75, 'rare', 11),
        ('streak_30', 'Айлық серия', 'Месячная серия', '30 күн қатарынан оқы', 'Учись 30 дней подряд', 'flame', 'streak', '{"type":"streak_days","threshold":30}', 300, 'epic', 12),
        ('streak_100', 'Жүзкүндік', 'Стодневка', '100 күн қатарынан оқы', 'Учись 100 дней подряд', 'crown', 'streak', '{"type":"streak_days","threshold":100}', 1000, 'legendary', 13),
        ('first_mastery', 'Бірінші меңгеру', 'Первое освоение', 'Бір параграфты меңгер', 'Освой один параграф', 'book-open', 'mastery', '{"type":"paragraphs_mastered","threshold":1}', 25, 'common', 20),
        ('mastery_10', '10 параграф', '10 параграфов', '10 параграфты меңгер', 'Освой 10 параграфов', 'brain', 'mastery', '{"type":"paragraphs_mastered","threshold":10}', 100, 'rare', 21),
        ('chapter_A', 'A деңгей', 'Уровень A', 'Тарауда A деңгейіне жет', 'Достигни уровня A в главе', 'medal', 'mastery', '{"type":"chapter_a","threshold":1}', 200, 'epic', 22),
        ('comeback_kid', 'Камбэк', 'Камбэк', 'Struggling-ден mastered-ке жет', 'Пройди от struggling до mastered', 'zap', 'mastery', '{"type":"struggling_to_mastered","threshold":1}', 150, 'epic', 23);
    """)

    # ── Seed daily quests ──
    op.execute("""
        INSERT INTO daily_quests (code, name_kk, name_ru, description_kk, description_ru, quest_type, target_value, xp_reward) VALUES
        ('complete_3_tests', '3 тест тапсыр', 'Сдай 3 теста', 'Бүгін 3 тестті тапсыр', 'Сдай 3 теста сегодня', 'complete_tests', 3, 30),
        ('study_30_min', '30 минут оқы', 'Учись 30 минут', 'Бүгін 30 минут оқы', 'Проведи 30 минут за учебой', 'study_time', 30, 25),
        ('master_paragraph', 'Параграфты меңгер', 'Освой параграф', 'Бүгін 1 параграфты меңгер', 'Освой 1 параграф сегодня', 'master_paragraph', 1, 40),
        ('review_2_spaced', '2 қайталау', '2 повторения', 'Бүгін 2 интервалды қайталау жаса', 'Сделай 2 интервальных повторения', 'review_spaced', 2, 20);
    """)

    # ── Update alembic_version ──
    op.execute("UPDATE alembic_version SET version_num = '050_gamification' WHERE version_num = '049_fix_students_update_rls';")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS student_daily_quests;")
    op.execute("DROP TABLE IF EXISTS student_achievements;")
    op.execute("DROP TABLE IF EXISTS xp_transactions;")
    op.execute("DROP TABLE IF EXISTS daily_quests;")
    op.execute("DROP TABLE IF EXISTS achievements;")
    op.execute("DROP TYPE IF EXISTS quest_type;")
    op.execute("DROP TYPE IF EXISTS achievement_rarity;")
    op.execute("DROP TYPE IF EXISTS achievement_category;")
    op.execute("DROP TYPE IF EXISTS xp_source_type;")
    op.execute("DROP INDEX IF EXISTS ix_students_leaderboard;")
    op.execute("""
        ALTER TABLE students
            DROP COLUMN IF EXISTS total_xp,
            DROP COLUMN IF EXISTS level,
            DROP COLUMN IF EXISTS current_streak,
            DROP COLUMN IF EXISTS longest_streak,
            DROP COLUMN IF EXISTS last_activity_date;
    """)
