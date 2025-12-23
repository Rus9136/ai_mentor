#!/usr/bin/env python3
"""
Скрипт загрузки структурированного учебника (structured_book_kz.json) в базу данных.

Формат JSON:
{
    "textbook": {...},
    "chapters": [
        {
            "number": 1,
            "title": "...",
            "paragraphs": [
                {
                    "number": 1,
                    "title": "...",
                    "learning_objective": "...",
                    "key_terms": [...],
                    "content": "...",
                    "questions": [...]
                }
            ]
        }
    ]
}

Использование:
    python load_structured_book.py books/output/structured_book_kz.json
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph


async def load_to_database(data: dict, db_url: str, dry_run: bool = False):
    """Загружает данные в базу."""

    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("📚 Загрузка учебника в базу данных...")
        print("=" * 60)

        textbook_data = data['textbook']
        chapters_data = data['chapters']

        if dry_run:
            print("🔍 DRY RUN - данные НЕ будут записаны в БД")
            print()

        # 1. Проверяем, нет ли уже такого учебника
        existing = await session.execute(
            select(Textbook).where(
                Textbook.title == textbook_data['title'],
                Textbook.school_id.is_(None),
                Textbook.is_deleted == False
            )
        )
        if existing.scalar_one_or_none():
            print(f"⚠️  Учебник '{textbook_data['title']}' уже существует!")
            print("   Используйте --force для перезаписи или удалите существующий")
            return None

        # 2. Создаем учебник
        textbook = Textbook(
            school_id=None,  # Глобальный контент
            title=textbook_data['title'],
            subject=textbook_data['subject'],
            grade_level=textbook_data['grade_level'],
            author=textbook_data.get('authors', textbook_data.get('author')),
            publisher=textbook_data.get('publisher'),
            year=textbook_data.get('year'),
            isbn=textbook_data.get('isbn'),
            description=textbook_data.get('description'),
            is_active=True,
        )

        print(f"📖 Учебник: {textbook.title}")
        print(f"   Предмет: {textbook.subject}, Класс: {textbook.grade_level}")
        print(f"   Автор: {textbook.author}")
        print(f"   Издательство: {textbook.publisher}, Год: {textbook.year}")
        print()

        if not dry_run:
            session.add(textbook)
            await session.flush()  # Получаем ID

        # 3. Создаем разделы и параграфы
        total_paragraphs = 0
        total_questions = 0

        for chapter_data in chapters_data:
            # Номер главы может быть римским числом в title
            chapter_num = chapter_data.get('number', 1)
            if isinstance(chapter_num, str):
                # Конвертируем римские числа
                roman_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}
                chapter_num = roman_map.get(chapter_num, int(chapter_num) if chapter_num.isdigit() else 1)

            chapter = Chapter(
                textbook_id=textbook.id if not dry_run else 0,
                title=chapter_data['title'],
                number=chapter_num,
                order=chapter_num,
                description=chapter_data.get('description'),
            )

            paragraphs_list = chapter_data.get('paragraphs', [])
            para_count = len(paragraphs_list)
            q_count = sum(
                len(p.get('questions') or [])
                for p in paragraphs_list
            )

            print(f"  📁 Раздел {chapter_num}: {chapter_data['title']}")
            print(f"     Параграфов: {para_count}, Вопросов: {q_count}")

            if not dry_run:
                session.add(chapter)
                await session.flush()

            # Параграфы
            for idx, para_data in enumerate(paragraphs_list):
                # Обработка key_terms - может быть список
                key_terms = para_data.get('key_terms', [])
                if isinstance(key_terms, list):
                    key_terms_json = json.dumps(key_terms, ensure_ascii=False)
                else:
                    key_terms_json = key_terms

                # Обработка questions - может быть список строк
                questions = para_data.get('questions', [])
                if isinstance(questions, list) and questions:
                    # Конвертируем список строк в формат для БД
                    questions_formatted = [
                        {"order": i+1, "text": q} if isinstance(q, str) else q
                        for i, q in enumerate(questions)
                    ]
                else:
                    questions_formatted = None

                paragraph = Paragraph(
                    chapter_id=chapter.id if not dry_run else 0,
                    title=para_data['title'],
                    number=para_data.get('number', idx + 1),
                    order=idx + 1,
                    content=para_data.get('content', ''),
                    learning_objective=para_data.get('learning_objective'),
                    key_terms=key_terms_json if key_terms else None,
                    questions=questions_formatted,
                )

                if not dry_run:
                    session.add(paragraph)

                total_paragraphs += 1
                total_questions += len(questions)

        print()
        print("=" * 60)
        print(f"📊 Итого:")
        print(f"   Разделов: {len(chapters_data)}")
        print(f"   Параграфов: {total_paragraphs}")
        print(f"   Вопросов: {total_questions}")

        if not dry_run:
            await session.commit()
            print()
            print(f"✅ Учебник успешно загружен! ID: {textbook.id}")
            return textbook.id
        else:
            print()
            print("🔍 DRY RUN завершен. Для загрузки уберите флаг --dry-run")
            return None


async def main():
    parser = argparse.ArgumentParser(
        description='Загрузка структурированного учебника в БД AI Mentor'
    )
    parser.add_argument(
        'input_file',
        help='Путь к JSON файлу со структурированным учебником'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Только показать что будет загружено, без записи в БД'
    )
    parser.add_argument(
        '--db-url',
        default='postgresql+asyncpg://ai_mentor_user:ai_mentor_pass@localhost:5433/ai_mentor_db',
        help='URL базы данных'
    )

    args = parser.parse_args()

    # Читаем JSON
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"❌ Файл не найден: {input_path}")
        sys.exit(1)

    print(f"📂 Чтение файла: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Проверяем формат
    if 'textbook' not in data or 'chapters' not in data:
        print("❌ Неверный формат JSON. Ожидается структура с 'textbook' и 'chapters'")
        sys.exit(1)

    print(f"   Глав в файле: {len(data['chapters'])}")
    total_p = sum(len(ch.get('paragraphs', [])) for ch in data['chapters'])
    print(f"   Параграфов: {total_p}")
    print()

    # Загружаем в БД
    await load_to_database(data, args.db_url, dry_run=args.dry_run)


if __name__ == '__main__':
    asyncio.run(main())
