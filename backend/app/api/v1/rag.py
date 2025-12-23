"""
RAG API endpoints for personalized explanations.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import (
    require_student,
    require_super_admin,
    get_current_user_school_id,
)
from app.models.user import User
from app.models.student import Student
from app.models.chapter import Chapter
from app.models.textbook import Textbook
from app.services.rag_service import RAGService, RAGServiceError
from app.services.embedding_service import EmbeddingService, EmbeddingServiceError
from app.repositories.paragraph_repo import ParagraphRepository
from app.repositories.chapter_repo import ChapterRepository
from app.repositories.textbook_repo import TextbookRepository
from app.repositories.embedding_repo import EmbeddingRepository
from app.schemas.rag import (
    ExplainQuestionRequest,
    ExplainParagraphRequest,
    GenerateEmbeddingsRequest,
    BatchGenerateEmbeddingsRequest,
    ExplanationResponse,
    EmbeddingStatusResponse,
    EmbeddingChunkResponse,
    GenerateEmbeddingsResponse,
    BatchGenerateEmbeddingsResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_student_from_user(db: AsyncSession, user: User) -> Student:
    """Get Student record from User."""
    result = await db.execute(
        select(Student).where(Student.user_id == user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student record not found for this user"
        )
    return student


# =============================================================================
# Student Endpoints
# =============================================================================

@router.post("/explain", response_model=ExplanationResponse)
async def explain_question(
    request: ExplainQuestionRequest,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get personalized explanation for a question.

    Uses RAG to retrieve relevant context and generates explanation
    based on student's mastery level (A/B/C).

    - **question_text**: The question or concept to explain
    - **paragraph_id**: Optional paragraph for context
    - **chapter_id**: Optional chapter for context
    - **language**: Response language (ru or kk)
    """
    student = await get_student_from_user(db, current_user)

    try:
        rag_service = RAGService(db)

        response = await rag_service.explain(
            student_id=student.id,
            school_id=school_id,
            question=request.question_text,
            chapter_id=request.chapter_id,
            paragraph_id=request.paragraph_id,
            language=request.language
        )

        logger.info(
            f"Generated explanation for student {student.id}: "
            f"mastery={response.mastery_level}, tokens={response.tokens_used}"
        )

        return response

    except EmbeddingServiceError as e:
        logger.error(f"Embedding service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service is not available. Please try again later."
        )
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )


@router.post("/paragraphs/{paragraph_id}/explain", response_model=ExplanationResponse)
async def explain_paragraph(
    paragraph_id: int,
    request: ExplainParagraphRequest = ExplainParagraphRequest(),
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get personalized explanation for a paragraph.

    Can optionally include a specific question about the paragraph content.

    - **paragraph_id**: Paragraph ID to explain
    - **user_question**: Optional specific question about the paragraph
    - **language**: Response language (ru or kk)
    """
    student = await get_student_from_user(db, current_user)

    # Verify paragraph access (global or school-specific)
    para_repo = ParagraphRepository(db)
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    paragraph = await para_repo.get_by_id(paragraph_id)
    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    chapter = await chapter_repo.get_by_id(paragraph.chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {paragraph.chapter_id} not found"
        )

    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if textbook and textbook.school_id not in (None, school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this paragraph"
        )

    try:
        rag_service = RAGService(db)

        response = await rag_service.explain_paragraph(
            student_id=student.id,
            school_id=school_id,
            paragraph_id=paragraph_id,
            user_question=request.user_question,
            language=request.language
        )

        logger.info(
            f"Generated paragraph explanation for student {student.id}, "
            f"paragraph {paragraph_id}"
        )

        return response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except EmbeddingServiceError as e:
        logger.error(f"Embedding service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service is not available. Please try again later."
        )
    except Exception as e:
        logger.error(f"Error generating paragraph explanation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )


# =============================================================================
# Admin Endpoints (Embedding Management)
# =============================================================================

@router.post(
    "/admin/global/paragraphs/{paragraph_id}/embeddings",
    response_model=GenerateEmbeddingsResponse
)
async def generate_embeddings(
    paragraph_id: int,
    request: GenerateEmbeddingsRequest = GenerateEmbeddingsRequest(),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate embeddings for a global paragraph (SUPER_ADMIN only).

    Chunks the paragraph content and generates OpenAI embeddings
    for vector search.

    - **paragraph_id**: Paragraph ID
    - **force**: Force regeneration even if embeddings exist
    """
    # Verify paragraph exists and is global
    para_repo = ParagraphRepository(db)
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    paragraph = await para_repo.get_by_id(paragraph_id)
    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    chapter = await chapter_repo.get_by_id(paragraph.chapter_id)
    if chapter:
        textbook = await textbook_repo.get_by_id(chapter.textbook_id)
        if textbook and textbook.school_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Use school admin endpoint for non-global paragraphs"
            )

    try:
        embedding_service = EmbeddingService(db)

        chunks_created, total_tokens, processing_time = \
            await embedding_service.generate_paragraph_embeddings(
                paragraph_id=paragraph_id,
                force=request.force
            )

        logger.info(
            f"Generated embeddings for paragraph {paragraph_id}: "
            f"{chunks_created} chunks, {total_tokens} tokens, {processing_time}ms"
        )

        return GenerateEmbeddingsResponse(
            paragraph_id=paragraph_id,
            chunks_created=chunks_created,
            model=embedding_service.model,
            total_tokens=total_tokens,
            processing_time_ms=processing_time
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except EmbeddingServiceError as e:
        logger.error(f"Embedding service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding service error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {str(e)}"
        )


@router.get(
    "/admin/global/paragraphs/{paragraph_id}/embeddings",
    response_model=EmbeddingStatusResponse
)
async def get_embeddings_status(
    paragraph_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get embedding status for a paragraph (SUPER_ADMIN only).

    Returns information about existing embeddings including
    chunk count and model used.
    """
    para_repo = ParagraphRepository(db)
    embedding_repo = EmbeddingRepository(db)

    paragraph = await para_repo.get_by_id(paragraph_id)
    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    embeddings = await embedding_repo.get_by_paragraph(paragraph_id)

    if not embeddings:
        return EmbeddingStatusResponse(
            paragraph_id=paragraph_id,
            paragraph_title=paragraph.title,
            chunks_count=0,
            model=None,
            created_at=None,
            updated_at=None,
            chunks=[]
        )

    chunks = [
        EmbeddingChunkResponse(
            id=emb.id,
            paragraph_id=emb.paragraph_id,
            chunk_index=emb.chunk_index,
            chunk_text=emb.chunk_text[:500] + "..."
                if len(emb.chunk_text) > 500 else emb.chunk_text,
            model=emb.model
        )
        for emb in embeddings
    ]

    return EmbeddingStatusResponse(
        paragraph_id=paragraph_id,
        paragraph_title=paragraph.title,
        chunks_count=len(embeddings),
        model=embeddings[0].model,
        created_at=embeddings[0].created_at,
        updated_at=max(e.updated_at for e in embeddings),
        chunks=chunks
    )


@router.delete(
    "/admin/global/paragraphs/{paragraph_id}/embeddings",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_embeddings(
    paragraph_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete all embeddings for a paragraph (SUPER_ADMIN only).
    """
    embedding_repo = EmbeddingRepository(db)

    count = await embedding_repo.delete_by_paragraph(paragraph_id)

    logger.info(f"Deleted {count} embeddings for paragraph {paragraph_id}")


@router.post(
    "/admin/global/textbooks/{textbook_id}/embeddings",
    response_model=BatchGenerateEmbeddingsResponse
)
async def generate_textbook_embeddings(
    textbook_id: int,
    request: BatchGenerateEmbeddingsRequest = BatchGenerateEmbeddingsRequest(),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate embeddings for all paragraphs in a textbook (SUPER_ADMIN only).

    Processes all paragraphs in the textbook, skipping those that
    already have embeddings (unless force=True).

    - **textbook_id**: Textbook ID
    - **force**: Force regeneration for all paragraphs
    """
    import time
    start_time = time.time()

    # Verify textbook exists and is global
    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    if textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Use school admin endpoint for non-global textbooks"
        )

    try:
        embedding_service = EmbeddingService(db)

        processed, skipped, total_chunks, total_tokens, errors = \
            await embedding_service.generate_textbook_embeddings(
                textbook_id=textbook_id,
                force=request.force
            )

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Generated embeddings for textbook {textbook_id}: "
            f"processed={processed}, skipped={skipped}, "
            f"chunks={total_chunks}, tokens={total_tokens}, errors={len(errors)}"
        )

        return BatchGenerateEmbeddingsResponse(
            textbook_id=textbook_id,
            textbook_title=textbook.title,
            total_paragraphs=processed + skipped + len(errors),
            processed_paragraphs=processed,
            skipped_paragraphs=skipped,
            total_chunks_created=total_chunks,
            total_tokens=total_tokens,
            processing_time_ms=processing_time,
            errors=errors[:10]  # Limit errors in response
        )

    except EmbeddingServiceError as e:
        logger.error(f"Embedding service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding service error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating textbook embeddings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {str(e)}"
        )
