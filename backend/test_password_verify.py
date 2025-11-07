"""
Тест проверки пароля
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import verify_password, get_password_hash

DATABASE_URL = "postgresql+asyncpg://ai_mentor_user:ai_mentor_pass@localhost:5432/ai_mentor_db"


async def test_password():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Получаем пользователя
        result = await session.execute(
            select(User).where(User.email == "superadmin@aimentor.com")
        )
        user = result.scalar_one_or_none()

        if not user:
            print("❌ Пользователь не найден!")
            return

        print(f"✅ Пользователь найден: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Role: {user.role}")
        print(f"   Password hash (first 40 chars): {user.password_hash[:40]}")
        print(f"   Is active: {user.is_active}")
        print(f"   Is verified: {user.is_verified}")

        # Тестируем пароли
        test_passwords = ["admin123", "password123", "Admin123"]

        for test_pwd in test_passwords:
            result = verify_password(test_pwd, user.password_hash)
            status = "✅ MATCH" if result else "❌ NO MATCH"
            print(f"\n   Testing password '{test_pwd}': {status}")

        # Генерируем новый хеш для сравнения
        new_hash = get_password_hash("admin123")
        print(f"\n   New hash for 'admin123': {new_hash[:40]}")
        print(f"   DB hash:                  {user.password_hash[:40]}")


if __name__ == "__main__":
    asyncio.run(test_password())
