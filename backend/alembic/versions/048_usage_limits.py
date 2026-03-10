"""Add subscription_plans, school_subscriptions, daily_usage_counters tables.

Revision ID: 048_usage_limits
Revises: 047_paragraph_prerequisites
"""

from alembic import op

revision = '048_usage_limits'
down_revision = '047_paragraph_prerequisites'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── subscription_plans (global, no school_id) ──
    op.execute("""
        CREATE TABLE subscription_plans (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            display_name VARCHAR(100) NOT NULL,
            daily_message_limit INTEGER,
            feature_limits JSONB NOT NULL DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT true,
            sort_order INTEGER NOT NULL DEFAULT 0,
            description TEXT,
            price_monthly_kzt INTEGER,
            price_yearly_kzt INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    # ── school_subscriptions ──
    op.execute("""
        CREATE TABLE school_subscriptions (
            id SERIAL PRIMARY KEY,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            plan_id INTEGER NOT NULL REFERENCES subscription_plans(id) ON DELETE RESTRICT,
            starts_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ,
            limit_overrides JSONB,
            is_active BOOLEAN NOT NULL DEFAULT true,
            activated_by INTEGER REFERENCES users(id),
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE UNIQUE INDEX uix_school_subscriptions_active
        ON school_subscriptions(school_id) WHERE is_active = true;
    """)

    # ── daily_usage_counters ──
    op.execute("""
        CREATE TABLE daily_usage_counters (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE,
            usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
            feature VARCHAR(30) NOT NULL,
            message_count INTEGER NOT NULL DEFAULT 0,
            token_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(user_id, usage_date, feature)
        );
    """)
    op.execute("""
        CREATE INDEX ix_daily_usage_school_date
        ON daily_usage_counters(school_id, usage_date);
    """)
    op.execute("""
        CREATE INDEX ix_daily_usage_user_date
        ON daily_usage_counters(user_id, usage_date);
    """)

    # ── Grants for runtime user ──
    op.execute("GRANT SELECT ON subscription_plans TO ai_mentor_app;")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE subscription_plans_id_seq TO ai_mentor_app;")

    op.execute("GRANT SELECT, INSERT, UPDATE ON school_subscriptions TO ai_mentor_app;")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE school_subscriptions_id_seq TO ai_mentor_app;")

    op.execute("GRANT SELECT, INSERT, UPDATE ON daily_usage_counters TO ai_mentor_app;")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE daily_usage_counters_id_seq TO ai_mentor_app;")

    # ── RLS for school_subscriptions ──
    op.execute("ALTER TABLE school_subscriptions ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY school_subscriptions_school_isolation ON school_subscriptions
        USING (school_id::text = current_setting('app.current_school_id', true)
               OR current_setting('app.current_school_id', true) IS NULL
               OR current_setting('app.current_school_id', true) = '');
    """)

    # ── RLS for daily_usage_counters ──
    op.execute("ALTER TABLE daily_usage_counters ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY daily_usage_counters_school_isolation ON daily_usage_counters
        USING (school_id::text = current_setting('app.current_school_id', true)
               OR current_setting('app.current_school_id', true) IS NULL
               OR current_setting('app.current_school_id', true) = ''
               OR school_id IS NULL);
    """)

    # ── Seed default plans ──
    op.execute("""
        INSERT INTO subscription_plans (name, display_name, daily_message_limit, feature_limits, sort_order, description)
        VALUES
            ('free', 'Бесплатный', 20,
             '{"chat": 20, "rag": 10, "teacher_chat": 30, "lesson_plan": 3}'::jsonb,
             0, 'Бесплатный тариф с ограниченным количеством сообщений'),
            ('basic', 'Базовый', 100,
             '{"chat": 100, "rag": 50, "teacher_chat": 100, "lesson_plan": 20}'::jsonb,
             1, 'Базовый тариф для школ'),
            ('premium', 'Премиум', NULL,
             '{}'::jsonb,
             2, 'Премиум тариф без ограничений');
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS daily_usage_counters;")
    op.execute("DROP TABLE IF EXISTS school_subscriptions;")
    op.execute("DROP TABLE IF EXISTS subscription_plans;")
