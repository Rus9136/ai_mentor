"""
Скрипт для сброса пароля SUPER_ADMIN пользователя.
"""
import asyncio
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash


async def reset_password():
    """Сбросить пароль SUPER_ADMIN."""
    async with AsyncSessionLocal() as session:
        # Ищем superadmin
        result = await session.execute(
            select(User).where(User.email == "superadmin@aimentor.com")
        )
        user = result.scalar_one_or_none()

        if not user:
            print("❌ SUPER_ADMIN не найден")
            return

        # Обновляем пароль
        new_password = "admin123"
        await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(password_hash=get_password_hash(new_password))
        )
        await session.commit()

        print("✅ Пароль SUPER_ADMIN обновлен!")
        print(f"   Email: {user.email}")
        print(f"   New Password: {new_password}")
        print(f"   ID: {user.id}")


if __name__ == "__main__":
    asyncio.run(reset_password())
