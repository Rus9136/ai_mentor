"""Middleware for FastAPI application."""
from app.middleware.tenancy import TenancyMiddleware

__all__ = ["TenancyMiddleware"]
