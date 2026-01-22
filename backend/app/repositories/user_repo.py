"""
User repository for database operations.
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, and_, func
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

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        """
        Get user by Google ID (for OAuth users).

        Args:
            google_id: Google account ID

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(
                User.google_id == google_id,
                User.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_by_google_id_include_deleted(self, google_id: str) -> Optional[User]:
        """
        Get user by Google ID including soft-deleted users.

        Used for account restoration when a deleted user tries to log in again.

        Args:
            google_id: Google account ID

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email_include_deleted(self, email: str) -> Optional[User]:
        """
        Get user by email including soft-deleted users.

        Used for account restoration when a deleted user tries to register again.

        Args:
            email: User email

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
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

    async def get_by_school_paginated(
        self,
        school_id: int,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[User], int]:
        """
        Get users for a school with pagination and filters.

        Args:
            school_id: School ID for data isolation
            page: Page number (1-indexed)
            page_size: Number of items per page
            role: Filter by role (admin, teacher, student, parent)
            is_active: Filter by active status

        Returns:
            Tuple of (list of users, total count)
        """
        # Build filters
        filters = [
            User.school_id == school_id,
            User.is_deleted == False,  # noqa: E712
        ]

        if role is not None:
            filters.append(User.role == role)

        if is_active is not None:
            filters.append(User.is_active == is_active)

        # Base query
        query = select(User).where(and_(*filters))

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply ordering and pagination
        query = query.order_by(User.last_name, User.first_name)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        users = list(result.scalars().all())

        return users, total

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

        Clears google_id to allow re-registration with the same Google account.

        Args:
            user: User instance

        Returns:
            Deleted user
        """
        from datetime import datetime
        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        user.google_id = None  # Allow re-registration with same Google account
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def restore(self, user: User) -> User:
        """
        Restore a soft-deleted user.

        Args:
            user: User instance

        Returns:
            Restored user
        """
        user.is_deleted = False
        user.deleted_at = None
        user.is_active = True
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
