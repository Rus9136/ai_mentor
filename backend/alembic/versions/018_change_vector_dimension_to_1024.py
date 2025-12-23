"""change_vector_dimension_to_1024

Change embedding vector dimension from 1536 to 1024 for Jina AI support.
Jina embeddings-v3 uses 1024 dimensions (vs OpenAI's 1536).

This migration:
1. Drops the old IVFFlat index
2. Deletes existing embeddings (they will be regenerated)
3. Changes the embedding column from vector(1536) to vector(1024)
4. Recreates the IVFFlat index for the new dimension

Revision ID: 018
Revises: 017_add_ivfflat_vector_index
Create Date: 2025-12-19

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '018_vector_1024'
down_revision: Union[str, None] = '017_add_ivfflat_vector_index'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Change vector dimension from 1536 to 1024.

    Steps:
    1. Drop existing IVFFlat index
    2. Delete all embeddings (they need to be regenerated with new dimension)
    3. Alter column type from vector(1536) to vector(1024)
    4. Recreate IVFFlat index
    """
    # 1. Drop existing index
    op.execute("DROP INDEX IF EXISTS ix_paragraph_embeddings_embedding_ivfflat;")

    # 2. Delete existing embeddings (they have wrong dimension now)
    op.execute("DELETE FROM paragraph_embeddings;")

    # 3. Change column type to vector(1024)
    op.execute("""
        ALTER TABLE paragraph_embeddings
        ALTER COLUMN embedding TYPE vector(1024);
    """)

    # 4. Recreate IVFFlat index for new dimension
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_paragraph_embeddings_embedding_ivfflat
        ON paragraph_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

    # Update comment
    op.execute("""
        COMMENT ON INDEX ix_paragraph_embeddings_embedding_ivfflat IS
        'IVFFlat index for cosine similarity search on paragraph embeddings (1024 dims for Jina AI). '
        'Lists=100 is optimal for 10K-100K vectors.';
    """)

    # Update default model in column
    op.execute("""
        ALTER TABLE paragraph_embeddings
        ALTER COLUMN model SET DEFAULT 'jina-embeddings-v3';
    """)


def downgrade() -> None:
    """
    Revert to vector(1536) for OpenAI.
    """
    # Drop index
    op.execute("DROP INDEX IF EXISTS ix_paragraph_embeddings_embedding_ivfflat;")

    # Delete embeddings
    op.execute("DELETE FROM paragraph_embeddings;")

    # Change back to vector(1536)
    op.execute("""
        ALTER TABLE paragraph_embeddings
        ALTER COLUMN embedding TYPE vector(1536);
    """)

    # Recreate index
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_paragraph_embeddings_embedding_ivfflat
        ON paragraph_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

    # Revert default model
    op.execute("""
        ALTER TABLE paragraph_embeddings
        ALTER COLUMN model SET DEFAULT 'text-embedding-3-small';
    """)
