"""
Database session middleware for shared session pattern.

This middleware creates ONE database session per request and stores it in
request.state.db. This ensures that session variables (for RLS) are set
in the SAME connection used by all queries in the request.

This solves the RLS + eager loading problem where selectinload/joinedload
would create separate queries in different sessions without session variables.
"""
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to manage database session lifecycle.

    Creates a session at request start, commits/rollbacks at request end.
    Session is stored in request.state.db and reused by get_db() dependency.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Create database session for request.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response from endpoint
        """
        # Create session and store in request.state
        async with AsyncSessionLocal() as session:
            request.state.db = session

            try:
                # Call endpoint
                response = await call_next(request)

                # Commit if no errors
                await session.commit()

                return response

            except Exception as e:
                # Rollback on error
                await session.rollback()
                logger.error(f"Database session error: {e}", exc_info=True)
                raise

            finally:
                # Clean up
                await session.close()
                request.state.db = None
