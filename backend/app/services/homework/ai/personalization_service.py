"""
AI Personalization Service.

Adapts question difficulty based on student mastery.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.homework import BloomLevel, GenerationParams


class PersonalizationService:
    """Service for difficulty personalization based on mastery."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def personalize_difficulty(
        self,
        student_id: int,
        paragraph_id: int,
        base_params: GenerationParams
    ) -> GenerationParams:
        """
        Adapt difficulty based on student mastery.

        Args:
            student_id: Student ID
            paragraph_id: Paragraph ID
            base_params: Base generation parameters

        Returns:
            Adjusted GenerationParams
        """
        from app.services.mastery_service import MasteryService
        mastery_service = MasteryService(self.db)

        # Get student's mastery level for this paragraph
        mastery = await mastery_service.paragraph_repo.get_by_student_paragraph(
            student_id=student_id,
            paragraph_id=paragraph_id
        )

        params = base_params.model_copy()

        if mastery:
            if mastery.status == "mastered":
                # High level - harder questions
                params.bloom_levels = [
                    BloomLevel.ANALYZE,
                    BloomLevel.EVALUATE,
                    BloomLevel.CREATE
                ]
                params.questions_count = max(3, params.questions_count - 2)

            elif mastery.status == "progressing":
                # Medium level - standard
                params.bloom_levels = [
                    BloomLevel.UNDERSTAND,
                    BloomLevel.APPLY,
                    BloomLevel.ANALYZE
                ]

            else:  # struggling
                # Low level - easier questions
                params.bloom_levels = [
                    BloomLevel.REMEMBER,
                    BloomLevel.UNDERSTAND,
                    BloomLevel.APPLY
                ]
                params.questions_count = min(7, params.questions_count + 2)

        return params
