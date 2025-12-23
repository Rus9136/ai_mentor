"""
Repository for ParagraphEmbedding operations including vector search.
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, delete, text, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paragraph import Paragraph, ParagraphEmbedding
from app.models.chapter import Chapter


class EmbeddingRepository:
    """Repository for embedding CRUD and vector search operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, embedding_id: int) -> Optional[ParagraphEmbedding]:
        """
        Get embedding by ID.

        Args:
            embedding_id: Embedding ID

        Returns:
            ParagraphEmbedding or None if not found
        """
        result = await self.db.execute(
            select(ParagraphEmbedding).where(
                ParagraphEmbedding.id == embedding_id,
                ParagraphEmbedding.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_by_paragraph(
        self,
        paragraph_id: int,
        include_deleted: bool = False
    ) -> List[ParagraphEmbedding]:
        """
        Get all embeddings for a paragraph.

        Args:
            paragraph_id: Paragraph ID
            include_deleted: Whether to include soft-deleted embeddings

        Returns:
            List of embeddings ordered by chunk_index
        """
        query = select(ParagraphEmbedding).where(
            ParagraphEmbedding.paragraph_id == paragraph_id
        )
        if not include_deleted:
            query = query.where(ParagraphEmbedding.is_deleted == False)
        query = query.order_by(ParagraphEmbedding.chunk_index)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_similar(
        self,
        query_embedding: List[float],
        chapter_id: Optional[int] = None,
        paragraph_ids: Optional[List[int]] = None,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Tuple[ParagraphEmbedding, float]]:
        """
        Search for similar embeddings using cosine similarity.

        Uses pgvector's <=> operator for cosine distance.
        Similarity = 1 - distance.

        Args:
            query_embedding: Query vector (1024 dimensions for Jina, 1536 for OpenAI)
            chapter_id: Optional filter by chapter
            paragraph_ids: Optional filter by specific paragraphs
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of (embedding, similarity_score) tuples sorted by similarity DESC
        """
        # Build the embedding string for pgvector
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        # Build dynamic query parts
        filter_parts = []
        if chapter_id:
            filter_parts.append(f"AND p.chapter_id = {chapter_id}")
        if paragraph_ids:
            ids_str = ",".join(map(str, paragraph_ids))
            filter_parts.append(f"AND pe.paragraph_id IN ({ids_str})")

        filters_sql = " ".join(filter_parts)

        # Build complete query with explicit string interpolation for the vector
        # Use $N placeholders for asyncpg compatibility
        query_str = f"""
            SELECT
                pe.id,
                pe.paragraph_id,
                pe.chunk_index,
                pe.chunk_text,
                pe.embedding,
                pe.model,
                pe.created_at,
                pe.updated_at,
                pe.deleted_at,
                pe.is_deleted,
                (1 - (pe.embedding <=> '{embedding_str}'::vector)) AS similarity
            FROM paragraph_embeddings pe
            JOIN paragraphs p ON pe.paragraph_id = p.id
            WHERE pe.is_deleted = false
            AND p.is_deleted = false
            AND (1 - (pe.embedding <=> '{embedding_str}'::vector)) >= {min_similarity}
            {filters_sql}
            ORDER BY similarity DESC
            LIMIT {top_k}
        """

        result = await self.db.execute(text(query_str))

        # Convert results to ParagraphEmbedding objects with similarity
        embeddings_with_scores = []
        for row in result.fetchall():
            embedding = ParagraphEmbedding(
                id=row.id,
                paragraph_id=row.paragraph_id,
                chunk_index=row.chunk_index,
                chunk_text=row.chunk_text,
                embedding=row.embedding,
                model=row.model,
                created_at=row.created_at,
                updated_at=row.updated_at,
                deleted_at=row.deleted_at,
                is_deleted=row.is_deleted
            )
            embeddings_with_scores.append((embedding, float(row.similarity)))

        return embeddings_with_scores

    async def get_embeddings_with_context(
        self,
        embedding_ids: List[int]
    ) -> List[Tuple[ParagraphEmbedding, Paragraph, Chapter]]:
        """
        Get embeddings with paragraph and chapter context.

        Args:
            embedding_ids: List of embedding IDs

        Returns:
            List of (embedding, paragraph, chapter) tuples
        """
        if not embedding_ids:
            return []

        query = (
            select(ParagraphEmbedding, Paragraph, Chapter)
            .join(Paragraph, ParagraphEmbedding.paragraph_id == Paragraph.id)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(ParagraphEmbedding.id.in_(embedding_ids))
        )
        result = await self.db.execute(query)
        return list(result.all())

    async def create(self, embedding: ParagraphEmbedding) -> ParagraphEmbedding:
        """
        Create a new embedding.

        Args:
            embedding: ParagraphEmbedding instance

        Returns:
            Created embedding
        """
        self.db.add(embedding)
        await self.db.commit()
        await self.db.refresh(embedding)
        return embedding

    async def bulk_create(
        self,
        embeddings: List[ParagraphEmbedding]
    ) -> List[ParagraphEmbedding]:
        """
        Bulk create embeddings.

        Args:
            embeddings: List of ParagraphEmbedding instances

        Returns:
            List of created embeddings
        """
        if not embeddings:
            return []

        self.db.add_all(embeddings)
        await self.db.commit()

        # Refresh all embeddings to get their IDs
        for emb in embeddings:
            await self.db.refresh(emb)

        return embeddings

    async def delete_by_paragraph(self, paragraph_id: int) -> int:
        """
        Hard delete all embeddings for a paragraph.

        Args:
            paragraph_id: Paragraph ID

        Returns:
            Number of deleted embeddings
        """
        result = await self.db.execute(
            delete(ParagraphEmbedding).where(
                ParagraphEmbedding.paragraph_id == paragraph_id
            )
        )
        await self.db.commit()
        return result.rowcount

    async def count_by_paragraph(self, paragraph_id: int) -> int:
        """
        Count embeddings for a paragraph.

        Args:
            paragraph_id: Paragraph ID

        Returns:
            Number of embeddings
        """
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count(ParagraphEmbedding.id)).where(
                ParagraphEmbedding.paragraph_id == paragraph_id,
                ParagraphEmbedding.is_deleted == False
            )
        )
        return result.scalar() or 0

    async def get_paragraphs_without_embeddings(
        self,
        textbook_id: int
    ) -> List[Paragraph]:
        """
        Get paragraphs that don't have embeddings yet.

        Args:
            textbook_id: Textbook ID

        Returns:
            List of paragraphs without embeddings
        """
        # Subquery for paragraphs that have embeddings
        embeddings_subquery = (
            select(ParagraphEmbedding.paragraph_id)
            .where(ParagraphEmbedding.is_deleted == False)
            .distinct()
            .subquery()
        )

        # Query paragraphs not in the subquery
        query = (
            select(Paragraph)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id == textbook_id,
                Paragraph.is_deleted == False,
                Chapter.is_deleted == False,
                Paragraph.id.notin_(select(embeddings_subquery.c.paragraph_id))
            )
            .order_by(Chapter.order, Paragraph.order)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())
