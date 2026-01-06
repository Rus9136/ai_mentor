"""
Rate limiting configuration using slowapi.

Protects against brute force attacks on authentication endpoints.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.

    Handles X-Forwarded-For header for reverse proxy setups (nginx, etc.)
    """
    # Check X-Forwarded-For first (for reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take first IP (original client)
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct connection
    return get_remote_address(request)


# Create limiter instance with IP-based key function
limiter = Limiter(key_func=get_client_ip)

# Rate limit constants
AUTH_RATE_LIMIT = "5/minute"  # 5 login attempts per minute per IP
REFRESH_RATE_LIMIT = "10/minute"  # 10 refresh attempts per minute per IP
ONBOARDING_RATE_LIMIT = "10/minute"  # 10 onboarding attempts per minute per IP
