"""
Upload Service для обработки загруженных файлов
Поддерживает изображения и PDF файлы
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException


class UploadService:
    """Сервис для upload и валидации файлов"""

    # Разрешенные MIME типы
    ALLOWED_IMAGE_TYPES = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    ]

    ALLOWED_PDF_TYPES = [
        "application/pdf",
    ]

    ALLOWED_DOC_TYPES = [
        "application/msword",  # .doc
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/vnd.ms-excel",  # .xls
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
        "application/vnd.ms-powerpoint",  # .ppt
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
        "text/plain",  # .txt
    ]

    # All allowed types for homework attachments
    ALLOWED_HOMEWORK_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_PDF_TYPES + ALLOWED_DOC_TYPES

    # Максимальные размеры файлов (в байтах)
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_DOC_SIZE = 20 * 1024 * 1024  # 20 MB
    MAX_HOMEWORK_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

    def __init__(self, upload_dir: str = "uploads"):
        """
        Инициализация UploadService

        Args:
            upload_dir: Директория для сохранения файлов (относительно корня приложения)
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_image(
        self,
        file: UploadFile,
        max_size: Optional[int] = None,
    ) -> str:
        """
        Сохранить изображение

        Args:
            file: Загруженный файл
            max_size: Максимальный размер файла (опционально, по умолчанию MAX_IMAGE_SIZE)

        Returns:
            URL загруженного изображения (например: "/uploads/abc123_20231030_150000.jpg")

        Raises:
            HTTPException: Если файл невалиден или произошла ошибка сохранения
        """
        max_size = max_size or self.MAX_IMAGE_SIZE

        # Валидация файла
        self._validate_file(
            file=file,
            allowed_types=self.ALLOWED_IMAGE_TYPES,
            max_size=max_size,
        )

        # Чтение содержимого файла
        try:
            file_content = await file.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка чтения файла: {str(e)}",
            )

        # Генерация уникального имени файла
        filename = self._generate_filename(file.filename or "image.jpg")

        # Сохранение файла
        file_path = self.upload_dir / filename

        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка сохранения файла: {str(e)}",
            )

        # Возврат URL
        return f"/{self.upload_dir}/{filename}"

    async def save_pdf(
        self,
        file: UploadFile,
        max_size: Optional[int] = None,
    ) -> str:
        """
        Сохранить PDF файл

        Args:
            file: Загруженный файл
            max_size: Максимальный размер файла (опционально, по умолчанию MAX_PDF_SIZE)

        Returns:
            URL загруженного PDF (например: "/uploads/textbook_abc123.pdf")

        Raises:
            HTTPException: Если файл невалиден или произошла ошибка сохранения
        """
        max_size = max_size or self.MAX_PDF_SIZE

        # Валидация файла
        self._validate_file(
            file=file,
            allowed_types=self.ALLOWED_PDF_TYPES,
            max_size=max_size,
        )

        # Чтение содержимого файла
        try:
            file_content = await file.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка чтения файла: {str(e)}",
            )

        # Генерация уникального имени файла
        filename = self._generate_filename(file.filename or "document.pdf")

        # Сохранение файла
        file_path = self.upload_dir / filename

        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка сохранения файла: {str(e)}",
            )

        # Возврат URL
        return f"/{self.upload_dir}/{filename}"

    def _validate_file(
        self,
        file: UploadFile,
        allowed_types: list[str],
        max_size: int,
    ) -> None:
        """
        Валидация файла

        Args:
            file: Загруженный файл
            allowed_types: Разрешенные MIME типы
            max_size: Максимальный размер файла в байтах

        Raises:
            HTTPException: Если файл невалиден
        """
        # Проверка MIME типа
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый тип файла: {file.content_type}. "
                f"Разрешены: {', '.join(allowed_types)}",
            )

        # Проверка размера файла
        # Примечание: file.size может быть None, поэтому читаем содержимое для точной проверки
        # Это будет сделано в save_image/save_pdf, но можем добавить проверку здесь
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"Файл слишком большой: {file.size / 1024 / 1024:.2f} MB. "
                f"Максимальный размер: {max_size / 1024 / 1024:.0f} MB",
            )

    def _generate_filename(self, original_filename: str) -> str:
        """
        Генерация уникального имени файла

        Args:
            original_filename: Оригинальное имя файла

        Returns:
            Уникальное имя файла с сохранением расширения
            Формат: {uuid}_{timestamp}{extension}
            Пример: "a1b2c3d4_20231030_150000.jpg"
        """
        # Извлечение расширения файла
        file_ext = Path(original_filename).suffix.lower()

        # Генерация уникального ID (первые 8 символов UUID)
        unique_id = str(uuid.uuid4())[:8]

        # Timestamp в формате YYYYMMDD_HHMMSS
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Формирование имени файла
        filename = f"{unique_id}_{timestamp}{file_ext}"

        return filename

    async def save_homework_file(
        self,
        file: UploadFile,
        max_size: Optional[int] = None,
    ) -> dict:
        """
        Сохранить файл для homework attachment.

        Args:
            file: Загруженный файл
            max_size: Максимальный размер файла (опционально)

        Returns:
            dict с url, name, type, size

        Raises:
            HTTPException: Если файл невалиден или произошла ошибка сохранения
        """
        max_size = max_size or self.MAX_HOMEWORK_FILE_SIZE

        # Валидация файла
        self._validate_file(
            file=file,
            allowed_types=self.ALLOWED_HOMEWORK_TYPES,
            max_size=max_size,
        )

        # Чтение содержимого файла
        try:
            file_content = await file.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка чтения файла: {str(e)}",
            )

        # Генерация уникального имени файла
        filename = self._generate_filename(file.filename or "file")

        # Сохранение файла
        file_path = self.upload_dir / filename

        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка сохранения файла: {str(e)}",
            )

        # Определение типа файла
        file_type = self._get_file_type(file.content_type)

        # Возврат данных attachment
        return {
            "url": f"/{self.upload_dir}/{filename}",
            "name": file.filename or "file",
            "type": file_type,
            "size": len(file_content),
        }

    def _get_file_type(self, mime_type: str) -> str:
        """Определить тип файла по MIME type."""
        if mime_type in self.ALLOWED_IMAGE_TYPES:
            return "image"
        elif mime_type in self.ALLOWED_PDF_TYPES:
            return "pdf"
        elif mime_type in self.ALLOWED_DOC_TYPES:
            return "doc"
        return "other"

    def delete_file(self, file_url: str) -> bool:
        """
        Удаление файла по URL (опционально, для будущего использования)

        Args:
            file_url: URL файла (например: "/uploads/abc123.jpg")

        Returns:
            True если файл успешно удален, False otherwise
        """
        try:
            # Извлечение имени файла из URL
            filename = file_url.split("/")[-1]
            file_path = self.upload_dir / filename

            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Ошибка удаления файла {file_url}: {e}")
            return False
