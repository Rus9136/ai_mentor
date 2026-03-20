"""Fix RLS policies: add is_super_admin bypass to 8 tables from migration 055.

Migration 055 replaced app.current_school_id with app.current_tenant_id but
forgot to add the is_super_admin bypass. When SUPER_ADMIN has tenant_id=NULL,
COALESCE(..., '0')::INTEGER evaluates to 0, matching no rows. This caused
LLM usage monitoring (and other pages) to show empty data for SUPER_ADMIN.

Revision ID: 067_fix_rls_super_admin_bypass
Revises: 066_coding_courses
"""

from alembic import op

revision = '067_fix_rls_super_admin_bypass'
down_revision = '066_coding_courses'

_SA_BYPASS = "COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'"

_USING = (
    f"({_SA_BYPASS}) OR "
    "(school_id IS NULL) OR "
    "(school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::INTEGER)"
)

_USING_STRICT = (
    f"({_SA_BYPASS}) OR "
    "(school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::INTEGER)"
)


def upgrade() -> None:
    # 1. llm_usage_logs
    op.execute("DROP POLICY IF EXISTS llm_usage_logs_school_isolation ON llm_usage_logs;")
    op.execute(
        f"CREATE POLICY llm_usage_logs_school_isolation ON llm_usage_logs "
        f"FOR ALL USING ({_USING});"
    )

    # 2. chat_session_summaries
    op.execute("DROP POLICY IF EXISTS css_school_isolation ON chat_session_summaries;")
    op.execute(
        f"CREATE POLICY css_school_isolation ON chat_session_summaries "
        f"FOR ALL USING ({_USING});"
    )

    # 3. student_memory
    op.execute("DROP POLICY IF EXISTS sm_school_isolation ON student_memory;")
    op.execute(
        f"CREATE POLICY sm_school_isolation ON student_memory "
        f"FOR ALL USING ({_USING});"
    )

    # 4. teacher_chat_session_summaries
    op.execute("DROP POLICY IF EXISTS tcss_school_isolation ON teacher_chat_session_summaries;")
    op.execute(
        f"CREATE POLICY tcss_school_isolation ON teacher_chat_session_summaries "
        f"FOR ALL USING ({_USING});"
    )

    # 5. teacher_memory
    op.execute("DROP POLICY IF EXISTS tm_school_isolation ON teacher_memory;")
    op.execute(
        f"CREATE POLICY tm_school_isolation ON teacher_memory "
        f"FOR ALL USING ({_USING});"
    )

    # 6. review_schedule (strict - no NULL school_id)
    op.execute("DROP POLICY IF EXISTS review_schedule_school_isolation ON review_schedule;")
    op.execute(
        f"CREATE POLICY review_schedule_school_isolation ON review_schedule "
        f"FOR ALL USING ({_USING_STRICT}) WITH CHECK ({_USING_STRICT});"
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

    # 9. student_join_requests (was using tenant_id=0 bypass instead of is_super_admin)
    op.execute("DROP POLICY IF EXISTS student_join_requests_tenant_isolation ON student_join_requests;")
    op.execute(
        f"CREATE POLICY student_join_requests_tenant_isolation ON student_join_requests "
        f"FOR ALL USING ({_USING});"
    )


def downgrade() -> None:
    """Revert to migration 055 policies (without super_admin bypass)."""
    _OLD_USING = (
        "(school_id IS NULL) OR "
        "(school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::INTEGER)"
    )
    _OLD_STRICT = (
        "school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::INTEGER"
    )

    for table, policy in [
        ("llm_usage_logs", "llm_usage_logs_school_isolation"),
        ("chat_session_summaries", "css_school_isolation"),
        ("student_memory", "sm_school_isolation"),
        ("teacher_chat_session_summaries", "tcss_school_isolation"),
        ("teacher_memory", "tm_school_isolation"),
        ("school_subscriptions", "school_subscriptions_school_isolation"),
        ("daily_usage_counters", "daily_usage_counters_school_isolation"),
    ]:
        op.execute(f"DROP POLICY IF EXISTS {policy} ON {table};")
        op.execute(f"CREATE POLICY {policy} ON {table} FOR ALL USING ({_OLD_USING});")

    op.execute("DROP POLICY IF EXISTS review_schedule_school_isolation ON review_schedule;")
    op.execute(
        f"CREATE POLICY review_schedule_school_isolation ON review_schedule "
        f"FOR ALL USING ({_OLD_STRICT}) WITH CHECK ({_OLD_STRICT});"
    )
