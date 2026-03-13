"""
Prerequisite Service (Knowledge Graph).

Manages dependency relationships between paragraphs and checks
whether students meet prerequisites before starting new topics.
"""

import logging
from typing import List, Dict, Optional
from collections import deque

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.prerequisite import ParagraphPrerequisite
from app.models.paragraph import Paragraph
from app.models.chapter import Chapter
from app.models.textbook import Textbook
from app.models.mastery import ParagraphMastery
from app.repositories.prerequisite_repo import PrerequisiteRepository
from app.repositories.paragraph_mastery_repo import ParagraphMasteryRepository
from app.utils.mastery_decay import calculate_effective_score
from app.schemas.prerequisite import (
    PrerequisiteCheckResponse,
    PrerequisiteWarning,
    PrerequisiteResponse,
    PrerequisiteEdge,
    GraphNode,
    TextbookGraphResponse,
    PrerequisiteAnalyticsItem,
    PrerequisiteAnalyticsResponse,
)

logger = logging.getLogger(__name__)

# effective_score >= this threshold means prerequisite is met
PREREQUISITE_THRESHOLD = 0.60

# Max BFS depth for cycle detection
MAX_CYCLE_DEPTH = 10


class PrerequisiteService:
    """Service for managing paragraph prerequisites (Knowledge Graph)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.prereq_repo = PrerequisiteRepository(db)
        self.mastery_repo = ParagraphMasteryRepository(db)

    # =========================================================================
    # Student: check prerequisites
    # =========================================================================

    async def check_prerequisites(
        self, student_id: int, paragraph_id: int
    ) -> PrerequisiteCheckResponse:
        """
        Check if a student meets all prerequisites for a paragraph.
        Returns warnings for unmet prerequisites.
        """
        prereqs = await self.prereq_repo.get_prerequisites(paragraph_id)

        if not prereqs:
            return PrerequisiteCheckResponse(
                paragraph_id=paragraph_id,
                has_warnings=False,
                can_proceed=True,
            )

        # Batch fetch mastery for all prerequisite paragraphs
        prereq_paragraph_ids = [p.prerequisite_paragraph_id for p in prereqs]
        mastery_map = await self._get_mastery_map(student_id, prereq_paragraph_ids)

        warnings = []
        for prereq in prereqs:
            pid = prereq.prerequisite_paragraph_id
            mastery = mastery_map.get(pid)

            effective = 0.0
            if mastery and mastery.best_score:
                effective = mastery.effective_score or 0.0

            if effective < PREREQUISITE_THRESHOLD:
                para = prereq.prerequisite
                chapter = para.chapter if para else None
                textbook = chapter.textbook if chapter else None
                warnings.append(PrerequisiteWarning(
                    paragraph_id=pid,
                    paragraph_title=para.title if para else None,
                    paragraph_number=para.number if para else None,
                    chapter_title=chapter.title if chapter else None,
                    textbook_title=textbook.title if textbook else None,
                    grade_level=textbook.grade_level if textbook else None,
                    current_score=round(effective, 4),
                    strength=prereq.strength,
                    recommendation="review_first" if prereq.strength == "required" else "consider_review",
                ))

        has_required_unmet = any(w.strength == "required" for w in warnings)

        return PrerequisiteCheckResponse(
            paragraph_id=paragraph_id,
            has_warnings=len(warnings) > 0,
            warnings=warnings,
            can_proceed=not has_required_unmet,
        )

    async def check_prerequisites_batch(
        self, student_id: int, paragraph_ids: List[int]
    ) -> Dict[int, List[PrerequisiteWarning]]:
        """
        Batch check prerequisites for multiple paragraphs.
        Returns Dict[paragraph_id, List[PrerequisiteWarning]].
        Uses only 2 queries (prerequisites + mastery).
        """
        if not paragraph_ids:
            return {}

        # 1. Batch fetch all prerequisites
        prereqs_by_para = await self.prereq_repo.get_prerequisites_batch(paragraph_ids)

        if not prereqs_by_para:
            return {}

        # 2. Collect all prerequisite paragraph IDs
        all_prereq_ids = set()
        for prereqs in prereqs_by_para.values():
            for p in prereqs:
                all_prereq_ids.add(p.prerequisite_paragraph_id)

        # 3. Batch fetch mastery for all prerequisite paragraphs
        mastery_map = await self._get_mastery_map(student_id, list(all_prereq_ids))

        # 4. Build warnings per paragraph
        result: Dict[int, List[PrerequisiteWarning]] = {}
        for para_id, prereqs in prereqs_by_para.items():
            warnings = []
            for prereq in prereqs:
                pid = prereq.prerequisite_paragraph_id
                mastery = mastery_map.get(pid)

                effective = 0.0
                if mastery and mastery.best_score:
                    effective = mastery.effective_score or 0.0

                if effective < PREREQUISITE_THRESHOLD:
                    para = prereq.prerequisite
                    chapter = para.chapter if para else None
                    textbook = chapter.textbook if chapter else None
                    warnings.append(PrerequisiteWarning(
                        paragraph_id=pid,
                        paragraph_title=para.title if para else None,
                        paragraph_number=para.number if para else None,
                        chapter_title=chapter.title if chapter else None,
                        textbook_title=textbook.title if textbook else None,
                        grade_level=textbook.grade_level if textbook else None,
                        current_score=round(effective, 4),
                        strength=prereq.strength,
                        recommendation="review_first" if prereq.strength == "required" else "consider_review",
                    ))
            if warnings:
                result[para_id] = warnings

        return result

    # =========================================================================
    # Admin: CRUD
    # =========================================================================

    async def add_prerequisite(
        self,
        paragraph_id: int,
        prerequisite_paragraph_id: int,
        strength: str = "required",
    ) -> ParagraphPrerequisite:
        """
        Add a prerequisite link. Validates:
        1. Both paragraphs exist
        2. Both are in the same textbook
        3. No circular dependency
        4. Link doesn't already exist
        """
        # Check duplicate
        if await self.prereq_repo.exists(paragraph_id, prerequisite_paragraph_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This prerequisite link already exists",
            )

        # Load both paragraphs with chapters and textbooks
        para = await self._get_paragraph_with_chapter(paragraph_id)
        prereq_para = await self._get_paragraph_with_chapter(prerequisite_paragraph_id)

        # Validate same subject (allows cross-textbook within same subject)
        para_textbook = para.chapter.textbook if para.chapter else None
        prereq_textbook = prereq_para.chapter.textbook if prereq_para.chapter else None
        para_subject_id = para_textbook.subject_id if para_textbook else None
        prereq_subject_id = prereq_textbook.subject_id if prereq_textbook else None

        if para_subject_id is None or prereq_subject_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both paragraphs must belong to textbooks with a subject assigned.",
            )

        if para_subject_id != prereq_subject_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Paragraphs must be in textbooks of the same subject. "
                    f"Paragraph {paragraph_id} is in subject {para_subject_id}, "
                    f"prerequisite {prerequisite_paragraph_id} is in subject {prereq_subject_id}."
                ),
            )

        # Check for circular dependency (across all textbooks of the subject)
        await self._check_circular_dependency(
            paragraph_id, prerequisite_paragraph_id, para_subject_id
        )

        prereq = ParagraphPrerequisite(
            paragraph_id=paragraph_id,
            prerequisite_paragraph_id=prerequisite_paragraph_id,
            strength=strength,
        )
        await self.prereq_repo.create(prereq)
        await self.db.commit()

        logger.info(
            f"Added prerequisite: paragraph {paragraph_id} ← "
            f"prerequisite {prerequisite_paragraph_id} ({strength})"
        )
        return prereq

    async def remove_prerequisite(self, prereq_id: int) -> None:
        """Remove a prerequisite link."""
        prereq = await self.prereq_repo.get_by_id(prereq_id)
        if not prereq:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prerequisite link {prereq_id} not found",
            )

        await self.prereq_repo.delete_by_id(prereq_id)
        await self.db.commit()

        logger.info(
            f"Removed prerequisite {prereq_id}: paragraph {prereq.paragraph_id} ← "
            f"prerequisite {prereq.prerequisite_paragraph_id}"
        )

    async def get_textbook_graph(self, textbook_id: int) -> TextbookGraphResponse:
        """Get full prerequisite graph for a textbook (nodes + edges).
        Includes cross-textbook prerequisite nodes if they exist."""
        # Load all paragraphs for this textbook (nodes)
        result = await self.db.execute(
            select(Paragraph)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id == textbook_id,
                Paragraph.is_deleted == False,
            )
            .options(selectinload(Paragraph.chapter))
            .order_by(Chapter.order, Paragraph.order)
        )
        paragraphs = list(result.scalars().all())
        node_ids = {p.id for p in paragraphs}

        # Load edges
        prereqs = await self.prereq_repo.get_by_textbook(textbook_id)

        edges = [
            PrerequisiteEdge(
                id=p.id,
                from_paragraph_id=p.prerequisite_paragraph_id,
                to_paragraph_id=p.paragraph_id,
                strength=p.strength,
            )
            for p in prereqs
        ]

        # Find cross-textbook prerequisite paragraph IDs
        cross_ids = {
            e.from_paragraph_id for e in edges
            if e.from_paragraph_id not in node_ids
        }

        # Load cross-textbook paragraphs
        if cross_ids:
            result = await self.db.execute(
                select(Paragraph)
                .where(Paragraph.id.in_(cross_ids), Paragraph.is_deleted == False)
                .options(selectinload(Paragraph.chapter))
            )
            cross_paragraphs = list(result.scalars().all())
            paragraphs.extend(cross_paragraphs)

        nodes = [
            GraphNode(
                id=p.id,
                title=p.title,
                number=p.number,
                chapter_id=p.chapter_id,
                chapter_title=p.chapter.title if p.chapter else None,
                chapter_number=p.chapter.number if p.chapter else None,
                order=p.order or 0,
            )
            for p in paragraphs
        ]

        return TextbookGraphResponse(
            textbook_id=textbook_id,
            nodes=nodes,
            edges=edges,
            total_edges=len(edges),
        )

    # =========================================================================
    # Teacher: analytics
    # =========================================================================

    async def get_prerequisite_analytics(
        self,
        paragraph_id: int,
        student_ids: List[int],
    ) -> PrerequisiteAnalyticsResponse:
        """
        For teachers: analyze which prerequisites students in a class are failing.
        Shows "root cause" — the prerequisite that's actually the problem.
        """
        # Get paragraph info
        para = await self._get_paragraph_with_chapter(paragraph_id)

        prereqs = await self.prereq_repo.get_prerequisites(paragraph_id)
        if not prereqs:
            return PrerequisiteAnalyticsResponse(
                paragraph_id=paragraph_id,
                paragraph_title=para.title,
            )

        # For each prerequisite, batch-fetch mastery for all students
        items = []
        for prereq in prereqs:
            pid = prereq.prerequisite_paragraph_id
            prereq_para = prereq.prerequisite
            chapter = prereq_para.chapter if prereq_para else None
            textbook = chapter.textbook if chapter else None

            # Get mastery records for all students
            mastery_records = await self._get_mastery_for_students(
                student_ids, pid
            )

            total = len(student_ids)
            struggling = 0
            score_sum = 0.0

            for sid in student_ids:
                mastery = mastery_records.get(sid)
                effective = 0.0
                if mastery and mastery.best_score:
                    effective = mastery.effective_score or 0.0
                score_sum += effective
                if effective < PREREQUISITE_THRESHOLD:
                    struggling += 1

            avg_score = score_sum / total if total > 0 else 0.0

            items.append(PrerequisiteAnalyticsItem(
                prerequisite_paragraph_id=pid,
                prerequisite_title=prereq_para.title if prereq_para else None,
                prerequisite_number=prereq_para.number if prereq_para else None,
                chapter_title=chapter.title if chapter else None,
                textbook_title=textbook.title if textbook else None,
                grade_level=textbook.grade_level if textbook else None,
                strength=prereq.strength,
                struggling_count=struggling,
                total_students=total,
                average_score=round(avg_score, 4),
            ))

        # Sort by struggling_count desc (worst prerequisite first)
        items.sort(key=lambda x: x.struggling_count, reverse=True)

        return PrerequisiteAnalyticsResponse(
            paragraph_id=paragraph_id,
            paragraph_title=para.title,
            prerequisites=items,
        )

    # =========================================================================
    # Private helpers
    # =========================================================================

    async def _get_paragraph_with_chapter(self, paragraph_id: int) -> Paragraph:
        """Load paragraph with its chapter and textbook (for subject check)."""
        result = await self.db.execute(
            select(Paragraph)
            .options(
                selectinload(Paragraph.chapter)
                .selectinload(Chapter.textbook)
            )
            .where(Paragraph.id == paragraph_id, Paragraph.is_deleted == False)
        )
        para = result.scalar_one_or_none()
        if not para:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paragraph {paragraph_id} not found",
            )
        return para

    async def _get_mastery_map(
        self, student_id: int, paragraph_ids: List[int]
    ) -> Dict[int, ParagraphMastery]:
        """Batch fetch mastery records. Returns Dict[paragraph_id, ParagraphMastery]."""
        if not paragraph_ids:
            return {}

        result = await self.db.execute(
            select(ParagraphMastery).where(
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.paragraph_id.in_(paragraph_ids),
            )
        )
        records = result.scalars().all()
        return {m.paragraph_id: m for m in records}

    async def _get_mastery_for_students(
        self, student_ids: List[int], paragraph_id: int
    ) -> Dict[int, ParagraphMastery]:
        """Fetch mastery records for multiple students on one paragraph."""
        if not student_ids:
            return {}

        result = await self.db.execute(
            select(ParagraphMastery).where(
                ParagraphMastery.student_id.in_(student_ids),
                ParagraphMastery.paragraph_id == paragraph_id,
            )
        )
        records = result.scalars().all()
        return {m.student_id: m for m in records}

    async def _check_circular_dependency(
        self,
        paragraph_id: int,
        prerequisite_paragraph_id: int,
        subject_id: int,
    ) -> None:
        """
        Check if adding paragraph_id → prerequisite_paragraph_id would create a cycle.
        Uses BFS from prerequisite_paragraph_id following the prerequisite chain
        across all textbooks of the subject.
        If paragraph_id is reachable, adding this edge creates a cycle.
        """
        graph = await self.prereq_repo.get_all_prerequisites_for_subject(subject_id)

        # BFS from prerequisite_paragraph_id
        visited = set()
        queue = deque([prerequisite_paragraph_id])
        depth = 0

        while queue and depth < MAX_CYCLE_DEPTH:
            level_size = len(queue)
            for _ in range(level_size):
                node = queue.popleft()
                if node == paragraph_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Adding this prerequisite would create a circular dependency. "
                            f"Paragraph {paragraph_id} is already a prerequisite "
                            f"(direct or transitive) of paragraph {prerequisite_paragraph_id}."
                        ),
                    )
                if node not in visited:
                    visited.add(node)
                    for prereq_id in graph.get(node, []):
                        if prereq_id not in visited:
                            queue.append(prereq_id)
            depth += 1
