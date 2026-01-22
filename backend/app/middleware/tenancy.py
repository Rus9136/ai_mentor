"""
Tenancy middleware for automatic tenant context management.

This middleware extracts user information from JWT token and stores it in
contextvars. The get_db() dependency then reads this context and sets
PostgreSQL session variables for RLS policies.

Architecture:
    1. Request arrives
    2. TenancyMiddleware decodes JWT → stores in contextvars
    3. Endpoint calls get_db() → reads contextvars → sets session variables
    4. All queries in that session are filtered by RLS
    5. Request ends → context cleared
"""
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_token
from app.core.tenant_context import set_tenant_context, clear_tenant_context

logger = logging.getLogger(__name__)


class TenancyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant info from JWT and store in contextvars.

    For each request:
    1. Checks if endpoint is public (skip auth)
    2. Extracts JWT token from Authorization header
    3. Decodes token to get user_id, role, and school_id
    4. Stores in contextvars for get_db() to use
    5. Clears context after request completes

    This ensures RLS policies work correctly because get_db() will set
    session variables in the SAME connection used by all queries.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Extract user info from JWT and store in contextvars.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response from endpoint
        """
        # Always clear context at start to prevent leakage from previous requests
        clear_tenant_context()

        try:
            # Skip tenant context for public endpoints
            if not self._is_public_endpoint(request.url.path):
                self._set_context_from_token(request)

            # Process request
            response = await call_next(request)
            return response

        finally:
            # Always clear context at end, even on errors
            clear_tenant_context()

    def _set_context_from_token(self, request: Request) -> None:
        """
        Extract JWT and set tenant context.

        Args:
            request: FastAPI request
        """
        try:
            token = self._extract_token(request)
            if not token:
                logger.debug("TenancyMiddleware: No token found")
                return

            payload = decode_token(token)
            if not payload:
                logger.debug("TenancyMiddleware: Invalid token")
                return

            user_id_str = payload.get("sub")
            if not user_id_str:
                logger.debug("TenancyMiddleware: No 'sub' claim in token")
                return

            try:
                user_id = int(user_id_str)
            except (ValueError, TypeError):
                logger.warning("TenancyMiddleware: Invalid user_id format")
                return

            # Set context in contextvars
            set_tenant_context(
                user_id=user_id,
                role=payload.get("role"),
                school_id=payload.get("school_id"),
                is_authenticated=True
            )

            logger.debug(
                f"TenancyMiddleware: context set for user_id={user_id}, "
                f"role={payload.get('role')}, school_id={payload.get('school_id')}"
            )

        except Exception as e:
            # Don't fail request on token errors - let endpoint handle auth
            logger.warning(f"TenancyMiddleware: Token processing error: {type(e).__name__}")

    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if endpoint is public (no authentication required).

        Args:
            path: Request URL path

        Returns:
            True if endpoint is public
        """
        public_prefixes = [
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/auth/google",
            # NOTE: /api/v1/auth/onboarding is NOT public - it requires auth token
            # and needs tenant context for RLS to work on user updates
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/",
        ]

        # Exact match for root
        if path == "/":
            return True

        # Prefix match for others
        return any(
            path.startswith(prefix)
            for prefix in public_prefixes
            if prefix != "/"
        )

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
            return auth_header.split(" ", 1)[1]

        return None
