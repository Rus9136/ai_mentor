# План интеграции ГОСО (Государственный общеобязательный стандарт образования)

**Дата создания:** 2025-12-09
**Последнее обновление:** 2025-12-16
**Статус:** ✅ MVP ЗАВЕРШЁН — схема + модели + Pydantic схемы + импорт данных + API endpoints готовы и протестированы.
**Версия документа:** 2.5

---

## Основная цель

Расширить схему базы данных и API платформы AI Mentor для полной поддержки Государственного общеобязательного стандарта образования Республики Казахстан (ГОСО).

**Ключевые задачи:**
1. Нормализовать цели обучения ("Обучающиеся должны...") из ГОСО в отдельные таблицы
2. Создать справочник предметов
3. Хранить структуру долгосрочного плана (юниты, темы, исследовательские вопросы)
4. Связать темы долгосрочного плана с целями обучения ГОСО
5. Связать параграфы учебников с темами и целями ГОСО (M:N)
6. Хранить исторические концепты ГОСО
7. Хранить учебные активности ("Топтық жұмыс", "Жұптық жұмыс", "Тапсырма")
8. Поддержать версионирование стандартов (редакции ГОСО)
9. Обеспечить двуязычность (RU/KZ) для всех новых сущностей

**Пилотный предмет:** История Казахстана (5-9 классы)

**Источник данных:** `docs/adilet_merged.json` (официальная типовая учебная программа доработанная на двух языках)

---

## Scope (MVP vs Target)

### MVP (делаем сейчас)

- **Схема БД**: только global ГОСО + мэппинг параграфов
  - `subjects`, `frameworks`, `goso_sections`, `goso_subsections`, `learning_outcomes`
  - `paragraph_outcomes`
- **Доступ**: ГОСО эндпоинты **не анонимные** (только аутентифицированные роли).
- **Multi-tenant**:
  - global справочники — read-only для школ (write только SUPER_ADMIN),
  - `paragraph_outcomes` — школы могут писать только для своих параграфов (global параграфы — только SUPER_ADMIN).

### Target (после MVP)

- `curriculum_units/topics` и связанные M:N таблицы
- per-school overrides для `curriculum_units/topics`
- `historical_concepts`, `activities`
- Изменения существующих таблиц (`textbooks.subject_id`, `chapters.goso_section_id`, `paragraphs.goso_subsection_id`) — после MVP

---

## Статистика данных для импорта

| Данные | Количество | Источник в JSON |
|--------|------------|-----------------|
| Предмет | 1 | `metadata.subject` |
| Версия ГОСО (framework) | 1 | `metadata.order`, `metadata.amendments` |
| Разделы ГОСО | 4 | `content_organization.sections` |
| Подразделы ГОСО | 9 | `content_organization.sections[].subsections` |
| Цели обучения | 164 | `learning_objectives.all_objectives` |
| Исторические концепты | 6 | `content_organization.historical_concepts` |
| Юниты долгосрочного плана | ~46 | `long_term_plan.{grade}.quarters[].units` |
| Темы уроков | 165 | `long_term_plan.{grade}.quarters[].units[].topics` |
| Исследовательские вопросы | 145 | `long_term_plan...topics[].research_question` |

---

## Архитектура решения

### MVP схема связей (012/013)

```
                                    subjects
                                        │
                                        ▼
                                    frameworks (версия ГОСО)
                                        │
          ▼
    goso_sections
          │
          ▼
   goso_subsections
          │
          ▼
   learning_outcomes
          │
          ▼
   paragraph_outcomes (M:N → paragraphs)
          │
          ▼
      paragraphs
```

### Иерархия данных (MVP)

```
subjects (справочник предметов)
    │
frameworks (версии ГОСО: goso_hist_kz_2023...)
    │
    ├── goso_sections (разделы ГОСО, уровень 1) ─── 4 шт.
    │       │
    │       └── goso_subsections (подразделы, уровень 2) ─── 9 шт.
    │               │
    │               └── learning_outcomes (цели: "5.1.1.1 - Обучающиеся должны...") ─── 164 шт.
    │                       │
    │                       ├── paragraph_outcomes (M:N → paragraphs)

paragraphs (параграфы учебника)
```

### Кодировка целей ГОСО

Формат: `{класс}.{раздел}.{подраздел}.{порядковый_номер}`

Пример: `7.2.1.2`
- `7` - 7 класс
- `2` - раздел 2 (например, "Развитие культуры")
- `1` - подраздел 1 (например, "Мировоззрение и религия")
- `2` - вторая цель в этом подразделе

---

## Таблицы (MVP vs Target)

**MVP (реализовано миграциями 012/013):** таблицы 1–6.  
**Target (отложено):** таблицы 7–12 + изменения существующих таблиц.

### 1. `subjects` - Справочник предметов

```sql
CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,       -- "history_kz", "math", "physics"
    name_ru VARCHAR(255) NOT NULL,          -- "История Казахстана"
    name_kz VARCHAR(255) NOT NULL,          -- "Қазақстан тарихы"
    description_ru TEXT,
    description_kz TEXT,
    grade_from INTEGER NOT NULL DEFAULT 1,  -- С какого класса (1-11)
    grade_to INTEGER NOT NULL DEFAULT 11,   -- По какой класс
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_subjects_code ON subjects(code);
CREATE INDEX ix_subjects_is_active ON subjects(is_active);
```

**Начальные данные:**
```sql
INSERT INTO subjects (code, name_ru, name_kz, grade_from, grade_to) VALUES
('history_kz', 'История Казахстана', 'Қазақстан тарихы', 5, 11),
('history_world', 'Всемирная история', 'Дүниежүзі тарихы', 5, 11),
('math', 'Математика', 'Математика', 1, 6),
('algebra', 'Алгебра', 'Алгебра', 7, 11),
('geometry', 'Геометрия', 'Геометрия', 7, 11),
('physics', 'Физика', 'Физика', 7, 11),
('chemistry', 'Химия', 'Химия', 7, 11),
('biology', 'Биология', 'Биология', 5, 11),
('geography', 'География', 'География', 5, 11),
('kazakh_lang', 'Казахский язык', 'Қазақ тілі', 1, 11),
('russian_lang', 'Русский язык', 'Орыс тілі', 1, 11),
('english_lang', 'Английский язык', 'Ағылшын тілі', 1, 11),
('literature', 'Литература', 'Әдебиет', 5, 11),
('informatics', 'Информатика', 'Информатика', 5, 11);
```

---

### 2. `frameworks` - Версии ГОСО

```sql
CREATE TABLE frameworks (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,      -- "goso_hist_kz_2023_10_31"
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    title_ru VARCHAR(500) NOT NULL,         -- "ГОСО История Казахстана 2023"
    title_kz VARCHAR(500) NOT NULL,
    description_ru TEXT,
    description_kz TEXT,

    -- Нормативные данные
    document_type VARCHAR(255),             -- "Типовая учебная программа"
    order_number VARCHAR(50),               -- "399"
    order_date DATE,                        -- "2022-09-16"
    ministry VARCHAR(500),                  -- "Министерство просвещения РК"
    appendix_number INTEGER,                -- 61

    -- Поправки (JSON массив)
    amendments JSON,                        -- [{"order_number": "467", "date": "2022-11-21"}, ...]

    -- Период действия
    valid_from DATE,
    valid_to DATE,                          -- NULL = бессрочно

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX ix_frameworks_code ON frameworks(code);
CREATE INDEX ix_frameworks_subject_id ON frameworks(subject_id);
CREATE INDEX ix_frameworks_is_active ON frameworks(is_active);
```

---

### 3. `goso_sections` - Разделы ГОСО (уровень 1)

```sql
CREATE TABLE goso_sections (
    id SERIAL PRIMARY KEY,
    framework_id INTEGER NOT NULL REFERENCES frameworks(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,              -- "1", "2", "3", "4"
    name_ru VARCHAR(500) NOT NULL,          -- "Развитие социальных отношений"
    name_kz VARCHAR(500),
    description_ru TEXT,
    description_kz TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(framework_id, code)
);

CREATE INDEX ix_goso_sections_framework_id ON goso_sections(framework_id);
CREATE INDEX ix_goso_sections_display_order ON goso_sections(display_order);
```

**Данные для Истории Казахстана:**
| code | name_ru |
|------|---------|
| 1 | Развитие социальных отношений |
| 2 | Развитие культуры |
| 3 | Развитие государства |
| 4 | Экономическое развитие Казахстана |

---

### 4. `goso_subsections` - Подразделы ГОСО (уровень 2)

```sql
CREATE TABLE goso_subsections (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL REFERENCES goso_sections(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,              -- "1.1", "1.2", "2.1"
    name_ru VARCHAR(500) NOT NULL,          -- "Этнические отношения"
    name_kz VARCHAR(500),
    description_ru TEXT,
    description_kz TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(section_id, code)
);

CREATE INDEX ix_goso_subsections_section_id ON goso_subsections(section_id);
CREATE INDEX ix_goso_subsections_display_order ON goso_subsections(display_order);
```

**Данные для Истории Казахстана:**
| section | code | name_ru |
|---------|------|---------|
| 1 | 1.1 | Этнические отношения |
| 1 | 1.2 | Социальные отношения |
| 2 | 2.1 | Мировоззрение и религия |
| 2 | 2.2 | Искусство и литература |
| 2 | 2.3 | Образование и наука |
| 3 | 3.1 | Внутренняя политика государства |
| 3 | 3.2 | Внешняя политика государства |
| 4 | 4.1 | Хозяйство |
| 4 | 4.2 | Производственные отношения и торговля |

---

### 5. `learning_outcomes` - Цели обучения ГОСО (164 шт.)

```sql
CREATE TABLE learning_outcomes (
    id SERIAL PRIMARY KEY,
    framework_id INTEGER NOT NULL REFERENCES frameworks(id) ON DELETE CASCADE,
    subsection_id INTEGER NOT NULL REFERENCES goso_subsections(id) ON DELETE CASCADE,
    grade INTEGER NOT NULL CHECK (grade BETWEEN 1 AND 11),
    code VARCHAR(20) NOT NULL,              -- "5.1.1.1", "7.2.1.2"

    -- Формулировка цели
    title_ru TEXT NOT NULL,                 -- "описывать антропологические признаки..."
    title_kz TEXT,
    description_ru TEXT,                    -- Развёрнутое описание (опционально)
    description_kz TEXT,

    -- Когнитивный уровень (опционально)
    cognitive_level VARCHAR(50),            -- "знание", "понимание", "применение", "анализ"

    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,

    UNIQUE(framework_id, code)
);

CREATE INDEX ix_learning_outcomes_framework_id ON learning_outcomes(framework_id);
CREATE INDEX ix_learning_outcomes_subsection_id ON learning_outcomes(subsection_id);
CREATE INDEX ix_learning_outcomes_grade ON learning_outcomes(grade);
CREATE INDEX ix_learning_outcomes_code ON learning_outcomes(code);
CREATE INDEX ix_learning_outcomes_is_active ON learning_outcomes(is_active);
```

**Примеры данных:**
| code | grade | title_ru |
|------|-------|----------|
| 5.1.1.1 | 5 | описывать антропологические признаки первобытных людей |
| 5.1.1.2 | 5 | определять антропологический облик людей древнего Казахстана |
| 7.2.1.2 | 7 | объяснять демографические изменения и миграционные процессы... |

---

### 6. `paragraph_outcomes` - Связь параграф ↔ цели ГОСО (M:N)

```sql
CREATE TABLE paragraph_outcomes (
    id SERIAL PRIMARY KEY,
    paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    outcome_id INTEGER NOT NULL REFERENCES learning_outcomes(id) ON DELETE CASCADE,

    -- Уверенность связи (если мэппит AI: 0.0-1.0, вручную: 1.0)
    confidence DECIMAL(3,2) DEFAULT 1.0,

    -- Якорь в тексте (страница, абзац)
    anchor VARCHAR(100),

    -- Комментарий к связи
    notes TEXT,

    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(paragraph_id, outcome_id)
);

CREATE INDEX ix_paragraph_outcomes_paragraph_id ON paragraph_outcomes(paragraph_id);
CREATE INDEX ix_paragraph_outcomes_outcome_id ON paragraph_outcomes(outcome_id);
```

---

### 7. `curriculum_units` - Юниты/разделы долгосрочного плана (~46 шт.)

> Target (после MVP): в MVP не реализуем. В MVP достаточно global ГОСО + `paragraph_outcomes`.

Группировка тем по разделам внутри четверти.

```sql
CREATE TABLE curriculum_units (
    id SERIAL PRIMARY KEY,
    framework_id INTEGER NOT NULL REFERENCES frameworks(id) ON DELETE CASCADE,
    grade INTEGER NOT NULL CHECK (grade BETWEEN 1 AND 11),
    quarter INTEGER NOT NULL CHECK (quarter BETWEEN 1 AND 4),

    -- Название раздела/юнита
    name_ru VARCHAR(500) NOT NULL,          -- "Жизнь древних людей на территории Казахстана"
    name_kz VARCHAR(500),

    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(framework_id, grade, quarter, name_ru)
);

CREATE INDEX ix_curriculum_units_framework_id ON curriculum_units(framework_id);
CREATE INDEX ix_curriculum_units_grade ON curriculum_units(grade);
CREATE INDEX ix_curriculum_units_quarter ON curriculum_units(quarter);
CREATE INDEX ix_curriculum_units_grade_quarter ON curriculum_units(grade, quarter);
```

**Примеры данных (5 класс):**
| grade | quarter | name_ru |
|-------|---------|---------|
| 5 | 1 | Жизнь древних людей на территории Казахстана |
| 5 | 1 | Краеведение |
| 5 | 2 | Жизнь древних кочевников |
| 5 | 2 | Краеведение |
| 5 | 3 | Усуни и кангюи |

---

### 8. `curriculum_topics` - Темы уроков (165 шт.)

> Target (после MVP)

```sql
CREATE TABLE curriculum_topics (
    id SERIAL PRIMARY KEY,
    unit_id INTEGER NOT NULL REFERENCES curriculum_units(id) ON DELETE CASCADE,

    -- Название темы
    title_ru VARCHAR(500) NOT NULL,         -- "Жизнь древнейших людей"
    title_kz VARCHAR(500),

    -- Исследовательский вопрос урока
    research_question_ru TEXT,              -- "Как жили древнейшие люди?"
    research_question_kz TEXT,

    -- Рекомендуемое количество часов
    recommended_hours INTEGER DEFAULT 1,

    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX ix_curriculum_topics_unit_id ON curriculum_topics(unit_id);
CREATE INDEX ix_curriculum_topics_display_order ON curriculum_topics(display_order);
```

**Примеры данных:**
| unit_id | title_ru | research_question_ru |
|---------|----------|---------------------|
| 1 | Вводный урок | Что изучает история древнего Казахстана? |
| 1 | Жизнь древнейших людей | Как жили древнейшие люди? |
| 1 | Стоянки эпохи камня на территории Казахстана | Какие находки эпохи камня были обнаружены археологами? |
| 1 | Ботайская культура | Почему ботайцы считаются первыми людьми, приручившими лошадей? |

---

### 9. `curriculum_topic_outcomes` - Связь тема ↔ цели ГОСО (M:N)

> Target (после MVP)

```sql
CREATE TABLE curriculum_topic_outcomes (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES curriculum_topics(id) ON DELETE CASCADE,
    outcome_id INTEGER NOT NULL REFERENCES learning_outcomes(id) ON DELETE CASCADE,

    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(topic_id, outcome_id)
);

CREATE INDEX ix_curriculum_topic_outcomes_topic_id ON curriculum_topic_outcomes(topic_id);
CREATE INDEX ix_curriculum_topic_outcomes_outcome_id ON curriculum_topic_outcomes(outcome_id);
```

**Примеры данных:**
| topic_id | outcome_id (code) | display_order |
|----------|-------------------|---------------|
| 2 (Жизнь древнейших людей) | 1 (5.1.1.1) | 1 |
| 2 (Жизнь древнейших людей) | 15 (5.1.2.1) | 2 |
| 3 (Стоянки эпохи камня) | 45 (5.2.3.1) | 1 |
| 3 (Стоянки эпохи камня) | 46 (5.2.2.1) | 2 |

---

### 10. `paragraph_curriculum_topics` - Связь параграф ↔ темы (M:N)

> Target (после MVP)

```sql
CREATE TABLE paragraph_curriculum_topics (
    id SERIAL PRIMARY KEY,
    paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES curriculum_topics(id) ON DELETE CASCADE,

    -- Насколько параграф покрывает тему (0.0-1.0)
    coverage DECIMAL(3,2) DEFAULT 1.0,

    -- Комментарий
    notes TEXT,                             -- "основная тема", "дополнительный материал"

    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(paragraph_id, topic_id)
);

CREATE INDEX ix_paragraph_curriculum_topics_paragraph_id ON paragraph_curriculum_topics(paragraph_id);
CREATE INDEX ix_paragraph_curriculum_topics_topic_id ON paragraph_curriculum_topics(topic_id);
```

---

### 11. `historical_concepts` - Исторические концепты (6 шт.)

> Target (после MVP)

```sql
CREATE TABLE historical_concepts (
    id SERIAL PRIMARY KEY,
    framework_id INTEGER NOT NULL REFERENCES frameworks(id) ON DELETE CASCADE,

    name_ru VARCHAR(255) NOT NULL,          -- "Изменение и преемственность"
    name_kz VARCHAR(255),

    -- Ожидаемые результаты
    expected_outcomes_ru TEXT,              -- "анализировать и оценивать исторические примеры..."
    expected_outcomes_kz TEXT,

    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_historical_concepts_framework_id ON historical_concepts(framework_id);
```

**Данные для Истории Казахстана:**
| name_ru | expected_outcomes_ru |
|---------|---------------------|
| Изменение и преемственность | анализировать и оценивать исторические примеры непрерывности и изменения во времени и пространстве |
| Причина и следствие | анализировать и оценивать взаимодействие нескольких причин и влияний, понимать историческую обусловленность |
| Доказательство | анализировать особенности исторического источника, делать обоснованные заключения и выводы |
| Сходство и различия | сравнивать связанные исторические события и процессы в различных обществах |
| Значимость | определять значимость исторического события, явления, процесса для развития общества |
| Интерпретация | объяснять и оценивать различные точки зрения на историческое событие |

---

### 12. `activities` - Учебные активности

> Target (после MVP)

```sql
CREATE TYPE activity_category AS ENUM (
    'group_work',       -- Топтық жұмыс
    'pair_work',        -- Жұптық жұмыс
    'individual_task',  -- Тапсырма / Жеке жұмыс
    'discussion',       -- Талқылау / Обсуждение
    'research',         -- Зерттеу / Исследование
    'project',          -- Жоба / Проект
    'presentation',     -- Презентация
    'role_play',        -- Рөлдік ойын
    'other'             -- Басқа / Другое
);

CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    outcome_id INTEGER REFERENCES learning_outcomes(id) ON DELETE SET NULL,

    category activity_category NOT NULL,
    title_ru VARCHAR(500),
    title_kz VARCHAR(500),
    body_ru TEXT NOT NULL,                  -- Описание/инструкция
    body_kz TEXT,

    duration_minutes INTEGER,               -- Примерное время выполнения
    display_order INTEGER NOT NULL DEFAULT 0,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX ix_activities_paragraph_id ON activities(paragraph_id);
CREATE INDEX ix_activities_outcome_id ON activities(outcome_id);
CREATE INDEX ix_activities_category ON activities(category);
CREATE INDEX ix_activities_display_order ON activities(display_order);
```

---

## Изменения существующих таблиц

> Target (после MVP): в MVP не меняем `textbooks/chapters/paragraphs`, чтобы не усложнять и не ломать текущий контент-флоу.

### Таблица `textbooks`

```sql
-- Добавить FK на справочник предметов
ALTER TABLE textbooks
ADD COLUMN subject_id INTEGER REFERENCES subjects(id);

CREATE INDEX ix_textbooks_subject_id ON textbooks(subject_id);

-- Старое поле subject (VARCHAR) оставляем на переходный период
```

### Таблица `chapters`

```sql
-- Добавить связь с разделом ГОСО
ALTER TABLE chapters
ADD COLUMN goso_section_id INTEGER REFERENCES goso_sections(id) ON DELETE SET NULL;

CREATE INDEX ix_chapters_goso_section_id ON chapters(goso_section_id);
```

### Таблица `paragraphs`

```sql
-- Добавить связь с подразделом ГОСО
ALTER TABLE paragraphs
ADD COLUMN goso_subsection_id INTEGER REFERENCES goso_subsections(id) ON DELETE SET NULL;

CREATE INDEX ix_paragraphs_goso_subsection_id ON paragraphs(goso_subsection_id);
```

---

## Этапы реализации

### MVP (012/013 + импорт + API)
**Приоритет:** Высокий | **Сложность:** Средняя

**Этап 1 — Схема (готово):**
- ✅ Миграция `012_add_goso_core_tables.py`:
  - `subjects`, `frameworks`, `goso_sections`, `goso_subsections`, `learning_outcomes`
  - RLS: global read, write только SUPER_ADMIN
- ✅ Миграция `013_add_paragraph_outcomes.py`:
  - `paragraph_outcomes`
  - RLS: школы пишут только для своих параграфов, global параграфы — только SUPER_ADMIN

**Этап 2 — Импорт (готово):**
- ✅ Скрипт импорта из `docs/adilet_merged.json` (global данные по ГОСО на двух языках)
- ✅ Импортирован пилот: История Казахстана 5–9 (1 framework, 4 sections, 9 subsections, 164 outcomes)

**Этап 3 — API (готово):**
- ✅ Все эндпоинты **только для аутентифицированных пользователей** (НЕ public/anonymous)
- ✅ `/api/v1/goso/*` — read-only endpoints для subjects/frameworks/outcomes
- ✅ `/api/v1/admin/global/paragraphs/{id}/outcomes` — CRUD для SUPER_ADMIN (маппинг paragraph↔outcome)
- ✅ `/api/v1/admin/school/paragraphs/{id}/outcomes` — CRUD для School ADMIN (маппинг paragraph↔outcome)

### Target (после MVP)
- `curriculum_units/topics` + связи и отчёты покрытия
- `historical_concepts`, `activities`
- UI админки для управления долгосрочным планом и активностями
- Изменения существующих таблиц (`subject_id`, `goso_section_id`, `goso_subsection_id`)

---

## Порядок миграций

```
MVP:
  Миграция 012: subjects + frameworks + goso_sections + goso_subsections + learning_outcomes (+ RLS)
  Миграция 013: paragraph_outcomes (+ RLS)

Target:
  014+: curriculum_units/topics + связи
  015+: historical_concepts
  016+: activities
```

---

## Примеры SQL запросов

### 1. Найти все темы для 7 класса, 2 четверти:
```sql
SELECT ct.title_ru, ct.research_question_ru
FROM curriculum_topics ct
JOIN curriculum_units cu ON ct.unit_id = cu.id
WHERE cu.grade = 7 AND cu.quarter = 2
ORDER BY cu.display_order, ct.display_order;
```

### 2. Найти все цели обучения для темы:
```sql
SELECT lo.code, lo.title_ru
FROM learning_outcomes lo
JOIN curriculum_topic_outcomes cto ON lo.id = cto.outcome_id
WHERE cto.topic_id = 123
ORDER BY cto.display_order;
```

### 3. Найти параграфы учебника по теме долгосрочного плана:
```sql
SELECT p.title, p.number, t.title as textbook
FROM paragraphs p
JOIN paragraph_curriculum_topics pct ON p.id = pct.paragraph_id
JOIN chapters c ON p.chapter_id = c.id
JOIN textbooks t ON c.textbook_id = t.id
WHERE pct.topic_id = 123;
```

### 4. Проверить покрытие учебником долгосрочного плана:
```sql
SELECT
    ct.title_ru as topic,
    COUNT(pct.paragraph_id) as paragraphs_count,
    CASE WHEN COUNT(pct.paragraph_id) > 0 THEN 'Покрыто' ELSE 'Не покрыто' END as status
FROM curriculum_topics ct
LEFT JOIN paragraph_curriculum_topics pct ON ct.id = pct.topic_id
GROUP BY ct.id
ORDER BY ct.id;
```

### 5. Получить полную структуру ГОСО для класса:
```sql
SELECT
    gs.code as section_code,
    gs.name_ru as section_name,
    gss.code as subsection_code,
    gss.name_ru as subsection_name,
    lo.code as outcome_code,
    lo.title_ru as outcome_title
FROM learning_outcomes lo
JOIN goso_subsections gss ON lo.subsection_id = gss.id
JOIN goso_sections gs ON gss.section_id = gs.id
WHERE lo.grade = 7
ORDER BY gs.display_order, gss.display_order, lo.display_order;
```

---

## SQLAlchemy модели

### `backend/app/models/subject.py`

```python
"""Subject model."""
from sqlalchemy import Column, String, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Subject(BaseModel):
    """Subject (предмет) model."""

    __tablename__ = "subjects"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name_ru = Column(String(255), nullable=False)
    name_kz = Column(String(255), nullable=False)
    description_ru = Column(Text, nullable=True)
    description_kz = Column(Text, nullable=True)
    grade_from = Column(Integer, default=1, nullable=False)
    grade_to = Column(Integer, default=11, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    frameworks = relationship("Framework", back_populates="subject")
    textbooks = relationship("Textbook", back_populates="subject_ref")

    def __repr__(self) -> str:
        return f"<Subject(id={self.id}, code='{self.code}', name='{self.name_ru}')>"
```

### `backend/app/models/goso.py`

```python
"""GOSO (State Educational Standard) models."""
import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Text, Date, Numeric, JSON, Enum
from sqlalchemy.orm import relationship
from app.models.base import SoftDeleteModel, BaseModel


class Framework(SoftDeleteModel):
    """Framework (версия ГОСО) model."""

    __tablename__ = "frameworks"

    code = Column(String(100), unique=True, nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    title_ru = Column(String(500), nullable=False)
    title_kz = Column(String(500), nullable=True)
    description_ru = Column(Text, nullable=True)
    description_kz = Column(Text, nullable=True)

    # Нормативные данные
    document_type = Column(String(255), nullable=True)
    order_number = Column(String(50), nullable=True)
    order_date = Column(Date, nullable=True)
    ministry = Column(String(500), nullable=True)
    appendix_number = Column(Integer, nullable=True)
    amendments = Column(JSON, nullable=True)

    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    subject = relationship("Subject", back_populates="frameworks")
    sections = relationship("GosoSection", back_populates="framework", cascade="all, delete-orphan")
    outcomes = relationship("LearningOutcome", back_populates="framework", cascade="all, delete-orphan")
    curriculum_units = relationship("CurriculumUnit", back_populates="framework", cascade="all, delete-orphan")
    historical_concepts = relationship("HistoricalConcept", back_populates="framework", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Framework(id={self.id}, code='{self.code}')>"


class GosoSection(BaseModel):
    """GOSO Section (раздел) model."""

    __tablename__ = "goso_sections"

    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name_ru = Column(String(500), nullable=False)
    name_kz = Column(String(500), nullable=True)
    description_ru = Column(Text, nullable=True)
    description_kz = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    framework = relationship("Framework", back_populates="sections")
    subsections = relationship("GosoSubsection", back_populates="section", cascade="all, delete-orphan")
    chapters = relationship("Chapter", back_populates="goso_section")

    def __repr__(self) -> str:
        return f"<GosoSection(id={self.id}, code='{self.code}', name='{self.name_ru}')>"


class GosoSubsection(BaseModel):
    """GOSO Subsection (подраздел) model."""

    __tablename__ = "goso_subsections"

    section_id = Column(Integer, ForeignKey("goso_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name_ru = Column(String(500), nullable=False)
    name_kz = Column(String(500), nullable=True)
    description_ru = Column(Text, nullable=True)
    description_kz = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    section = relationship("GosoSection", back_populates="subsections")
    outcomes = relationship("LearningOutcome", back_populates="subsection")
    paragraphs = relationship("Paragraph", back_populates="goso_subsection")

    def __repr__(self) -> str:
        return f"<GosoSubsection(id={self.id}, code='{self.code}', name='{self.name_ru}')>"


class LearningOutcome(SoftDeleteModel):
    """Learning Outcome (цель обучения ГОСО) model."""

    __tablename__ = "learning_outcomes"

    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False, index=True)
    subsection_id = Column(Integer, ForeignKey("goso_subsections.id", ondelete="CASCADE"), nullable=False, index=True)
    grade = Column(Integer, nullable=False, index=True)
    code = Column(String(20), nullable=False, index=True)
    title_ru = Column(Text, nullable=False)
    title_kz = Column(Text, nullable=True)
    description_ru = Column(Text, nullable=True)
    description_kz = Column(Text, nullable=True)
    cognitive_level = Column(String(50), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    framework = relationship("Framework", back_populates="outcomes")
    subsection = relationship("GosoSubsection", back_populates="outcomes")
    paragraph_links = relationship("ParagraphOutcome", back_populates="outcome", cascade="all, delete-orphan")
    topic_links = relationship("CurriculumTopicOutcome", back_populates="outcome", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="outcome")

    def __repr__(self) -> str:
        return f"<LearningOutcome(id={self.id}, code='{self.code}')>"


class ParagraphOutcome(BaseModel):
    """Paragraph-Outcome M:N link table."""

    __tablename__ = "paragraph_outcomes"

    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)
    outcome_id = Column(Integer, ForeignKey("learning_outcomes.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence = Column(Numeric(3, 2), default=1.0)
    anchor = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    paragraph = relationship("Paragraph", back_populates="outcome_links")
    outcome = relationship("LearningOutcome", back_populates="paragraph_links")
    creator = relationship("User")

    def __repr__(self) -> str:
        return f"<ParagraphOutcome(paragraph_id={self.paragraph_id}, outcome_id={self.outcome_id})>"


class HistoricalConcept(BaseModel):
    """Historical Concept model."""

    __tablename__ = "historical_concepts"

    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False, index=True)
    name_ru = Column(String(255), nullable=False)
    name_kz = Column(String(255), nullable=True)
    expected_outcomes_ru = Column(Text, nullable=True)
    expected_outcomes_kz = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    framework = relationship("Framework", back_populates="historical_concepts")

    def __repr__(self) -> str:
        return f"<HistoricalConcept(id={self.id}, name='{self.name_ru}')>"
```

### `backend/app/models/curriculum.py`

```python
"""Curriculum (долгосрочный план) models."""
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Text, Numeric
from sqlalchemy.orm import relationship
from app.models.base import SoftDeleteModel, BaseModel


class CurriculumUnit(BaseModel):
    """Curriculum Unit (юнит/раздел долгосрочного плана) model."""

    __tablename__ = "curriculum_units"

    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False, index=True)
    grade = Column(Integer, nullable=False, index=True)
    quarter = Column(Integer, nullable=False, index=True)
    name_ru = Column(String(500), nullable=False)
    name_kz = Column(String(500), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    framework = relationship("Framework", back_populates="curriculum_units")
    topics = relationship("CurriculumTopic", back_populates="unit", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CurriculumUnit(id={self.id}, grade={self.grade}, quarter={self.quarter}, name='{self.name_ru}')>"


class CurriculumTopic(SoftDeleteModel):
    """Curriculum Topic (тема урока) model."""

    __tablename__ = "curriculum_topics"

    unit_id = Column(Integer, ForeignKey("curriculum_units.id", ondelete="CASCADE"), nullable=False, index=True)
    title_ru = Column(String(500), nullable=False)
    title_kz = Column(String(500), nullable=True)
    research_question_ru = Column(Text, nullable=True)
    research_question_kz = Column(Text, nullable=True)
    recommended_hours = Column(Integer, default=1)
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    unit = relationship("CurriculumUnit", back_populates="topics")
    outcome_links = relationship("CurriculumTopicOutcome", back_populates="topic", cascade="all, delete-orphan")
    paragraph_links = relationship("ParagraphCurriculumTopic", back_populates="topic", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CurriculumTopic(id={self.id}, title='{self.title_ru}')>"


class CurriculumTopicOutcome(BaseModel):
    """Curriculum Topic - Learning Outcome M:N link table."""

    __tablename__ = "curriculum_topic_outcomes"

    topic_id = Column(Integer, ForeignKey("curriculum_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    outcome_id = Column(Integer, ForeignKey("learning_outcomes.id", ondelete="CASCADE"), nullable=False, index=True)
    display_order = Column(Integer, default=0, nullable=False)

    # Relationships
    topic = relationship("CurriculumTopic", back_populates="outcome_links")
    outcome = relationship("LearningOutcome", back_populates="topic_links")

    def __repr__(self) -> str:
        return f"<CurriculumTopicOutcome(topic_id={self.topic_id}, outcome_id={self.outcome_id})>"


class ParagraphCurriculumTopic(BaseModel):
    """Paragraph - Curriculum Topic M:N link table."""

    __tablename__ = "paragraph_curriculum_topics"

    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("curriculum_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    coverage = Column(Numeric(3, 2), default=1.0)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    paragraph = relationship("Paragraph", back_populates="topic_links")
    topic = relationship("CurriculumTopic", back_populates="paragraph_links")
    creator = relationship("User")

    def __repr__(self) -> str:
        return f"<ParagraphCurriculumTopic(paragraph_id={self.paragraph_id}, topic_id={self.topic_id})>"
```

### `backend/app/models/activity.py`

```python
"""Activity model."""
import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from app.models.base import SoftDeleteModel


class ActivityCategory(str, enum.Enum):
    GROUP_WORK = "group_work"           # Топтық жұмыс
    PAIR_WORK = "pair_work"             # Жұптық жұмыс
    INDIVIDUAL_TASK = "individual_task" # Тапсырма
    DISCUSSION = "discussion"           # Талқылау
    RESEARCH = "research"               # Зерттеу
    PROJECT = "project"                 # Жоба
    PRESENTATION = "presentation"       # Презентация
    ROLE_PLAY = "role_play"             # Рөлдік ойын
    OTHER = "other"


class Activity(SoftDeleteModel):
    """Activity (учебная активность) model."""

    __tablename__ = "activities"

    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)
    outcome_id = Column(Integer, ForeignKey("learning_outcomes.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(Enum(ActivityCategory), nullable=False, index=True)
    title_ru = Column(String(500), nullable=True)
    title_kz = Column(String(500), nullable=True)
    body_ru = Column(Text, nullable=False)
    body_kz = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    paragraph = relationship("Paragraph", back_populates="activities")
    outcome = relationship("LearningOutcome", back_populates="activities")

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, category='{self.category}', title='{self.title_ru}')>"
```

---

## Риски и митигация

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| Сложность импорта JSON | Средняя | Пошаговый импорт, валидация данных |
| Двуязычность увеличивает объём работы | Средняя | Поля `_ru/_kz`, KZ опционально на старте |
| Мэппинг параграфов к темам вручную | Высокая | AI-подсказки по названиям тем |
| Изменение ГОСО в будущем | Низкая | Версионирование через frameworks |
| Большое количество связей M:N | Средняя | Продуманные индексы, кэширование |

---

## Критерии готовности

### MVP (Minimum Viable Product):
- [x] Таблицы `subjects/frameworks/goso_sections/goso_subsections/learning_outcomes` созданы (миграция 012)
- [x] Таблица `paragraph_outcomes` создана (миграция 013)
- [x] RLS policies настроены для всех ГОСО таблиц
- [x] Clean DB test пройден (2025-12-16): все 19 миграций применяются без ошибок
- [x] SQLAlchemy модели созданы (2025-12-16): `subject.py`, `goso.py`
- [x] Pydantic схемы созданы (2025-12-16): `goso.py` (Create/Update/Response + nested)
- [x] Импортирован пилот (История Казахстана 5–9): outcomes + структура (2025-12-16)
- [x] Эндпоинты read-only (auth-only) для student/teacher/admin: subjects/frameworks/outcomes (2025-12-16)
- [x] Эндпоинты маппинга для SUPER_ADMIN и School ADMIN: `paragraph_outcomes` (2025-12-16)

### Full Release:
- [ ] Долгосрочный план (`curriculum_*`) работает
- [ ] Таблица `historical_concepts` заполнена
- [ ] Таблица `activities` работает
- [ ] Связи `paragraph_curriculum_topics` работают
- [ ] UI админки для управления ГОСО
- [ ] UI для привязки параграфов к темам/целям
- [ ] Отчёт о покрытии учебником долгосрочного плана

---

## Следующие шаги

1. ✅ **Миграция 012** — `backend/alembic/versions/012_add_goso_core_tables.py`
2. ✅ **Миграция 013** — `backend/alembic/versions/013_add_paragraph_outcomes.py`
3. ✅ **Clean DB test** — все миграции применяются на чистую БД (2025-12-16)
4. ✅ **SQLAlchemy модели + Pydantic схемы** (2025-12-16):
   - `backend/app/models/subject.py` — Subject
   - `backend/app/models/goso.py` — Framework, GosoSection, GosoSubsection, LearningOutcome, ParagraphOutcome
   - `backend/app/schemas/goso.py` — все Create/Update/Response схемы + nested responses
   - Обновлены `models/__init__.py`, `schemas/__init__.py`, `paragraph.py` (outcome_links relationship)
5. ✅ **Импорт данных** из `docs/adilet_merged.json` (2025-12-16):
   - Скрипты: `scripts/import_goso.py` (Python), `scripts/import_goso.sql` (SQL)
   - Импортировано: 1 subject, 1 framework, 4 sections, 9 subsections, 164 learning outcomes
   - Пилот: История Казахстана 5–9 классы
6. ✅ **API endpoints (auth-only)** (2025-12-16):
   - `/api/v1/goso/*` — read-only endpoints для всех аутентифицированных пользователей
   - `/api/v1/admin/global/paragraphs/{id}/outcomes` — CRUD для SUPER_ADMIN
   - `/api/v1/admin/school/paragraphs/{id}/outcomes` — CRUD для School ADMIN
   - Реализовано: `backend/app/api/v1/goso.py`, `backend/app/repositories/goso_repo.py`
   - Обновлены: `admin_global.py`, `admin_school.py`, `main.py`
7. ✅ **Тестирование API** (2025-12-16): все 16 endpoints протестированы и работают

---

**Автор:** Claude Code
**Дата создания:** 2025-12-09
**Последнее обновление:** 2025-12-16
