"""
Repository for InvitationCode data access.
"""
import secrets
import string
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invitation_code import InvitationCode, InvitationCodeUse
from app.models.school_class import SchoolClass
from app.models.user import User


class InvitationCodeRepository:
    """Repository for InvitationCode CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def generate_code(prefix: Optional[str] = None, length: int = 8) -> str:
        """
        Generate a unique invitation code.

        Args:
            prefix: Optional prefix for the code
            length: Length of random part (default 8)

        Returns:
            Generated code like "7A-X8K2M3N4" or "X8K2M3N4"
        """
        alphabet = string.ascii_uppercase + string.digits
        # Remove ambiguous characters
        alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('L', '')
        random_part = ''.join(secrets.choice(alphabet) for _ in range(length))

        if prefix:
            return f"{prefix.upper()}-{random_part}"
        return random_part

    async def get_by_id(
        self,
        code_id: int,
        school_id: int,
        load_uses: bool = False
    ) -> Optional[InvitationCode]:
        """
        Get invitation code by ID with school isolation.

        Args:
            code_id: Invitation code ID
            school_id: School ID for data isolation
            load_uses: Whether to eager load uses

        Returns:
            InvitationCode or None if not found
        """
        query = select(InvitationCode).where(
            InvitationCode.id == code_id,
            InvitationCode.school_id == school_id
        )

        if load_uses:
            query = query.options(selectinload(InvitationCode.uses))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[InvitationCode]:
        """
        Get invitation code by code string.

        Note: This method doesn't enforce school isolation because
        students use codes without knowing which school they belong to.

        Args:
            code: The invitation code string

        Returns:
            InvitationCode or None if not found
        """
        result = await self.db.execute(
            select(InvitationCode)
            .options(
                selectinload(InvitationCode.school),
                selectinload(InvitationCode.school_class)
            )
            .where(InvitationCode.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        school_id: int,
        is_active: Optional[bool] = None,
        class_id: Optional[int] = None,
        grade_level: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[InvitationCode]:
        """
        Get all invitation codes for a school with optional filters.

        Args:
            school_id: School ID for data isolation
            is_active: Filter by active status
            class_id: Filter by class ID
            grade_level: Filter by grade level
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of invitation codes
        """
        filters = [InvitationCode.school_id == school_id]

        if is_active is not None:
            filters.append(InvitationCode.is_active == is_active)

        if class_id is not None:
            filters.append(InvitationCode.class_id == class_id)

        if grade_level is not None:
            filters.append(InvitationCode.grade_level == grade_level)

        query = (
            select(InvitationCode)
            .options(
                selectinload(InvitationCode.school_class),
                selectinload(InvitationCode.creator)
            )
            .where(and_(*filters))
            .order_by(InvitationCode.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        school_id: int,
        is_active: Optional[bool] = None,
        class_id: Optional[int] = None,
        grade_level: Optional[int] = None
    ) -> int:
        """
        Count invitation codes with filters.

        Args:
            school_id: School ID for data isolation
            is_active: Filter by active status
            class_id: Filter by class ID
            grade_level: Filter by grade level

        Returns:
            Number of matching codes
        """
        filters = [InvitationCode.school_id == school_id]

        if is_active is not None:
            filters.append(InvitationCode.is_active == is_active)

        if class_id is not None:
            filters.append(InvitationCode.class_id == class_id)

        if grade_level is not None:
            filters.append(InvitationCode.grade_level == grade_level)

        result = await self.db.execute(
            select(func.count(InvitationCode.id)).where(and_(*filters))
        )
        return result.scalar_one()

    async def create(
        self,
        school_id: int,
        grade_level: int,
        created_by: int,
        class_id: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        max_uses: Optional[int] = None,
        code_prefix: Optional[str] = None
    ) -> InvitationCode:
        """
        Create a new invitation code.

        Args:
            school_id: School ID
            grade_level: Grade level (1-11)
            created_by: User ID who creates the code
            class_id: Optional class ID
            expires_at: Optional expiration date
            max_uses: Optional maximum uses
            code_prefix: Optional prefix for code generation

        Returns:
            Created invitation code
        """
        # Generate unique code with retries
        for _ in range(10):
            code = self.generate_code(prefix=code_prefix)
            existing = await self.get_by_code(code)
            if not existing:
                break
        else:
            raise ValueError("Failed to generate unique code")

        invitation_code = InvitationCode(
            code=code,
            school_id=school_id,
            class_id=class_id,
            grade_level=grade_level,
            expires_at=expires_at,
            max_uses=max_uses,
            created_by=created_by,
            is_active=True,
            uses_count=0
        )

        self.db.add(invitation_code)
        await self.db.commit()
        await self.db.refresh(invitation_code)
        return invitation_code

    async def update(self, invitation_code: InvitationCode) -> InvitationCode:
        """
        Update an invitation code.

        Args:
            invitation_code: InvitationCode instance with updated fields

        Returns:
            Updated invitation code
        """
        await self.db.commit()
        await self.db.refresh(invitation_code)
        return invitation_code

    async def deactivate(self, invitation_code: InvitationCode) -> InvitationCode:
        """
        Deactivate an invitation code.

        Args:
            invitation_code: InvitationCode instance

        Returns:
            Deactivated invitation code
        """
        invitation_code.is_active = False
        await self.db.commit()
        await self.db.refresh(invitation_code)
        return invitation_code

    async def validate_code(self, code: str) -> tuple[bool, Optional[str], Optional[InvitationCode]]:
        """
        Validate an invitation code.

        Args:
            code: The invitation code string

        Returns:
            Tuple of (is_valid, error_code, invitation_code)
            error_code can be: "code_not_found", "code_expired", "code_exhausted", "code_inactive"
        """
        invitation_code = await self.get_by_code(code)

        if not invitation_code:
            return False, "code_not_found", None

        if not invitation_code.is_active:
            return False, "code_inactive", None

        if invitation_code.expires_at:
            if datetime.now(timezone.utc) > invitation_code.expires_at:
                return False, "code_expired", None

        if invitation_code.max_uses is not None:
            if invitation_code.uses_count >= invitation_code.max_uses:
                return False, "code_exhausted", None

        return True, None, invitation_code

    async def use_code(
        self,
        invitation_code: InvitationCode,
        student_id: int
    ) -> InvitationCodeUse:
        """
        Record usage of an invitation code.

        Args:
            invitation_code: InvitationCode instance
            student_id: Student ID who uses the code

        Returns:
            Created InvitationCodeUse record
        """
        # Increment uses count
        invitation_code.uses_count += 1

        # Create use record
        code_use = InvitationCodeUse(
            invitation_code_id=invitation_code.id,
            student_id=student_id
        )

        self.db.add(code_use)
        await self.db.commit()
        await self.db.refresh(code_use)
        return code_use

    async def get_uses(
        self,
        code_id: int,
        school_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[InvitationCodeUse]:
        """
        Get all uses of an invitation code.

        Args:
            code_id: Invitation code ID
            school_id: School ID for validation
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of code uses
        """
        # Verify code belongs to school
        invitation_code = await self.get_by_id(code_id, school_id)
        if not invitation_code:
            return []

        query = (
            select(InvitationCodeUse)
            .options(selectinload(InvitationCodeUse.student))
            .where(InvitationCodeUse.invitation_code_id == code_id)
            .order_by(InvitationCodeUse.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())
