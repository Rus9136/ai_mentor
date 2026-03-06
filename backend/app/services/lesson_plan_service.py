"""
Lesson Plan (QMJ) generation service.

Generates structured lesson plans using LLM based on paragraph content,
learning objectives, and optional class mastery data.
"""
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.class_student import ClassStudent
from app.models.class_teacher import ClassTeacher
from app.models.goso import LearningOutcome, ParagraphOutcome
from app.models.mastery import ParagraphMastery
from app.models.paragraph import Paragraph
from app.models.paragraph_content import ParagraphContent
from app.repositories.paragraph_repo import ParagraphRepository
from app.schemas.lesson_plan import (
    DifferentiationBlock,
    LessonPlanContext,
    LessonPlanGenerateResponse,
    LessonPlanHeader,
    LessonPlanResponse,
    LessonStage,
)
from app.services.homework.ai.utils.json_parser import parse_json_object
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

MONTHLY_VALUES = {
    1: {"kk": "Заң мен тәртіп", "ru": "Закон и порядок",
        "decomposition_kk": "Қиын жағдайларда басқаларға көмектесуге дайын болу",
        "decomposition_ru": "Готовность помогать другим в трудных ситуациях"},
    2: {"kk": "Отбасы", "ru": "Семья",
        "decomposition_kk": "Отбасы мүшелеріне қамқорлық жасау",
        "decomposition_ru": "Забота о членах семьи"},
    3: {"kk": "Наурыз — жаңару", "ru": "Наурыз — обновление",
        "decomposition_kk": "Ұлттық салт-дәстүрлерді құрметтеу",
        "decomposition_ru": "Уважение национальных традиций"},
    4: {"kk": "Еңбек пен шығармашылық", "ru": "Труд и творчество",
        "decomposition_kk": "Еңбектің маңызын түсіну",
        "decomposition_ru": "Понимание значения труда"},
    5: {"kk": "Отан", "ru": "Родина",
        "decomposition_kk": "Отансүйгіштік рухта тәрбиелеу",
        "decomposition_ru": "Воспитание в духе патриотизма"},
    6: {"kk": "Білім", "ru": "Знание",
        "decomposition_kk": "Білімге деген ынта мен құштарлық",
        "decomposition_ru": "Стремление и тяга к знаниям"},
    7: {"kk": "Білім", "ru": "Знание",
        "decomposition_kk": "Білімге деген ынта мен құштарлық",
        "decomposition_ru": "Стремление и тяга к знаниям"},
    8: {"kk": "Білім", "ru": "Знание",
        "decomposition_kk": "Білімге деген ынта мен құштарлық",
        "decomposition_ru": "Стремление и тяга к знаниям"},
    9: {"kk": "Білім", "ru": "Знание",
        "decomposition_kk": "Білімге деген ынта мен құштарлық",
        "decomposition_ru": "Стремление и тяга к знаниям"},
    10: {"kk": "Денсаулық", "ru": "Здоровье",
         "decomposition_kk": "Салауатты өмір салтын ұстану",
         "decomposition_ru": "Здоровый образ жизни"},
    11: {"kk": "Достық пен ынтымақтастық", "ru": "Дружба и сотрудничество",
         "decomposition_kk": "Ұжымда бірлесіп жұмыс істеу",
         "decomposition_ru": "Совместная работа в коллективе"},
    12: {"kk": "Тәуелсіздік", "ru": "Независимость",
         "decomposition_kk": "Тәуелсіздік құндылықтарын бағалау",
         "decomposition_ru": "Ценность независимости"},
}


class LessonPlanService:
    def __init__(self, db: AsyncSession, llm_service: LLMService):
        self.db = db
        self.llm_service = llm_service
        self.paragraph_repo = ParagraphRepository(db)

    async def generate(
        self,
        paragraph_id: int,
        school_id: int,
        teacher_id: int,
        class_id: Optional[int],
        language: str,
        duration_min: int,
    ) -> LessonPlanGenerateResponse:
        paragraph_ctx = await self._collect_paragraph_context(paragraph_id, language)
        class_ctx = None
        if class_id:
            class_ctx = await self._collect_class_context(teacher_id, class_id, paragraph_id)

        system_prompt = self._build_system_prompt(language)
        user_prompt = self._build_user_prompt(paragraph_ctx, class_ctx, language, duration_min)

        response = await self.llm_service.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4000,
        )

        lesson_plan = self._parse_response(response.content)

        context = LessonPlanContext(
            paragraph_title=paragraph_ctx["metadata"]["paragraph_title"] or "",
            chapter_title=paragraph_ctx["metadata"]["chapter_title"],
            textbook_title=paragraph_ctx["metadata"]["textbook_title"],
            subject=paragraph_ctx["metadata"]["subject"],
            grade_level=paragraph_ctx["metadata"]["grade_level"],
            mastery_distribution=class_ctx["distribution"] if class_ctx else None,
            total_students=class_ctx["total_students"] if class_ctx else None,
            struggling_topics=None,
        )

        return LessonPlanGenerateResponse(lesson_plan=lesson_plan, context=context)

    async def _collect_paragraph_context(self, paragraph_id: int, language: str) -> dict:
        metadata = await self.paragraph_repo.get_content_metadata(paragraph_id)
        if not metadata:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")

        result = await self.db.execute(
            select(Paragraph)
            .options(selectinload(Paragraph.outcome_links).selectinload(ParagraphOutcome.outcome))
            .where(Paragraph.id == paragraph_id, Paragraph.is_deleted == False)  # noqa: E712
        )
        paragraph = result.scalar_one_or_none()
        if not paragraph:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")

        # Load language-specific content
        content_result = await self.db.execute(
            select(ParagraphContent).where(
                ParagraphContent.paragraph_id == paragraph_id,
                ParagraphContent.language == language,
            )
        )
        para_content = content_result.scalar_one_or_none()

        # Collect GOSO outcomes
        outcomes = []
        for link in paragraph.outcome_links:
            o = link.outcome
            title = o.title_kz if language == "kk" and o.title_kz else o.title_ru
            outcomes.append({"code": o.code, "title": title, "cognitive_level": o.cognitive_level})

        return {
            "metadata": metadata,
            "paragraph": paragraph,
            "content": para_content,
            "outcomes": outcomes,
        }

    async def _collect_class_context(self, teacher_id: int, class_id: int, paragraph_id: int) -> dict:
        # Verify teacher access
        access = await self.db.execute(
            select(ClassTeacher).where(and_(
                ClassTeacher.teacher_id == teacher_id,
                ClassTeacher.class_id == class_id,
            ))
        )
        if not access.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this class")

        # Get student IDs
        students_result = await self.db.execute(
            select(ClassStudent.student_id).where(ClassStudent.class_id == class_id)
        )
        student_ids = [row[0] for row in students_result.all()]
        if not student_ids:
            return {"total_students": 0, "distribution": {"A": 0, "B": 0, "C": 0}}

        # Get mastery data
        mastery_result = await self.db.execute(
            select(ParagraphMastery).where(
                ParagraphMastery.student_id.in_(student_ids),
                ParagraphMastery.paragraph_id == paragraph_id,
            )
        )
        masteries = mastery_result.scalars().all()

        count_a = sum(1 for m in masteries if m.status == "mastered")
        count_b = sum(1 for m in masteries if m.status == "progressing")
        count_c = sum(1 for m in masteries if m.status == "struggling")
        total = len(student_ids)

        return {
            "total_students": total,
            "distribution": {"A": count_a, "B": count_b, "C": count_c},
            "count_a": count_a,
            "count_b": count_b,
            "count_c": count_c,
            "percent_a": round(count_a / total * 100) if total else 0,
            "percent_b": round(count_b / total * 100) if total else 0,
            "percent_c": round(count_c / total * 100) if total else 0,
        }

    def _get_monthly_value(self, language: str) -> tuple[str, str]:
        month = datetime.now().month
        val = MONTHLY_VALUES.get(month, MONTHLY_VALUES[9])
        return val[language], val[f"decomposition_{language}"]

    def _build_system_prompt(self, language: str) -> str:
        lang_instruction = "Язык ответа: қазақша" if language == "kk" else "Язык ответа: русский"
        return f"""Ты — опытный методист-педагог Казахстана с 20-летним стажем.
Твоя задача — составить Қысқамерзімді жоспар (ҚМЖ) по стандарту ГОСО РК.

Требования к плану:
1. Строго следуй формату QMJ (3 этапа: басы / ортасы / соңы)
2. Используй активные методы обучения (проблемное обучение, групповая работа, дискуссия)
3. Для каждого задания укажи дескрипторы с баллами
4. Саралау (дифференциация) — обязательна, если даны уровни учеников
5. Формативное оценивание на каждом этапе
6. Рефлексия в конце (метод + шаблон)
7. {lang_instruction}
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

Верни ответ СТРОГО в JSON формате (без markdown обёртки)."""

    def _build_user_prompt(self, paragraph_ctx: dict, class_ctx: Optional[dict], language: str, duration_min: int) -> str:
        meta = paragraph_ctx["metadata"]
        p = paragraph_ctx["paragraph"]
        content = paragraph_ctx["content"]
        outcomes = paragraph_ctx["outcomes"]

        learning_obj = p.learning_objective or p.summary or p.title or ""
        lesson_obj = p.lesson_objective or p.summary or p.title or ""
        key_terms_str = ", ".join(p.key_terms) if p.key_terms else "—"

        questions_str = "—"
        if p.questions:
            questions_str = "\n".join(
                f"{i+1}. {q['text'] if isinstance(q, dict) else q}"
                for i, q in enumerate(p.questions[:10])
            )

        outcomes_str = "—"
        if outcomes:
            outcomes_str = "\n".join(f"- {o['code']}: {o['title']}" for o in outcomes)

        explain_text = ""
        if content and content.explain_text:
            explain_text = f"\nТҮСІНДІРМЕ:\n{content.explain_text[:2000]}"

        monthly_value, value_decomposition = self._get_monthly_value(language)

        # Class context block
        class_block = ""
        if class_ctx and class_ctx["total_students"] > 0:
            class_block = f"""
СЫНЫП ДЕРЕКТЕРІ:
- Оқушылар саны: {class_ctx['total_students']}
- A деңгей (mastered, ≥85%): {class_ctx['count_a']} оқушы ({class_ctx['percent_a']}%)
- B деңгей (progressing, 60-84%): {class_ctx['count_b']} оқушы ({class_ctx['percent_b']}%)
- C деңгей (struggling, <60%): {class_ctx['count_c']} оқушы ({class_ctx['percent_c']}%)

Саралау бөлімінде A/B/C деңгейлеріне арнайы тапсырмалар мен қолдау түрлерін көрсет."""

        prompt = f"""Составь ҚМЖ для следующего урока:

КОНТЕКСТ:
- Пән (предмет): {meta['subject']}
- Сынып (класс): {meta['grade_level']}
- Оқулық (учебник): {meta['textbook_title']}
- Бөлім (раздел): {meta['chapter_number']}-бөлім: {meta['chapter_title']}
- Тақырып (тема): {p.title}
- Сабақ ұзақтығы: {duration_min} минут

МАҚСАТТАР:
- Оқу мақсаты: {learning_obj}
- Сабақтың мақсаты: {lesson_obj}

ГОСО ОҚЫТУ НӘТИЖЕЛЕРІ:
{outcomes_str}

МАЗМҰНЫ (кратко):
{(p.content or '')[:3000]}
{explain_text}

НЕГІЗГІ ҰҒЫМДАР:
{key_terms_str}

СҰРАҚТАР:
{questions_str}
{class_block}

Құндылық (айдың құндылығы): {monthly_value}
Құндылық декомпозициясы: {value_decomposition}

JSON ФОРМАТ (строго следуй этой структуре):
{{
  "header": {{
    "section": "N-бөлім: ...",
    "topic": "...",
    "learning_objective": "...",
    "lesson_objective": "...",
    "monthly_value": "...",
    "value_decomposition": "..."
  }},
  "stages": [
    {{
      "name": "Сабақтың басы",
      "name_detail": "Қызығушылықты ояту",
      "duration_min": 5,
      "method_name": "...",
      "method_purpose": "...",
      "method_effectiveness": "...",
      "teacher_activity": "...",
      "student_activity": "...",
      "assessment": "...",
      "differentiation": null,
      "resources": "...",
      "tasks": []
    }},
    {{
      "name": "Сабақтың ортасы",
      "name_detail": "Мағынаны ашу",
      "duration_min": 30,
      "method_name": "...",
      "method_purpose": "...",
      "method_effectiveness": "...",
      "teacher_activity": "...",
      "student_activity": "...",
      "assessment": "...",
      "differentiation": "...",
      "resources": "...",
      "tasks": [
        {{
          "number": 1,
          "teacher_activity": "...",
          "student_activity": "...",
          "descriptors": [{{"text": "...", "score": 1}}],
          "total_score": 5
        }}
      ]
    }},
    {{
      "name": "Сабақтың соңы",
      "name_detail": "Ой толғаныс / Рефлексия",
      "duration_min": 5,
      "method_name": "...",
      "method_purpose": "...",
      "method_effectiveness": "...",
      "teacher_activity": "...",
      "student_activity": "...",
      "assessment": "...",
      "differentiation": null,
      "resources": "...",
      "tasks": []
    }}
  ],
  "total_score": 20,
  "differentiation": {{
    "approach": "...",
    "for_level_a": "...",
    "for_level_b": "...",
    "for_level_c": "..."
  }},
  "health_safety": "...",
  "reflection_template": ["...", "..."]
}}"""
        return prompt

    def _parse_response(self, llm_content: str) -> LessonPlanResponse:
        try:
            data = parse_json_object(llm_content)
            return LessonPlanResponse(**data)
        except (ValueError, json.JSONDecodeError) as e:
            logger.error("Failed to parse lesson plan JSON: %s", e)
            raise ValueError(f"Failed to parse AI response: {e}") from e
