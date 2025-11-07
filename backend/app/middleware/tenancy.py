"""
Tenancy middleware for automatic tenant context management.

This middleware automatically sets the tenant context (school_id) for each request
based on the JWT token. Works together with RLS policies to provide automatic
data isolation at the database level.
"""
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import get_db
from app.core.security import decode_token
from app.core.tenancy import set_current_tenant, reset_tenant, set_super_admin_flag
from app.models.user import UserRole
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


class TenancyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically set tenant context for RLS policies.

    For each authenticated request:
    1. Extracts JWT token from Authorization header
    2. Decodes token to get user_id
    3. Fetches user from database to get school_id and role
    4. Sets tenant context:
       - For SUPER_ADMIN: resets tenant (bypass RLS)
       - For other roles: sets school_id as current tenant
    5. After request completes: cleans up tenant context

    This ensures RLS policies automatically filter data by school_id
    without requiring manual filtering in each endpoint.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and set tenant context.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response from endpoint
        """
        # Skip tenant context for public endpoints (login, health check, docs)
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)

        # Try to extract and set tenant context
        tenant_set = False
        db_session = None

        try:
            # Extract JWT token from Authorization header
            token = self._extract_token(request)

            if token:
                # Decode token to get user_id
                payload = decode_token(token)

                if payload and payload.get("sub"):
                    # Get database session
                    db_generator = get_db()
                    db_session = await db_generator.__anext__()

                    try:
                        # Get user from database
                        user_id = int(payload["sub"])
                        user_repo = UserRepository(db_session)
                        user = await user_repo.get_by_id(user_id)

                        if user and user.is_active:
                            # Set tenant context based on user role
                            if user.role == UserRole.SUPER_ADMIN:
                                # SUPER_ADMIN: reset tenant to see all data
                                await reset_tenant(db_session)
                                await set_super_admin_flag(db_session, True)
                                logger.debug(
                                    f"Tenant context: SUPER_ADMIN (user_id={user.id}), bypass RLS"
                                )
                            elif user.school_id:
                                # Regular user: set school_id as tenant
                                await set_current_tenant(db_session, user.school_id)
                                await set_super_admin_flag(db_session, False)
                                logger.debug(
                                    f"Tenant context set: school_id={user.school_id}, "
                                    f"user_id={user.id}, role={user.role}"
                                )
                            else:
                                logger.warning(
                                    f"User {user.id} has no school_id and is not SUPER_ADMIN"
                                )

                            # Commit the session variable changes
                            await db_session.commit()
                            tenant_set = True

                    except Exception as e:
                        logger.error(f"Error setting tenant context: {e}")
                        await db_session.rollback()
                    finally:
                        # Close database session
                        await db_session.close()

        except Exception as e:
            logger.error(f"Error in TenancyMiddleware: {e}")

        # Process request
        response = await call_next(request)

        # Cleanup: tenant context is automatically cleaned up when connection is closed
        # PostgreSQL session variables are connection-scoped

        return response

    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if endpoint is public (no authentication required).

        Args:
            path: Request URL path

        Returns:
            True if endpoint is public
        """
        public_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

        return any(path.startswith(endpoint) for endpoint in public_endpoints)

    def _extract_token(self, request: Request) -> str | None:
        """
        Extract JWT token from Authorization header.

        Args:
            request: FastAPI request

        Returns:
            JWT token string or None if not found
        """
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]

        return None
