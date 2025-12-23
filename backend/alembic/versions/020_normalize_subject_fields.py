"""Normalize subject fields - add subject_id FK to textbooks and teachers

Revision ID: 020
Revises: 019_add_chat_tables
Create Date: 2025-12-23

This migration:
1. Adds standard Kazakhstan school subjects to the subjects reference table
2. Adds subject_id FK column to textbooks and teachers tables
3. Migrates existing text data to FK references
4. Keeps text columns for backward compatibility
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = '020'
down_revision: Union[str, None] = '019_add_chat_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Standard Kazakhstan school subjects
SUBJECTS = [
    # code, name_ru, name_kz, grade_from, grade_to
    ("math", "Математика", "Математика", 1, 11),
    ("algebra", "Алгебра", "Алгебра", 7, 11),
    ("geometry", "Геометрия", "Геометрия", 7, 11),
    ("physics", "Физика", "Физика", 7, 11),
    ("chemistry", "Химия", "Химия", 8, 11),
    ("biology", "Биология", "Биология", 5, 11),
    ("geography", "География", "География", 5, 11),
    ("world_history", "Всемирная история", "Дүниежүзі тарихы", 5, 11),
    ("informatics", "Информатика", "Информатика", 5, 11),
    ("kazakh_lang", "Казахский язык", "Қазақ тілі", 1, 11),
    ("russian_lang", "Русский язык", "Орыс тілі", 1, 11),
    ("english_lang", "Английский язык", "Ағылшын тілі", 1, 11),
    ("kazakh_lit", "Казахская литература", "Қазақ әдебиеті", 5, 11),
    ("russian_lit", "Русская литература", "Орыс әдебиеті", 5, 11),
    ("world_lit", "Мировая литература", "Әлем әдебиеті", 5, 11),
    ("natural_science", "Естествознание", "Жаратылыстану", 1, 6),
    ("social_studies", "Познание мира", "Дүниетану", 1, 4),
    ("art", "Изобразительное искусство", "Бейнелеу өнері", 1, 6),
    ("music", "Музыка", "Музыка", 1, 6),
    ("pe", "Физическая культура", "Дене шынықтыру", 1, 11),
    ("tech", "Технология", "Технология", 1, 9),
]


def upgrade() -> None:
    """Add subject_id FK to textbooks and teachers, migrate data."""

    # Get connection for raw SQL
    connection = op.get_bind()

    # 1. Insert subjects that don't exist yet
    # (history_kz already exists from GOSO migration)
    now = datetime.utcnow()
    for code, name_ru, name_kz, grade_from, grade_to in SUBJECTS:
        # Check if subject already exists
        result = connection.execute(
            sa.text("SELECT id FROM subjects WHERE code = :code"),
            {"code": code}
        )
        if result.fetchone() is None:
            connection.execute(
                sa.text("""
                    INSERT INTO subjects (code, name_ru, name_kz, grade_from, grade_to, is_active, created_at, updated_at)
                    VALUES (:code, :name_ru, :name_kz, :grade_from, :grade_to, true, :now, :now)
                """),
                {
                    "code": code,
                    "name_ru": name_ru,
                    "name_kz": name_kz,
                    "grade_from": grade_from,
                    "grade_to": grade_to,
                    "now": now,
                }
            )

    # 2. Add subject_id column to textbooks
    op.add_column('textbooks', sa.Column('subject_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_textbooks_subject_id',
        'textbooks', 'subjects',
        ['subject_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_textbooks_subject_id', 'textbooks', ['subject_id'])

    # 3. Add subject_id column to teachers
    op.add_column('teachers', sa.Column('subject_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_teachers_subject_id',
        'teachers', 'subjects',
        ['subject_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_teachers_subject_id', 'teachers', ['subject_id'])

    # 4. Migrate existing data - textbooks
    # Match by name_ru or name_kz (case-insensitive)
    connection.execute(sa.text("""
        UPDATE textbooks t
        SET subject_id = s.id
        FROM subjects s
        WHERE LOWER(TRIM(t.subject)) = LOWER(s.name_ru)
           OR LOWER(TRIM(t.subject)) = LOWER(s.name_kz)
    """))

    # 5. Migrate existing data - teachers
    connection.execute(sa.text("""
        UPDATE teachers t
        SET subject_id = s.id
        FROM subjects s
        WHERE t.subject IS NOT NULL
          AND (LOWER(TRIM(t.subject)) = LOWER(s.name_ru)
           OR LOWER(TRIM(t.subject)) = LOWER(s.name_kz))
    """))

    # Log unmapped records for manual review
    unmapped_textbooks = connection.execute(sa.text("""
        SELECT id, subject FROM textbooks
        WHERE subject_id IS NULL AND is_deleted = false
    """)).fetchall()

    unmapped_teachers = connection.execute(sa.text("""
        SELECT id, subject FROM teachers
        WHERE subject IS NOT NULL AND subject_id IS NULL AND is_deleted = false
    """)).fetchall()

    if unmapped_textbooks:
        print(f"WARNING: {len(unmapped_textbooks)} textbooks have unmapped subjects:")
        for row in unmapped_textbooks[:5]:
            print(f"  - ID {row[0]}: '{row[1]}'")

    if unmapped_teachers:
        print(f"WARNING: {len(unmapped_teachers)} teachers have unmapped subjects:")
        for row in unmapped_teachers[:5]:
            print(f"  - ID {row[0]}: '{row[1]}'")


def downgrade() -> None:
    """Remove subject_id columns from textbooks and teachers."""

    # Drop foreign keys and indexes first
    op.drop_index('ix_teachers_subject_id', table_name='teachers')
    op.drop_constraint('fk_teachers_subject_id', 'teachers', type_='foreignkey')
    op.drop_column('teachers', 'subject_id')

    op.drop_index('ix_textbooks_subject_id', table_name='textbooks')
    op.drop_constraint('fk_textbooks_subject_id', 'textbooks', type_='foreignkey')
    op.drop_column('textbooks', 'subject_id')

    # Note: We don't remove the inserted subjects as they may be used by GOSO
