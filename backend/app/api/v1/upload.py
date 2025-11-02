"""
Upload API endpoints
Поддержка загрузки изображений и PDF файлов
"""

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from app.models.user import User
from app.api.dependencies import require_super_admin
from app.services.upload_service import UploadService
from app.schemas.upload import ImageUploadResponse, PDFUploadResponse

router = APIRouter()

# Создание instance UploadService
# В production можно использовать dependency injection
upload_service = UploadService(upload_dir="uploads")


@router.post("/image", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(require_super_admin),
):
    """
    Upload изображения для параграфов

    Requires:
        - SUPER_ADMIN роль
        - Файл: JPEG, PNG, WebP, GIF
        - Макс размер: 5 MB

    Returns:
        ImageUploadResponse с URL загруженного изображения
    """
    try:
        # Сохранение изображения через UploadService
        url = await upload_service.save_image(file)

        # Формирование response
        return ImageUploadResponse(
            url=url,
            filename=file.filename or "unknown",
            size=file.size or 0,
            mime_type=file.content_type or "unknown",
        )
    except HTTPException:
        # Re-raise HTTPException from UploadService
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка загрузки изображения: {str(e)}",
        )


@router.post("/pdf", response_model=PDFUploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(require_super_admin),
):
    """
    Upload PDF файлов для учебников

    Requires:
        - SUPER_ADMIN роль
        - Файл: PDF
        - Макс размер: 50 MB

    Returns:
        PDFUploadResponse с URL загруженного PDF
    """
    try:
        # Сохранение PDF через UploadService
        url = await upload_service.save_pdf(file)

        # Формирование response
        return PDFUploadResponse(
            url=url,
            filename=file.filename or "unknown",
            size=file.size or 0,
        )
    except HTTPException:
        # Re-raise HTTPException from UploadService
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка загрузки PDF: {str(e)}",
        )
