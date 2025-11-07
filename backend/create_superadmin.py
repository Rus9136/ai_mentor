"""
Скрипт для создания SUPER_ADMIN пользователя.
"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


async def create_superadmin():
    """Создать SUPER_ADMIN пользователя."""
    async with AsyncSessionLocal() as session:
        # Проверяем, существует ли уже superadmin
        result = await session.execute(
            select(User).where(User.email == "superadmin@aimentor.com")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("✅ SUPER_ADMIN уже существует:")
            print(f"   Email: {existing_user.email}")
            print(f"   Role: {existing_user.role}")
            print(f"   ID: {existing_user.id}")
            return

        # Создаем нового SUPER_ADMIN
        superadmin = User(
            email="superadmin@aimentor.com",
            password_hash=get_password_hash("admin123"),
            first_name="Super",
            last_name="Admin",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
            school_id=None,  # SUPER_ADMIN не привязан к школе
        )

        session.add(superadmin)
        await session.commit()
        await session.refresh(superadmin)

        print("✅ SUPER_ADMIN успешно создан!")
        print(f"   Email: {superadmin.email}")
        print(f"   Password: admin123")
        print(f"   Role: {superadmin.role}")
        print(f"   ID: {superadmin.id}")


if __name__ == "__main__":
    asyncio.run(create_superadmin())
