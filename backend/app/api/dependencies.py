"""
FastAPI dependencies for authentication and authorization.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.database import get_db
from app.core.security import decode_token, verify_token_type
from app.core.tenancy import set_current_tenant, reset_tenant, set_super_admin_flag, set_current_user_id
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenPayload

logger = logging.getLogger(__name__)


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token type
    if not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Convert user_id from string to int
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )

    # Set tenant context for RLS policies
    # This MUST be done in the SAME session that will be used by endpoints

    # Always set current user ID (for self-update RLS policies)
    await set_current_user_id(db, user.id)

    if user.role == UserRole.SUPER_ADMIN:
        await set_super_admin_flag(db, True)
        await reset_tenant(db)
        await db.commit()
        logger.info(f"Set SUPER_ADMIN mode for user_id={user.id}")
    elif user.school_id is not None:
        await set_current_tenant(db, user.school_id)
        await set_super_admin_flag(db, False)
        await db.commit()
        logger.info(f"Set tenant context: school_id={user.school_id}, user_id={user.id}")
    else:
        # User without school_id (e.g., student in onboarding)
        await set_super_admin_flag(db, False)
        await reset_tenant(db)
        await db.commit()
        logger.info(f"Set context for user without school: user_id={user.id}")

    return user


async def get_current_user_school_id(
    current_user: User = Depends(get_current_user)
) -> int:
    """
    Extract school_id from current user.

    This is critical for data isolation in multi-tenant architecture.
    SUPER_ADMIN users don't have school_id and will raise an error.

    Args:
        current_user: Current authenticated user

    Returns:
        School ID of the current user

    Raises:
        HTTPException: If user is SUPER_ADMIN (no school_id)
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SUPER_ADMIN has no school_id. Use global endpoints instead."
        )

    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no school_id assigned"
        )

    return current_user.school_id


def require_role(allowed_roles: list[UserRole]):
    """
    Factory function to create role-based access control dependency.

    Args:
        allowed_roles: List of allowed user roles

    Returns:
        Dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' is not allowed for this operation"
            )
        return current_user

    return role_checker


# Pre-configured role dependencies
require_super_admin = require_role([UserRole.SUPER_ADMIN])
require_admin = require_role([UserRole.ADMIN])
require_teacher = require_role([UserRole.TEACHER])
require_student = require_role([UserRole.STUDENT])
require_parent = require_role([UserRole.PARENT])

# Combined role dependencies
require_super_admin_or_admin = require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN])
require_admin_or_teacher = require_role([UserRole.ADMIN, UserRole.TEACHER])
