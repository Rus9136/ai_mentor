"""
Seed script: insert initial coding topics and challenges.

Usage:
  docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -f -
  OR run via Python after applying migration 065.
"""
import json

# ============================================================================
# Topics
# ============================================================================
TOPICS = [
    {
        "title": "Переменные и ввод/вывод",
        "title_kk": "Айнымалылар және енгізу/шығару",
        "slug": "variables",
        "description": "Основы: print(), input(), переменные, арифметика",
        "description_kk": "Негіздер: print(), input(), айнымалылар, арифметика",
        "sort_order": 0,
        "icon": "Variable",
        "grade_level": 6,
    },
    {
        "title": "Условия и ветвление",
        "title_kk": "Шарттар және тармақталу",
        "slug": "conditions",
        "description": "if, elif, else — принятие решений в программе",
        "description_kk": "if, elif, else — бағдарламада шешім қабылдау",
        "sort_order": 1,
        "icon": "GitBranch",
        "grade_level": 7,
    },
    {
        "title": "Циклы",
        "title_kk": "Циклдер",
        "slug": "loops",
        "description": "for, while — повторение действий",
        "description_kk": "for, while — әрекеттерді қайталау",
        "sort_order": 2,
        "icon": "Repeat",
        "grade_level": 8,
    },
    {
        "title": "Строки",
        "title_kk": "Жолдар",
        "slug": "strings",
        "description": "Работа с текстом: срезы, методы строк",
        "description_kk": "Мәтінмен жұмыс: кесінділер, жол әдістері",
        "sort_order": 3,
        "icon": "Type",
        "grade_level": 8,
    },
    {
        "title": "Списки и массивы",
        "title_kk": "Тізімдер және массивтер",
        "slug": "lists",
        "description": "Коллекции данных: list, append, sort, поиск",
        "description_kk": "Деректер жинақтары: list, append, sort, іздеу",
        "sort_order": 4,
        "icon": "List",
        "grade_level": 9,
    },
    {
        "title": "Функции",
        "title_kk": "Функциялар",
        "slug": "functions",
        "description": "def, return, параметры, рекурсия",
        "description_kk": "def, return, параметрлер, рекурсия",
        "sort_order": 5,
        "icon": "Box",
        "grade_level": 8,
    },
    {
        "title": "ООП",
        "title_kk": "ООБ (Объектіге бағытталған бағдарламалау)",
        "slug": "oop",
        "description": "Классы, объекты, наследование",
        "description_kk": "Кластар, объектілер, мұрагерлік",
        "sort_order": 6,
        "icon": "Boxes",
        "grade_level": 9,
    },
]

# ============================================================================
# Challenges
# ============================================================================
# Each challenge: (topic_slug, sort_order, title, title_kk, description, description_kk,
#                  difficulty, points, starter_code, hints, hints_kk, test_cases)

CHALLENGES = [
    # ---- variables (topic 0) ----
    ("variables", 0, "Привет, мир!", "Сәлем, әлем!",
     "Напишите программу, которая выводит `Hello, World!`",
     "`Hello, World!` деп шығаратын бағдарлама жазыңыз",
     "easy", 10, '# Напишите ваш код здесь\n',
     ["Используйте функцию print()"], ["print() функциясын қолданыңыз"],
     [
         {"input": "", "expected_output": "Hello, World!", "is_hidden": False, "description": "Базовый тест"},
     ]),

    ("variables", 1, "Эхо — повтори ввод", "Жаңғырық — енгізуді қайтала",
     "Считайте одну строку и выведите её обратно.",
     "Бір жолды оқып, оны қайта шығарыңыз.",
     "easy", 10, '',
     ["input() считывает строку", "print() выводит"], ["input() жолды оқиды", "print() шығарады"],
     [
         {"input": "Hello", "expected_output": "Hello", "is_hidden": False, "description": "Простой ввод"},
         {"input": "Python", "expected_output": "Python", "is_hidden": False, "description": "Слово Python"},
         {"input": "Привет мир", "expected_output": "Привет мир", "is_hidden": True, "description": "С пробелом"},
     ]),

    ("variables", 2, "Сумма двух чисел", "Екі санның қосындысы",
     "Считайте два целых числа (каждое на отдельной строке) и выведите их сумму.",
     "Екі бүтін санды оқып (әрқайсысы жеке жолда), олардың қосындысын шығарыңыз.",
     "easy", 10, 'a = int(input())\nb = int(input())\n# Вычислите и выведите сумму\n',
     ["Используйте int() для преобразования строки в число", "print(a + b)"],
     ["Жолды санға айналдыру үшін int() қолданыңыз", "print(a + b)"],
     [
         {"input": "5\n3", "expected_output": "8", "is_hidden": False, "description": "5 + 3 = 8"},
         {"input": "0\n0", "expected_output": "0", "is_hidden": False, "description": "0 + 0 = 0"},
         {"input": "-2\n7", "expected_output": "5", "is_hidden": True, "description": "Отрицательное число"},
         {"input": "100\n200", "expected_output": "300", "is_hidden": True, "description": "Большие числа"},
     ]),

    ("variables", 3, "Площадь прямоугольника", "Тіктөртбұрыштың ауданы",
     "Считайте длину и ширину прямоугольника (целые числа) и выведите его площадь.",
     "Тіктөртбұрыштың ұзындығы мен енін оқып, ауданын шығарыңыз.",
     "easy", 10, '',
     ["Площадь = длина × ширина"], ["Аудан = ұзындық × ен"],
     [
         {"input": "5\n3", "expected_output": "15", "is_hidden": False, "description": "5 × 3 = 15"},
         {"input": "10\n7", "expected_output": "70", "is_hidden": False, "description": "10 × 7 = 70"},
         {"input": "1\n1", "expected_output": "1", "is_hidden": True, "description": "1 × 1"},
         {"input": "0\n5", "expected_output": "0", "is_hidden": True, "description": "Нулевая сторона"},
     ]),

    ("variables", 4, "Обмен значений", "Мәндерді ауыстыру",
     "Считайте два числа a и b, затем выведите сначала b, потом a (каждое на отдельной строке).",
     "Екі a және b сандарын оқып, алдымен b, содан кейін a шығарыңыз (әрқайсысы жеке жолда).",
     "easy", 10, '',
     ["Можно использовать a, b = b, a"], ["a, b = b, a қолдануға болады"],
     [
         {"input": "1\n2", "expected_output": "2\n1", "is_hidden": False, "description": "1,2 → 2,1"},
         {"input": "10\n20", "expected_output": "20\n10", "is_hidden": False, "description": "10,20 → 20,10"},
         {"input": "5\n5", "expected_output": "5\n5", "is_hidden": True, "description": "Одинаковые"},
     ]),

    ("variables", 5, "Последняя цифра числа", "Санның соңғы цифры",
     "Считайте целое число и выведите его последнюю цифру.",
     "Бүтін санды оқып, оның соңғы цифрын шығарыңыз.",
     "medium", 20, '',
     ["Используйте оператор % (остаток от деления)", "n % 10 даёт последнюю цифру"],
     ["% (бөлуден қалдық) операторын қолданыңыз", "n % 10 соңғы цифрды береді"],
     [
         {"input": "123", "expected_output": "3", "is_hidden": False, "description": "123 → 3"},
         {"input": "0", "expected_output": "0", "is_hidden": False, "description": "0 → 0"},
         {"input": "9870", "expected_output": "0", "is_hidden": True, "description": "9870 → 0"},
         {"input": "7", "expected_output": "7", "is_hidden": True, "description": "Одна цифра"},
     ]),

    ("variables", 6, "Часы и минуты", "Сағат және минут",
     "Дано количество минут. Выведите через пробел количество часов и оставшихся минут.\n\nПример: 150 → `2 30`",
     "Минут саны берілген. Сағат пен қалған минутты бос орын арқылы шығарыңыз.\n\nМысал: 150 → `2 30`",
     "medium", 20, '',
     ["Часы = минуты // 60", "Остаток = минуты % 60"],
     ["Сағат = минут // 60", "Қалдық = минут % 60"],
     [
         {"input": "150", "expected_output": "2 30", "is_hidden": False, "description": "150 мин"},
         {"input": "60", "expected_output": "1 0", "is_hidden": False, "description": "Ровно час"},
         {"input": "0", "expected_output": "0 0", "is_hidden": True, "description": "Ноль"},
         {"input": "59", "expected_output": "0 59", "is_hidden": True, "description": "Меньше часа"},
         {"input": "1440", "expected_output": "24 0", "is_hidden": True, "description": "Сутки"},
     ]),

    ("variables", 7, "Расстояние между точками", "Нүктелер арасындағы қашықтық",
     "Даны координаты двух точек: x1, y1, x2, y2 (каждое на отдельной строке). Выведите расстояние между ними, округлённое до 2 знаков после запятой.",
     "Екі нүктенің координаталары берілген: x1, y1, x2, y2. Олардың арасындағы қашықтықты 2 ондық белгіге дейін дөңгелектеп шығарыңыз.",
     "medium", 20, 'import math\n\nx1 = int(input())\ny1 = int(input())\nx2 = int(input())\ny2 = int(input())\n# Вычислите расстояние\n',
     ["Формула: sqrt((x2-x1)² + (y2-y1)²)", "Используйте round(value, 2)"],
     ["Формула: sqrt((x2-x1)² + (y2-y1)²)", "round(value, 2) қолданыңыз"],
     [
         {"input": "0\n0\n3\n4", "expected_output": "5.0", "is_hidden": False, "description": "(0,0)→(3,4)"},
         {"input": "1\n1\n1\n1", "expected_output": "0.0", "is_hidden": False, "description": "Одна точка"},
         {"input": "0\n0\n1\n1", "expected_output": "1.41", "is_hidden": True, "description": "√2"},
     ]),

    # ---- conditions (topic 1) ----
    ("conditions", 0, "Чётное или нечётное", "Жұп немесе тақ",
     "Считайте целое число и выведите `even` если оно чётное, `odd` если нечётное.",
     "Бүтін санды оқып, жұп болса `even`, тақ болса `odd` деп шығарыңыз.",
     "easy", 10, '',
     ["n % 2 == 0 → чётное"], ["n % 2 == 0 → жұп"],
     [
         {"input": "4", "expected_output": "even", "is_hidden": False, "description": "4 — чётное"},
         {"input": "7", "expected_output": "odd", "is_hidden": False, "description": "7 — нечётное"},
         {"input": "0", "expected_output": "even", "is_hidden": True, "description": "0 — чётное"},
         {"input": "-3", "expected_output": "odd", "is_hidden": True, "description": "Отрицательное"},
     ]),

    ("conditions", 1, "Максимум из трёх", "Үшеудің максимумы",
     "Считайте три целых числа и выведите наибольшее из них.",
     "Үш бүтін санды оқып, ең үлкенін шығарыңыз.",
     "easy", 10, '',
     ["Можно использовать max(a, b, c)", "Или вложенные if"],
     ["max(a, b, c) қолдануға болады", "Немесе кірістірілген if"],
     [
         {"input": "1\n2\n3", "expected_output": "3", "is_hidden": False, "description": "1,2,3 → 3"},
         {"input": "5\n5\n5", "expected_output": "5", "is_hidden": False, "description": "Все равны"},
         {"input": "-1\n-2\n-3", "expected_output": "-1", "is_hidden": True, "description": "Отрицательные"},
         {"input": "100\n1\n50", "expected_output": "100", "is_hidden": True, "description": "Макс в начале"},
     ]),

    ("conditions", 2, "Оценка по баллу", "Балл бойынша баға",
     "Считайте балл (0-100) и выведите оценку:\n- 90-100 → `A`\n- 70-89 → `B`\n- 50-69 → `C`\n- 0-49 → `F`",
     "Баллды (0-100) оқып, бағаны шығарыңыз:\n- 90-100 → `A`\n- 70-89 → `B`\n- 50-69 → `C`\n- 0-49 → `F`",
     "easy", 10, '',
     ["Используйте if/elif/else цепочку", "Начните с наибольшего порога"],
     ["if/elif/else тізбегін қолданыңыз", "Ең жоғарғы шектен бастаңыз"],
     [
         {"input": "95", "expected_output": "A", "is_hidden": False, "description": "95 → A"},
         {"input": "75", "expected_output": "B", "is_hidden": False, "description": "75 → B"},
         {"input": "50", "expected_output": "C", "is_hidden": False, "description": "50 → C"},
         {"input": "30", "expected_output": "F", "is_hidden": False, "description": "30 → F"},
         {"input": "100", "expected_output": "A", "is_hidden": True, "description": "100 → A"},
         {"input": "0", "expected_output": "F", "is_hidden": True, "description": "0 → F"},
     ]),

    ("conditions", 3, "Високосный год", "Кібісе жылы",
     "Считайте год и выведите `YES` если он високосный, `NO` иначе.\n\nПравило: год делится на 4, но не на 100, если только не делится на 400.",
     "Жылды оқып, кібісе болса `YES`, әйтпесе `NO` деп шығарыңыз.\n\nЕреже: жыл 4-ке бөлінеді, бірақ 100-ге бөлінбейді, 400-ге бөлінетін болмаса.",
     "medium", 20, '',
     ["(year % 4 == 0 and year % 100 != 0) or year % 400 == 0"],
     ["(year % 4 == 0 and year % 100 != 0) or year % 400 == 0"],
     [
         {"input": "2024", "expected_output": "YES", "is_hidden": False, "description": "2024 — високосный"},
         {"input": "2023", "expected_output": "NO", "is_hidden": False, "description": "2023 — нет"},
         {"input": "1900", "expected_output": "NO", "is_hidden": True, "description": "1900 — делится на 100"},
         {"input": "2000", "expected_output": "YES", "is_hidden": True, "description": "2000 — делится на 400"},
     ]),

    ("conditions", 4, "Треугольник существует?", "Үшбұрыш бар ма?",
     "Считайте три стороны треугольника и выведите `YES` если треугольник может существовать, `NO` иначе.",
     "Үшбұрыштың үш қабырғасын оқып, ол бола алатын болса `YES`, әйтпесе `NO` шығарыңыз.",
     "medium", 20, '',
     ["Сумма любых двух сторон должна быть строго больше третьей"],
     ["Кез келген екі қабырғаның қосындысы үшіншісінен қатаң үлкен болуы керек"],
     [
         {"input": "3\n4\n5", "expected_output": "YES", "is_hidden": False, "description": "3,4,5"},
         {"input": "1\n2\n3", "expected_output": "NO", "is_hidden": False, "description": "1+2=3, не строго"},
         {"input": "5\n5\n5", "expected_output": "YES", "is_hidden": True, "description": "Равносторонний"},
         {"input": "1\n1\n10", "expected_output": "NO", "is_hidden": True, "description": "Невозможный"},
     ]),

    ("conditions", 5, "Калькулятор", "Калькулятор",
     "Считайте два числа и операцию (`+`, `-`, `*`, `/`). Выведите результат.\nПри делении на 0 выведите `Error`.\nРезультат — целое число (используйте `//` для деления).",
     "Екі санды және амалды (`+`, `-`, `*`, `/`) оқыңыз. Нәтижесін шығарыңыз.\n0-ге бөлгенде `Error` шығарыңыз.\nНәтиже — бүтін сан (бөлу үшін `//` қолданыңыз).",
     "medium", 20, '',
     ["Используйте if/elif для выбора операции", "Проверяйте деление на ноль перед //"],
     ["Амалды таңдау үшін if/elif қолданыңыз", "// алдында нөлге бөлуді тексеріңіз"],
     [
         {"input": "10\n3\n+", "expected_output": "13", "is_hidden": False, "description": "10+3=13"},
         {"input": "10\n3\n-", "expected_output": "7", "is_hidden": False, "description": "10-3=7"},
         {"input": "10\n3\n*", "expected_output": "30", "is_hidden": False, "description": "10*3=30"},
         {"input": "10\n3\n/", "expected_output": "3", "is_hidden": False, "description": "10//3=3"},
         {"input": "10\n0\n/", "expected_output": "Error", "is_hidden": True, "description": "Деление на 0"},
     ]),

    ("conditions", 6, "Сортировка трёх чисел", "Үш санды сұрыптау",
     "Считайте три числа и выведите их в порядке возрастания через пробел.",
     "Үш санды оқып, оларды өсу ретімен бос орын арқылы шығарыңыз.",
     "medium", 20, '',
     ["Можно поместить в список и sorted()", "Или сравнить попарно с if"],
     ["Тізімге салып sorted() қолдануға болады", "Немесе if арқылы жұптап салыстырыңыз"],
     [
         {"input": "3\n1\n2", "expected_output": "1 2 3", "is_hidden": False, "description": "3,1,2"},
         {"input": "5\n5\n5", "expected_output": "5 5 5", "is_hidden": False, "description": "Все равны"},
         {"input": "-1\n0\n1", "expected_output": "-1 0 1", "is_hidden": True, "description": "С отрицательным"},
     ]),

    ("conditions", 7, "Квадратное уравнение", "Квадрат теңдеу",
     "Считайте коэффициенты a, b, c квадратного уравнения ax²+bx+c=0.\nЕсли D > 0 — два корня (через пробел, меньший первый, округлить до 2 знаков).\nЕсли D = 0 — один корень.\nЕсли D < 0 — выведите `No roots`.",
     "ax²+bx+c=0 квадрат теңдеуінің a, b, c коэффициенттерін оқыңыз.\nD > 0 болса — екі түбір (бос орын арқылы, кішісі бірінші, 2 белгіге дөңгелектеу).\nD = 0 болса — бір түбір.\nD < 0 болса — `No roots` шығарыңыз.",
     "hard", 30, 'import math\n\na = int(input())\nb = int(input())\nc = int(input())\n',
     ["D = b² - 4ac", "x = (-b ± √D) / (2a)"],
     ["D = b² - 4ac", "x = (-b ± √D) / (2a)"],
     [
         {"input": "1\n-3\n2", "expected_output": "1.0 2.0", "is_hidden": False, "description": "x²-3x+2=0"},
         {"input": "1\n-2\n1", "expected_output": "1.0", "is_hidden": False, "description": "x²-2x+1=0, D=0"},
         {"input": "1\n0\n1", "expected_output": "No roots", "is_hidden": False, "description": "x²+1=0, D<0"},
         {"input": "1\n0\n-4", "expected_output": "-2.0 2.0", "is_hidden": True, "description": "x²-4=0"},
     ]),

    # ---- loops (topic 2) ----
    ("loops", 0, "Сумма от 1 до N", "1-ден N-ге дейінгі қосынды",
     "Считайте число N и выведите сумму чисел от 1 до N.",
     "N санын оқып, 1-ден N-ге дейінгі сандардың қосындысын шығарыңыз.",
     "easy", 10, '',
     ["Используйте for i in range(1, n+1)", "Или формулу n*(n+1)//2"],
     ["for i in range(1, n+1) қолданыңыз", "Немесе n*(n+1)//2 формуласын"],
     [
         {"input": "5", "expected_output": "15", "is_hidden": False, "description": "1+2+3+4+5=15"},
         {"input": "1", "expected_output": "1", "is_hidden": False, "description": "N=1"},
         {"input": "100", "expected_output": "5050", "is_hidden": True, "description": "N=100"},
     ]),

    ("loops", 1, "Таблица умножения", "Көбейту кестесі",
     "Считайте число N и выведите таблицу умножения для N (от 1 до 10).\nФормат: `N * i = result` на каждой строке.",
     "N санын оқып, N үшін көбейту кестесін шығарыңыз (1-ден 10-ға дейін).\nФормат: әр жолда `N * i = result`.",
     "easy", 10, '',
     ["for i in range(1, 11)", "Используйте f-строку: f\"{n} * {i} = {n*i}\""],
     ["for i in range(1, 11)", "f-жолды қолданыңыз: f\"{n} * {i} = {n*i}\""],
     [
         {"input": "5", "expected_output": "5 * 1 = 5\n5 * 2 = 10\n5 * 3 = 15\n5 * 4 = 20\n5 * 5 = 25\n5 * 6 = 30\n5 * 7 = 35\n5 * 8 = 40\n5 * 9 = 45\n5 * 10 = 50", "is_hidden": False, "description": "Таблица для 5"},
     ]),

    ("loops", 2, "Факториал", "Факториал",
     "Считайте число N (0 ≤ N ≤ 20) и выведите N! (факториал).",
     "N санын оқып (0 ≤ N ≤ 20), N! (факториал) шығарыңыз.",
     "easy", 10, '',
     ["0! = 1", "Умножайте в цикле: result *= i"],
     ["0! = 1", "Циклде көбейтіңіз: result *= i"],
     [
         {"input": "5", "expected_output": "120", "is_hidden": False, "description": "5!=120"},
         {"input": "0", "expected_output": "1", "is_hidden": False, "description": "0!=1"},
         {"input": "1", "expected_output": "1", "is_hidden": True, "description": "1!=1"},
         {"input": "10", "expected_output": "3628800", "is_hidden": True, "description": "10!"},
     ]),

    ("loops", 3, "Степень двойки", "Екінің дәрежесі",
     "Считайте число N и выведите `YES` если N является степенью двойки, `NO` иначе.",
     "N санын оқып, 2-нің дәрежесі болса `YES`, әйтпесе `NO` шығарыңыз.",
     "easy", 10, '',
     ["Делите N на 2 пока оно чётное", "Если в конце получилось 1 — степень двойки"],
     ["N-ді 2-ге бөліңіз, жұп болған кезде", "Соңында 1 болса — 2-нің дәрежесі"],
     [
         {"input": "8", "expected_output": "YES", "is_hidden": False, "description": "8=2³"},
         {"input": "6", "expected_output": "NO", "is_hidden": False, "description": "6 — нет"},
         {"input": "1", "expected_output": "YES", "is_hidden": True, "description": "1=2⁰"},
         {"input": "1024", "expected_output": "YES", "is_hidden": True, "description": "1024=2¹⁰"},
     ]),

    ("loops", 4, "Количество цифр", "Цифрлар саны",
     "Считайте целое положительное число и выведите количество цифр в нём.",
     "Бүтін оң санды оқып, ондағы цифрлар санын шығарыңыз.",
     "medium", 20, '',
     ["Делите число на 10 пока оно > 0, считайте шаги"],
     ["Санды 10-ға бөліңіз > 0 болғанша, қадамдарды санаңыз"],
     [
         {"input": "12345", "expected_output": "5", "is_hidden": False, "description": "12345 — 5 цифр"},
         {"input": "7", "expected_output": "1", "is_hidden": False, "description": "Одна цифра"},
         {"input": "100", "expected_output": "3", "is_hidden": True, "description": "100"},
         {"input": "1000000", "expected_output": "7", "is_hidden": True, "description": "Миллион"},
     ]),

    ("loops", 5, "Простое ли число?", "Жай сан ба?",
     "Считайте число N (N ≥ 1) и выведите `YES` если оно простое, `NO` иначе.",
     "N санын оқып (N ≥ 1), жай болса `YES`, әйтпесе `NO` шығарыңыз.",
     "medium", 20, '',
     ["Простое число делится только на 1 и само себя", "Проверяйте делители от 2 до √N"],
     ["Жай сан тек 1-ге және өзіне бөлінеді", "2-ден √N-ге дейін бөлгіштерді тексеріңіз"],
     [
         {"input": "7", "expected_output": "YES", "is_hidden": False, "description": "7 — простое"},
         {"input": "4", "expected_output": "NO", "is_hidden": False, "description": "4=2×2"},
         {"input": "1", "expected_output": "NO", "is_hidden": True, "description": "1 — не простое"},
         {"input": "2", "expected_output": "YES", "is_hidden": True, "description": "2 — простое"},
         {"input": "97", "expected_output": "YES", "is_hidden": True, "description": "97 — простое"},
     ]),

    ("loops", 6, "Числа Фибоначчи", "Фибоначчи сандары",
     "Считайте число N и выведите первые N чисел Фибоначчи через пробел.\nПоследовательность: 1, 1, 2, 3, 5, 8, ...",
     "N санын оқып, алғашқы N Фибоначчи сандарын бос орын арқылы шығарыңыз.\nТізбек: 1, 1, 2, 3, 5, 8, ...",
     "medium", 20, '',
     ["Два предыдущих числа дают следующее", "a, b = b, a + b"],
     ["Алдыңғы екі сан келесісін береді", "a, b = b, a + b"],
     [
         {"input": "5", "expected_output": "1 1 2 3 5", "is_hidden": False, "description": "5 чисел"},
         {"input": "1", "expected_output": "1", "is_hidden": False, "description": "Одно число"},
         {"input": "8", "expected_output": "1 1 2 3 5 8 13 21", "is_hidden": True, "description": "8 чисел"},
     ]),

    ("loops", 7, "Пирамида из звёздочек", "Жұлдызшалардан пирамида",
     "Считайте число N и выведите пирамиду из `*` высотой N строк.\nСтрока i содержит i звёздочек.\n\nПример для N=3:\n```\n*\n**\n***\n```",
     "N санын оқып, биіктігі N жол болатын `*` пирамидасын шығарыңыз.\ni-жолда i жұлдызша болады.",
     "medium", 20, '',
     ["print('*' * i) в цикле"], ["print('*' * i) циклде"],
     [
         {"input": "3", "expected_output": "*\n**\n***", "is_hidden": False, "description": "N=3"},
         {"input": "1", "expected_output": "*", "is_hidden": False, "description": "N=1"},
         {"input": "5", "expected_output": "*\n**\n***\n****\n*****", "is_hidden": True, "description": "N=5"},
     ]),

    # ---- strings (topic 3) ----
    ("strings", 0, "Длина без пробелов", "Бос орынсыз ұзындық",
     "Считайте строку и выведите количество символов без пробелов.",
     "Жолды оқып, бос орынсыз таңбалар санын шығарыңыз.",
     "easy", 10, '',
     ["s.replace(' ', '') убирает пробелы", "len() считает символы"],
     ["s.replace(' ', '') бос орындарды алады", "len() таңбаларды санайды"],
     [
         {"input": "hello world", "expected_output": "10", "is_hidden": False, "description": "hello world"},
         {"input": "abc", "expected_output": "3", "is_hidden": False, "description": "Без пробелов"},
         {"input": "   ", "expected_output": "0", "is_hidden": True, "description": "Только пробелы"},
     ]),

    ("strings", 1, "Перевернуть строку", "Жолды аудару",
     "Считайте строку и выведите её в обратном порядке.",
     "Жолды оқып, оны кері ретпен шығарыңыз.",
     "easy", 10, '',
     ["Используйте срез [::-1]"], ["[::-1] кесіндісін қолданыңыз"],
     [
         {"input": "hello", "expected_output": "olleh", "is_hidden": False, "description": "hello"},
         {"input": "abc", "expected_output": "cba", "is_hidden": False, "description": "abc"},
         {"input": "a", "expected_output": "a", "is_hidden": True, "description": "Один символ"},
     ]),

    ("strings", 2, "Палиндром?", "Палиндром ба?",
     "Считайте строку и выведите `YES` если она палиндром (читается одинаково слева и справа), `NO` иначе. Регистр не учитывать.",
     "Жолды оқып, палиндром болса (солдан және оңнан бірдей оқылса) `YES`, әйтпесе `NO` шығарыңыз. Регистрді ескермеңіз.",
     "medium", 20, '',
     ["s.lower() для приведения к нижнему регистру", "Сравните s с s[::-1]"],
     ["s.lower() кіші регистрге келтіру үшін", "s пен s[::-1] салыстырыңыз"],
     [
         {"input": "level", "expected_output": "YES", "is_hidden": False, "description": "level"},
         {"input": "hello", "expected_output": "NO", "is_hidden": False, "description": "hello"},
         {"input": "Racecar", "expected_output": "YES", "is_hidden": True, "description": "С заглавной"},
     ]),

    ("strings", 3, "Подсчёт гласных", "Дауысты дыбыстарды санау",
     "Считайте строку и выведите количество гласных букв (a, e, i, o, u). Регистр не учитывать.",
     "Жолды оқып, дауысты дыбыстар санын (a, e, i, o, u) шығарыңыз. Регистрді ескермеңіз.",
     "medium", 20, '',
     ["Переберите символы: for ch in s.lower()"],
     ["Таңбаларды аралаңыз: for ch in s.lower()"],
     [
         {"input": "Hello World", "expected_output": "3", "is_hidden": False, "description": "e,o,o"},
         {"input": "xyz", "expected_output": "0", "is_hidden": False, "description": "Нет гласных"},
         {"input": "AEIOU", "expected_output": "5", "is_hidden": True, "description": "Все гласные"},
     ]),

    ("strings", 4, "Шифр Цезаря", "Цезарь шифры",
     "Считайте строку и число сдвига N. Сдвиньте каждую букву на N позиций вперёд (только латинские a-z). Остальные символы не трогать. Строка в нижнем регистре.",
     "Жолды және N ығысу санын оқыңыз. Әр әріпті N позицияға алға жылжытыңыз (тек латын a-z). Басқа таңбаларды өзгертпеңіз. Жол кіші регистрде.",
     "hard", 30, '',
     ["ord('a') = 97, chr(97) = 'a'", "Новая позиция: (ord(ch) - 97 + n) % 26 + 97"],
     ["ord('a') = 97, chr(97) = 'a'", "Жаңа позиция: (ord(ch) - 97 + n) % 26 + 97"],
     [
         {"input": "abc\n1", "expected_output": "bcd", "is_hidden": False, "description": "abc сдвиг 1"},
         {"input": "xyz\n3", "expected_output": "abc", "is_hidden": False, "description": "xyz сдвиг 3 → abc"},
         {"input": "hello world\n5", "expected_output": "mjqqt btwqi", "is_hidden": True, "description": "С пробелом"},
     ]),

    ("strings", 5, "Самое длинное слово", "Ең ұзын сөз",
     "Считайте строку из нескольких слов (разделённых пробелами). Выведите самое длинное слово. Если несколько одинаковой длины — первое из них.",
     "Бірнеше сөзден тұратын жолды (бос орынмен бөлінген) оқыңыз. Ең ұзын сөзді шығарыңыз. Бірнеше бірдей ұзындықта болса — біріншісін.",
     "medium", 20, '',
     ["split() разбивает строку на слова", "max(words, key=len)"],
     ["split() жолды сөздерге бөледі", "max(words, key=len)"],
     [
         {"input": "hello world python", "expected_output": "python", "is_hidden": False, "description": "python — 6"},
         {"input": "a bb ccc", "expected_output": "ccc", "is_hidden": False, "description": "ccc — 3"},
         {"input": "cat dog", "expected_output": "cat", "is_hidden": True, "description": "Одинаковая длина"},
     ]),

    # ---- lists (topic 4) ----
    ("lists", 0, "Сумма элементов", "Элементтер қосындысы",
     "Считайте N, затем N целых чисел (каждое на отдельной строке). Выведите их сумму.",
     "N-ді, содан кейін N бүтін санды оқыңыз. Олардың қосындысын шығарыңыз.",
     "easy", 10, '',
     ["Считайте числа в список через цикл", "sum(lst) вычисляет сумму"],
     ["Сандарды тізімге цикл арқылы оқыңыз", "sum(lst) қосындыны есептейді"],
     [
         {"input": "3\n1\n2\n3", "expected_output": "6", "is_hidden": False, "description": "1+2+3=6"},
         {"input": "1\n42", "expected_output": "42", "is_hidden": False, "description": "Один элемент"},
         {"input": "4\n-1\n-2\n3\n4", "expected_output": "4", "is_hidden": True, "description": "С отрицательными"},
     ]),

    ("lists", 1, "Минимум и максимум", "Минимум және максимум",
     "Считайте N, затем N чисел. Выведите минимум и максимум через пробел.",
     "N-ді, содан кейін N санды оқыңыз. Минимум мен максимумды бос орын арқылы шығарыңыз.",
     "easy", 10, '',
     ["min(lst), max(lst)"], ["min(lst), max(lst)"],
     [
         {"input": "5\n3\n1\n4\n1\n5", "expected_output": "1 5", "is_hidden": False, "description": "1..5"},
         {"input": "1\n7", "expected_output": "7 7", "is_hidden": True, "description": "Один элемент"},
     ]),

    ("lists", 2, "Чётные элементы", "Жұп элементтер",
     "Считайте N, затем N чисел. Выведите только чётные числа через пробел. Если чётных нет — выведите `None`.",
     "N-ді, содан кейін N санды оқыңыз. Тек жұп сандарды бос орын арқылы шығарыңыз. Жұптары жоқ болса — `None`.",
     "easy", 10, '',
     ["Фильтрация: [x for x in lst if x % 2 == 0]"],
     ["Сүзу: [x for x in lst if x % 2 == 0]"],
     [
         {"input": "5\n1\n2\n3\n4\n5", "expected_output": "2 4", "is_hidden": False, "description": "2 и 4"},
         {"input": "3\n1\n3\n5", "expected_output": "None", "is_hidden": False, "description": "Нет чётных"},
         {"input": "3\n0\n2\n4", "expected_output": "0 2 4", "is_hidden": True, "description": "Все чётные"},
     ]),

    ("lists", 3, "Перевернуть список", "Тізімді аудару",
     "Считайте N, затем N чисел. Выведите их в обратном порядке через пробел.",
     "N-ді, содан кейін N санды оқыңыз. Оларды кері ретпен бос орын арқылы шығарыңыз.",
     "easy", 10, '',
     ["lst[::-1] или lst.reverse()"], ["lst[::-1] немесе lst.reverse()"],
     [
         {"input": "4\n1\n2\n3\n4", "expected_output": "4 3 2 1", "is_hidden": False, "description": "1234 → 4321"},
         {"input": "1\n5", "expected_output": "5", "is_hidden": True, "description": "Один элемент"},
     ]),

    ("lists", 4, "Уникальные элементы", "Бірегей элементтер",
     "Считайте N, затем N чисел. Выведите уникальные элементы в порядке первого появления через пробел.",
     "N-ді, содан кейін N санды оқыңыз. Бірегей элементтерді алғашқы кездесу ретімен бос орын арқылы шығарыңыз.",
     "medium", 20, '',
     ["Используйте set для отслеживания уже встреченных"],
     ["Кездескендерді қадағалау үшін set қолданыңыз"],
     [
         {"input": "6\n1\n2\n2\n3\n1\n4", "expected_output": "1 2 3 4", "is_hidden": False, "description": "С дубликатами"},
         {"input": "3\n5\n5\n5", "expected_output": "5", "is_hidden": True, "description": "Все одинаковые"},
     ]),

    ("lists", 5, "Сортировка пузырьком", "Көпіршікті сұрыптау",
     "Считайте N, затем N чисел. Отсортируйте их алгоритмом пузырьковой сортировки и выведите через пробел.\n\n*Не используйте sort() или sorted()*.",
     "N-ді, содан кейін N санды оқыңыз. Оларды көпіршікті сұрыптау алгоритмімен сұрыптап, бос орын арқылы шығарыңыз.\n\n*sort() немесе sorted() қолданбаңыз*.",
     "medium", 20, '',
     ["Два вложенных цикла", "Если lst[j] > lst[j+1], меняем местами"],
     ["Екі кірістірілген цикл", "lst[j] > lst[j+1] болса, орындарын ауыстырамыз"],
     [
         {"input": "5\n5\n3\n1\n4\n2", "expected_output": "1 2 3 4 5", "is_hidden": False, "description": "5 элементов"},
         {"input": "3\n1\n2\n3", "expected_output": "1 2 3", "is_hidden": True, "description": "Уже отсортирован"},
         {"input": "4\n4\n3\n2\n1", "expected_output": "1 2 3 4", "is_hidden": True, "description": "Обратный порядок"},
     ]),

    ("lists", 6, "Бинарный поиск", "Екілік іздеу",
     "Считайте N, затем N отсортированных чисел, затем число X для поиска.\nВыведите индекс X (0-based) или `-1` если не найдено.\n\n*Используйте бинарный поиск, не линейный.*",
     "N-ді, содан кейін N сұрыпталған санды, содан кейін іздеу үшін X санын оқыңыз.\nX-тің индексін (0-ден) немесе табылмаса `-1` шығарыңыз.\n\n*Сызықтық емес, екілік іздеуді қолданыңыз.*",
     "hard", 30, '',
     ["left = 0, right = n - 1", "mid = (left + right) // 2"],
     ["left = 0, right = n - 1", "mid = (left + right) // 2"],
     [
         {"input": "5\n1\n3\n5\n7\n9\n5", "expected_output": "2", "is_hidden": False, "description": "5 at index 2"},
         {"input": "5\n1\n3\n5\n7\n9\n4", "expected_output": "-1", "is_hidden": False, "description": "4 не найден"},
         {"input": "1\n42\n42", "expected_output": "0", "is_hidden": True, "description": "Один элемент"},
     ]),

    ("lists", 7, "Сумма строк матрицы", "Матрица жолдарының қосындысы",
     "Считайте размеры матрицы N и M, затем N строк по M чисел (через пробел).\nВыведите сумму каждой строки на отдельной строке.",
     "N және M матрица өлшемдерін, содан кейін N жолда M санды оқыңыз (бос орын арқылы).\nӘр жолдың қосындысын жеке жолда шығарыңыз.",
     "hard", 30, '',
     ["Два вложенных цикла или list comprehension"],
     ["Екі кірістірілген цикл немесе list comprehension"],
     [
         {"input": "2\n3\n1 2 3\n4 5 6", "expected_output": "6\n15", "is_hidden": False, "description": "2×3 матрица"},
         {"input": "1\n1\n42", "expected_output": "42", "is_hidden": True, "description": "1×1"},
     ]),

    # ---- functions (topic 5) ----
    ("functions", 0, "Функция приветствия", "Сәлемдесу функциясы",
     "Напишите функцию `greet(name)`, которая возвращает строку `Hello, {name}!`.\nСчитайте имя и выведите результат вызова функции.",
     "`greet(name)` функциясын жазыңыз, ол `Hello, {name}!` жолын қайтарады.\nАтты оқып, функция нәтижесін шығарыңыз.",
     "easy", 10, 'def greet(name):\n    # Ваш код здесь\n    pass\n\nname = input()\nprint(greet(name))\n',
     ["return f\"Hello, {name}!\""], ["return f\"Hello, {name}!\""],
     [
         {"input": "Alice", "expected_output": "Hello, Alice!", "is_hidden": False, "description": "Alice"},
         {"input": "World", "expected_output": "Hello, World!", "is_hidden": True, "description": "World"},
     ]),

    ("functions", 1, "Функция is_even", "is_even функциясы",
     "Напишите функцию `is_even(n)`, которая возвращает `True` если число чётное, `False` иначе.\nСчитайте число и выведите результат.",
     "`is_even(n)` функциясын жазыңыз, сан жұп болса `True`, әйтпесе `False` қайтарады.\nСанды оқып, нәтижесін шығарыңыз.",
     "easy", 10, 'def is_even(n):\n    # Ваш код здесь\n    pass\n\nn = int(input())\nprint(is_even(n))\n',
     ["return n % 2 == 0"], ["return n % 2 == 0"],
     [
         {"input": "4", "expected_output": "True", "is_hidden": False, "description": "4 — True"},
         {"input": "7", "expected_output": "False", "is_hidden": False, "description": "7 — False"},
         {"input": "0", "expected_output": "True", "is_hidden": True, "description": "0 — True"},
     ]),

    ("functions", 2, "Рекурсивный факториал", "Рекурсивті факториал",
     "Напишите рекурсивную функцию `factorial(n)`, которая возвращает n!.\nСчитайте число и выведите результат.",
     "n! қайтаратын `factorial(n)` рекурсивті функциясын жазыңыз.\nСанды оқып, нәтижесін шығарыңыз.",
     "medium", 20, 'def factorial(n):\n    # Ваш код здесь\n    pass\n\nn = int(input())\nprint(factorial(n))\n',
     ["Базовый случай: если n <= 1, вернуть 1", "Рекурсия: n * factorial(n - 1)"],
     ["Базалық жағдай: n <= 1 болса, 1 қайтару", "Рекурсия: n * factorial(n - 1)"],
     [
         {"input": "5", "expected_output": "120", "is_hidden": False, "description": "5!=120"},
         {"input": "0", "expected_output": "1", "is_hidden": False, "description": "0!=1"},
         {"input": "10", "expected_output": "3628800", "is_hidden": True, "description": "10!"},
     ]),

    ("functions", 3, "Функция is_prime", "is_prime функциясы",
     "Напишите функцию `is_prime(n)`, которая возвращает `True` если n — простое число, `False` иначе.\nСчитайте число и выведите результат.",
     "n жай сан болса `True`, әйтпесе `False` қайтаратын `is_prime(n)` функциясын жазыңыз.\nСанды оқып, нәтижесін шығарыңыз.",
     "medium", 20, 'def is_prime(n):\n    # Ваш код здесь\n    pass\n\nn = int(input())\nprint(is_prime(n))\n',
     ["Проверяйте делители от 2 до √n", "Используйте цикл с break"],
     ["2-ден √n-ге дейін бөлгіштерді тексеріңіз", "break бар циклді қолданыңыз"],
     [
         {"input": "7", "expected_output": "True", "is_hidden": False, "description": "7 — простое"},
         {"input": "4", "expected_output": "False", "is_hidden": False, "description": "4 — нет"},
         {"input": "1", "expected_output": "False", "is_hidden": True, "description": "1 — нет"},
         {"input": "2", "expected_output": "True", "is_hidden": True, "description": "2 — да"},
     ]),

    ("functions", 4, "НОД (Евклид)", "ЕҮОБ (Евклид)",
     "Напишите функцию `gcd(a, b)`, которая возвращает наибольший общий делитель двух чисел (алгоритм Евклида).\nСчитайте два числа и выведите результат.",
     "Екі санның ең үлкен ортақ бөлгішін (Евклид алгоритмі) қайтаратын `gcd(a, b)` функциясын жазыңыз.\nЕкі санды оқып, нәтижесін шығарыңыз.",
     "medium", 20, 'def gcd(a, b):\n    # Ваш код здесь\n    pass\n\na = int(input())\nb = int(input())\nprint(gcd(a, b))\n',
     ["Пока b != 0: a, b = b, a % b", "Вернуть a"],
     ["b != 0 болғанша: a, b = b, a % b", "a қайтару"],
     [
         {"input": "12\n8", "expected_output": "4", "is_hidden": False, "description": "НОД(12,8)=4"},
         {"input": "7\n3", "expected_output": "1", "is_hidden": False, "description": "Взаимно простые"},
         {"input": "100\n100", "expected_output": "100", "is_hidden": True, "description": "Равные"},
     ]),

    ("functions", 5, "Декоратор-таймер", "Декоратор-таймер",
     "Напишите функцию `repeat(n)`, которая принимает число n и возвращает функцию-декоратор. Декоратор должен вызвать оригинальную функцию n раз.\n\nСчитайте число n, создайте декорированную функцию hello() которая печатает `Hello!`, и вызовите её.",
     "`repeat(n)` функциясын жазыңыз, ол n санын қабылдап, декоратор-функцияны қайтарады. Декоратор түпнұсқа функцияны n рет шақыруы керек.\n\nn санын оқып, `Hello!` деп шығаратын hello() декорацияланған функциясын жасап, оны шақырыңыз.",
     "hard", 30, 'def repeat(n):\n    # Ваш код здесь: вернуть декоратор\n    pass\n\nn = int(input())\n\n@repeat(n)\ndef hello():\n    print("Hello!")\n\nhello()\n',
     ["Декоратор — это функция, возвращающая функцию", "def decorator(func): def wrapper(): for _ in range(n): func()"],
     ["Декоратор — функция қайтаратын функция", "def decorator(func): def wrapper(): for _ in range(n): func()"],
     [
         {"input": "3", "expected_output": "Hello!\nHello!\nHello!", "is_hidden": False, "description": "3 раза"},
         {"input": "1", "expected_output": "Hello!", "is_hidden": True, "description": "1 раз"},
     ]),

    # ---- oop (topic 6) ----
    ("oop", 0, "Класс Rectangle", "Rectangle класы",
     "Создайте класс `Rectangle` с атрибутами `width` и `height` (через `__init__`). Добавьте метод `area()`, возвращающий площадь.\n\nСчитайте ширину и высоту, создайте прямоугольник и выведите площадь.",
     "`Rectangle` класын `width` және `height` атрибуттарымен жасаңыз (`__init__` арқылы). `area()` әдісін қосыңыз.\n\nЕні мен биіктігін оқып, тіктөртбұрыш жасап, ауданын шығарыңыз.",
     "easy", 10, 'class Rectangle:\n    # Ваш код здесь\n    pass\n\nw = int(input())\nh = int(input())\nrect = Rectangle(w, h)\nprint(rect.area())\n',
     ["def __init__(self, width, height)", "def area(self): return self.width * self.height"],
     ["def __init__(self, width, height)", "def area(self): return self.width * self.height"],
     [
         {"input": "5\n3", "expected_output": "15", "is_hidden": False, "description": "5×3=15"},
         {"input": "10\n10", "expected_output": "100", "is_hidden": True, "description": "Квадрат"},
     ]),

    ("oop", 1, "Класс Student", "Student класы",
     "Создайте класс `Student` с атрибутами `name` и `grades` (список). Добавьте:\n- `add_grade(grade)` — добавить оценку\n- `average()` — средний балл (округлить до 1 знака)\n\nСчитайте имя, количество оценок N, затем N оценок. Выведите `{name}: {average}`.",
     "`Student` класын `name` және `grades` (тізім) атрибуттарымен жасаңыз:\n- `add_grade(grade)` — баға қосу\n- `average()` — орташа балл (1 белгіге дөңгелектеу)\n\nАтты, N бағалар санын, содан кейін N бағаны оқыңыз. `{name}: {average}` шығарыңыз.",
     "easy", 10, 'class Student:\n    # Ваш код здесь\n    pass\n\nname = input()\nn = int(input())\ns = Student(name)\nfor _ in range(n):\n    s.add_grade(int(input()))\nprint(f"{s.name}: {s.average()}")\n',
     ["self.grades = [] в __init__", "average = round(sum(self.grades) / len(self.grades), 1)"],
     ["__init__ ішінде self.grades = []", "average = round(sum(self.grades) / len(self.grades), 1)"],
     [
         {"input": "Alice\n3\n80\n90\n100", "expected_output": "Alice: 90.0", "is_hidden": False, "description": "3 оценки"},
         {"input": "Bob\n1\n75", "expected_output": "Bob: 75.0", "is_hidden": True, "description": "Одна оценка"},
     ]),

    ("oop", 2, "Класс BankAccount", "BankAccount класы",
     "Создайте класс `BankAccount` с атрибутом `balance` (начальный = 0). Методы:\n- `deposit(amount)` — пополнить\n- `withdraw(amount)` — снять (если достаточно средств, иначе вывести `Insufficient funds`)\n- `get_balance()` — вернуть баланс\n\nСчитайте количество операций, затем операции в формате `D amount` или `W amount`. В конце выведите баланс.",
     "`BankAccount` класын `balance` атрибутымен жасаңыз (бастапқы = 0). Әдістер:\n- `deposit(amount)` — толтыру\n- `withdraw(amount)` — алу (жеткілікті болса, әйтпесе `Insufficient funds`)\n- `get_balance()` — балансты қайтару\n\nОпераций санын, содан кейін `D amount` немесе `W amount` форматындағы амалдарды оқыңыз. Соңында балансты шығарыңыз.",
     "medium", 20, '',
     ["if self.balance >= amount для withdraw"],
     ["withdraw үшін if self.balance >= amount"],
     [
         {"input": "3\nD 100\nW 30\nW 50", "expected_output": "20", "is_hidden": False, "description": "100-30-50=20"},
         {"input": "2\nD 50\nW 100", "expected_output": "Insufficient funds\n50", "is_hidden": False, "description": "Недостаточно средств"},
     ]),

    ("oop", 3, "Наследование: Animal → Dog", "Мұрагерлік: Animal → Dog",
     "Создайте класс `Animal` с атрибутом `name` и методом `speak()`, возвращающим `...`.\nСоздайте класс `Dog(Animal)`, переопределяющий `speak()` — возвращает `Woof!`.\n\nСчитайте имя и выведите `{name} says {speak()}`.",
     "`Animal` класын `name` атрибутымен және `...` қайтаратын `speak()` әдісімен жасаңыз.\n`Dog(Animal)` класын жасап, `speak()` — `Woof!` қайтарсын.\n\nАтты оқып, `{name} says {speak()}` шығарыңыз.",
     "medium", 20, 'class Animal:\n    # Ваш код здесь\n    pass\n\nclass Dog(Animal):\n    # Ваш код здесь\n    pass\n\nname = input()\ndog = Dog(name)\nprint(f"{dog.name} says {dog.speak()}")\n',
     ["super().__init__(name)", "def speak(self): return 'Woof!'"],
     ["super().__init__(name)", "def speak(self): return 'Woof!'"],
     [
         {"input": "Rex", "expected_output": "Rex says Woof!", "is_hidden": False, "description": "Rex"},
         {"input": "Buddy", "expected_output": "Buddy says Woof!", "is_hidden": True, "description": "Buddy"},
     ]),

    ("oop", 4, "Класс Stack", "Stack класы",
     "Реализуйте класс `Stack` с методами:\n- `push(item)` — добавить элемент\n- `pop()` — удалить и вернуть верхний элемент (или `None` если пуст)\n- `peek()` — вернуть верхний элемент без удаления (или `None`)\n- `size()` — количество элементов\n\nСчитайте количество команд, затем команды: `push X`, `pop`, `peek`, `size`.\nДля pop, peek, size выведите результат.",
     "`Stack` класын жасаңыз:\n- `push(item)` — элемент қосу\n- `pop()` — жоғарғы элементті алып тастау (бос болса `None`)\n- `peek()` — жоғарғы элементті қайтару (бос болса `None`)\n- `size()` — элементтер саны\n\nКомандалар санын, содан кейін командаларды оқыңыз: `push X`, `pop`, `peek`, `size`.\npop, peek, size үшін нәтижесін шығарыңыз.",
     "medium", 20, '',
     ["Используйте список: self.items = []", "push = append, pop = pop()"],
     ["Тізімді қолданыңыз: self.items = []", "push = append, pop = pop()"],
     [
         {"input": "5\npush 1\npush 2\npeek\npop\nsize", "expected_output": "2\n2\n1", "is_hidden": False, "description": "Базовый тест"},
         {"input": "2\npop\nsize", "expected_output": "None\n0", "is_hidden": True, "description": "Пустой стек"},
     ]),

    ("oop", 5, "Мини-проект: Зоомагазин", "Шағын жоба: Зоодүкен",
     "Создайте систему классов:\n- `Animal(name, species, price)` с `__str__` → `{name} ({species}) - {price} тг`\n- `PetShop(shop_name)` с методами:\n  - `add_animal(animal)` — добавить животное\n  - `find_by_species(species)` — список животных этого вида\n  - `total_value()` — общая стоимость всех животных\n\nСчитайте название магазина, количество животных N, затем N строк `name species price`.\nВыведите:\n1. Название магазина\n2. Общую стоимость\n3. Все животные (каждое на строке)",
     "Кластар жүйесін жасаңыз:\n- `Animal(name, species, price)` + `__str__` → `{name} ({species}) - {price} тг`\n- `PetShop(shop_name)`:\n  - `add_animal(animal)`\n  - `find_by_species(species)` — осы түрдің жануарлар тізімі\n  - `total_value()` — жалпы құны\n\nДүкен атын, N жануар санын, содан кейін N жол `name species price` оқыңыз.\nШығарыңыз:\n1. Дүкен аты\n2. Жалпы құн\n3. Барлық жануарлар (әрқайсысы жеке жолда)",
     "hard", 30, '',
     ["Используйте список self.animals = []", "sum(a.price for a in self.animals)"],
     ["self.animals = [] тізімін қолданыңыз", "sum(a.price for a in self.animals)"],
     [
         {"input": "ZooLand\n3\nRex dog 5000\nMurka cat 3000\nPolly parrot 8000",
          "expected_output": "ZooLand\n16000\nRex (dog) - 5000 тг\nMurka (cat) - 3000 тг\nPolly (parrot) - 8000 тг",
          "is_hidden": False, "description": "3 животных"},
     ]),
]


def generate_sql() -> str:
    """Generate SQL INSERT statements for topics and challenges."""
    lines = []

    # Topics
    for i, t in enumerate(TOPICS):
        vals = (
            f"'{t['title']}', "
            f"'{t['title_kk']}', "
            f"'{t['slug']}', "
            f"'{t.get('description', '')}', "
            f"'{t.get('description_kk', '')}', "
            f"{t['sort_order']}, "
            f"'{t.get('icon', '')}', "
            f"{t.get('grade_level', 'NULL')}, "
            f"NULL, "  # paragraph_id
            f"true"
        )
        lines.append(
            f"INSERT INTO coding_topics (title, title_kk, slug, description, description_kk, "
            f"sort_order, icon, grade_level, paragraph_id, is_active) VALUES ({vals});"
        )

    lines.append("")

    # Challenges — reference topic by slug subquery
    for ch in CHALLENGES:
        (slug, sort_order, title, title_kk, desc, desc_kk,
         diff, points, starter, hints, hints_kk, tests) = ch

        esc = lambda s: s.replace("'", "''")
        starter_val = f"'{esc(starter)}'" if starter else "NULL"

        lines.append(
            f"INSERT INTO coding_challenges "
            f"(topic_id, sort_order, title, title_kk, description, description_kk, "
            f"difficulty, points, starter_code, hints, hints_kk, test_cases, is_active) VALUES ("
            f"(SELECT id FROM coding_topics WHERE slug = '{slug}'), "
            f"{sort_order}, "
            f"'{esc(title)}', "
            f"'{esc(title_kk)}', "
            f"'{esc(desc)}', "
            f"'{esc(desc_kk)}', "
            f"'{diff}', "
            f"{points}, "
            f"{starter_val}, "
            f"'{json.dumps(hints, ensure_ascii=False)}'::jsonb, "
            f"'{json.dumps(hints_kk, ensure_ascii=False)}'::jsonb, "
            f"'{json.dumps(tests, ensure_ascii=False)}'::jsonb, "
            f"true);"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_sql())
