"""
Repository for ParagraphContent data access.
"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paragraph_content import ParagraphContent


class ParagraphContentRepository:
    """Repository for ParagraphContent CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, content_id: int) -> Optional[ParagraphContent]:
        """
        Get content by ID.

        Args:
            content_id: ParagraphContent ID

        Returns:
            ParagraphContent or None if not found
        """
        result = await self.db.execute(
            select(ParagraphContent).where(ParagraphContent.id == content_id)
        )
        return result.scalar_one_or_none()

    async def get_by_paragraph_and_language(
        self,
        paragraph_id: int,
        language: str = "ru"
    ) -> Optional[ParagraphContent]:
        """
        Get content by paragraph ID and language.

        Args:
            paragraph_id: Paragraph ID
            language: Language code ('ru' or 'kk')

        Returns:
            ParagraphContent or None if not found
        """
        result = await self.db.execute(
            select(ParagraphContent).where(
                ParagraphContent.paragraph_id == paragraph_id,
                ParagraphContent.language == language
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_paragraph(self, paragraph_id: int) -> List[ParagraphContent]:
        """
        Get all content records for a paragraph (both languages).

        Args:
            paragraph_id: Paragraph ID

        Returns:
            List of ParagraphContent (max 2: ru and kk)
        """
        result = await self.db.execute(
            select(ParagraphContent)
            .where(ParagraphContent.paragraph_id == paragraph_id)
            .order_by(ParagraphContent.language)
        )
        return list(result.scalars().all())

    async def get_or_create(
        self,
        paragraph_id: int,
        language: str = "ru"
    ) -> ParagraphContent:
        """
        Get existing content or create new one.

        Args:
            paragraph_id: Paragraph ID
            language: Language code ('ru' or 'kk')

        Returns:
            ParagraphContent (existing or newly created)
        """
        content = await self.get_by_paragraph_and_language(paragraph_id, language)
        if content:
            return content

        # Create new
        content = ParagraphContent(
            paragraph_id=paragraph_id,
            language=language
        )
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def create(self, content: ParagraphContent) -> ParagraphContent:
        """
        Create a new content record.

        Args:
            content: ParagraphContent instance

        Returns:
            Created ParagraphContent
        """
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def update(self, content: ParagraphContent) -> ParagraphContent:
        """
        Update an existing content record.

        Args:
            content: ParagraphContent instance with updated fields

        Returns:
            Updated ParagraphContent
        """
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def update_explain_text(
        self,
        content_id: int,
        explain_text: str,
        status: str = "ready"
    ) -> Optional[ParagraphContent]:
        """
        Update explanation text.

        Args:
            content_id: ParagraphContent ID
            explain_text: New explanation text
            status: New status (default: 'ready')

        Returns:
            Updated ParagraphContent or None
        """
        content = await self.get_by_id(content_id)
        if not content:
            return None

        content.explain_text = explain_text
        content.status_explain = status
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def update_media_url(
        self,
        content_id: int,
        media_type: str,
        url: str,
        status: str = "ready"
    ) -> Optional[ParagraphContent]:
        """
        Update media URL (audio, slides, or video).

        Args:
            content_id: ParagraphContent ID
            media_type: Type of media ('audio', 'slides', 'video')
            url: URL to the media file
            status: New status (default: 'ready')

        Returns:
            Updated ParagraphContent or None
        """
        content = await self.get_by_id(content_id)
        if not content:
            return None

        if media_type == "audio":
            content.audio_url = url
            content.status_audio = status
        elif media_type == "slides":
            content.slides_url = url
            content.status_slides = status
        elif media_type == "video":
            content.video_url = url
            content.status_video = status
        else:
            raise ValueError(f"Invalid media type: {media_type}")

        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def update_cards(
        self,
        content_id: int,
        cards: list,
        status: str = "ready"
    ) -> Optional[ParagraphContent]:
        """
        Update flashcards.

        Args:
            content_id: ParagraphContent ID
            cards: List of card dictionaries
            status: New status (default: 'ready')

        Returns:
            Updated ParagraphContent or None
        """
        content = await self.get_by_id(content_id)
        if not content:
            return None

        content.cards = cards
        content.status_cards = status
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def clear_media(
        self,
        content_id: int,
        media_type: str
    ) -> Optional[ParagraphContent]:
        """
        Clear media URL (set to None).

        Args:
            content_id: ParagraphContent ID
            media_type: Type of media ('audio', 'slides', 'video')

        Returns:
            Updated ParagraphContent or None
        """
        content = await self.get_by_id(content_id)
        if not content:
            return None

        if media_type == "audio":
            content.audio_url = None
            content.status_audio = "empty"
        elif media_type == "slides":
            content.slides_url = None
            content.status_slides = "empty"
        elif media_type == "video":
            content.video_url = None
            content.status_video = "empty"
        else:
            raise ValueError(f"Invalid media type: {media_type}")

        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def delete(self, content: ParagraphContent) -> None:
        """
        Delete a content record.

        Args:
            content: ParagraphContent instance to delete
        """
        await self.db.delete(content)
        await self.db.commit()
