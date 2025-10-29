"""
Script to create a SUPER_ADMIN user for testing.
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole


async def create_superadmin():
    """Create SUPER_ADMIN user."""
    async with AsyncSessionLocal() as db:
        # Check if super admin already exists
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.email == "superadmin@aimentor.com")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("SUPER_ADMIN user already exists!")
            print(f"Email: {existing_user.email}")
            print(f"Role: {existing_user.role}")
            return

        # Create super admin
        super_admin = User(
            email="superadmin@aimentor.com",
            password_hash=get_password_hash("superadmin123"),
            first_name="Super",
            last_name="Admin",
            role=UserRole.SUPER_ADMIN,
            school_id=None,  # SUPER_ADMIN not tied to school
            is_active=True,
            is_verified=True,
        )

        db.add(super_admin)
        await db.commit()
        await db.refresh(super_admin)

        print("SUPER_ADMIN user created successfully!")
        print(f"ID: {super_admin.id}")
        print(f"Email: {super_admin.email}")
        print(f"Role: {super_admin.role}")
        print(f"Password: superadmin123")
        print("\nYou can now login with these credentials.")


if __name__ == "__main__":
    asyncio.run(create_superadmin())
