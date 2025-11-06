"""
User repository for database operations.
"""
from typing import Optional, List
from sqlalchemy import select, and_
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

    async def get_by_school(
        self,
        school_id: int,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """
        Get all users for a specific school with optional filters.

        Args:
            school_id: School ID for data isolation
            role: Filter by role (admin, teacher, student, parent)
            is_active: Filter by active status

        Returns:
            List of users
        """
        filters = [
            User.school_id == school_id,
            User.is_deleted == False  # noqa: E712
        ]

        if role is not None:
            filters.append(User.role == role)

        if is_active is not None:
            filters.append(User.is_active == is_active)

        query = select(User).where(and_(*filters))
        query = query.order_by(User.last_name, User.first_name)

        result = await self.db.execute(query)
        return result.scalars().all()

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

    async def update(self, user: User) -> User:
        """
        Update an existing user.

        Args:
            user: User instance with updated fields

        Returns:
            Updated user
        """
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def soft_delete(self, user: User) -> User:
        """
        Soft delete a user.

        Args:
            user: User instance

        Returns:
            Deleted user
        """
        from datetime import datetime
        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def deactivate(self, user: User) -> User:
        """
        Deactivate a user (set is_active=False).

        Args:
            user: User instance

        Returns:
            Deactivated user
        """
        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def activate(self, user: User) -> User:
        """
        Activate a user (set is_active=True).

        Args:
            user: User instance

        Returns:
            Activated user
        """
        user.is_active = True
        await self.db.commit()
        await self.db.refresh(user)
        return user
