"""
Tests for App Version API endpoints.

- GET /api/version (public)
- GET /api/v1/admin/global/app-versions (SUPER_ADMIN)
- POST /api/v1/admin/global/app-versions (SUPER_ADMIN)
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_version import AppVersion, Platform
from app.models.user import User


# ========== Fixtures ==========


@pytest_asyncio.fixture
async def app_version_android(db_session: AsyncSession) -> AppVersion:
    """Seed an active Android version record."""
    version = AppVersion(
        platform=Platform.ANDROID,
        latest_version="2.1.0",
        min_version="1.5.0",
        release_notes="Bug fixes and improvements",
        is_active=True,
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)
    return version


@pytest_asyncio.fixture
async def app_version_ios(db_session: AsyncSession) -> AppVersion:
    """Seed an active iOS version record."""
    version = AppVersion(
        platform=Platform.IOS,
        latest_version="3.0.0",
        min_version="2.0.0",
        release_notes="New design",
        is_active=True,
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)
    return version


# ========== Unit tests: is_version_lower ==========


class TestIsVersionLower:
    """Unit tests for the is_version_lower helper."""

    def test_lower_major(self):
        from app.api.v1.app_version import is_version_lower

        assert is_version_lower("1.0.0", "2.0.0") is True

    def test_lower_minor(self):
        from app.api.v1.app_version import is_version_lower

        assert is_version_lower("1.0.0", "1.1.0") is True

    def test_lower_patch(self):
        from app.api.v1.app_version import is_version_lower

        assert is_version_lower("1.0.0", "1.0.1") is True

    def test_equal(self):
        from app.api.v1.app_version import is_version_lower

        assert is_version_lower("1.0.0", "1.0.0") is False

    def test_higher(self):
        from app.api.v1.app_version import is_version_lower

        assert is_version_lower("2.0.0", "1.0.0") is False

    def test_complex_comparison(self):
        from app.api.v1.app_version import is_version_lower

        assert is_version_lower("1.9.9", "2.0.0") is True
        assert is_version_lower("1.10.0", "1.9.0") is False


# ========== Public endpoint: GET /api/version ==========


class TestGetAppVersion:
    """Tests for GET /api/version (public, no auth)."""

    @pytest.mark.asyncio
    async def test_get_version_android(self, test_app, app_version_android):
        """Returns version info for android platform."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/version", params={"platform": "android"})

        assert response.status_code == 200
        data = response.json()
        assert data["latest_version"] == "2.1.0"
        assert data["min_version"] == "1.5.0"
        assert data["force_update"] is False
        assert data["release_notes"] == "Bug fixes and improvements"

    @pytest.mark.asyncio
    async def test_get_version_ios(self, test_app, app_version_ios):
        """Returns version info for ios platform."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/version", params={"platform": "ios"})

        assert response.status_code == 200
        data = response.json()
        assert data["latest_version"] == "3.0.0"
        assert data["min_version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_get_version_force_update_true(self, test_app, app_version_android):
        """current_version < min_version → force_update: true."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/version",
                params={"platform": "android", "current_version": "1.0.0"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["force_update"] is True

    @pytest.mark.asyncio
    async def test_get_version_force_update_false(self, test_app, app_version_android):
        """current_version >= min_version → force_update: false."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/version",
                params={"platform": "android", "current_version": "1.5.0"},
            )

        assert response.status_code == 200
        assert response.json()["force_update"] is False

    @pytest.mark.asyncio
    async def test_get_version_force_update_false_newer(self, test_app, app_version_android):
        """current_version > min_version → force_update: false."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/version",
                params={"platform": "android", "current_version": "2.1.0"},
            )

        assert response.status_code == 200
        assert response.json()["force_update"] is False

    @pytest.mark.asyncio
    async def test_get_version_without_current_version(self, test_app, app_version_android):
        """No current_version param → force_update: false."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/version", params={"platform": "android"})

        assert response.status_code == 200
        assert response.json()["force_update"] is False

    @pytest.mark.asyncio
    async def test_get_version_invalid_platform(self, test_app):
        """Invalid platform → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/version", params={"platform": "windows"})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_version_missing_platform(self, test_app):
        """No platform param → 422."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/version")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_version_no_active_record(self, test_app):
        """No active version in DB → 404."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/version", params={"platform": "android"})

        assert response.status_code == 404


# ========== Admin: GET /api/v1/admin/global/app-versions ==========


class TestListAppVersions:
    """Tests for GET /api/v1/admin/global/app-versions."""

    @pytest.mark.asyncio
    async def test_list_versions_super_admin(
        self, test_app, super_admin_token, app_version_android, app_version_ios
    ):
        """SUPER_ADMIN can list all version records."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/admin/global/app-versions",
                headers={"Authorization": f"Bearer {super_admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        platforms = {item["platform"] for item in data}
        assert platforms == {"android", "ios"}

    @pytest.mark.asyncio
    async def test_list_versions_unauthorized(self, test_app):
        """No token → 401/403."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/admin/global/app-versions")

        assert response.status_code in (401, 403)


# ========== Admin: POST /api/v1/admin/global/app-versions ==========


class TestCreateAppVersion:
    """Tests for POST /api/v1/admin/global/app-versions."""

    @pytest.mark.asyncio
    async def test_create_version_super_admin(
        self, test_app, super_admin_token, app_version_android
    ):
        """Creates new version and deactivates old one."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/admin/global/app-versions",
                headers={"Authorization": f"Bearer {super_admin_token}"},
                json={
                    "platform": "android",
                    "latest_version": "3.0.0",
                    "min_version": "2.0.0",
                    "release_notes": "Major update",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["latest_version"] == "3.0.0"
        assert data["min_version"] == "2.0.0"
        assert data["is_active"] is True
        assert data["platform"] == "android"

        # Verify old record deactivated by listing all
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            list_resp = await client.get(
                "/api/v1/admin/global/app-versions",
                headers={"Authorization": f"Bearer {super_admin_token}"},
            )

        versions = list_resp.json()
        android_versions = [v for v in versions if v["platform"] == "android"]
        assert len(android_versions) == 2
        active = [v for v in android_versions if v["is_active"]]
        inactive = [v for v in android_versions if not v["is_active"]]
        assert len(active) == 1
        assert active[0]["latest_version"] == "3.0.0"
        assert len(inactive) == 1
        assert inactive[0]["latest_version"] == "2.1.0"

    @pytest.mark.asyncio
    async def test_create_version_unauthorized(self, test_app):
        """No token → 401/403."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/admin/global/app-versions",
                json={
                    "platform": "android",
                    "latest_version": "1.0.0",
                    "min_version": "1.0.0",
                },
            )

        assert response.status_code in (401, 403)
