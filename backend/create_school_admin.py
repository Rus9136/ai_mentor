"""
Скрипт для создания тестового школьного админа
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import User, School

async def create_test_school_admin():
    # Создаем engine и сессию
    engine = create_async_engine(settings.async_database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Проверяем, существует ли школа
        from sqlalchemy import select
        result = await session.execute(select(School).where(School.id == 3))
        school = result.scalar_one_or_none()

        if not school:
            print("Школа с ID 3 не найдена!")
            return

        # Проверяем, существует ли пользователь с таким email
        result = await session.execute(
            select(User).where(User.email == "admin@testschool.com")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"✅ Пользователь admin@testschool.com уже существует")
            print(f"   Email: admin@testschool.com")
            print(f"   Пароль: admin123")
            print(f"   Роль: ADMIN")
            print(f"   Школа: {school.name} (ID: {school.id})")
            return

        # Создаем нового админа
        admin = User(
            email="admin@testschool.com",
            password_hash=get_password_hash("admin123"),
            role="admin",
            school_id=school.id,
            first_name="Админ",
            last_name="Тестовый",
            middle_name="Школьный",
            is_active=True
        )

        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print("✅ Школьный админ успешно создан!")
        print(f"   Email: {admin.email}")
        print(f"   Пароль: admin123")
        print(f"   Роль: ADMIN")
        print(f"   Школа: {school.name} (ID: {school.id})")

if __name__ == "__main__":
    asyncio.run(create_test_school_admin())
