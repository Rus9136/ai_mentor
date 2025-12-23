#!/usr/bin/env python3
"""
Генератор Mermaid Mind Map из распарсенного JSON книги
"""
import json
import re
import argparse
import os


def clean_text(text, max_len=50):
    """Очистка текста для Mermaid (убираем спецсимволы)."""
    # Убираем символы, которые ломают Mermaid
    text = re.sub(r'[()"\'\[\]{}«»<>|/\\]', '', text)
    text = re.sub(r'[─═\-]{2,}', '', text)
    text = text.strip()
    # Обрезаем длинный текст
    if len(text) > max_len:
        text = text[:max_len] + '...'
    return text


def is_valid_text(text):
    """Проверяет, что текст не является OCR мусором."""
    if not text or len(text) < 3:
        return False

    # Паттерны OCR мусора
    garbage_patterns = [
        r'\d[А-Я]{2,}\d',         # Цифры внутри слова: "ЗОЯ24УХАЧ"
        r'[А-Я]+\d+[А-Я]+',       # Буквы-цифры-буквы
        r'^[А-Я]{1,3}\d+',        # Короткие с цифрами в начале
        r'ТЕРРИТОРИИ',            # Артефакты карт
        r'ГРАНИЦЫ',
        r'ВОЕННЫЕ ПОХОДЫ',
        r'СТОЛИЦЫ',
        r'ПРОЧЕЕ',
        r'СОДЕРЖАНИЕ',
        r'ЕСТІСІН',
        r'НАСЕЛЕННЫЕ ПУНКТЫ',
        r'СВОБОДИТЕЛЬНАЯ БОРЬБА',
        r'В СОСТАВЕ$',
        r'^КАЗАХСТАН В',
        r'^[А-Я\s]+:$',           # Просто слово с двоеточием
        r'Ключевые слова',        # Служебные фразы
        r'Закрепите свои знания',
        r'Памятник Памятник',
    ]

    for pattern in garbage_patterns:
        if re.search(pattern, text):
            return False

    # Считаем долю кириллицы и латиницы
    letters = len(re.findall(r'[а-яА-ЯәөұүқңіёӘӨҰҮҚҢІЁa-zA-Z]', text))
    total = len(text.replace(' ', ''))
    if total == 0:
        return False
    ratio = letters / total
    # Должно быть минимум 70% букв
    return ratio > 0.7


def extract_structure(data):
    """Извлекает иерархическую структуру из JSON."""
    structure = {
        'title': 'История Казахстана XVIII-XIX вв.',
        'sections': []
    }

    # Собираем все параграфы
    all_paragraphs = []

    for item in data:
        item_type = item.get('type', '')
        title = item.get('title', '')

        # Пропускаем служебные страницы (УДК, ISBN и т.д.)
        skip_patterns = ['УДК', 'ББК', 'ISBN', 'ИБ №', 'И89', 'ІБВМ', 'ӘОЖ', 'КБЖ']
        if any(skip in title for skip in skip_patterns):
            continue

        # Только параграфы
        if item_type == 'paragraph':
            clean_title = clean_text(title, 60)
            if not is_valid_text(clean_title):
                continue
            # Пропускаем дубликаты из оглавления (короткие ссылки)
            if len(clean_title) < 15:
                continue

            paragraph = {
                'title': clean_title,
                'subtitles': [],
                'page': item.get('page', 0)
            }

            # Извлекаем подзаголовки из контента
            subtitle_count = 0
            for content_item in item.get('content', []):
                if subtitle_count >= 3:
                    break
                if content_item.get('type') == 'subtitle':
                    sub_text = clean_text(content_item.get('text', ''), 40)
                    if sub_text and len(sub_text) > 8 and is_valid_text(sub_text):
                        paragraph['subtitles'].append(sub_text)
                        subtitle_count += 1

            all_paragraphs.append(paragraph)

    # Группируем параграфы по темам (по номеру параграфа)
    sections_map = {
        'Казахско-джунгарские войны': [],
        'Присоединение к России': [],
        'Колониальная политика': [],
        'Национально-освободительное движение': [],
        'Культура и просвещение': [],
    }

    for para in all_paragraphs:
        title_lower = para['title'].lower()
        page = para.get('page', 0) or 0

        # Распределяем по темам на основе содержания и страниц
        if any(w in title_lower for w in ['джунгар', 'ополчени', 'бедстви', 'анракай', 'булант', 'батыр', 'бии']):
            sections_map['Казахско-джунгарские войны'].append(para)
        elif any(w in title_lower for w in ['присяг', 'русск', 'росси', 'абулхаир', 'абылай']):
            sections_map['Присоединение к России'].append(para)
        elif any(w in title_lower for w in ['реформ', 'колони', 'переселен', 'администр', 'торгов']):
            sections_map['Колониальная политика'].append(para)
        elif any(w in title_lower for w in ['восстан', 'освободит', 'кенесары', 'движени']):
            sections_map['Национально-освободительное движение'].append(para)
        elif any(w in title_lower for w in ['культур', 'литератур', 'просвещ', 'абай', 'алтынсар', 'шакарим']):
            sections_map['Культура и просвещение'].append(para)
        elif page < 50:
            sections_map['Казахско-джунгарские войны'].append(para)
        elif page < 100:
            sections_map['Присоединение к России'].append(para)
        elif page < 150:
            sections_map['Колониальная политика'].append(para)
        else:
            sections_map['Культура и просвещение'].append(para)

    # Формируем структуру
    for section_name, paragraphs in sections_map.items():
        if paragraphs:
            structure['sections'].append({
                'title': section_name,
                'paragraphs': paragraphs
            })

    return structure


def generate_markdown(structure, max_sections=10, max_paragraphs=6, max_subtitles=3):
    """Генерирует Markdown для Markmap."""
    lines = [f'# {structure["title"]}']

    for section in structure['sections'][:max_sections]:
        section_title = section['title'].replace('\n', ' ')
        lines.append(f'\n## {section_title}')

        for para in section['paragraphs'][:max_paragraphs]:
            para_title = para['title'].replace('\n', ' ')
            # Убираем $ в начале для чистоты
            para_title = re.sub(r'^\$\s*', '§ ', para_title)
            lines.append(f'\n### {para_title}')

            for sub in para['subtitles'][:max_subtitles]:
                sub_text = sub.replace('\n', ' ')
                lines.append(f'- {sub_text}')

    return '\n'.join(lines)


def generate_html(markdown_code, title="Mind Map"):
    """Генерирует HTML страницу с Markmap визуализацией."""
    # Экранируем markdown для вставки в JS
    escaped_md = markdown_code.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
        }}
        .header {{
            background: rgba(0,0,0,0.3);
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{
            color: #fff;
            font-size: 24px;
            font-weight: 500;
        }}
        .header p {{
            color: rgba(255,255,255,0.6);
            font-size: 14px;
            margin-top: 5px;
        }}
        #mindmap {{
            width: 100%;
            height: calc(100vh - 80px);
        }}
        svg {{
            width: 100%;
            height: 100%;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-view@0.15.4"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.15.4"></script>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Интерактивная карта • Колесо мыши для масштаба • Перетаскивание для навигации</p>
    </div>
    <svg id="mindmap"></svg>
    <script>
        const markdown = `{escaped_md}`;

        const {{ Transformer }} = window.markmap;
        const {{ Markmap }} = window.markmap;

        const transformer = new Transformer();
        const {{ root }} = transformer.transform(markdown);

        const svg = document.getElementById('mindmap');
        const mm = Markmap.create(svg, {{
            colorFreezeLevel: 2,
            duration: 500,
            maxWidth: 300,
            zoom: true,
            pan: true,
        }}, root);

        // Авто-подгонка при загрузке
        setTimeout(() => mm.fit(), 100);
    </script>
</body>
</html>'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Mermaid mindmap from parsed book JSON')
    parser.add_argument('input_file', nargs='?', help='Path to input JSON file')
    parser.add_argument('-o', '--output', help='Output file path (default: mindmap.html)')
    parser.add_argument('--mermaid', help='Also save raw Mermaid code to this file')
    parser.add_argument('--sections', type=int, default=10, help='Max sections to include')
    parser.add_argument('--paragraphs', type=int, default=5, help='Max paragraphs per section')

    args = parser.parse_args()

    # Default paths
    if args.input_file is None:
        input_file = "../results/ИсторияКазахстана7_Рус_parsed.json"
    else:
        input_file = args.input_file

    if args.output is None:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"../results/{base_name}_mindmap.html"
    else:
        output_file = args.output

    print(f"📖 Загрузка: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("🔄 Извлечение структуры...")
    structure = extract_structure(data)

    print(f"   Найдено разделов: {len(structure['sections'])}")
    total_paragraphs = sum(len(s['paragraphs']) for s in structure['sections'])
    print(f"   Найдено параграфов: {total_paragraphs}")

    print("🎨 Генерация Markmap диаграммы...")
    markdown_code = generate_markdown(
        structure,
        max_sections=args.sections,
        max_paragraphs=args.paragraphs
    )

    # Сохраняем Markdown код если нужно
    if args.mermaid:
        with open(args.mermaid, 'w', encoding='utf-8') as f:
            f.write(markdown_code)
        print(f"✅ Markdown: {args.mermaid}")

    # Генерируем HTML
    html = generate_html(markdown_code, structure['title'])

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ HTML сохранён: {output_file}")
    print(f"\n🌐 Откройте в браузере: file://{os.path.abspath(output_file)}")
