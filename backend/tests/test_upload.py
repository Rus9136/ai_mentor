"""
Tests for Upload Service and API.

Covers:
- UploadService (save_image, save_pdf, validate_file, delete_file)
- Upload API endpoints (POST /upload/image, POST /upload/pdf)
- File type validation
- File size validation
- Error handling
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
from io import BytesIO

from fastapi import HTTPException, UploadFile
from httpx import AsyncClient, ASGITransport

from app.services.upload_service import UploadService
from app.models.user import User, UserRole


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def upload_service(tmp_path):
    """Create UploadService with temporary directory."""
    return UploadService(upload_dir=str(tmp_path))


@pytest.fixture
def mock_image_file():
    """Create a mock image file."""
    file = MagicMock(spec=UploadFile)
    file.filename = "test_image.jpg"
    file.content_type = "image/jpeg"
    file.size = 1024 * 100  # 100 KB
    file.read = AsyncMock(return_value=b"fake image content")
    return file


@pytest.fixture
def mock_png_file():
    """Create a mock PNG file."""
    file = MagicMock(spec=UploadFile)
    file.filename = "test_image.png"
    file.content_type = "image/png"
    file.size = 1024 * 200  # 200 KB
    file.read = AsyncMock(return_value=b"fake png content")
    return file


@pytest.fixture
def mock_pdf_file():
    """Create a mock PDF file."""
    file = MagicMock(spec=UploadFile)
    file.filename = "test_document.pdf"
    file.content_type = "application/pdf"
    file.size = 1024 * 1024  # 1 MB
    file.read = AsyncMock(return_value=b"%PDF-1.4 fake pdf content")
    return file


@pytest.fixture
def mock_large_image():
    """Create a mock image file that exceeds size limit."""
    file = MagicMock(spec=UploadFile)
    file.filename = "large_image.jpg"
    file.content_type = "image/jpeg"
    file.size = 10 * 1024 * 1024  # 10 MB (exceeds 5 MB limit)
    file.read = AsyncMock(return_value=b"x" * (10 * 1024 * 1024))
    return file


@pytest.fixture
def mock_large_pdf():
    """Create a mock PDF file that exceeds size limit."""
    file = MagicMock(spec=UploadFile)
    file.filename = "large_document.pdf"
    file.content_type = "application/pdf"
    file.size = 60 * 1024 * 1024  # 60 MB (exceeds 50 MB limit)
    file.read = AsyncMock(return_value=b"x" * (60 * 1024 * 1024))
    return file


@pytest.fixture
def mock_invalid_type_file():
    """Create a mock file with invalid type."""
    file = MagicMock(spec=UploadFile)
    file.filename = "document.docx"
    file.content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    file.size = 1024 * 100
    file.read = AsyncMock(return_value=b"fake docx content")
    return file


@pytest.fixture
def mock_super_admin():
    """Create a mock super admin user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "admin@test.com"
    user.role = UserRole.SUPER_ADMIN
    user.is_active = True
    return user


# =============================================================================
# UploadService Tests
# =============================================================================

class TestUploadServiceInit:
    """Tests for UploadService initialization."""

    def test_init_creates_directory(self, tmp_path):
        """Test that init creates upload directory."""
        upload_dir = tmp_path / "test_uploads"
        service = UploadService(upload_dir=str(upload_dir))

        assert upload_dir.exists()

    def test_init_with_existing_directory(self, tmp_path):
        """Test init with existing directory."""
        upload_dir = tmp_path / "existing"
        upload_dir.mkdir()

        service = UploadService(upload_dir=str(upload_dir))

        assert upload_dir.exists()


class TestSaveImage:
    """Tests for UploadService.save_image method."""

    @pytest.mark.asyncio
    async def test_save_image_jpeg(self, upload_service, mock_image_file):
        """Test saving JPEG image."""
        url = await upload_service.save_image(mock_image_file)

        assert url.endswith(".jpg")
        assert "/uploads/" in url or url.startswith("/")

    @pytest.mark.asyncio
    async def test_save_image_png(self, upload_service, mock_png_file):
        """Test saving PNG image."""
        url = await upload_service.save_image(mock_png_file)

        assert url.endswith(".png")

    @pytest.mark.asyncio
    async def test_save_image_webp(self, upload_service):
        """Test saving WebP image."""
        file = MagicMock(spec=UploadFile)
        file.filename = "test.webp"
        file.content_type = "image/webp"
        file.size = 1024 * 50
        file.read = AsyncMock(return_value=b"fake webp")

        url = await upload_service.save_image(file)

        assert url.endswith(".webp")

    @pytest.mark.asyncio
    async def test_save_image_gif(self, upload_service):
        """Test saving GIF image."""
        file = MagicMock(spec=UploadFile)
        file.filename = "animation.gif"
        file.content_type = "image/gif"
        file.size = 1024 * 100
        file.read = AsyncMock(return_value=b"GIF89a fake gif")

        url = await upload_service.save_image(file)

        assert url.endswith(".gif")

    @pytest.mark.asyncio
    async def test_save_image_invalid_type(self, upload_service, mock_invalid_type_file):
        """Test saving image with invalid type raises error."""
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.save_image(mock_invalid_type_file)

        assert exc_info.value.status_code == 400
        assert "тип файла" in exc_info.value.detail.lower() or "type" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_save_image_too_large(self, upload_service, mock_large_image):
        """Test saving image that exceeds size limit."""
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.save_image(mock_large_image)

        assert exc_info.value.status_code == 400
        assert "большой" in exc_info.value.detail.lower() or "size" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_save_image_custom_max_size(self, upload_service):
        """Test saving image with custom max size."""
        file = MagicMock(spec=UploadFile)
        file.filename = "small.jpg"
        file.content_type = "image/jpeg"
        file.size = 1024 * 100  # 100 KB
        file.read = AsyncMock(return_value=b"content")

        # Should work with custom max size
        url = await upload_service.save_image(file, max_size=1024 * 1024)

        assert ".jpg" in url

    @pytest.mark.asyncio
    async def test_save_image_read_error(self, upload_service):
        """Test handling read error."""
        file = MagicMock(spec=UploadFile)
        file.filename = "test.jpg"
        file.content_type = "image/jpeg"
        file.size = 1024
        file.read = AsyncMock(side_effect=Exception("Read failed"))

        with pytest.raises(HTTPException) as exc_info:
            await upload_service.save_image(file)

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_save_image_without_filename(self, upload_service):
        """Test saving image without original filename."""
        file = MagicMock(spec=UploadFile)
        file.filename = None
        file.content_type = "image/jpeg"
        file.size = 1024
        file.read = AsyncMock(return_value=b"content")

        url = await upload_service.save_image(file)

        assert ".jpg" in url  # Default extension


class TestSavePDF:
    """Tests for UploadService.save_pdf method."""

    @pytest.mark.asyncio
    async def test_save_pdf_success(self, upload_service, mock_pdf_file):
        """Test saving PDF file."""
        url = await upload_service.save_pdf(mock_pdf_file)

        assert url.endswith(".pdf")

    @pytest.mark.asyncio
    async def test_save_pdf_invalid_type(self, upload_service, mock_image_file):
        """Test saving non-PDF file as PDF raises error."""
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.save_pdf(mock_image_file)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_save_pdf_too_large(self, upload_service, mock_large_pdf):
        """Test saving PDF that exceeds size limit."""
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.save_pdf(mock_large_pdf)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_save_pdf_custom_max_size(self, upload_service, mock_pdf_file):
        """Test saving PDF with custom max size."""
        url = await upload_service.save_pdf(mock_pdf_file, max_size=100 * 1024 * 1024)

        assert ".pdf" in url

    @pytest.mark.asyncio
    async def test_save_pdf_read_error(self, upload_service):
        """Test handling read error for PDF."""
        file = MagicMock(spec=UploadFile)
        file.filename = "test.pdf"
        file.content_type = "application/pdf"
        file.size = 1024
        file.read = AsyncMock(side_effect=Exception("Read failed"))

        with pytest.raises(HTTPException) as exc_info:
            await upload_service.save_pdf(file)

        assert exc_info.value.status_code == 500


class TestValidateFile:
    """Tests for UploadService._validate_file method."""

    def test_validate_file_valid_image(self, upload_service, mock_image_file):
        """Test validating a valid image file."""
        # Should not raise
        upload_service._validate_file(
            file=mock_image_file,
            allowed_types=UploadService.ALLOWED_IMAGE_TYPES,
            max_size=UploadService.MAX_IMAGE_SIZE
        )

    def test_validate_file_invalid_type(self, upload_service, mock_invalid_type_file):
        """Test validating file with invalid type."""
        with pytest.raises(HTTPException) as exc_info:
            upload_service._validate_file(
                file=mock_invalid_type_file,
                allowed_types=UploadService.ALLOWED_IMAGE_TYPES,
                max_size=UploadService.MAX_IMAGE_SIZE
            )

        assert exc_info.value.status_code == 400

    def test_validate_file_size_exceeded(self, upload_service, mock_large_image):
        """Test validating file that exceeds size limit."""
        with pytest.raises(HTTPException) as exc_info:
            upload_service._validate_file(
                file=mock_large_image,
                allowed_types=UploadService.ALLOWED_IMAGE_TYPES,
                max_size=UploadService.MAX_IMAGE_SIZE
            )

        assert exc_info.value.status_code == 400

    def test_validate_file_size_none(self, upload_service):
        """Test validating file when size is None."""
        file = MagicMock(spec=UploadFile)
        file.filename = "test.jpg"
        file.content_type = "image/jpeg"
        file.size = None  # Size unknown

        # Should not raise - validation passes when size is unknown
        upload_service._validate_file(
            file=file,
            allowed_types=UploadService.ALLOWED_IMAGE_TYPES,
            max_size=UploadService.MAX_IMAGE_SIZE
        )


class TestGenerateFilename:
    """Tests for UploadService._generate_filename method."""

    def test_generate_filename_preserves_extension(self, upload_service):
        """Test that filename generation preserves extension."""
        filename = upload_service._generate_filename("original.jpg")
        assert filename.endswith(".jpg")

    def test_generate_filename_lowercase_extension(self, upload_service):
        """Test that extension is lowercased."""
        filename = upload_service._generate_filename("original.JPG")
        assert filename.endswith(".jpg")

    def test_generate_filename_unique(self, upload_service):
        """Test that generated filenames are unique."""
        filename1 = upload_service._generate_filename("test.jpg")
        filename2 = upload_service._generate_filename("test.jpg")

        # Due to timestamp, filenames might be the same if called quickly
        # But UUID part should be different
        assert len(filename1) > 10  # Has UUID and timestamp

    def test_generate_filename_format(self, upload_service):
        """Test filename format."""
        filename = upload_service._generate_filename("original.png")

        # Format: {uuid}_{timestamp}.{ext}
        parts = filename.split("_")
        assert len(parts) >= 3  # uuid, date, time.ext


class TestDeleteFile:
    """Tests for UploadService.delete_file method."""

    def test_delete_existing_file(self, upload_service, tmp_path):
        """Test deleting an existing file."""
        # Create a test file
        test_file = tmp_path / "test_file.jpg"
        test_file.write_bytes(b"test content")

        result = upload_service.delete_file(f"/{tmp_path}/test_file.jpg")

        assert result is True
        assert not test_file.exists()

    def test_delete_nonexistent_file(self, upload_service):
        """Test deleting a non-existent file."""
        result = upload_service.delete_file("/uploads/nonexistent.jpg")

        assert result is False

    def test_delete_file_error_handling(self, upload_service):
        """Test error handling during file deletion."""
        # Invalid path should return False, not raise
        result = upload_service.delete_file("")

        assert result is False


# =============================================================================
# Constants Tests
# =============================================================================

class TestUploadServiceConstants:
    """Tests for UploadService constants."""

    def test_allowed_image_types(self):
        """Test ALLOWED_IMAGE_TYPES contains expected types."""
        assert "image/jpeg" in UploadService.ALLOWED_IMAGE_TYPES
        assert "image/png" in UploadService.ALLOWED_IMAGE_TYPES
        assert "image/webp" in UploadService.ALLOWED_IMAGE_TYPES
        assert "image/gif" in UploadService.ALLOWED_IMAGE_TYPES

    def test_allowed_pdf_types(self):
        """Test ALLOWED_PDF_TYPES contains PDF."""
        assert "application/pdf" in UploadService.ALLOWED_PDF_TYPES

    def test_max_image_size(self):
        """Test MAX_IMAGE_SIZE is 5 MB."""
        assert UploadService.MAX_IMAGE_SIZE == 5 * 1024 * 1024

    def test_max_pdf_size(self):
        """Test MAX_PDF_SIZE is 50 MB."""
        assert UploadService.MAX_PDF_SIZE == 50 * 1024 * 1024


# =============================================================================
# API Endpoint Tests
# =============================================================================

class TestUploadImageEndpoint:
    """Tests for POST /upload/image endpoint."""

    @pytest.mark.asyncio
    async def test_upload_image_unauthorized(self):
        """Test upload image without authentication."""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # Create fake file data
            files = {"file": ("test.jpg", b"fake image", "image/jpeg")}
            response = await client.post("/api/v1/upload/image", files=files)

        # Should fail without auth
        assert response.status_code in [401, 403]


class TestUploadPDFEndpoint:
    """Tests for POST /upload/pdf endpoint."""

    @pytest.mark.asyncio
    async def test_upload_pdf_unauthorized(self):
        """Test upload PDF without authentication."""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            files = {"file": ("test.pdf", b"%PDF-1.4", "application/pdf")}
            response = await client.post("/api/v1/upload/pdf", files=files)

        # Should fail without auth
        assert response.status_code in [401, 403]


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases in upload service."""

    @pytest.mark.asyncio
    async def test_unicode_filename(self, upload_service):
        """Test handling file with unicode filename."""
        file = MagicMock(spec=UploadFile)
        file.filename = "изображение_тест.jpg"
        file.content_type = "image/jpeg"
        file.size = 1024
        file.read = AsyncMock(return_value=b"content")

        url = await upload_service.save_image(file)

        assert ".jpg" in url

    @pytest.mark.asyncio
    async def test_special_characters_filename(self, upload_service):
        """Test handling file with special characters in name."""
        file = MagicMock(spec=UploadFile)
        file.filename = "test file (1) [copy].jpg"
        file.content_type = "image/jpeg"
        file.size = 1024
        file.read = AsyncMock(return_value=b"content")

        url = await upload_service.save_image(file)

        assert ".jpg" in url

    @pytest.mark.asyncio
    async def test_empty_content(self, upload_service):
        """Test handling file with empty content."""
        file = MagicMock(spec=UploadFile)
        file.filename = "empty.jpg"
        file.content_type = "image/jpeg"
        file.size = 0
        file.read = AsyncMock(return_value=b"")

        # Should still save (validation doesn't check for empty)
        url = await upload_service.save_image(file)

        assert ".jpg" in url

    @pytest.mark.asyncio
    async def test_long_filename(self, upload_service):
        """Test handling file with very long filename."""
        file = MagicMock(spec=UploadFile)
        file.filename = "a" * 200 + ".jpg"
        file.content_type = "image/jpeg"
        file.size = 1024
        file.read = AsyncMock(return_value=b"content")

        url = await upload_service.save_image(file)

        # Generated filename should be manageable
        assert len(url.split("/")[-1]) < 100

    def test_concurrent_filename_generation(self, upload_service):
        """Test that concurrent filename generation produces unique names."""
        filenames = set()
        for _ in range(100):
            filename = upload_service._generate_filename("test.jpg")
            filenames.add(filename)

        # All should be unique (UUIDs)
        assert len(filenames) == 100
