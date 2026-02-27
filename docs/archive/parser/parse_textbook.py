"""
Парсер учебника алгебры из MD формата → PostgreSQL + MinIO/S3

Запуск:
    pip install psycopg2-binary minio python-dotenv
    python parse_textbook.py

Конфиг через .env файл или переменные окружения.
"""

import re
import os
import json
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ─── НАСТРОЙКИ ────────────────────────────────────────────────────────────────

MD_FILE        = "./386_with_local_images.md"
IMAGES_DIR     = "./images"           # папка с локальными изображениями
TEXTBOOK_ID    = str(uuid.uuid4())    # или задайте фиксированный UUID
TEXTBOOK_TITLE = "Алгебра 9 сынып, 1-бөлім"
SUBJECT        = "algebra"
GRADE          = 9
LANGUAGE       = "kz"

# MinIO / S3
MINIO_ENDPOINT  = "localhost:9000"     # или ваш S3 endpoint
MINIO_ACCESS    = "minioadmin"
MINIO_SECRET    = "minioadmin"
MINIO_BUCKET    = "textbooks"
MINIO_SECURE    = False                # True для HTTPS

# PostgreSQL
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "ai_mentor"
DB_USER = "postgres"
DB_PASS = "postgres"

# Служебные разделы которые не нужно загружать в БД
SKIP_SECTIONS = {
    "АЛҒЫ СӨ3", "АЛҒЫ СӨЗ",
    "Шартты белгілер:",
    "Аеторгары:", "Авторлары:",
    "МАЗМУНЫ", "Учебное издание",
}

# ─── МОДЕЛИ ДАННЫХ ─────────────────────────────────────────────────────────────

@dataclass
class ContentBlock:
    block_id:    str = field(default_factory=lambda: str(uuid.uuid4()))
    textbook_id: str = ""
    chapter:     str = ""
    paragraph:   str = ""
    section:     str = ""
    block_order: int = 0
    block_type:  str = ""   # heading | text | task | subtask | image | formula | answer
    content:     str = ""
    image_url:   str = ""
    image_local: str = ""   # локальный путь до загрузки
    metadata:    dict = field(default_factory=dict)

# ─── ПАРСЕР ────────────────────────────────────────────────────────────────────

class TextbookParser:

    # Служебные страницы до начала реального контента
    CONTENT_START_MARKER = "КАЙТАЛАУҒА АРНАЛҒАН ЖАТТЫҒУЛАР"

    def __init__(self, md_path: str):
        with open(md_path, encoding="utf-8") as f:
            self.lines = f.readlines()
        self.blocks: list[ContentBlock] = []
        self.order = 0
        self.current_chapter   = ""
        self.current_paragraph = ""
        self.current_section   = ""
        self.current_task_num  = ""
        self.content_started   = False

    def _next_order(self) -> int:
        self.order += 1
        return self.order

    def _add(self, block_type: str, content: str = "", image_local: str = "",
             metadata: dict = None):
        b = ContentBlock(
            textbook_id  = TEXTBOOK_ID,
            chapter      = self.current_chapter,
            paragraph    = self.current_paragraph,
            section      = self.current_section,
            block_order  = self._next_order(),
            block_type   = block_type,
            content      = content.strip(),
            image_local  = image_local,
            metadata     = metadata or {},
        )
        self.blocks.append(b)

    # ── определяем тип строки ─────────────────────────────────────────────────

    def _is_skip_section(self, text: str) -> bool:
        return any(skip in text for skip in SKIP_SECTIONS)

    def _is_chapter(self, text: str) -> bool:
        """Тарау (раздел) — заглавными буквами"""
        t = text.strip()
        return len(t) > 10 and t == t.upper() and not t.startswith('§')

    def _is_paragraph(self, text: str) -> bool:
        """§ N. Название"""
        return bool(re.match(r'^§\s*\d+', text.strip()))

    def _is_section_heading(self, text: str) -> bool:
        """Подраздел типа 'Бөлшек-рационал өрнектерді түрлендіру'"""
        t = text.strip()
        return len(t) > 5 and not self._is_chapter(t) and not self._is_paragraph(t)

    def _is_task(self, text: str) -> bool:
        """Основная задача: '1. Берілген...'"""
        return bool(re.match(r'^\d+\.\s+\S', text.strip()))

    def _is_subtask(self, text: str) -> bool:
        """Подпункт задачи: '1) $формула$' или '1) текст'"""
        return bool(re.match(r'^\d+\)\s+\S', text.strip()))

    def _is_image(self, text: str) -> bool:
        return bool(re.match(r'!\[.*?\]\(\.\/images\/', text.strip()))

    def _extract_image_path(self, text: str) -> str:
        m = re.search(r'!\[.*?\]\(\.(\/images\/.+?)\)', text.strip())
        return m.group(1).lstrip('/') if m else ""

    def _has_formula(self, text: str) -> bool:
        return '$' in text

    def _extract_formulas(self, text: str) -> list[str]:
        return re.findall(r'\$([^$]+)\$', text)

    # ── основной цикл ─────────────────────────────────────────────────────────

    def parse(self) -> list[ContentBlock]:
        for raw_line in self.lines:
            line = raw_line.strip()
            if not line:
                continue

            # Ждём начала реального учебного контента
            if not self.content_started:
                if self.CONTENT_START_MARKER in line:
                    self.content_started = True
                continue

            # Пропускаем МАЗМУНЫ (оглавление) и выходные данные в конце
            if "## МАЗМУНЫ" in line or "Учебное издание" in line:
                break

            # ── Заголовки (строки начинающиеся с ##) ──────────────────────────
            if line.startswith("## ") or line.startswith("# "):
                heading = re.sub(r'^#+\s*', '', line).strip()

                if self._is_skip_section(heading):
                    continue

                if self._is_paragraph(heading):
                    self.current_paragraph = heading
                    self._add("paragraph_heading", heading)

                elif self._is_chapter(heading):
                    self.current_chapter = heading
                    self.current_paragraph = ""
                    self._add("chapter_heading", heading)

                else:
                    self.current_section = heading
                    self._add("section_heading", heading)

                continue

            # ── Изображение ───────────────────────────────────────────────────
            if self._is_image(line):
                img_path = self._extract_image_path(line)
                self._add("image", image_local=img_path)
                continue

            # ── Основная задача ───────────────────────────────────────────────
            if self._is_task(line):
                m = re.match(r'^(\d+)\.\s+(.+)', line)
                if m:
                    self.current_task_num = m.group(1)
                    task_text = m.group(2)
                    formulas = self._extract_formulas(task_text)
                    self._add(
                        "task",
                        content  = task_text,
                        metadata = {
                            "task_number": int(self.current_task_num),
                            "formulas": formulas,
                        }
                    )
                continue

            # ── Подпункт задачи ───────────────────────────────────────────────
            if self._is_subtask(line):
                m = re.match(r'^(\d+)\)\s+(.+)', line)
                if m:
                    sub_num  = m.group(1)
                    sub_text = m.group(2).rstrip(';').rstrip('.')
                    formulas = self._extract_formulas(sub_text)

                    # Определяем тип: только формула или смешанный
                    btype = "subtask_formula" if formulas else "subtask_text"

                    self._add(
                        btype,
                        content  = sub_text,
                        metadata = {
                            "task_number":    int(self.current_task_num) if self.current_task_num else None,
                            "subtask_number": int(sub_num),
                            "formulas":       formulas,
                            "section":        self.current_section,
                        }
                    )
                continue

            # ── Обычный текст (теория, пояснения) ────────────────────────────
            if len(line) > 3:
                formulas = self._extract_formulas(line)
                btype = "theory_formula" if formulas and len(line) < 200 else "text"
                self._add(btype, content=line,
                          metadata={"formulas": formulas} if formulas else {})

        return self.blocks


# ─── ЗАГРУЗКА В MINIO ──────────────────────────────────────────────────────────

def upload_images_to_minio(blocks: list[ContentBlock], images_base_dir: str) -> dict[str, str]:
    """
    Загружает все изображения в MinIO.
    Возвращает словарь {local_path: public_url}
    """
    try:
        from minio import Minio
        from minio.error import S3Error
    except ImportError:
        print("⚠️  minio не установлен: pip install minio")
        print("   Изображения будут сохранены с локальными путями")
        return {}

    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS,
        secret_key=MINIO_SECRET,
        secure=MINIO_SECURE
    )

    # Создаём bucket если нет
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
        print(f"✓ Создан bucket: {MINIO_BUCKET}")

    url_map = {}
    image_blocks = [b for b in blocks if b.block_type == "image" and b.image_local]

    print(f"\nЗагружаю {len(image_blocks)} изображений в MinIO...")

    for i, block in enumerate(image_blocks):
        local_path = Path(images_base_dir) / Path(block.image_local).name
        if not local_path.exists():
            print(f"  [{i+1}] ⚠️  Файл не найден: {local_path}")
            continue

        # Путь в MinIO: textbooks/algebra9kz/images/img_007.jpg
        s3_key = f"textbooks/algebra9kz/{block.image_local}"

        try:
            client.fput_object(MINIO_BUCKET, s3_key, str(local_path))
            protocol = "https" if MINIO_SECURE else "http"
            url = f"{protocol}://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{s3_key}"
            url_map[block.image_local] = url
            print(f"  [{i+1}/{len(image_blocks)}] ✓ {Path(block.image_local).name}")
        except Exception as e:
            print(f"  [{i+1}] ✗ {e}")

    return url_map


# ─── ЗАГРУЗКА В POSTGRESQL ─────────────────────────────────────────────────────

SQL_CREATE_TEXTBOOK = """
CREATE TABLE IF NOT EXISTS textbooks (
    id         UUID PRIMARY KEY,
    title      TEXT NOT NULL,
    subject    VARCHAR(50),
    grade      INTEGER,
    language   VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

SQL_CREATE_BLOCKS = """
CREATE TABLE IF NOT EXISTS content_blocks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    textbook_id  UUID REFERENCES textbooks(id) ON DELETE CASCADE,
    chapter      TEXT,
    paragraph    TEXT,
    section      TEXT,
    block_order  INTEGER NOT NULL,
    block_type   VARCHAR(50) NOT NULL,
    content      TEXT,
    image_url    TEXT,
    metadata     JSONB DEFAULT '{}',
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_blocks_textbook ON content_blocks(textbook_id);
CREATE INDEX IF NOT EXISTS idx_blocks_type     ON content_blocks(block_type);
CREATE INDEX IF NOT EXISTS idx_blocks_chapter  ON content_blocks(chapter);
"""

def save_to_postgres(blocks: list[ContentBlock], url_map: dict[str, str]):
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print("⚠️  psycopg2 не установлен: pip install psycopg2-binary")
        save_to_json(blocks, url_map)
        return

    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()

    # Создаём таблицы если нет
    cur.execute(SQL_CREATE_TEXTBOOK)
    cur.execute(SQL_CREATE_BLOCKS)

    # Вставляем учебник
    cur.execute("""
        INSERT INTO textbooks (id, title, subject, grade, language)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (TEXTBOOK_ID, TEXTBOOK_TITLE, SUBJECT, GRADE, LANGUAGE))

    # Вставляем блоки пачками
    batch = []
    for b in blocks:
        image_url = url_map.get(b.image_local, b.image_local) if b.image_local else None
        batch.append((
            b.block_id, b.textbook_id, b.chapter, b.paragraph, b.section,
            b.block_order, b.block_type, b.content or None,
            image_url, json.dumps(b.metadata, ensure_ascii=False)
        ))

    psycopg2.extras.execute_batch(cur, """
        INSERT INTO content_blocks
            (id, textbook_id, chapter, paragraph, section,
             block_order, block_type, content, image_url, metadata)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, batch, page_size=200)

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n✓ Загружено в PostgreSQL: {len(blocks)} блоков")


# ─── FALLBACK: сохранение в JSON ───────────────────────────────────────────────

def save_to_json(blocks: list[ContentBlock], url_map: dict[str, str]):
    output = []
    for b in blocks:
        image_url = url_map.get(b.image_local, b.image_local) if b.image_local else None
        output.append({
            "id":          b.block_id,
            "textbook_id": b.textbook_id,
            "chapter":     b.chapter,
            "paragraph":   b.paragraph,
            "section":     b.section,
            "block_order": b.block_order,
            "block_type":  b.block_type,
            "content":     b.content,
            "image_url":   image_url,
            "metadata":    b.metadata,
        })

    out_path = "./algebra9_blocks.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Сохранено в JSON: {out_path} ({len(output)} блоков)")


# ─── СТАТИСТИКА ────────────────────────────────────────────────────────────────

def print_stats(blocks: list[ContentBlock]):
    from collections import Counter
    types = Counter(b.block_type for b in blocks)
    chapters = len(set(b.chapter for b in blocks if b.chapter))

    print("\n─── Статистика парсинга ───────────────────────────────")
    print(f"  Всего блоков:    {len(blocks)}")
    print(f"  Разделов:        {chapters}")
    print()
    for btype, count in sorted(types.items(), key=lambda x: -x[1]):
        print(f"  {btype:<25} {count}")
    print("───────────────────────────────────────────────────────")


# ─── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"📖 Парсинг: {MD_FILE}")
    parser = TextbookParser(MD_FILE)
    blocks = parser.parse()
    print_stats(blocks)

    # Загружаем изображения в MinIO (если доступен)
    url_map = upload_images_to_minio(blocks, IMAGES_DIR)

    # Сохраняем в PostgreSQL (или JSON если нет подключения)
    try:
        save_to_postgres(blocks, url_map)
    except Exception as e:
        print(f"⚠️  PostgreSQL недоступен ({e}), сохраняю в JSON...")
        save_to_json(blocks, url_map)

    print("\n✅ Готово!")
