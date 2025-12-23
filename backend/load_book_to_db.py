#!/usr/bin/env python3
"""
Скрипт загрузки распарсенных учебников в базу данных AI Mentor.

Загружает книгу как глобальный контент (school_id=NULL).
Создает: Textbook → Chapters → Paragraphs

Использование:
    python load_to_db.py results/ИсторияКазахстана7_Рус_parsed.json --lang ru
    python load_to_db.py results/История_Казахстана_Каз_parsed.json --lang kk
"""
import asyncio
import argparse
import json
import re
import sys
import os
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, text

from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph


# ============================================================================
# КОНФИГУРАЦИЯ УЧЕБНИКА "ИСТОРИЯ КАЗАХСТАНА 7 КЛАСС"
# ============================================================================

TEXTBOOK_CONFIG = {
    "ru": {
        "title": "История Казахстана (XVIII-XIX вв.)",
        "subject": "История Казахстана",
        "grade_level": 7,
        "author": "Т. Омарбеков, Г.Б. Хабижанова, Т.Е. Картаева, М.С. Ногайбаева, Г.Е. Абикенова",
        "publisher": "Мектеп",
        "year": 2025,
        "isbn": "978-601-07-1769-5",
        "description": "Учебник по истории Казахстана для 7 класса общеобразовательных школ. "
                      "Охватывает период XVIII-XIX веков: казахско-джунгарские войны, "
                      "вхождение в состав Российской империи, национально-освободительные движения.",
    },
    "kk": {
        "title": "Қазақстан тарихы (XVIII-XIX ғғ.)",
        "subject": "Қазақстан тарихы",
        "grade_level": 7,
        "author": "Т. Омарбеков, Г.Б. Хабижанова, Т.Е. Картаева, М.С. Ногайбаева, Г.Е. Абикенова",
        "publisher": "Мектеп",
        "year": 2025,
        "isbn": "978-601-07-1769-5",
        "description": "7 сынып жалпы білім беретін мектептеріне арналған Қазақстан тарихы оқулығы.",
    }
}

# Маппинг параграфов к разделам (из оглавления)
CHAPTERS_CONFIG = {
    "ru": [
        {
            "number": 1,
            "title": "Казахско-джунгарские войны",
            "description": "Противостояние Казахского ханства и Джунгарии в XVIII веке",
            "paragraphs": range(1, 7),  # §1-6
        },
        {
            "number": 2,
            "title": "Казахское ханство в XVIII веке",
            "description": "Политическое развитие и казахско-русские отношения",
            "paragraphs": range(7, 15),  # §7-14
        },
        {
            "number": 3,
            "title": "Культура Казахстана в XVIII веке",
            "description": "Духовная культура, традиции и искусство",
            "paragraphs": range(15, 19),  # §15-18
        },
        {
            "number": 4,
            "title": "Колонизация и народно-освободительная борьба",
            "description": "Колониальная политика и восстания казахов",
            "paragraphs": range(19, 33),  # §19-32
        },
        {
            "number": 5,
            "title": "Казахстан в составе Российской империи",
            "description": "Административные реформы и социально-экономические изменения",
            "paragraphs": range(33, 46),  # §33-45
        },
        {
            "number": 6,
            "title": "Культура Казахстана в XIX - начале XX века",
            "description": "Просвещение, литература, наука и искусство",
            "paragraphs": range(46, 61),  # §46-60
        },
    ],
    "kk": [
        {
            "number": 1,
            "title": "Қазақ-жоңғар соғыстары",
            "description": "XVIII ғасырдағы Қазақ хандығы мен Жоңғария арасындағы қарсылық",
            "paragraphs": range(1, 7),
        },
        {
            "number": 2,
            "title": "XVIII ғасырдағы Қазақ хандығы",
            "description": "Саяси даму және қазақ-орыс қатынастары",
            "paragraphs": range(7, 15),
        },
        {
            "number": 3,
            "title": "XVIII ғасырдағы Қазақстан мәдениеті",
            "description": "Рухани мәдениет, дәстүрлер және өнер",
            "paragraphs": range(15, 19),
        },
        {
            "number": 4,
            "title": "Отарлау және ұлт-азаттық қозғалыс",
            "description": "Отарлық саясат және қазақтардың көтерілістері",
            "paragraphs": range(19, 33),
        },
        {
            "number": 5,
            "title": "Ресей империясы құрамындағы Қазақстан",
            "description": "Әкімшілік реформалар және әлеуметтік-экономикалық өзгерістер",
            "paragraphs": range(33, 46),
        },
        {
            "number": 6,
            "title": "XIX - XX ғасыр басындағы Қазақстан мәдениеті",
            "description": "Ағарту, әдебиет, ғылым және өнер",
            "paragraphs": range(46, 61),
        },
    ]
}


# ============================================================================
# ФУНКЦИИ ОБРАБОТКИ ДАННЫХ
# ============================================================================

def extract_paragraph_number(title: str) -> Optional[int]:
    """
    Извлекает номер параграфа из заголовка.

    Примеры:
        "$ 1. Внутреннее положение..." → 1
        "§ 5. Анракайская битва..." → 5
        "$12 Становление Абылай хана..." → 12
        "$ 7-8. Казахско-русские отношения..." → 7
        "5 9. Причины и последствия..." → 9 (OCR ошибка: §→5)
        "8 21-22. Национально-освободительное..." → 21 (OCR ошибка: §→8)
    """
    # Паттерн: $ или § + номер
    match = re.match(r'^[§$]\s*(\d+)', title)
    if match:
        return int(match.group(1))
    # OCR ошибка: § распознаётся как 5 или 8
    match = re.match(r'^[58]\s+(\d+)', title)
    if match:
        return int(match.group(1))
    return None


def clean_paragraph_title(title: str) -> str:
    """
    Очищает заголовок параграфа от символов § и $.

    "$ 1. Внутреннее положение..." → "Внутреннее положение..."
    "5 9. Причины..." → "Причины..." (OCR ошибка)
    """
    # Убираем "$ N." или "§ N." из начала
    cleaned = re.sub(r'^[§$]\s*\d+[-\d]*\.\s*', '', title)
    # OCR ошибка: "5 N." или "8 N."
    cleaned = re.sub(r'^[58]\s+\d+[-\d]*\.\s*', '', cleaned)
    # Если осталось пусто или только номер
    if not cleaned or re.match(r'^\d+$', cleaned):
        return title
    return cleaned.strip()


def extract_content_and_questions(content_items: list) -> tuple[str, list]:
    """
    Разделяет content на текст и вопросы.

    Returns:
        (full_text, questions_list)
    """
    text_parts = []
    questions = []
    question_order = 1

    for item in content_items:
        item_type = item.get('type', 'text')
        item_text = item.get('text', '').strip()

        if not item_text:
            continue

        if item_type == 'question':
            # Извлекаем номер вопроса если есть
            q_match = re.match(r'^(\d+)\.\s*(.+)', item_text)
            if q_match:
                q_text = q_match.group(2)
            else:
                q_text = item_text

            questions.append({
                "order": question_order,
                "text": q_text
            })
            question_order += 1

        elif item_type in ('text', 'subtitle'):
            text_parts.append(item_text)

        elif item_type == 'task':
            # Задания тоже добавляем в текст
            text_parts.append(f"\n[Задание] {item_text}")

        elif item_type == 'source':
            text_parts.append(f"\n[Источник] {item_text}")

        elif item_type == 'image':
            text_parts.append(f"\n[Иллюстрация: {item_text}]")

        elif item_type == 'table':
            text_parts.append(f"\n[Таблица: {item_text}]")

    full_text = '\n'.join(text_parts)
    return full_text, questions


def find_chapter_for_paragraph(para_num: int, chapters_config: list) -> Optional[dict]:
    """Находит раздел для данного номера параграфа."""
    for chapter in chapters_config:
        if para_num in chapter['paragraphs']:
            return chapter
    return None


def transform_parsed_data(parsed_data: list, lang: str) -> dict:
    """
    Трансформирует данные парсера в структуру для загрузки в БД.

    Returns:
        {
            "textbook": {...},
            "chapters": [
                {
                    "number": 1,
                    "title": "...",
                    "paragraphs": [
                        {"number": 1, "title": "...", "content": "...", "questions": [...]}
                    ]
                }
            ]
        }
    """
    chapters_config = CHAPTERS_CONFIG[lang]
    textbook_config = TEXTBOOK_CONFIG[lang]

    # Собираем параграфы из parsed_data
    # ВАЖНО: может быть несколько секций с одним номером (оглавление + реальный контент)
    # Берем версию с максимальным контентом
    parsed_paragraphs = {}
    for section in parsed_data:
        if section.get('type') != 'paragraph':
            continue

        title = section.get('title', '')
        para_num = extract_paragraph_number(title)

        if para_num is None:
            continue

        content_items = section.get('content', [])
        full_text, questions = extract_content_and_questions(content_items)

        # Если уже есть параграф с таким номером - берем тот, что длиннее
        if para_num in parsed_paragraphs:
            existing_len = len(parsed_paragraphs[para_num]['content'])
            if len(full_text) <= existing_len:
                continue  # Текущий короче - пропускаем

        parsed_paragraphs[para_num] = {
            "number": para_num,
            "title": clean_paragraph_title(title),
            "content": full_text,
            "questions": questions if questions else None,
            "page": section.get('page'),
        }

    # Формируем структуру разделов
    chapters = []
    for chapter_cfg in chapters_config:
        chapter_paragraphs = []

        for para_num in chapter_cfg['paragraphs']:
            if para_num in parsed_paragraphs:
                chapter_paragraphs.append(parsed_paragraphs[para_num])

        chapters.append({
            "number": chapter_cfg['number'],
            "title": chapter_cfg['title'],
            "description": chapter_cfg.get('description'),
            "paragraphs": chapter_paragraphs,
        })

    return {
        "textbook": textbook_config,
        "chapters": chapters,
    }


# ============================================================================
# ЗАГРУЗКА В БД
# ============================================================================

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
            print("   Используйте --force для перезаписи")
            return

        # 2. Создаем учебник
        textbook = Textbook(
            school_id=None,  # Глобальный контент
            title=textbook_data['title'],
            subject=textbook_data['subject'],
            grade_level=textbook_data['grade_level'],
            author=textbook_data.get('author'),
            publisher=textbook_data.get('publisher'),
            year=textbook_data.get('year'),
            isbn=textbook_data.get('isbn'),
            description=textbook_data.get('description'),
            is_active=True,
        )

        print(f"📖 Учебник: {textbook.title}")
        print(f"   Предмет: {textbook.subject}, Класс: {textbook.grade_level}")
        print()

        if not dry_run:
            session.add(textbook)
            await session.flush()  # Получаем ID

        # 3. Создаем разделы и параграфы
        total_paragraphs = 0
        total_questions = 0

        for chapter_data in chapters_data:
            chapter = Chapter(
                textbook_id=textbook.id if not dry_run else 0,
                title=chapter_data['title'],
                number=chapter_data['number'],
                order=chapter_data['number'],
                description=chapter_data.get('description'),
            )

            para_count = len(chapter_data['paragraphs'])
            q_count = sum(
                len(p.get('questions') or [])
                for p in chapter_data['paragraphs']
            )

            print(f"  📁 Раздел {chapter_data['number']}: {chapter_data['title']}")
            print(f"     Параграфов: {para_count}, Вопросов: {q_count}")

            if not dry_run:
                session.add(chapter)
                await session.flush()

            # Параграфы
            for idx, para_data in enumerate(chapter_data['paragraphs']):
                paragraph = Paragraph(
                    chapter_id=chapter.id if not dry_run else 0,
                    title=para_data['title'],
                    number=para_data['number'],
                    order=idx + 1,
                    content=para_data['content'],
                    questions=para_data.get('questions'),
                )

                if not dry_run:
                    session.add(paragraph)

                total_paragraphs += 1
                total_questions += len(para_data.get('questions') or [])

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
        else:
            print()
            print("🔍 DRY RUN завершен. Для загрузки уберите флаг --dry-run")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description='Загрузка распарсенного учебника в БД AI Mentor'
    )
    parser.add_argument(
        'input_file',
        help='Путь к JSON файлу с результатами парсинга'
    )
    parser.add_argument(
        '--lang', '-l',
        choices=['ru', 'kk'],
        default='ru',
        help='Язык учебника: ru (русский) или kk (казахский)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Только показать что будет загружено, без записи в БД'
    )
    # Собираем URL из переменных окружения или используем default
    default_db_url = os.getenv(
        'DATABASE_URL',
        f"postgresql+asyncpg://{os.getenv('POSTGRES_USER', 'ai_mentor_user')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'ai_mentor_pass')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'ai_mentor_db')}"
    )

    parser.add_argument(
        '--db-url',
        default=default_db_url,
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
        parsed_data = json.load(f)

    print(f"   Секций в файле: {len(parsed_data)}")
    print()

    # Трансформируем данные
    transformed = transform_parsed_data(parsed_data, args.lang)

    # Загружаем в БД
    await load_to_database(transformed, args.db_url, dry_run=args.dry_run)


if __name__ == '__main__':
    asyncio.run(main())
