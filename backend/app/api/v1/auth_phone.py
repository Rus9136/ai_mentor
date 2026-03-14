"""
Phone authentication endpoints.

Provides registration and login by phone number (Kazakhstan format +7XXXXXXXXXX).
Password is optional for now — will be required in the future.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.core.rate_limiter import limiter, AUTH_RATE_LIMIT
from app.core.errors import APIError, ErrorCode
from app.models.user import User, UserRole, AuthProvider
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    PhoneRegisterRequest,
    PhoneLoginRequest,
    PhoneAuthResponse,
    UserResponse,
)


router = APIRouter()


@router.post("/phone/register", response_model=PhoneAuthResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def phone_register(
    request: Request,
    data: PhoneRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new student with phone number.

    Creates a new user with STUDENT role and phone auth provider.
    After registration, user must complete onboarding (invitation code)
    to bind to a school.
    """
    user_repo = UserRepository(db)

    # Check if phone is already registered
    existing = await user_repo.get_by_phone(data.phone)
    if existing:
        raise APIError(
            ErrorCode.RES_002,
            message="Phone number already registered",
        )

    # Create user
    user = User(
        email=f"phone_{data.phone}@phone.local",
        phone=data.phone,
        auth_provider=AuthProvider.PHONE,
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        role=UserRole.STUDENT,
        school_id=None,
        is_active=True,
        is_verified=False,
        password_hash=get_password_hash(data.password) if data.password else None,
    )
    user = await user_repo.create(user)

    # Generate tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "school_id": user.school_id,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return PhoneAuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        requires_onboarding=True,
    )


@router.post("/phone/login", response_model=PhoneAuthResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def phone_login(
    request: Request,
    data: PhoneLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with phone number.

    Currently password is not required. In the future, password
    verification will be enforced.
    """
    user_repo = UserRepository(db)

    user = await user_repo.get_by_phone(data.phone)
    if not user:
        raise APIError(ErrorCode.AUTH_001, message="Phone number not registered")

    if not user.is_active:
        raise APIError(ErrorCode.ACCESS_004)

    # Generate tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "school_id": user.school_id,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})

    # Check if onboarding is needed
    requires_onboarding = (
        user.role == UserRole.STUDENT and user.school_id is None
    )

    return PhoneAuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        requires_onboarding=requires_onboarding,
    )
