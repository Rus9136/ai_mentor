"""
Authentication endpoints.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.core.rate_limiter import limiter, AUTH_RATE_LIMIT, REFRESH_RATE_LIMIT
from app.core.errors import APIError, ErrorCode
from app.api.dependencies import get_current_user
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
)


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint.

    Authenticates user with email and password, returns access and refresh tokens.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(credentials.email)

    # Check if user exists
    if not user:
        raise APIError(ErrorCode.AUTH_001)  # Incorrect email or password

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise APIError(ErrorCode.AUTH_001)  # Incorrect email or password

    # Check if user is active
    if not user.is_active:
        raise APIError(ErrorCode.ACCESS_004)  # User account is inactive

    # Create token payload
    token_data = {
        "sub": str(user.id),  # JWT spec requires sub to be a string
        "email": user.email,
        "role": user.role.value,
        "school_id": user.school_id,
    }

    # Generate tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(REFRESH_RATE_LIMIT)
async def refresh_token(
    request: Request,
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh token endpoint.

    Takes a refresh token and returns new access and refresh tokens.
    """
    payload = decode_token(refresh_request.refresh_token)

    if not payload:
        raise APIError(ErrorCode.AUTH_007)  # Invalid refresh token

    # Verify token type
    if not verify_token_type(payload, "refresh"):
        raise APIError(ErrorCode.AUTH_004)  # Invalid token type

    # Get user
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise APIError(ErrorCode.AUTH_003)  # Invalid token payload

    # Convert user_id from string to int
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise APIError(ErrorCode.AUTH_003)  # Invalid user ID in token

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise APIError(ErrorCode.AUTH_005)  # User not found

    if not user.is_active:
        raise APIError(ErrorCode.ACCESS_004)  # User account is inactive

    # Create new tokens
    token_data = {
        "sub": str(user.id),  # JWT spec requires sub to be a string
        "email": user.email,
        "role": user.role.value,
        "school_id": user.school_id,
    }

    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.

    Returns information about the authenticated user.
    """
    return UserResponse.model_validate(current_user)
