"""
Скрипт для создания пользователей с обходом RLS (через ai_mentor_user role).
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.models.user import User, UserRole
from app.models.school import School
from app.core.security import get_password_hash

# URL с ai_mentor_user (superuser) для обхода RLS
DATABASE_URL = "postgresql+asyncpg://ai_mentor_user:ai_mentor_pass@localhost:5432/ai_mentor_db"


async def create_users():
    """Создать тестовых пользователей."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Создаем/находим школу
        result = await session.execute(
            select(School).where(School.code == "SCHOOL001")
        )
        school = result.scalar_one_or_none()

        if not school:
            school = School(
                name="Тестовая школа №1",
                code="SCHOOL001",
                is_active=True,
            )
            session.add(school)
            await session.commit()
            await session.refresh(school)
            print(f"✅ Создана школа: {school.name} (ID: {school.id})")
        else:
            print(f"✅ Школа уже существует: {school.name} (ID: {school.id})")

        # 2. Создаем SUPER_ADMIN
        result = await session.execute(
            select(User).where(User.email == "superadmin@aimentor.com")
        )
        superadmin = result.scalar_one_or_none()

        if not superadmin:
            superadmin = User(
                email="superadmin@aimentor.com",
                password_hash=get_password_hash("admin123"),
                first_name="Super",
                last_name="Admin",
                role=UserRole.SUPER_ADMIN,
                is_active=True,
                is_verified=True,
                school_id=None,
            )
            session.add(superadmin)
            await session.commit()
            await session.refresh(superadmin)
            print(f"✅ Создан SUPER_ADMIN: {superadmin.email} (ID: {superadmin.id})")
        else:
            print(f"✅ SUPER_ADMIN уже существует: {superadmin.email} (ID: {superadmin.id})")

        # 3. Создаем School ADMIN
        result = await session.execute(
            select(User).where(User.email == "school.admin@test.com")
        )
        school_admin = result.scalar_one_or_none()

        if not school_admin:
            school_admin = User(
                email="school.admin@test.com",
                password_hash=get_password_hash("admin123"),
                first_name="School",
                last_name="Admin",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                school_id=school.id,
            )
            session.add(school_admin)
            await session.commit()
            await session.refresh(school_admin)
            print(f"✅ Создан School ADMIN: {school_admin.email} (ID: {school_admin.id}, School: {school.id})")
        else:
            print(f"✅ School ADMIN уже существует: {school_admin.email} (ID: {school_admin.id})")

        print("\n" + "="*60)
        print("УЧЕТНЫЕ ДАННЫЕ ДЛЯ ВХОДА:")
        print("="*60)
        print("\n1. SUPER_ADMIN:")
        print(f"   Email: superadmin@aimentor.com")
        print(f"   Пароль: admin123")
        print(f"   Роль: SUPER_ADMIN")
        print(f"   ID: {superadmin.id}")

        print("\n2. School ADMIN:")
        print(f"   Email: school.admin@test.com")
        print(f"   Пароль: admin123")
        print(f"   Роль: ADMIN")
        print(f"   Школа: {school.name} (ID: {school.id})")
        print(f"   ID: {school_admin.id}")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(create_users())
