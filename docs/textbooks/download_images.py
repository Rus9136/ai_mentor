import re
import os
import requests
import time
from pathlib import Path

MD_FILE = "/Users/rus/Projects/Latex/1513.md"
OUTPUT_DIR = "/Users/rus/Projects/Latex/images"
UPDATED_MD = "/Users/rus/Projects/Latex/1513_with_local_images.md"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(MD_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Find all image URLs
pattern = r'!\[([^\]]*)\]\((https://cdn\.mathpix\.com/cropped/[^)]+)\)'
matches = list(re.finditer(pattern, content))

print(f"Найдено изображений: {len(matches)}")

updated_content = content
success = 0
failed = 0

for i, match in enumerate(matches):
    alt_text = match.group(1)
    url = match.group(2)
    
    # Extract filename from URL
    url_path = url.split('?')[0]
    parts = url_path.split('/')
    original_name = parts[-1]  # e.g. 8db738b1-454d-4d01-b59a-a9337c8eed6d-002.jpg
    
    # Create numbered filename to keep order
    ext = original_name.split('.')[-1] if '.' in original_name else 'jpg'
    filename = f"img_{i+1:03d}_{original_name[:20]}.{ext}"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    print(f"[{i+1}/{len(matches)}] Скачиваю: {filename[:50]}...", end=" ")
    
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            # Replace URL in markdown with local path
            local_ref = f"./images/{filename}"
            old_tag = match.group(0)
            new_tag = f"![{alt_text}]({local_ref})"
            updated_content = updated_content.replace(old_tag, new_tag, 1)
            
            size = len(response.content) // 1024
            print(f"✓ ({size} KB)")
            success += 1
        else:
            print(f"✗ HTTP {response.status_code}")
            failed += 1
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        failed += 1
    
    # Small delay to be polite
    time.sleep(0.1)

# Save updated MD with local image paths
with open(UPDATED_MD, "w", encoding="utf-8") as f:
    f.write(updated_content)

print(f"\n{'='*50}")
print(f"Успешно: {success}/{len(matches)}")
print(f"Ошибки: {failed}/{len(matches)}")
print(f"Изображения сохранены в: {OUTPUT_DIR}")
print(f"Обновлённый MD файл: {UPDATED_MD}")
