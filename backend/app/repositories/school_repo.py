"""
Repository for School data access.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import School


class SchoolRepository:
    """Repository for School CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[School]:
        """
        Get all schools (not deleted).

        Returns:
            List of all schools ordered by creation date (newest first)
        """
        result = await self.db.execute(
            select(School)
            .where(School.is_deleted == False)
            .order_by(School.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, school_id: int) -> Optional[School]:
        """
        Get school by ID.

        Args:
            school_id: School ID

        Returns:
            School or None if not found
        """
        result = await self.db.execute(
            select(School).where(School.id == school_id, School.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[School]:
        """
        Get school by code (for uniqueness validation).

        Args:
            code: School code

        Returns:
            School or None if not found
        """
        result = await self.db.execute(
            select(School).where(School.code == code, School.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def create(self, school: School) -> School:
        """
        Create a new school.

        Args:
            school: School instance

        Returns:
            Created school
        """
        self.db.add(school)
        await self.db.commit()
        await self.db.refresh(school)
        return school

    async def update(self, school: School) -> School:
        """
        Update an existing school.

        Args:
            school: School instance with updated fields

        Returns:
            Updated school
        """
        await self.db.commit()
        await self.db.refresh(school)
        return school

    async def soft_delete(self, school: School) -> None:
        """
        Soft delete a school.

        Args:
            school: School instance
        """
        school.is_deleted = True
        school.deleted_at = datetime.utcnow()
        await self.db.commit()

    async def block(self, school_id: int) -> School:
        """
        Block a school (set is_active = False).

        Args:
            school_id: School ID

        Returns:
            Blocked school

        Raises:
            ValueError: If school not found
        """
        school = await self.get_by_id(school_id)
        if not school:
            raise ValueError(f"School {school_id} not found")

        school.is_active = False
        await self.db.commit()
        await self.db.refresh(school)
        return school

    async def unblock(self, school_id: int) -> School:
        """
        Unblock a school (set is_active = True).

        Args:
            school_id: School ID

        Returns:
            Unblocked school

        Raises:
            ValueError: If school not found
        """
        school = await self.get_by_id(school_id)
        if not school:
            raise ValueError(f"School {school_id} not found")

        school.is_active = True
        await self.db.commit()
        await self.db.refresh(school)
        return school
