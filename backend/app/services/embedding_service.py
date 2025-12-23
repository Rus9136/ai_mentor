"""
Service for generating and managing text embeddings.

Supports multiple embedding providers:
- OpenAI (text-embedding-3-small)
- Jina AI (jina-embeddings-v3) - free tier: 1M tokens/month
"""
import logging
import time
from typing import List, Tuple, Optional, Protocol
from abc import ABC, abstractmethod

import httpx
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.paragraph import Paragraph, ParagraphEmbedding
from app.repositories.embedding_repo import EmbeddingRepository
from app.repositories.paragraph_repo import ParagraphRepository

logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Exception for embedding service errors."""
    pass


class EmbeddingClient(ABC):
    """Abstract base class for embedding clients."""

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass

    @abstractmethod
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 20
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        pass


class OpenAIEmbeddingClient(EmbeddingClient):
    """OpenAI embedding client."""

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise EmbeddingServiceError("OPENAI_API_KEY is not configured")

        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS

    @property
    def model_name(self) -> str:
        return self.model

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        if not text or not text.strip():
            raise EmbeddingServiceError("Cannot generate embedding for empty text")

        try:
            response = await self.client.embeddings.create(
                input=text.strip(),
                model=self.model,
                dimensions=self.dimensions
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {str(e)}")
            raise EmbeddingServiceError(f"Failed to generate embedding: {str(e)}")

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 20
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI API."""
        if not texts:
            return []

        valid_texts = [(i, t.strip()) for i, t in enumerate(texts) if t and t.strip()]
        if not valid_texts:
            return []

        all_embeddings = [None] * len(texts)

        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            batch_texts = [t for _, t in batch]

            try:
                response = await self.client.embeddings.create(
                    input=batch_texts,
                    model=self.model,
                    dimensions=self.dimensions
                )

                for j, item in enumerate(response.data):
                    original_idx = batch[j][0]
                    all_embeddings[original_idx] = item.embedding

            except Exception as e:
                logger.error(f"OpenAI batch embedding error: {str(e)}")
                raise EmbeddingServiceError(f"Failed to generate embeddings: {str(e)}")

        return [e for e in all_embeddings if e is not None]


class JinaEmbeddingClient(EmbeddingClient):
    """
    Jina AI embedding client.

    Free tier: 1M tokens/month
    Models: jina-embeddings-v3 (1024 dimensions)
    API: https://api.jina.ai/v1/embeddings
    """

    API_URL = "https://api.jina.ai/v1/embeddings"

    def __init__(self):
        if not settings.JINA_API_KEY:
            raise EmbeddingServiceError("JINA_API_KEY is not configured")

        self.api_key = settings.JINA_API_KEY
        self.model = settings.JINA_EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS

    @property
    def model_name(self) -> str:
        return self.model

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Jina AI API."""
        if not text or not text.strip():
            raise EmbeddingServiceError("Cannot generate embedding for empty text")

        embeddings = await self._call_api([text.strip()], task="retrieval.passage")
        return embeddings[0]

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 50  # Jina supports larger batches
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts using Jina AI API."""
        if not texts:
            return []

        valid_texts = [(i, t.strip()) for i, t in enumerate(texts) if t and t.strip()]
        if not valid_texts:
            return []

        all_embeddings = [None] * len(texts)

        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            batch_texts = [t for _, t in batch]

            try:
                embeddings = await self._call_api(batch_texts, task="retrieval.passage")

                for j, emb in enumerate(embeddings):
                    original_idx = batch[j][0]
                    all_embeddings[original_idx] = emb

            except Exception as e:
                logger.error(f"Jina batch embedding error: {str(e)}")
                raise EmbeddingServiceError(f"Failed to generate embeddings: {str(e)}")

        return [e for e in all_embeddings if e is not None]

    async def _call_api(
        self,
        texts: List[str],
        task: str = "retrieval.passage"
    ) -> List[List[float]]:
        """
        Call Jina AI embeddings API.

        Args:
            texts: List of texts to embed
            task: Task type - "retrieval.passage" for documents,
                  "retrieval.query" for search queries

        Returns:
            List of embedding vectors
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "task": task,
            "dimensions": self.dimensions,
            "input": texts,
            "late_chunking": False  # We handle chunking ourselves
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload
                )

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Jina API error {response.status_code}: {error_text}")
                    raise EmbeddingServiceError(
                        f"Jina API error {response.status_code}: {error_text}"
                    )

                data = response.json()

                # Extract embeddings from response
                embeddings = []
                for item in sorted(data["data"], key=lambda x: x["index"]):
                    embeddings.append(item["embedding"])

                logger.debug(
                    f"Jina API: generated {len(embeddings)} embeddings, "
                    f"tokens used: {data.get('usage', {}).get('total_tokens', 'N/A')}"
                )

                return embeddings

            except httpx.TimeoutException:
                raise EmbeddingServiceError("Jina API request timed out")
            except httpx.RequestError as e:
                raise EmbeddingServiceError(f"Jina API request failed: {str(e)}")


def get_embedding_client() -> EmbeddingClient:
    """
    Factory function to get the configured embedding client.

    Returns:
        EmbeddingClient based on EMBEDDING_PROVIDER setting
    """
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "openai":
        return OpenAIEmbeddingClient()
    elif provider == "jina":
        return JinaEmbeddingClient()
    else:
        raise EmbeddingServiceError(
            f"Unknown embedding provider: {provider}. "
            f"Supported: openai, jina"
        )


class EmbeddingService:
    """Service for text chunking and embedding generation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_repo = EmbeddingRepository(db)
        self.paragraph_repo = ParagraphRepository(db)

        # Get embedding client based on configuration
        self.client = get_embedding_client()
        self.model = self.client.model_name
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    def _create_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """Create text splitter with configured chunk size and overlap."""
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", ", ", " ", ""]
        )

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks for embedding.

        Args:
            text: Full text to split

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        splitter = self._create_text_splitter()
        chunks = splitter.split_text(text)

        # Filter empty chunks and strip whitespace
        return [c.strip() for c in chunks if c.strip()]

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            EmbeddingServiceError: If text is empty or API call fails
        """
        return await self.client.generate_embedding(text)

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 20
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call

        Returns:
            List of embedding vectors
        """
        return await self.client.generate_embeddings_batch(texts, batch_size)

    def _build_paragraph_text(self, paragraph: Paragraph) -> str:
        """
        Build full text from paragraph for embedding.

        Combines title, content, summary, and key terms.

        Args:
            paragraph: Paragraph model

        Returns:
            Combined text for embedding
        """
        text_parts = []

        if paragraph.title:
            text_parts.append(f"# {paragraph.title}")

        if paragraph.content:
            text_parts.append(paragraph.content)

        if paragraph.summary:
            text_parts.append(f"\nСводка: {paragraph.summary}")

        if paragraph.key_terms:
            if isinstance(paragraph.key_terms, list):
                terms_str = ", ".join(paragraph.key_terms)
            else:
                terms_str = str(paragraph.key_terms)
            text_parts.append(f"\nКлючевые термины: {terms_str}")

        if paragraph.learning_objective:
            text_parts.append(f"\nЦель обучения: {paragraph.learning_objective}")

        return "\n\n".join(text_parts)

    async def generate_paragraph_embeddings(
        self,
        paragraph_id: int,
        force: bool = False
    ) -> Tuple[int, int, int]:
        """
        Generate and store embeddings for a paragraph.

        Args:
            paragraph_id: Paragraph ID
            force: If True, regenerate even if embeddings exist

        Returns:
            Tuple of (chunks_created, total_tokens, processing_time_ms)

        Raises:
            ValueError: If paragraph not found
            EmbeddingServiceError: If embedding generation fails
        """
        start_time = time.time()

        # Get paragraph
        paragraph = await self.paragraph_repo.get_by_id(paragraph_id)
        if not paragraph:
            raise ValueError(f"Paragraph {paragraph_id} not found")

        # Check if embeddings exist
        existing = await self.embedding_repo.get_by_paragraph(paragraph_id)
        if existing and not force:
            logger.info(
                f"Embeddings already exist for paragraph {paragraph_id}, "
                "skipping (use force=True to regenerate)"
            )
            return (0, 0, 0)

        # Delete existing embeddings if regenerating
        if existing:
            await self.embedding_repo.delete_by_paragraph(paragraph_id)
            logger.info(f"Deleted {len(existing)} existing embeddings")

        # Build full text from paragraph content
        full_text = self._build_paragraph_text(paragraph)

        if not full_text.strip():
            logger.warning(f"No content to embed for paragraph {paragraph_id}")
            return (0, 0, int((time.time() - start_time) * 1000))

        # Chunk the text
        chunks = self.chunk_text(full_text)

        if not chunks:
            logger.warning(f"No chunks generated for paragraph {paragraph_id}")
            return (0, 0, int((time.time() - start_time) * 1000))

        logger.info(f"Generated {len(chunks)} chunks for paragraph {paragraph_id}")

        # Generate embeddings
        embeddings = await self.generate_embeddings_batch(chunks)

        if len(embeddings) != len(chunks):
            logger.warning(
                f"Embedding count mismatch: {len(embeddings)} embeddings for "
                f"{len(chunks)} chunks"
            )

        # Create ParagraphEmbedding records
        embedding_records = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            record = ParagraphEmbedding(
                paragraph_id=paragraph_id,
                chunk_index=i,
                chunk_text=chunk,
                embedding=embedding,
                model=self.model
            )
            embedding_records.append(record)

        # Bulk insert
        await self.embedding_repo.bulk_create(embedding_records)

        # Estimate tokens (rough: 4 chars = 1 token)
        total_chars = sum(len(c) for c in chunks)
        estimated_tokens = total_chars // 4

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Created {len(embedding_records)} embeddings for paragraph {paragraph_id} "
            f"using {self.model} in {processing_time}ms (~{estimated_tokens} tokens)"
        )

        return (len(embedding_records), estimated_tokens, processing_time)

    async def generate_textbook_embeddings(
        self,
        textbook_id: int,
        force: bool = False
    ) -> Tuple[int, int, int, int, List[str]]:
        """
        Generate embeddings for all paragraphs in a textbook.

        Args:
            textbook_id: Textbook ID
            force: If True, regenerate even if embeddings exist

        Returns:
            Tuple of (processed, skipped, chunks_created, total_tokens, errors)
        """
        start_time = time.time()
        processed = 0
        skipped = 0
        total_chunks = 0
        total_tokens = 0
        errors = []

        # Get paragraphs without embeddings (or all if force)
        if force:
            from app.repositories.chapter_repo import ChapterRepository
            chapter_repo = ChapterRepository(self.db)
            chapters = await chapter_repo.get_by_textbook(textbook_id)

            paragraphs = []
            for chapter in chapters:
                chapter_paragraphs = await self.paragraph_repo.get_by_chapter(chapter.id)
                paragraphs.extend(chapter_paragraphs)
        else:
            paragraphs = await self.embedding_repo.get_paragraphs_without_embeddings(
                textbook_id
            )

        logger.info(f"Processing {len(paragraphs)} paragraphs for textbook {textbook_id}")

        for paragraph in paragraphs:
            try:
                chunks, tokens, _ = await self.generate_paragraph_embeddings(
                    paragraph.id,
                    force=force
                )

                if chunks > 0:
                    processed += 1
                    total_chunks += chunks
                    total_tokens += tokens
                else:
                    skipped += 1

            except Exception as e:
                error_msg = f"Paragraph {paragraph.id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Error processing paragraph: {error_msg}")

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Textbook {textbook_id}: processed={processed}, skipped={skipped}, "
            f"chunks={total_chunks}, tokens={total_tokens}, errors={len(errors)}"
        )

        return (processed, skipped, total_chunks, total_tokens, errors)


# For query embeddings (used in RAG search)
async def generate_query_embedding(text: str) -> List[float]:
    """
    Generate embedding for a search query.

    Uses "retrieval.query" task for Jina (optimized for queries).

    Args:
        text: Query text

    Returns:
        Embedding vector
    """
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "jina":
        client = JinaEmbeddingClient()
        embeddings = await client._call_api([text.strip()], task="retrieval.query")
        return embeddings[0]
    else:
        client = get_embedding_client()
        return await client.generate_embedding(text)
