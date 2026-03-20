"""Integrate coding module into gamification system.

Add enum values for coding XP sources and quest types,
seed 10 new coding-related achievements and 1 daily quest.

Revision ID: 069_coding_gamification
Revises: 068_mastery_history_enhancements
"""

revision = "069_coding_gamification"
down_revision = "068_mastery_history_enhancements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op

    # ── 1. Add enum values ──
    op.execute("ALTER TYPE xp_source_type ADD VALUE IF NOT EXISTS 'coding_challenge'")
    op.execute("ALTER TYPE xp_source_type ADD VALUE IF NOT EXISTS 'course_complete'")
    op.execute("ALTER TYPE quest_type ADD VALUE IF NOT EXISTS 'solve_challenge'")

    # ── 2. Seed 10 coding achievements ──
    # sort_order 30-39 reserved for coding achievements
    op.execute("""
        INSERT INTO achievements (code, name_kk, name_ru, description_kk, description_ru, icon, category, criteria, xp_reward, rarity, sort_order, is_active, created_at, updated_at)
        VALUES
        ('first_challenge', 'Бірінші есеп', 'Первая задача',
         'Python тілінде бірінші есепті шешіңіз', 'Решите первую задачу на Python',
         '🎯', 'milestone', '{"type": "challenges_solved", "threshold": 1}', 20, 'common', 30, true, NOW(), NOW()),

        ('challenge_10', '10 есеп шешілді', '10 задач решено',
         'Python тілінде 10 есепті шешіңіз', 'Решите 10 задач на Python',
         '🔟', 'milestone', '{"type": "challenges_solved", "threshold": 10}', 50, 'common', 31, true, NOW(), NOW()),

        ('challenge_50', '50 есеп шешілді', '50 задач решено',
         'Python тілінде 50 есепті шешіңіз', 'Решите 50 задач на Python',
         '⭐', 'milestone', '{"type": "challenges_solved", "threshold": 50}', 150, 'rare', 32, true, NOW(), NOW()),

        ('challenge_100', '100 есеп шешілді', '100 задач решено',
         'Python тілінде 100 есепті шешіңіз', 'Решите 100 задач на Python',
         '💯', 'milestone', '{"type": "challenges_solved", "threshold": 100}', 500, 'epic', 33, true, NOW(), NOW()),

        ('loop_master', 'Циклдар шебері', 'Мастер циклов',
         'Циклдар тақырыбындағы барлық есептерді шешіңіз', 'Решите все задачи по теме Циклы',
         '🔁', 'learning', '{"type": "topic_completed", "threshold": 1, "topic_slug": "loops"}', 75, 'rare', 34, true, NOW(), NOW()),

        ('list_tamer', 'Тізімдер шебері', 'Укротитель списков',
         'Тізімдер тақырыбындағы барлық есептерді шешіңіз', 'Решите все задачи по теме Списки',
         '📊', 'learning', '{"type": "topic_completed", "threshold": 1, "topic_slug": "lists"}', 75, 'rare', 35, true, NOW(), NOW()),

        ('oop_architect', 'ООП сәулетшісі', 'Архитектор ООП',
         'ООП тақырыбында бірінші есепті шешіңіз', 'Решите первую задачу по теме ООП',
         '🏗️', 'learning', '{"type": "topic_first_solved", "threshold": 1, "topic_slug": "oop"}', 50, 'rare', 36, true, NOW(), NOW()),

        ('speed_coder', 'Жылдам кодер', 'Быстрый кодер',
         'Есепті 2 минуттан аз уақытта шешіңіз', 'Решите задачу менее чем за 2 минуты',
         '⚡', 'learning', '{"type": "fast_challenge", "threshold": 1, "time_limit_ms": 120000}', 50, 'rare', 37, true, NOW(), NOW()),

        ('hard_5', 'Қиын 5', 'Сложная пятёрка',
         '5 қиын деңгейдегі есепті шешіңіз', 'Решите 5 задач уровня hard',
         '🏆', 'mastery', '{"type": "hard_challenges_solved", "threshold": 5}', 200, 'epic', 38, true, NOW(), NOW()),

        ('course_graduate', 'Курс түлегі', 'Выпускник курса',
         'Бір курсты толықтай аяқтаңыз', 'Полностью завершите один курс',
         '🎓', 'milestone', '{"type": "courses_completed", "threshold": 1}', 150, 'epic', 39, true, NOW(), NOW())
        ON CONFLICT (code) DO NOTHING
    """)

    # ── 3. Seed 1 coding daily quest ──
    op.execute("""
        INSERT INTO daily_quests (code, name_kk, name_ru, description_kk, description_ru, quest_type, target_value, xp_reward, is_active, created_at, updated_at)
        VALUES
        ('solve_1_challenge', 'Python есебін шеш', 'Реши задачу по Python',
         'Python тілінде кем дегенде 1 есепті шешіңіз', 'Решите хотя бы 1 задачу на Python',
         'solve_challenge', 1, 50, true, NOW(), NOW())
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    from alembic import op

    # Remove seeded data
    op.execute("""
        DELETE FROM achievements
        WHERE code IN (
            'first_challenge', 'challenge_10', 'challenge_50', 'challenge_100',
            'loop_master', 'list_tamer', 'oop_architect', 'speed_coder',
            'hard_5', 'course_graduate'
        )
    """)
    op.execute("DELETE FROM daily_quests WHERE code = 'solve_1_challenge'")
    # Note: enum values cannot be easily removed in PostgreSQL
