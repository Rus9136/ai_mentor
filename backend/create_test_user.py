"""
Создание тестового SUPER_ADMIN пользователя.
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


async def create_test_superadmin():
    """Создать тестового SUPER_ADMIN пользователя."""
    async with AsyncSessionLocal() as db:
        # Проверяем, существует ли уже пользователь
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.email == "admin@test.com")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("✓ User admin@test.com already exists")
            print(f"  ID: {existing.id}")
            print(f"  Role: {existing.role}")
            return

        # Создаём нового пользователя
        user = User(
            email="admin@test.com",
            password_hash=get_password_hash("admin123"),
            first_name="Test",
            last_name="Admin",
            role=UserRole.SUPER_ADMIN,
            school_id=None,  # SUPER_ADMIN не привязан к школе
            is_active=True,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        print("✓ Created test SUPER_ADMIN user:")
        print(f"  Email: admin@test.com")
        print(f"  Password: admin123")
        print(f"  ID: {user.id}")
        print(f"  Role: {user.role}")


if __name__ == "__main__":
    asyncio.run(create_test_superadmin())
