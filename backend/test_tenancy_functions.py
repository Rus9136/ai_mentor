"""
Test script for tenancy functions.
Tests set_current_tenant, get_current_tenant, and reset_tenant functions.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.tenancy import set_current_tenant, get_current_tenant, reset_tenant


async def test_tenancy_functions():
    """Test tenancy session variable functions."""
    print("🧪 Testing Tenancy Functions...\n")

    # Create engine and session
    engine = create_async_engine(settings.async_database_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("1️⃣ Test: set_current_tenant(db, 123)")
        await set_current_tenant(session, 123)
        tenant_id = await get_current_tenant(session)
        assert tenant_id == 123, f"Expected 123, got {tenant_id}"
        print(f"   ✅ Tenant set successfully: {tenant_id}\n")

        print("2️⃣ Test: get_current_tenant() after set")
        tenant_id = await get_current_tenant(session)
        assert tenant_id == 123, f"Expected 123, got {tenant_id}"
        print(f"   ✅ Tenant retrieved successfully: {tenant_id}\n")

        print("3️⃣ Test: set_current_tenant(db, 456) - update tenant")
        await set_current_tenant(session, 456)
        tenant_id = await get_current_tenant(session)
        assert tenant_id == 456, f"Expected 456, got {tenant_id}"
        print(f"   ✅ Tenant updated successfully: {tenant_id}\n")

        print("4️⃣ Test: reset_tenant()")
        await reset_tenant(session)
        tenant_id = await get_current_tenant(session)
        assert tenant_id is None, f"Expected None, got {tenant_id}"
        print(f"   ✅ Tenant reset successfully: {tenant_id}\n")

        print("5️⃣ Test: get_current_tenant() when not set")
        tenant_id = await get_current_tenant(session)
        assert tenant_id is None, f"Expected None, got {tenant_id}"
        print(f"   ✅ No tenant set (as expected): {tenant_id}\n")

    await engine.dispose()

    print("=" * 50)
    print("🎉 All tenancy function tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_tenancy_functions())
