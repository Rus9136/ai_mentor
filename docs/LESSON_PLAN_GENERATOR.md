# AI Lesson Plan Generator (KMJ / QMJ)

Система автоматической генерации краткосрочных планов уроков (Қысқамерзімді жоспар) с помощью AI, с учётом уровней учеников конкретного класса.

---

## 1. Описание продукта

### Проблема
Учитель тратит 30-60 минут на составление QMJ (қысқамерзімді жоспар) для каждого урока. При этом:
- Данные об уровнях учеников (A/B/C) уже есть в системе AI Mentor
- Цели обучения (`learning_objective`) и цели урока (`lesson_objective`) уже привязаны к параграфам
- Контент параграфа, ключевые термины, вопросы — всё доступно в БД

### Решение
Учитель в Teacher App выбирает **параграф** и (опционально) **класс** — система генерирует готовый QMJ по стандарту ГОСО, адаптированный под уровни конкретных учеников.

### Пользователь
**TEACHER** — учитель, привязанный к школе, классам и предмету.

### Результат
Структурированный план урока в формате QMJ, содержащий:
- Заголовок (предмет, тема, цели, ценности месяца)
- 3 этапа урока (начало / середина / конец) с хронометражем
- Деятельность учителя и учеников на каждом этапе
- Задания с дескрипторами и баллами
- Дифференциация (саралау) по уровням A/B/C
- Методы оценивания (формативное)
- Рефлексия

---

## 2. Входные данные (что уже есть в системе)

### Из модели Paragraph
| Поле | Описание | Файл |
|------|----------|------|
| `title` | Название параграфа (тема урока) | `backend/app/models/paragraph.py:19` |
| `content` | Полный текст параграфа | `paragraph.py:22` |
| `learning_objective` | Оқу мақсаты (цель обучения по ГОСО) | `paragraph.py:24` |
| `lesson_objective` | Сабақ мақсаты (цель урока) | `paragraph.py:25` |
| `key_terms` | JSON массив ключевых терминов | `paragraph.py:27` |
| `questions` | JSON массив вопросов | `paragraph.py:28` |
| `summary` | Краткое содержание | `paragraph.py:23` |

### Из иерархии Paragraph -> Chapter -> Textbook
| Поле | Описание | Источник |
|------|----------|----------|
| `chapter.title` | Название раздела (бөлім) | `chapter.py:18` |
| `chapter.number` | Номер раздела | `chapter.py:17` |
| `textbook.title` | Название учебника | `textbook.py:18` |
| `textbook.subject` | Предмет | `textbook.py:20` |
| `textbook.grade_level` | Класс (1-11) | `textbook.py:21` |

Метод получения: `ParagraphRepository.get_content_metadata()` (`paragraph_repo.py:153-192`)

### Из ParagraphContent (по языку)
| Поле | Описание |
|------|----------|
| `explain_text` | Упрощённое объяснение |
| `cards` | JSONB массив карточек |
| `audio_text` | Текст для аудио |

### Из ГОСО (LearningOutcome)
| Поле | Описание |
|------|----------|
| `code` | Код цели обучения (напр. "11.1.1.1") |
| `title_ru`, `title_kz` | Двуязычное описание |
| `cognitive_level` | Уровень по Блуму |

Связь: `paragraph_outcomes` (junction table) -> `LearningOutcome`

### Из данных класса (если выбран)
| Данные | Источник | Описание |
|--------|----------|----------|
| Количество учеников | `ClassStudent` | Общее число |
| Mastery A (mastered) | `ParagraphMastery.status` | score >= 85% |
| Mastery B (progressing) | `ParagraphMastery.status` | score 60-84% |
| Mastery C (struggling) | `ParagraphMastery.status` | score < 60% |
| Средний балл | `ChapterMastery.average_score` | По главе/предмету |
| Проблемные темы | `TeacherAnalyticsService` | Темы с >30% в уровне C |
| Самооценка | `ParagraphSelfAssessment` | understood/questions/difficult |

---

## 3. Формат выходного документа (QMJ)

### 3.1 Заголовочная таблица

```
| Бөлім (раздел)          | {chapter.number}-бөлім: {chapter.title}          |
| Педагогтің аты-жөні     | {teacher.name}                                    |
| Күні                    | {date}                                            |
| Сыныбы                  | {class.name}                                      |
| Сабақтың тақырыбы       | {paragraph.title}                                 |
| Оқу мақсаты             | {paragraph.learning_objective}                    |
| Сабақтың мақсаты        | {paragraph.lesson_objective}                      |
| Құндылық (ценность)     | {monthly_value} — {value_decomposition}           |
```

### 3.2 Основная таблица (3 этапа)

| Кезең | Уақыт | Содержание |
|-------|-------|------------|
| **Сабақтың басы** (Қызығушылықты ояту) | 5-7 мин | Мотивация, связь с предыдущей темой, активация знаний |
| **Сабақтың ортасы** (Мағынаны ашу) | 25-30 мин | 2-4 задания с дескрипторами, дифференциация |
| **Сабақтың соңы** (Ой толғаныс / Рефлексия) | 5-7 мин | Рефлексия, оценивание, обратная связь |

Каждый этап содержит:
- **Педагогтің іс-әрекеті** — действия учителя
- **Оқушының іс-әрекеті** — действия учеников
- **Бағалау** — критерии оценивания (дескрипторы, баллы)
- **Саралау** — дифференциация по уровням A/B/C
- **Ресурстар** — необходимые ресурсы

### 3.3 Нижний блок

- Саралау (общий подход к дифференциации)
- Бағалау (общий подход к оцениванию)
- Денсаулық және қауіпсіздік (здоровье и безопасность)
- Жалпы бағалау / Рефлексия учителя (2 пустых поля)

### 3.4 Таксономия Блума (БЛУМ таксономиясы)

Задания в QMJ должны покрывать разные когнитивные уровни по Блуму. Глаголы-действия из таксономии используются в формулировках заданий и дескрипторов.

**Пирамида уровней (от низшего к высшему):**

| Деңгей | Уровень | Глаголы-действия (қазақша) | Примеры заданий |
|--------|---------|---------------------------|-----------------|
| **1. Білім** | Знание | Анықта, қайтала, белгіле, атап шық, еске түсір, астын сыз | Терминдерді анықта, негізгі ұғымдарды атап шық |
| **2. Түсіну** | Понимание | Аудар, суретте, түсіндір, баянда, орнына қой, әңгімеле | Мәтінді өз сөзімен баянда, мағынасын түсіндір |
| **3. Қолдану** | Применение | Қолдан, пайдалан, ойнап көрсет, практикада қолдан, суретін сал, бейнеле | Формуланы практикада қолдан, мысал келтір |
| **4. Талдау** | Анализ | Бөліп көрсет, эксперимент жаса, тест жаса, салыстыр, қарама-қарсы қой, сына, диаграмма жаса, категорияға бөл | Кейіпкерлерді салыстыр, себеп-салдарын талда |
| **5. Шығару (Синтез)** | Создание | Жоспарла, ұсын, қондыр, жинақта, теріп ал, құрастыр, ұйымдастыр, дайында | Жоспар құрастыр, жаңа шешім ұсын, эссе жаз |
| **6. Бағалау** | Оценка | Өлше, бағала, рейтинг жаса, салыстыр, қайта қарастыр, таңдап ал, орнына қой | Пікірін негізде, шешімді бағала, таңдауын дәлелде |

**Правила использования в QMJ:**
- Этап "Сабақтың басы" — уровни 1-2 (Білім, Түсіну): активация знаний, вспоминание
- Этап "Сабақтың ортасы" — уровни 3-5 (Қолдану, Талдау, Шығару): основные задания
- Этап "Сабақтың соңы" — уровень 6 (Бағалау): рефлексия, самооценка
- Дескрипторы заданий формулируются через глаголы соответствующего уровня
- Дифференциация по A/B/C: уровень C — Білім/Түсіну, уровень B — Қолдану/Талдау, уровень A — Шығару/Бағалау

**Для промпта LLM:** Таксономия включается в system prompt как справочник, чтобы AI использовал правильные глаголы при формулировке заданий и дескрипторов.

---

## 4. Техническая архитектура

### 4.1 Общая схема

```
Teacher App (Next.js)
    │
    │  POST /api/v1/teachers/lesson-plans/generate
    │  { paragraph_id, class_id?, language, duration_min }
    ▼
API Layer (teachers_lesson_plans.py)
    │  - require_teacher
    │  - get_current_user_school_id
    │  - Проверка доступа к параграфу
    │  - Загрузка mastery данных (если class_id)
    ▼
LessonPlanService (lesson_plan_service.py)
    │  1. Собирает контекст: metadata + content + mastery
    │  2. Строит промпт из шаблона QMJ
    │  3. Вызывает LLMService.generate()
    │  4. Парсит JSON ответ
    │  5. Валидирует структуру
    ▼
LLMService (llm_service.py) — уже существует
    │  Cerebras (primary) → OpenRouter (fallback) → OpenAI (fallback)
    ▼
LessonPlanResponse → JSON → Teacher App → Отображение / Export DOCX
```

### 4.2 Решение: один вызов LLM (не цепочка агентов)

**Обоснование:**
- План урока — единый документ, все входные данные доступны заранее
- Один вызов: ~5-10 сек. Цепочка: ~20-30 сек
- Качество определяется промптом, а не количеством вызовов
- Цепочку агентов можно добавить в V2 для проверки качества

### 4.3 Выбор модели

- **Primary:** Cerebras `llama-3.3-70b` — быстрый, бесплатный, достаточно умный для структурированного плана
- **Fallback:** OpenRouter → OpenAI GPT-4
- `max_tokens: 4000` (план урока ~2000-3000 токенов)
- `temperature: 0.7` (креативность в методах, но структура стабильна)

---

## 5. Backend: детальная спецификация

### 5.1 Pydantic Schemas

**Файл:** `backend/app/schemas/lesson_plan.py`

```python
# --- REQUEST ---

class LessonPlanGenerateRequest(BaseModel):
    paragraph_id: int
    class_id: Optional[int] = None        # Если не указан — план без дифференциации
    language: str = "kk"                   # kk | ru
    duration_min: int = 40                 # 40 | 45 | 80 (спаренный)

# --- RESPONSE ---

class LessonPlanHeader(BaseModel):
    section: str                           # "3-бөлім: Ғасырлық туынды"
    topic: str                             # Тема урока
    learning_objective: str                # Оқу мақсаты (из ГОСО)
    lesson_objective: str                  # Сабақ мақсаты
    monthly_value: str                     # Құндылық месяца
    value_decomposition: str               # Декомпозиция ценности

class TaskDescriptor(BaseModel):
    text: str                              # Текст дескриптора
    score: int                             # Балл за критерий

class LessonTask(BaseModel):
    number: int                            # Номер задания
    teacher_activity: str                  # Действия учителя
    student_activity: str                  # Действия учеников
    descriptors: list[TaskDescriptor]      # Критерии оценки
    total_score: int                       # Общий балл за задание

class LessonStage(BaseModel):
    name: str                              # "Сабақтың басы" и т.д.
    name_detail: str                       # "Қызығушылықты ояту"
    duration_min: int                      # Продолжительность
    method_name: str                       # Название метода ("Гүлмен тілек", etc.)
    method_purpose: str                    # Цель метода
    method_effectiveness: str              # Тиімділігі
    teacher_activity: str                  # Педагогтің іс-әрекеті
    student_activity: str                  # Оқушының іс-әрекеті
    assessment: str                        # Бағалау
    differentiation: Optional[str] = None  # Саралау (если есть данные класса)
    resources: str                         # Ресурстар
    tasks: list[LessonTask] = []           # Задания (для этапа "ортасы")

class DifferentiationBlock(BaseModel):
    approach: str                          # Общий подход
    for_level_a: str                       # Для продвинутых
    for_level_b: str                       # Для средних
    for_level_c: str                       # Для отстающих

class LessonPlanResponse(BaseModel):
    header: LessonPlanHeader
    stages: list[LessonStage]             # 3 этапа
    total_score: int                       # Общий балл за урок
    differentiation: Optional[DifferentiationBlock] = None
    health_safety: str                     # Денсаулық және қауіпсіздік
    reflection_template: list[str]         # Шаблоны для рефлексии учителя

class LessonPlanGenerateResponse(BaseModel):
    lesson_plan: LessonPlanResponse
    context: LessonPlanContext

class LessonPlanContext(BaseModel):
    paragraph_title: str
    chapter_title: str
    textbook_title: str
    subject: str
    grade_level: int
    mastery_distribution: Optional[dict] = None  # {"A": 8, "B": 12, "C": 5}
    total_students: Optional[int] = None
    struggling_topics: Optional[list[str]] = None
```

### 5.2 Service

**Файл:** `backend/app/services/lesson_plan_service.py`

```
class LessonPlanService:
    def __init__(self, db: AsyncSession, llm_service: LLMService):
        ...

    async def generate(
        self,
        paragraph_id: int,
        school_id: int,
        teacher_id: int,
        class_id: Optional[int],
        language: str,
        duration_min: int
    ) -> LessonPlanGenerateResponse:
        """
        1. Загрузить метаданные параграфа (get_content_metadata)
        2. Загрузить контент параграфа (content, key_terms, questions, learning/lesson objectives)
        3. Загрузить ParagraphContent для нужного языка (explain_text, cards)
        4. Загрузить ГОСО learning outcomes (paragraph_outcomes)
        5. Если class_id:
           a. Проверить доступ учителя к классу (ClassTeacher)
           b. Загрузить список учеников класса
           c. Загрузить ParagraphMastery для каждого ученика по этому параграфу
           d. Рассчитать распределение A/B/C
           e. Загрузить struggling topics из TeacherAnalyticsService
        6. Определить monthly_value по текущему месяцу
        7. Собрать промпт (system + user)
        8. Вызвать LLMService.generate()
        9. Распарсить JSON ответ (parse_json_object)
        10. Валидировать через Pydantic schema
        11. Вернуть LessonPlanGenerateResponse
        """
```

**Методы:**

| Метод | Назначение |
|-------|-----------|
| `_collect_paragraph_context()` | Загрузка всех данных о параграфе |
| `_collect_class_context()` | Загрузка данных о классе и mastery |
| `_calculate_mastery_distribution()` | Подсчёт A/B/C из ParagraphMastery |
| `_get_monthly_value()` | Ценность текущего месяца (из справочника) |
| `_build_system_prompt()` | System prompt для LLM |
| `_build_user_prompt()` | User prompt с контекстом |
| `_parse_response()` | Парсинг JSON + валидация |

### 5.3 Промпт

**System Prompt:**
```
Ты — опытный методист-педагог Казахстана с 20-летним стажем.
Твоя задача — составить Қысқамерзімді жоспар (КМЖ) по стандарту ГОСО РК.

Требования к плану:
1. Строго следуй формату QMJ (3 этапа: басы / ортасы / соңы)
2. Используй активные методы обучения (проблемное обучение, групповая работа, дискуссия)
3. Для каждого задания укажи дескрипторы с баллами
4. Саралау (дифференциация) — обязательна, если даны уровни учеников
5. Формативное оценивание на каждом этапе
6. Рефлексия в конце (метод + шаблон)
7. Язык ответа: {language}
8. Все названия методов — на казахском языке
9. Задания должны покрывать разные уровни таксономии Блума
10. Дескрипторы формулируй через глаголы соответствующего уровня Блума

ТАКСОНОМИЯ БЛУМА (БЛУМ таксономиясы) — справочник глаголов:
1. Білім (знание): анықта, қайтала, белгіле, атап шық, еске түсір, астын сыз
2. Түсіну (понимание): аудар, суретте, түсіндір, баянда, орнына қой, әңгімеле
3. Қолдану (применение): қолдан, пайдалан, ойнап көрсет, практикада қолдан, суретін сал, бейнеле
4. Талдау (анализ): бөліп көрсет, эксперимент жаса, тест жаса, салыстыр, қарама-қарсы қой, сына, диаграмма жаса, категорияға бөл
5. Шығару/Синтез (создание): жоспарла, ұсын, қондыр, жинақта, теріп ал, құрастыр, ұйымдастыр, дайында
6. Бағалау (оценка): өлше, бағала, рейтинг жаса, салыстыр, қайта қарастыр, таңдап ал, орнына қой

Распределение уровней Блума по этапам урока:
- Сабақтың басы: уровни 1-2 (Білім, Түсіну) — активация знаний
- Сабақтың ортасы: уровни 3-5 (Қолдану, Талдау, Шығару) — основные задания
- Сабақтың соңы: уровень 6 (Бағалау) — рефлексия, самооценка

Саралау по уровням учеников через Блума:
- C деңгей (struggling): Білім, Түсіну — простые задания на знание и понимание
- B деңгей (progressing): Қолдану, Талдау — задания на применение и анализ
- A деңгей (mastered): Шығару, Бағалау — творческие и оценочные задания

Верни ответ СТРОГО в JSON формате (без markdown обёртки).
```

**User Prompt (шаблон):**
```
Составь QMJ для следующего урока:

КОНТЕКСТ:
- Пән (предмет): {subject}
- Сынып (класс): {grade_level}
- Оқулық (учебник): {textbook_title}
- Бөлім (раздел): {chapter.number}-бөлім: {chapter.title}
- Тақырып (тема): {paragraph.title}
- Сабақ ұзақтығы: {duration_min} минут

МАҚСАТТАР:
- Оқу бағдарламасына сәйкес оқу мақсаты: {learning_objective}
- Сабақтың мақсаты: {lesson_objective}

МАЗМҰНЫ (кратко):
{content[:3000]}

НЕГІЗГІ ҰҒЫМДАР:
{key_terms}

СҰРАҚТАР:
{questions}

--- ЕСЛИ ВЫБРАН КЛАСС ---
СЫНЫП ДЕРЕКТЕРІ:
- Оқушылар саны: {total_students}
- A деңгей (mastered, ≥85%): {count_a} оқушы ({percent_a}%)
- B деңгей (progressing, 60-84%): {count_b} оқушы ({percent_b}%)
- C деңгей (struggling, <60%): {count_c} оқушы ({percent_c}%)
- Орташа балл: {average_score}%
- Қиын тақырыптар: {struggling_topics}

Саралау бөлімінде A/B/C деңгейлеріне арнайы тапсырмалар мен
қолдау түрлерін көрсет.
--- КОНЕЦ БЛОКА КЛАССА ---

Құндылық (айдың құндылығы): {monthly_value}
Құндылық декомпозициясы: {value_decomposition}

JSON ФОРМАТ:
{json_schema_example}
```

### 5.4 API Endpoint

**Файл:** `backend/app/api/v1/teachers_lesson_plans.py`

```python
router = APIRouter(prefix="/teachers/lesson-plans", tags=["Teachers - Lesson Plans"])

@router.post("/generate", response_model=LessonPlanGenerateResponse)
async def generate_lesson_plan(
    request: LessonPlanGenerateRequest,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Генерация QMJ (қысқамерзімді жоспар) по параграфу."""
    service = LessonPlanService(db, LLMService())
    return await service.generate(
        paragraph_id=request.paragraph_id,
        school_id=school_id,
        teacher_id=current_user.teacher.id,
        class_id=request.class_id,
        language=request.language,
        duration_min=request.duration_min,
    )
```

**Регистрация в `main.py`:**
```python
from app.api.v1 import teachers_lesson_plans

app.include_router(
    teachers_lesson_plans.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Lesson Plans"]
)
```

### 5.5 Справочник ценностей месяца

Захардкоженный dict (или в БД позже):

```python
MONTHLY_VALUES = {
    1:  {"kk": "Заң мен тәртіп", "ru": "Закон и порядок",
         "decomposition_kk": "Қиын жағдайларда басқаларға көмектесуге дайын болу"},
    2:  {"kk": "Отбасы", "ru": "Семья", ...},
    3:  {"kk": "Наурыз — жаңару", "ru": "Наурыз — обновление", ...},
    4:  {"kk": "Еңбек пен шығармашылық", "ru": "Труд и творчество", ...},
    5:  {"kk": "Отан", "ru": "Родина", ...},
    9:  {"kk": "Білім", "ru": "Знание", ...},
    10: {"kk": "Денсаулық", "ru": "Здоровье", ...},
    11: {"kk": "Достық пен ынтымақтастық", "ru": "Дружба и сотрудничество", ...},
    12: {"kk": "Тәуелсіздік", "ru": "Независимость", ...},
}
```

---

## 6. Frontend: Teacher App

### 6.1 Новая страница

**URL:** `/lesson-plans/create`

**Расположение:** `teacher-app/src/app/[locale]/(dashboard)/lesson-plans/create/page.tsx`

### 6.2 UI компоненты

```
┌──────────────────────────────────────────────────────┐
│  Сабақ жоспарын құру                                 │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Оқулық:    [▼ Алгебра 9 сынып, 1-бөлім       ] │ │
│  │ Бөлім:     [▼ 1-бөлім: Функциялар             ] │ │
│  │ Параграф:  [▼ §3. Сызықтық функция            ] │ │
│  │ Сынып:     [▼ 9А (необязательно)              ] │ │
│  │ Тіл:       [▼ Қазақша                         ] │ │
│  │ Ұзақтығы:  [▼ 40 мин                          ] │ │
│  │                                                  │ │
│  │           [ Жоспар құру ▶ ]                      │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ Mastery Distribution (если выбран класс) ──────┐ │
│  │  A (mastered):    ████████ 8 (32%)              │ │
│  │  B (progressing): ████████████ 12 (48%)         │ │
│  │  C (struggling):  █████ 5 (20%)                 │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ Сабақ жоспары ─────────────────────────────────┐ │
│  │  (Сгенерированный план в формате таблицы)       │ │
│  │                                                  │ │
│  │  [Қайта құру 🔄]  [DOCX жүктеу 📥]  [PDF 📥]   │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 6.3 API Client

**Файл:** `teacher-app/src/lib/api/lesson-plans.ts`

```typescript
import { apiClient } from './client';

export interface LessonPlanGenerateRequest {
  paragraph_id: number;
  class_id?: number;
  language: string;
  duration_min: number;
}

export async function generateLessonPlan(
  data: LessonPlanGenerateRequest
): Promise<LessonPlanGenerateResponse> {
  const response = await apiClient.post('/teachers/lesson-plans/generate', data);
  return response.data;
}
```

### 6.4 React Hook

**Файл:** `teacher-app/src/lib/hooks/use-lesson-plans.ts`

```typescript
import { useMutation } from '@tanstack/react-query';
import { generateLessonPlan } from '../api/lesson-plans';

export function useGenerateLessonPlan() {
  return useMutation({
    mutationFn: generateLessonPlan,
    // onSuccess, onError handlers
  });
}
```

---

## 7. План реализации по этапам

### Этап 1: MVP Backend (2-3 дня)

**Цель:** Рабочий API endpoint, генерирующий план урока.

| # | Задача | Файл | Зависимости |
|---|--------|------|-------------|
| 1.1 | Создать Pydantic schemas | `backend/app/schemas/lesson_plan.py` | — |
| 1.2 | Создать LessonPlanService | `backend/app/services/lesson_plan_service.py` | schemas, llm_service, paragraph_repo |
| 1.3 | Реализовать сбор контекста параграфа | lesson_plan_service.py | paragraph_repo.get_content_metadata() |
| 1.4 | Реализовать сбор mastery данных класса | lesson_plan_service.py | ParagraphMastery, ClassStudent |
| 1.5 | Написать system + user промпты | lesson_plan_service.py | Шаблон QMJ |
| 1.6 | Реализовать парсинг JSON ответа | lesson_plan_service.py | json_parser.parse_json_object() |
| 1.7 | Создать API endpoint | `backend/app/api/v1/teachers_lesson_plans.py` | LessonPlanService |
| 1.8 | Зарегистрировать router в main.py | `backend/app/main.py` | — |
| 1.9 | Тестирование через curl/Postman | — | Рабочий backend |

**Критерий готовности:** `POST /api/v1/teachers/lesson-plans/generate` возвращает валидный JSON с планом урока.

### Этап 2: Frontend MVP (2-3 дня)

**Цель:** Страница в Teacher App для генерации и просмотра плана.

| # | Задача | Файл |
|---|--------|------|
| 2.1 | Создать API client функцию | `teacher-app/src/lib/api/lesson-plans.ts` |
| 2.2 | Создать TypeScript типы | `teacher-app/src/types/lesson-plan.ts` |
| 2.3 | Создать React hook | `teacher-app/src/lib/hooks/use-lesson-plans.ts` |
| 2.4 | Создать страницу генерации | `teacher-app/src/app/[locale]/(dashboard)/lesson-plans/create/page.tsx` |
| 2.5 | Каскадные селекты (учебник → раздел → параграф) | Компонент в page.tsx |
| 2.6 | Селект класса с mastery preview | Компонент в page.tsx |
| 2.7 | Отображение плана в табличном формате | Компонент `LessonPlanView` |
| 2.8 | Добавить в навигацию | Sidebar/menu |
| 2.9 | Локализация (kk/ru) | `messages/kk.json`, `messages/ru.json` |

**Критерий готовности:** Учитель может выбрать параграф, нажать "Генерировать", увидеть план.

### Этап 3: Export и сохранение (2-3 дня)

**Цель:** Экспорт в DOCX, сохранение планов в БД.

| # | Задача | Описание |
|---|--------|----------|
| 3.1 | Создать модель `LessonPlan` | Таблица в БД для хранения сгенерированных планов |
| 3.2 | Миграция `036_lesson_plans` | CREATE TABLE lesson_plans |
| 3.3 | CRUD endpoints | GET list, GET by id, DELETE |
| 3.4 | Export в DOCX | Библиотека `python-docx`, шаблон таблицы QMJ |
| 3.5 | Export в PDF | Через `weasyprint` или `reportlab` |
| 3.6 | Страница "Мои планы" | Список сохранённых планов с фильтрами |
| 3.7 | Редактирование плана | Inline editing полей перед экспортом |

### Этап 4: Улучшения (3-5 дней)

**Цель:** Качество генерации, шаблоны, аналитика.

| # | Задача | Описание |
|---|--------|----------|
| 4.1 | Предметные шаблоны промптов | Разные промпты для математики, истории, информатики, литературы |
| 4.2 | Streaming генерации | SSE для отображения плана по мере генерации |
| 4.3 | Шаблоны учителя | Учитель сохраняет свои шаблоны/предпочтения |
| 4.4 | Двухэтапная генерация | Шаг 1: генерация, Шаг 2: AI-проверка качества |
| 4.5 | Учёт истории самооценки | Использование ParagraphSelfAssessment для deeper differentiation |
| 4.6 | Аналитика использования | Сколько планов генерируется, по каким предметам |
| 4.7 | Обратная связь учителя | Лайк/дизлайк + комментарий для улучшения промптов |

---

## 8. Зависимости и ограничения

### Существующие компоненты (переиспользуем)
- `LLMService` — вызов LLM (`backend/app/services/llm_service.py`)
- `ParagraphRepository.get_content_metadata()` — метаданные параграфа
- `parse_json_object()` — парсинг JSON из LLM ответа (`homework/ai/utils/json_parser.py`)
- `require_teacher`, `get_current_user_school_id` — авторизация
- `apiClient` — axios клиент в teacher-app
- `TeacherAnalyticsService` — данные о mastery класса

### Новые зависимости
- `python-docx` — для экспорта в DOCX (этап 3)
- Нет новых npm пакетов (shadcn/ui + React Query уже есть)

### Ограничения
- **Размер контента:** `content[:3000]` для промпта (чтобы не превысить context window)
- **Время генерации:** ~5-10 сек (Cerebras), ~15-20 сек (OpenAI fallback)
- **Качество:** зависит от learning_objective и lesson_objective — если они пустые, план будет generic
- **Mastery данные:** если ученики ещё не проходили параграф, mastery = пустой → план без дифференциации

### Риски
| Риск | Вероятность | Митигация |
|------|------------|-----------|
| LLM возвращает невалидный JSON | Средняя | Retry + fallback на текстовый формат |
| Долгая генерация (>15 сек) | Низкая | Loading state + таймаут 30 сек |
| Некачественный план для редких предметов | Средняя | Предметные шаблоны (этап 4) |
| Пустые learning/lesson objectives | Высокая | Fallback на content + key_terms |

---

## 9. Метрики успеха

| Метрика | Цель |
|---------|------|
| Время генерации | < 10 сек (P95) |
| Успешная генерация | > 95% запросов |
| Использование учителями | > 50% активных учителей пробуют за первую неделю |
| Повторное использование | > 30% учителей генерируют 5+ планов |
| Качество (обратная связь) | > 70% лайков |
