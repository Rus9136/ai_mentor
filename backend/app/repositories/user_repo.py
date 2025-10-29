"""
User repository for database operations.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository for User model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(
                User.email == email,
                User.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """
        Create a new user.

        Args:
            user: User object to create

        Returns:
            Created user
        """
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
