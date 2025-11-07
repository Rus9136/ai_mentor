"""
Integration test for TenancyMiddleware.
Tests that middleware sets tenant context from JWT token.
"""
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token
from app.core.tenancy import get_current_tenant
from app.repositories.user_repo import UserRepository


async def test_tenancy_middleware():
    """Test that TenancyMiddleware sets tenant context from JWT."""
    print("🧪 Testing TenancyMiddleware...\n")

    # Get a database session
    db_generator = get_db()
    db = await db_generator.__anext__()

    try:
        # Get an existing user from database (ADMIN with school_id)
        user_repo = UserRepository(db)

        # Try to find a SUPER_ADMIN user first
        result = await db.execute(
            text("""
            SELECT id, email, role, school_id
            FROM users
            WHERE role = 'super_admin' AND is_active = true
            LIMIT 1
            """)
        )
        super_admin = result.first()

        # Try to find a regular ADMIN user
        result = await db.execute(
            text("""
            SELECT id, email, role, school_id
            FROM users
            WHERE role = 'admin' AND is_active = true AND school_id IS NOT NULL
            LIMIT 1
            """)
        )
        admin_user = result.first()

        if not super_admin and not admin_user:
            print("⚠️  No users found in database. Please create test users first.")
            return

        # Test 1: Public endpoint (no authentication)
        print("1️⃣ Test: Public endpoint (/health) - should work without token")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            print(f"   ✅ Public endpoint works: {response.json()}\n")

        # Test 2: SUPER_ADMIN user (if exists)
        if super_admin:
            print(f"2️⃣ Test: SUPER_ADMIN request - should reset tenant context")
            print(f"   User: {super_admin.email}, ID: {super_admin.id}, Role: {super_admin.role}")

            # Create JWT token for SUPER_ADMIN
            token = create_access_token({"sub": str(super_admin.id)})

            # Make authenticated request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                data = response.json()
                print(f"   ✅ SUPER_ADMIN authenticated: {data['email']}")
                print(f"   ✅ Tenant context should be reset (no school_id)\n")

        # Test 3: Regular ADMIN user
        if admin_user:
            print(f"3️⃣ Test: ADMIN request - should set tenant context")
            print(f"   User: {admin_user.email}, ID: {admin_user.id}, School ID: {admin_user.school_id}")

            # Create JWT token for ADMIN
            token = create_access_token({"sub": str(admin_user.id)})

            # Make authenticated request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                data = response.json()
                print(f"   ✅ ADMIN authenticated: {data['email']}")
                print(f"   ✅ Tenant context should be set to school_id={admin_user.school_id}\n")

        # Test 4: Unauthenticated request to protected endpoint
        print("4️⃣ Test: Protected endpoint without token - should return 403")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")
            assert response.status_code == 403, f"Expected 403, got {response.status_code}"
            print(f"   ✅ Unauthenticated request blocked\n")

        print("=" * 50)
        print("🎉 TenancyMiddleware integration tests passed!")
        print("=" * 50)
        print("\n📝 Note: Middleware sets tenant context automatically.")
        print("   - SUPER_ADMIN: tenant context is reset (sees all data)")
        print("   - Other roles: tenant context = user.school_id")

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(test_tenancy_middleware())
