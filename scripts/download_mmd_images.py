"""
Download Mathpix CDN images from MMD file and update paths to local.

Usage:
    python scripts/download_mmd_images.py <textbook_id>

Images are saved to: uploads/textbook-images/{textbook_id}/
MMD is updated in-place with local image paths.
"""
import re
import os
import sys
import time
import hashlib
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


def download_image(url: str, filepath: Path) -> tuple[bool, str]:
    """Download a single image. Returns (success, error_msg)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            filepath.write_bytes(response.content)
            return True, ""
        return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


def process_mmd_images(textbook_id: int, base_dir: str = "uploads") -> dict:
    """
    Download all Mathpix CDN images from an MMD file and update paths.

    Returns dict with stats: total, success, failed, images_dir, mmd_path
    """
    mmd_path = Path(base_dir) / "textbook-mmd" / str(textbook_id) / f"textbook_{textbook_id}.mmd"
    if not mmd_path.exists():
        raise FileNotFoundError(f"MMD file not found: {mmd_path}")

    images_dir = Path(base_dir) / "textbook-images" / str(textbook_id)
    images_dir.mkdir(parents=True, exist_ok=True)

    content = mmd_path.read_text(encoding="utf-8")

    # Find all Mathpix CDN image URLs
    pattern = r'!\[([^\]]*)\]\((https://cdn\.mathpix\.com/cropped/[^)]+)\)'
    matches = list(re.finditer(pattern, content))

    print(f"Textbook {textbook_id}: found {len(matches)} images")

    if not matches:
        return {"total": 0, "success": 0, "failed": 0}

    # Deduplicate URLs (same URL may appear multiple times)
    url_to_filename: dict[str, str] = {}
    download_tasks: list[tuple[str, Path]] = []

    for i, match in enumerate(matches):
        url = match.group(2)
        if url in url_to_filename:
            continue  # Already scheduled

        # Generate stable filename from URL hash + index
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        url_path = url.split("?")[0]
        ext = url_path.rsplit(".", 1)[-1] if "." in url_path.split("/")[-1] else "jpg"
        filename = f"img_{len(url_to_filename)+1:03d}_{url_hash}.{ext}"

        url_to_filename[url] = filename
        filepath = images_dir / filename
        if not filepath.exists():  # Skip already downloaded
            download_tasks.append((url, filepath))

    print(f"Unique images: {len(url_to_filename)}, to download: {len(download_tasks)}")

    # Download in parallel (8 threads)
    success = 0
    failed = 0

    if download_tasks:
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(download_image, url, fp): (url, fp)
                for url, fp in download_tasks
            }
            for future in as_completed(futures):
                url, fp = futures[future]
                ok, err = future.result()
                if ok:
                    success += 1
                    size_kb = fp.stat().st_size // 1024
                    print(f"  OK  {fp.name} ({size_kb} KB)")
                else:
                    failed += 1
                    print(f"  FAIL {fp.name}: {err}")

    # Already existing
    already = len(url_to_filename) - len(download_tasks)
    if already > 0:
        print(f"Already downloaded: {already}")
        success += already

    # Update MMD content: replace CDN URLs with local paths
    updated_content = content
    for match in matches:
        alt_text = match.group(1)
        url = match.group(2)
        filename = url_to_filename[url]
        old_tag = match.group(0)
        new_tag = f"![{alt_text}](images/{filename})"
        updated_content = updated_content.replace(old_tag, new_tag, 1)

    # Save updated MMD
    mmd_path.write_text(updated_content, encoding="utf-8")
    print(f"\nDone! Success: {success}, Failed: {failed}")
    print(f"Images: {images_dir}")
    print(f"MMD updated: {mmd_path}")

    return {
        "total": len(url_to_filename),
        "success": success,
        "failed": failed,
        "images_dir": str(images_dir),
        "mmd_path": str(mmd_path),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/download_mmd_images.py <textbook_id>")
        sys.exit(1)

    textbook_id = int(sys.argv[1])
    process_mmd_images(textbook_id)
