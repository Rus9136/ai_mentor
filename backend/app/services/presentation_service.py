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

# Subject code → PPTX theme mapping
SUBJECT_THEME_MAP: dict[str, str] = {
    "history_kz": "warm",
    "world_history": "warm",
    "biology": "forest",
    "natural_science": "forest",
    "chemistry": "forest",
    "geography": "forest",
    "algebra": "midnight",
    "geometry": "midnight",
    "math": "midnight",
    "informatics": "midnight",
    "physics": "midnight",
}
DEFAULT_THEME = "warm"


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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.llm_service.generate(
            messages=messages,
            temperature=0.8,
            max_tokens=4000,
            usage_context=usage_ctx,
        )

        logger.debug("LLM raw response for presentation: %s", response.content[:500])

        presentation_data = await self._parse_with_retry(
            response.content, messages, usage_ctx
        )

        # Validate through v2 schemas (soft — truncates, never raises)
        from app.schemas.presentation import validate_slides_data
        presentation_data = validate_slides_data(presentation_data)

        # Auto-select theme based on subject
        subject_code = metadata.get("subject_code") or ""
        theme = SUBJECT_THEME_MAP.get(subject_code, DEFAULT_THEME)

        context = PresentationContext(
            paragraph_title=metadata.get("paragraph_title") or "",
            chapter_title=metadata["chapter_title"],
            textbook_title=metadata["textbook_title"],
            subject=metadata["subject"],
            grade_level=metadata["grade_level"],
            textbook_id=textbook_id,
            theme=theme,
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
        lang_instruction = (
            "Write ALL text in Kazakh (қазақша). Never mix languages."
            if language == "kk"
            else "Write ALL text in Russian. Never mix languages."
        )

        structure = self._get_slide_structure(slide_count)

        return f"""You are an expert pedagogical content designer who creates educational
slide decks for the AI-Mentor platform.

{lang_instruction}

Output a single JSON object — no preamble, no markdown fences. Schema:
{{"title":"string ≤60 chars","slides":[...array of slide objects...]}}

SLIDE STRUCTURE (exactly {slide_count} slides):
{structure}

SLIDE TYPES AND REQUIRED FIELDS:

title: {{"type":"title","title":"≤50 chars","subtitle":"≤90 chars","image_query":"2-3 ENGLISH words for stock photo"}}

objectives: {{"type":"objectives","title":"Сабақтың мақсаты","items":["3-4 strings ≤80 chars, start with verb"]}}

content — choose ONE layout_hint per slide:
{{"type":"content","title":"≤50 chars","body":"150-280 chars, full sentences",
"layout_hint":"image_left"|"image_right"|"stat_callout",
"image_query":"2-3 ENGLISH words (for image_left/image_right)",
"stat_value":"1-7 chars (for stat_callout, e.g. 1511, 70%, Жайық)",
"stat_label":"≤35 chars (for stat_callout)"}}

LAYOUT RULES:
- stat_callout: when slide centers on a memorable date, number, or key term
- image_left / image_right: for narrative content. Alternate between them.
- NEVER use same layout_hint two slides in a row.

key_terms: {{"type":"key_terms","title":"Негізгі ұғымдар","terms":[{{"term":"≤25 chars","definition":"≤90 chars"}}] (4-6 items)}}

quiz: {{"type":"quiz","question":"≤120 chars, ends with ?","options":["4 strings ≤40 chars"],"answer":0|1|2|3}}

summary: {{"type":"summary","title":"Қорытынды","items":["3-5 strings ≤70 chars"]}}

IMAGE_QUERY RULES:
- ALWAYS in English, even when content is Kazakh/Russian
- 2-3 concrete nouns: "ulytau mountains", "kazakh steppe horse"
- Avoid abstract: NOT "history", NOT "leadership"
- For historical figures, use place or era: "medieval central asia"

STYLE RULES:
- No markdown formatting (no *, #, emojis)
- Body: complete sentences, never bullet fragments
- Be concise — respect character limits strictly
- Use FACTS and NUMBERS, not vague phrases"""

    def _get_slide_structure(self, slide_count: int) -> str:
        if slide_count == 5:
            return """1. title
2. objectives
3. content (image_left)
4. content (stat_callout OR image_right)
5. summary"""
        elif slide_count == 15:
            return """1. title
2. objectives
3. content (image_left)
4. content (stat_callout)
5. content (image_right)
6. content (image_left)
7. content (stat_callout)
8. content (image_right)
9. key_terms
10. content (image_left)
11. content (image_right)
12. quiz
13. quiz
14. content (stat_callout)
15. summary"""
        else:  # 10
            return """1. title
2. objectives
3. content (image_left)
4. content (stat_callout)
5. content (image_right)
6. content (stat_callout)
7. key_terms
8. content (stat_callout)
9. quiz
10. summary"""

    def _build_user_prompt(self, paragraph_ctx: dict, images: list[dict], language: str, slide_count: int) -> str:
        meta = paragraph_ctx["metadata"]
        p = paragraph_ctx["paragraph"]
        content = paragraph_ctx["content"]

        learning_obj = p.learning_objective or p.summary or p.title or ""
        lesson_obj = p.lesson_objective or p.summary or p.title or ""
        key_terms_str = ", ".join(p.key_terms) if p.key_terms else "—"

        explain_text = ""
        if content and content.explain_text:
            explain_text = f"\nSIMPLIFIED EXPLANATION:\n{content.explain_text[:2000]}"

        prompt = f"""Subject: {meta['subject']}, grade {meta['grade_level']}
Textbook: {meta['textbook_title']}
Chapter: {meta['chapter_number']} — {meta['chapter_title']}
Topic: {p.title}

Learning objective: {learning_obj}
Lesson objective: {lesson_obj}

PARAGRAPH CONTENT:
{(p.content or '')[:2500]}
{explain_text}

Key terms: {key_terms_str}

Create exactly {slide_count} slides. Use image_query (ENGLISH keywords) for stock photos.
For dates and key numbers, use stat_callout layout with stat_value + stat_label.
Return JSON: {{"title":"...","slides":[...]}}"""
        return prompt

    def _parse_response(self, llm_content: str) -> dict:
        """Parse LLM JSON response. Raises ValueError on failure."""
        data = parse_json_object(llm_content)
        if "slides" not in data:
            raise ValueError("Missing 'slides' key in response")
        return data

    async def _parse_with_retry(
        self, llm_content: str, messages: list[dict], usage_ctx: LLMUsageContext
    ) -> dict:
        """Parse JSON, retry once on failure with error feedback."""
        first_error: Exception | None = None
        try:
            return self._parse_response(llm_content)
        except (ValueError, Exception) as exc:
            first_error = exc
            logger.warning("First parse attempt failed: %s. Retrying...", exc)

        # Retry: append error feedback and ask LLM to fix
        retry_messages = messages + [
            {"role": "assistant", "content": llm_content},
            {
                "role": "user",
                "content": (
                    f"Your response was not valid JSON. Error: {first_error}\n"
                    "Please return ONLY a valid JSON object with the exact schema "
                    'requested: {"title":"...","slides":[...]}. '
                    "No markdown fences, no explanation."
                ),
            },
        ]

        try:
            retry_response = await self.llm_service.generate(
                messages=retry_messages,
                temperature=0.3,
                max_tokens=4000,
                usage_context=usage_ctx,
            )
            logger.debug("LLM retry response: %s", retry_response.content[:500])
            return self._parse_response(retry_response.content)
        except Exception as retry_error:
            logger.error(
                "Retry parse also failed: %s. Returning error.", retry_error
            )
            raise ValueError(f"Failed to parse AI response after retry: {retry_error}") from retry_error

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
