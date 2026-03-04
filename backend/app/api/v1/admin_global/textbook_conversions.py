"""
Textbook PDF conversion endpoints for SUPER_ADMIN.
Upload PDF, track conversion status, download MMD.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin
from app.models.user import User
from app.models.textbook import Textbook
from app.services.textbook_conversion_service import TextbookConversionService
from app.schemas.textbook_conversion import (
    ConversionStatusResponse,
    ConversionUploadResponse,
)
from ._dependencies import require_global_textbook


router = APIRouter()


@router.post(
    "/textbooks/{textbook_id}/conversions",
    response_model=ConversionUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_pdf_for_conversion(
    file: UploadFile = File(..., description="PDF file of the textbook"),
    textbook: Textbook = Depends(require_global_textbook),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a PDF for a global textbook and start Mathpix conversion.
    Returns 202 Accepted with conversion ID. Poll GET .../status to track progress.
    """
    service = TextbookConversionService(db)
    conversion = await service.upload_and_start(
        textbook_id=textbook.id,
        file=file,
        user_id=current_user.id,
    )
    return ConversionUploadResponse(
        conversion_id=conversion.id,
        textbook_id=textbook.id,
        status=conversion.status.value,
    )


@router.get(
    "/textbooks/{textbook_id}/conversions/status",
    response_model=ConversionStatusResponse,
)
async def get_conversion_status(
    textbook: Textbook = Depends(require_global_textbook),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest conversion status for a textbook."""
    service = TextbookConversionService(db)
    conversion = await service.get_status(textbook.id)
    if not conversion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No conversion found for this textbook",
        )
    return conversion


@router.get("/textbooks/{textbook_id}/conversions/mmd")
async def download_mmd(
    textbook: Textbook = Depends(require_global_textbook),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Download the converted MMD file for a textbook.
    Only available when conversion status is COMPLETED.
    """
    service = TextbookConversionService(db)
    conversion = await service.get_status(textbook.id)

    if not conversion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No conversion found",
        )

    if conversion.status.value != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conversion not completed. Current status: {conversion.status.value}",
        )

    mmd_path = Path(conversion.mmd_path)
    if not mmd_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MMD file not found on disk",
        )

    return FileResponse(
        path=str(mmd_path),
        media_type="text/markdown",
        filename=f"textbook_{textbook.id}.mmd",
    )
