#!/usr/bin/env python3
"""
Structured book parser for OCR text
Identifies paragraphs, questions, tasks, and content types
"""
import re
import json
import os

def classify_line(line):
    """Определение типа строки."""
    line = line.strip()

    if not line:
        return "empty"

    # Разделители страниц - пропускаем
    if re.match(r"^[─═-]{10,}$", line):
        return "separator"

    # Маркеры страниц [Страница N]
    if re.match(r"^\[Страница \d+\]$", line):
        return "page_marker"

    # Параграфы: $ 1., § 5., $12, §14
    # Также ловим OCR ошибки: 5 9. (§→5), 8 21. (§→8)
    if re.match(r"^[§$]\s*\d+", line):
        return "paragraph"
    # OCR ошибка: § распознаётся как 5 или 8
    if re.match(r"^[58]\s+\d+[-\d]*\.", line):
        return "paragraph"

    # Подзаголовки (часто идут большим шрифтом, длинные, без точки)
    # Улучшенная проверка для заголовков на казахском/русском
    if re.match(r"^[A-ZА-ЯӘӨҰҮҚҢІЁ][A-Za-zА-Яа-яӘәӨөҰұҮүҚқҢңІіЁё ,«»\"-]{8,}$", line):
        # Исключаем обычные предложения (содержат много маленьких слов)
        if not re.search(r"\s(и|в|на|с|у|о|а|но|да|или|к|по|от|за|до|из|при)\s", line, re.IGNORECASE):
            return "subtitle"

    # Нумерованные вопросы: "1. Текст вопроса?"
    if re.match(r"^\d+\.\s+.+", line):
        return "question"

    # Задания (топтық, жұптық + русские эквиваленты)
    if re.search(r"(Топтық жұмыс|Жұптық жұмыс|Тапсырма|Сұрақтар|Групповая работа|Парная работа|Задание|Вопросы)", line, re.IGNORECASE):
        return "task"

    # Источники
    if re.match(r"^(Дерек.*|Source.*|Көз.*|Источник.*)", line, re.IGNORECASE):
        return "source"

    # Иллюстрации
    if re.match(r"^(Сурет.*|Рис\.|Рисунок.*)", line, re.IGNORECASE):
        return "image"

    # Таблица
    if re.match(r"^(Кесте.*|Таблица.*)", line, re.IGNORECASE):
        return "table"

    # Длинные заголовки (АЛҒЫ СӨЗ и т.д.)
    if len(line) < 50 and line.isupper() and len(line.split()) <= 5:
        return "chapter_title"

    return "text"


def parse_book(text):
    """
    Главная функция: принимает текст OCR учебника
    и возвращает структурированный объект книги.
    """

    book = []
    current_paragraph = None
    current_page = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        line_type = classify_line(line)

        # Пропускаем разделители
        if line_type in ["separator", "empty"]:
            continue

        # Маркер страницы
        if line_type == "page_marker":
            page_match = re.search(r"\[Страница (\d+)\]", line)
            if page_match:
                current_page = int(page_match.group(1))
            continue

        # Новый параграф
        if line_type == "paragraph":
            current_paragraph = {
                "type": "paragraph",
                "title": line,
                "page": current_page,
                "content": []
            }
            book.append(current_paragraph)
            continue

        # Новая глава (большие заголовки)
        if line_type == "chapter_title":
            current_paragraph = {
                "type": "chapter",
                "title": line,
                "page": current_page,
                "content": []
            }
            book.append(current_paragraph)
            continue

        # Когда параграф/глава есть — добавляем элементы внутрь
        if current_paragraph:
            current_paragraph["content"].append({
                "type": line_type,
                "text": line,
                "page": current_page
            })
        else:
            # Текст до первого параграфа (введение, обложка и т.д.)
            if not book or book[-1].get("title") != "INTRO":
                book.append({
                    "type": "intro",
                    "title": "INTRO",
                    "page": current_page,
                    "content": []
                })
            book[-1]["content"].append({
                "type": line_type,
                "text": line,
                "page": current_page
            })

    return book


def save_as_json(book, filename="parsed_book.json"):
    """Сохранение в JSON формате."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(book, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON сохранён: {filename}")


def save_as_text(book, filename="parsed_book.txt"):
    """Сохранение в читаемом текстовом формате."""
    with open(filename, "w", encoding="utf-8") as f:
        for section in book:
            section_type = section.get('type', 'unknown')
            page = section.get('page', '?')

            f.write(f"\n{'═' * 70}\n")
            f.write(f"[{section_type.upper()}] {section['title']} (стр. {page})\n")
            f.write(f"{'═' * 70}\n\n")

            for item in section.get('content', []):
                item_type = item.get('type', 'text')
                item_page = item.get('page', '?')
                text = item.get('text', '')

                if item_type == "question":
                    f.write(f"\n❓ {text}\n")
                elif item_type == "task":
                    f.write(f"\n📝 {text}\n")
                elif item_type == "subtitle":
                    f.write(f"\n▶ {text}\n")
                elif item_type == "source":
                    f.write(f"\n📚 {text}\n")
                elif item_type == "image":
                    f.write(f"\n🖼️  {text}\n")
                elif item_type == "table":
                    f.write(f"\n📊 {text}\n")
                else:
                    f.write(f"{text}\n")

    print(f"✅ Текст сохранён: {filename}")


def print_statistics(book):
    """Вывод статистики по распарсенной книге."""
    total_sections = len(book)

    # Подсчёт типов секций
    chapters = sum(1 for s in book if s.get('type') == 'chapter')
    paragraphs = sum(1 for s in book if s.get('type') == 'paragraph')

    # Подсчёт типов контента
    questions = sum(
        sum(1 for item in s.get('content', []) if item.get('type') == 'question')
        for s in book
    )
    tasks = sum(
        sum(1 for item in s.get('content', []) if item.get('type') == 'task')
        for s in book
    )
    subtitles = sum(
        sum(1 for item in s.get('content', []) if item.get('type') == 'subtitle')
        for s in book
    )

    print("\n" + "═" * 70)
    print("📊 СТАТИСТИКА ПАРСИНГА")
    print("═" * 70)
    print(f"Всего секций: {total_sections}")
    print(f"  ├─ Глав: {chapters}")
    print(f"  └─ Параграфов: {paragraphs}")
    print(f"\nЭлементов контента:")
    print(f"  ├─ Вопросов: {questions}")
    print(f"  ├─ Заданий: {tasks}")
    print(f"  └─ Подзаголовков: {subtitles}")
    print("═" * 70 + "\n")


# -------------------------
# 🔥 Главная точка запуска
# -------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Parse OCR text into structured format')
    parser.add_argument('input_file', nargs='?', help='Path to input text file')
    parser.add_argument('-j', '--json', help='Path to output JSON file')
    parser.add_argument('-t', '--text', help='Path to output text file')

    args = parser.parse_args()

    # Default paths
    if args.input_file is None:
        input_file = "../books/output/История Казахстана Каз_improved.txt"
    else:
        input_file = args.input_file

    # Extract base name for output files
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    base_name = base_name.replace("_improved", "")

    if args.json is None:
        json_file = f"../results/{base_name}_parsed.json"
    else:
        json_file = args.json

    if args.text is None:
        text_file = f"../results/{base_name}_parsed.txt"
    else:
        text_file = args.text

    print(f"📖 Чтение файла: {input_file}")

    try:
        with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"❌ Ошибка: файл '{input_file}' не найден!")
        print(f"   Сначала запустите OCR: cd parsers && python pdf_to_text.py")
        exit(1)

    print("🔄 Парсинг книги...")
    book = parse_book(text)

    print("💾 Сохранение результатов...")
    save_as_json(book, json_file)
    save_as_text(book, text_file)

    print_statistics(book)

    print("✅ Готово! Файл успешно распарсен.")
    print("\nСозданные файлы:")
    print(f"  • {json_file} - структурированные данные")
    print(f"  • {text_file} - читаемый текстовый формат")
