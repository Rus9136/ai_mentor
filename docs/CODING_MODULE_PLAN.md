# Модуль программирования — план доработки

> Дата: 2026-03-19
> Обновлено: 2026-03-21
> Статус: Этапы 0-3 реализованы, этапы 4-5 запланированы

## Текущее состояние (Этап 0 + Этап 1) ✅

### Этап 0 — Песочница ✅

Реализована базовая Python-песочница:
- CodeMirror 6 редактор с подсветкой Python
- Pyodide (WebAssembly) — выполнение Python в браузере
- Поддержка `input()` через поле "Входные данные"
- Таймаут 10 сек для защиты от бесконечных циклов
- Интеграция в homework CODE тип (answer_code)
- Навигация: пункт "Код" в sidebar
- Страница: `/sandbox`

### Этап 1 — Задачи с автопроверкой ✅

Реализовано:
- **3 таблицы БД:** `coding_topics`, `coding_challenges`, `coding_submissions` (миграция `065_coding_challenges`)
- **Backend API:** 6 endpoints (`/students/coding/topics`, `.../challenges`, `.../submit`, `.../submissions`, `.../stats`)
- **Автопроверка через Pyodide:** клиентский прогон тест-кейсов (`challenge-runner.ts`)
- **Каталог задач:** страница `/sandbox/challenges` с фильтрацией по темам
- **Страница задачи:** `/sandbox/challenges/[id]` — split-view (условие + редактор)
- **50 задач** по 7 темам: Переменные, Условия, Циклы, Строки, Списки, Функции, ООП
- **XP система:** начисление очков за первое решение, защита от дублирования
- **Подсказки:** пошаговое раскрытие подсказок
- **Локализация:** русский + казахский
- **11 интеграционных тестов** (все проходят)

**Файлы backend:**
| Файл | Описание |
|------|----------|
| `alembic/versions/065_coding_challenges.py` | Миграция: 3 таблицы + GRANT |
| `app/models/coding.py` | CodingTopic, CodingChallenge, CodingSubmission |
| `app/schemas/coding.py` | Pydantic схемы (request/response) |
| `app/repositories/coding_repo.py` | CRUD + статистика |
| `app/services/coding_service.py` | Бизнес-логика, XP, прогресс |
| `app/api/v1/students/coding.py` | 6 API endpoints |
| `scripts/seed_coding_challenges.py` | Скрипт генерации SQL для 50 задач |
| `tests/test_coding_challenges.py` | 11 интеграционных тестов |

**Файлы frontend (`student-app/`):**
| Файл | Описание |
|------|----------|
| `src/lib/api/coding.ts` | API клиент |
| `src/lib/hooks/use-coding.ts` | React Query хуки |
| `src/lib/pyodide/challenge-runner.ts` | Прогон тест-кейсов через Pyodide |
| `src/components/sandbox/ChallengeCard.tsx` | Карточка задачи в каталоге |
| `src/components/sandbox/ChallengeRunner.tsx` | Редактор + проверка + подсказки |
| `src/components/sandbox/TestResults.tsx` | Результаты тестов |
| `src/app/[locale]/(app)/sandbox/challenges/page.tsx` | Каталог задач |
| `src/app/[locale]/(app)/sandbox/challenges/[id]/page.tsx` | Страница задачи |

---

### Этап 2 — Пошаговые курсы ✅

Реализовано:
- **3 таблицы БД:** `coding_courses`, `coding_lessons`, `coding_course_progress` (миграция `066_coding_courses`)
- **Backend API:** 4 endpoints (`/students/coding/courses`, `.../lessons`, `.../lessons/{id}`, `.../lessons/{id}/complete`)
- **CourseService:** бизнес-логика прогресса, завершение уроков, автозавершение курса
- **Каталог курсов:** страница `/sandbox/courses` с карточками курсов и прогрессом
- **Список уроков:** страница `/sandbox/courses/[slug]` с индикаторами выполнения
- **Страница урока:** `/sandbox/courses/[slug]/lessons/[id]` — теория (markdown) + вкладка практики с ChallengeRunner
- **Навигация:** кнопки prev/next между уроками, автоматическое завершение курса
- **Seed-скрипт:** `scripts/seed_coding_courses.py` — курс "Основы Python" (20 уроков)
- **11 интеграционных тестов** (все проходят)
- **Локализация:** русский + казахский (namespace `courses`)

**Файлы backend:**
| Файл | Описание |
|------|----------|
| `alembic/versions/066_coding_courses.py` | Миграция: 3 таблицы + GRANT |
| `app/models/coding.py` | + CodingCourse, CodingLesson, CodingCourseProgress |
| `app/schemas/coding.py` | + CourseWithProgress, LessonDetail, LessonCompleteResponse |
| `app/repositories/coding_repo.py` | + CourseRepository |
| `app/services/coding_service.py` | + CourseService |
| `app/api/v1/students/courses.py` | 4 API endpoints |
| `scripts/seed_coding_courses.py` | Скрипт генерации SQL для курса "Основы Python" |
| `tests/test_coding_courses.py` | 11 интеграционных тестов |

**Файлы frontend (`student-app/`):**
| Файл | Описание |
|------|----------|
| `src/lib/api/coding.ts` | + типы и API функции для курсов |
| `src/lib/hooks/use-coding.ts` | + React Query хуки для курсов |
| `src/components/sandbox/CourseCard.tsx` | Карточка курса с прогрессом |
| `src/components/sandbox/LessonView.tsx` | Компонент урока (теория + практика) |
| `src/app/[locale]/(app)/sandbox/courses/page.tsx` | Каталог курсов |
| `src/app/[locale]/(app)/sandbox/courses/[slug]/page.tsx` | Список уроков курса |
| `src/app/[locale]/(app)/sandbox/courses/[slug]/lessons/[id]/page.tsx` | Страница урока |

---

## Этап 2. Задачи с автопроверкой (архив плана)

> ℹ️ Этап 1 выше — реализованная версия. Ниже оставлен оригинальный план для справки.

## Этап 1 (оригинальный план). Задачи с автопроверкой

**Цель:** превратить песочницу из блокнота в обучающий инструмент.

### 1.1 Модель данных

```sql
-- Категории задач (темы)
CREATE TABLE coding_topics (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,           -- "Циклы", "Списки"
    title_kk VARCHAR(200),                 -- на казахском
    slug VARCHAR(50) UNIQUE NOT NULL,      -- "loops", "lists"
    description TEXT,
    description_kk TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    icon VARCHAR(50),                      -- lucide icon name
    grade_level INTEGER,                   -- рекомендуемый класс (6-11)
    paragraph_id INTEGER REFERENCES paragraphs(id),  -- привязка к учебнику
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Задачи
CREATE TABLE coding_challenges (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES coding_topics(id),
    title VARCHAR(300) NOT NULL,           -- "Чётное или нечётное?"
    title_kk VARCHAR(300),
    description TEXT NOT NULL,             -- условие задачи (markdown)
    description_kk TEXT,
    difficulty VARCHAR(20) NOT NULL DEFAULT 'easy',  -- easy, medium, hard
    sort_order INTEGER NOT NULL DEFAULT 0,
    points INTEGER NOT NULL DEFAULT 10,    -- XP за решение
    starter_code TEXT,                     -- начальный код в редакторе
    solution_code TEXT,                    -- эталонное решение (скрыто)
    hints JSONB DEFAULT '[]',             -- ["Используй оператор %", "..."]
    hints_kk JSONB DEFAULT '[]',
    test_cases JSONB NOT NULL,            -- см. формат ниже
    time_limit_ms INTEGER DEFAULT 5000,   -- лимит на один тест-кейс
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Результаты решений
CREATE TABLE coding_submissions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    school_id INTEGER NOT NULL REFERENCES schools(id),
    challenge_id INTEGER NOT NULL REFERENCES coding_challenges(id),
    code TEXT NOT NULL,                    -- код ученика
    status VARCHAR(20) NOT NULL,           -- passed, failed, error, timeout
    tests_passed INTEGER NOT NULL DEFAULT 0,
    tests_total INTEGER NOT NULL DEFAULT 0,
    execution_time_ms INTEGER,
    error_message TEXT,                    -- если ошибка
    attempt_number INTEGER NOT NULL DEFAULT 1,
    xp_earned INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_coding_submissions_student ON coding_submissions(student_id, challenge_id);
CREATE INDEX idx_coding_challenges_topic ON coding_challenges(topic_id, sort_order);
```

**Формат test_cases (JSONB):**
```json
[
  {
    "input": "",
    "expected_output": "Hello, World!",
    "is_hidden": false,
    "description": "Базовый тест"
  },
  {
    "input": "5\n3",
    "expected_output": "8",
    "is_hidden": false,
    "description": "5 + 3 = 8"
  },
  {
    "input": "0\n0",
    "expected_output": "0",
    "is_hidden": true,
    "description": "Граничный случай"
  }
]
```

- `is_hidden: false` — ученик видит входные/выходные данные (для понимания)
- `is_hidden: true` — скрытые тесты (защита от хардкода ответов)

### 1.2 Backend API

```
GET  /students/coding/topics                   — список тем с прогрессом
GET  /students/coding/topics/{slug}/challenges — задачи по теме
GET  /students/coding/challenges/{id}          — одна задача (условие + открытые тесты)
POST /students/coding/challenges/{id}/submit   — отправить решение
GET  /students/coding/challenges/{id}/submissions — мои попытки
GET  /students/coding/stats                    — статистика (решено, серия, XP)
```

### 1.3 Автопроверка (клиентская, через Pyodide)

Проверка работает полностью в браузере (не нагружая сервер):

```
1. Ученик нажимает "Проверить"
2. Для каждого test_case:
   a. Подставляем test_case.input в stdin
   b. Запускаем код через Pyodide
   c. Сравниваем stdout.strip() с expected_output.strip()
   d. Таймаут = time_limit_ms
3. Результат: { passed: 4, total: 5, details: [...] }
4. Если все тесты пройдены → POST /submit на сервер (сохранить + начислить XP)
```

Сравнение по строкам (strip + split по \n), игнорируя trailing whitespace.

### 1.4 Frontend

**Страница каталога задач:** `/sandbox/challenges`

```
┌─────────────────────────────────────────────────┐
│ 🐍 Задачи по Python                            │
├─────────────────────────────────────────────────┤
│ [Все] [Переменные] [Условия] [Циклы] [Списки]  │
├─────────────────────────────────────────────────┤
│                                                 │
│ 📗 Переменные и типы данных (6 класс)           │
│    ✅ 1. Привет, мир!              ⭐  10 XP    │
│    ✅ 2. Сумма двух чисел          ⭐  10 XP    │
│    🔵 3. Площадь прямоугольника    ⭐  10 XP    │
│    ⚪ 4. Обмен переменных          ⭐⭐ 20 XP   │
│                                                 │
│ 📘 Условия и ветвление (7 класс)                │
│    ⚪ 5. Чётное или нечётное?      ⭐  10 XP    │
│    ⚪ 6. Максимум из трёх          ⭐  10 XP    │
│    ...                                          │
└─────────────────────────────────────────────────┘

⚪ = не начато, 🔵 = в процессе, ✅ = решено
```

**Страница задачи:** `/sandbox/challenges/[id]`

```
┌─────────────────────────────────────────────────┐
│ ← Назад    Задача 3 / 24    ⭐ 10 XP    💡     │
├─────────────────┬───────────────────────────────┤
│ 📋 Условие      │   # Редактор кода             │
│                 │                               │
│ Даны длина и    │   a = int(input())            │
│ ширина прямо-   │   b = int(input())            │
│ угольника.      │   # напишите решение          │
│ Вычислите       │                               │
│ площадь.        │                               │
│                 │                               │
│ Пример:         │          [▶ Запустить] [✓ Про-│
│ Вход: 5 3       │                        верить]│
│ Выход: 15       ├───────────────────────────────┤
│                 │ Тесты:                        │
│ Вход: 10 7      │ ✅ Тест 1: 5,3 → 15          │
│ Выход: 70       │ ✅ Тест 2: 10,7 → 70         │
│                 │ ❌ Тест 3: 0,5 → 0 (получили │
│ 💡 Подсказка 1  │    "5")                       │
│ (нажмите чтобы  │ 🔒 Тест 4: скрытый           │
│  открыть)       │ 🔒 Тест 5: скрытый           │
│                 │                               │
│                 │ Результат: 2 / 5 тестов       │
└─────────────────┴───────────────────────────────┘
```

### 1.5 Начальный набор задач

По 5-8 задач на каждую тему, всего ~50 задач для старта:

**Переменные и ввод/вывод (6 класс, 8 задач):**
| # | Задача | Сложность | Концепция |
|---|--------|-----------|-----------|
| 1 | Привет, мир! | easy | print() |
| 2 | Эхо — повтори ввод | easy | input(), print() |
| 3 | Сумма двух чисел | easy | int(input()), + |
| 4 | Площадь прямоугольника | easy | *, переменные |
| 5 | Обмен значений двух переменных | easy | присваивание |
| 6 | Последняя цифра числа | medium | % 10 |
| 7 | Разделить на часы и минуты | medium | //, % |
| 8 | Расстояние между точками | medium | math.sqrt, ** |

**Условия и ветвление (7 класс, 8 задач):**
| # | Задача | Сложность | Концепция |
|---|--------|-----------|-----------|
| 9 | Чётное или нечётное | easy | if/else, % |
| 10 | Максимум из трёх чисел | easy | if/elif/else |
| 11 | Оценка по баллу | easy | elif цепочка |
| 12 | Високосный год | medium | and, or |
| 13 | Треугольник существует? | medium | составные условия |
| 14 | Калькулятор (+, -, *, /) | medium | input строки |
| 15 | Сортировка трёх чисел | medium | вложенные if |
| 16 | Квадратное уравнение | hard | discriminant, math.sqrt |

**Циклы (8 класс, 8 задач):**
| # | Задача | Сложность | Концепция |
|---|--------|-----------|-----------|
| 17 | Сумма от 1 до N | easy | for range |
| 18 | Таблица умножения | easy | for, f-string |
| 19 | Факториал | easy | for, *= |
| 20 | Степень двойки | easy | while |
| 21 | Количество цифр в числе | medium | while, // |
| 22 | Простое ли число? | medium | for, break |
| 23 | Числа Фибоначчи | medium | for, два переменных |
| 24 | Рисование пирамиды из * | medium | вложенные for |

**Строки (8-9 класс, 6 задач):**
| # | Задача | Сложность | Концепция |
|---|--------|-----------|-----------|
| 25 | Длина строки без пробелов | easy | len, replace |
| 26 | Перевернуть строку | easy | slicing [::-1] |
| 27 | Палиндром? | medium | сравнение строк |
| 28 | Подсчёт гласных | medium | for, in |
| 29 | Шифр Цезаря | hard | ord(), chr() |
| 30 | Самое длинное слово | medium | split(), max() |

**Списки и массивы (9 класс, 8 задач):**
| # | Задача | Сложность | Концепция |
|---|--------|-----------|-----------|
| 31 | Сумма элементов списка | easy | for, sum |
| 32 | Минимум и максимум | easy | min, max |
| 33 | Чётные элементы | easy | for, if, append |
| 34 | Перевернуть список | easy | [::-1] или reverse |
| 35 | Уникальные элементы | medium | set или цикл |
| 36 | Сортировка пузырьком | medium | вложенные for |
| 37 | Бинарный поиск | hard | while, mid |
| 38 | Матрица — сумма строк | hard | двумерный список |

**Функции (8-9 класс, 6 задач):**
| # | Задача | Сложность | Концепция |
|---|--------|-----------|-----------|
| 39 | Функция приветствия | easy | def, параметры |
| 40 | Функция is_even | easy | return bool |
| 41 | Функция факториал | medium | рекурсия |
| 42 | Функция is_prime | medium | return, for |
| 43 | НОД (алгоритм Евклида) | medium | while, рекурсия |
| 44 | Декоратор-таймер | hard | функции высшего порядка |

**ООП (9-10 класс, 6 задач):**
| # | Задача | Сложность | Концепция |
|---|--------|-----------|-----------|
| 45 | Класс Rectangle | easy | class, __init__, метод |
| 46 | Класс Student с оценками | easy | list в атрибуте |
| 47 | Класс BankAccount | medium | deposit, withdraw |
| 48 | Наследование: Animal → Dog | medium | super().__init__ |
| 49 | Класс Stack (push, pop) | medium | структура данных |
| 50 | Мини-проект: Зоомагазин | hard | несколько классов |

### 1.6 Файлы для реализации

**Backend (новые):**
| Файл | Описание |
|------|----------|
| `alembic/versions/065_coding_challenges.py` | Миграция: 3 таблицы |
| `app/models/coding.py` | SQLAlchemy модели |
| `app/schemas/coding.py` | Pydantic схемы |
| `app/repositories/coding_repo.py` | CRUD |
| `app/services/coding_service.py` | Бизнес-логика, XP |
| `app/api/v1/students/coding.py` | API endpoints |

**Frontend (новые):**
| Файл | Описание |
|------|----------|
| `src/app/[locale]/(app)/sandbox/challenges/page.tsx` | Каталог задач |
| `src/app/[locale]/(app)/sandbox/challenges/[id]/page.tsx` | Страница задачи |
| `src/components/sandbox/ChallengeCard.tsx` | Карточка задачи |
| `src/components/sandbox/TestResults.tsx` | Результаты тестов |
| `src/components/sandbox/ChallengeRunner.tsx` | Редактор + проверка |
| `src/lib/api/coding.ts` | API клиент |
| `src/lib/hooks/use-coding.ts` | React Query хуки |
| `src/lib/pyodide/challenge-runner.ts` | Прогон тест-кейсов через Pyodide |

---

## Этап 2. Пошаговые курсы (Learning Paths)

**Цель:** структурированное обучение для тех, кто начинает с нуля.

### 2.1 Концепция

Курс = последовательность уроков. Урок = теория (текст) + интерактивный код + мини-задача.

```sql
CREATE TABLE coding_courses (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    title_kk VARCHAR(300),
    description TEXT,
    description_kk TEXT,
    slug VARCHAR(50) UNIQUE NOT NULL,       -- "python-basics"
    grade_level INTEGER,
    total_lessons INTEGER NOT NULL DEFAULT 0,
    estimated_hours FLOAT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE coding_lessons (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES coding_courses(id),
    title VARCHAR(300) NOT NULL,
    title_kk VARCHAR(300),
    sort_order INTEGER NOT NULL DEFAULT 0,
    theory_content TEXT NOT NULL,            -- markdown с примерами
    theory_content_kk TEXT,
    starter_code TEXT,                       -- код для эксперимента
    challenge_id INTEGER REFERENCES coding_challenges(id), -- задача-закрепление
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE coding_course_progress (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    course_id INTEGER NOT NULL REFERENCES coding_courses(id),
    last_lesson_id INTEGER REFERENCES coding_lessons(id),
    completed_lessons INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    UNIQUE(student_id, course_id)
);
```

### 2.2 Начальные курсы

**Курс 1: Основы Python (6 класс, ~20 уроков)**
1. Что такое программирование?
2. Первая программа: `print("Сәлем!")`
3. Переменные — коробки для данных
4. Типы данных: числа и строки
5. Ввод данных: `input()`
6. Арифметические операции
7. Практика: калькулятор
8. Условие `if` — принимаем решения
9. `if/else` — два пути
10. `elif` — много путей
11. Практика: оценка по баллу
12. Цикл `for` — повторяем действия
13. `range()` — счётчик повторений
14. Практика: таблица умножения
15. Цикл `while` — повторяем пока
16. `break` и `continue`
17. Практика: угадай число
18. Списки — коллекция данных
19. Методы списков: append, remove, sort
20. Итоговый проект: список дел

**Курс 2: Продвинутый Python (8-9 класс, ~16 уроков)**
1. Функции — переиспользуем код
2. Параметры и return
3. Области видимости
4. Практика: библиотека функций
5. Строковые методы
6. Срезы (slicing)
7. Словари — ключ-значение
8. Кортежи и множества
9. List comprehension
10. Работа с матрицами
11. Сортировки: bubble, selection
12. Поиск: линейный и бинарный
13. Рекурсия
14. Практика: алгоритмические задачи
15. Обработка ошибок: try/except
16. Итоговый проект: записная книжка

**Курс 3: ООП на Python (9-10 класс, ~12 уроков)**
1. Что такое объект? (аналогия: телефон — модель, цвет, звонить)
2. Первый класс: `class Dog`
3. `__init__` — создаём объект с параметрами
4. Методы — что объект умеет делать
5. Практика: класс `Rectangle`
6. Несколько объектов, `self`
7. `__str__` — красивый вывод
8. Наследование: `class Puppy(Dog)`
9. `super()` и переопределение методов
10. Практика: `Animal → Cat, Dog, Bird`
11. Инкапсуляция: приватные атрибуты
12. Итоговый проект: мини-игра "Зоомагазин"

### 2.3 UI

**Страница курсов:** `/sandbox/courses`

```
┌─────────────────────────────────────────────┐
│ 🎓 Курсы по Python                         │
├─────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐            │
│ │ 🐍 Основы   │ │ 🚀 Продвину-│            │
│ │    Python   │ │    тый      │            │
│ │ 6 класс     │ │ 8-9 класс   │            │
│ │ 20 уроков   │ │ 16 уроков   │            │
│ │ ████░░ 60%  │ │ ░░░░░░ 0%   │            │
│ │ [Продолжить]│ │ [Начать]    │            │
│ └─────────────┘ └─────────────┘            │
│ ┌─────────────┐                            │
│ │ 🏗️ ООП      │                            │
│ │ 9-10 класс  │                            │
│ │ 12 уроков   │                            │
│ │ 🔒 Сначала  │                            │
│ │ пройди курс │                            │
│ │ "Продвинут."│                            │
│ └─────────────┘                            │
└─────────────────────────────────────────────┘
```

**Страница урока:** `/sandbox/courses/[slug]/lessons/[id]` — сплит: теория слева + редактор справа.

---

## Этап 3. AI-ментор для кода ✅

**Цель:** помощь ученику в момент затруднения без выдачи готового ответа.

Реализовано:
- **Отдельный `CodingChatService`** (~250 строк) — не расширяет ChatService (1500 строк), работает напрямую с ChatSession/ChatMessage + LLMService
- **4 AI-действия:** подсказка, объяснение ошибки, code review, пошаговая трассировка
- **1 сессия на задачу** — все действия и follow-up в одном потоке (переиспользование в течение 24ч)
- **SSE streaming** — как в основном чате
- **Без RAG/Memory** — не нужны для coding задач
- **Без solution_code в промпте** — защита от утечки решения
- **Двуязычные промпты** — русский + казахский
- **16 интеграционных тестов** (все проходят)

### 3.1 Функции

| Кнопка | Действие | Промпт для AI |
|--------|----------|---------------|
| 💡 Подсказка | Наводящий вопрос | "Дай подсказку для задачи {title}, не давай решение. Код ученика: {code}. Ошибка: {error}" |
| 🔍 Объясни ошибку | Разбор traceback | "Объясни ошибку простым языком для школьника: {traceback}" |
| 📝 Проверь код | Code review | "Оцени код ученика: стиль, эффективность, возможные баги. Не переписывай, дай советы." |
| 🔄 Покажи пошагово | Трассировка | "Покажи пошаговое выполнение кода с состоянием переменных на каждом шаге" |

### 3.2 Реализация

- Отдельный `CodingChatService` (не расширяет ChatService) + `LLMService`
- Новый тип чата: `chat_type = "coding"`, миграция `072_coding_chat` (challenge_id в chat_sessions)
- Системный промпт с правилами: никогда не давать готовое решение, наводящие вопросы, простой язык
- UI: кнопка "AI Ментор" в toolbar ChallengeRunner → slide-over панель с чатом
- Контекст: условие задачи + код ученика + ошибка (автоматически)
- API: `POST /students/coding/ai/start`, `POST .../messages/stream`, `GET .../sessions/{id}`, `GET .../challenge/{id}/session`

**Файлы backend:**
| Файл | Описание |
|------|----------|
| `alembic/versions/072_coding_chat.py` | Миграция: challenge_id в chat_sessions |
| `app/schemas/coding_chat.py` | CodingAction enum, request schemas |
| `app/services/coding_chat_service.py` | Сервис: сессии, streaming, промпты ru/kk |
| `app/api/v1/students/coding_chat.py` | 4 API endpoints |
| `tests/test_coding_chat.py` | 16 интеграционных тестов |

**Файлы frontend (`student-app/`):**
| Файл | Описание |
|------|----------|
| `src/lib/api/coding-chat.ts` | API клиент + SSE streaming |
| `src/lib/hooks/use-coding-chat.ts` | React хуки для AI чата |
| `src/components/sandbox/CodingAIPanel.tsx` | Slide-over панель AI-ментора |
| `src/components/sandbox/ChallengeRunner.tsx` | + кнопка "AI Ментор" в toolbar |

---

## Этап 4. Визуализация выполнения

**Цель:** ученик видит как Python выполняет код пошагово.

### 4.1 Режим "Отладка"

Кнопка "🔍 По шагам" рядом с "▶ Запустить":

```
Шаг 1:  x = 5           │ x: 5
Шаг 2:  y = 3           │ x: 5, y: 3
Шаг 3:  z = x + y  ←    │ x: 5, y: 3, z: 8
Шаг 4:  print(z)        │ Вывод: 8
        [◀ Назад] [Далее ▶] [▶▶ Автоплей]
```

### 4.2 Реализация

Два варианта:

**Вариант A (простой):** AI-генерация трассировки через LLM — отправляем код, получаем пошаговый разбор в markdown. Быстро реализовать, но неинтерактивно.

**Вариант B (полноценный):** Pyodide + AST-трассировка:
- Парсим Python-код через `ast` модуль в Pyodide
- Инструментируем каждую строку для записи состояния переменных
- Выполняем и собираем массив шагов `[{line, variables, output}]`
- Рендерим интерактивный stepper

Рекомендуется: начать с варианта A, потом перейти на B.

---

## Этап 5. Геймификация программирования

**Цель:** мотивация через достижения, серии, рейтинги.

### 5.1 Достижения

| Значок | Название | Условие |
|--------|----------|---------|
| 🐣 | Первый код | Запустить первую программу в песочнице |
| 🎯 | Первая задача | Решить первую задачу (все тесты) |
| 🔟 | Десятка | Решить 10 задач |
| 💯 | Сотня | Решить 100 задач |
| 🔁 | Мастер циклов | Решить все задачи на циклы |
| 📊 | Укротитель списков | Решить все задачи на списки |
| 🏗️ | Архитектор | Решить первую задачу на ООП |
| 🔥 | Серия 7 дней | Решать задачи 7 дней подряд |
| 🔥🔥 | Серия 30 дней | Решать задачи 30 дней подряд |
| ⚡ | Скоростной | Решить задачу менее чем за 2 мин |
| 🏆 | Олимпиадник | Решить 5 задач уровня hard |
| 🎓 | Выпускник | Пройти курс "Основы Python" |
| 🧠 | ООП-мастер | Пройти курс "ООП на Python" |

### 5.2 Рейтинг по программированию

Отдельный leaderboard "Программирование":
- Очки = сумма XP за решённые задачи
- Фильтр: школа / класс / все
- Показывается на странице `/sandbox/challenges`

### 5.3 Ежедневные задачи

"Задача дня" — каждый день одна случайная задача:
- Решил сегодня → +50 XP бонус
- Серия дней → множитель XP (x1.5 за 7 дней, x2 за 30)
- Виджет на главной странице

---

## Навигация после всех этапов

```
Sidebar:
  🏠 Главная
  📚 Предметы
  🏆 Достижения
  📝 Тесты
  📋 Задания
  💻 Код ──────────────┐
  👤 Профиль           │
                       ▼
              ┌─────────────────┐
              │ 🐍 Песочница    │  ← текущая (этап 0)
              │ 📋 Задачи       │  ← этап 1
              │ 🎓 Курсы        │  ← этап 2
              └─────────────────┘

  /sandbox              → песочница (свободный режим)
  /sandbox/challenges   → каталог задач
  /sandbox/challenges/3 → решение задачи
  /sandbox/courses      → список курсов
  /sandbox/courses/python-basics/lessons/5 → урок
```

---

## Приоритеты и сроки

| Этап | Что | Статус | Приоритет | Зависимости |
|------|-----|--------|-----------|-------------|
| **0** | Песочница | ✅ Готово | — | — |
| **1** | Задачи с автопроверкой | ✅ Готово | — | — |
| **2** | Пошаговые курсы | ✅ Готово | — | Этап 1 ✅ |
| **3** | AI-ментор для кода | ✅ Готово | — | Этап 1 ✅ |
| **4** | Визуализация выполнения | 📋 План | 🟢 Низкий | — |
| **5** | Геймификация | 📋 План | 🟡 Средний | Этап 1 ✅ |

Рекомендуемый следующий: **5 → 2 → 3 → 4**

Этап 5 (геймификация) даёт максимальный эффект следующим: достижения + серии + рейтинг поверх уже работающих задач. Затем курсы для структурного обучения, AI-ментор для помощи, визуализация как бонус.

---

## Покрытие учебной программы

| Класс | Темы в учебнике | Покрытие задачами |
|-------|-----------------|-------------------|
| 6 | IDE, синтаксис, типы, ввод/вывод, линейные алгоритмы | Тема "Переменные" (8 задач) |
| 7 | Файлы, ветвление if/elif/else, вложенные/составные условия | Тема "Условия" (8 задач) |
| 8 | for, while, break/continue, вложенные циклы, трассировка | Тема "Циклы" (8 задач) |
| 8-9 | Функции, return, параметры | Тема "Функции" (6 задач) |
| 9 | Списки, сортировка, поиск, двумерные массивы | Тема "Списки" (8 задач) |
| 9-10 | ООП: классы, наследование | Тема "ООП" (6 задач) |
| 8-9 | Строки, срезы, методы | Тема "Строки" (6 задач) |

Итого: **50 задач** покрывают основную программу 6-10 классов.
Расширение до 100-200 задач — через AI-генерацию + ручную проверку тест-кейсов.
