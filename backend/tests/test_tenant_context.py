"""
Tests for tenant context and RLS session variables.

These tests verify that:
1. Tenant context is properly stored in contextvars
2. get_db() correctly reads context and sets session variables
3. RLS isolation works with the new architecture
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_context import (
    TenantInfo,
    get_tenant_context,
    set_tenant_context,
    clear_tenant_context,
    require_tenant_context,
)


class TestTenantInfo:
    """Tests for TenantInfo dataclass."""

    def test_default_tenant_info(self):
        """Test default TenantInfo values."""
        info = TenantInfo()
        assert info.user_id is None
        assert info.role is None
        assert info.school_id is None
        assert info.is_authenticated is False

    def test_is_super_admin_true(self):
        """Test is_super_admin property for super_admin role."""
        info = TenantInfo(role="super_admin", is_authenticated=True)
        assert info.is_super_admin is True

    def test_is_super_admin_false(self):
        """Test is_super_admin property for other roles."""
        info = TenantInfo(role="admin", is_authenticated=True)
        assert info.is_super_admin is False

    def test_has_school_true(self):
        """Test has_school property when school_id is set."""
        info = TenantInfo(school_id=1, is_authenticated=True)
        assert info.has_school is True

    def test_has_school_false(self):
        """Test has_school property when school_id is None."""
        info = TenantInfo(is_authenticated=True)
        assert info.has_school is False


class TestTenantContextFunctions:
    """Tests for tenant context management functions."""

    def setup_method(self):
        """Clear context before each test."""
        clear_tenant_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_tenant_context()

    def test_get_tenant_context_default(self):
        """Test getting default tenant context."""
        ctx = get_tenant_context()
        assert ctx.is_authenticated is False
        assert ctx.user_id is None

    def test_set_tenant_context(self):
        """Test setting tenant context."""
        set_tenant_context(
            user_id=123,
            role="admin",
            school_id=456,
            is_authenticated=True
        )

        ctx = get_tenant_context()
        assert ctx.user_id == 123
        assert ctx.role == "admin"
        assert ctx.school_id == 456
        assert ctx.is_authenticated is True

    def test_set_tenant_context_super_admin(self):
        """Test setting context for super_admin."""
        set_tenant_context(
            user_id=1,
            role="super_admin",
            school_id=None,
            is_authenticated=True
        )

        ctx = get_tenant_context()
        assert ctx.is_super_admin is True
        assert ctx.has_school is False

    def test_clear_tenant_context(self):
        """Test clearing tenant context."""
        set_tenant_context(user_id=123, role="admin", is_authenticated=True)
        clear_tenant_context()

        ctx = get_tenant_context()
        assert ctx.is_authenticated is False
        assert ctx.user_id is None

    def test_require_tenant_context_authenticated(self):
        """Test require_tenant_context with authenticated user."""
        set_tenant_context(user_id=123, is_authenticated=True)
        ctx = require_tenant_context()
        assert ctx.user_id == 123

    def test_require_tenant_context_unauthenticated(self):
        """Test require_tenant_context without authentication."""
        with pytest.raises(RuntimeError, match="Tenant context not set"):
            require_tenant_context()


class TestTenantContextIsolation:
    """Tests for context isolation between different contexts."""

    def setup_method(self):
        """Clear context before each test."""
        clear_tenant_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_tenant_context()

    def test_context_isolation_sequential(self):
        """Test that contexts don't leak between operations."""
        # First context
        set_tenant_context(user_id=1, school_id=10, is_authenticated=True)
        ctx1 = get_tenant_context()
        assert ctx1.user_id == 1

        # Clear and set new context
        clear_tenant_context()
        set_tenant_context(user_id=2, school_id=20, is_authenticated=True)
        ctx2 = get_tenant_context()

        # Verify new context
        assert ctx2.user_id == 2
        assert ctx2.school_id == 20


class TestDatabaseSessionVariables:
    """Tests for database session variable setup."""

    def setup_method(self):
        """Clear context before each test."""
        clear_tenant_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_tenant_context()

    @pytest.mark.asyncio
    async def test_session_variables_for_regular_user(self):
        """Test session variables are set for regular user."""
        from app.core.database import _set_session_variables

        # Mock session
        mock_session = AsyncMock(spec=AsyncSession)

        # Set context for regular user
        set_tenant_context(
            user_id=123,
            role="admin",
            school_id=456,
            is_authenticated=True
        )

        # Call function
        result = await _set_session_variables(mock_session)

        # Verify result
        assert result is True

        # Verify session.execute was called 3 times (user_id, is_super_admin, tenant_id)
        assert mock_session.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_session_variables_for_super_admin(self):
        """Test session variables are set for super_admin."""
        from app.core.database import _set_session_variables

        mock_session = AsyncMock(spec=AsyncSession)

        # Set context for super_admin
        set_tenant_context(
            user_id=1,
            role="super_admin",
            school_id=None,
            is_authenticated=True
        )

        result = await _set_session_variables(mock_session)
        assert result is True

        # Verify session.execute was called 3 times
        assert mock_session.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_session_variables_unauthenticated(self):
        """Test session variables are cleared for unauthenticated requests."""
        from app.core.database import _set_session_variables

        mock_session = AsyncMock(spec=AsyncSession)

        # No context set (unauthenticated)
        clear_tenant_context()

        result = await _set_session_variables(mock_session)
        assert result is False

        # All should be set to NULL - 3 calls
        assert mock_session.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_session_variables_user_without_school(self):
        """Test session variables for user without school."""
        from app.core.database import _set_session_variables

        mock_session = AsyncMock(spec=AsyncSession)

        # User without school (e.g., during onboarding)
        set_tenant_context(
            user_id=99,
            role="student",
            school_id=None,
            is_authenticated=True
        )

        result = await _set_session_variables(mock_session)
        assert result is True
        assert mock_session.execute.call_count == 3


class TestVerifyRLSContext:
    """Tests for verify_rls_context function."""

    @pytest.mark.asyncio
    async def test_verify_rls_context(self):
        """Test verify_rls_context returns correct values."""
        from app.core.database import verify_rls_context

        # Mock session with pre-set values
        mock_session = AsyncMock(spec=AsyncSession)

        # Setup mock to return different values for different calls
        mock_results = [
            MagicMock(scalar=MagicMock(return_value="123")),   # user_id
            MagicMock(scalar=MagicMock(return_value="456")),   # tenant_id
            MagicMock(scalar=MagicMock(return_value="false")), # is_super_admin
        ]
        mock_session.execute.side_effect = mock_results

        result = await verify_rls_context(mock_session)

        assert result["user_id"] == 123
        assert result["tenant_id"] == 456
        assert result["is_super_admin"] is False

    @pytest.mark.asyncio
    async def test_verify_rls_context_empty(self):
        """Test verify_rls_context handles empty values."""
        from app.core.database import verify_rls_context

        mock_session = AsyncMock(spec=AsyncSession)

        # Setup mock to return empty strings
        mock_results = [
            MagicMock(scalar=MagicMock(return_value="")),
            MagicMock(scalar=MagicMock(return_value=None)),
            MagicMock(scalar=MagicMock(return_value=None)),
        ]
        mock_session.execute.side_effect = mock_results

        result = await verify_rls_context(mock_session)

        assert result["user_id"] is None
        assert result["tenant_id"] is None
        assert result["is_super_admin"] is False
