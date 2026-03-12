"""
Shared files API — public file browser with listing, preview, and download.
"""

import os
import mimetypes
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()

SHARED_DIR = Path("/app/shared-files") if Path("/app/shared-files").exists() else Path("shared-files")


def _get_file_info(file_path: Path) -> dict:
    stat = file_path.stat()
    mime, _ = mimetypes.guess_type(file_path.name)
    return {
        "name": file_path.name,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "mime_type": mime or "application/octet-stream",
    }


@router.get("/list")
async def list_files(dir: str = Query("", description="Subdirectory path")):
    """List files and folders in shared-files directory."""
    base = SHARED_DIR / dir
    base = base.resolve()

    # Prevent path traversal
    if not str(base).startswith(str(SHARED_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    if not base.exists() or not base.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    items = []
    for entry in sorted(base.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            items.append({
                "name": entry.name,
                "type": "directory",
                "size": 0,
                "modified": datetime.fromtimestamp(
                    entry.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
            })
        else:
            info = _get_file_info(entry)
            info["type"] = "file"
            items.append(info)

    return {"path": dir, "items": items}


@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a file from shared-files."""
    full_path = (SHARED_DIR / file_path).resolve()

    if not str(full_path).startswith(str(SHARED_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type=mimetypes.guess_type(full_path.name)[0] or "application/octet-stream",
    )


@router.get("/preview/{file_path:path}")
async def preview_file(file_path: str):
    """Serve a file inline for browser preview."""
    full_path = (SHARED_DIR / file_path).resolve()

    if not str(full_path).startswith(str(SHARED_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    mime = mimetypes.guess_type(full_path.name)[0] or "application/octet-stream"

    return FileResponse(
        path=str(full_path),
        media_type=mime,
        headers={"Content-Disposition": f"inline; filename=\"{full_path.name}\""},
    )
