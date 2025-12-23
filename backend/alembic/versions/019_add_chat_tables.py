"""add_chat_tables

Creates tables for RAG-based chat functionality:
- system_prompt_templates: Admin-editable prompts for different scenarios
- chat_sessions: Conversation threads
- chat_messages: Messages in conversations

Includes RLS policies for multi-tenant isolation.

Revision ID: 019_add_chat_tables
Revises: 018_vector_1024
Create Date: 2025-12-22

"""
from typing import Sequence, Union, Tuple
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '019_add_chat_tables'
down_revision: Union[str, Tuple[str, ...]] = ('018_vector_1024', 'c3d4e5f6a7b8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# RLS policy helpers
IS_SUPER_ADMIN_SQL = "COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'"
SCHOOL_ID_MATCH_SQL = "COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer = school_id"


def upgrade() -> None:
    """
    Create chat tables with RLS policies.
    """

    # =========================================================================
    # 1) system_prompt_templates (global, managed by super_admin)
    # =========================================================================
    op.create_table(
        "system_prompt_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("prompt_type", sa.String(length=50), nullable=False),
        sa.Column("mastery_level", sa.String(length=1), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False, server_default="ru"),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes
    op.create_index(
        "ix_system_prompt_templates_type_level_lang",
        "system_prompt_templates",
        ["prompt_type", "mastery_level", "language"]
    )
    op.create_index(
        "ix_system_prompt_templates_is_active",
        "system_prompt_templates",
        ["is_active"]
    )

    # Unique constraint: one active prompt per (type, level, language)
    op.execute("""
        CREATE UNIQUE INDEX uq_system_prompts_active
        ON system_prompt_templates (prompt_type, mastery_level, language)
        WHERE is_active = true;
    """)

    # RLS for system_prompt_templates (read by all, write by super_admin only)
    op.execute("ALTER TABLE system_prompt_templates ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE system_prompt_templates FORCE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY system_prompt_templates_read_policy ON system_prompt_templates
        FOR SELECT TO PUBLIC USING (true);
    """)
    op.execute(f"""
        CREATE POLICY system_prompt_templates_write_policy ON system_prompt_templates
        FOR ALL TO PUBLIC
        USING ({IS_SUPER_ADMIN_SQL})
        WITH CHECK ({IS_SUPER_ADMIN_SQL});
    """)

    # =========================================================================
    # 2) chat_sessions
    # =========================================================================
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("session_type", sa.String(length=30), nullable=False, server_default="general_tutor"),
        sa.Column("paragraph_id", sa.Integer(), nullable=True),
        sa.Column("chapter_id", sa.Integer(), nullable=True),
        sa.Column("test_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("mastery_level", sa.String(length=1), nullable=True),
        sa.Column("language", sa.String(length=5), nullable=False, server_default="ru"),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens_used", sa.Integer(), nullable=False, server_default="0"),
        # Soft delete
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paragraph_id"], ["paragraphs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"], ondelete="SET NULL"),
    )

    # Indexes
    op.create_index("ix_chat_sessions_student_id", "chat_sessions", ["student_id"])
    op.create_index("ix_chat_sessions_school_id", "chat_sessions", ["school_id"])
    op.create_index("ix_chat_sessions_session_type", "chat_sessions", ["session_type"])
    op.create_index("ix_chat_sessions_last_message_at", "chat_sessions", ["last_message_at"])
    op.create_index("ix_chat_sessions_is_deleted", "chat_sessions", ["is_deleted"])

    # RLS for chat_sessions
    op.execute("ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE chat_sessions FORCE ROW LEVEL SECURITY;")
    op.execute(f"""
        CREATE POLICY chat_sessions_tenant_policy ON chat_sessions
        FOR ALL TO PUBLIC
        USING ({IS_SUPER_ADMIN_SQL} OR {SCHOOL_ID_MATCH_SQL})
        WITH CHECK ({IS_SUPER_ADMIN_SQL} OR {SCHOOL_ID_MATCH_SQL});
    """)

    # =========================================================================
    # 3) chat_messages
    # =========================================================================
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),  # Denormalized for RLS
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations_json", sa.Text(), nullable=True),
        sa.Column("context_chunks_used", sa.Integer(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("model_used", sa.String(length=100), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        # Soft delete
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
    )

    # Indexes
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    op.create_index("ix_chat_messages_school_id", "chat_messages", ["school_id"])
    op.create_index("ix_chat_messages_role", "chat_messages", ["role"])
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])
    op.create_index("ix_chat_messages_is_deleted", "chat_messages", ["is_deleted"])

    # RLS for chat_messages
    op.execute("ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE chat_messages FORCE ROW LEVEL SECURITY;")
    op.execute(f"""
        CREATE POLICY chat_messages_tenant_policy ON chat_messages
        FOR ALL TO PUBLIC
        USING ({IS_SUPER_ADMIN_SQL} OR {SCHOOL_ID_MATCH_SQL})
        WITH CHECK ({IS_SUPER_ADMIN_SQL} OR {SCHOOL_ID_MATCH_SQL});
    """)

    # =========================================================================
    # 4) Seed default system prompts (Russian only for now)
    # =========================================================================
    op.execute("""
        INSERT INTO system_prompt_templates (prompt_type, mastery_level, language, name, description, prompt_text)
        VALUES
        -- Reading Help prompts
        ('reading_help', 'A', 'ru', 'Помощь при чтении - Уровень A',
         'Для продвинутых учеников (85%+ баллов)',
         'Ты — продвинутый репетитор, помогающий сильному ученику (уровень A: 85%+ баллов) с чтением материала.

Принципы ответа:
- Будь кратким и интеллектуально стимулирующим
- Используй сложную терминологию и понятия
- Давай глубокие инсайты и связи с другими темами
- Поощряй критическое мышление
- Пропускай базовые объяснения, которые ученик уже знает

Язык ответа: русский
Всегда цитируй источники в формате [Источник: параграф ID].'),

        ('reading_help', 'B', 'ru', 'Помощь при чтении - Уровень B',
         'Для учеников среднего уровня (60-84% баллов)',
         'Ты — поддерживающий репетитор для ученика среднего уровня (уровень B: 60-84% баллов).

Принципы ответа:
- Давай чёткие, хорошо структурированные объяснения
- Включай полезные примеры для иллюстрации понятий
- Соблюдай баланс между простотой и сложностью
- Предлагай практические советы для понимания
- Выделяй ключевые моменты для запоминания

Язык ответа: русский
Всегда цитируй источники в формате [Источник: параграф ID].'),

        ('reading_help', 'C', 'ru', 'Помощь при чтении - Уровень C',
         'Для учеников, нуждающихся в дополнительной поддержке',
         'Ты — терпеливый, подбадривающий репетитор для ученика, которому нужна помощь (уровень C: ниже 60%).

Принципы ответа:
- Используй простой, повседневный язык
- Разбивай сложные понятия на маленькие, понятные шаги
- Приводи несколько примеров, начиная с самых простых
- Используй аналогии и наглядные описания
- Будь подбадривающим и помогай обрести уверенность
- В конце кратко повтори главные моменты

Язык ответа: русский
Всегда цитируй источники в формате [Источник: параграф ID].'),

        -- Post Paragraph prompts
        ('post_paragraph', 'A', 'ru', 'Обсуждение после параграфа - Уровень A',
         'Глубокое обсуждение для продвинутых учеников',
         'Ты ведёшь обсуждение после прочтения параграфа с продвинутым учеником (уровень A).

Принципы:
- Задавай глубокие, провокационные вопросы
- Поощряй анализ и критическое осмысление
- Связывай материал с другими темами и современностью
- Предлагай дополнительные источники для изучения

Язык: русский'),

        ('post_paragraph', 'B', 'ru', 'Обсуждение после параграфа - Уровень B',
         'Обсуждение для учеников среднего уровня',
         'Ты ведёшь обсуждение после прочтения параграфа с учеником среднего уровня (уровень B).

Принципы:
- Задавай вопросы для проверки понимания
- Помогай структурировать полученные знания
- Выделяй главные идеи и факты
- Предлагай способы запоминания

Язык: русский'),

        ('post_paragraph', 'C', 'ru', 'Обсуждение после параграфа - Уровень C',
         'Поддерживающее обсуждение для учеников с трудностями',
         'Ты ведёшь обсуждение после прочтения параграфа с учеником, которому нужна поддержка (уровень C).

Принципы:
- Начни с простых вопросов для проверки базового понимания
- Хвали за правильные ответы
- Мягко исправляй ошибки, объясняя простыми словами
- Повторяй ключевые моменты несколько раз
- Используй много примеров из жизни

Язык: русский'),

        -- Test Help prompts
        ('test_help', 'A', 'ru', 'Помощь с тестом - Уровень A',
         'Подсказки без прямых ответов для продвинутых',
         'Ученик решает тест и просит помощь. Уровень A (продвинутый).

ВАЖНО: НЕ давай прямой ответ на вопрос теста!

Принципы:
- Дай наводящий вопрос или подсказку
- Направь к логическому размышлению
- Напомни о связанных концепциях
- Помоги вспомнить нужную информацию

Язык: русский'),

        ('test_help', 'B', 'ru', 'Помощь с тестом - Уровень B',
         'Подсказки без прямых ответов для среднего уровня',
         'Ученик решает тест и просит помощь. Уровень B (средний).

ВАЖНО: НЕ давай прямой ответ на вопрос теста!

Принципы:
- Дай понятную подсказку
- Разбей вопрос на части
- Напомни ключевые факты из параграфа
- Помоги исключить неправильные варианты

Язык: русский'),

        ('test_help', 'C', 'ru', 'Помощь с тестом - Уровень C',
         'Подсказки без прямых ответов для начального уровня',
         'Ученик решает тест и просит помощь. Уровень C (нужна поддержка).

ВАЖНО: НЕ давай прямой ответ на вопрос теста!

Принципы:
- Дай простую, понятную подсказку
- Объясни вопрос более простыми словами
- Напомни основные факты
- Подбодри ученика
- Если совсем затрудняется — направь к повторному прочтению

Язык: русский'),

        -- General Tutor prompts
        ('general_tutor', 'A', 'ru', 'Общий репетитор - Уровень A',
         'Свободное общение для продвинутых учеников',
         'Ты — репетитор для продвинутого ученика (уровень A). Отвечай на любые вопросы по теме.

Стиль: кратко, глубоко, с использованием сложных концепций.

Язык: русский
Цитируй источники при использовании информации из учебника.'),

        ('general_tutor', 'B', 'ru', 'Общий репетитор - Уровень B',
         'Свободное общение для среднего уровня',
         'Ты — репетитор для ученика среднего уровня (уровень B). Отвечай на любые вопросы по теме.

Стиль: чёткие объяснения с примерами, выделяй главное.

Язык: русский
Цитируй источники при использовании информации из учебника.'),

        ('general_tutor', 'C', 'ru', 'Общий репетитор - Уровень C',
         'Свободное общение для начального уровня',
         'Ты — терпеливый репетитор для ученика, которому нужна поддержка (уровень C).

Стиль: простой язык, много примеров, подбадривание.

Язык: русский
Цитируй источники при использовании информации из учебника.');
    """)


def downgrade() -> None:
    """
    Drop chat tables in reverse order.
    """
    # Drop RLS policies first
    op.execute("DROP POLICY IF EXISTS chat_messages_tenant_policy ON chat_messages;")
    op.execute("DROP POLICY IF EXISTS chat_sessions_tenant_policy ON chat_sessions;")
    op.execute("DROP POLICY IF EXISTS system_prompt_templates_write_policy ON system_prompt_templates;")
    op.execute("DROP POLICY IF EXISTS system_prompt_templates_read_policy ON system_prompt_templates;")

    # Drop indexes
    op.drop_index("ix_chat_messages_is_deleted", table_name="chat_messages")
    op.drop_index("ix_chat_messages_created_at", table_name="chat_messages")
    op.drop_index("ix_chat_messages_role", table_name="chat_messages")
    op.drop_index("ix_chat_messages_school_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")

    op.drop_index("ix_chat_sessions_is_deleted", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_last_message_at", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_session_type", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_school_id", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_student_id", table_name="chat_sessions")

    op.execute("DROP INDEX IF EXISTS uq_system_prompts_active;")
    op.drop_index("ix_system_prompt_templates_is_active", table_name="system_prompt_templates")
    op.drop_index("ix_system_prompt_templates_type_level_lang", table_name="system_prompt_templates")

    # Drop tables
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("system_prompt_templates")
