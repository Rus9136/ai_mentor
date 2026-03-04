"""
Async wrapper around mpxpy (Mathpix SDK) for PDF-to-MMD conversion.

This service has no DB dependency — it is a pure external API client.
SDK mpxpy is synchronous, so blocking calls are run via asyncio.to_thread().
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


class MathpixError(Exception):
    """Raised when a Mathpix API call fails."""
    pass


@dataclass
class MathpixResult:
    """Result of a Mathpix PDF conversion."""
    pdf_id: str
    mmd_text: str
    page_count: Optional[int] = None


class MathpixService:
    """Async wrapper around mpxpy MathpixClient."""

    def __init__(self, app_id: str, app_key: str):
        self.app_id = app_id
        self.app_key = app_key

    def _get_client(self):
        """Create a new MathpixClient instance."""
        from mpxpy import MathpixClient
        return MathpixClient(app_id=self.app_id, app_key=self.app_key)

    async def convert_pdf(self, file_path: str, timeout: int = 600) -> MathpixResult:
        """
        Submit PDF to Mathpix and wait for MMD result.

        Args:
            file_path: Absolute path to the PDF file.
            timeout: Max wait time in seconds (default 10 min).

        Returns:
            MathpixResult with pdf_id and mmd_text.

        Raises:
            MathpixError: If submission or conversion fails.
        """
        def _sync_convert() -> MathpixResult:
            client = self._get_client()
            pdf = client.pdf_new(file_path=file_path, convert_to_md=True)
            pdf.wait_until_complete(timeout=timeout)
            mmd_text = pdf.to_md_text()
            pdf_id = getattr(pdf, "pdf_id", None) or str(id(pdf))
            # Cleanup from Mathpix servers
            try:
                pdf.delete()
            except Exception as e:
                logger.warning(f"Failed to delete Mathpix PDF {pdf_id}: {e}")
            return MathpixResult(pdf_id=pdf_id, mmd_text=mmd_text)

        try:
            return await asyncio.to_thread(_sync_convert)
        except MathpixError:
            raise
        except Exception as e:
            raise MathpixError(f"Mathpix conversion failed: {e}") from e
