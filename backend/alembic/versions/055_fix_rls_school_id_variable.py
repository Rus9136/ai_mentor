"""Fix RLS policies: replace app.current_school_id with app.current_tenant_id.

8 RLS policies referenced app.current_school_id, but the application sets
app.current_tenant_id. This caused policies to silently fail or become
overly permissive via IS NULL fallbacks.

Revision ID: 055_fix_rls_school_id_variable
Revises: 054_quiz_streak_columns
"""

from alembic import op

revision = '055_fix_rls_school_id_variable'
down_revision = '054_quiz_streak_columns'


# Standard USING clause for school-scoped tables
_USING = (
    "(school_id IS NULL) OR "
    "(school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::INTEGER)"
)

# For tables that should NOT allow NULL school_id access
_USING_STRICT = (
    "school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::INTEGER"
)


def upgrade() -> None:
    # 1. chat_session_summaries
    op.execute("DROP POLICY IF EXISTS css_school_isolation ON chat_session_summaries;")
    op.execute(
        f"CREATE POLICY css_school_isolation ON chat_session_summaries "
        f"FOR ALL USING ({_USING});"
    )

    # 2. student_memory
    op.execute("DROP POLICY IF EXISTS sm_school_isolation ON student_memory;")
    op.execute(
        f"CREATE POLICY sm_school_isolation ON student_memory "
        f"FOR ALL USING ({_USING});"
    )

    # 3. teacher_chat_session_summaries
    op.execute("DROP POLICY IF EXISTS tcss_school_isolation ON teacher_chat_session_summaries;")
    op.execute(
        f"CREATE POLICY tcss_school_isolation ON teacher_chat_session_summaries "
        f"FOR ALL USING ({_USING});"
    )

    # 4. teacher_memory
    op.execute("DROP POLICY IF EXISTS tm_school_isolation ON teacher_memory;")
    op.execute(
        f"CREATE POLICY tm_school_isolation ON teacher_memory "
        f"FOR ALL USING ({_USING});"
    )

    # 5. review_schedule (strict — no NULL school_id)
    op.execute("DROP POLICY IF EXISTS review_schedule_school_isolation ON review_schedule;")
    op.execute(
        f"CREATE POLICY review_schedule_school_isolation ON review_schedule "
        f"FOR ALL USING ({_USING_STRICT}) WITH CHECK ({_USING_STRICT});"
    )

    # 6. llm_usage_logs
    op.execute("DROP POLICY IF EXISTS llm_usage_logs_school_isolation ON llm_usage_logs;")
    op.execute(
        f"CREATE POLICY llm_usage_logs_school_isolation ON llm_usage_logs "
        f"FOR ALL USING ({_USING});"
    )

    # 7. school_subscriptions
    op.execute("DROP POLICY IF EXISTS school_subscriptions_school_isolation ON school_subscriptions;")
    op.execute(
        f"CREATE POLICY school_subscriptions_school_isolation ON school_subscriptions "
        f"FOR ALL USING ({_USING});"
    )

    # 8. daily_usage_counters
    op.execute("DROP POLICY IF EXISTS daily_usage_counters_school_isolation ON daily_usage_counters;")
    op.execute(
        f"CREATE POLICY daily_usage_counters_school_isolation ON daily_usage_counters "
        f"FOR ALL USING ({_USING});"
    )


def downgrade() -> None:
    # Revert to old app.current_school_id policies (broken but matches old state)
    _OLD_USING = (
        "(school_id IS NULL) OR "
        "(school_id = current_setting('app.current_school_id', true)::INTEGER)"
    )

    for table, policy in [
        ("chat_session_summaries", "css_school_isolation"),
        ("student_memory", "sm_school_isolation"),
        ("teacher_chat_session_summaries", "tcss_school_isolation"),
        ("teacher_memory", "tm_school_isolation"),
        ("llm_usage_logs", "llm_usage_logs_school_isolation"),
        ("school_subscriptions", "school_subscriptions_school_isolation"),
        ("daily_usage_counters", "daily_usage_counters_school_isolation"),
    ]:
        op.execute(f"DROP POLICY IF EXISTS {policy} ON {table};")
        op.execute(
            f"CREATE POLICY {policy} ON {table} FOR ALL USING ({_OLD_USING});"
        )

    op.execute("DROP POLICY IF EXISTS review_schedule_school_isolation ON review_schedule;")
    op.execute(
        "CREATE POLICY review_schedule_school_isolation ON review_schedule "
        f"FOR ALL USING (school_id = current_setting('app.current_school_id', true)::INTEGER) "
        f"WITH CHECK (school_id = current_setting('app.current_school_id', true)::INTEGER);"
    )
