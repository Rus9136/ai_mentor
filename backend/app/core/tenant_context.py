"""
Tenant context management using contextvars.

This module provides thread-safe storage for tenant information that persists
across async calls within a single request. The middleware sets these values
early in the request lifecycle, and get_db() uses them to configure RLS.

Architecture:
    Request → TenancyMiddleware (sets context) → get_db() (reads context, sets session vars)
                                               → Endpoint (uses same db session with RLS)
"""
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class TenantInfo:
    """
    Tenant context information extracted from JWT token.

    Attributes:
        user_id: Current user's ID
        role: User's role (super_admin, admin, teacher, student, parent)
        school_id: User's school ID (None for super_admin or unassigned users)
        is_authenticated: Whether the request has valid authentication
    """
    user_id: Optional[int] = None
    role: Optional[str] = None
    school_id: Optional[int] = None
    is_authenticated: bool = False

    @property
    def is_super_admin(self) -> bool:
        """Check if user is SUPER_ADMIN."""
        return self.role == "super_admin"

    @property
    def has_school(self) -> bool:
        """Check if user has a school assigned."""
        return self.school_id is not None


# Context variable to store tenant info per request
# Each async request gets its own isolated copy
_tenant_context: ContextVar[TenantInfo] = ContextVar(
    "tenant_context",
    default=TenantInfo()
)


def get_tenant_context() -> TenantInfo:
    """
    Get current tenant context.

    Returns:
        TenantInfo with current request's tenant data.
        Returns empty TenantInfo if not set (unauthenticated request).

    Example:
        ctx = get_tenant_context()
        if ctx.is_authenticated:
            print(f"User {ctx.user_id} from school {ctx.school_id}")
    """
    return _tenant_context.get()


def set_tenant_context(
    user_id: Optional[int] = None,
    role: Optional[str] = None,
    school_id: Optional[int] = None,
    is_authenticated: bool = False
) -> TenantInfo:
    """
    Set tenant context for the current request.

    Called by TenancyMiddleware after JWT validation.

    Args:
        user_id: User ID from JWT 'sub' claim
        role: User role from JWT 'role' claim
        school_id: School ID from JWT 'school_id' claim
        is_authenticated: Whether JWT was valid

    Returns:
        The created TenantInfo object

    Example:
        # In middleware after decoding JWT:
        set_tenant_context(
            user_id=payload["sub"],
            role=payload["role"],
            school_id=payload.get("school_id"),
            is_authenticated=True
        )
    """
    info = TenantInfo(
        user_id=user_id,
        role=role,
        school_id=school_id,
        is_authenticated=is_authenticated
    )
    _tenant_context.set(info)

    logger.debug(
        f"Tenant context set: user_id={user_id}, role={role}, "
        f"school_id={school_id}, authenticated={is_authenticated}"
    )

    return info


def clear_tenant_context() -> None:
    """
    Clear tenant context.

    Called at the end of request to clean up.
    Important for connection pooling to avoid context leakage.
    """
    _tenant_context.set(TenantInfo())
    logger.debug("Tenant context cleared")


def require_tenant_context() -> TenantInfo:
    """
    Get tenant context, raising error if not authenticated.

    Use this in places where authentication is required.

    Returns:
        TenantInfo with valid tenant data

    Raises:
        RuntimeError: If tenant context is not set (unauthenticated)

    Example:
        ctx = require_tenant_context()
        # Safe to use ctx.user_id, ctx.school_id etc.
    """
    ctx = get_tenant_context()
    if not ctx.is_authenticated:
        raise RuntimeError(
            "Tenant context not set. This endpoint requires authentication. "
            "Ensure TenancyMiddleware is configured and JWT is valid."
        )
    return ctx
