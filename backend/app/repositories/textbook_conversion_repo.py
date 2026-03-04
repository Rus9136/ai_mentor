"""
Repository for TextbookConversion data access.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.textbook_conversion import TextbookConversion, ConversionStatus

logger = logging.getLogger(__name__)


class TextbookConversionRepository:
    """Repository for TextbookConversion CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, conversion: TextbookConversion) -> TextbookConversion:
        """Create a new conversion record."""
        self.db.add(conversion)
        await self.db.flush()
        await self.db.refresh(conversion)
        return conversion

    async def get_by_id(self, conversion_id: int) -> Optional[TextbookConversion]:
        """Get conversion by ID."""
        result = await self.db.execute(
            select(TextbookConversion).where(TextbookConversion.id == conversion_id)
        )
        return result.scalar_one_or_none()

    async def get_by_textbook_id(self, textbook_id: int) -> Optional[TextbookConversion]:
        """Get the latest conversion for a textbook."""
        result = await self.db.execute(
            select(TextbookConversion)
            .where(TextbookConversion.textbook_id == textbook_id)
            .order_by(desc(TextbookConversion.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_active_by_textbook_id(self, textbook_id: int) -> Optional[TextbookConversion]:
        """Get PENDING or PROCESSING conversion (prevents duplicate runs)."""
        result = await self.db.execute(
            select(TextbookConversion).where(
                and_(
                    TextbookConversion.textbook_id == textbook_id,
                    TextbookConversion.status.in_([
                        ConversionStatus.PENDING,
                        ConversionStatus.PROCESSING,
                    ]),
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        conversion_id: int,
        status: ConversionStatus,
        mmd_path: Optional[str] = None,
        error_message: Optional[str] = None,
        page_count: Optional[int] = None,
        mathpix_pdf_id: Optional[str] = None,
    ) -> Optional[TextbookConversion]:
        """Update conversion status and related fields."""
        conversion = await self.get_by_id(conversion_id)
        if not conversion:
            logger.warning(f"Conversion {conversion_id} not found for status update")
            return None

        conversion.status = status
        conversion.updated_at = datetime.now(timezone.utc)

        if status == ConversionStatus.PROCESSING:
            conversion.started_at = datetime.now(timezone.utc)
        elif status in (ConversionStatus.COMPLETED, ConversionStatus.FAILED):
            conversion.completed_at = datetime.now(timezone.utc)

        if mmd_path is not None:
            conversion.mmd_path = mmd_path
        if error_message is not None:
            conversion.error_message = error_message
        if page_count is not None:
            conversion.page_count = page_count
        if mathpix_pdf_id is not None:
            conversion.mathpix_pdf_id = mathpix_pdf_id

        await self.db.flush()
        await self.db.refresh(conversion)
        return conversion
