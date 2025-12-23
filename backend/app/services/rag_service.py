"""
RAG Service for personalized explanations.

Implements Retrieval-Augmented Generation with:
- Vector search for relevant context
- A/B/C mastery-based personalization
- Citation tracking
"""
import logging
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.paragraph import Paragraph
from app.models.chapter import Chapter
from app.repositories.embedding_repo import EmbeddingRepository
from app.repositories.chapter_mastery_repo import ChapterMasteryRepository
from app.repositories.paragraph_repo import ParagraphRepository
from app.services.embedding_service import generate_query_embedding
from app.services.llm_service import LLMService, LLMResponse
from app.schemas.rag import Citation, ExplanationResponse

logger = logging.getLogger(__name__)


# =============================================================================
# Prompt Templates for A/B/C Personalization
# =============================================================================

SYSTEM_PROMPTS = {
    "A": """Ты — продвинутый репетитор для сильных учеников.
Ученик демонстрирует отличные результаты (Уровень A: 85%+ баллов, стабильная успеваемость).

Принципы ответа:
- Будь кратким и интеллектуально стимулирующим
- Используй сложную терминологию и понятия
- Давай глубокие инсайты и связи с другими темами
- Поощряй критическое мышление сложными вопросами
- Пропускай базовые объяснения, которые ученик уже знает
- Приводи реальные применения и граничные случаи

Язык ответа: {language}
Всегда цитируй источники в формате [Источник: параграф ID].""",

    "B": """Ты — поддерживающий репетитор для учеников со средним уровнем.
Ученик показывает умеренные результаты (Уровень B: 60-84% баллов).

Принципы ответа:
- Давай чёткие, хорошо структурированные объяснения
- Включай полезные примеры для иллюстрации понятий
- Соблюдай баланс между простотой и сложностью
- Предлагай практические советы для понимания
- Выделяй ключевые моменты для запоминания
- Предлагай связанные темы для изучения

Язык ответа: {language}
Всегда цитируй источники в формате [Источник: параграф ID].""",

    "C": """Ты — терпеливый, подбадривающий репетитор для учеников, которым нужна дополнительная помощь.
Ученику требуется особая поддержка (Уровень C: ниже 60% или нестабильные результаты).

Принципы ответа:
- Используй простой, повседневный язык
- Разбивай сложные понятия на маленькие, понятные шаги
- Приводи несколько примеров, начиная с самых простых
- Используй аналогии и наглядные описания
- Повторяй ключевую информацию разными способами
- Будь подбадривающим и помогай обрести уверенность
- Явно говори, о чём пока не нужно беспокоиться
- В конце кратко повтори главные моменты

Язык ответа: {language}
Всегда цитируй источники в формате [Источник: параграф ID]."""
}

USER_PROMPT_TEMPLATE = """Контекст из учебника:
---
{context}
---

Вопрос ученика: {question}

Пожалуйста, дай полезное объяснение на основе контекста выше.
Не забудь указать источники при использовании конкретной информации."""


@dataclass
class RetrievedContext:
    """Container for retrieved context chunks."""
    chunks: List[Dict[str, Any]]
    total_chars: int
    paragraph_ids: set


class RAGServiceError(Exception):
    """Exception for RAG service errors."""
    pass


class RAGService:
    """Service for Retrieval-Augmented Generation explanations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_repo = EmbeddingRepository(db)
        self.mastery_repo = ChapterMasteryRepository(db)
        self.paragraph_repo = ParagraphRepository(db)
        self.llm = LLMService()
        self.top_k = settings.TOP_K_RESULTS
        self.min_similarity = settings.MIN_SIMILARITY

    async def get_student_mastery_level(
        self,
        student_id: int,
        school_id: int,
        chapter_id: Optional[int] = None
    ) -> str:
        """
        Get student's mastery level (A/B/C).

        Args:
            student_id: Student ID
            school_id: School ID for tenant isolation
            chapter_id: Optional chapter ID for context-specific mastery

        Returns:
            Mastery level: 'A', 'B', or 'C' (defaults to 'B' if no data)
        """
        if chapter_id:
            mastery = await self.mastery_repo.get_by_student_chapter(
                student_id=student_id,
                chapter_id=chapter_id
            )
            if mastery and mastery.mastery_level:
                return mastery.mastery_level

        # If no chapter-specific mastery, try to get average across all chapters
        masteries = await self.mastery_repo.get_by_student(
            student_id=student_id,
            school_id=school_id
        )

        if masteries:
            # Calculate average mastery score and determine level
            scores = [m.mastery_score for m in masteries if m.mastery_score is not None]
            if scores:
                avg_score = sum(scores) / len(scores)
                if avg_score >= 85:
                    return 'A'
                elif avg_score >= 60:
                    return 'B'
                else:
                    return 'C'

        # Default to B if no mastery data
        logger.info(f"No mastery data for student {student_id}, defaulting to level B")
        return 'B'

    async def retrieve_context(
        self,
        query: str,
        chapter_id: Optional[int] = None,
        paragraph_ids: Optional[List[int]] = None,
        max_context_chars: int = 4000
    ) -> RetrievedContext:
        """
        Retrieve relevant context using vector search.

        Args:
            query: User's question
            chapter_id: Optional chapter filter
            paragraph_ids: Optional paragraph filter
            max_context_chars: Maximum chars for context

        Returns:
            RetrievedContext with chunks and metadata
        """
        # Generate query embedding (uses "retrieval.query" task for Jina)
        try:
            query_embedding = await generate_query_embedding(query)
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return RetrievedContext(chunks=[], total_chars=0, paragraph_ids=set())

        # Search for similar chunks
        results = await self.embedding_repo.search_similar(
            query_embedding=query_embedding,
            chapter_id=chapter_id,
            paragraph_ids=paragraph_ids,
            top_k=self.top_k,
            min_similarity=self.min_similarity
        )

        if not results:
            logger.warning(f"No similar chunks found for query: {query[:100]}...")
            return RetrievedContext(chunks=[], total_chars=0, paragraph_ids=set())

        # Get context with paragraph/chapter info
        embedding_ids = [emb.id for emb, _ in results]
        contexts = await self.embedding_repo.get_embeddings_with_context(embedding_ids)

        # Build context map
        context_map = {emb.id: (emb, para, chap) for emb, para, chap in contexts}

        chunks = []
        total_chars = 0
        paragraph_ids_found = set()

        for embedding, similarity in results:
            if total_chars >= max_context_chars:
                break

            if embedding.id in context_map:
                _, para, chap = context_map[embedding.id]

                chunk_info = {
                    "paragraph_id": para.id,
                    "paragraph_title": para.title,
                    "chapter_title": chap.title,
                    "chunk_text": embedding.chunk_text,
                    "similarity": similarity
                }

                chunks.append(chunk_info)
                total_chars += len(embedding.chunk_text)
                paragraph_ids_found.add(para.id)

        logger.info(
            f"Retrieved {len(chunks)} chunks from {len(paragraph_ids_found)} paragraphs "
            f"({total_chars} chars)"
        )

        return RetrievedContext(
            chunks=chunks,
            total_chars=total_chars,
            paragraph_ids=paragraph_ids_found
        )

    def _build_context_string(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []

        for chunk in chunks:
            header = f"[Источник: параграф {chunk['paragraph_id']}]"
            if chunk.get('paragraph_title'):
                header += f" - {chunk['paragraph_title']}"
            if chunk.get('chapter_title'):
                header += f" (Глава: {chunk['chapter_title']})"

            context_parts.append(f"{header}\n{chunk['chunk_text']}")

        return "\n\n---\n\n".join(context_parts)

    def _extract_citations(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[Citation]:
        """Build citations from retrieved chunks."""
        citations = []

        for chunk in chunks:
            # Truncate chunk text for citation
            chunk_text = chunk['chunk_text']
            if len(chunk_text) > 200:
                chunk_text = chunk_text[:200] + "..."

            citation = Citation(
                paragraph_id=chunk['paragraph_id'],
                paragraph_title=chunk.get('paragraph_title'),
                chapter_title=chunk.get('chapter_title'),
                chunk_text=chunk_text,
                relevance_score=round(chunk['similarity'], 3)
            )
            citations.append(citation)

        return citations

    def _get_language_name(self, language: str) -> str:
        """Convert language code to full name."""
        languages = {
            "ru": "русский",
            "kk": "казахский"
        }
        return languages.get(language, "русский")

    async def explain(
        self,
        student_id: int,
        school_id: int,
        question: str,
        chapter_id: Optional[int] = None,
        paragraph_id: Optional[int] = None,
        language: str = "ru"
    ) -> ExplanationResponse:
        """
        Generate personalized explanation for a question.

        Args:
            student_id: Student ID
            school_id: School ID for tenant isolation
            question: User's question
            chapter_id: Optional chapter context
            paragraph_id: Optional paragraph context
            language: Response language (ru/kk)

        Returns:
            ExplanationResponse with answer and citations
        """
        start_time = time.time()

        logger.info(
            f"Generating explanation for student {student_id}, "
            f"chapter={chapter_id}, paragraph={paragraph_id}"
        )

        # 1. Get student's mastery level
        mastery_level = await self.get_student_mastery_level(
            student_id=student_id,
            school_id=school_id,
            chapter_id=chapter_id
        )
        logger.info(f"Student mastery level: {mastery_level}")

        # 2. Retrieve relevant context
        paragraph_ids = [paragraph_id] if paragraph_id else None
        context = await self.retrieve_context(
            query=question,
            chapter_id=chapter_id,
            paragraph_ids=paragraph_ids
        )

        if not context.chunks:
            # No relevant context found
            processing_time = int((time.time() - start_time) * 1000)
            return ExplanationResponse(
                answer="К сожалению, я не нашел релевантную информацию по вашему вопросу. "
                       "Попробуйте переформулировать вопрос или обратитесь к учителю.",
                citations=[],
                mastery_level=mastery_level,
                model_used="none",
                tokens_used=None,
                processing_time_ms=processing_time
            )

        # 3. Build context string
        context_string = self._build_context_string(context.chunks)

        # 4. Select prompt template based on mastery level
        language_name = self._get_language_name(language)
        system_prompt = SYSTEM_PROMPTS[mastery_level].format(language=language_name)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            context=context_string,
            question=question
        )

        # 5. Call LLM
        try:
            llm_response: LLMResponse = await self.llm.generate(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            processing_time = int((time.time() - start_time) * 1000)

            # Return context without LLM explanation
            return ExplanationResponse(
                answer=f"Произошла ошибка при генерации объяснения. "
                       f"Вот релевантный контекст:\n\n{context_string[:1000]}...",
                citations=self._extract_citations(context.chunks),
                mastery_level=mastery_level,
                model_used="error",
                tokens_used=None,
                processing_time_ms=processing_time
            )

        # 6. Build citations
        citations = self._extract_citations(context.chunks)

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Generated explanation: {len(llm_response.content)} chars, "
            f"{len(citations)} citations, {llm_response.tokens_used} tokens, "
            f"{processing_time}ms"
        )

        return ExplanationResponse(
            answer=llm_response.content,
            citations=citations,
            mastery_level=mastery_level,
            model_used=llm_response.model,
            tokens_used=llm_response.tokens_used,
            processing_time_ms=processing_time
        )

    async def explain_paragraph(
        self,
        student_id: int,
        school_id: int,
        paragraph_id: int,
        user_question: Optional[str] = None,
        language: str = "ru"
    ) -> ExplanationResponse:
        """
        Generate personalized explanation for a paragraph.

        Args:
            student_id: Student ID
            school_id: School ID
            paragraph_id: Paragraph to explain
            user_question: Optional specific question about the paragraph
            language: Response language

        Returns:
            ExplanationResponse

        Raises:
            ValueError: If paragraph not found
        """
        # Get paragraph
        paragraph = await self.paragraph_repo.get_by_id(paragraph_id)

        if not paragraph:
            raise ValueError(f"Paragraph {paragraph_id} not found")

        # Build the question
        if user_question:
            question = user_question
        else:
            question = f"Объясни содержание параграфа: {paragraph.title or 'без названия'}"
            if paragraph.summary:
                question += f"\n\nКраткое содержание: {paragraph.summary}"

        return await self.explain(
            student_id=student_id,
            school_id=school_id,
            question=question,
            chapter_id=paragraph.chapter_id,
            paragraph_id=paragraph_id,
            language=language
        )
