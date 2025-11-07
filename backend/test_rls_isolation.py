"""
Test script for RLS (Row Level Security) data isolation.
Verifies that users from different schools cannot see each other's data.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select

from app.core.config import settings
from app.core.tenancy import set_current_tenant, reset_tenant
from app.models.student import Student


async def test_rls_isolation():
    """Test that RLS policies enforce data isolation between schools."""
    print("🧪 Testing RLS Data Isolation...\n")

    # Create engine and session
    engine = create_async_engine(settings.async_database_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # ===========================================
        # Test 0: Check session variables
        # ===========================================
        print("0️⃣ Test: Check session variables")
        result = await session.execute(text("SELECT current_setting('app.is_super_admin', true)"))
        is_super_admin = result.scalar()
        result = await session.execute(text("SELECT current_setting('app.current_tenant_id', true)"))
        tenant_id = result.scalar()
        print(f"   is_super_admin: {is_super_admin}")
        print(f"   current_tenant_id: {tenant_id}\n")

        # ===========================================
        # Test 1: No tenant context - should see NO students
        # ===========================================
        print("1️⃣ Test: Query without tenant context")
        await reset_tenant(session)
        # Explicitly set is_super_admin to false
        await session.execute(text("SELECT set_config('app.is_super_admin', 'false', false)"))
        await session.commit()

        result = await session.execute(select(Student))
        students = result.scalars().all()
        print(f"   Students visible without tenant: {len(students)}")
        print(f"   (Should be 0 when no tenant is set)\n")

        # ===========================================
        # Test 2: Set tenant to school_id=1 - should see only school 1 students
        # ===========================================
        print("2️⃣ Test: Set tenant context to school_id=1")
        await set_current_tenant(session, 1)
        await session.commit()

        result = await session.execute(select(Student))
        students_school_1 = result.scalars().all()
        print(f"   Students visible for school 1: {len(students_school_1)}")
        if students_school_1:
            print(f"   Sample: Student ID={students_school_1[0].id}, school_id={students_school_1[0].school_id}")
        print()

        # ===========================================
        # Test 3: Set tenant to school_id=2 - should see only school 2 students
        # ===========================================
        print("3️⃣ Test: Set tenant context to school_id=2")
        await set_current_tenant(session, 2)
        await session.commit()

        result = await session.execute(select(Student))
        students_school_2 = result.scalars().all()
        print(f"   Students visible for school 2: {len(students_school_2)}")
        if students_school_2:
            print(f"   Sample: Student ID={students_school_2[0].id}, school_id={students_school_2[0].school_id}")
        print()

        # ===========================================
        # Test 4: Set tenant to school_id=3 - should see only school 3 students
        # ===========================================
        print("4️⃣ Test: Set tenant context to school_id=3")
        await set_current_tenant(session, 3)
        await session.commit()

        result = await session.execute(select(Student))
        students_school_3 = result.scalars().all()
        print(f"   Students visible for school 3: {len(students_school_3)}")
        if students_school_3:
            print(f"   Sample: Student ID={students_school_3[0].id}, school_id={students_school_3[0].school_id}")
        print()

        # ===========================================
        # Verification
        # ===========================================
        print("=" * 60)
        print("✅ RLS Isolation Test Results:")
        print(f"   - School 1 students: {len(students_school_1)}")
        print(f"   - School 2 students: {len(students_school_2)}")
        print(f"   - School 3 students: {len(students_school_3)}")
        print()

        # Check that no overlap
        school_1_ids = {s.id for s in students_school_1}
        school_2_ids = {s.id for s in students_school_2}
        school_3_ids = {s.id for s in students_school_3}

        overlap_1_2 = school_1_ids & school_2_ids
        overlap_1_3 = school_1_ids & school_3_ids
        overlap_2_3 = school_2_ids & school_3_ids

        if not overlap_1_2 and not overlap_1_3 and not overlap_2_3:
            print("   ✅ NO DATA OVERLAP - Perfect isolation!")
        else:
            print("   ⚠️  DATA OVERLAP DETECTED:")
            if overlap_1_2:
                print(f"      School 1 ∩ School 2: {overlap_1_2}")
            if overlap_1_3:
                print(f"      School 1 ∩ School 3: {overlap_1_3}")
            if overlap_2_3:
                print(f"      School 2 ∩ School 3: {overlap_2_3}")

        print("=" * 60)

        # ===========================================
        # Test 5: Check global content (textbooks with school_id = NULL)
        # ===========================================
        print("\n5️⃣ Test: Global content visibility")

        # School 1 context
        await set_current_tenant(session, 1)
        await session.commit()
        result = await session.execute(
            text("SELECT COUNT(*) FROM textbooks WHERE school_id IS NULL")
        )
        global_textbooks_school_1 = result.scalar()
        print(f"   School 1 sees {global_textbooks_school_1} global textbooks")

        # School 2 context
        await set_current_tenant(session, 2)
        await session.commit()
        result = await session.execute(
            text("SELECT COUNT(*) FROM textbooks WHERE school_id IS NULL")
        )
        global_textbooks_school_2 = result.scalar()
        print(f"   School 2 sees {global_textbooks_school_2} global textbooks")

        if global_textbooks_school_1 == global_textbooks_school_2:
            print(f"   ✅ Global content is visible to ALL schools!\n")
        else:
            print(f"   ⚠️  Global content visibility differs!\n")

    await engine.dispose()

    print("=" * 60)
    print("🎉 RLS isolation test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_rls_isolation())
