"""
Скрипт для создания тестового школьного админа для E2E тестов
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import User, School

async def create_test_school_admin():
    # Создаем engine и сессию
    engine = create_async_engine(settings.async_database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Находим любую школу или создаем тестовую
        result = await session.execute(select(School).limit(1))
        school = result.scalar_one_or_none()

        if not school:
            # Создаем тестовую школу
            school = School(
                name="Тестовая школа для E2E",
                code="TEST_E2E",
                region="Test Region"
            )
            session.add(school)
            await session.commit()
            await session.refresh(school)
            print(f"✅ Создана тестовая школа: {school.name} (ID: {school.id})")

        # Проверяем, существует ли пользователь с таким email
        result = await session.execute(
            select(User).where(User.email == "school.admin@test.com")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"✅ Пользователь school.admin@test.com уже существует")
            print(f"   Email: school.admin@test.com")
            print(f"   Пароль: admin123")
            print(f"   Роль: ADMIN")
            print(f"   Школа: {school.name} (ID: {school.id})")
            return

        # Создаем нового админа
        admin = User(
            email="school.admin@test.com",
            password_hash=get_password_hash("admin123"),
            role="admin",
            school_id=school.id,
            first_name="School",
            last_name="Admin",
            middle_name="Test",
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
