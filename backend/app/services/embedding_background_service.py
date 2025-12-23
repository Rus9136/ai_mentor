"""
Background service for embedding generation.

Provides async task queue for generating embeddings when paragraphs
are created or updated.
"""
import asyncio
import logging
from typing import Optional, Set
from contextlib import asynccontextmanager

from app.core.database import AsyncSessionLocal
from app.services.embedding_service import EmbeddingService, EmbeddingServiceError

logger = logging.getLogger(__name__)

# Queue for pending embedding generation tasks
_pending_paragraphs: Set[int] = set()
_processing_lock = asyncio.Lock()
_background_task: Optional[asyncio.Task] = None


async def queue_embedding_generation(paragraph_id: int) -> None:
    """
    Queue a paragraph for embedding generation.

    This is a fire-and-forget operation that adds the paragraph
    to the processing queue. The actual embedding generation
    happens asynchronously in the background.

    Args:
        paragraph_id: Paragraph ID to generate embeddings for
    """
    global _background_task

    async with _processing_lock:
        _pending_paragraphs.add(paragraph_id)

        # Start background processor if not running
        if _background_task is None or _background_task.done():
            _background_task = asyncio.create_task(_process_queue())

    logger.info(f"Queued paragraph {paragraph_id} for embedding generation")


async def _process_queue() -> None:
    """
    Background processor for embedding queue.

    Continuously processes pending paragraphs until the queue is empty.
    Implements rate limiting and error handling.
    """
    logger.info("Starting embedding background processor")

    while True:
        # Get next paragraph to process
        paragraph_id = None

        async with _processing_lock:
            if _pending_paragraphs:
                paragraph_id = _pending_paragraphs.pop()

        if paragraph_id is None:
            # Queue is empty, stop processor
            logger.info("Embedding queue empty, stopping processor")
            break

        # Process paragraph
        try:
            async with AsyncSessionLocal() as db:
                service = EmbeddingService(db)
                chunks, tokens, time_ms = await service.generate_paragraph_embeddings(
                    paragraph_id=paragraph_id,
                    force=True  # Always regenerate for updates
                )

                if chunks > 0:
                    logger.info(
                        f"Generated {chunks} embeddings for paragraph {paragraph_id} "
                        f"({tokens} tokens, {time_ms}ms)"
                    )
                else:
                    logger.info(f"No embeddings generated for paragraph {paragraph_id}")

        except EmbeddingServiceError as e:
            logger.error(
                f"Embedding service error for paragraph {paragraph_id}: {str(e)}"
            )
            # Re-queue for retry (with limit)
            # For now, just log the error
        except Exception as e:
            logger.error(
                f"Unexpected error generating embeddings for paragraph {paragraph_id}: {str(e)}"
            )

        # Rate limiting: wait between paragraphs
        await asyncio.sleep(0.5)


def get_queue_status() -> dict:
    """
    Get current queue status.

    Returns:
        Dict with queue size and processing state
    """
    return {
        "pending_count": len(_pending_paragraphs),
        "is_processing": _background_task is not None and not _background_task.done()
    }


async def clear_queue() -> int:
    """
    Clear the pending queue.

    Returns:
        Number of items cleared
    """
    async with _processing_lock:
        count = len(_pending_paragraphs)
        _pending_paragraphs.clear()
        return count


# =============================================================================
# Integration helpers for use in paragraph CRUD endpoints
# =============================================================================

def should_regenerate_embeddings(
    old_content: Optional[str],
    new_content: Optional[str],
    old_summary: Optional[str] = None,
    new_summary: Optional[str] = None,
    old_key_terms: Optional[list] = None,
    new_key_terms: Optional[list] = None
) -> bool:
    """
    Check if embeddings should be regenerated based on content changes.

    Args:
        old_content: Previous paragraph content
        new_content: New paragraph content
        old_summary: Previous summary
        new_summary: New summary
        old_key_terms: Previous key terms
        new_key_terms: New key terms

    Returns:
        True if embeddings should be regenerated
    """
    # Content changed
    if old_content != new_content:
        return True

    # Summary changed
    if old_summary != new_summary:
        return True

    # Key terms changed
    if old_key_terms != new_key_terms:
        return True

    return False


async def trigger_embedding_generation_if_needed(
    paragraph_id: int,
    content_changed: bool = False
) -> None:
    """
    Trigger embedding generation if content changed.

    This is a convenience wrapper that checks if generation is needed
    and queues the task.

    Args:
        paragraph_id: Paragraph ID
        content_changed: Whether content has changed
    """
    if content_changed:
        await queue_embedding_generation(paragraph_id)
