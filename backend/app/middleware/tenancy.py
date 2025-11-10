"""
Tenancy middleware for automatic tenant context management.

This middleware extracts user information from JWT token and stores it in context.
The actual tenant context (session variables) is set by get_db() dependency in the
SAME database connection that endpoints use, ensuring RLS policies work correctly.
"""
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_token

logger = logging.getLogger(__name__)


class TenancyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract user info and prepare tenant context.

    For each authenticated request:
    1. Extracts JWT token from Authorization header
    2. Decodes token to get user_id, role, and school_id
    3. Stores this info in context for get_db() to use
    4. get_db() dependency will set session variables in the actual DB connection

    This ensures RLS policies work correctly with SQLAlchemy eager loading.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Extract user info from JWT and store in context.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response from endpoint
        """
        # Skip tenant context for public endpoints (login, health check, docs)
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)

        # Extract user info from JWT token and set context
        try:
            token = self._extract_token(request)
            logger.info(f"TenancyMiddleware: Extracted token: {token[:20] if token else 'None'}...")
            if token:
                payload = decode_token(token)
                logger.info(f"TenancyMiddleware: Decoded payload: {payload}")
                if payload and payload.get("sub"):
                    user_id = int(payload["sub"])
                    user_role = payload.get("role")
                    user_school_id = payload.get("school_id")

                    # Store in request.state for get_db() to use
                    request.state.user_id = user_id
                    request.state.user_role = user_role
                    request.state.user_school_id = user_school_id

                    logger.info(
                        f"TenancyMiddleware: Stored in request.state - user_id={user_id}, "
                        f"role={user_role}, school_id={user_school_id}"
                    )
                else:
                    logger.warning(f"TenancyMiddleware: No payload or sub in token")
        except Exception as e:
            logger.error(f"Error extracting user info in TenancyMiddleware: {e}", exc_info=True)

        # Process request - get_db() will read from request.state and set session variables
        response = await call_next(request)
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
