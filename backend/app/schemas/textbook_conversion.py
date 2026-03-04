"""
Pydantic schemas for textbook PDF conversion.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ConversionResponse(BaseModel):
    """Full response schema for a conversion record."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    textbook_id: int
    status: str
    pdf_path: str
    mmd_path: Optional[str] = None
    mathpix_pdf_id: Optional[str] = None
    page_count: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ConversionStatusResponse(BaseModel):
    """Lightweight status check response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    textbook_id: int
    status: str
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ConversionUploadResponse(BaseModel):
    """Response after uploading PDF and starting conversion."""
    conversion_id: int
    textbook_id: int
    status: str = "PENDING"
    message: str = "PDF uploaded. Conversion started."
