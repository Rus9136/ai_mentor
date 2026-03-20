"""
Seed script for coding courses (learning paths).

Generates SQL INSERT statements for 3 courses with lessons:
1. Основы Python (6 класс, 20 уроков)
2. Продвинутый Python (8-9 класс, 16 уроков)
3. ООП на Python (9-10 класс, 12 уроков)

Usage:
    python scripts/seed_coding_courses.py > seed_courses.sql
    # Then run in psql or via docker exec

Each lesson has theory_content (markdown) and optionally links to an existing
coding_challenge by title pattern.
"""

COURSES = [
    {
        "title": "Основы Python",
        "title_kk": "Python негіздері",
        "description": "Первый курс программирования для начинающих. От print() до списков.",
        "description_kk": "Бағдарламалау бойынша бірінші курс. print()-тен бастап тізімдерге дейін.",
        "slug": "python-basics",
        "grade_level": 6,
        "estimated_hours": 10,
        "sort_order": 0,
        "icon": "Snake",
        "lessons": [
            {
                "title": "Что такое программирование?",
                "title_kk": "Бағдарламалау деген не?",
                "theory": """# Что такое программирование?

**Программирование** — это умение давать компьютеру точные инструкции.

Представь, что ты объясняешь роботу, как приготовить бутерброд:
1. Возьми хлеб
2. Положи масло
3. Положи сыр

Каждый шаг — это **команда**. Набор команд — это **программа**.

## Языки программирования

Компьютер не понимает казахский или русский. Для общения с ним есть **языки программирования**:
- **Python** — простой и мощный
- JavaScript — для веб-сайтов
- C++ — для игр и быстрых программ

Мы будем учить **Python** — один из самых популярных языков в мире!

## Почему Python?

- Простой синтаксис (легко читать)
- Используется в Google, NASA, Instagram
- Подходит для начинающих

В следующем уроке мы напишем первую программу!""",
                "theory_kk": "# Бағдарламалау деген не?\n\n**Бағдарламалау** — компьютерге нақты нұсқаулар беру.\n\nРобот бутерброд жасау:\n1. Нан ал\n2. Май жақ\n3. Ірімшік қой\n\nӘр қадам — **команда**. Командалар жиынтығы — **бағдарлама**.\n\n## Python тілі\n\n- Қарапайым синтаксис\n- Google, NASA қолданады\n- Жаңадан бастаушыларға қолайлы",
            },
            {
                "title": "Первая программа: print()",
                "title_kk": "Бірінші бағдарлама: print()",
                "theory": """# Первая программа: print()

Функция `print()` выводит текст на экран.

```python
print("Привет, мир!")
```

Результат:
```
Привет, мир!
```

## Правила

- Текст (строка) пишется **в кавычках**: `"текст"` или `'текст'`
- Кавычки обязательны! Без них Python не поймёт, что это текст

## Несколько print()

```python
print("Строка 1")
print("Строка 2")
print("Строка 3")
```

Каждый `print()` выводит текст на **новой строке**.

## Попробуй!

Напиши программу, которая выводит своё имя:
```python
print("Меня зовут Адилет!")
```""",
                "theory_kk": "# Бірінші бағдарлама: print()\n\n`print()` функциясы мәтінді экранға шығарады.\n\n```python\nprint(\"Сәлем, Әлем!\")\n```\n\nНәтиже:\n```\nСәлем, Әлем!\n```",
                "challenge_title_pattern": "Привет, мир",
            },
            {
                "title": "Переменные — коробки для данных",
                "title_kk": "Айнымалылар — деректерге арналған қораптар",
                "theory": """# Переменные

**Переменная** — это имя для хранения данных. Как коробка с подписью.

```python
name = "Айгерим"
age = 14
print(name)
print(age)
```

Результат:
```
Айгерим
14
```

## Правила имён переменных

- Можно: буквы, цифры, `_`
- Нельзя начинать с цифры
- Нельзя использовать пробелы

```python
my_name = "Адилет"    # ✅ правильно
student1 = "Бекзат"   # ✅ правильно
1student = "Ошибка"   # ❌ начинается с цифры
```

## Переменная может менять значение

```python
x = 5
print(x)  # 5
x = 10
print(x)  # 10
```

Как коробка — можно достать старое и положить новое.""",
                "theory_kk": "# Айнымалылар\n\n**Айнымалы** — деректерді сақтау үшін аты. Жазуы бар қорап сияқты.\n\n```python\nname = \"Айгерім\"\nage = 14\nprint(name)\nprint(age)\n```",
            },
            {
                "title": "Типы данных: числа и строки",
                "title_kk": "Деректер түрлері: сандар мен жолдар",
                "theory": """# Типы данных

В Python есть разные типы данных:

## Числа (int, float)

```python
age = 14          # int — целое число
height = 1.65     # float — дробное число
```

С числами можно считать:
```python
a = 10
b = 3
print(a + b)   # 13
print(a - b)   # 7
print(a * b)   # 30
print(a / b)   # 3.333...
print(a // b)  # 3 — целочисленное деление
print(a % b)   # 1 — остаток от деления
```

## Строки (str)

```python
name = "Python"
greeting = 'Сәлем!'
```

Строки можно складывать:
```python
first = "Привет"
second = ", мир!"
print(first + second)  # Привет, мир!
```

## Проверка типа

```python
print(type(14))      # <class 'int'>
print(type(1.5))     # <class 'float'>
print(type("текст")) # <class 'str'>
```""",
                "theory_kk": "# Деректер түрлері\n\n## Сандар (int, float)\n\n```python\nage = 14          # int — бүтін сан\nheight = 1.65     # float — бөлшек сан\n```\n\n## Жолдар (str)\n\n```python\nname = \"Python\"\ngreeting = 'Сәлем!'\n```",
            },
            {
                "title": "Ввод данных: input()",
                "title_kk": "Деректер енгізу: input()",
                "theory": """# Ввод данных: input()

Функция `input()` позволяет пользователю ввести данные с клавиатуры.

```python
name = input("Как тебя зовут? ")
print("Привет, " + name + "!")
```

## Важно: input() всегда возвращает строку!

```python
age = input("Сколько тебе лет? ")
print(type(age))  # <class 'str'> — это строка, не число!
```

Чтобы получить число, используй `int()`:

```python
age = int(input("Сколько тебе лет? "))
print(age + 1)  # Теперь можно считать!
```

## Шаблон для ввода числа

```python
n = int(input())  # Ввести целое число
x = float(input())  # Ввести дробное число
```""",
                "theory_kk": "# Деректер енгізу: input()\n\n`input()` функциясы пайдаланушыдан деректерді алады.\n\n```python\nname = input(\"Атыңыз кім? \")\nprint(\"Сәлем, \" + name + \"!\")\n```\n\n**Маңызды:** `input()` әрқашан жол (str) қайтарады!\n\n```python\nn = int(input())  # Бүтін сан енгізу\n```",
                "challenge_title_pattern": "Эхо",
            },
            {
                "title": "Арифметические операции",
                "title_kk": "Арифметикалық амалдар",
                "theory": """# Арифметические операции

| Операция | Символ | Пример | Результат |
|----------|--------|--------|-----------|
| Сложение | `+` | `5 + 3` | `8` |
| Вычитание | `-` | `10 - 4` | `6` |
| Умножение | `*` | `3 * 7` | `21` |
| Деление | `/` | `15 / 4` | `3.75` |
| Целочисленное деление | `//` | `15 // 4` | `3` |
| Остаток | `%` | `15 % 4` | `3` |
| Степень | `**` | `2 ** 3` | `8` |

## Порядок операций

Как в математике: сначала `**`, потом `*`, `/`, `//`, `%`, в конце `+`, `-`.

```python
result = 2 + 3 * 4    # 14, не 20!
result = (2 + 3) * 4  # 20 — скобки меняют порядок
```

## Практика

```python
a = int(input())
b = int(input())
print("Сумма:", a + b)
print("Разность:", a - b)
print("Произведение:", a * b)
```""",
                "theory_kk": "# Арифметикалық амалдар\n\n| Амал | Белгі | Мысал | Нәтиже |\n|------|--------|--------|--------|\n| Қосу | `+` | `5 + 3` | `8` |\n| Азайту | `-` | `10 - 4` | `6` |\n| Көбейту | `*` | `3 * 7` | `21` |\n| Бөлу | `/` | `15 / 4` | `3.75` |",
                "challenge_title_pattern": "Сумма двух чисел",
            },
            {
                "title": "Практика: калькулятор",
                "title_kk": "Тәжірибе: калькулятор",
                "theory": """# Практика: калькулятор

Давай объединим всё, что узнали, и напишем простой калькулятор!

## Задание

Программа получает два числа и выводит результаты всех операций.

```python
a = int(input())
b = int(input())

print(a + b)   # сумма
print(a - b)   # разность
print(a * b)   # произведение
```

## Площадь прямоугольника

```python
width = int(input())
height = int(input())
area = width * height
print(area)
```

Теперь реши задачу на практике!""",
                "theory_kk": "# Тәжірибе: калькулятор\n\nБарлық үйренгенімізді біріктірейік!\n\n```python\na = int(input())\nb = int(input())\nprint(a + b)\nprint(a - b)\nprint(a * b)\n```",
                "challenge_title_pattern": "Площадь прямоугольника",
            },
            {
                "title": "Условие if — принимаем решения",
                "title_kk": "if шарты — шешім қабылдау",
                "theory": """# Условие if

Условие `if` позволяет выполнять код только если условие **истинно**.

```python
age = int(input("Сколько тебе лет? "))

if age >= 18:
    print("Ты взрослый!")
```

## Важно: отступы!

Python использует **отступы** (4 пробела) для обозначения блока кода:

```python
if age >= 18:
    print("Строка 1 — внутри if")
    print("Строка 2 — внутри if")
print("Строка 3 — вне if, выполнится всегда")
```

## Операторы сравнения

| Оператор | Значение |
|----------|----------|
| `==` | равно |
| `!=` | не равно |
| `>` | больше |
| `<` | меньше |
| `>=` | больше или равно |
| `<=` | меньше или равно |""",
                "theory_kk": "# if шарты\n\n`if` шарт **ақиқат** болғанда ғана кодты орындайды.\n\n```python\nage = int(input())\nif age >= 18:\n    print(\"Сен ересексің!\")\n```",
            },
            {
                "title": "if/else — два пути",
                "title_kk": "if/else — екі жол",
                "theory": """# if/else — два пути

`else` выполняется когда условие `if` **ложно**:

```python
number = int(input())

if number % 2 == 0:
    print("Чётное")
else:
    print("Нечётное")
```

## Пример: проверка пароля

```python
password = input("Введи пароль: ")

if password == "secret123":
    print("Доступ разрешён!")
else:
    print("Неверный пароль!")
```

Реши задачу — определи, чётное число или нечётное!""",
                "theory_kk": "# if/else — екі жол\n\n`else` — `if` шарт **жалған** болғанда орындалады:\n\n```python\nnumber = int(input())\nif number % 2 == 0:\n    print(\"Жұп\")\nelse:\n    print(\"Тақ\")\n```",
                "challenge_title_pattern": "Чётное или нечётное",
            },
            {
                "title": "elif — много путей",
                "title_kk": "elif — көп жол",
                "theory": """# elif — много путей

Когда вариантов больше двух, используй `elif`:

```python
score = int(input("Введи балл: "))

if score >= 90:
    print("Отлично! 5")
elif score >= 70:
    print("Хорошо! 4")
elif score >= 50:
    print("Удовлетворительно. 3")
else:
    print("Нужно подтянуть. 2")
```

## Порядок важен!

Python проверяет условия **сверху вниз** и выполняет **первое** подходящее.

Реши задачу — определи оценку по баллу!""",
                "theory_kk": "# elif — көп жол\n\nЕкі нұсқадан көп болса, `elif` қолданыңыз:\n\n```python\nscore = int(input())\nif score >= 90:\n    print(\"Өте жақсы! 5\")\nelif score >= 70:\n    print(\"Жақсы! 4\")\nelif score >= 50:\n    print(\"Қанағаттанарлық. 3\")\nelse:\n    print(\"Жақсарту керек. 2\")\n```",
                "challenge_title_pattern": "Оценка по баллу",
            },
            {
                "title": "Практика: условия",
                "title_kk": "Тәжірибе: шарттар",
                "theory": """# Практика: условия

Закрепим условия на практике.

## Задание: Максимум из трёх

Дано три числа. Найди наибольшее.

```python
a = int(input())
b = int(input())
c = int(input())

if a >= b and a >= c:
    print(a)
elif b >= a and b >= c:
    print(b)
else:
    print(c)
```

## Логические операторы

| Оператор | Значение |
|----------|----------|
| `and` | И (оба условия верны) |
| `or` | ИЛИ (хотя бы одно верно) |
| `not` | НЕ (инвертирует) |

Реши задачу!""",
                "theory_kk": "# Тәжірибе: шарттар\n\nШарттарды тәжірибеде бекітеміз.\n\n```python\na = int(input())\nb = int(input())\nc = int(input())\nif a >= b and a >= c:\n    print(a)\nelif b >= a and b >= c:\n    print(b)\nelse:\n    print(c)\n```",
                "challenge_title_pattern": "Максимум из трёх",
            },
            {
                "title": "Цикл for — повторяем действия",
                "title_kk": "for циклі — әрекеттерді қайталау",
                "theory": """# Цикл for

Цикл `for` повторяет действия заданное число раз.

```python
for i in range(5):
    print("Привет!")
```

Выведет "Привет!" 5 раз.

## range() — генератор чисел

```python
range(5)        # 0, 1, 2, 3, 4
range(1, 6)     # 1, 2, 3, 4, 5
range(0, 10, 2) # 0, 2, 4, 6, 8
```

## Пример: сумма от 1 до N

```python
n = int(input())
total = 0
for i in range(1, n + 1):
    total += i
print(total)
```""",
                "theory_kk": "# for циклі\n\n`for` циклі берілген рет әрекеттерді қайталайды.\n\n```python\nfor i in range(5):\n    print(\"Сәлем!\")\n```\n\n## range()\n\n```python\nrange(5)        # 0, 1, 2, 3, 4\nrange(1, 6)     # 1, 2, 3, 4, 5\n```",
                "challenge_title_pattern": "Сумма от 1 до N",
            },
            {
                "title": "range() — счётчик повторений",
                "title_kk": "range() — қайталау есептегіші",
                "theory": """# range() подробнее

## Синтаксис

```python
range(stop)             # от 0 до stop-1
range(start, stop)      # от start до stop-1
range(start, stop, step) # с шагом step
```

## Примеры

```python
# Числа от 1 до 10
for i in range(1, 11):
    print(i)

# Чётные числа от 2 до 20
for i in range(2, 21, 2):
    print(i)

# Обратный отсчёт
for i in range(10, 0, -1):
    print(i)
print("Пуск!")
```

## f-строки

Для красивого вывода используй f-строки:

```python
for i in range(1, 11):
    print(f"{i} x 5 = {i * 5}")
```""",
                "theory_kk": "# range() толығырақ\n\n```python\nrange(stop)             # 0-ден stop-1-ге дейін\nrange(start, stop)      # start-тан stop-1-ге дейін\nrange(start, stop, step) # step қадаммен\n```",
                "challenge_title_pattern": "Таблица умножения",
            },
            {
                "title": "Практика: таблица умножения",
                "title_kk": "Тәжірибе: көбейту кестесі",
                "theory": """# Практика: таблица умножения

Напишем программу, которая выводит таблицу умножения для числа N.

```python
n = int(input())
for i in range(1, 11):
    print(f"{n} x {i} = {n * i}")
```

Результат для n = 7:
```
7 x 1 = 7
7 x 2 = 14
7 x 3 = 21
...
7 x 10 = 70
```

Реши задачу!""",
                "theory_kk": "# Тәжірибе: көбейту кестесі\n\nN саны үшін көбейту кестесін шығаратын бағдарлама жазамыз.\n\n```python\nn = int(input())\nfor i in range(1, 11):\n    print(f\"{n} x {i} = {n * i}\")\n```",
            },
            {
                "title": "Цикл while — повторяем пока",
                "title_kk": "while циклі — болғанша қайталау",
                "theory": """# Цикл while

`while` повторяет код, пока условие **истинно**:

```python
count = 0
while count < 5:
    print(count)
    count += 1
```

Результат: 0, 1, 2, 3, 4

## Отличие от for

- `for` — когда знаешь **сколько** раз повторять
- `while` — когда повторяешь **пока** условие верно

## Пример: степень двойки

Найти наименьшую степень 2, которая больше N:

```python
n = int(input())
power = 1
while power <= n:
    power *= 2
print(power)
```""",
                "theory_kk": "# while циклі\n\n`while` шарт **ақиқат** болғанша кодты қайталайды:\n\n```python\ncount = 0\nwhile count < 5:\n    print(count)\n    count += 1\n```",
                "challenge_title_pattern": "Степень двойки",
            },
            {
                "title": "break и continue",
                "title_kk": "break және continue",
                "theory": """# break и continue

## break — досрочный выход из цикла

```python
for i in range(100):
    if i == 5:
        break
    print(i)
# Выведет: 0, 1, 2, 3, 4
```

## continue — пропуск итерации

```python
for i in range(10):
    if i % 2 == 0:
        continue
    print(i)
# Выведет: 1, 3, 5, 7, 9
```

## Пример: поиск числа

```python
numbers = [3, 7, 1, 9, 4, 6]
target = 9

for n in numbers:
    if n == target:
        print(f"Найдено: {n}")
        break
else:
    print("Не найдено")
```""",
                "theory_kk": "# break және continue\n\n## break — циклден ерте шығу\n\n```python\nfor i in range(100):\n    if i == 5:\n        break\n    print(i)\n```\n\n## continue — итерацияны өткізу\n\n```python\nfor i in range(10):\n    if i % 2 == 0:\n        continue\n    print(i)\n```",
            },
            {
                "title": "Практика: угадай число",
                "title_kk": "Тәжірибе: санды тап",
                "theory": """# Практика: угадай число

Напишем игру «Угадай число»!

```python
import random

secret = random.randint(1, 100)
attempts = 0

while True:
    guess = int(input("Угадай число (1-100): "))
    attempts += 1

    if guess < secret:
        print("Больше!")
    elif guess > secret:
        print("Меньше!")
    else:
        print(f"Верно! Ты угадал за {attempts} попыток!")
        break
```

Это классический пример использования `while True` + `break`.

Реши задачу на факториал!""",
                "theory_kk": "# Тәжірибе: санды тап\n\n«Санды тап» ойынын жазамыз!\n\n```python\nimport random\nsecret = random.randint(1, 100)\nattempts = 0\nwhile True:\n    guess = int(input())\n    attempts += 1\n    if guess < secret:\n        print(\"Үлкен!\")\n    elif guess > secret:\n        print(\"Кіші!\")\n    else:\n        print(f\"Дұрыс! {attempts} әрекет\")\n        break\n```",
                "challenge_title_pattern": "Факториал",
            },
            {
                "title": "Списки — коллекция данных",
                "title_kk": "Тізімдер — деректер жинағы",
                "theory": """# Списки

**Список** (list) хранит несколько значений в одной переменной.

```python
fruits = ["яблоко", "банан", "киви"]
numbers = [1, 2, 3, 4, 5]
mixed = [1, "текст", True, 3.14]
```

## Индексы (с нуля!)

```python
fruits = ["яблоко", "банан", "киви"]
print(fruits[0])   # яблоко
print(fruits[1])   # банан
print(fruits[-1])  # киви (с конца)
```

## Длина списка

```python
print(len(fruits))  # 3
```

## Перебор списка

```python
for fruit in fruits:
    print(fruit)
```""",
                "theory_kk": "# Тізімдер\n\n**Тізім** (list) бір айнымалыда бірнеше мән сақтайды.\n\n```python\nfruits = [\"алма\", \"банан\", \"киви\"]\nnumbers = [1, 2, 3, 4, 5]\n```\n\n## Индекстер (нөлден!)\n\n```python\nprint(fruits[0])   # алма\nprint(fruits[-1])  # киви\n```",
                "challenge_title_pattern": "Сумма элементов списка",
            },
            {
                "title": "Методы списков: append, remove, sort",
                "title_kk": "Тізім әдістері: append, remove, sort",
                "theory": """# Методы списков

## Добавление элементов

```python
fruits = ["яблоко", "банан"]
fruits.append("киви")       # Добавить в конец
fruits.insert(0, "манго")   # Вставить по индексу
print(fruits)  # ["манго", "яблоко", "банан", "киви"]
```

## Удаление

```python
fruits.remove("банан")  # Удалить по значению
del fruits[0]           # Удалить по индексу
last = fruits.pop()     # Удалить и вернуть последний
```

## Сортировка

```python
numbers = [3, 1, 4, 1, 5, 9]
numbers.sort()          # [1, 1, 3, 4, 5, 9]
numbers.sort(reverse=True)  # [9, 5, 4, 3, 1, 1]
```

## Полезные функции

```python
print(sum(numbers))   # сумма
print(min(numbers))   # минимум
print(max(numbers))   # максимум
print(len(numbers))   # длина
```""",
                "theory_kk": "# Тізім әдістері\n\n## Элементтер қосу\n\n```python\nfruits = [\"алма\", \"банан\"]\nfruits.append(\"киви\")\nprint(fruits)  # [\"алма\", \"банан\", \"киви\"]\n```\n\n## Сұрыптау\n\n```python\nnumbers = [3, 1, 4, 1, 5, 9]\nnumbers.sort()  # [1, 1, 3, 4, 5, 9]\n```",
            },
            {
                "title": "Итоговый проект: список дел",
                "title_kk": "Қорытынды жоба: істер тізімі",
                "theory": """# Итоговый проект: список дел

Поздравляю! Ты изучил основы Python. Давай объединим всё в одном проекте.

## Задание

Напиши программу «Список дел» (To-Do List):
- Добавить задачу
- Показать все задачи
- Удалить задачу
- Выйти

```python
todos = []

while True:
    print("\\n1. Добавить задачу")
    print("2. Показать задачи")
    print("3. Удалить задачу")
    print("4. Выйти")

    choice = input("Выбери действие: ")

    if choice == "1":
        task = input("Введи задачу: ")
        todos.append(task)
        print("Добавлено!")
    elif choice == "2":
        if not todos:
            print("Список пуст")
        else:
            for i, task in enumerate(todos, 1):
                print(f"{i}. {task}")
    elif choice == "3":
        num = int(input("Номер задачи: "))
        if 1 <= num <= len(todos):
            removed = todos.pop(num - 1)
            print(f"Удалено: {removed}")
    elif choice == "4":
        print("Пока!")
        break
```

**Курс завершён!** Переходи к курсу «Продвинутый Python».""",
                "theory_kk": "# Қорытынды жоба: істер тізімі\n\nҚұттықтаймын! Python негіздерін үйрендіңіз.\n\n«Істер тізімі» бағдарламасын жазайық:\n- Тапсырма қосу\n- Барлық тапсырмаларды көрсету\n- Тапсырманы жою\n- Шығу",
            },
        ],
    },
]


def escape_sql(s: str) -> str:
    """Escape single quotes for SQL."""
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


def main():
    print("-- =========================================================")
    print("-- Seed: Coding Courses (Learning Paths)")
    print("-- =========================================================")
    print()
    print("BEGIN;")
    print()

    for course in COURSES:
        lessons = course.pop("lessons")
        total = len(lessons)

        print(f"-- Course: {course['title']}")
        print(f"INSERT INTO coding_courses (title, title_kk, description, description_kk, slug, grade_level, total_lessons, estimated_hours, sort_order, icon, is_active)")
        print(f"VALUES ({escape_sql(course['title'])}, {escape_sql(course['title_kk'])}, {escape_sql(course['description'])}, {escape_sql(course['description_kk'])}, {escape_sql(course['slug'])}, {course['grade_level']}, {total}, {course['estimated_hours']}, {course['sort_order']}, {escape_sql(course['icon'])}, TRUE);")
        print()

        for i, lesson in enumerate(lessons):
            challenge_ref = "NULL"
            pattern = lesson.get("challenge_title_pattern")
            if pattern:
                challenge_ref = f"(SELECT id FROM coding_challenges WHERE title LIKE {escape_sql('%' + pattern + '%')} LIMIT 1)"

            theory_kk = lesson.get("theory_kk")
            print(f"-- Lesson {i + 1}: {lesson['title']}")
            print(f"INSERT INTO coding_lessons (course_id, title, title_kk, sort_order, theory_content, theory_content_kk, challenge_id, is_active)")
            print(f"VALUES ((SELECT id FROM coding_courses WHERE slug = {escape_sql(course['slug'])}), {escape_sql(lesson['title'])}, {escape_sql(lesson['title_kk'])}, {i}, {escape_sql(lesson['theory'])}, {escape_sql(theory_kk)}, {challenge_ref}, TRUE);")
            print()

    print()
    print("-- Update alembic version")
    print("UPDATE alembic_version SET version_num = '066_coding_courses' WHERE version_num = '065_coding_challenges';")
    print()
    print("COMMIT;")


if __name__ == "__main__":
    main()
