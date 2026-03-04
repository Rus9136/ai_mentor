"""
Textbook PDF conversion orchestration service.

Handles: PDF upload, Mathpix submission, background processing, status tracking.
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional, Set

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.textbook_conversion import TextbookConversion, ConversionStatus
from app.repositories.textbook_conversion_repo import TextbookConversionRepository
from app.services.mathpix_service import MathpixService, MathpixError

logger = logging.getLogger(__name__)

# Track active background conversions (prevents duplicate launches)
_active_conversions: Set[int] = set()


class TextbookConversionService:
    """Orchestrates textbook PDF-to-MMD conversion."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TextbookConversionRepository(db)

    async def upload_and_start(
        self,
        textbook_id: int,
        file: UploadFile,
        user_id: int,
    ) -> TextbookConversion:
        """
        Upload PDF and start background conversion.

        1. Validate PDF file
        2. Check no active conversion exists
        3. Save PDF to disk
        4. Create TextbookConversion record (PENDING)
        5. Launch background task
        """
        # Validate content type
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Expected PDF file, got: {file.content_type}",
            )

        # Check file size (50 MB max)
        max_size = 50 * 1024 * 1024
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large: {len(content) / 1024 / 1024:.1f} MB (max 50 MB)",
            )

        # Check no active conversion
        active = await self.repo.get_active_by_textbook_id(textbook_id)
        if active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Conversion already in progress (id={active.id}, status={active.status.value})",
            )

        # Save PDF to disk
        pdf_dir = Path(settings.UPLOAD_DIR) / "textbook-pdf" / str(textbook_id)
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_filename = f"textbook_{textbook_id}.pdf"
        pdf_path = pdf_dir / pdf_filename
        pdf_path.write_bytes(content)

        # Create conversion record
        conversion = TextbookConversion(
            textbook_id=textbook_id,
            status=ConversionStatus.PENDING,
            pdf_path=str(pdf_path),
            created_by=user_id,
        )
        conversion = await self.repo.create(conversion)
        await self.db.commit()

        # Launch background task
        _launch_conversion_task(conversion.id, str(pdf_path), textbook_id)

        return conversion

    async def get_status(self, textbook_id: int) -> Optional[TextbookConversion]:
        """Get the latest conversion for a textbook."""
        return await self.repo.get_by_textbook_id(textbook_id)

    async def get_by_id(self, conversion_id: int) -> Optional[TextbookConversion]:
        """Get conversion by ID."""
        return await self.repo.get_by_id(conversion_id)


# =============================================================================
# Background task (module-level, independent DB session)
# =============================================================================

def _launch_conversion_task(conversion_id: int, pdf_path: str, textbook_id: int) -> None:
    """Launch background conversion task if not already running."""
    if conversion_id in _active_conversions:
        logger.warning(f"Conversion {conversion_id} already active, skipping")
        return
    _active_conversions.add(conversion_id)
    asyncio.create_task(_run_conversion(conversion_id, pdf_path, textbook_id))


async def _run_conversion(conversion_id: int, pdf_path: str, textbook_id: int) -> None:
    """
    Background task: send PDF to Mathpix, save MMD, update DB.
    Uses its own AsyncSession (not the request session).
    """
    logger.info(f"Starting Mathpix conversion {conversion_id} for textbook {textbook_id}")

    try:
        # Update status to PROCESSING
        async with AsyncSessionLocal() as db:
            repo = TextbookConversionRepository(db)
            await repo.update_status(conversion_id, status=ConversionStatus.PROCESSING)
            await db.commit()

        # Check Mathpix credentials
        if not settings.MATHPIX_APP_ID or not settings.MATHPIX_APP_KEY:
            raise MathpixError("MATHPIX_APP_ID and MATHPIX_APP_KEY must be configured")

        # Run Mathpix conversion (blocking, in thread)
        mathpix = MathpixService(
            app_id=settings.MATHPIX_APP_ID,
            app_key=settings.MATHPIX_APP_KEY,
        )
        result = await mathpix.convert_pdf(pdf_path, timeout=600)

        # Save MMD file
        mmd_dir = Path(settings.UPLOAD_DIR) / "textbook-mmd" / str(textbook_id)
        mmd_dir.mkdir(parents=True, exist_ok=True)
        mmd_path = mmd_dir / f"textbook_{textbook_id}.mmd"
        mmd_path.write_text(result.mmd_text, encoding="utf-8")

        # Update status to COMPLETED
        async with AsyncSessionLocal() as db:
            repo = TextbookConversionRepository(db)
            await repo.update_status(
                conversion_id,
                status=ConversionStatus.COMPLETED,
                mmd_path=str(mmd_path),
                mathpix_pdf_id=result.pdf_id,
                page_count=result.page_count,
            )
            await db.commit()

        logger.info(f"Conversion {conversion_id} completed → {mmd_path}")

    except MathpixError as e:
        logger.error(f"Mathpix error for conversion {conversion_id}: {e}")
        async with AsyncSessionLocal() as db:
            repo = TextbookConversionRepository(db)
            await repo.update_status(
                conversion_id,
                status=ConversionStatus.FAILED,
                error_message=str(e),
            )
            await db.commit()

    except Exception as e:
        logger.error(f"Unexpected error in conversion {conversion_id}: {e}", exc_info=True)
        async with AsyncSessionLocal() as db:
            repo = TextbookConversionRepository(db)
            await repo.update_status(
                conversion_id,
                status=ConversionStatus.FAILED,
                error_message=f"Unexpected error: {str(e)}",
            )
            await db.commit()

    finally:
        _active_conversions.discard(conversion_id)
