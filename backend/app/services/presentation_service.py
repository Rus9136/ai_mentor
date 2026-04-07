"""
Presentation generation service.

Generates structured slide presentations using LLM based on paragraph content,
then exports to PPTX via presentation_export module.
"""
import logging
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.paragraph import Paragraph
from app.models.paragraph_content import ParagraphContent
from app.models.presentation import Presentation
from app.models.subscription import DailyUsageCounter
from app.repositories.paragraph_repo import ParagraphRepository
from app.schemas.presentation import (
    PresentationContext,
    PresentationGenerateResponse,
    PresentationSaveRequest,
    PresentationUpdateRequest,
)
from app.services.homework.ai.utils.json_parser import parse_json_object
from app.services.llm_service import LLMService, LLMUsageContext

logger = logging.getLogger(__name__)

MAX_DAILY_PRESENTATIONS = 10


class PresentationService:
    def __init__(self, db: AsyncSession, llm_service: LLMService):
        self.db = db
        self.llm_service = llm_service
        self.paragraph_repo = ParagraphRepository(db)

    # --- Generation ---

    async def generate(
        self,
        paragraph_id: int,
        school_id: int,
        teacher_id: int,
        user_id: int,
        class_id: Optional[int],
        language: str,
        slide_count: int,
    ) -> PresentationGenerateResponse:
        paragraph_ctx = await self._collect_paragraph_context(paragraph_id, language)
        metadata = paragraph_ctx["metadata"]
        paragraph = paragraph_ctx["paragraph"]
        content = paragraph_ctx["content"]

        # Extract available images from paragraph content
        textbook_id = metadata["textbook_id"]
        images = self._extract_image_urls(paragraph.content, textbook_id)

        system_prompt = self._build_system_prompt(language, slide_count)
        user_prompt = self._build_user_prompt(paragraph_ctx, images, language, slide_count)

        usage_ctx = LLMUsageContext(
            db=self.db,
            feature="presentation",
            user_id=user_id,
            teacher_id=teacher_id,
            school_id=school_id,
        )
        response = await self.llm_service.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4000,
            usage_context=usage_ctx,
        )

        presentation_data = self._parse_response(response.content)

        context = PresentationContext(
            paragraph_title=metadata.get("paragraph_title") or "",
            chapter_title=metadata["chapter_title"],
            textbook_title=metadata["textbook_title"],
            subject=metadata["subject"],
            grade_level=metadata["grade_level"],
            textbook_id=textbook_id,
        )

        return PresentationGenerateResponse(
            presentation=presentation_data,
            context=context,
        )

    async def _collect_paragraph_context(self, paragraph_id: int, language: str) -> dict:
        metadata = await self.paragraph_repo.get_content_metadata(paragraph_id)
        if not metadata:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")

        result = await self.db.execute(
            select(Paragraph)
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

        return {
            "metadata": metadata,
            "paragraph": paragraph,
            "content": para_content,
        }

    def _extract_image_urls(self, paragraph_content: str, textbook_id: int) -> list[dict]:
        """Extract image URLs from paragraph markdown content."""
        if not paragraph_content:
            return []

        pattern = r'!\[([^\]]*)\]\(images/([^)]+)\)'
        matches = re.findall(pattern, paragraph_content)
        images = []
        for alt_text, filename in matches:
            relative_path = f"/uploads/textbook-images/{textbook_id}/{filename}"
            absolute_path = Path(settings.UPLOAD_DIR) / "textbook-images" / str(textbook_id) / filename
            if absolute_path.exists():
                images.append({
                    "alt_text": alt_text,
                    "filename": filename,
                    "url": relative_path,
                    "absolute_path": str(absolute_path),
                })
        return images

    def _build_system_prompt(self, language: str, slide_count: int) -> str:
        lang_instruction = "Язык: қазақша" if language == "kk" else "Язык: русский"
        return f"""Ты — дизайнер учебных презентаций для школ Казахстана.
Создай структуру из {slide_count} слайдов на основе параграфа учебника.
{lang_instruction}.

КРИТИЧЕСКИЕ ПРАВИЛА (нарушение = ошибка):
1. Каждый слайд = ОДИН тезис. НЕ перегружай текстом.
2. СТРОГИЕ ЛИМИТЫ символов:
   - title: максимум 50 символов
   - subtitle: максимум 80 символов
   - body: максимум 250 символов (3-4 коротких предложения)
   - items: максимум 6 пунктов, каждый до 70 символов
   - terms: максимум 5 штук, term до 30 символов, definition до 60 символов
   - question: максимум 100 символов
   - options: 4 варианта, каждый до 50 символов
3. Текст должен быть КРАТКИМ и ЯСНЫМ. Не пиши длинные абзацы.
4. Используй ФАКТЫ и ЦИФРЫ, а не общие фразы.

ТИПЫ СЛАЙДОВ:
- "title" — титульный: {{"type":"title","title":"...","subtitle":"..."}}
- "objectives" — цели: {{"type":"objectives","title":"...","items":["..."]}}
- "content" — контент: {{"type":"content","title":"...","body":"...","image_url":null}}
- "key_terms" — термины: {{"type":"key_terms","title":"...","terms":[{{"term":"...","definition":"..."}}]}}
- "quiz" — вопрос: {{"type":"quiz","title":"Білімді тексер","question":"...","options":["..."],"answer":0}}
- "summary" — итоги: {{"type":"summary","title":"Қорытынды","items":["..."]}}

СТРУКТУРА ПРЕЗЕНТАЦИИ:
- Слайд 1: type="title"
- Слайд 2: type="objectives"
- Слайды 3-{slide_count-2}: чередуй "content" и "key_terms" (минимум 1 key_terms)
- Слайд {slide_count-1}: type="quiz"
- Слайд {slide_count}: type="summary"

Для image_url используй ТОЛЬКО URL из списка. Нет подходящего — null.

Ответ СТРОГО JSON (без markdown обёртки, без ```json```)."""

    def _build_user_prompt(self, paragraph_ctx: dict, images: list[dict], language: str, slide_count: int) -> str:
        meta = paragraph_ctx["metadata"]
        p = paragraph_ctx["paragraph"]
        content = paragraph_ctx["content"]

        learning_obj = p.learning_objective or p.summary or p.title or ""
        lesson_obj = p.lesson_objective or p.summary or p.title or ""
        key_terms_str = ", ".join(p.key_terms) if p.key_terms else "—"

        explain_text = ""
        if content and content.explain_text:
            explain_text = f"\nТҮСІНДІРМЕ (упрощённое объяснение):\n{content.explain_text[:2000]}"

        # Image list for LLM
        images_block = "Нет доступных изображений"
        if images:
            img_lines = [f"{i+1}. {img['url']} — {img['alt_text'] or img['filename']}" for i, img in enumerate(images)]
            images_block = "\n".join(img_lines)

        prompt = f"""Предмет: {meta['subject']}, {meta['grade_level']} класс
Учебник: {meta['textbook_title']}
Раздел: {meta['chapter_number']}-бөлім: {meta['chapter_title']}
Тема: {p.title}

Цель обучения: {learning_obj}
Цель урока: {lesson_obj}

СОДЕРЖАНИЕ ПАРАГРАФА:
{(p.content or '')[:2500]}
{explain_text}

Ключевые термины: {key_terms_str}

Изображения: {images_block}

Создай {slide_count} слайдов. Помни: title до 50 символов, body до 250, items до 6 штук по 70 символов.
Верни JSON:
{{"title":"...","slides":[...]}}"""
        return prompt

    def _parse_response(self, llm_content: str) -> dict:
        try:
            data = parse_json_object(llm_content)
            if "slides" not in data:
                raise ValueError("Missing 'slides' key in response")
            return data
        except (ValueError, Exception) as e:
            logger.error("Failed to parse presentation JSON: %s", e)
            raise ValueError(f"Failed to parse AI response: {e}") from e

    # --- Rate Limiting ---

    async def check_rate_limit(self, user_id: int) -> None:
        """Check if teacher has exceeded daily presentation limit."""
        today = date.today()
        result = await self.db.execute(
            select(DailyUsageCounter.message_count).where(
                DailyUsageCounter.user_id == user_id,
                DailyUsageCounter.usage_date == today,
                DailyUsageCounter.feature == "presentation",
            )
        )
        count = result.scalar_one_or_none() or 0
        if count >= MAX_DAILY_PRESENTATIONS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily limit of {MAX_DAILY_PRESENTATIONS} presentations reached",
            )

    # --- CRUD ---

    async def save(
        self,
        teacher_id: int,
        school_id: int,
        data: PresentationSaveRequest,
    ) -> Presentation:
        title = data.title or data.context_data.get("paragraph_title", "Presentation")
        pres = Presentation(
            teacher_id=teacher_id,
            school_id=school_id,
            paragraph_id=data.paragraph_id,
            class_id=data.class_id,
            language=data.language,
            slide_count=data.slide_count,
            title=title,
            slides_data=data.slides_data,
            context_data=data.context_data,
        )
        self.db.add(pres)
        await self.db.commit()
        await self.db.refresh(pres)
        return pres

    async def list_by_teacher(
        self,
        teacher_id: int,
        school_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Presentation]:
        result = await self.db.execute(
            select(Presentation)
            .where(
                Presentation.teacher_id == teacher_id,
                Presentation.school_id == school_id,
            )
            .order_by(desc(Presentation.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(
        self,
        presentation_id: int,
        teacher_id: int,
        school_id: int,
    ) -> Presentation:
        result = await self.db.execute(
            select(Presentation).where(
                Presentation.id == presentation_id,
                Presentation.teacher_id == teacher_id,
                Presentation.school_id == school_id,
            )
        )
        pres = result.scalar_one_or_none()
        if not pres:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")
        return pres

    async def update(
        self,
        presentation_id: int,
        teacher_id: int,
        school_id: int,
        data: PresentationUpdateRequest,
    ) -> Presentation:
        pres = await self.get_by_id(presentation_id, teacher_id, school_id)
        if data.title is not None:
            pres.title = data.title
        if data.slides_data is not None:
            pres.slides_data = data.slides_data
        pres.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(pres)
        return pres

    async def delete(
        self,
        presentation_id: int,
        teacher_id: int,
        school_id: int,
    ) -> None:
        pres = await self.get_by_id(presentation_id, teacher_id, school_id)
        await self.db.delete(pres)
        await self.db.commit()
