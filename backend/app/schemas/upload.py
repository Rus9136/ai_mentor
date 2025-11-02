"""
Pydantic schemas для Upload API
"""

from pydantic import BaseModel, Field


class ImageUploadResponse(BaseModel):
    """Response schema для image upload"""

    url: str = Field(..., description="URL загруженного изображения")
    filename: str = Field(..., description="Оригинальное имя файла")
    size: int = Field(..., description="Размер файла в байтах")
    mime_type: str = Field(..., description="MIME тип файла")

    model_config = {"from_attributes": True}


class PDFUploadResponse(BaseModel):
    """Response schema для PDF upload"""

    url: str = Field(..., description="URL загруженного PDF")
    filename: str = Field(..., description="Оригинальное имя файла")
    size: int = Field(..., description="Размер файла в байтах")

    model_config = {"from_attributes": True}
