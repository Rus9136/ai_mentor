"""add_ivfflat_vector_index

Add IVFFlat index for efficient vector similarity search on paragraph_embeddings.

Revision ID: 017
Revises: 016_fix_users_rls_for_oauth
Create Date: 2025-12-19

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '017_add_ivfflat_vector_index'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add IVFFlat index for efficient vector similarity search.

    IVFFlat is chosen over HNSW because:
    - Better for datasets < 1M vectors
    - Lower memory usage
    - Faster index creation

    Lists = 100: Recommended for ~10K-100K vectors
    (can be tuned later based on actual data size)

    The index uses cosine distance operator (vector_cosine_ops) which
    is converted to similarity by: similarity = 1 - distance
    """
    # Create IVFFlat index for cosine similarity search
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_paragraph_embeddings_embedding_ivfflat
        ON paragraph_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

    # Add a comment explaining the index
    op.execute("""
        COMMENT ON INDEX ix_paragraph_embeddings_embedding_ivfflat IS
        'IVFFlat index for cosine similarity search on paragraph embeddings. '
        'Lists=100 is optimal for 10K-100K vectors. '
        'Use: embedding <=> query_vector for cosine distance.';
    """)


def downgrade() -> None:
    """Remove IVFFlat index."""
    op.execute("DROP INDEX IF EXISTS ix_paragraph_embeddings_embedding_ivfflat;")
