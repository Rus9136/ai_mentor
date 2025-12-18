"""
Service for ParagraphContent operations including file uploads.
"""
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException

from app.models.paragraph import Paragraph


class ParagraphContentService:
    """Service for paragraph content management and file uploads."""

    # Allowed file types by media type
    ALLOWED_AUDIO = {".mp3", ".ogg", ".wav", ".m4a"}
    ALLOWED_SLIDES = {".pdf", ".pptx"}
    ALLOWED_VIDEO = {".mp4", ".webm"}

    # MIME type mappings
    AUDIO_MIME_TYPES = {
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/ogg": ".ogg",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mp4": ".m4a",
        "audio/x-m4a": ".m4a",
        "audio/m4a": ".m4a",
        "audio/aac": ".m4a",
    }
    SLIDES_MIME_TYPES = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    }
    VIDEO_MIME_TYPES = {
        "video/mp4": ".mp4",
        "video/webm": ".webm",
    }

    # Max file sizes
    MAX_AUDIO_SIZE = 50 * 1024 * 1024   # 50 MB
    MAX_SLIDES_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_VIDEO_SIZE = 200 * 1024 * 1024  # 200 MB

    def __init__(self, upload_dir: str = "uploads"):
        """
        Initialize service.

        Args:
            upload_dir: Base directory for uploads
        """
        self.upload_dir = Path(upload_dir)
        self.content_dir = self.upload_dir / "paragraph-contents"
        self.content_dir.mkdir(parents=True, exist_ok=True)

    def _get_media_config(self, media_type: str) -> tuple:
        """Get configuration for media type."""
        if media_type == "audio":
            return self.AUDIO_MIME_TYPES, self.MAX_AUDIO_SIZE, "audio"
        elif media_type == "slides":
            return self.SLIDES_MIME_TYPES, self.MAX_SLIDES_SIZE, "slides"
        elif media_type == "video":
            return self.VIDEO_MIME_TYPES, self.MAX_VIDEO_SIZE, "video"
        else:
            raise ValueError(f"Invalid media type: {media_type}")

    async def upload_media(
        self,
        paragraph_id: int,
        language: str,
        media_type: str,
        file: UploadFile
    ) -> str:
        """
        Upload a media file and return its URL.

        Args:
            paragraph_id: Paragraph ID
            language: Language code ('ru' or 'kk')
            media_type: Type of media ('audio', 'slides', 'video')
            file: Uploaded file

        Returns:
            URL to access the uploaded file

        Raises:
            HTTPException: If file validation fails
        """
        mime_types, max_size, default_name = self._get_media_config(media_type)

        # Validate MIME type
        content_type = file.content_type or ""
        if content_type not in mime_types:
            allowed = ", ".join(mime_types.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый тип файла: {content_type}. Разрешены: {allowed}"
            )

        # Read file content
        try:
            content = await file.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка чтения файла: {str(e)}"
            )

        # Validate size
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"Файл слишком большой: {len(content) / 1024 / 1024:.1f} MB. "
                       f"Максимум: {max_size / 1024 / 1024:.0f} MB"
            )

        # Create directory structure: /uploads/paragraph-contents/{paragraph_id}/{language}/
        target_dir = self.content_dir / str(paragraph_id) / language
        target_dir.mkdir(parents=True, exist_ok=True)

        # Determine file extension
        ext = mime_types.get(content_type, "")
        if not ext and file.filename:
            ext = Path(file.filename).suffix.lower()

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{media_type}_{unique_id}_{timestamp}{ext}"

        # Save file
        file_path = target_dir / filename
        try:
            with open(file_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка сохранения файла: {str(e)}"
            )

        # Return URL
        return f"/{self.upload_dir}/paragraph-contents/{paragraph_id}/{language}/{filename}"

    async def delete_media(
        self,
        paragraph_id: int,
        language: str,
        media_type: str,
        current_url: Optional[str] = None
    ) -> bool:
        """
        Delete a media file from disk.

        Args:
            paragraph_id: Paragraph ID
            language: Language code
            media_type: Type of media ('audio', 'slides', 'video')
            current_url: Current URL of the file (optional, for direct deletion)

        Returns:
            True if file was deleted, False otherwise
        """
        if current_url:
            # Extract path from URL
            try:
                # URL format: /uploads/paragraph-contents/{id}/{lang}/{filename}
                relative_path = current_url.lstrip("/")
                file_path = Path(relative_path)
                if file_path.exists():
                    file_path.unlink()
                    return True
            except Exception:
                pass

        # Try to find and delete files matching the pattern
        target_dir = self.content_dir / str(paragraph_id) / language
        if target_dir.exists():
            for file in target_dir.glob(f"{media_type}_*"):
                try:
                    file.unlink()
                    return True
                except Exception:
                    pass

        return False

    def calculate_source_hash(self, paragraph: Paragraph) -> str:
        """
        Calculate SHA256 hash from paragraph content.

        Used to detect when source paragraph has changed,
        so we can mark content as 'outdated'.

        Args:
            paragraph: Paragraph model

        Returns:
            SHA256 hash string (64 characters)
        """
        # Combine relevant fields
        source_text = f"{paragraph.content or ''}"
        source_text += f"|{paragraph.summary or ''}"
        source_text += f"|{paragraph.learning_objective or ''}"

        # Calculate hash
        return hashlib.sha256(source_text.encode("utf-8")).hexdigest()

    def check_outdated(
        self,
        source_hash: Optional[str],
        paragraph: Paragraph
    ) -> bool:
        """
        Check if content is outdated (source paragraph changed).

        Args:
            source_hash: Stored hash of source content
            paragraph: Current paragraph

        Returns:
            True if content is outdated (hash mismatch), False otherwise
        """
        if not source_hash:
            return False

        current_hash = self.calculate_source_hash(paragraph)
        return source_hash != current_hash
